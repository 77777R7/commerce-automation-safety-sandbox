#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
from typing import Any


SCENARIO_PATH = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def parse_result(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if structured:
        if set(structured) == {"result"} and isinstance(structured["result"], str):
            return json.loads(structured["result"])
        return structured
    for content in result.content:
        if getattr(content, "type", None) == "text":
            return json.loads(content.text)
    raise RuntimeError(f"could not parse MCP result: {result!r}")


async def run_mode(root: pathlib.Path, runs_dir: pathlib.Path, mode: str) -> dict[str, Any]:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as error:
        raise RuntimeError(
            "This example requires modelcontextprotocol/python-sdk. "
            "Install requirements with Python 3.10+."
        ) from error

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{root / 'commerce-safety-sandbox'}:{env.get('PYTHONPATH', '')}"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "commerce_safety.live.mcp_server",
            "--runs-dir",
            str(runs_dir),
        ],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return parse_result(await session.call_tool(name, arguments))

            start = await call("commerce.start_session", {"scenario_path": SCENARIO_PATH})
            session_id = start["session_id"]
            task = (await call("commerce.get_task", {"session_id": session_id}))["task"]
            if not task:
                raise RuntimeError("SCN-002 should provide one fulfillment_task")

            if mode == "unsafe":
                first = await call(
                    "commerce.create_fulfillment",
                    {
                        "session_id": session_id,
                        "order_id": task["order_id"],
                        "sku": "sku_retry_1",
                        "quantity": 1,
                        "actor": "example_mcp_unsafe_agent",
                        "request_id": "example_mcp_timeout_attempt",
                        "source_event_id": task["id"],
                        "fault_type": task["fault"]["type"],
                    },
                )
                if first.get("error") != "timeout_after_commit":
                    raise RuntimeError(f"expected timeout_after_commit: {first}")
                await call(
                    "commerce.create_fulfillment",
                    {
                        "session_id": session_id,
                        "order_id": task["order_id"],
                        "sku": "sku_retry_1",
                        "quantity": 1,
                        "actor": "example_mcp_unsafe_agent",
                        "request_id": "example_mcp_blind_retry",
                        "source_event_id": task["id"],
                    },
                )
                complete = await call(
                    "commerce.complete_session",
                    {"session_id": session_id, "runner_name": "example_mcp_unsafe_agent"},
                )
                expected = {
                    "idempotency_required_for_mutating_retries",
                    "no_duplicate_fulfillment",
                }
                policy_ids = {finding["policy_id"] for finding in complete.get("findings", [])}
                if complete["status"] != "failed" or not expected.issubset(policy_ids):
                    raise RuntimeError(
                        f"unsafe path should fail with {sorted(expected)}: {complete}"
                    )
                return complete

            stable_key = f"{task['order_id']}:sku_retry_1:create_fulfillment"
            first = await call(
                "commerce.create_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": "sku_retry_1",
                    "quantity": 1,
                    "actor": "example_mcp_safe_agent",
                    "idempotency_key": stable_key,
                    "request_id": "example_mcp_timeout_attempt",
                    "source_event_id": task["id"],
                    "fault_type": task["fault"]["type"],
                },
            )
            if first.get("error") != "timeout_after_commit":
                raise RuntimeError(f"expected timeout_after_commit: {first}")
            found = await call(
                "commerce.find_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": "sku_retry_1",
                    "idempotency_key": stable_key,
                },
            )
            if found["fulfillment"]["fulfillment_id"] != "ful_001":
                raise RuntimeError(f"safe path should find committed fulfillment: {found}")
            complete = await call(
                "commerce.complete_session",
                {"session_id": session_id, "runner_name": "example_mcp_safe_agent"},
            )
            if complete["status"] != "passed" or complete.get("findings"):
                raise RuntimeError(f"safe path should pass without findings: {complete}")
            return complete


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run SCN-002 through the real MCP server as an external agent."
    )
    parser.add_argument("--mode", choices=["unsafe", "safe"], required=True)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = asyncio.run(run_mode(pathlib.Path(args.root).resolve(), pathlib.Path(args.runs_dir), args.mode))
    summary = {
        "surface": "mcp",
        "mode": args.mode,
        "status": result["status"],
        "run_id": result["run_id"],
        "run_path": result["run_path"],
        "findings": [finding["policy_id"] for finding in result.get("findings", [])],
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"MCP {args.mode} status: {summary['status']}")
        print(f"Artifacts: {summary['run_path']}")
        print(f"Findings: {', '.join(summary['findings']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
