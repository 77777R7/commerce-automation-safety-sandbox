from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .mcp_tools import CommerceMCPTools


def load_action_log(path: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError(f"Action log row {line_number} must be a JSON object")
        if "action" not in data:
            raise ValueError(f"Action log row {line_number} is missing action")
        actions.append(data)
    return actions


def run_action_log(
    *,
    scenario_path: Path,
    action_log_path: Path,
    runs_dir: Path,
    runner_name: str = "logged_agent",
) -> dict[str, Any]:
    tools = CommerceMCPTools(runs_dir=runs_dir)
    session = tools.call_tool(
        "commerce.start_session",
        {"scenario_path": str(scenario_path)},
    )
    session_id = session["session_id"]

    # Seed scenario events into the trace before replaying external actions.
    while True:
        task = tools.call_tool("commerce.get_task", {"session_id": session_id})
        if task.get("done"):
            break

    actions = load_action_log(action_log_path)
    for action in actions:
        tool_name = f"commerce.{action['action']}"
        arguments = {key: value for key, value in action.items() if key != "action"}
        arguments.setdefault("session_id", session_id)
        tools.call_tool(tool_name, arguments)

    result = tools.call_tool(
        "commerce.complete_session",
        {"session_id": session_id, "runner_name": runner_name},
    )
    return {
        **result,
        "action_log": str(action_log_path),
        "actions_replayed": len(actions),
    }
