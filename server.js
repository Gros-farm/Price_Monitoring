const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const ROOT = __dirname;
const DATA_DIR = process.env.DATA_DIR ? path.resolve(process.env.DATA_DIR) : path.join(ROOT, "data");
const SEED_DATA_DIR = path.join(ROOT, "data");
const PORT = Number(process.env.PORT || 4173);
const HOST = process.env.HOST || "0.0.0.0";
const TWO_HOURS_MS = 2 * 60 * 60 * 1000;
const AGENT_CONFIG = readJson(path.join(ROOT, "scripts", "agents", "stores.json")) || {};
const AGENT_STATUS_FILE = "agent-status.json";

const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
};

const server = http.createServer((request, response) => {
  const parsedUrl = new URL(request.url, `http://${request.headers.host || "localhost"}`);

  if (parsedUrl.pathname === "/health" && request.method === "GET") {
    return sendJson(response, 200, { status: "ok" });
  }

  const storeMatch = parsedUrl.pathname.match(/^\/api\/stores\/([^/]+)\/(products|refresh|refresh-if-stale)$/);
  if (storeMatch) {
    const [, storeId, action] = storeMatch;
    if (!AGENT_CONFIG[storeId]) {
      return sendJson(response, 404, { error: "Магазин не настроен" });
    }

    if (action === "products" && request.method === "GET") {
      return sendStoreSnapshot(response, storeId);
    }

    if ((action === "refresh" || action === "refresh-if-stale") && request.method === "POST") {
      return sendStoreSnapshot(response, storeId, {
        refreshRequested: true,
        onlyIfStale: action === "refresh-if-stale",
      });
    }
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    return send(response, 405, "Method Not Allowed", "text/plain; charset=utf-8");
  }

  return sendStatic(request, response, parsedUrl.pathname);
});

server.listen(PORT, HOST, () => {
  const visibleHost = HOST === "0.0.0.0" ? "127.0.0.1" : HOST;
  console.log(`Price monitor server: http://${visibleHost}:${PORT}/`);
});

function sendStoreSnapshot(response, storeId, options = {}) {
  const store = AGENT_CONFIG[storeId];
  const outputPath = dataPath(store.dataFile);
  const payload = readJson(outputPath);

  if (!payload) {
    return sendJson(response, 404, { error: "Файл данных не найден" });
  }

  const status = readJson(dataPath(AGENT_STATUS_FILE))?.stores?.[storeId] || null;
  const stat = safeStat(outputPath);
  const isFresh = stat ? Date.now() - stat.mtimeMs < TWO_HOURS_MS : false;

  return sendJson(response, 200, {
    ...payload,
    notice: buildSnapshotNotice(payload, store, { ...options, isFresh, status }),
    agent: {
      mode: "external",
      status,
      command: `npm run agent:${storeId}`,
      message: "Данные обновляет отдельный агент. Сайт читает последний успешный каталог.",
    },
  });
}

function buildSnapshotNotice(payload, store, { refreshRequested = false, onlyIfStale = false, isFresh = false, status = null } = {}) {
  const base = payload.notice || `${store.name}: загружен последний сохраненный каталог.`;
  if (!refreshRequested) return base;
  if (onlyIfStale && isFresh) return `${base} Каталог свежий, повторный запуск агента не нужен.`;
  if (status?.used_cached_data) {
    return `${base} Свежий сбор не прошел, поэтому показан последний сохраненный каталог.`;
  }
  if (status?.status === "failed") {
    return `${base} Последний запуск агента не обновил данные, показан сохраненный каталог.`;
  }
  return `${base} Показан последний успешный каталог. Для нового сбора запустите агента.`;
}

function dataPath(fileName) {
  const outputPath = path.join(DATA_DIR, fileName);
  if (!fs.existsSync(outputPath)) {
    const seedPath = path.join(SEED_DATA_DIR, fileName);
    if (fs.existsSync(seedPath)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
      fs.copyFileSync(seedPath, outputPath);
    }
  }
  return outputPath;
}

function sendStatic(request, response, pathname) {
  const safePath = pathname === "/" ? "/index.html" : decodeURIComponent(pathname);
  const filePath = path.normalize(path.join(ROOT, safePath));

  if (!filePath.startsWith(ROOT)) {
    return send(response, 403, "Forbidden", "text/plain; charset=utf-8");
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      return send(response, 404, "Not Found", "text/plain; charset=utf-8");
    }

    const mime = MIME_TYPES[path.extname(filePath)] || "application/octet-stream";
    response.writeHead(200, { "Content-Type": mime });
    if (request.method === "HEAD") return response.end();
    response.end(data);
  });
}

function sendJsonFile(response, filePath) {
  fs.readFile(filePath, "utf8", (error, data) => {
    if (error) {
      return sendJson(response, 404, { error: "Файл данных не найден" });
    }
    send(response, 200, data, "application/json; charset=utf-8");
  });
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function safeStat(filePath) {
  try {
    return fs.statSync(filePath);
  } catch {
    return null;
  }
}

function sendJson(response, status, payload) {
  send(response, status, JSON.stringify(payload, null, 2), "application/json; charset=utf-8");
}

function send(response, status, body, contentType) {
  response.writeHead(status, { "Content-Type": contentType });
  response.end(body);
}
