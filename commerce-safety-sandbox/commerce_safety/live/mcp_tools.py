from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..io import read_json
from ..models import to_plain
from ..twin import TimeoutAfterCommit
from .sessions import SessionManager


class CommerceMCPTools:
    """MVP MCP tool surface for live commerce sessions.

    This class intentionally keeps the tool semantics independent from any one
    MCP transport. Stage 3 locks the agent-facing tool names and payloads; a
    stdio/server wrapper can sit on top without changing the core behavior.
    """

    def __init__(self, runs_dir: Path | str = Path("runs")):
        self.manager = SessionManager(runs_dir=runs_dir)
        self._tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "commerce.start_session": self._start_session,
            "commerce.get_task": self._get_task,
            "commerce.create_fulfillment": self._create_fulfillment,
            "commerce.find_fulfillment": self._find_fulfillment,
            "commerce.complete_session": self._complete_session,
            "commerce.get_trace": self._get_trace,
            "commerce.get_policy_report": self._get_policy_report,
            "commerce.get_patch_hints": self._get_patch_hints,
        }

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": name, "description": self._description_for(name)}
            for name in self._tools
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Unknown commerce MCP tool: {name}")
        return self._tools[name](arguments)

    def _start_session(self, arguments: dict[str, Any]) -> dict[str, Any]:
        scenario_path = arguments.get("scenario_path")
        if not scenario_path:
            raise ValueError("scenario_path is required")
        session = self.manager.create_session(Path(scenario_path))
        return {
            "ok": True,
            "session_id": session.session_id,
            "scenario_id": session.scenario_id,
            "scenario_name": session.scenario_name,
            "status": session.status,
        }

    def _get_task(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session_id = arguments["session_id"]
        task = self.manager.get_next_task(session_id)
        return {
            "ok": True,
            "session_id": session_id,
            "task": task,
            "done": task is None,
        }

    def _create_fulfillment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        try:
            fulfillment = session.twin.create_fulfillment(
                order_id=arguments["order_id"],
                sku=arguments["sku"],
                quantity=int(arguments.get("quantity", 1)),
                actor=arguments.get("actor", "mcp_agent"),
                webhook_id=arguments.get("webhook_id"),
                idempotency_key=arguments.get("idempotency_key"),
                request_id=arguments.get("request_id"),
                source_event_id=arguments.get("source_event_id"),
                fault_type=arguments.get("fault_type"),
            )
        except TimeoutAfterCommit as error:
            return {
                "ok": False,
                "error": "timeout_after_commit",
                "message": "Twin committed the mutation before returning a timeout.",
                "fulfillment_id": error.fulfillment.fulfillment_id,
            }
        return {
            "ok": True,
            "session_id": session.session_id,
            "fulfillment": to_plain(fulfillment),
        }

    def _find_fulfillment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        fulfillment = session.twin.find_fulfillment(
            order_id=arguments["order_id"],
            sku=arguments["sku"],
            idempotency_key=arguments.get("idempotency_key"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "fulfillment": to_plain(fulfillment) if fulfillment else None,
        }

    def _complete_session(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            **self.manager.complete_session(
                arguments["session_id"],
                runner_name=arguments.get("runner_name", "mcp_agent"),
            ),
        }

    def _get_trace(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        trace_path = session.output_path / "trace.json"
        if trace_path.exists():
            return read_json(trace_path)
        return {
            "run_id": session.session_id,
            "session_id": session.session_id,
            "scenario_id": session.scenario_id,
            "scenario_name": session.scenario_name,
            "status": session.status,
            "initial_state": session.initial_state,
            "current_state": session.twin.snapshot_summary(),
            "timeline": [to_plain(event) for event in session.twin.timeline],
        }

    def _get_policy_report(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        return read_json(session.output_path / "policy_report.json")

    def _get_patch_hints(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        return read_json(session.output_path / "patch_hints.json")

    def _description_for(self, name: str) -> str:
        descriptions = {
            "commerce.start_session": "Start a live commerce validation session.",
            "commerce.get_task": "Return the next seeded scenario task.",
            "commerce.create_fulfillment": "Create fulfillment in the permissive twin.",
            "commerce.find_fulfillment": "Find an existing fulfillment by order, sku, or key.",
            "commerce.complete_session": "Evaluate policies and write artifacts.",
            "commerce.get_trace": "Read the live trace timeline.",
            "commerce.get_policy_report": "Read structured policy findings.",
            "commerce.get_patch_hints": "Read agent-readable repair hints.",
        }
        return descriptions[name]
