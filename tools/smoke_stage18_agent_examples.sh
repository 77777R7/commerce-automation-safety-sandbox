#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
RUNS_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage18-runs.XXXXXX")"
SERVER_LOG="$(mktemp "${TMPDIR:-/tmp}/commerce-safety-stage18-http.XXXXXX.log")"
PORT="$((19765 + (RANDOM % 1000)))"
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

"$PYTHON_BIN" -m pytest tests/test_stage18_agent_integration_examples.py

MCP_RUNS="$RUNS_ROOT/mcp"
HTTP_RUNS="$RUNS_ROOT/http"
ACTION_RUNS="$RUNS_ROOT/action-log"
mkdir -p "$MCP_RUNS" "$HTTP_RUNS" "$ACTION_RUNS"

MCP_BAD_JSON="$RUNS_ROOT/mcp_bad.json"
MCP_SAFE_JSON="$RUNS_ROOT/mcp_safe.json"
"$PYTHON_BIN" examples/agent_integrations/mcp_scn002_timeout_retry_agent.py \
  --root "$ROOT_DIR" \
  --runs-dir "$MCP_RUNS" \
  --mode unsafe \
  --json > "$MCP_BAD_JSON"
"$PYTHON_BIN" examples/agent_integrations/mcp_scn002_timeout_retry_agent.py \
  --root "$ROOT_DIR" \
  --runs-dir "$MCP_RUNS" \
  --mode safe \
  --json > "$MCP_SAFE_JSON"

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
"$PYTHON_BIN" examples/agent_integrations/http_scn002_timeout_retry_agent.py \
  --base-url "http://127.0.0.1:$PORT" \
  --mode unsafe \
  --json > "$HTTP_BAD_JSON"
"$PYTHON_BIN" examples/agent_integrations/http_scn002_timeout_retry_agent.py \
  --base-url "http://127.0.0.1:$PORT" \
  --mode safe \
  --json > "$HTTP_SAFE_JSON"

ACTION_BAD_JSON="$RUNS_ROOT/action_bad.json"
ACTION_SAFE_JSON="$RUNS_ROOT/action_safe.json"
set +e
"$PYTHON_BIN" ./commerce-safety --runs-dir "$ACTION_RUNS" gate \
  --scenario commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml \
  --action-log examples/agent_integrations/action_logs/scn004_refund_bad.jsonl \
  --runner-name example_action_log_unsafe_agent \
  --json > "$ACTION_BAD_JSON"
bad_status=$?
set -e
if [[ "$bad_status" -ne 1 ]]; then
  cat "$ACTION_BAD_JSON" >&2
  echo "FAIL: unsafe action-log example should exit 1" >&2
  exit 1
fi

"$PYTHON_BIN" ./commerce-safety --runs-dir "$ACTION_RUNS" gate \
  --scenario commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml \
  --action-log examples/agent_integrations/action_logs/scn004_refund_safe.jsonl \
  --runner-name example_action_log_safe_agent \
  --json > "$ACTION_SAFE_JSON"

"$PYTHON_BIN" - \
  "$MCP_BAD_JSON" "$MCP_SAFE_JSON" \
  "$HTTP_BAD_JSON" "$HTTP_SAFE_JSON" \
  "$ACTION_BAD_JSON" "$ACTION_SAFE_JSON" <<'PY'
import json
import pathlib
import subprocess
import sys

json_paths = [pathlib.Path(path) for path in sys.argv[1:]]
expected = [
    ("mcp", "unsafe", "failed"),
    ("mcp", "safe", "passed"),
    ("http", "unsafe", "failed"),
    ("http", "safe", "passed"),
    ("action-log", "unsafe", "failed"),
    ("action-log", "safe", "passed"),
]
run_paths = []
for json_path, (surface, mode, status) in zip(json_paths, expected):
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if surface != "action-log":
        assert payload["surface"] == surface, payload
        assert payload["mode"] == mode, payload
    assert payload["status"] == status, payload
    if mode == "unsafe":
        assert payload["findings"], payload
    else:
        assert payload["findings"] == [], payload
    run_paths.append(payload["run_path"])

subprocess.run(
    [sys.executable, "tools/check_run_manifest.py", *run_paths],
    check=True,
)
PY

echo "Stage 18 agent integration examples gate passed."
