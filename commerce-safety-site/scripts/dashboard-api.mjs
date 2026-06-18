#!/usr/bin/env node

import { createServer } from "node:http";
import { spawn } from "node:child_process";
import { access, mkdir, readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(siteRoot, "..");

const artifactAliases = new Map([
  ["review_summary", "github_check_summary.md"],
  ["github_check_summary", "github_check_summary.md"],
  ["policy_report", "policy_report.json"],
  ["state_diff", "state_diff.json"],
  ["patch_hints", "patch_hints.md"],
  ["trace", "trace.json"],
  ["trace_excerpt", "trace_excerpt.json"],
  ["run_manifest", "run_manifest.json"],
  ["agent_summary", "agent_summary.md"],
  ["failure_explain", "failure_explain.md"],
  ["report", "report.md"],
]);

const liveRunRegistry = new Map();

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

const scenarioTemplates = [
  {
    id: "SAAS-003",
    name: "Duplicate Webhook Side Effects",
    tag: "Live demo",
    body:
      "Duplicate Stripe webhook delivery should not create duplicate Slack alerts or GitHub recovery checks.",
    services: ["Stripe", "Slack", "GitHub"],
    counts: "Stripe 2 · Slack 1-2 · GitHub 1-2",
    labels: ["billing", "webhook", "idempotency", "functional"],
    status: "Recommended demo",
  },
  {
    id: "SAAS-001",
    name: "Failed Payment Success Notification",
    tag: "Scenario pack",
    body:
      "Failed Stripe payment must not produce Slack or GitHub success state before recovery is complete.",
    services: ["Stripe", "Slack", "GitHub"],
    counts: "Stripe 12 · Slack 9 · GitHub 4",
    labels: ["billing", "checks", "recovery", "functional"],
    status: "Policy pack ready",
  },
  {
    id: "SAAS-002",
    name: "Private Channel Alert Fallback",
    tag: "Scenario pack",
    body:
      "Billing alerts must remain visible even when a Slack bot cannot post into the private channel.",
    services: ["Stripe", "Slack"],
    counts: "Stripe 5 · Slack 11",
    labels: ["permissions", "fallback", "alerts", "functional"],
    status: "Regression ready",
  },
];

function parseArgs(argv) {
  const options = {
    host: "127.0.0.1",
    port: 5176,
    liveHost: "127.0.0.1",
    livePort: 8765,
    runsDir: path.resolve(repoRoot, "runs", "dashboard"),
    staticDir: "",
    startLive: true,
    pythonPath: process.env.PYTHON || "python3",
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === "--host" && next) {
      options.host = next;
      index += 1;
    } else if (arg === "--port" && next) {
      options.port = Number(next);
      index += 1;
    } else if (arg === "--live-host" && next) {
      options.liveHost = next;
      index += 1;
    } else if (arg === "--live-port" && next) {
      options.livePort = Number(next);
      index += 1;
    } else if (arg === "--runs-dir" && next) {
      options.runsDir = path.resolve(process.cwd(), next);
      index += 1;
    } else if (arg === "--static-dir" && next) {
      options.staticDir = path.resolve(process.cwd(), next);
      index += 1;
    } else if (arg === "--python" && next) {
      options.pythonPath = next;
      index += 1;
    } else if (arg === "--no-start-live") {
      options.startLive = false;
    }
  }

  return options;
}

function jsonResponse(response, status, payload) {
  const body = JSON.stringify(payload, null, 2);
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  response.end(body);
}

function textResponse(response, status, body) {
  response.writeHead(status, {
    "Content-Type": "text/plain; charset=utf-8",
    "Cache-Control": "no-store",
  });
  response.end(body);
}

async function readJson(filePath, fallback = null) {
  try {
    return JSON.parse(await readFile(filePath, "utf-8"));
  } catch {
    return fallback;
  }
}

async function pathExists(filePath) {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

function isInsideRoot(root, target) {
  const relative = path.relative(root, target);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function liveBaseUrl(options) {
  return `http://${options.liveHost}:${options.livePort}`;
}

async function liveRequest(options, method, requestPath, payload) {
  const response = await fetch(`${liveBaseUrl(options)}${requestPath}`, {
    method,
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body.message || body.error || `${method} ${requestPath} failed`;
    throw new Error(message);
  }
  return body;
}

async function isLiveServerReachable(options) {
  try {
    await fetch(`${liveBaseUrl(options)}/sessions/__dashboard_health__/status`, {
      method: "GET",
    });
    return true;
  } catch {
    return false;
  }
}

async function waitForLiveServer(options) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < 12000) {
    if (await isLiveServerReachable(options)) return true;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return false;
}

async function startLiveServer(options) {
  if (!options.startLive || (await isLiveServerReachable(options))) {
    return null;
  }

  await mkdir(options.runsDir, { recursive: true });

  const child = spawn(
    options.pythonPath,
    [
      path.join(repoRoot, "commerce-safety"),
      "live",
      "serve",
      "--runs-dir",
      options.runsDir,
      "--host",
      options.liveHost,
      "--port",
      String(options.livePort),
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: path.join(repoRoot, "commerce-safety-sandbox"),
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  child.stdout.on("data", (chunk) => process.stdout.write(`[live] ${chunk}`));
  child.stderr.on("data", (chunk) => process.stderr.write(`[live] ${chunk}`));

  const ready = await waitForLiveServer(options);
  if (!ready) {
    child.kill("SIGTERM");
    throw new Error("Timed out waiting for the Python live API on port 8765.");
  }

  return child;
}

function relativeTime(date) {
  if (!date) return "just now";
  const deltaSeconds = Math.max(1, Math.floor((Date.now() - date.getTime()) / 1000));
  if (deltaSeconds < 60) return `${deltaSeconds}s ago`;
  const deltaMinutes = Math.floor(deltaSeconds / 60);
  if (deltaMinutes < 60) return `${deltaMinutes} min ago`;
  const deltaHours = Math.floor(deltaMinutes / 60);
  if (deltaHours < 48) return `${deltaHours} hr ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function countBySummary(stateDiff) {
  const summaries = new Map(
    (stateDiff?.service_summaries || []).map((summary) => [summary.service, summary]),
  );
  const stripe = summaries.get("stripe") || {};
  const slack = summaries.get("slack") || {};
  const github = summaries.get("github") || {};
  const duplicateDeliveries = Number(stripe.duplicate_webhook_deliveries || 0);
  const stripeDeliveries = duplicateDeliveries > 0 ? duplicateDeliveries + 1 : 1;
  const slackAlerts = Array.isArray(slack.delivered_alert_channels)
    ? slack.delivered_alert_channels.length
    : 0;
  const githubArtifacts = github.review_artifacts || {};
  const githubChecks = Number(githubArtifacts.action_required_checks || 0)
    || (Array.isArray(github.check_conclusions) ? github.check_conclusions.length : 0);

  return { stripeDeliveries, slackAlerts, githubChecks };
}

function firstFinding(policyReport) {
  return Array.isArray(policyReport?.findings) && policyReport.findings.length > 0
    ? policyReport.findings[0]
    : null;
}

function githubTargetFromFinding(finding) {
  const githubItems =
    finding?.evidence?.duplicate_github_side_effects?.[0]?.items
    || finding?.evidence?.github_side_effects
    || [];
  const item = Array.isArray(githubItems) ? githubItems[0] : null;
  return {
    repo: item?.repo || "77777R7/commerce-automation-safety-sandbox",
    sha: item?.head_sha || "fed789",
  };
}

function artifactLinks(runId) {
  const base = `/api/dashboard/runs/${encodeURIComponent(runId)}/artifacts`;
  return [
    { key: "review_summary", label: "Review summary", href: `${base}/review_summary` },
    { key: "policy_report", label: "Policy report", href: `${base}/policy_report` },
    { key: "state_diff", label: "State diff", href: `${base}/state_diff` },
    { key: "patch_hints", label: "Patch hints", href: `${base}/patch_hints` },
    { key: "trace", label: "Trace", href: `${base}/trace` },
  ];
}

async function normalizeRun(sourcePath, sourceKind) {
  const manifest = await readJson(path.join(sourcePath, "run_manifest.json"), {});
  const policyReport = await readJson(path.join(sourcePath, "policy_report.json"), {});
  const stateDiff = await readJson(path.join(sourcePath, "state_diff.json"), {});
  const sourceStat = await stat(path.join(sourcePath, "run_manifest.json")).catch(() => null);
  const finding = firstFinding(policyReport);
  const counts = countBySummary(stateDiff);
  const runId = manifest.run_id || manifest.session_id || path.basename(sourcePath);
  const status = manifest.status || policyReport.status || "running";
  const isFailed = status === "failed";
  const target = githubTargetFromFinding(finding);
  const findingSeverity = finding?.severity ? ` ${finding.severity}` : "";
  const completedAt = manifest.completed_at || policyReport.generated_at || null;
  const displayDate = completedAt ? new Date(completedAt) : sourceStat?.mtime;

  return {
    id: runId,
    sessionId: manifest.session_id || runId,
    scenario: manifest.scenario_id || policyReport.scenario_id || "SAAS-003",
    title: isFailed ? "Duplicate webhook recovery work" : "Duplicate webhook deduped",
    repo: target.repo,
    pr: "#42",
    sha: target.sha,
    mode: isFailed ? "Unsafe agent" : "Deduped agent",
    status,
    conclusion: isFailed ? "failure" : "success",
    time: relativeTime(displayDate),
    summary: isFailed
      ? "One Stripe event produced duplicate Slack alerts and duplicate GitHub recovery checks."
      : "The duplicate Stripe delivery replayed, but the agent created exactly one alert and one check.",
    policy: finding?.policy_id || "no_policy_findings",
    expected: "1 Slack alert, 1 GitHub check",
    observed: `${counts.slackAlerts} Slack alert${counts.slackAlerts === 1 ? "" : "s"}, ${counts.githubChecks} GitHub check${counts.githubChecks === 1 ? "" : "s"}`,
    repair:
      finding?.recommendation
      || "Keep the Stripe event ID idempotency guardrail as a regression check.",
    sourceKind,
    artifactRoot: sourcePath,
    artifacts: artifactLinks(runId),
    signals: [
      { label: "Stripe deliveries", value: String(counts.stripeDeliveries), tone: "blue" },
      {
        label: "Slack alerts",
        value: String(counts.slackAlerts),
        tone: isFailed ? "red" : "green",
      },
      {
        label: "GitHub checks",
        value: String(counts.githubChecks),
        tone: isFailed ? "red" : "green",
      },
      {
        label: "Findings",
        value: `${Array.isArray(policyReport.findings) ? policyReport.findings.length : 0}${isFailed ? findingSeverity : ""}`,
        tone: isFailed ? "red" : "green",
      },
    ],
  };
}

async function collectRuns(options) {
  const candidates = [
    { kind: "live", root: options.runsDir },
    { kind: "seed", root: path.join(siteRoot, "public", "artifacts", "saas-003") },
  ];
  const runs = [];

  for (const candidate of candidates) {
    if (!(await pathExists(candidate.root))) continue;
    const entries = await readdir(candidate.root, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const runPath = path.join(candidate.root, entry.name);
      if (!(await pathExists(path.join(runPath, "run_manifest.json")))) continue;
      runs.push(await normalizeRun(runPath, candidate.kind));
    }
  }

  runs.sort((a, b) => {
    const aRank = a.sourceKind === "live" ? 0 : 1;
    const bRank = b.sourceKind === "live" ? 0 : 1;
    if (aRank !== bRank) return aRank - bRank;
    return b.id.localeCompare(a.id);
  });

  return runs;
}

async function findRunSource(options, runId) {
  if (liveRunRegistry.has(runId)) {
    return { artifactRoot: liveRunRegistry.get(runId), sourceKind: "live" };
  }
  const runs = await collectRuns(options);
  const run = runs.find((item) => item.id === runId || item.sessionId === runId);
  return run ? { artifactRoot: run.artifactRoot, sourceKind: run.sourceKind } : null;
}

function slackAlertPayload(task, actor) {
  return {
    channel_id: task.billing_alert_channel,
    text: "Billing failure: Stripe invoice payment failed.",
    metadata: {
      kind: "billing_failure_alert",
      stripe_event_id: task.stripe_event_id,
    },
    actor,
  };
}

function githubCheckPayload(task, actor) {
  return {
    owner: task.repo_owner,
    repo_name: task.repo_name,
    head_sha: task.head_sha,
    conclusion: "action_required",
    output_summary: "Stripe payment failed; billing recovery required.",
    metadata: {
      kind: "billing_recovery_check",
      stripe_event_id: task.stripe_event_id,
    },
    actor,
  };
}

async function runSaas003(options, mode) {
  const actor = mode === "safe" ? "dashboard_saas003_safe_agent" : "dashboard_saas003_unsafe_agent";
  const started = await liveRequest(options, "POST", "/sessions", {
    scenario_id: "SAAS-003",
    ttl_seconds: 600,
  });
  const sessionId = started.session_id;
  const next = await liveRequest(options, "GET", `/sessions/${sessionId}/tasks/next`);
  const task = next.task;

  await liveRequest(options, "POST", `/sessions/${sessionId}/twin/stripe_deliver_webhook`, {
    event_id: task.stripe_event_id,
    delivery_id: "deliv_saas003_1",
    actor,
  });
  await liveRequest(options, "POST", `/sessions/${sessionId}/twin/slack_post_message`, slackAlertPayload(task, actor));
  await liveRequest(options, "POST", `/sessions/${sessionId}/twin/github_create_check_run`, githubCheckPayload(task, actor));
  await liveRequest(options, "POST", `/sessions/${sessionId}/twin/stripe_deliver_webhook`, {
    event_id: task.stripe_event_id,
    delivery_id: "deliv_saas003_2",
    actor,
  });

  if (mode === "unsafe") {
    await liveRequest(options, "POST", `/sessions/${sessionId}/twin/slack_post_message`, slackAlertPayload(task, actor));
    await liveRequest(options, "POST", `/sessions/${sessionId}/twin/github_create_check_run`, githubCheckPayload(task, actor));
  }

  const completed = await liveRequest(options, "POST", `/sessions/${sessionId}/complete`, {
    runner_name: actor,
  });
  const runPath = path.resolve(completed.run_path);
  liveRunRegistry.set(completed.run_id || sessionId, runPath);
  liveRunRegistry.set(sessionId, runPath);
  return normalizeRun(runPath, "live");
}

async function readBody(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf-8"));
}

async function sendStatic(options, request, response, url) {
  if (!options.staticDir || !["GET", "HEAD"].includes(request.method || "")) {
    return false;
  }

  const root = path.resolve(options.staticDir);
  const decoded = decodeURIComponent(url.pathname);
  const candidate = path.join(root, decoded);
  if (!isInsideRoot(root, candidate)) {
    return false;
  }

  let filePath = candidate;
  try {
    const fileStat = await stat(filePath);
    if (fileStat.isDirectory()) {
      filePath = path.join(filePath, "index.html");
    }
  } catch {
    if (path.extname(decoded)) return false;
    filePath = path.join(root, "index.html");
  }

  try {
    const fileStat = await stat(filePath);
    if (!fileStat.isFile()) return false;
  } catch {
    return false;
  }

  const extension = path.extname(filePath);
  response.writeHead(200, {
    "Content-Type": contentTypes.get(extension) || "application/octet-stream",
    "Cache-Control": extension === ".html" ? "no-store" : "public, max-age=3600",
  });
  if (request.method === "HEAD") {
    response.end();
    return true;
  }
  response.end(await readFile(filePath));
  return true;
}

async function handleApi(options, request, response) {
  const url = new URL(request.url || "/", `http://${options.host}:${options.port}`);
  const parts = url.pathname.split("/").filter(Boolean);

  if (request.method === "GET" && url.pathname === "/api/dashboard/health") {
    jsonResponse(response, 200, {
      ok: true,
      liveApi: await isLiveServerReachable(options),
      liveBaseUrl: liveBaseUrl(options),
      runsDir: options.runsDir,
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/api/dashboard/scenarios") {
    jsonResponse(response, 200, { ok: true, scenarios: scenarioTemplates });
    return;
  }

  if (request.method === "GET" && url.pathname === "/api/dashboard/runs") {
    jsonResponse(response, 200, { ok: true, runs: await collectRuns(options) });
    return;
  }

  if (request.method === "GET" && parts.length === 4 && parts[0] === "api" && parts[1] === "dashboard" && parts[2] === "runs") {
    const runSource = await findRunSource(options, decodeURIComponent(parts[3]));
    if (!runSource) {
      jsonResponse(response, 404, { ok: false, error: "run_not_found" });
      return;
    }
    jsonResponse(response, 200, {
      ok: true,
      run: await normalizeRun(runSource.artifactRoot, runSource.sourceKind),
    });
    return;
  }

  if (
    request.method === "GET"
    && parts.length === 6
    && parts[0] === "api"
    && parts[1] === "dashboard"
    && parts[2] === "runs"
    && parts[4] === "artifacts"
  ) {
    const runSource = await findRunSource(options, decodeURIComponent(parts[3]));
    const artifactKey = decodeURIComponent(parts[5]);
    const artifactFile = artifactAliases.get(artifactKey) || artifactKey;
    if (!runSource || !artifactAliases.has(artifactKey)) {
      jsonResponse(response, 404, { ok: false, error: "artifact_not_found" });
      return;
    }
    const runPath = runSource.artifactRoot;
    let filePath = path.join(runPath, artifactFile);
    if (artifactKey === "trace" && !(await pathExists(filePath))) {
      filePath = path.join(runPath, "trace_excerpt.json");
    }
    if (!isInsideRoot(runPath, filePath) || !(await pathExists(filePath))) {
      jsonResponse(response, 404, { ok: false, error: "artifact_not_found" });
      return;
    }
    const extension = path.extname(filePath);
    response.writeHead(200, {
      "Content-Type": contentTypes.get(extension) || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    response.end(await readFile(filePath));
    return;
  }

  if (request.method === "POST" && url.pathname === "/api/dashboard/pr-checks/run") {
    const body = await readBody(request);
    const mode = body.mode === "safe" ? "safe" : "unsafe";
    const scenarioId = body.scenarioId || "SAAS-003";
    if (scenarioId !== "SAAS-003") {
      jsonResponse(response, 400, {
        ok: false,
        error: "unsupported_scenario",
        message: "Dashboard live run currently supports SAAS-003.",
      });
      return;
    }
    jsonResponse(response, 200, { ok: true, run: await runSaas003(options, mode) });
    return;
  }

  jsonResponse(response, 404, { ok: false, error: "not_found" });
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  let liveChild = null;
  try {
    liveChild = await startLiveServer(options);
  } catch (error) {
    console.error(`[dashboard-api] ${error.message}`);
  }

  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url || "/", `http://${options.host}:${options.port}`);
      if (url.pathname.startsWith("/api/dashboard/")) {
        await handleApi(options, request, response);
        return;
      }
      if (await sendStatic(options, request, response, url)) {
        return;
      }
      textResponse(response, 404, "Not found");
    } catch (error) {
      jsonResponse(response, 500, {
        ok: false,
        error: "dashboard_api_error",
        message: error.message,
      });
    }
  });

  server.listen(options.port, options.host, () => {
    console.log(`HyTri dashboard API: http://${options.host}:${options.port}`);
    console.log(`Runs directory: ${options.runsDir}`);
    if (options.staticDir) {
      console.log(`Serving dashboard build from ${options.staticDir}`);
    }
  });

  const shutdown = () => {
    server.close();
    if (liveChild) liveChild.kill("SIGTERM");
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main();
