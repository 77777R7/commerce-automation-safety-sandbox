from __future__ import annotations

import json

from commerce_safety.live.http_api import LiveAPI
from commerce_safety.live.mcp_server import AGENT_FACING_MCP_TOOL_NAMES
from commerce_safety.live.mcp_tools import CommerceMCPTools


def _request(
    api: LiveAPI,
    method: str,
    path: str,
    payload: dict | None = None,
):
    status, body = api.handle(method, path, payload or {})
    return status, json.loads(json.dumps(body))


def test_http_sandbox_lifecycle_status_reset_teardown_and_ttl(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SAAS-003", "ttl_seconds": 120},
    )
    assert status == 201, created
    session_id = created["session_id"]
    assert created["ttl_expires_at"] is not None

    status, lifecycle = _request(api, "GET", f"/sessions/{session_id}/status")
    assert status == 200, lifecycle
    assert lifecycle["status"] == "open"
    assert lifecycle["ttl_expired"] is False
    assert lifecycle["tasks_total"] == 1
    assert lifecycle["tasks_remaining"] == 1

    status, task = _request(api, "GET", f"/sessions/{session_id}/tasks/next")
    assert status == 200, task
    assert task["done"] is False
    status, lifecycle = _request(api, "GET", f"/sessions/{session_id}/status")
    assert lifecycle["tasks_remaining"] == 0

    status, reset = _request(api, "POST", f"/sessions/{session_id}/reset")
    assert status == 200, reset
    assert reset["status"] == "open"
    assert reset["tasks_remaining"] == 1

    status, teardown = _request(api, "POST", f"/sessions/{session_id}/teardown")
    assert status == 200, teardown
    assert teardown["status"] == "torn_down"
    status, missing = _request(api, "GET", f"/sessions/{session_id}/status")
    assert status == 404
    assert missing["error"]["code"] == "session_not_found"


def test_mcp_sandbox_lifecycle_tools_are_agent_facing(tmp_path):
    expected_tools = {
        "sandbox.get_session_status",
        "sandbox.reset_session",
        "sandbox.teardown_session",
    }
    assert expected_tools.issubset(set(AGENT_FACING_MCP_TOOL_NAMES))
    tools = CommerceMCPTools(runs_dir=tmp_path)
    assert expected_tools.issubset({tool["name"] for tool in tools.list_tools()})

    started = tools.call_tool(
        "sandbox.start_session",
        {"scenario_id": "SAAS-003", "ttl_seconds": 120},
    )
    session_id = started["session_id"]
    status = tools.call_tool("sandbox.get_session_status", {"session_id": session_id})
    assert status["tasks_remaining"] == 1
    tools.call_tool("sandbox.get_task", {"session_id": session_id})
    reset = tools.call_tool("sandbox.reset_session", {"session_id": session_id})
    assert reset["tasks_remaining"] == 1
    torn_down = tools.call_tool("sandbox.teardown_session", {"session_id": session_id})
    assert torn_down["status"] == "torn_down"
