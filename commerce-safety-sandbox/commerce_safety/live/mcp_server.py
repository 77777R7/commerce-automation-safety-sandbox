from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .mcp_tools import CommerceMCPTools


CORE_MCP_TOOL_NAMES = [
    "commerce.start_session",
    "commerce.get_task",
    "commerce.create_fulfillment",
    "commerce.find_fulfillment",
    "commerce.complete_session",
    "commerce.get_trace",
    "commerce.get_policy_report",
    "commerce.get_patch_hints",
]

SANDBOX_MCP_TOOL_ALIASES = [
    "sandbox.start_session",
    "sandbox.get_session_status",
    "sandbox.reset_session",
    "sandbox.teardown_session",
    "sandbox.get_task",
    "sandbox.complete_session",
    "sandbox.get_trace",
    "sandbox.get_policy_report",
    "sandbox.get_patch_hints",
]

AGENT_FACING_MCP_TOOL_NAMES = [
    *SANDBOX_MCP_TOOL_ALIASES,
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
    "stripe.create_customer",
    "stripe.create_subscription",
    "stripe.deliver_webhook",
    "slack.post_message",
    "github.create_check_run",
    "github.create_issue",
    "github.comment_on_pr",
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
]


def _require_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:
        raise RuntimeError(
            "The real MCP server requires modelcontextprotocol/python-sdk. "
            "Install it with `python -m pip install mcp` using Python 3.10+."
        ) from error
    return FastMCP


def create_mcp_server(
    *,
    runs_dir: Path | str = Path("runs"),
    name: str = "Commerce Safety Sandbox",
):
    """Create the official-SDK FastMCP server for the core V3.5 tool surface."""

    FastMCP = _require_fastmcp()
    app = FastMCP(name)
    tools = CommerceMCPTools(runs_dir=runs_dir)

    @app.tool(name="commerce.start_session")
    def start_session(
        scenario_path: str | None = None,
        scenario_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a live commerce validation session from an allowlisted scenario."""

        return tools.call_tool(
            "commerce.start_session",
            {"scenario_path": scenario_path, "scenario_id": scenario_id},
        )

    @app.tool(name="commerce.get_task")
    def get_task(session_id: str) -> dict[str, Any]:
        """Return the next seeded scenario task for an open session."""

        return tools.call_tool("commerce.get_task", {"session_id": session_id})

    @app.tool(name="sandbox.start_session")
    def sandbox_start_session(
        scenario_path: str | None = None,
        scenario_id: str | None = None,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Start a live agent validation session from an allowlisted scenario."""

        return tools.call_tool(
            "sandbox.start_session",
            {
                "scenario_path": scenario_path,
                "scenario_id": scenario_id,
                "ttl_seconds": ttl_seconds,
            },
        )

    @app.tool(name="sandbox.get_session_status")
    def sandbox_get_session_status(session_id: str) -> dict[str, Any]:
        """Read sandbox session lifecycle status."""

        return tools.call_tool(
            "sandbox.get_session_status",
            {"session_id": session_id},
        )

    @app.tool(name="sandbox.reset_session")
    def sandbox_reset_session(session_id: str) -> dict[str, Any]:
        """Reset a sandbox session to its initial state."""

        return tools.call_tool("sandbox.reset_session", {"session_id": session_id})

    @app.tool(name="sandbox.teardown_session")
    def sandbox_teardown_session(session_id: str) -> dict[str, Any]:
        """Tear down an in-memory sandbox session."""

        return tools.call_tool(
            "sandbox.teardown_session",
            {"session_id": session_id},
        )

    @app.tool(name="sandbox.get_task")
    def sandbox_get_task(session_id: str) -> dict[str, Any]:
        """Return the next seeded scenario task for an open session."""

        return tools.call_tool("sandbox.get_task", {"session_id": session_id})

    @app.tool(name="commerce.reserve_inventory")
    def reserve_inventory(
        session_id: str,
        order_id: str,
        sku: str,
        quantity: int = 1,
        actor: str = "mcp_agent",
        webhook_id: str | None = None,
    ) -> dict[str, Any]:
        """Reserve inventory in the permissive commerce twin."""

        return tools.call_tool(
            "commerce.reserve_inventory",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "quantity": quantity,
                "actor": actor,
                "webhook_id": webhook_id,
            },
        )

    @app.tool(name="commerce.promise_fulfillment")
    def promise_fulfillment(
        session_id: str,
        order_id: str,
        sku: str,
        quantity: int = 1,
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
        reservation_id: str | None = None,
    ) -> dict[str, Any]:
        """Record a customer-facing fulfillment promise."""

        return tools.call_tool(
            "commerce.promise_fulfillment",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "quantity": quantity,
                "actor": actor,
                "source_event_id": source_event_id,
                "reservation_id": reservation_id,
            },
        )

    @app.tool(name="commerce.refresh_inventory")
    def refresh_inventory(
        session_id: str,
        sku: str,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Refresh inventory from true availability."""

        return tools.call_tool(
            "commerce.refresh_inventory",
            {"session_id": session_id, "sku": sku, "actor": actor},
        )

    @app.tool(name="commerce.route_manual_review")
    def route_manual_review(
        session_id: str,
        order_id: str,
        sku: str,
        actor: str = "mcp_agent",
        reason: str = "manual_review_required",
        source_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Route a risky order line to manual review instead of mutating commerce state."""

        return tools.call_tool(
            "commerce.route_manual_review",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "actor": actor,
                "reason": reason,
                "source_event_id": source_event_id,
            },
        )

    @app.tool(name="commerce.create_fulfillment")
    def create_fulfillment(
        session_id: str,
        order_id: str,
        sku: str,
        quantity: int = 1,
        actor: str = "mcp_agent",
        webhook_id: str | None = None,
        idempotency_key: str | None = None,
        request_id: str | None = None,
        source_event_id: str | None = None,
        fault_type: str | None = None,
    ) -> dict[str, Any]:
        """Create fulfillment in the permissive twin, allowing unsafe mutations."""

        return tools.call_tool(
            "commerce.create_fulfillment",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "quantity": quantity,
                "actor": actor,
                "webhook_id": webhook_id,
                "idempotency_key": idempotency_key,
                "request_id": request_id,
                "source_event_id": source_event_id,
                "fault_type": fault_type,
            },
        )

    @app.tool(name="commerce.find_fulfillment")
    def find_fulfillment(
        session_id: str,
        order_id: str,
        sku: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Find an existing fulfillment by order, SKU, and optional idempotency key."""

        return tools.call_tool(
            "commerce.find_fulfillment",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "idempotency_key": idempotency_key,
            },
        )

    @app.tool(name="commerce.create_refund")
    def create_refund(
        session_id: str,
        order_id: str,
        amount: float,
        reason: str = "buyer_request",
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
        approval_id: str | None = None,
        approved_by: str | None = None,
    ) -> dict[str, Any]:
        """Issue a refund in the permissive twin; policies evaluate the risk later."""

        return tools.call_tool(
            "commerce.create_refund",
            {
                "session_id": session_id,
                "order_id": order_id,
                "amount": amount,
                "reason": reason,
                "actor": actor,
                "source_event_id": source_event_id,
                "approval_id": approval_id,
                "approved_by": approved_by,
            },
        )

    @app.tool(name="commerce.create_approval_request")
    def create_approval_request(
        session_id: str,
        order_id: str,
        amount: float,
        required_policy: str,
        reason: str = "buyer_request",
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an approval request before a risky refund or commerce action."""

        return tools.call_tool(
            "commerce.create_approval_request",
            {
                "session_id": session_id,
                "order_id": order_id,
                "amount": amount,
                "required_policy": required_policy,
                "reason": reason,
                "actor": actor,
                "source_event_id": source_event_id,
            },
        )

    @app.tool(name="commerce.cancel_order")
    def cancel_order(
        session_id: str,
        order_id: str,
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Mark an order cancelled inside the permissive twin."""

        return tools.call_tool(
            "commerce.cancel_order",
            {
                "session_id": session_id,
                "order_id": order_id,
                "actor": actor,
                "source_event_id": source_event_id,
            },
        )

    @app.tool(name="commerce.release_inventory")
    def release_inventory(
        session_id: str,
        order_id: str,
        sku: str,
        quantity: int = 1,
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Release reserved inventory."""

        return tools.call_tool(
            "commerce.release_inventory",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "quantity": quantity,
                "actor": actor,
                "source_event_id": source_event_id,
            },
        )

    @app.tool(name="commerce.place_workflow_hold")
    def place_workflow_hold(
        session_id: str,
        order_id: str,
        sku: str | None = None,
        actor: str = "mcp_agent",
        reason: str = "workflow_hold_required",
        source_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Place a workflow hold for manual warehouse/order review."""

        return tools.call_tool(
            "commerce.place_workflow_hold",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "actor": actor,
                "reason": reason,
                "source_event_id": source_event_id,
            },
        )

    @app.tool(name="commerce.submit_warehouse_cancellation_request")
    def submit_warehouse_cancellation_request(
        session_id: str,
        order_id: str,
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Request warehouse cancellation for an in-progress warehouse job."""

        return tools.call_tool(
            "commerce.submit_warehouse_cancellation_request",
            {
                "session_id": session_id,
                "order_id": order_id,
                "actor": actor,
                "source_event_id": source_event_id,
            },
        )

    @app.tool(name="commerce.warehouse_continue_fulfillment")
    def warehouse_continue_fulfillment(
        session_id: str,
        order_id: str,
        actor: str = "mcp_agent",
        source_event_id: str | None = None,
        new_status: str = "shipped",
    ) -> dict[str, Any]:
        """Advance warehouse fulfillment after cancellation to model a conflict."""

        return tools.call_tool(
            "commerce.warehouse_continue_fulfillment",
            {
                "session_id": session_id,
                "order_id": order_id,
                "actor": actor,
                "source_event_id": source_event_id,
                "new_status": new_status,
            },
        )

    @app.tool(name="commerce.skip_duplicate_webhook")
    def skip_duplicate_webhook(
        session_id: str,
        webhook: dict[str, Any],
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Record that an agent detected and skipped a duplicate webhook."""

        return tools.call_tool(
            "commerce.skip_duplicate_webhook",
            {
                "session_id": session_id,
                "webhook": webhook,
                "actor": actor,
            },
        )

    @app.tool(name="stripe.create_customer")
    def stripe_create_customer(
        session_id: str,
        email: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Create a Stripe customer in the SaaS validation twin."""

        return tools.call_tool(
            "stripe.create_customer",
            {
                "session_id": session_id,
                "email": email,
                "name": name,
                "metadata": metadata or {},
                "actor": actor,
            },
        )

    @app.tool(name="stripe.create_subscription")
    def stripe_create_subscription(
        session_id: str,
        customer_id: str,
        price_id: str,
        amount_due: int,
        currency: str = "usd",
        payment_outcome: str = "succeeded",
        metadata: dict[str, Any] | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Create a Stripe subscription and initial invoice/payment intent."""

        return tools.call_tool(
            "stripe.create_subscription",
            {
                "session_id": session_id,
                "customer_id": customer_id,
                "price_id": price_id,
                "amount_due": amount_due,
                "currency": currency,
                "payment_outcome": payment_outcome,
                "metadata": metadata or {},
                "actor": actor,
            },
        )

    @app.tool(name="stripe.deliver_webhook")
    def stripe_deliver_webhook(
        session_id: str,
        event_id: str,
        delivery_id: str | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Deliver a Stripe webhook event in the SaaS validation twin."""

        return tools.call_tool(
            "stripe.deliver_webhook",
            {
                "session_id": session_id,
                "event_id": event_id,
                "delivery_id": delivery_id,
                "actor": actor,
            },
        )

    @app.tool(name="slack.post_message")
    def slack_post_message(
        session_id: str,
        channel_id: str,
        text: str,
        thread_ts: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Post a Slack message in the SaaS validation twin."""

        return tools.call_tool(
            "slack.post_message",
            {
                "session_id": session_id,
                "channel_id": channel_id,
                "text": text,
                "thread_ts": thread_ts,
                "metadata": metadata or {},
                "actor": actor,
            },
        )

    @app.tool(name="github.create_check_run")
    def github_create_check_run(
        session_id: str,
        owner: str,
        repo_name: str,
        head_sha: str,
        name: str = "agent-policy/saas-validation",
        status: str = "completed",
        conclusion: str | None = None,
        output_summary: str = "",
        details_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Create a GitHub check run in the SaaS validation twin."""

        return tools.call_tool(
            "github.create_check_run",
            {
                "session_id": session_id,
                "owner": owner,
                "repo_name": repo_name,
                "head_sha": head_sha,
                "name": name,
                "status": status,
                "conclusion": conclusion,
                "output_summary": output_summary,
                "details_url": details_url,
                "metadata": metadata or {},
                "actor": actor,
            },
        )

    @app.tool(name="github.create_issue")
    def github_create_issue(
        session_id: str,
        owner: str,
        repo_name: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Create a GitHub issue in the SaaS validation twin."""

        return tools.call_tool(
            "github.create_issue",
            {
                "session_id": session_id,
                "owner": owner,
                "repo_name": repo_name,
                "title": title,
                "body": body,
                "labels": labels or [],
                "metadata": metadata or {},
                "actor": actor,
            },
        )

    @app.tool(name="github.comment_on_pr")
    def github_comment_on_pr(
        session_id: str,
        owner: str,
        repo_name: str,
        pull_number: int,
        body: str,
        metadata: dict[str, Any] | None = None,
        actor: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Comment on a GitHub PR in the SaaS validation twin."""

        return tools.call_tool(
            "github.comment_on_pr",
            {
                "session_id": session_id,
                "owner": owner,
                "repo_name": repo_name,
                "pull_number": pull_number,
                "body": body,
                "metadata": metadata or {},
                "actor": actor,
            },
        )

    @app.tool(name="amazon.get_inventory_summaries")
    def amazon_get_inventory_summaries(
        session_id: str,
        sellerSkus: list[str] | None = None,
    ) -> dict[str, Any]:
        """Read Amazon-shaped FBA inventory summaries."""

        return tools.call_tool(
            "amazon.get_inventory_summaries",
            {"session_id": session_id, "sellerSkus": sellerSkus},
        )

    @app.tool(name="amazon.get_listing_item")
    def amazon_get_listing_item(
        session_id: str,
        sellerSku: str,
        sellerId: str = "seller_123",
    ) -> dict[str, Any]:
        """Read Amazon-shaped listing item availability."""

        return tools.call_tool(
            "amazon.get_listing_item",
            {
                "session_id": session_id,
                "sellerSku": sellerSku,
                "sellerId": sellerId,
            },
        )

    @app.tool(name="amazon.patch_listing_quantity")
    def amazon_patch_listing_quantity(
        session_id: str,
        sellerSku: str,
        quantity: int,
        sellerId: str = "seller_123",
        actor: str = "amazon_like_agent",
    ) -> dict[str, Any]:
        """Submit an Amazon-shaped listing quantity patch."""

        return tools.call_tool(
            "amazon.patch_listing_quantity",
            {
                "session_id": session_id,
                "sellerSku": sellerSku,
                "quantity": quantity,
                "sellerId": sellerId,
                "actor": actor,
            },
        )

    @app.tool(name="amazon.submit_feed")
    def amazon_submit_feed(
        session_id: str,
        feedType: str = "POST_ORDER_FULFILLMENT_DATA",
        actor: str = "amazon_like_agent",
    ) -> dict[str, Any]:
        """Submit an Amazon-shaped feed and receive a processing status."""

        return tools.call_tool(
            "amazon.submit_feed",
            {"session_id": session_id, "feedType": feedType, "actor": actor},
        )

    @app.tool(name="amazon.get_feed_status")
    def amazon_get_feed_status(session_id: str, feedId: str) -> dict[str, Any]:
        """Read Amazon-shaped feed processing status."""

        return tools.call_tool(
            "amazon.get_feed_status",
            {"session_id": session_id, "feedId": feedId},
        )

    @app.tool(name="amazon.get_order")
    def amazon_get_order(session_id: str, amazonOrderId: str) -> dict[str, Any]:
        """Read an Amazon-shaped order."""

        return tools.call_tool(
            "amazon.get_order",
            {"session_id": session_id, "amazonOrderId": amazonOrderId},
        )

    @app.tool(name="amazon.get_order_items")
    def amazon_get_order_items(session_id: str, amazonOrderId: str) -> dict[str, Any]:
        """Read Amazon-shaped order items."""

        return tools.call_tool(
            "amazon.get_order_items",
            {"session_id": session_id, "amazonOrderId": amazonOrderId},
        )

    @app.tool(name="amazon.confirm_shipment")
    def amazon_confirm_shipment(
        session_id: str,
        amazonOrderId: str,
        packageDetail: dict[str, Any] | None = None,
        actor: str = "amazon_like_agent",
        sourceEventId: str | None = None,
    ) -> dict[str, Any]:
        """Confirm shipment through an Amazon-shaped Orders API path."""

        return tools.call_tool(
            "amazon.confirm_shipment",
            {
                "session_id": session_id,
                "amazonOrderId": amazonOrderId,
                "packageDetail": packageDetail or {},
                "actor": actor,
                "sourceEventId": sourceEventId,
            },
        )

    @app.tool(name="amazon.inject_notification")
    def amazon_inject_notification(
        session_id: str,
        notificationType: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Inject an Amazon-shaped notification such as ORDER_CHANGE."""

        return tools.call_tool(
            "amazon.inject_notification",
            {
                "session_id": session_id,
                "notificationType": notificationType,
                "payload": payload,
            },
        )

    @app.tool(name="amazon.promise_fulfillment")
    def amazon_promise_fulfillment(
        session_id: str,
        amazonOrderId: str,
        sellerSku: str,
        quantity: int = 1,
        actor: str = "amazon_like_agent",
        sourceEventId: str | None = None,
    ) -> dict[str, Any]:
        """Record an Amazon seller-ops fulfillment promise."""

        return tools.call_tool(
            "amazon.promise_fulfillment",
            {
                "session_id": session_id,
                "amazonOrderId": amazonOrderId,
                "sellerSku": sellerSku,
                "quantity": quantity,
                "actor": actor,
                "sourceEventId": sourceEventId,
            },
        )

    @app.tool(name="amazon.route_manual_review")
    def amazon_route_manual_review(
        session_id: str,
        amazonOrderId: str,
        sellerSku: str,
        reason: str = "manual_review_required",
        actor: str = "amazon_like_agent",
        sourceEventId: str | None = None,
    ) -> dict[str, Any]:
        """Route an Amazon-shaped seller-ops case to manual review."""

        return tools.call_tool(
            "amazon.route_manual_review",
            {
                "session_id": session_id,
                "amazonOrderId": amazonOrderId,
                "sellerSku": sellerSku,
                "reason": reason,
                "actor": actor,
                "sourceEventId": sourceEventId,
            },
        )

    @app.tool(name="amazon.cancel_order")
    def amazon_cancel_order(
        session_id: str,
        amazonOrderId: str,
        actor: str = "amazon_like_agent",
        sourceEventId: str | None = None,
    ) -> dict[str, Any]:
        """Cancel an order through an Amazon-shaped seller-ops action."""

        return tools.call_tool(
            "amazon.cancel_order",
            {
                "session_id": session_id,
                "amazonOrderId": amazonOrderId,
                "actor": actor,
                "sourceEventId": sourceEventId,
            },
        )

    @app.tool(name="amazon.place_workflow_hold")
    def amazon_place_workflow_hold(
        session_id: str,
        amazonOrderId: str,
        sellerSku: str | None = None,
        reason: str = "workflow_hold_required",
        actor: str = "amazon_like_agent",
        sourceEventId: str | None = None,
    ) -> dict[str, Any]:
        """Place a workflow hold for Amazon-shaped warehouse/order review."""

        return tools.call_tool(
            "amazon.place_workflow_hold",
            {
                "session_id": session_id,
                "amazonOrderId": amazonOrderId,
                "sellerSku": sellerSku,
                "reason": reason,
                "actor": actor,
                "sourceEventId": sourceEventId,
            },
        )

    @app.tool(name="amazon.submit_warehouse_cancellation_request")
    def amazon_submit_warehouse_cancellation_request(
        session_id: str,
        amazonOrderId: str,
        actor: str = "amazon_like_agent",
        sourceEventId: str | None = None,
    ) -> dict[str, Any]:
        """Request warehouse cancellation for an Amazon-shaped order conflict."""

        return tools.call_tool(
            "amazon.submit_warehouse_cancellation_request",
            {
                "session_id": session_id,
                "amazonOrderId": amazonOrderId,
                "actor": actor,
                "sourceEventId": sourceEventId,
            },
        )

    @app.tool(name="amazon.get_coverage")
    def amazon_get_coverage(session_id: str) -> dict[str, Any]:
        """Read Amazon Seller Ops skin coverage."""

        return tools.call_tool("amazon.get_coverage", {"session_id": session_id})

    @app.tool(name="commerce.complete_session")
    def complete_session(
        session_id: str,
        runner_name: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Evaluate policies, write artifacts, and return the validation result."""

        return tools.call_tool(
            "commerce.complete_session",
            {"session_id": session_id, "runner_name": runner_name},
        )

    @app.tool(name="commerce.get_trace")
    def get_trace(session_id: str) -> dict[str, Any]:
        """Read the live trace timeline for a session."""

        return tools.call_tool("commerce.get_trace", {"session_id": session_id})

    @app.tool(name="commerce.get_policy_report")
    def get_policy_report(session_id: str) -> dict[str, Any]:
        """Read structured policy findings for a completed session."""

        return tools.call_tool(
            "commerce.get_policy_report",
            {"session_id": session_id},
        )

    @app.tool(name="commerce.get_patch_hints")
    def get_patch_hints(session_id: str) -> dict[str, Any]:
        """Read agent-readable repair hints for a completed session."""

        return tools.call_tool("commerce.get_patch_hints", {"session_id": session_id})

    @app.tool(name="sandbox.complete_session")
    def sandbox_complete_session(
        session_id: str,
        runner_name: str = "mcp_agent",
    ) -> dict[str, Any]:
        """Evaluate policies, write artifacts, and return the validation result."""

        return tools.call_tool(
            "sandbox.complete_session",
            {"session_id": session_id, "runner_name": runner_name},
        )

    @app.tool(name="sandbox.get_trace")
    def sandbox_get_trace(session_id: str) -> dict[str, Any]:
        """Read the live trace and event ledger for a session."""

        return tools.call_tool("sandbox.get_trace", {"session_id": session_id})

    @app.tool(name="sandbox.get_policy_report")
    def sandbox_get_policy_report(session_id: str) -> dict[str, Any]:
        """Read structured policy findings for a completed session."""

        return tools.call_tool(
            "sandbox.get_policy_report",
            {"session_id": session_id},
        )

    @app.tool(name="sandbox.get_patch_hints")
    def sandbox_get_patch_hints(session_id: str) -> dict[str, Any]:
        """Read agent-readable repair hints for a completed session."""

        return tools.call_tool("sandbox.get_patch_hints", {"session_id": session_id})

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the real Commerce Safety MCP server.",
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where live session artifacts are written.",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="MCP transport to run.",
    )
    args = parser.parse_args(argv)

    if args.transport != "stdio":
        raise SystemExit(
            "MCP streamable-http transport is disabled in local V3.5 until "
            "host binding and auth policy are explicitly gated. Use --transport stdio."
        )

    app = create_mcp_server(runs_dir=Path(args.runs_dir))
    app.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
