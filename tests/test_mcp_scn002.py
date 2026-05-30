from __future__ import annotations

from pathlib import Path

from commerce_safety.live.mcp_tools import CommerceMCPTools


SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def test_mcp_tools_run_scn002_bad_path_without_cli_runner(tmp_path):
    tools = CommerceMCPTools(runs_dir=tmp_path)
    started = tools.call_tool("commerce.start_session", {"scenario_path": SCN002})
    session_id = started["session_id"]
    task = tools.call_tool("commerce.get_task", {"session_id": session_id})["task"]

    first = tools.call_tool(
        "commerce.create_fulfillment",
        {
            "session_id": session_id,
            "order_id": task["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "mcp_bad_agent",
            "request_id": "mcp_req_timeout_1",
            "source_event_id": task["id"],
            "fault_type": task["fault"]["type"],
        },
    )
    assert first["ok"] is False
    assert first["error"] == "timeout_after_commit"

    retry = tools.call_tool(
        "commerce.create_fulfillment",
        {
            "session_id": session_id,
            "order_id": task["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "mcp_bad_agent",
            "request_id": "mcp_req_retry_2",
            "source_event_id": task["id"],
        },
    )
    assert retry["ok"] is True
    assert retry["fulfillment"]["fulfillment_id"] == "ful_002"

    completed = tools.call_tool(
        "commerce.complete_session",
        {"session_id": session_id, "runner_name": "mcp_bad_agent"},
    )
    assert completed["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in completed["findings"]}
    assert "idempotency_required_for_mutating_retries" in policy_ids
    assert "no_duplicate_fulfillment" in policy_ids

    policy_report = tools.call_tool(
        "commerce.get_policy_report",
        {"session_id": session_id},
    )
    patch_hints = tools.call_tool(
        "commerce.get_patch_hints",
        {"session_id": session_id},
    )
    trace = tools.call_tool("commerce.get_trace", {"session_id": session_id})
    assert policy_report["status"] == "failed"
    assert len(patch_hints["hints"]) >= 2
    assert any(event["event"] == "fault_injected" for event in trace["timeline"])
    assert Path(completed["run_path"], "patch_hints.json").exists()


def test_mcp_tools_run_scn002_good_path_with_find_before_retry(tmp_path):
    tools = CommerceMCPTools(runs_dir=tmp_path)
    started = tools.call_tool("commerce.start_session", {"scenario_path": SCN002})
    session_id = started["session_id"]
    task = tools.call_tool("commerce.get_task", {"session_id": session_id})["task"]
    stable_key = f"{task['order_id']}:sku_retry_1:create_fulfillment"

    first = tools.call_tool(
        "commerce.create_fulfillment",
        {
            "session_id": session_id,
            "order_id": task["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "mcp_good_agent",
            "idempotency_key": stable_key,
            "request_id": "mcp_req_timeout_1",
            "source_event_id": task["id"],
            "fault_type": task["fault"]["type"],
        },
    )
    assert first["error"] == "timeout_after_commit"

    found = tools.call_tool(
        "commerce.find_fulfillment",
        {
            "session_id": session_id,
            "order_id": task["order_id"],
            "sku": "sku_retry_1",
            "idempotency_key": stable_key,
        },
    )
    assert found["fulfillment"]["fulfillment_id"] == "ful_001"

    replay = tools.call_tool(
        "commerce.create_fulfillment",
        {
            "session_id": session_id,
            "order_id": task["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "mcp_good_agent",
            "idempotency_key": stable_key,
            "request_id": "mcp_req_retry_2",
            "source_event_id": task["id"],
        },
    )
    assert replay["fulfillment"]["fulfillment_id"] == "ful_001"

    completed = tools.call_tool(
        "commerce.complete_session",
        {"session_id": session_id, "runner_name": "mcp_good_agent"},
    )
    assert completed["status"] == "passed"
    assert completed["findings"] == []
    assert tools.call_tool(
        "commerce.get_patch_hints",
        {"session_id": session_id},
    )["hints"] == []
