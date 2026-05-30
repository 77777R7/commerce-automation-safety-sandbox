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
