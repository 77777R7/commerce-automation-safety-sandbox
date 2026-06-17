#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage9-mcp.XXXXXX")"
PYTHON_BIN="${PYTHON:-python3}"

cleanup() {
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$PYTHON_BIN" - "$ROOT_DIR" "$RUNS_DIR" <<'PY'
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = pathlib.Path(sys.argv[1])
RUNS_DIR = pathlib.Path(sys.argv[2])
SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def parse_result(result):
    structured = getattr(result, "structuredContent", None)
    if structured:
        if set(structured) == {"result"} and isinstance(structured["result"], str):
            return json.loads(structured["result"])
        return structured
    for content in result.content:
        if getattr(content, "type", None) == "text":
            return json.loads(content.text)
    raise AssertionError(f"could not parse MCP result: {result!r}")


async def call(session, name, arguments):
    return parse_result(await session.call_tool(name, arguments))


async def run():
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'commerce-safety-sandbox'}:{env.get('PYTHONPATH', '')}"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "commerce_safety.live.mcp_server",
            "--runs-dir",
            str(RUNS_DIR),
        ],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            required = {
                "commerce.start_session",
                "commerce.get_task",
                "commerce.create_fulfillment",
                "commerce.find_fulfillment",
                "commerce.complete_session",
                "commerce.get_trace",
                "commerce.get_policy_report",
                "commerce.get_patch_hints",
                "stripe.create_customer",
                "stripe.create_subscription",
                "slack.post_message",
                "github.create_check_run",
                "github.create_issue",
                "github.comment_on_pr",
            }
            missing = required - names
            if missing:
                raise AssertionError(f"missing real MCP tools: {sorted(missing)}")

            bad = await call(
                session,
                "commerce.start_session",
                {"scenario_path": SCN002},
            )
            bad_session = bad["session_id"]
            bad_task = (
                await call(session, "commerce.get_task", {"session_id": bad_session})
            )["task"]

            first = await call(
                session,
                "commerce.create_fulfillment",
                {
                    "session_id": bad_session,
                    "order_id": bad_task["order_id"],
                    "sku": "sku_retry_1",
                    "quantity": 1,
                    "actor": "real_mcp_bad_agent",
                    "request_id": "real_mcp_req_timeout_1",
                    "source_event_id": bad_task["id"],
                    "fault_type": bad_task["fault"]["type"],
                },
            )
            if first.get("error") != "timeout_after_commit":
                raise AssertionError(f"expected timeout_after_commit: {first}")

            retry = await call(
                session,
                "commerce.create_fulfillment",
                {
                    "session_id": bad_session,
                    "order_id": bad_task["order_id"],
                    "sku": "sku_retry_1",
                    "quantity": 1,
                    "actor": "real_mcp_bad_agent",
                    "request_id": "real_mcp_req_retry_2",
                    "source_event_id": bad_task["id"],
                },
            )
            if retry["fulfillment"]["fulfillment_id"] != "ful_002":
                raise AssertionError(f"expected duplicate fulfillment: {retry}")

            bad_complete = await call(
                session,
                "commerce.complete_session",
                {"session_id": bad_session, "runner_name": "real_mcp_bad_agent"},
            )
            if bad_complete["status"] != "failed":
                raise AssertionError(f"unsafe MCP path should fail: {bad_complete}")
            policy_ids = {finding["policy_id"] for finding in bad_complete["findings"]}
            expected = {
                "idempotency_required_for_mutating_retries",
                "no_duplicate_fulfillment",
            }
            if not expected.issubset(policy_ids):
                raise AssertionError(f"missing policy findings: {policy_ids}")
            patch_hints = await call(
                session,
                "commerce.get_patch_hints",
                {"session_id": bad_session},
            )
            if not patch_hints["hints"]:
                raise AssertionError("unsafe MCP path should produce patch hints")

            good = await call(
                session,
                "commerce.start_session",
                {"scenario_path": SCN002},
            )
            good_session = good["session_id"]
            good_task = (
                await call(session, "commerce.get_task", {"session_id": good_session})
            )["task"]
            stable_key = f"{good_task['order_id']}:sku_retry_1:create_fulfillment"

            first = await call(
                session,
                "commerce.create_fulfillment",
                {
                    "session_id": good_session,
                    "order_id": good_task["order_id"],
                    "sku": "sku_retry_1",
                    "quantity": 1,
                    "actor": "real_mcp_good_agent",
                    "idempotency_key": stable_key,
                    "request_id": "real_mcp_req_timeout_1",
                    "source_event_id": good_task["id"],
                    "fault_type": good_task["fault"]["type"],
                },
            )
            if first.get("error") != "timeout_after_commit":
                raise AssertionError(f"expected safe timeout_after_commit: {first}")

            found = await call(
                session,
                "commerce.find_fulfillment",
                {
                    "session_id": good_session,
                    "order_id": good_task["order_id"],
                    "sku": "sku_retry_1",
                    "idempotency_key": stable_key,
                },
            )
            if found["fulfillment"]["fulfillment_id"] != "ful_001":
                raise AssertionError(f"expected committed fulfillment: {found}")

            replay = await call(
                session,
                "commerce.create_fulfillment",
                {
                    "session_id": good_session,
                    "order_id": good_task["order_id"],
                    "sku": "sku_retry_1",
                    "quantity": 1,
                    "actor": "real_mcp_good_agent",
                    "idempotency_key": stable_key,
                    "request_id": "real_mcp_req_retry_2",
                    "source_event_id": good_task["id"],
                },
            )
            if replay["fulfillment"]["fulfillment_id"] != "ful_001":
                raise AssertionError(f"expected idempotent replay: {replay}")

            good_complete = await call(
                session,
                "commerce.complete_session",
                {"session_id": good_session, "runner_name": "real_mcp_good_agent"},
            )
            if good_complete["status"] != "passed" or good_complete["findings"]:
                raise AssertionError(f"safe MCP path should pass: {good_complete}")


asyncio.run(run())
print("Stage 9 real MCP server gate passed.")
PY
