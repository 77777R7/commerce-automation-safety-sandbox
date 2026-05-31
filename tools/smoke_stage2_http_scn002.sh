#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage2-runs.XXXXXX")"
SERVER_LOG="$(mktemp "${TMPDIR:-/tmp}/commerce-safety-stage2-server.XXXXXX.log")"
CLI="$ROOT_DIR/commerce-safety"
PYTHON_BIN="${PYTHON:-python3}"
PORT="$((18765 + (RANDOM % 1000)))"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$RUNS_DIR"
  rm -f "$SERVER_LOG"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$PYTHON_BIN" "$CLI" --runs-dir "$RUNS_DIR" live serve --host 127.0.0.1 --port "$PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

if ! "$PYTHON_BIN" - "http://127.0.0.1:$PORT" "$SERVER_PID" <<'PY'
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
then
  cat "$SERVER_LOG" >&2
  exit 1
fi

"$PYTHON_BIN" - "$PORT" "$RUNS_DIR" <<'PY'
import json
import pathlib
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

port = int(sys.argv[1])
runs_dir = pathlib.Path(sys.argv[2])
base_url = f"http://127.0.0.1:{port}"
scenario_path = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def request(method, path, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def create_session():
    status, body = request("POST", "/sessions", {"scenario_path": scenario_path})
    if status != 201:
        raise SystemExit(f"create session failed: {status} {body}")
    return body["session_id"]


def next_task(session_id):
    status, body = request("GET", f"/sessions/{session_id}/tasks/next")
    if status != 200 or body.get("done"):
        raise SystemExit(f"next task failed: {status} {body}")
    return body["task"]


bad_session = create_session()
bad_task = next_task(bad_session)
status, body = request(
    "POST",
    f"/sessions/{bad_session}/twin/create_fulfillment",
    {
        "order_id": bad_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "external_bad_agent",
        "request_id": "http_req_timeout_1",
        "source_event_id": bad_task["id"],
        "fault_type": bad_task["fault"]["type"],
    },
)
if status != 504 or body.get("error") != "timeout_after_commit":
    raise SystemExit(f"expected timeout_after_commit: {status} {body}")
status, body = request(
    "POST",
    f"/sessions/{bad_session}/twin/create_fulfillment",
    {
        "order_id": bad_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "external_bad_agent",
        "request_id": "http_req_retry_2",
        "source_event_id": bad_task["id"],
    },
)
if status != 200 or body["fulfillment"]["fulfillment_id"] != "ful_002":
    raise SystemExit(f"expected duplicate fulfillment: {status} {body}")
status, bad_complete = request(
    "POST",
    f"/sessions/{bad_session}/complete",
    {"runner_name": "external_bad_agent"},
)
if status != 200 or bad_complete["status"] != "failed":
    raise SystemExit(f"bad external agent should fail: {status} {bad_complete}")
bad_policy_ids = {finding["policy_id"] for finding in bad_complete["findings"]}
expected = {"idempotency_required_for_mutating_retries", "no_duplicate_fulfillment"}
if not expected.issubset(bad_policy_ids):
    raise SystemExit(f"missing bad findings: {sorted(expected - bad_policy_ids)}")
bad_run_path = pathlib.Path(bad_complete["run_path"])
if not (bad_run_path / "patch_hints.json").is_file():
    raise SystemExit("bad external agent missing patch_hints.json")

good_session = create_session()
good_task = next_task(good_session)
stable_key = f"{good_task['order_id']}:sku_retry_1:create_fulfillment"
status, body = request(
    "POST",
    f"/sessions/{good_session}/twin/create_fulfillment",
    {
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "external_good_agent",
        "idempotency_key": stable_key,
        "request_id": "http_req_timeout_1",
        "source_event_id": good_task["id"],
        "fault_type": good_task["fault"]["type"],
    },
)
if status != 504 or body.get("error") != "timeout_after_commit":
    raise SystemExit(f"expected good timeout_after_commit: {status} {body}")
status, body = request(
    "POST",
    f"/sessions/{good_session}/twin/create_fulfillment",
    {
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "external_good_agent",
        "idempotency_key": stable_key,
        "request_id": "http_req_retry_2",
        "source_event_id": good_task["id"],
    },
)
if status != 200 or body["fulfillment"]["fulfillment_id"] != "ful_001":
    raise SystemExit(f"expected idempotency replay: {status} {body}")
status, good_complete = request(
    "POST",
    f"/sessions/{good_session}/complete",
    {"runner_name": "external_good_agent"},
)
if status != 200 or good_complete["status"] != "passed" or good_complete["findings"]:
    raise SystemExit(f"good external agent should pass: {status} {good_complete}")

if not any(runs_dir.iterdir()):
    raise SystemExit("expected live run artifacts in runs dir")

print("Stage 2 HTTP SCN-002 gate passed.")
PY
