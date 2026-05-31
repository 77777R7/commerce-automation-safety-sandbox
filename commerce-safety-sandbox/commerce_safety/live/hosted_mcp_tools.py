from __future__ import annotations

from pathlib import Path
from typing import Any

from .hosted import AuthContext, HostedTrustError, HostedTrustStore
from .mcp_tools import CommerceMCPTools


class HostedCommerceMCPTools:
    """Stage 19 hosted MCP semantic layer with API-token trust boundaries.

    The real FastMCP server can bind these semantics later. For the Design
    Partner Trust Gate, this wrapper proves the required MCP tool behavior:
    workspace-scoped API keys, scopes, audit events, TTL enforcement, and no
    cross-tenant session access while preserving the permissive twin.
    """

    def __init__(
        self,
        *,
        trust_store: HostedTrustStore,
        runs_dir: Path | str = Path("runs"),
    ):
        self.trust_store = trust_store
        self.tools = CommerceMCPTools(runs_dir=runs_dir)
        self.manager = self.tools.manager

    def list_tools(self) -> list[dict[str, str]]:
        return self.tools.list_tools()

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        api_token = str(arguments.get("api_token", "")).strip()
        context = self._authenticate(api_token)
        self.trust_store.check_rate_limit(context)
        self.trust_store.check_request_size(arguments)
        self.trust_store.scan_payload(context, arguments)
        self._authorize(name, arguments, context)

        clean_args = {key: value for key, value in arguments.items() if key != "api_token"}
        if name == "commerce.start_session":
            session = self.manager.create_session(
                Path(clean_args["scenario_path"]) if clean_args.get("scenario_path") else None,
                scenario_id=clean_args.get("scenario_id"),
                workspace_id=context.workspace_id,
                created_by=context.actor_id or context.token_id,
                ttl_seconds=self.trust_store.session_ttl_seconds,
                retention_days=self.trust_store.artifact_retention_days,
            )
            self.trust_store.audit(
                workspace_id=context.workspace_id,
                actor_type=context.actor_type,
                actor_id=context.actor_id or context.token_id,
                event_type="session.created",
                resource_type="session",
                resource_id=session.session_id,
                metadata={"scenario_id": session.scenario_id, "surface": "mcp"},
            )
            return {
                "ok": True,
                "session_id": session.session_id,
                "workspace_id": session.workspace_id,
                "scenario_id": session.scenario_id,
                "scenario_name": session.scenario_name,
                "status": session.status,
                "ttl_expires_at": session.ttl_expires_at,
                "retention_expires_at": session.retention_expires_at,
            }

        result = self.tools.call_tool(name, clean_args)
        session_id = clean_args.get("session_id")
        if session_id and name.startswith("commerce."):
            event_type = "mcp.tool_called"
            if name == "commerce.complete_session":
                event_type = "session.completed"
                self.trust_store.audit(
                    workspace_id=context.workspace_id,
                    actor_type="system",
                    actor_id="system",
                    event_type="policy_report.generated",
                    resource_type="session",
                    resource_id=session_id,
                    metadata={"surface": "mcp"},
                )
            self.trust_store.audit(
                workspace_id=context.workspace_id,
                actor_type=context.actor_type,
                actor_id=context.actor_id or context.token_id,
                event_type=event_type,
                resource_type="session",
                resource_id=session_id,
                metadata={"tool": name, "surface": "mcp"},
            )
        return result

    def _authenticate(self, api_token: str) -> AuthContext:
        if not api_token:
            raise HostedTrustError(401, "unauthorized", "Missing hosted MCP API token.")
        return self.trust_store.authenticate({"authorization": f"Bearer {api_token}"})

    def _authorize(
        self,
        name: str,
        arguments: dict[str, Any],
        context: AuthContext,
    ) -> None:
        self.trust_store.require_scope(context, self._required_scope(name))
        session_id = arguments.get("session_id")
        if session_id:
            session = self.manager.get_session(str(session_id))
            self.trust_store.require_workspace(context, session.workspace_id)
            if name not in {
                "commerce.get_trace",
                "commerce.get_policy_report",
                "commerce.get_patch_hints",
            }:
                self._require_session_writable(session_id=str(session_id), context=context)

    def _required_scope(self, name: str) -> str:
        if name == "commerce.start_session":
            return "sessions:create"
        if name in {
            "commerce.get_task",
            "commerce.get_trace",
            "commerce.get_policy_report",
            "commerce.get_patch_hints",
        }:
            return "sessions:read"
        return "mcp:call"

    def _require_session_writable(self, *, session_id: str, context: AuthContext) -> None:
        session = self.manager.get_session(session_id)
        if session.status == "aborted":
            raise HostedTrustError(409, "session_aborted", "Session has been aborted.")
        if session.status != "open" and session_id:
            raise HostedTrustError(409, "session_closed", "Session is no longer open.")
        if session.ttl_expires_at:
            from datetime import datetime, timezone

            if datetime.fromisoformat(session.ttl_expires_at) <= datetime.now(timezone.utc):
                raise HostedTrustError(
                    409,
                    "session_ttl_expired",
                    "Session TTL has expired and no more writes are allowed.",
                )

