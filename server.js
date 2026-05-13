const childProcess = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const url = require("node:url");

const ROOT = __dirname;
const PORT = Number(process.env.PORT || 4173);
const HOST = process.env.HOST || "127.0.0.1";
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
  const parsedUrl = url.parse(request.url, true);

  if (parsedUrl.pathname === "/api/stores/auchan/products" && request.method === "GET") {
    return sendJsonFile(response, path.join(ROOT, "data", "auchan-products.json"));
  }

  if (parsedUrl.pathname === "/api/stores/auchan/refresh" && request.method === "POST") {
    return refreshAuchan(response);
  }

  if (parsedUrl.pathname === "/api/stores/auchan/refresh-if-stale" && request.method === "POST") {
    const dataPath = path.join(ROOT, "data", "auchan-products.json");
    const stat = safeStat(dataPath);
    if (stat && Date.now() - stat.mtimeMs < TWO_HOURS_MS) {
      return sendJsonFile(response, dataPath);
    }
    return refreshAuchan(response);
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    return send(response, 405, "Method Not Allowed", "text/plain; charset=utf-8");
  }

  return sendStatic(request, response, parsedUrl.pathname);
});

server.listen(PORT, HOST, () => {
  console.log(`Price monitor server: http://${HOST}:${PORT}/`);
});

function refreshAuchan(response) {
  const script = path.join(ROOT, "scripts", "fetch_auchan.py");
  const output = path.join(ROOT, "data", "auchan-products.json");
  const python = process.env.PYTHON || "python3";

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
