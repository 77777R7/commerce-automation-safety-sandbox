#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage9-api.XXXXXX")"
PYTHON_BIN="${PYTHON:-python3}"
LOG_FILE="$RUNS_DIR/live-server.log"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

PORT="$("$PYTHON_BIN" - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
BASE_URL="http://127.0.0.1:$PORT"

"$PYTHON_BIN" ./commerce-safety \
  --runs-dir "$RUNS_DIR/runs" \
  live serve \
  --port "$PORT" \
  >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

if ! "$PYTHON_BIN" - "$BASE_URL" <<'PY'
import sys
import time
import urllib.error
import urllib.request

base_url = sys.argv[1]
deadline = time.time() + 90
while time.time() < deadline:
    try:
        urllib.request.urlopen(f"{base_url}/sessions/not-real/trace", timeout=0.5)
    except urllib.error.HTTPError:
        raise SystemExit(0)
    except Exception:
        time.sleep(0.1)
raise SystemExit("live server did not become ready")
PY
then
  cat "$LOG_FILE" >&2 || true
  exit 1
fi

SCHEMATHESIS_BIN="${SCHEMATHESIS:-$(dirname "$PYTHON_BIN")/schemathesis}"
if [[ ! -x "$SCHEMATHESIS_BIN" ]]; then
  SCHEMATHESIS_BIN="$(command -v schemathesis || true)"
fi
if [[ -z "$SCHEMATHESIS_BIN" || ! -x "$SCHEMATHESIS_BIN" ]]; then
  echo "Schemathesis executable not found. Install requirements with Python 3.10+." >&2
  exit 1
fi

FIXTURE_VALUES="$RUNS_DIR/schemathesis-fixtures.json"
FIXTURE_SPEC="$RUNS_DIR/live_twin_api.schemathesis.yaml"
SCHEMATHESIS_LOG="$RUNS_DIR/schemathesis.log"

"$PYTHON_BIN" - "$BASE_URL" "$FIXTURE_VALUES" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request


BASE_URL = sys.argv[1]
FIXTURE_VALUES = pathlib.Path(sys.argv[2])
SCENARIOS = {
    "SCN-001": {
        "scenario_path": "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml"
    },
    "SCN-002": {"scenario_id": "SCN-002"},
    "SCN-003": {"scenario_id": "SCN-003"},
    "SCN-004": {"scenario_id": "SCN-004"},
    "SCN-005": {"scenario_id": "SCN-005"},
    "SAAS-001": {"scenario_id": "SAAS-001"},
    "SAAS-003": {"scenario_id": "SAAS-003"},
    "LIFECYCLE_STATUS": {"scenario_id": "SAAS-003", "ttl_seconds": 300},
    "LIFECYCLE_RESET": {"scenario_id": "SAAS-003", "ttl_seconds": 300},
    "LIFECYCLE_TEARDOWN": {"scenario_id": "SAAS-003", "ttl_seconds": 300},
}


def request(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


sessions = {}
for scenario_id, payload in SCENARIOS.items():
    status, body = request("POST", "/sessions", payload)
    assert status == 201, body
    sessions[scenario_id] = body["session_id"]

status, feed = request(
    "POST",
    f"/sessions/{sessions['SCN-003']}/amazon/sp-api/feeds/2021-06-30/feeds",
    {
        "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
        "messages": [{"sellerSku": "SELLER-0001", "quantity": 0}],
        "actor": "schemathesis_fixture_setup",
    },
)
assert status == 202, feed

FIXTURE_VALUES.write_text(
    json.dumps(
        {
            "sessions": sessions,
            "feed_id": feed["payload"]["feedId"],
        },
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)
PY

"$PYTHON_BIN" tools/build_schemathesis_fixture_spec.py \
  --source docs/openapi/live_twin_api.yaml \
  --fixtures-json "$FIXTURE_VALUES" \
  --output "$FIXTURE_SPEC"

if ! "$SCHEMATHESIS_BIN" run "$FIXTURE_SPEC" \
  --url "$BASE_URL" \
  --phases=examples,coverage,stateful \
  --checks=status_code_conformance,content_type_conformance,response_schema_conformance \
  --mode=positive \
  --max-examples=2 \
  --generation-deterministic \
  --request-timeout=5 \
  --no-color \
  >"$SCHEMATHESIS_LOG" 2>&1
then
  cat "$SCHEMATHESIS_LOG" >&2
  exit 1
fi

cat "$SCHEMATHESIS_LOG"

if grep -qE "WARNINGS|Missing test data|Schema validation mismatch" "$SCHEMATHESIS_LOG"; then
  echo "Schemathesis emitted contract warnings; update fixtures or schema instead of allowlisting." >&2
  exit 1
fi

"$PYTHON_BIN" - "$BASE_URL" "$RUNS_DIR" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request


BASE_URL = sys.argv[1]
RUNS_DIR = pathlib.Path(sys.argv[2])
SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def request(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def start_session():
    status, body = request("POST", "/sessions", {"scenario_path": SCN002})
    assert status == 201, body
    return body["session_id"]


def next_task(session_id: str):
    status, body = request("GET", f"/sessions/{session_id}/tasks/next")
    assert status == 200, body
    assert body["task"]["id"] == "task_fulfill_2001"
    return body["task"]


bad_session = start_session()
bad_task = next_task(bad_session)
status, body = request(
    "POST",
    f"/sessions/{bad_session}/twin/create_fulfillment",
    {
        "order_id": bad_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "schemathesis_bad_agent",
        "request_id": "schema_req_timeout_1",
        "source_event_id": bad_task["id"],
        "fault_type": bad_task["fault"]["type"],
    },
)
assert status == 504, body
assert body["error"] == "timeout_after_commit"

status, body = request(
    "POST",
    f"/sessions/{bad_session}/twin/create_fulfillment",
    {
        "order_id": bad_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "schemathesis_bad_agent",
        "request_id": "schema_req_retry_2",
        "source_event_id": bad_task["id"],
    },
)
assert status == 200, body
assert body["fulfillment"]["fulfillment_id"] == "ful_002"
status, body = request(
    "POST",
    f"/sessions/{bad_session}/complete",
    {"runner_name": "schemathesis_bad_agent"},
)
assert status == 200, body
assert body["status"] == "failed"
assert {finding["policy_id"] for finding in body["findings"]} >= {
    "idempotency_required_for_mutating_retries",
    "no_duplicate_fulfillment",
}

good_session = start_session()
good_task = next_task(good_session)
stable_key = f"{good_task['order_id']}:sku_retry_1:create_fulfillment"
status, body = request(
    "POST",
    f"/sessions/{good_session}/twin/create_fulfillment",
    {
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "schemathesis_good_agent",
        "idempotency_key": stable_key,
        "request_id": "schema_req_timeout_1",
        "source_event_id": good_task["id"],
        "fault_type": good_task["fault"]["type"],
    },
)
assert status == 504, body
assert body["error"] == "timeout_after_commit"
status, body = request(
    "POST",
    f"/sessions/{good_session}/twin/create_fulfillment",
    {
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "schemathesis_good_agent",
        "idempotency_key": stable_key,
        "request_id": "schema_req_retry_2",
        "source_event_id": good_task["id"],
    },
)
assert status == 200, body
assert body["fulfillment"]["fulfillment_id"] == "ful_001"
status, body = request(
    "POST",
    f"/sessions/{good_session}/complete",
    {"runner_name": "schemathesis_good_agent"},
)
assert status == 200, body
assert body["status"] == "passed"
assert body["findings"] == []

assert list((RUNS_DIR / "runs").glob("sess_*")), "expected live run artifacts"
PY

echo "Stage 9 API hardening gate passed."
