#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage3-mcp.XXXXXX")"

cleanup() {
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

python3 - "$RUNS_DIR" <<'PY'
import pathlib
import sys

from commerce_safety.live.mcp_tools import CommerceMCPTools

runs_dir = pathlib.Path(sys.argv[1])
scenario_path = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"
tools = CommerceMCPTools(runs_dir=runs_dir)
tool_names = {tool["name"] for tool in tools.list_tools()}
required_tools = {
    "commerce.start_session",
    "commerce.get_task",
    "commerce.create_fulfillment",
    "commerce.find_fulfillment",
    "commerce.complete_session",
    "commerce.get_trace",
    "commerce.get_policy_report",
    "commerce.get_patch_hints",
}
missing = required_tools - tool_names
if missing:
    raise SystemExit(f"missing MCP tools: {sorted(missing)}")


def start():
    return tools.call_tool(
        "commerce.start_session",
        {"scenario_path": scenario_path},
    )["session_id"]


def task(session_id):
    result = tools.call_tool("commerce.get_task", {"session_id": session_id})
    if result.get("done") or not result.get("task"):
        raise SystemExit("expected SCN-002 task")
    return result["task"]


bad_session = start()
bad_task = task(bad_session)
first = tools.call_tool(
    "commerce.create_fulfillment",
    {
        "session_id": bad_session,
        "order_id": bad_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "mcp_bad_agent",
        "request_id": "mcp_req_timeout_1",
        "source_event_id": bad_task["id"],
        "fault_type": bad_task["fault"]["type"],
    },
)
if first.get("error") != "timeout_after_commit":
    raise SystemExit(f"expected timeout_after_commit: {first}")
retry = tools.call_tool(
    "commerce.create_fulfillment",
    {
        "session_id": bad_session,
        "order_id": bad_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "mcp_bad_agent",
        "request_id": "mcp_req_retry_2",
        "source_event_id": bad_task["id"],
    },
)
if retry["fulfillment"]["fulfillment_id"] != "ful_002":
    raise SystemExit(f"expected duplicate fulfillment: {retry}")
bad_complete = tools.call_tool(
    "commerce.complete_session",
    {"session_id": bad_session, "runner_name": "mcp_bad_agent"},
)
if bad_complete["status"] != "failed":
    raise SystemExit(f"bad MCP path should fail: {bad_complete}")
bad_policy_ids = {finding["policy_id"] for finding in bad_complete["findings"]}
expected = {"idempotency_required_for_mutating_retries", "no_duplicate_fulfillment"}
if not expected.issubset(bad_policy_ids):
    raise SystemExit(f"missing MCP bad findings: {sorted(expected - bad_policy_ids)}")
if not tools.call_tool("commerce.get_patch_hints", {"session_id": bad_session})["hints"]:
    raise SystemExit("bad MCP path should produce patch hints")

good_session = start()
good_task = task(good_session)
stable_key = f"{good_task['order_id']}:sku_retry_1:create_fulfillment"
first = tools.call_tool(
    "commerce.create_fulfillment",
    {
        "session_id": good_session,
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "mcp_good_agent",
        "idempotency_key": stable_key,
        "request_id": "mcp_req_timeout_1",
        "source_event_id": good_task["id"],
        "fault_type": good_task["fault"]["type"],
    },
)
if first.get("error") != "timeout_after_commit":
    raise SystemExit(f"expected good timeout_after_commit: {first}")
found = tools.call_tool(
    "commerce.find_fulfillment",
    {
        "session_id": good_session,
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "idempotency_key": stable_key,
    },
)
if found["fulfillment"]["fulfillment_id"] != "ful_001":
    raise SystemExit(f"expected find_fulfillment to see committed fulfillment: {found}")
replay = tools.call_tool(
    "commerce.create_fulfillment",
    {
        "session_id": good_session,
        "order_id": good_task["order_id"],
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "mcp_good_agent",
        "idempotency_key": stable_key,
        "request_id": "mcp_req_retry_2",
        "source_event_id": good_task["id"],
    },
)
if replay["fulfillment"]["fulfillment_id"] != "ful_001":
    raise SystemExit(f"expected idempotency replay: {replay}")
good_complete = tools.call_tool(
    "commerce.complete_session",
    {"session_id": good_session, "runner_name": "mcp_good_agent"},
)
if good_complete["status"] != "passed" or good_complete["findings"]:
    raise SystemExit(f"good MCP path should pass: {good_complete}")

print("Stage 3 MCP SCN-002 gate passed.")
PY
