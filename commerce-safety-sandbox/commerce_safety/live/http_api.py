from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..models import to_plain
from ..platform_skins.amazon import AmazonPlatformBinding, AmazonSellerOpsRouter
from ..platform_skins.shopify import (
    ShopifyGraphQLRouter,
    ShopifyPlatformBinding,
    load_shopify_coverage,
)
from ..platform_skins.shopify.webhook_mapper import map_shopify_webhook
from ..twin import TimeoutAfterCommit
from .mcp_tools import CommerceMCPTools
from .sessions import SessionManager


class LiveAPI:
    def __init__(self, runs_dir: Path | str = Path("runs")):
        self.tools = CommerceMCPTools(runs_dir=runs_dir)
        self.manager: SessionManager = self.tools.manager
        self.shopify_graphql = ShopifyGraphQLRouter(self.tools)
        self.shopify_coverage = load_shopify_coverage()
        self.amazon = AmazonSellerOpsRouter(self.tools)
        self.twin_action_tools = {
            "reserve_inventory",
            "promise_fulfillment",
            "refresh_inventory",
            "route_manual_review",
            "create_fulfillment",
            "find_fulfillment",
            "create_refund",
            "create_approval_request",
            "cancel_order",
            "release_inventory",
            "place_workflow_hold",
            "submit_warehouse_cancellation_request",
            "warehouse_continue_fulfillment",
            "skip_duplicate_webhook",
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

            if method == "POST" and parts == ["sessions"]:
                return self._create_session(payload)
            if method == "GET" and self._matches(
                parts,
                "sessions",
                "*",
                "tasks",
                "next",
            ):
                return self._get_next_task(parts[1])
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
            return 404, {"ok": False, "error": "not_found"}
        except (FileNotFoundError, KeyError, ValueError) as error:
            return 400, {"ok": False, "error": str(error)}

    def _create_session(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        scenario_path = body.get("scenario_path")
        if not scenario_path:
            raise ValueError("scenario_path is required")
        session = self.manager.create_session(Path(scenario_path))
        return 201, {
            "ok": True,
            "session_id": session.session_id,
            "scenario_id": session.scenario_id,
            "scenario_name": session.scenario_name,
            "status": session.status,
        }

    def _get_next_task(self, session_id: str) -> tuple[int, dict[str, Any]]:
        task = self.manager.get_next_task(session_id)
        return 200, {
            "ok": True,
            "session_id": session_id,
            "task": task,
            "done": task is None,
        }

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
        return 200, self.tools.call_tool(f"commerce.{action}", payload)

    def _receive_shopify_webhook(
        self,
        session_id: str,
        body: dict[str, Any],
        headers: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        binding = ShopifyPlatformBinding.from_twin(session.twin)
        event = map_shopify_webhook(headers, body, binding.order_ids)
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

    def _shopify_coverage(self, session_id: str) -> tuple[int, dict[str, Any]]:
        self.manager.get_session(session_id)
        return 200, {
            "ok": True,
            "session_id": session_id,
            "coverage": self.shopify_coverage.as_dict(),
        }

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
        return self.amazon.get_inventory_summaries(
            session_id=session_id,
            twin=session.twin,
            binding=binding,
            seller_skus=seller_skus,
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
        self.manager.get_session(session_id)
        return self.amazon.get_feed(session_id=session_id, feed_id=feed_id)

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
            return 404, {"ok": False, "error": "not_found"}
        return actions[action](
            session_id=session_id,
            binding=binding,
            body=body,
        )

    def _get_trace(self, session_id: str) -> tuple[int, dict[str, Any]]:
        session = self.manager.get_session(session_id)
        return 200, {
            "ok": True,
            "session_id": session_id,
            "scenario_id": session.scenario_id,
            "status": session.status,
            "initial_state": session.initial_state,
            "current_state": session.twin.snapshot_summary(),
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


class LiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        runs_dir: Path | str,
    ):
        super().__init__(server_address, LiveHTTPRequestHandler)
        self.api = LiveAPI(runs_dir=runs_dir)


class LiveHTTPRequestHandler(BaseHTTPRequestHandler):
    server: LiveHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        status, payload = self.server.api.handle(
            "POST",
            self.path,
            self._read_json(),
            headers=dict(self.headers.items()),
        )
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
        status, payload = self.server.api.handle(
            "PATCH",
            self.path,
            self._read_json(),
            headers=dict(self.headers.items()),
        )
        self._send_json(status, payload)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_live_http_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    runs_dir: Path | str = Path("runs"),
) -> LiveHTTPServer:
    return LiveHTTPServer((host, port), runs_dir=runs_dir)


def serve_live_http(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    runs_dir: Path | str = Path("runs"),
) -> int:
    server = create_live_http_server(host=host, port=port, runs_dir=runs_dir)
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
