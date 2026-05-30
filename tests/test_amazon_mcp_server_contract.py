from __future__ import annotations

from commerce_safety.live.mcp_server import AGENT_FACING_MCP_TOOL_NAMES


def test_stage13_amazon_tools_are_part_of_real_mcp_contract():
    required = {
        "amazon.get_inventory_summaries",
        "amazon.get_listing_item",
        "amazon.patch_listing_quantity",
        "amazon.submit_feed",
        "amazon.get_feed_status",
        "amazon.get_order",
        "amazon.get_order_items",
        "amazon.confirm_shipment",
        "amazon.inject_notification",
        "amazon.promise_fulfillment",
        "amazon.route_manual_review",
        "amazon.cancel_order",
        "amazon.place_workflow_hold",
        "amazon.submit_warehouse_cancellation_request",
        "amazon.get_coverage",
    }

    assert required.issubset(set(AGENT_FACING_MCP_TOOL_NAMES))
