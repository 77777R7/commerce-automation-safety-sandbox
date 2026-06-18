#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
RUNS_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-saas001-runs.XXXXXX")"
SERVER_LOG="$(mktemp "${TMPDIR:-/tmp}/commerce-safety-saas001-http.XXXXXX.log")"
PORT="$((20765 + (RANDOM % 1000)))"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$RUNS_ROOT"
  rm -f "$SERVER_LOG"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"
export PYTHONPYCACHEPREFIX="$RUNS_ROOT/pycache"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

"$PYTHON_BIN" -m pytest \
  tests/test_saas001_agent_surfaces.py \
  tests/test_saas001_demo_pack.py \
  tests/test_cli_ux.py

"$PYTHON_BIN" tools/generate_saas001_demo_pack.py \
  --output-dir "$RUNS_ROOT/generated_sample_outputs" >/dev/null

HTTP_RUNS="$RUNS_ROOT/http"
MCP_RUNS="$RUNS_ROOT/mcp"
mkdir -p "$HTTP_RUNS" "$MCP_RUNS"

"$PYTHON_BIN" "$ROOT_DIR/commerce-safety" --runs-dir "$HTTP_RUNS" live serve \
  --host 127.0.0.1 \
  --port "$PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

"$PYTHON_BIN" - "http://127.0.0.1:$PORT" "$SERVER_PID" <<'PY'
import os
import sys
import time
import urllib.error
import urllib.request

base_url = sys.argv[1]
server_pid = int(sys.argv[2])
deadline = time.time() + 90

while time.time() < deadline:
    try:
        urllib.request.urlopen(f"{base_url}/sessions/not-real/trace", timeout=0.5)
    except urllib.error.HTTPError:
        raise SystemExit(0)
    except Exception:
        try:
            os.kill(server_pid, 0)
        except OSError:
            raise SystemExit("live server exited before it was ready")
        time.sleep(0.1)

raise SystemExit("live server did not become ready")
PY

HTTP_BAD_JSON="$RUNS_ROOT/http_bad.json"
HTTP_SAFE_JSON="$RUNS_ROOT/http_safe.json"
"$PYTHON_BIN" examples/agent_integrations/http_saas001_failed_payment_agent.py \
  --base-url "http://127.0.0.1:$PORT" \
  --mode unsafe \
  --json > "$HTTP_BAD_JSON"
"$PYTHON_BIN" examples/agent_integrations/http_saas001_failed_payment_agent.py \
  --base-url "http://127.0.0.1:$PORT" \
  --mode safe \
  --json > "$HTTP_SAFE_JSON"

MCP_BAD_JSON="$RUNS_ROOT/mcp_bad.json"
MCP_SAFE_JSON="$RUNS_ROOT/mcp_safe.json"
"$PYTHON_BIN" examples/agent_integrations/mcp_saas001_failed_payment_agent.py \
  --root "$ROOT_DIR" \
  --runs-dir "$MCP_RUNS" \
  --mode unsafe \
  --json > "$MCP_BAD_JSON"
"$PYTHON_BIN" examples/agent_integrations/mcp_saas001_failed_payment_agent.py \
  --root "$ROOT_DIR" \
  --runs-dir "$MCP_RUNS" \
  --mode safe \
  --json > "$MCP_SAFE_JSON"

"$PYTHON_BIN" - \
  "$HTTP_BAD_JSON" "$HTTP_SAFE_JSON" "$MCP_BAD_JSON" "$MCP_SAFE_JSON" <<'PY'
import json
import pathlib
import subprocess
import sys

expected_policies = {
    "no_success_state_after_failed_payment",
    "billing_failure_must_trigger_alert",
    "slack_permission_failure_must_not_be_silent",
    "github_check_must_match_policy_status",
}
json_paths = [pathlib.Path(path) for path in sys.argv[1:]]
expected = [
    ("http", "unsafe", "failed"),
    ("http", "safe", "passed"),
    ("mcp", "unsafe", "failed"),
    ("mcp", "safe", "passed"),
]
run_paths = []
for json_path, (surface, mode, status) in zip(json_paths, expected):
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["surface"] == surface, payload
    assert payload["scenario_id"] == "SAAS-001", payload
    assert payload["mode"] == mode, payload
    assert payload["status"] == status, payload
    if mode == "unsafe":
        assert expected_policies.issubset(set(payload["findings"])), payload
    else:
        assert payload["findings"] == [], payload
    run_paths.append(payload["run_path"])

subprocess.run(
    [sys.executable, "tools/check_run_manifest.py", *run_paths],
    check=True,
)
PY

echo "SAAS-001 demo pack gate passed."
