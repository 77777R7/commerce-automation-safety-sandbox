from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode


HOSTED_POC_SCOPES = {
    "sessions:create",
    "sessions:read",
    "twin:call",
    "mcp:call",
    "reports:read",
    "artifacts:read",
    "workspace:export",
    "workspace:delete",
    "tokens:manage",
    "audit:read",
}

ROLE_SCOPES: dict[str, set[str]] = {
    "owner": set(HOSTED_POC_SCOPES),
    "operator": {
        "sessions:create",
        "sessions:read",
        "twin:call",
        "mcp:call",
        "reports:read",
        "artifacts:read",
        "audit:read",
    },
    "viewer": {
        "sessions:read",
        "reports:read",
        "artifacts:read",
    },
    "agent_token": {
        "sessions:create",
        "sessions:read",
        "twin:call",
        "mcp:call",
    },
}

SECRET_PATTERNS = {
    "stripe_live_secret": re.compile(r"\bsk_live_[A-Za-z0-9_]{12,}\b"),
    "shopify_admin_token": re.compile(r"\bshpat_[A-Za-z0-9_]{12,}\b"),
    "github_token": re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    "slack_bot_token": re.compile(r"\bxoxb-[A-Za-z0-9-]{12,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
    "address_like": re.compile(
        r"\b\d{1,6}\s+[A-Za-z0-9 .'-]+\s+"
        r"(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|way|blvd)\b",
        re.IGNORECASE,
    ),
}


class HostedTrustError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    plan: str = "design_partner"
    status: str = "active"
    created_at: str = field(default_factory=lambda: _now().isoformat())


@dataclass
class User:
    user_id: str
    email: str
    workspace_id: str
    role: str = "owner"
    status: str = "active"


@dataclass
class ApiToken:
    token_id: str
    workspace_id: str
    role: str
    scopes: set[str]
    token_hash: str
    token_last4: str
    token_type: str = "agent_api_key"
    created_at: str = field(default_factory=lambda: _now().isoformat())
    expires_at: str | None = None
    revoked_at: str | None = None
    last_used_at: str | None = None


@dataclass
class AuthContext:
    workspace_id: str
    token_id: str
    role: str
    scopes: set[str]
    actor_type: str = "agent_token"
    actor_id: str | None = None


@dataclass
class AuditEvent:
    audit_id: str
    workspace_id: str
    actor_type: str
    actor_id: str
    event_type: str
    resource_type: str
    resource_id: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeletionReceipt:
    deletion_receipt_id: str
    workspace_id: str
    deleted_by: str
    deleted_at: str
    retained_tombstone: bool = True


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _json_size(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


class HostedTrustStore:
    """In-memory Stage 19 trust boundary for hosted design-partner POCs.

    This is intentionally not a production identity provider. It gives the
    hosted beta path explicit workspace, token, scope, audit, retention, and
    artifact authorization semantics that can later be backed by Postgres and
    object storage without changing the HTTP/MCP contract.
    """

    def __init__(
        self,
        *,
        request_body_limit_bytes: int = 1_048_576,
        rate_limit_requests: int = 250,
        session_ttl_seconds: int = 30 * 60,
        artifact_retention_days: int = 14,
        signing_secret: str = "stage19-local-signing-secret",
    ):
        self.request_body_limit_bytes = request_body_limit_bytes
        self.rate_limit_requests = rate_limit_requests
        self.session_ttl_seconds = session_ttl_seconds
        self.artifact_retention_days = artifact_retention_days
        self.signing_secret = signing_secret
        self.workspaces: dict[str, Workspace] = {}
        self.users: dict[str, User] = {}
        self.tokens: dict[str, ApiToken] = {}
        self._token_ids_by_hash: dict[str, str] = {}
        self.audit_events: list[AuditEvent] = []
        self.deletion_receipts: list[DeletionReceipt] = []
        self._request_counts: dict[str, int] = {}

    def create_workspace(
        self,
        name: str,
        *,
        workspace_id: str | None = None,
        owner_email: str = "owner@example.test",
    ) -> Workspace:
        workspace = Workspace(
            workspace_id=workspace_id or f"ws_{secrets.token_hex(4)}",
            name=name,
        )
        self.workspaces[workspace.workspace_id] = workspace
        self.users[f"user_{workspace.workspace_id}_owner"] = User(
            user_id=f"user_{workspace.workspace_id}_owner",
            email=owner_email,
            workspace_id=workspace.workspace_id,
            role="owner",
        )
        self.audit(
            workspace_id=workspace.workspace_id,
            actor_type="system",
            actor_id="system",
            event_type="workspace.created",
            resource_type="workspace",
            resource_id=workspace.workspace_id,
            metadata={"plan": workspace.plan},
        )
        return workspace

    def create_token(
        self,
        workspace_id: str,
        *,
        role: str = "agent_token",
        scopes: set[str] | list[str] | None = None,
        token_type: str = "agent_api_key",
        expires_at: str | None = None,
        secret: str | None = None,
    ) -> tuple[str, ApiToken]:
        self._require_workspace_exists(workspace_id)
        if role not in ROLE_SCOPES:
            raise ValueError(f"Unknown hosted role: {role}")
        resolved_scopes = set(scopes) if scopes is not None else set(ROLE_SCOPES[role])
        unknown_scopes = resolved_scopes - HOSTED_POC_SCOPES
        if unknown_scopes:
            raise ValueError(f"Unknown hosted scopes: {sorted(unknown_scopes)}")
        raw_secret = secret or f"cs_live_{secrets.token_urlsafe(24)}"
        token = ApiToken(
            token_id=f"tok_{secrets.token_hex(4)}",
            workspace_id=workspace_id,
            role=role,
            scopes=resolved_scopes,
            token_hash=_hash_token(raw_secret),
            token_last4=raw_secret[-4:],
            token_type=token_type,
            expires_at=expires_at,
        )
        self.tokens[token.token_id] = token
        self._token_ids_by_hash[token.token_hash] = token.token_id
        self.audit(
            workspace_id=workspace_id,
            actor_type="system",
            actor_id="system",
            event_type="token.created",
            resource_type="api_token",
            resource_id=token.token_id,
            metadata={"role": role, "scopes": sorted(resolved_scopes), "token_type": token_type},
        )
        return raw_secret, token

    def authenticate(self, headers: dict[str, Any]) -> AuthContext:
        normalized = {str(key).lower(): str(value) for key, value in headers.items()}
        secret = ""
        auth = normalized.get("authorization", "")
        if auth.startswith("Bearer "):
            secret = auth.removeprefix("Bearer ").strip()
        elif normalized.get("x-commerce-safety-token"):
            secret = normalized["x-commerce-safety-token"].strip()
        if not secret:
            raise HostedTrustError(401, "unauthorized", "Missing hosted API token.")
        token_id = self._token_ids_by_hash.get(_hash_token(secret))
        if token_id is None:
            self.audit_auth_failure("invalid_token")
            raise HostedTrustError(401, "unauthorized", "Invalid hosted API token.")
        token = self.tokens[token_id]
        if token.revoked_at is not None:
            self.audit_auth_failure("revoked_token", workspace_id=token.workspace_id)
            raise HostedTrustError(401, "token_revoked", "Hosted API token has been revoked.")
        expires_at = _parse_iso(token.expires_at)
        if expires_at and expires_at <= _now():
            self.audit_auth_failure("expired_token", workspace_id=token.workspace_id)
            raise HostedTrustError(401, "token_expired", "Hosted API token has expired.")
        workspace = self._require_workspace_exists(token.workspace_id)
        if workspace.status == "suspended":
            raise HostedTrustError(403, "workspace_suspended", "Workspace is suspended.")
        if workspace.status == "deleted":
            raise HostedTrustError(410, "workspace_deleted", "Workspace has been deleted.")
        token.last_used_at = _now().isoformat()
        actor_type = "agent_token" if token.role == "agent_token" else "user"
        return AuthContext(
            workspace_id=token.workspace_id,
            token_id=token.token_id,
            role=token.role,
            scopes=set(token.scopes),
            actor_type=actor_type,
            actor_id=token.token_id,
        )

    def require_scope(self, context: AuthContext, scope: str) -> None:
        if scope not in context.scopes:
            self.audit(
                workspace_id=context.workspace_id,
                actor_type=context.actor_type,
                actor_id=context.actor_id or context.token_id,
                event_type="authorization.denied",
                resource_type="scope",
                resource_id=scope,
                metadata={"role": context.role, "token_id": context.token_id},
            )
            raise HostedTrustError(403, "forbidden", f"Missing required scope: {scope}.")

    def require_workspace(self, context: AuthContext, workspace_id: str) -> None:
        if context.workspace_id != workspace_id:
            self.audit(
                workspace_id=context.workspace_id,
                actor_type=context.actor_type,
                actor_id=context.actor_id or context.token_id,
                event_type="authorization.denied",
                resource_type="workspace",
                resource_id=workspace_id,
                metadata={"reason": "cross_tenant_access"},
            )
            raise HostedTrustError(403, "forbidden", "Cross-workspace access is not allowed.")

    def check_rate_limit(self, context: AuthContext) -> None:
        count = self._request_counts.get(context.token_id, 0) + 1
        self._request_counts[context.token_id] = count
        if count > self.rate_limit_requests:
            self.audit(
                workspace_id=context.workspace_id,
                actor_type=context.actor_type,
                actor_id=context.actor_id or context.token_id,
                event_type="rate_limit.exceeded",
                resource_type="api_token",
                resource_id=context.token_id,
                metadata={"limit": self.rate_limit_requests},
            )
            raise HostedTrustError(429, "rate_limit_exceeded", "Hosted API rate limit exceeded.")

    def check_request_size(self, payload: dict[str, Any]) -> None:
        if _json_size(payload) > self.request_body_limit_bytes:
            raise HostedTrustError(
                413,
                "request_body_too_large",
                "JSON request body exceeds the hosted design-partner limit.",
            )

    def scan_payload(self, context: AuthContext, payload: dict[str, Any]) -> list[dict[str, str]]:
        text = json.dumps(payload, ensure_ascii=False)
        warnings: list[dict[str, str]] = []
        for pattern_id, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                warning = {"type": "secret", "pattern_id": pattern_id}
                warnings.append(warning)
                self.audit(
                    workspace_id=context.workspace_id,
                    actor_type=context.actor_type,
                    actor_id=context.actor_id or context.token_id,
                    event_type="secret.warning_detected",
                    resource_type="request",
                    resource_id="hosted_request",
                    metadata=warning,
                )
        for pattern_id, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                warning = {"type": "pii", "pattern_id": pattern_id}
                warnings.append(warning)
                self.audit(
                    workspace_id=context.workspace_id,
                    actor_type=context.actor_type,
                    actor_id=context.actor_id or context.token_id,
                    event_type="pii.warning_detected",
                    resource_type="request",
                    resource_id="hosted_request",
                    metadata=warning,
                )
        return warnings

    def revoke_token(self, context: AuthContext, token_id: str) -> ApiToken:
        self.require_scope(context, "tokens:manage")
        token = self.tokens[token_id]
        self.require_workspace(context, token.workspace_id)
        token.revoked_at = _now().isoformat()
        self.audit(
            workspace_id=context.workspace_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id or context.token_id,
            event_type="token.revoked",
            resource_type="api_token",
            resource_id=token_id,
            metadata={},
        )
        return token

    def suspend_workspace(self, context: AuthContext, workspace_id: str) -> Workspace:
        self.require_scope(context, "tokens:manage")
        self.require_workspace(context, workspace_id)
        workspace = self._require_workspace_exists(workspace_id)
        workspace.status = "suspended"
        self.audit(
            workspace_id=workspace_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id or context.token_id,
            event_type="workspace.suspended",
            resource_type="workspace",
            resource_id=workspace_id,
            metadata={},
        )
        return workspace

    def export_workspace(self, context: AuthContext, workspace_id: str) -> dict[str, Any]:
        self.require_scope(context, "workspace:export")
        self.require_workspace(context, workspace_id)
        tokens = [
            {
                "token_id": token.token_id,
                "role": token.role,
                "scopes": sorted(token.scopes),
                "token_type": token.token_type,
                "expires_at": token.expires_at,
                "revoked_at": token.revoked_at,
                "last_used_at": token.last_used_at,
            }
            for token in self.tokens.values()
            if token.workspace_id == workspace_id
        ]
        events = [
            self.audit_event_to_plain(event)
            for event in self.audit_events
            if event.workspace_id == workspace_id
        ]
        self.audit(
            workspace_id=workspace_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id or context.token_id,
            event_type="workspace.export_requested",
            resource_type="workspace",
            resource_id=workspace_id,
            metadata={},
        )
        return {"workspace_id": workspace_id, "tokens": tokens, "audit_events": events}

    def delete_workspace(self, context: AuthContext, workspace_id: str) -> DeletionReceipt:
        self.require_scope(context, "workspace:delete")
        self.require_workspace(context, workspace_id)
        workspace = self._require_workspace_exists(workspace_id)
        workspace.status = "deleted"
        for token in self.tokens.values():
            if token.workspace_id == workspace_id and token.revoked_at is None:
                token.revoked_at = _now().isoformat()
        receipt = DeletionReceipt(
            deletion_receipt_id=f"del_{secrets.token_hex(4)}",
            workspace_id=workspace_id,
            deleted_by=context.actor_id or context.token_id,
            deleted_at=_now().isoformat(),
        )
        self.deletion_receipts.append(receipt)
        self.audit(
            workspace_id=workspace_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id or context.token_id,
            event_type="workspace.delete_requested",
            resource_type="workspace",
            resource_id=workspace_id,
            metadata={"deletion_receipt_id": receipt.deletion_receipt_id},
        )
        self.audit(
            workspace_id=workspace_id,
            actor_type="system",
            actor_id="system",
            event_type="workspace.deleted",
            resource_type="workspace",
            resource_id=workspace_id,
            metadata={"deletion_receipt_id": receipt.deletion_receipt_id},
        )
        return receipt

    def sign_artifact_url(
        self,
        *,
        workspace_id: str,
        session_id: str,
        artifact_path: str,
        expires_in_seconds: int = 300,
    ) -> dict[str, Any]:
        expires = int((_now() + timedelta(seconds=expires_in_seconds)).timestamp())
        payload = f"{workspace_id}:{session_id}:{artifact_path}:{expires}"
        signature = hmac.new(
            self.signing_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        query = urlencode({"expires": str(expires), "signature": signature})
        return {
            "artifact_path": artifact_path,
            "expires": expires,
            "signature": signature,
            "download_path": (
                f"/workspaces/{workspace_id}/sessions/{session_id}/artifacts/"
                f"{artifact_path}/download?{query}"
            ),
        }

    def validate_artifact_signature(
        self,
        *,
        workspace_id: str,
        session_id: str,
        artifact_path: str,
        expires: str | None,
        signature: str | None,
    ) -> None:
        if not expires or not signature:
            raise HostedTrustError(
                403,
                "artifact_signature_required",
                "Artifact download requires a signed URL.",
            )
        try:
            expires_int = int(expires)
        except ValueError as error:
            raise HostedTrustError(403, "artifact_signature_invalid", "Invalid artifact expiry.") from error
        if expires_int <= int(_now().timestamp()):
            raise HostedTrustError(403, "artifact_url_expired", "Signed artifact URL has expired.")
        payload = f"{workspace_id}:{session_id}:{artifact_path}:{expires_int}"
        expected = hmac.new(
            self.signing_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HostedTrustError(403, "artifact_signature_invalid", "Invalid artifact signature.")

    def audit(
        self,
        *,
        workspace_id: str,
        actor_type: str,
        actor_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            audit_id=f"audit_{secrets.token_hex(5)}",
            workspace_id=workspace_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            created_at=_now().isoformat(),
            metadata=metadata or {},
        )
        self.audit_events.append(event)
        return event

    def audit_auth_failure(self, reason: str, *, workspace_id: str = "unknown") -> None:
        self.audit(
            workspace_id=workspace_id,
            actor_type="unknown",
            actor_id="unknown",
            event_type="auth.failed",
            resource_type="api_token",
            resource_id="unknown",
            metadata={"reason": reason},
        )

    def audit_event_to_plain(self, event: AuditEvent) -> dict[str, Any]:
        return {
            "audit_id": event.audit_id,
            "workspace_id": event.workspace_id,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "event_type": event.event_type,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "created_at": event.created_at,
            "metadata": event.metadata,
        }

    def deletion_receipt_to_plain(self, receipt: DeletionReceipt) -> dict[str, Any]:
        return {
            "deletion_receipt_id": receipt.deletion_receipt_id,
            "workspace_id": receipt.workspace_id,
            "deleted_by": receipt.deleted_by,
            "deleted_at": receipt.deleted_at,
            "retained_tombstone": receipt.retained_tombstone,
        }

    def _require_workspace_exists(self, workspace_id: str) -> Workspace:
        try:
            return self.workspaces[workspace_id]
        except KeyError as error:
            raise HostedTrustError(404, "workspace_not_found", "Workspace not found.") from error

