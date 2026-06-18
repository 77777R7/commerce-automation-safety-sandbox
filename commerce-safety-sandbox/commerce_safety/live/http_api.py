from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..models import to_plain
from ..platform_skins.amazon import AmazonPlatformBinding, AmazonSellerOpsRouter
from ..platform_skins.shopify import (
    ShopifyGraphQLRouter,
    ShopifyOpsRouter,
    ShopifyPlatformBinding,
    load_shopify_coverage,
)
from ..platform_skins.shopify.webhook_mapper import map_shopify_webhook
from ..reporting import is_saas_scenario
from ..twin import TimeoutAfterCommit
from .errors import LiveHTTPError, error_response
from .hosted import AuthContext, HostedTrustError, HostedTrustStore
from .mcp_tools import CommerceMCPTools
from .scenario_registry import ScenarioRegistryError
from .security import (
    SECURITY_HEADERS,
    constant_time_token_matches,
    normalize_api_token,
    validate_live_server_security,
)
from .sessions import SessionManager, SessionNotFoundError


MAX_JSON_BODY_BYTES = 1_048_576
SAAS_TRACE_SERVICES = ("stripe", "slack", "github")


def _saas_environment_state(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        service: snapshot[service]
        for service in SAAS_TRACE_SERVICES
        if service in snapshot
    }


def _optional_positive_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


def security_headers() -> dict[str, str]:
    return dict(SECURITY_HEADERS)


def read_json_object_from_stream(
    stream,
    length: int,
    *,
    max_bytes: int = MAX_JSON_BODY_BYTES,
) -> dict[str, Any]:
    if length > max_bytes:
        raise LiveHTTPError(
            413,
            "request_body_too_large",
            f"JSON request body exceeds the {max_bytes} byte limit.",
        )
    if length == 0:
        return {}
    try:
        raw = stream.read(length).decode("utf-8")
        data = json.loads(raw)
    except UnicodeDecodeError as error:
        raise LiveHTTPError(400, "invalid_json", "Request body must be UTF-8 JSON.") from error
    except json.JSONDecodeError as error:
        raise LiveHTTPError(400, "invalid_json", f"Invalid JSON body: {error.msg}.") from error
    if not isinstance(data, dict):
        raise LiveHTTPError(400, "invalid_json", "JSON body must be an object")
    return data


class LiveAPI:
    def __init__(
        self,
        runs_dir: Path | str = Path("runs"),
        *,
        api_token: str | None = None,
        hosted_trust_store: HostedTrustStore | None = None,
    ):
        self.tools = CommerceMCPTools(runs_dir=runs_dir)
        self.manager: SessionManager = self.tools.manager
        self.api_token = api_token
        self.hosted_trust_store = hosted_trust_store
        self.shopify_graphql = ShopifyGraphQLRouter(self.tools)
        self.shopify = ShopifyOpsRouter(self.tools)
        self.shopify_coverage = load_shopify_coverage()
        self.amazon = AmazonSellerOpsRouter(self.tools)
        self.twin_action_tools = {
            "reserve_inventory": "commerce.reserve_inventory",
            "promise_fulfillment": "commerce.promise_fulfillment",
            "refresh_inventory": "commerce.refresh_inventory",
            "route_manual_review": "commerce.route_manual_review",
            "create_fulfillment": "commerce.create_fulfillment",
            "find_fulfillment": "commerce.find_fulfillment",
            "create_refund": "commerce.create_refund",
            "create_approval_request": "commerce.create_approval_request",
            "cancel_order": "commerce.cancel_order",
            "release_inventory": "commerce.release_inventory",
            "place_workflow_hold": "commerce.place_workflow_hold",
            "submit_warehouse_cancellation_request": (
                "commerce.submit_warehouse_cancellation_request"
            ),
            "warehouse_continue_fulfillment": (
                "commerce.warehouse_continue_fulfillment"
            ),
            "skip_duplicate_webhook": "commerce.skip_duplicate_webhook",
            "stripe_create_customer": "stripe.create_customer",
            "stripe_create_subscription": "stripe.create_subscription",
            "stripe_deliver_webhook": "stripe.deliver_webhook",
            "slack_post_message": "slack.post_message",
            "github_create_check_run": "github.create_check_run",
            "github_create_issue": "github.create_issue",
            "github_comment_on_pr": "github.comment_on_pr",
        }

    def handle(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        try:
            method = method.upper()
            parts = self._path_parts(path)
            payload = body or {}
            request_headers = headers or {}
            auth_context = self._authenticate_hosted(request_headers, payload)
            if auth_context is None:
                auth_error = self._auth_error(request_headers)
                if auth_error is not None:
                    return auth_error
            else:
                self._authorize_hosted_request(
                    auth_context,
                    method=method,
                    parts=parts,
                    body=payload,
                    path=path,
                )

            if method == "GET" and self._matches(
                parts,
                "workspaces",
                "*",
                "sessions",
            ):
                return self._hosted_list_sessions(auth_context, parts[1])
            if method == "POST" and self._matches(
                parts,
                "workspaces",
                "*",
                "export",
            ):
                return self._hosted_export_workspace(auth_context, parts[1])
            if method == "POST" and self._matches(
                parts,
                "workspaces",
                "*",
                "delete",
            ):
                return self._hosted_delete_workspace(auth_context, parts[1])
            if method == "POST" and self._matches(
                parts,
                "workspaces",
                "*",
                "suspend",
            ):
                return self._hosted_suspend_workspace(auth_context, parts[1])
            if method == "POST" and self._matches(
                parts,
                "workspaces",
                "*",
                "tokens",
                "*",
                "revoke",
            ):
                return self._hosted_revoke_token(auth_context, parts[1], parts[3])
            if method == "GET" and self._matches(
                parts,
                "workspaces",
                "*",
                "audit",
            ):
                return self._hosted_audit_log(auth_context, parts[1])
            if method == "GET" and self._matches(
                parts,
                "workspaces",
                "*",
                "sessions",
                "*",
                "artifacts",
                "*",
                "signed-url",
            ):
                return self._hosted_signed_artifact_url(auth_context, parts[1], parts[3], parts[5])
            if method == "GET" and self._matches(
                parts,
                "workspaces",
                "*",
                "sessions",
                "*",
                "artifacts",
                "*",
                "download",
            ):
                return self._hosted_download_artifact(
                    auth_context,
                    parts[1],
                    parts[3],
                    parts[5],
                    path,
                )

            if method == "POST" and parts == ["sessions"]:
                return self._create_session(payload, auth_context)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "tasks",
                "next",
            ):
                return self._get_next_task(parts[1])
            if method == "GET" and self._matches(parts, "sessions", "*", "status"):
                return self._get_session_status(parts[1])
            if method == "POST" and self._matches(parts, "sessions", "*", "reset"):
                return self._reset_session(parts[1])
            if method == "POST" and self._matches(parts, "sessions", "*", "teardown"):
                return self._teardown_session(parts[1])
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "twin",
                "create_fulfillment",
            ):
                return self._create_fulfillment(parts[1], payload)
            if method == "POST" and self._matches(parts, "sessions", "*", "twin", "*"):
                return self._call_twin_action(parts[1], parts[3], payload)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "webhooks",
                "skip_duplicate",
            ):
                return self._skip_shopify_webhook(parts[1], payload, request_headers)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "webhooks",
            ):
                return self._receive_shopify_webhook(parts[1], payload, request_headers)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "admin",
                "api",
                "*",
                "graphql.json",
            ):
                return self._shopify_graphql(parts[1], payload)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "admin",
                "api",
                "*",
                "inventory_levels.json",
            ):
                return self._shopify_inventory_levels(parts[1], path)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "admin",
                "api",
                "*",
                "inventory_levels",
                "adjust.json",
            ):
                return self._shopify_inventory_adjust(parts[1], payload)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "actions",
                "*",
            ):
                return self._shopify_action(parts[1], parts[4], payload)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "coverage",
            ):
                return self._amazon_coverage(parts[1])
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "fba",
                "inventory",
                "v1",
                "summaries",
            ):
                return self._amazon_inventory_summaries(parts[1], path)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "listings",
                "*",
                "items",
                "*",
                "*",
            ):
                return self._amazon_listing_item(parts[1], parts[7], parts[8])
            if method == "PATCH" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "listings",
                "*",
                "items",
                "*",
                "*",
            ):
                return self._amazon_patch_listing_item(parts[1], parts[7], parts[8], payload)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "orders",
                "v0",
                "orders",
                "*",
            ):
                return self._amazon_get_order(parts[1], parts[7])
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "orders",
                "v0",
                "orders",
                "*",
                "orderItems",
            ):
                return self._amazon_get_order_items(parts[1], parts[7])
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "orders",
                "v0",
                "orders",
                "*",
                "shipmentConfirmation",
            ):
                return self._amazon_confirm_shipment(parts[1], parts[7], payload)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "feeds",
                "*",
                "feeds",
            ):
                return self._amazon_create_feed(parts[1], payload)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "sp-api",
                "feeds",
                "*",
                "feeds",
                "*",
            ):
                return self._amazon_get_feed(parts[1], parts[7])
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "notifications",
            ):
                return self._amazon_notification(parts[1], payload)
            if method == "POST" and self._matches(
                parts,
                "sessions",
                "*",
                "amazon",
                "actions",
                "*",
            ):
                return self._amazon_action(parts[1], parts[4], payload)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "shopify",
                "coverage",
            ):
                return self._shopify_coverage(parts[1])
            if method == "GET" and self._matches(parts, "sessions", "*", "trace"):
                return self._get_trace(parts[1])
            if method == "POST" and self._matches(parts, "sessions", "*", "complete"):
                return self._complete_session(parts[1], payload)
            return error_response(404, "not_found", f"Route not found: {method} {path}")
        except LiveHTTPError as error:
            return error_response(error.status_code, error.code, error.message)
        except HostedTrustError as error:
            return error_response(error.status_code, error.code, error.message)
        except SessionNotFoundError as error:
            return error_response(404, "session_not_found", str(error))
        except ScenarioRegistryError as error:
            return error_response(error.status_code, error.code, error.message)
        except FileNotFoundError as error:
            return error_response(404, "file_not_found", str(error))
        except KeyError as error:
            key = str(error).strip("'")
            return error_response(400, "missing_required_field", f"Missing required field: {key}")
        except ValueError as error:
            return error_response(400, "invalid_request", str(error))

    def _create_session(
        self,
        body: dict[str, Any],
        auth_context: AuthContext | None = None,
    ) -> tuple[int, dict[str, Any]]:
        workspace_id = "local"
        created_by = None
        ttl_seconds = _optional_positive_int(body.get("ttl_seconds"), "ttl_seconds")
        retention_days = _optional_positive_int(
            body.get("retention_days"),
            "retention_days",
        )
        if auth_context is not None and self.hosted_trust_store is not None:
            workspace_id = auth_context.workspace_id
            created_by = auth_context.actor_id or auth_context.token_id
            ttl_seconds = self.hosted_trust_store.session_ttl_seconds
            retention_days = self.hosted_trust_store.artifact_retention_days
        session = self.manager.create_session(
            scenario_path=body.get("scenario_path"),
            scenario_id=body.get("scenario_id"),
            workspace_id=workspace_id,
            created_by=created_by,
            ttl_seconds=ttl_seconds,
            retention_days=retention_days,
        )
        if auth_context is not None and self.hosted_trust_store is not None:
            self.hosted_trust_store.audit(
                workspace_id=auth_context.workspace_id,
                actor_type=auth_context.actor_type,
                actor_id=auth_context.actor_id or auth_context.token_id,
                event_type="session.created",
                resource_type="session",
                resource_id=session.session_id,
                metadata={"scenario_id": session.scenario_id},
            )
        return 201, {
            "ok": True,
            "session_id": session.session_id,
            "workspace_id": session.workspace_id,
            "scenario_id": session.scenario_id,
            "scenario_name": session.scenario_name,
            "status": session.status,
            "ttl_expires_at": session.ttl_expires_at,
            "retention_expires_at": session.retention_expires_at,
        }

    def _get_next_task(self, session_id: str) -> tuple[int, dict[str, Any]]:
        task = self.manager.get_next_task(session_id)
        return 200, {
            "ok": True,
            "session_id": session_id,
            "task": task,
            "done": task is None,
        }

    def _get_session_status(self, session_id: str) -> tuple[int, dict[str, Any]]:
        return 200, {"ok": True, **self.manager.session_status(session_id)}

    def _reset_session(self, session_id: str) -> tuple[int, dict[str, Any]]:
        return 200, {"ok": True, **self.manager.reset_session(session_id)}

    def _teardown_session(self, session_id: str) -> tuple[int, dict[str, Any]]:
        return 200, {"ok": True, **self.manager.teardown_session(session_id)}

    def _create_fulfillment(
        self,
        session_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        try:
            fulfillment = session.twin.create_fulfillment(
                order_id=body["order_id"],
                sku=body["sku"],
                quantity=int(body.get("quantity", 1)),
                actor=body.get("actor", "external_agent"),
                webhook_id=body.get("webhook_id"),
                idempotency_key=body.get("idempotency_key"),
                request_id=body.get("request_id"),
                source_event_id=body.get("source_event_id"),
                fault_type=body.get("fault_type"),
            )
        except TimeoutAfterCommit as error:
            return 504, {
                "ok": False,
                "error": "timeout_after_commit",
                "message": "Twin committed the mutation before returning a timeout.",
                "fulfillment_id": error.fulfillment.fulfillment_id,
            }

        return 200, {
            "ok": True,
            "session_id": session_id,
            "fulfillment": to_plain(fulfillment),
        }

    def _call_twin_action(
        self,
        session_id: str,
        action: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        if action not in self.twin_action_tools:
            return 404, {"ok": False, "error": "not_found"}
        payload = {"session_id": session_id, **body}
        return 200, self.tools.call_tool(self.twin_action_tools[action], payload)

    def _receive_shopify_webhook(
        self,
        session_id: str,
        body: dict[str, Any],
        headers: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        binding = ShopifyPlatformBinding.from_twin(session.twin)
        event = map_shopify_webhook(headers, body, binding.order_ids)
        if event["topic"] == "cancel_request":
            session.twin.receive_cancel_request(event)
        else:
            session.twin.receive_webhook(event)
        return 202, {
            "ok": True,
            "session_id": session_id,
            "event": event,
        }

    def _skip_shopify_webhook(
        self,
        session_id: str,
        body: dict[str, Any],
        headers: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        binding = ShopifyPlatformBinding.from_twin(session.twin)
        event = map_shopify_webhook(headers, body, binding.order_ids)
        session.twin.mark_duplicate_skipped(
            actor=body.get("actor", "shopify_like_agent"),
            webhook=event,
        )
        return 200, {
            "ok": True,
            "session_id": session_id,
            "event": "duplicate_webhook_skipped",
            "webhook": event,
        }

    def _shopify_graphql(
        self,
        session_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        binding = ShopifyPlatformBinding.from_twin(session.twin)
        extensions = body.get("extensions") or {}
        actor = (
            extensions.get("actor", "shopify_like_agent")
            if isinstance(extensions, dict)
            else "shopify_like_agent"
        )
        return self.shopify_graphql.handle(
            session_id=session_id,
            body=body,
            actor=actor,
            binding=binding,
        )

    def _shopify_session_binding(self, session_id: str):
        session = self.manager.get_session(session_id)
        return session, ShopifyPlatformBinding.from_twin(session.twin)

    def _shopify_inventory_levels(
        self,
        session_id: str,
        path: str,
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._shopify_session_binding(session_id)
        query = parse_qs(urlparse(path).query)
        inventory_item_ids = query.get("inventory_item_ids") or query.get(
            "inventory_item_id"
        )
        if inventory_item_ids and len(inventory_item_ids) == 1:
            inventory_item_ids = [
                item.strip()
                for item in str(inventory_item_ids[0]).split(",")
                if item.strip()
            ]
        return self.shopify.get_inventory_levels(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            inventory_item_ids=inventory_item_ids,
        )

    def _shopify_inventory_adjust(
        self,
        session_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        _, binding = self._shopify_session_binding(session_id)
        return self.shopify.adjust_inventory_level(
            session_id=session_id,
            binding=binding,
            body=body,
        )

    def _shopify_action(
        self,
        session_id: str,
        action: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        _, binding = self._shopify_session_binding(session_id)
        return self.shopify.run_action(
            session_id=session_id,
            binding=binding,
            action=action,
            body=body,
        )

    def _shopify_coverage(self, session_id: str) -> tuple[int, dict[str, Any]]:
        self.manager.get_session(session_id)
        return self.shopify.coverage_response(session_id)

    def _amazon_session_binding(self, session_id: str):
        session = self.manager.get_session(session_id)
        return session, AmazonPlatformBinding.from_twin(session.twin)

    def _amazon_coverage(self, session_id: str) -> tuple[int, dict[str, Any]]:
        self.manager.get_session(session_id)
        return self.amazon.coverage_response(session_id)

    def _amazon_inventory_summaries(
        self,
        session_id: str,
        path: str,
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._amazon_session_binding(session_id)
        query = parse_qs(urlparse(path).query)
        seller_skus = query.get("sellerSkus") or query.get("sellerSku")
        simulate_rate_limit = (
            query.get("simulateRateLimit", ["false"])[0].lower() == "true"
            or query.get("faultType", [None])[0] == "rate_limit_429"
        )
        return self.amazon.get_inventory_summaries(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            seller_skus=seller_skus,
            simulate_rate_limit=simulate_rate_limit,
        )

    def _amazon_listing_item(
        self,
        session_id: str,
        seller_id: str,
        sku: str,
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._amazon_session_binding(session_id)
        return self.amazon.get_listing_item(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            seller_id=seller_id,
            platform_sku=sku,
        )

    def _amazon_patch_listing_item(
        self,
        session_id: str,
        seller_id: str,
        sku: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._amazon_session_binding(session_id)
        return self.amazon.patch_listing_quantity(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            seller_id=seller_id,
            platform_sku=sku,
            body=body,
        )

    def _amazon_get_order(
        self,
        session_id: str,
        amazon_order_id: str,
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._amazon_session_binding(session_id)
        return self.amazon.get_order(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            amazon_order_id=amazon_order_id,
        )

    def _amazon_get_order_items(
        self,
        session_id: str,
        amazon_order_id: str,
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._amazon_session_binding(session_id)
        return self.amazon.get_order_items(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            amazon_order_id=amazon_order_id,
        )

    def _amazon_confirm_shipment(
        self,
        session_id: str,
        amazon_order_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        _, binding = self._amazon_session_binding(session_id)
        return self.amazon.confirm_shipment(
            session_id=session_id,
            binding=binding,
            amazon_order_id=amazon_order_id,
            body=body,
        )

    def _amazon_create_feed(
        self,
        session_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session, _ = self._amazon_session_binding(session_id)
        return self.amazon.create_feed(
            session_id=session_id,
            twin=session.twin,
            body=body,
        )

    def _amazon_get_feed(
        self,
        session_id: str,
        feed_id: str,
    ) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        return self.amazon.get_feed(
            session_id=session_id,
            feed_id=feed_id,
            twin=session.twin,
        )

    def _amazon_notification(
        self,
        session_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session, binding = self._amazon_session_binding(session_id)
        return self.amazon.inject_notification(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            body=body,
        )

    def _amazon_action(
        self,
        session_id: str,
        action: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        _, binding = self._amazon_session_binding(session_id)
        actions = {
            "promise_fulfillment": self.amazon.promise_fulfillment,
            "route_manual_review": self.amazon.route_manual_review,
            "cancel_order": self.amazon.cancel_order,
            "place_workflow_hold": self.amazon.place_workflow_hold,
            "submit_warehouse_cancellation_request": (
                self.amazon.submit_warehouse_cancellation_request
            ),
        }
        if action not in actions:
            return self.amazon.stub_response(
                session_id=session_id,
                surface=f"actions/{action}",
                reason="unsupported_seller_ops_action",
            )
        return actions[action](
            session_id=session_id,
            binding=binding,
            body=body,
        )

    def _get_trace(self, session_id: str) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        saas_scenario = is_saas_scenario(session.scenario)
        environment_state = session.environment.snapshot_summary()
        return 200, {
            "ok": True,
            "session_id": session_id,
            "scenario_id": session.scenario_id,
            "status": session.status,
            "state_source": "environment" if saas_scenario else "commerce_twin",
            "initial_state": (
                _saas_environment_state(session.initial_environment_state)
                if saas_scenario
                else session.initial_state
            ),
            "current_state": (
                _saas_environment_state(environment_state)
                if saas_scenario
                else session.twin.snapshot_summary()
            ),
            "environment_state": (
                _saas_environment_state(environment_state)
                if saas_scenario
                else environment_state
            ),
            "event_ledger": [to_plain(event) for event in session.environment.events],
            "timeline": [to_plain(event) for event in session.twin.timeline],
        }

    def _complete_session(
        self,
        session_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.manager.complete_session(
            session_id,
            runner_name=body.get("runner_name", "external_agent"),
        )
        return 200, {"ok": True, **result}

    def _path_parts(self, path: str) -> list[str]:
        parsed = urlparse(path)
        return [part for part in parsed.path.split("/") if part]

    def _matches(self, parts: list[str], *pattern: str) -> bool:
        if len(parts) != len(pattern):
            return False
        return all(
            expected == "*" or actual == expected
            for actual, expected in zip(parts, pattern)
        )

    def _authenticate_hosted(
        self,
        headers: dict[str, Any],
        payload: dict[str, Any],
    ) -> AuthContext | None:
        if self.hosted_trust_store is None:
            return None
        context = self.hosted_trust_store.authenticate(headers)
        self.hosted_trust_store.check_rate_limit(context)
        self.hosted_trust_store.check_request_size(payload)
        self.hosted_trust_store.scan_payload(context, payload)
        return context

    def _authorize_hosted_request(
        self,
        context: AuthContext,
        *,
        method: str,
        parts: list[str],
        body: dict[str, Any],
        path: str,
    ) -> None:
        if self.hosted_trust_store is None:
            return
        scope = self._hosted_required_scope(method, parts)
        if scope:
            self.hosted_trust_store.require_scope(context, scope)

        workspace_id = self._hosted_workspace_from_path(parts)
        if workspace_id is not None:
            self.hosted_trust_store.require_workspace(context, workspace_id)

        session_id = self._hosted_session_from_path(parts)
        if session_id is not None:
            session = self.manager.get_session(session_id)
            self.hosted_trust_store.require_workspace(context, session.workspace_id)
            if workspace_id is not None and workspace_id != session.workspace_id:
                raise HostedTrustError(
                    403,
                    "forbidden",
                    "Session does not belong to the requested workspace.",
                )
            if self._hosted_is_mutating(method, parts):
                if session.status == "aborted":
                    raise HostedTrustError(409, "session_aborted", "Session has been aborted.")
                if session.status != "open" and not self._matches(parts, "sessions", "*", "complete"):
                    raise HostedTrustError(409, "session_closed", "Session is no longer open.")
                if session.ttl_expires_at:
                    from datetime import datetime, timezone

                    if datetime.fromisoformat(session.ttl_expires_at) <= datetime.now(timezone.utc):
                        raise HostedTrustError(
                            409,
                            "session_ttl_expired",
                            "Session TTL has expired and no more writes are allowed.",
                        )
                if self._matches(parts, "sessions", "*", "twin", "*"):
                    self.hosted_trust_store.audit(
                        workspace_id=context.workspace_id,
                        actor_type=context.actor_type,
                        actor_id=context.actor_id or context.token_id,
                        event_type="http.twin_action_called",
                        resource_type="session",
                        resource_id=session_id,
                        metadata={"action": parts[3]},
                    )
                if self._matches(parts, "sessions", "*", "complete"):
                    self.hosted_trust_store.audit(
                        workspace_id=context.workspace_id,
                        actor_type=context.actor_type,
                        actor_id=context.actor_id or context.token_id,
                        event_type="session.completed",
                        resource_type="session",
                        resource_id=session_id,
                        metadata={},
                    )
                    self.hosted_trust_store.audit(
                        workspace_id=context.workspace_id,
                        actor_type="system",
                        actor_id="system",
                        event_type="policy_report.generated",
                        resource_type="session",
                        resource_id=session_id,
                        metadata={},
                    )

    def _hosted_required_scope(self, method: str, parts: list[str]) -> str | None:
        if method == "POST" and parts == ["sessions"]:
            return "sessions:create"
        if self._matches(parts, "sessions", "*", "twin", "*"):
            return "twin:call"
        if self._matches(parts, "sessions", "*", "complete"):
            return "twin:call"
        if self._matches(parts, "sessions", "*", "tasks", "next"):
            return "sessions:read"
        if self._matches(parts, "sessions", "*", "trace"):
            return "sessions:read"
        if len(parts) >= 6 and parts[0] == "workspaces" and "artifacts" in parts:
            return "artifacts:read"
        if self._matches(parts, "workspaces", "*", "sessions"):
            return "sessions:read"
        if self._matches(parts, "workspaces", "*", "export"):
            return "workspace:export"
        if self._matches(parts, "workspaces", "*", "delete"):
            return "workspace:delete"
        if self._matches(parts, "workspaces", "*", "suspend"):
            return "tokens:manage"
        if self._matches(parts, "workspaces", "*", "tokens", "*", "revoke"):
            return "tokens:manage"
        if self._matches(parts, "workspaces", "*", "audit"):
            return "audit:read"
        if len(parts) >= 3 and parts[0] == "sessions":
            return "twin:call" if method in {"POST", "PATCH"} else "sessions:read"
        return None

    def _hosted_workspace_from_path(self, parts: list[str]) -> str | None:
        if parts and parts[0] == "workspaces" and len(parts) >= 2:
            return parts[1]
        return None

    def _hosted_session_from_path(self, parts: list[str]) -> str | None:
        if parts and parts[0] == "sessions" and len(parts) >= 2:
            return parts[1]
        if len(parts) >= 4 and parts[0] == "workspaces" and parts[2] == "sessions":
            return parts[3]
        return None

    def _hosted_is_mutating(self, method: str, parts: list[str]) -> bool:
        if method in {"POST", "PATCH"}:
            if parts and parts[0] == "workspaces":
                return False
            return True
        return False

    def _hosted_list_sessions(
        self,
        context: AuthContext | None,
        workspace_id: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        sessions = self.manager.list_sessions(workspace_id=workspace_id)
        return 200, {"ok": True, "workspace_id": workspace_id, "sessions": sessions}

    def _hosted_export_workspace(
        self,
        context: AuthContext | None,
        workspace_id: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        export = self.hosted_trust_store.export_workspace(context, workspace_id)
        return 200, {"ok": True, "export": export}

    def _hosted_delete_workspace(
        self,
        context: AuthContext | None,
        workspace_id: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        receipt = self.hosted_trust_store.delete_workspace(context, workspace_id)
        return 200, {
            "ok": True,
            "deletion_receipt": self.hosted_trust_store.deletion_receipt_to_plain(receipt),
        }

    def _hosted_suspend_workspace(
        self,
        context: AuthContext | None,
        workspace_id: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        workspace = self.hosted_trust_store.suspend_workspace(context, workspace_id)
        return 200, {"ok": True, "workspace_id": workspace.workspace_id, "status": workspace.status}

    def _hosted_revoke_token(
        self,
        context: AuthContext | None,
        workspace_id: str,
        token_id: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        self.hosted_trust_store.require_workspace(context, workspace_id)
        token = self.hosted_trust_store.revoke_token(context, token_id)
        return 200, {"ok": True, "token_id": token.token_id, "revoked_at": token.revoked_at}

    def _hosted_audit_log(
        self,
        context: AuthContext | None,
        workspace_id: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        events = [
            self.hosted_trust_store.audit_event_to_plain(event)
            for event in self.hosted_trust_store.audit_events
            if event.workspace_id == workspace_id
        ]
        return 200, {"ok": True, "workspace_id": workspace_id, "audit_events": events}

    def _hosted_signed_artifact_url(
        self,
        context: AuthContext | None,
        workspace_id: str,
        session_id: str,
        artifact_path: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        self.manager.get_session(session_id)
        signed = self.hosted_trust_store.sign_artifact_url(
            workspace_id=workspace_id,
            session_id=session_id,
            artifact_path=artifact_path,
        )
        return 200, {"ok": True, **signed}

    def _hosted_download_artifact(
        self,
        context: AuthContext | None,
        workspace_id: str,
        session_id: str,
        artifact_path: str,
        path: str,
    ) -> tuple[int, dict[str, Any]]:
        assert context is not None and self.hosted_trust_store is not None
        query = parse_qs(urlparse(path).query)
        self.hosted_trust_store.validate_artifact_signature(
            workspace_id=workspace_id,
            session_id=session_id,
            artifact_path=artifact_path,
            expires=(query.get("expires") or [None])[0],
            signature=(query.get("signature") or [None])[0],
        )
        session = self.manager.get_session(session_id)
        artifact_file = session.output_path / artifact_path
        if not artifact_file.is_file():
            raise HostedTrustError(404, "artifact_not_found", "Artifact not found.")
        self.hosted_trust_store.audit(
            workspace_id=workspace_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id or context.token_id,
            event_type="artifact.downloaded",
            resource_type="artifact",
            resource_id=artifact_path,
            metadata={"session_id": session_id},
        )
        return 200, {
            "ok": True,
            "workspace_id": workspace_id,
            "session_id": session_id,
            "artifact_path": artifact_path,
            "content": artifact_file.read_text(encoding="utf-8"),
        }

    def _auth_error(self, headers: dict[str, Any]) -> tuple[int, dict[str, Any]] | None:
        if not self.api_token:
            return None
        normalized = {str(key).lower(): str(value) for key, value in headers.items()}
        auth_header = normalized.get("authorization", "")
        token_header = normalized.get("x-commerce-safety-token", "")
        expected_bearer = f"Bearer {self.api_token}"
        if constant_time_token_matches(auth_header, expected_bearer):
            return None
        if constant_time_token_matches(token_header, self.api_token):
            return None
        return error_response(401, "unauthorized", "Missing or invalid local auth token.")


class LiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        runs_dir: Path | str,
        api_token: str | None = None,
    ):
        super().__init__(server_address, LiveHTTPRequestHandler)
        self.api = LiveAPI(runs_dir=runs_dir, api_token=api_token)


class LiveHTTPRequestHandler(BaseHTTPRequestHandler):
    server: LiveHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        try:
            status, payload = self.server.api.handle(
                "POST",
                self.path,
                self._read_json(),
                headers=dict(self.headers.items()),
            )
        except LiveHTTPError as error:
            status, payload = error_response(error.status_code, error.code, error.message)
        self._send_json(status, payload)

    def do_GET(self) -> None:
        status, payload = self.server.api.handle(
            "GET",
            self.path,
            {},
            headers=dict(self.headers.items()),
        )
        self._send_json(status, payload)

    def do_PATCH(self) -> None:
        try:
            status, payload = self.server.api.handle(
                "PATCH",
                self.path,
                self._read_json(),
                headers=dict(self.headers.items()),
            )
        except LiveHTTPError as error:
            status, payload = error_response(error.status_code, error.code, error.message)
        self._send_json(status, payload)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        return read_json_object_from_stream(self.rfile, length)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for header, value in security_headers().items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(body)


def create_live_http_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    runs_dir: Path | str = Path("runs"),
    api_token: str | None = None,
) -> LiveHTTPServer:
    normalized_token = normalize_api_token(api_token)
    validate_live_server_security(host, normalized_token)
    return LiveHTTPServer((host, port), runs_dir=runs_dir, api_token=normalized_token)


def serve_live_http(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    runs_dir: Path | str = Path("runs"),
    api_token: str | None = None,
) -> int:
    resolved_token = normalize_api_token(
        api_token or os.environ.get("COMMERCE_SAFETY_API_TOKEN")
    )
    server = create_live_http_server(
        host=host,
        port=port,
        runs_dir=runs_dir,
        api_token=resolved_token,
    )
    actual_host, actual_port = server.server_address
    print(
        f"Commerce Safety live server listening on http://{actual_host}:{actual_port}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
