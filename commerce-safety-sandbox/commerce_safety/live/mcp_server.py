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

AGENT_FACING_MCP_TOOL_NAMES = [
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
    def start_session(scenario_path: str) -> dict[str, Any]:
        """Start a live commerce validation session from a scenario YAML path."""

        return tools.call_tool(
            "commerce.start_session",
            {"scenario_path": scenario_path},
        )

    @app.tool(name="commerce.get_task")
    def get_task(session_id: str) -> dict[str, Any]:
        """Return the next seeded scenario task for an open session."""

        return tools.call_tool("commerce.get_task", {"session_id": session_id})

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

    app = create_mcp_server(runs_dir=Path(args.runs_dir))
    app.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
