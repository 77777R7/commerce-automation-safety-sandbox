from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


P0_SCENARIOS: list[tuple[str, set[str]]] = [
    (
        "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml",
        {"no_duplicate_fulfillment", "webhook_dedup_required"},
    ),
    (
        "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml",
        {"idempotency_required_for_mutating_retries", "no_duplicate_fulfillment"},
    ),
    (
        "commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml",
        {
            "reservation_required_before_promise",
            "no_inventory_commit_from_stale_snapshot",
            "no_oversell",
        },
    ),
    (
        "commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml",
        {
            "no_refund_after_shipment_without_approval",
            "high_value_refund_requires_approval",
        },
    ),
    (
        "commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml",
        {
            "warehouse_conflict_requires_hold",
            "no_ship_after_cancel",
            "no_double_refund_or_inventory_release",
        },
    ),
]


REQUIRED_P0_MCP_TOOLS = {
    "commerce.start_session",
    "commerce.get_task",
    "commerce.reserve_inventory",
    "commerce.promise_fulfillment",
    "commerce.refresh_inventory",
    "commerce.route_manual_review",
    "commerce.create_fulfillment",
    "commerce.find_fulfillment",
    "commerce.create_refund",
    "commerce.create_approval_request",
    "commerce.cancel_order",
    "commerce.release_inventory",
    "commerce.place_workflow_hold",
    "commerce.submit_warehouse_cancellation_request",
    "commerce.warehouse_continue_fulfillment",
    "commerce.skip_duplicate_webhook",
    "commerce.complete_session",
    "commerce.get_trace",
    "commerce.get_policy_report",
    "commerce.get_patch_hints",
}


AsyncCall = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def parse_mcp_result(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if structured:
        if set(structured) == {"result"} and isinstance(structured["result"], str):
            return json.loads(structured["result"])
        return structured
    for content in result.content:
        if getattr(content, "type", None) == "text":
            return json.loads(content.text)
    raise AssertionError(f"could not parse MCP result: {result!r}")


async def start(call: AsyncCall, scenario_path: str) -> str:
    result = await call(
        "commerce.start_session",
        {"scenario_path": scenario_path},
    )
    return result["session_id"]


async def next_task(call: AsyncCall, session_id: str) -> dict[str, Any] | None:
    return (await call("commerce.get_task", {"session_id": session_id}))["task"]


async def line_item(call: AsyncCall, session_id: str, order_id: str) -> dict[str, Any]:
    trace = await call("commerce.get_trace", {"session_id": session_id})
    return trace["current_state"]["orders"][order_id]["line_items"][0]


async def complete(call: AsyncCall, session_id: str, runner_name: str) -> dict[str, Any]:
    return await call(
        "commerce.complete_session",
        {"session_id": session_id, "runner_name": runner_name},
    )


async def unsafe_path(call: AsyncCall, scenario_path: str) -> dict[str, Any]:
    session_id = await start(call, scenario_path)
    while True:
        task = await next_task(call, session_id)
        if task is None:
            break
        item = await line_item(call, session_id, task["order_id"])
        if task["type"] == "webhook":
            await call(
                "commerce.reserve_inventory",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_unsafe_agent",
                    "webhook_id": task["id"],
                },
            )
            await call(
                "commerce.create_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_unsafe_agent",
                    "webhook_id": task["id"],
                    "source_event_id": task["id"],
                },
            )
        elif task["type"] == "fulfillment_task":
            first = await call(
                "commerce.create_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_unsafe_agent",
                    "request_id": f"{task['id']}:attempt_1",
                    "source_event_id": task["id"],
                    "fault_type": task["fault"]["type"],
                },
            )
            if first.get("error") != "timeout_after_commit":
                raise AssertionError(f"expected timeout_after_commit: {first}")
            await call(
                "commerce.create_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_unsafe_agent",
                    "request_id": f"{task['id']}:attempt_2",
                    "source_event_id": task["id"],
                },
            )
        elif task["type"] == "inventory_promise_task":
            await call(
                "commerce.promise_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_unsafe_agent",
                    "source_event_id": task["id"],
                },
            )
        elif task["type"] == "refund_request":
            await call(
                "commerce.create_refund",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "amount": task["amount"],
                    "reason": task["reason"],
                    "actor": "stage10_unsafe_agent",
                    "source_event_id": task["id"],
                },
            )
        elif task["type"] == "cancel_request":
            for tool_name, payload in [
                ("commerce.cancel_order", {"order_id": task["order_id"]}),
                (
                    "commerce.release_inventory",
                    {
                        "order_id": task["order_id"],
                        "sku": item["sku"],
                        "quantity": item["quantity"],
                    },
                ),
                (
                    "commerce.create_refund",
                    {
                        "order_id": task["order_id"],
                        "amount": task["amount"],
                        "reason": task["reason"],
                    },
                ),
                (
                    "commerce.warehouse_continue_fulfillment",
                    {"order_id": task["order_id"], "new_status": "shipped"},
                ),
            ]:
                await call(
                    tool_name,
                    {
                        "session_id": session_id,
                        **payload,
                        "actor": "stage10_unsafe_agent",
                        "source_event_id": task["id"],
                    },
                )
    return await complete(call, session_id, "stage10_unsafe_agent")


async def safe_path(call: AsyncCall, scenario_path: str) -> dict[str, Any]:
    session_id = await start(call, scenario_path)
    seen_webhooks = set()
    while True:
        task = await next_task(call, session_id)
        if task is None:
            break
        item = await line_item(call, session_id, task["order_id"])
        if task["type"] == "webhook":
            if task["id"] in seen_webhooks:
                await call(
                    "commerce.skip_duplicate_webhook",
                    {
                        "session_id": session_id,
                        "actor": "stage10_safe_agent",
                        "webhook": task,
                    },
                )
                continue
            seen_webhooks.add(task["id"])
            await call(
                "commerce.reserve_inventory",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_safe_agent",
                    "webhook_id": task["id"],
                },
            )
            await call(
                "commerce.create_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_safe_agent",
                    "webhook_id": task["id"],
                    "idempotency_key": f"fulfillment:{task['order_id']}:{item['sku']}",
                    "source_event_id": task["id"],
                },
            )
        elif task["type"] == "fulfillment_task":
            stable_key = f"fulfillment:{task['order_id']}:{item['sku']}:create"
            first = await call(
                "commerce.create_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "actor": "stage10_safe_agent",
                    "idempotency_key": stable_key,
                    "request_id": f"{task['id']}:attempt_1",
                    "source_event_id": task["id"],
                    "fault_type": task["fault"]["type"],
                },
            )
            if first.get("error") != "timeout_after_commit":
                raise AssertionError(f"expected timeout_after_commit: {first}")
            found = await call(
                "commerce.find_fulfillment",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "idempotency_key": stable_key,
                },
            )
            if found["fulfillment"]["fulfillment_id"] != "ful_001":
                raise AssertionError(f"expected committed fulfillment: {found}")
        elif task["type"] == "inventory_promise_task":
            inventory = (
                await call(
                    "commerce.refresh_inventory",
                    {
                        "session_id": session_id,
                        "sku": item["sku"],
                        "actor": "stage10_safe_agent",
                    },
                )
            )["inventory"]
            if (inventory["available"] or 0) < item["quantity"]:
                await call(
                    "commerce.route_manual_review",
                    {
                        "session_id": session_id,
                        "order_id": task["order_id"],
                        "sku": item["sku"],
                        "actor": "stage10_safe_agent",
                        "reason": "fresh_inventory_unavailable",
                        "source_event_id": task["id"],
                    },
                )
            else:
                reservation = (
                    await call(
                        "commerce.reserve_inventory",
                        {
                            "session_id": session_id,
                            "order_id": task["order_id"],
                            "sku": item["sku"],
                            "quantity": item["quantity"],
                            "actor": "stage10_safe_agent",
                        },
                    )
                )["reservation"]
                await call(
                    "commerce.promise_fulfillment",
                    {
                        "session_id": session_id,
                        "order_id": task["order_id"],
                        "sku": item["sku"],
                        "quantity": item["quantity"],
                        "actor": "stage10_safe_agent",
                        "source_event_id": task["id"],
                        "reservation_id": reservation["reservation_id"],
                    },
                )
        elif task["type"] == "refund_request":
            await call(
                "commerce.create_approval_request",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "amount": task["amount"],
                    "reason": task["reason"],
                    "actor": "stage10_safe_agent",
                    "source_event_id": task["id"],
                    "required_policy": "no_refund_after_shipment_without_approval",
                },
            )
        elif task["type"] == "cancel_request":
            await call(
                "commerce.place_workflow_hold",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "sku": item["sku"],
                    "reason": "warehouse_pick_pack_conflict",
                    "actor": "stage10_safe_agent",
                    "source_event_id": task["id"],
                },
            )
            await call(
                "commerce.submit_warehouse_cancellation_request",
                {
                    "session_id": session_id,
                    "order_id": task["order_id"],
                    "actor": "stage10_safe_agent",
                    "source_event_id": task["id"],
                },
            )
    return await complete(call, session_id, "stage10_safe_agent")


async def run_all_p0(call: AsyncCall) -> None:
    for scenario_path, expected_findings in P0_SCENARIOS:
        unsafe = await unsafe_path(call, scenario_path)
        if unsafe["status"] != "failed":
            raise AssertionError(f"unsafe path should fail for {scenario_path}: {unsafe}")
        policy_ids = {finding["policy_id"] for finding in unsafe["findings"]}
        missing = expected_findings - policy_ids
        if missing:
            raise AssertionError(f"{scenario_path} missing findings: {sorted(missing)}")

        safe = await safe_path(call, scenario_path)
        if safe["status"] != "passed" or safe["findings"]:
            raise AssertionError(f"safe path should pass for {scenario_path}: {safe}")


async def run_mcp(root: pathlib.Path, runs_dir: pathlib.Path) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

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
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            missing = REQUIRED_P0_MCP_TOOLS - names
            if missing:
                raise AssertionError(f"missing Stage 10 MCP tools: {sorted(missing)}")

            async def call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
                return parse_mcp_result(await session.call_tool(name, arguments))

            await run_all_p0(call)


async def run_http(base_url: str) -> None:
    def request(method: str, path: str, payload: dict[str, Any] | None = None):
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

    async def call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        session_id = arguments.get("session_id")
        if name == "commerce.start_session":
            status, body = request("POST", "/sessions", arguments)
            if status != 201:
                raise AssertionError(f"start_session failed: {status} {body}")
            return body
        if name == "commerce.get_task":
            status, body = request("GET", f"/sessions/{session_id}/tasks/next")
        elif name == "commerce.get_trace":
            status, body = request("GET", f"/sessions/{session_id}/trace")
        elif name == "commerce.complete_session":
            status, body = request(
                "POST",
                f"/sessions/{session_id}/complete",
                {"runner_name": arguments.get("runner_name")},
            )
        else:
            action = name.removeprefix("commerce.")
            payload = {key: value for key, value in arguments.items() if key != "session_id"}
            status, body = request(
                "POST",
                f"/sessions/{session_id}/twin/{action}",
                payload,
            )
        if status not in {200, 504}:
            raise AssertionError(f"{name} failed: {status} {body}")
        return body

    await run_all_p0(call)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["mcp", "http"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--runs-dir", required=True)
    parser.add_argument("--base-url")
    args = parser.parse_args()

    root = pathlib.Path(args.root)
    if args.mode == "mcp":
        asyncio.run(run_mcp(root, pathlib.Path(args.runs_dir)))
    else:
        if not args.base_url:
            raise SystemExit("--base-url is required for http mode")
        asyncio.run(run_http(args.base_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
