#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import path from "node:path";
import process from "node:process";

function parseArgs(argv) {
  const options = {
    host: "127.0.0.1",
    frontendPort: 5175,
    apiPort: 5176,
    livePort: 8765,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];
    if (arg === "--host" && next) {
      options.host = next;
      index += 1;
    } else if (arg === "--frontend-port" && next) {
      options.frontendPort = Number(next);
      index += 1;
    } else if (arg === "--api-port" && next) {
      options.apiPort = Number(next);
      index += 1;
    } else if (arg === "--live-port" && next) {
      options.livePort = Number(next);
      index += 1;
    }
  }

  return options;
}

const options = parseArgs(process.argv.slice(2));

function parseNodeVersion(version) {
  const [major = 0, minor = 0, patch = 0] = version
    .trim()
    .split(".")
    .map((part) => Number(part));
  return { major, minor, patch };
}

function supportsVite(version) {
  const { major, minor } = parseNodeVersion(version);
  if (major === 20) return minor >= 19;
  if (major === 22) return minor >= 12;
  return major >= 23;
}

function nodeVersion(candidate) {
  const result = spawnSync(candidate, ["-p", "process.versions.node"], {
    encoding: "utf-8",
  });
  if (result.status !== 0) return "";
  return result.stdout.trim();
}

function addPathNodes(candidates) {
  const pathEntries = (process.env.PATH || "").split(path.delimiter).filter(Boolean);
  for (const entry of pathEntries) {
    candidates.add(path.join(entry, "node"));
  }
}

function addShellNodes(candidates) {
  const result = spawnSync("zsh", ["-lc", "command -v -a node || which -a node"], {
    encoding: "utf-8",
  });
  if (result.status !== 0) return;
  for (const line of result.stdout.split("\n")) {
    const candidate = line.trim();
    if (candidate) candidates.add(candidate);
  }
}

function findCompatibleNode() {
  const candidates = new Set([
    process.env.HYTRI_NODE,
    process.env.VITE_NODE,
    process.execPath,
    "/opt/homebrew/bin/node",
    "/usr/local/bin/node",
    "/opt/homebrew/opt/node/bin/node",
    "/usr/local/opt/node/bin/node",
  ]);
  addPathNodes(candidates);
  addShellNodes(candidates);

  const inspected = [];
  for (const candidate of candidates) {
    if (!candidate) continue;
    const version = nodeVersion(candidate);
    if (!version) continue;
    inspected.push(`${candidate} (${version})`);
    if (supportsVite(version)) {
      return { path: candidate, version };
    }
  }

  console.error("Could not find a Node.js runtime compatible with Vite.");
  console.error("Vite requires Node.js 20.19+ or 22.12+.");
  console.error(`Current process is Node.js ${process.versions.node} at ${process.execPath}.`);
  if (inspected.length) {
    console.error("Inspected runtimes:");
    for (const item of inspected) console.error(`- ${item}`);
  }
  console.error("Install/switch Node 22, or run with HYTRI_NODE=/path/to/node npm run dev:dashboard");
  process.exit(1);
}

const nodeRuntime = findCompatibleNode();
if (nodeRuntime.path !== process.execPath) {
  console.log(`Using Node.js ${nodeRuntime.version} at ${nodeRuntime.path} for dashboard services.`);
}

const children = [
  spawn(
    nodeRuntime.path,
    [
      "scripts/dashboard-api.mjs",
      "--host",
      options.host,
      "--port",
      String(options.apiPort),
      "--live-port",
      String(options.livePort),
    ],
    { stdio: "inherit" },
  ),
  spawn(
    nodeRuntime.path,
    [
      "node_modules/vite/bin/vite.js",
      "--host",
      options.host,
      "--port",
      String(options.frontendPort),
    ],
    { stdio: "inherit" },
  ),
];

let shuttingDown = false;

function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (!child.killed) child.kill(signal);
  }
}

for (const child of children) {
  child.on("exit", (code) => {
    if (!shuttingDown && code !== 0) {
      shutdown("SIGTERM");
      process.exitCode = code || 1;
    }
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
