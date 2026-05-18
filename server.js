const childProcess = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const ROOT = __dirname;
const DATA_DIR = process.env.DATA_DIR ? path.resolve(process.env.DATA_DIR) : path.join(ROOT, "data");
const SEED_DATA_DIR = path.join(ROOT, "data");
const PORT = Number(process.env.PORT || 4173);
const HOST = process.env.HOST || "0.0.0.0";
const TWO_HOURS_MS = 2 * 60 * 60 * 1000;

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

  if (parsedUrl.pathname === "/api/stores/auchan/products" && request.method === "GET") {
    return sendJsonFile(response, dataPath("auchan-products.json"));
  }

  if (parsedUrl.pathname === "/api/stores/auchan/refresh" && request.method === "POST") {
    return refreshAuchan(response);
  }

  if (parsedUrl.pathname === "/api/stores/auchan/refresh-if-stale" && request.method === "POST") {
    const outputPath = dataPath("auchan-products.json");
    const stat = safeStat(outputPath);
    if (stat && Date.now() - stat.mtimeMs < TWO_HOURS_MS) {
      return sendJsonFile(response, outputPath);
    }
    return refreshAuchan(response);
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

function refreshAuchan(response) {
  const script = path.join(ROOT, "scripts", "fetch_auchan.py");
  const output = dataPath("auchan-products.json");
  const python = findPython();

  fs.mkdirSync(DATA_DIR, { recursive: true });

  const child = childProcess.spawn(
    python,
    [script, "--output", output, "--limit", "120"],
    {
      cwd: ROOT,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  let stdout = "";
  let stderr = "";
  const timeout = setTimeout(() => {
    child.kill("SIGTERM");
  }, 90000);

  child.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });

  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  child.on("close", (code) => {
    clearTimeout(timeout);
    if (code === 0) {
      return sendJsonFile(response, output);
    }

    return sendJson(response, 502, {
      error: "Не удалось обновить каталог Ашана",
      details: stderr.trim() || stdout.trim() || `Сборщик завершился с кодом ${code}`,
      fallback: readJson(output),
    });
  });
}

function findPython() {
  if (process.env.PYTHON) return process.env.PYTHON;

  const candidates = [
    path.join(ROOT, ".venv", "bin", "python3"),
    path.join(ROOT, ".venv", "bin", "python"),
    "/private/tmp/price-monitor-venv/bin/python",
    "python3.12",
    "python3",
  ];

  return candidates.find((candidate) => {
    if (!candidate.startsWith("/")) return true;
    return fs.existsSync(candidate);
  }) || "python3";
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
