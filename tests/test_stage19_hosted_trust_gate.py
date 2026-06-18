from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from commerce_safety.live.hosted import HostedTrustError, HostedTrustStore
from commerce_safety.live.hosted_mcp_tools import HostedCommerceMCPTools
from commerce_safety.live.http_api import LiveAPI

from tools.stage10_p0_harness import run_all_p0


SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def _store(**kwargs: Any) -> HostedTrustStore:
    return HostedTrustStore(signing_secret="stage19-test-secret", **kwargs)


def _workspace_with_token(
    store: HostedTrustStore,
    *,
    workspace_id: str,
    role: str = "owner",
    scopes: set[str] | None = None,
    expires_at: str | None = None,
):
    workspace = store.create_workspace(
        f"Workspace {workspace_id}",
        workspace_id=workspace_id,
    )
    secret, token = store.create_token(
        workspace.workspace_id,
        role=role,
        scopes=scopes,
        expires_at=expires_at,
        secret=f"cs_live_{workspace_id}_{role}_secret_123456789",
    )
    return workspace, secret, token


def _request(
    api: LiveAPI,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    token: str | None = None,
):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return api.handle(method, path, payload or {}, headers=headers)


def test_stage19_auth_rbac_token_states_and_scopes(tmp_path: Path) -> None:
    store = _store()
    _, owner_secret, _ = _workspace_with_token(store, workspace_id="ws_auth", role="owner")
    _, viewer_secret, _ = _workspace_with_token(store, workspace_id="ws_view", role="viewer")
    _, agent_secret, _ = _workspace_with_token(store, workspace_id="ws_agent", role="agent_token")
    expired_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    _, expired_secret, _ = _workspace_with_token(
        store,
        workspace_id="ws_expired",
        role="owner",
        expires_at=expired_at,
    )
    _, revoked_secret, revoked = _workspace_with_token(
        store,
        workspace_id="ws_revoked",
        role="owner",
    )
    api = LiveAPI(runs_dir=tmp_path, hosted_trust_store=store)
    store.tokens[revoked.token_id].revoked_at = datetime.now(timezone.utc).isoformat()

    status, body = _request(api, "POST", "/sessions", {"scenario_id": "SCN-002"})
    assert status == 401
    assert body["error"]["code"] == "unauthorized"

    status, body = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token="wrong-token",
    )
    assert status == 401
    assert body["error"]["code"] == "unauthorized"

    status, body = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=expired_secret,
    )
    assert status == 401
    assert body["error"]["code"] == "token_expired"

    status, body = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=revoked_secret,
    )
    assert status == 401
    assert body["error"]["code"] == "token_revoked"

    status, body = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=viewer_secret,
    )
    assert status == 403
    assert body["error"]["code"] == "forbidden"

    status, body = _request(
        api,
        "POST",
        "/workspaces/ws_agent/export",
        {},
        token=agent_secret,
    )
    assert status == 403
    assert body["error"]["code"] == "forbidden"

    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=owner_secret,
    )
    assert status == 201
    assert created["workspace_id"] == "ws_auth"


def test_stage19_tenant_isolation_blocks_bola_and_guessed_ids(tmp_path: Path) -> None:
    store = _store()
    _, token_a, _ = _workspace_with_token(store, workspace_id="ws_a", role="owner")
    _, token_b, _ = _workspace_with_token(store, workspace_id="ws_b", role="owner")
    api = LiveAPI(runs_dir=tmp_path, hosted_trust_store=store)

    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=token_a,
    )
    assert status == 201
    session_id = created["session_id"]

    for method, path, payload in [
        ("GET", f"/sessions/{session_id}/trace", {}),
        ("POST", f"/sessions/{session_id}/complete", {"runner_name": "intruder"}),
        ("GET", f"/workspaces/ws_a/sessions/{session_id}/artifacts/trace.json/signed-url", {}),
    ]:
        status, body = _request(api, method, path, payload, token=token_b)
        assert status == 403, body
        assert body["error"]["code"] == "forbidden"

    status, body = _request(api, "GET", "/workspaces/ws_b/sessions", {}, token=token_b)
    assert status == 200
    assert body["sessions"] == []


def test_stage19_artifact_manifest_signed_url_and_audit_log(tmp_path: Path) -> None:
    store = _store()
    _, owner_secret, _ = _workspace_with_token(store, workspace_id="ws_art", role="owner")
    api = LiveAPI(runs_dir=tmp_path, hosted_trust_store=store)

    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=owner_secret,
    )
    assert status == 201
    session_id = created["session_id"]
    _request(api, "GET", f"/sessions/{session_id}/tasks/next", token=owner_secret)
    status, completed = _request(
        api,
        "POST",
        f"/sessions/{session_id}/complete",
        {"runner_name": "stage19_artifact_agent"},
        token=owner_secret,
    )
    assert status == 200
    run_path = Path(completed["run_path"])
    manifest = json.loads((run_path / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["workspace_id"] == "ws_art"
    assert manifest["session_id"] == session_id
    assert manifest["retention"]["expires_at"]
    assert manifest["artifacts"][0]["sha256"]

    status, signed = _request(
        api,
        "GET",
        f"/workspaces/ws_art/sessions/{session_id}/artifacts/trace.json/signed-url",
        token=owner_secret,
    )
    assert status == 200
    status, downloaded = _request(api, "GET", signed["download_path"], token=owner_secret)
    assert status == 200
    assert "trace.json" not in downloaded["content"][:80]

    expired = store.sign_artifact_url(
        workspace_id="ws_art",
        session_id=session_id,
        artifact_path="trace.json",
        expires_in_seconds=-1,
    )
    status, body = _request(api, "GET", expired["download_path"], token=owner_secret)
    assert status == 403
    assert body["error"]["code"] == "artifact_url_expired"

    status, audit = _request(api, "GET", "/workspaces/ws_art/audit", token=owner_secret)
    assert status == 200
    event_types = {event["event_type"] for event in audit["audit_events"]}
    assert "session.created" in event_types
    assert "session.completed" in event_types
    assert "policy_report.generated" in event_types
    assert "artifact.downloaded" in event_types


def test_stage19_limits_redaction_ttl_revoke_suspend_and_delete(tmp_path: Path) -> None:
    store = _store(request_body_limit_bytes=250, rate_limit_requests=3, session_ttl_seconds=0)
    _, owner_secret, owner_token = _workspace_with_token(store, workspace_id="ws_limits", role="owner")
    _, agent_secret, agent_token = _workspace_with_token(
        store,
        workspace_id="ws_limits_agent",
        role="agent_token",
    )
    api = LiveAPI(runs_dir=tmp_path, hosted_trust_store=store)

    status, body = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002", "note": "call me at test@example.com"},
        token=owner_secret,
    )
    assert status == 201
    assert any(event.event_type == "pii.warning_detected" for event in store.audit_events)

    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        token=agent_secret,
    )
    assert status == 201
    session_id = created["session_id"]
    status, body = _request(
        api,
        "POST",
        f"/sessions/{session_id}/twin/create_fulfillment",
        {"order_id": "order_retry_1", "sku": "sku_retry_1"},
        token=agent_secret,
    )
    assert status == 409
    assert body["error"]["code"] == "session_ttl_expired"

    large_store = _store(request_body_limit_bytes=64)
    _, large_secret, _ = _workspace_with_token(large_store, workspace_id="ws_large", role="owner")
    large_api = LiveAPI(runs_dir=tmp_path / "large", hosted_trust_store=large_store)
    status, body = _request(
        large_api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002", "blob": "x" * 128},
        token=large_secret,
    )
    assert status == 413

    limited_store = _store(rate_limit_requests=1)
    _, limited_secret, _ = _workspace_with_token(limited_store, workspace_id="ws_rate", role="owner")
    limited_api = LiveAPI(runs_dir=tmp_path / "rate", hosted_trust_store=limited_store)
    assert _request(limited_api, "GET", "/workspaces/ws_rate/sessions", token=limited_secret)[0] == 200
    status, body = _request(limited_api, "GET", "/workspaces/ws_rate/sessions", token=limited_secret)
    assert status == 429
    assert body["error"]["code"] == "rate_limit_exceeded"

    status, body = _request(
        api,
        "POST",
        f"/workspaces/ws_limits_agent/tokens/{agent_token.token_id}/revoke",
        {},
        token=agent_secret,
    )
    assert status == 403
    status, body = _request(
        api,
        "POST",
        f"/workspaces/ws_limits/tokens/{owner_token.token_id}/revoke",
        {},
        token=owner_secret,
    )
    assert status == 200

    _, admin_secret, _ = _workspace_with_token(store, workspace_id="ws_admin", role="owner")
    status, body = _request(api, "POST", "/workspaces/ws_admin/suspend", {}, token=admin_secret)
    assert status == 200
    status, body = _request(api, "POST", "/sessions", {"scenario_id": "SCN-002"}, token=admin_secret)
    assert status == 403
    assert body["error"]["code"] == "workspace_suspended"

    _, delete_secret, _ = _workspace_with_token(store, workspace_id="ws_delete", role="owner")
    status, body = _request(api, "POST", "/workspaces/ws_delete/delete", {}, token=delete_secret)
    assert status == 200
    assert body["deletion_receipt"]["workspace_id"] == "ws_delete"


def test_stage19_all_p0_through_hosted_http_and_hosted_mcp(tmp_path: Path) -> None:
    http_store = _store(rate_limit_requests=1000)
    _, http_secret, _ = _workspace_with_token(http_store, workspace_id="ws_http", role="agent_token")
    http_api = LiveAPI(runs_dir=tmp_path / "http", hosted_trust_store=http_store)

    async def http_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        session_id = arguments.get("session_id")
        if name == "commerce.start_session":
            status, body = _request(http_api, "POST", "/sessions", arguments, token=http_secret)
        elif name == "commerce.get_task":
            status, body = _request(
                http_api,
                "GET",
                f"/sessions/{session_id}/tasks/next",
                token=http_secret,
            )
        elif name == "commerce.get_trace":
            status, body = _request(http_api, "GET", f"/sessions/{session_id}/trace", token=http_secret)
        elif name == "commerce.complete_session":
            status, body = _request(
                http_api,
                "POST",
                f"/sessions/{session_id}/complete",
                {"runner_name": arguments.get("runner_name")},
                token=http_secret,
            )
        else:
            action = name.removeprefix("commerce.")
            payload = {key: value for key, value in arguments.items() if key != "session_id"}
            status, body = _request(
                http_api,
                "POST",
                f"/sessions/{session_id}/twin/{action}",
                payload,
                token=http_secret,
            )
        assert status in {200, 201, 504}, body
        return body

    asyncio.run(run_all_p0(http_call))

    mcp_store = _store(rate_limit_requests=1000)
    _, mcp_secret, _ = _workspace_with_token(mcp_store, workspace_id="ws_mcp", role="agent_token")
    hosted_mcp = HostedCommerceMCPTools(
        trust_store=mcp_store,
        runs_dir=tmp_path / "mcp",
    )

    async def mcp_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return hosted_mcp.call_tool(name, {**arguments, "api_token": mcp_secret})

    asyncio.run(run_all_p0(mcp_call))


def test_stage19_hosted_mcp_rejects_cross_tenant_session_access(tmp_path: Path) -> None:
    store = _store()
    _, secret_a, _ = _workspace_with_token(store, workspace_id="ws_mcp_a", role="agent_token")
    _, secret_b, _ = _workspace_with_token(store, workspace_id="ws_mcp_b", role="agent_token")
    hosted_mcp = HostedCommerceMCPTools(trust_store=store, runs_dir=tmp_path)

    started = hosted_mcp.call_tool(
        "commerce.start_session",
        {"scenario_id": "SCN-002", "api_token": secret_a},
    )
    try:
        hosted_mcp.call_tool(
            "commerce.get_task",
            {"session_id": started["session_id"], "api_token": secret_b},
        )
    except HostedTrustError as error:
        assert error.status_code == 403
        assert error.code == "forbidden"
    else:
        raise AssertionError("hosted MCP cross-tenant session access should be blocked")

