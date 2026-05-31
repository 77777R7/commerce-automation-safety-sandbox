from __future__ import annotations

from commerce_safety.live.mcp_tools import CommerceMCPTools


SCN003 = "commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml"


def test_amazon_mcp_tool_surface_runs_stale_inventory_failure(tmp_path):
    tools = CommerceMCPTools(runs_dir=tmp_path)
    tool_names = {tool["name"] for tool in tools.list_tools()}

    assert "amazon.get_inventory_summaries" in tool_names
    assert "amazon.promise_fulfillment" in tool_names
    assert "amazon.get_policy_report" not in tool_names

    session = tools.call_tool("commerce.start_session", {"scenario_path": SCN003})
    session_id = session["session_id"]

    inventory = tools.call_tool(
        "amazon.get_inventory_summaries",
        {"session_id": session_id, "sellerSkus": ["sku_stale_1"]},
    )
    assert inventory["payload"]["inventorySummaries"][0]["inventoryDetails"]["fulfillableQuantity"] == 1
    assert inventory["payload"]["inventorySummaries"][0]["sellerSku"] == "SELLER-0001"

    tools.call_tool(
        "amazon.promise_fulfillment",
        {
            "session_id": session_id,
            "amazonOrderId": "AMZ-3001",
            "sellerSku": "sku_stale_1",
            "quantity": 1,
            "sourceEventId": "task_promise_3001",
        },
    )
    complete = tools.call_tool(
        "commerce.complete_session",
        {"session_id": session_id, "runner_name": "amazon_mcp_unsafe_agent"},
    )

    assert complete["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in complete["findings"]}
    assert "amazon_no_promise_from_stale_inventory_summary" in policy_ids


def test_amazon_mcp_feed_report_and_rate_limit_metadata(tmp_path):
    tools = CommerceMCPTools(runs_dir=tmp_path)
    session = tools.call_tool("commerce.start_session", {"scenario_path": SCN003})
    session_id = session["session_id"]

    limited = tools.call_tool(
        "amazon.get_inventory_summaries",
        {
            "session_id": session_id,
            "sellerSkus": ["SELLER-0001"],
            "simulateRateLimit": True,
        },
    )
    assert limited["error"] == "rate_limited"
    assert limited["_commerce_twin"]["fault"] == "rate_limit_429"

    submitted = tools.call_tool(
        "amazon.submit_feed",
        {
            "session_id": session_id,
            "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
            "messages": [{"sellerSku": "SELLER-0001", "quantity": 0}],
        },
    )
    feed_id = submitted["payload"]["feedId"]
    report = tools.call_tool(
        "amazon.get_feed_status",
        {"session_id": session_id, "feedId": feed_id},
    )
    assert report["payload"]["processingStatus"] == "DONE"
    assert report["payload"]["processingReport"]["processingSummary"][
        "messagesProcessed"
    ] == 1
