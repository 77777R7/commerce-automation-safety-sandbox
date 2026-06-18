#!/usr/bin/env node

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const defaults = {
  dir: path.resolve(__dirname, "../dist"),
  host: "127.0.0.1",
  port: 5175,
};

function parseArgs(argv) {
  const options = { ...defaults };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === "--dir" && next) {
      options.dir = path.resolve(process.cwd(), next);
      index += 1;
    } else if (arg === "--host" && next) {
      options.host = next;
      index += 1;
    } else if (arg === "--port" && next) {
      options.port = Number(next);
      index += 1;
    }
  }

  return options;
}

const contentTypes = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".md", "text/markdown; charset=utf-8"],
  [".png", "image/png"],
  [".svg", "image/svg+xml"],
  [".txt", "text/plain; charset=utf-8"],
  [".webp", "image/webp"],
  [".yaml", "application/yaml; charset=utf-8"],
  [".yml", "application/yaml; charset=utf-8"],
]);

function isInsideRoot(root, target) {
  const relative = path.relative(root, target);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

async function findStaticFile(root, pathname) {
  const decoded = decodeURIComponent(pathname);
  const candidate = path.join(root, decoded);

  if (!isInsideRoot(root, candidate)) {
    return null;
  }

  try {
    const fileStat = await stat(candidate);
    if (fileStat.isDirectory()) {
      return path.join(candidate, "index.html");
    }
    if (fileStat.isFile()) {
      return candidate;
    }
  } catch {
    return null;
  }

  return null;
}

async function sendFile(response, filePath, method) {
  const extension = path.extname(filePath);
  const contentType = contentTypes.get(extension) ?? "application/octet-stream";
  response.writeHead(200, {
    "Content-Type": contentType,
    "Cache-Control": extension === ".html" ? "no-store" : "public, max-age=3600",
  });

  if (method === "HEAD") {
    response.end();
    return;
  }

  response.end(await readFile(filePath));
}

const options = parseArgs(process.argv.slice(2));
const root = path.resolve(options.dir);
const indexPath = path.join(root, "index.html");

const server = createServer(async (request, response) => {
  if (!request.url || !request.method || !["GET", "HEAD"].includes(request.method)) {
    response.writeHead(405);
    response.end();
    return;
  }

  const url = new URL(request.url, `http://${options.host}:${options.port}`);
  const staticFile = await findStaticFile(root, url.pathname);

  if (staticFile) {
    await sendFile(response, staticFile, request.method);
    return;
  }

  if (path.extname(url.pathname)) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
    return;
  }

  await sendFile(response, indexPath, request.method);
});

server.listen(options.port, options.host, () => {
  console.log(`Agent Integration Safety Site preview: http://${options.host}:${options.port}`);
  console.log(`Serving ${root}`);
  console.log("SPA fallback enabled for /demo/* routes.");
});
