from __future__ import annotations

from typing import Any

from ...models import to_plain
from .binding import AmazonPlatformBinding
from .coverage import load_amazon_coverage


class AmazonSellerOpsRouter:
    def __init__(self, tools: Any):
        self.tools = tools
        self.coverage = load_amazon_coverage()

    def coverage_response(self, session_id: str) -> tuple[int, dict[str, Any]]:
        return 200, {
            "ok": True,
            "session_id": session_id,
            "coverage": self.coverage.as_dict(),
        }

    def stub_response(
        self,
        *,
        session_id: str,
        surface: str,
        reason: str = "unsupported_amazon_seller_ops_surface",
    ) -> tuple[int, dict[str, Any]]:
        return 200, {
            "ok": True,
            "session_id": session_id,
            "_commerce_twin_stub": True,
            "coverage": "stub",
            "stub": {
                "skin": "amazon_seller_ops",
                "surface": surface,
                "status": self.coverage.route_status(surface),
                "reason": reason,
                "contract": "explicit_stub_not_full_sp_api",
            },
            "_commerce_twin": {
                "coverage": "stub",
                "stub": True,
                "unsupportedSurface": surface,
            },
        }

    def get_inventory_summaries(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: AmazonPlatformBinding,
        seller_skus: list[str] | None = None,
        simulate_rate_limit: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        if simulate_rate_limit:
            return self._rate_limit(
                session_id=session_id,
                twin=twin,
                operation="getInventorySummaries",
            )
        summaries = []
        for sku, inventory in twin.inventory.items():
            if seller_skus:
                resolved = [
                    binding.resolve_sku(seller_sku)[0] or str(seller_sku)
                    for seller_sku in seller_skus
                ]
                if sku not in resolved:
                    continue
            seller_sku = binding.seller_sku_for(sku)
            if seller_skus and sku not in seller_skus and seller_sku not in seller_skus:
                continue
            summaries.append(
                {
                    "sellerSku": seller_sku,
                    "asin": binding.asin_for_sku(sku),
                    "fnSku": binding.fnsku_for_sku(sku),
                    "condition": "NewItem",
                    "marketplaceId": binding.marketplace_id,
                    "inventoryDetails": {
                        "fulfillableQuantity": inventory.available,
                        "totalReservedQuantity": inventory.reserved,
                        "pendingCustomerOrderQuantity": inventory.committed,
                        "totalQuantity": inventory.on_hand,
                    },
                    "_commerce_twin": {
                        "coverage": "stateful",
                        "canonicalSku": sku,
                        "sellerId": binding.seller_id,
                        "sellerAliases": list(binding.seller_aliases),
                        "marketplaceIds": binding.marketplace_ids_for_sku(sku),
                        "snapshotVersion": inventory.source_version,
                        "lastSyncedAt": inventory.last_synced_at,
                        "trueAvailable": inventory.true_available,
                    },
                }
            )
        twin.add_event(
            actor="amazon_seller_ops_skin",
            event="amazon_inventory_summaries_read",
            message="Amazon-shaped FBA inventory summaries were read.",
            details={
                "seller_skus": seller_skus,
                "summary_count": len(summaries),
                "source": "getInventorySummaries",
                "seller_id": binding.seller_id,
                "marketplace_id": binding.marketplace_id,
            },
        )
        return 200, {
            "ok": True,
            "session_id": session_id,
            "payload": {"inventorySummaries": summaries},
        }

    def get_listing_item(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: AmazonPlatformBinding,
        seller_id: str,
        platform_sku: str,
        simulate_rate_limit: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        if simulate_rate_limit:
            return self._rate_limit(
                session_id=session_id,
                twin=twin,
                operation="getListingsItem",
            )
        sku, _ = binding.resolve_sku(platform_sku)
        if not sku:
            raise ValueError(f"unknown Amazon SKU: {platform_sku}")
        inventory = twin.inventory[sku]
        live_quantity = (
            inventory.true_available
            if inventory.true_available is not None
            else inventory.available
        )
        twin.add_event(
            actor="amazon_seller_ops_skin",
            event="amazon_listing_item_read",
            message=f"Amazon-shaped listing item read for {sku}.",
            details={
                "seller_id": seller_id,
                "known_seller": binding.is_known_seller(seller_id),
                "seller_sku": platform_sku,
                "canonical_sku": sku,
                "marketplace_id": binding.marketplace_id,
                "submitted_quantity": inventory.available,
                "live_quantity": live_quantity,
            },
        )
        return 200, {
            "ok": True,
            "session_id": session_id,
            "sku": sku,
            "sellerId": seller_id,
            "sellerBinding": {
                "expectedSellerId": binding.seller_id,
                "aliases": list(binding.seller_aliases),
                "knownSeller": binding.is_known_seller(seller_id),
            },
            "summaries": [
                {
                    "marketplaceId": marketplace_id,
                    "asin": binding.asin_for_sku(sku),
                }
                for marketplace_id in binding.marketplace_ids_for_sku(sku)
            ],
            "attributes": {
                "fulfillment_availability": [
                    {
                        "fulfillment_channel_code": "DEFAULT",
                        "marketplace_id": binding.marketplace_id,
                        "quantity": inventory.available,
                    }
                ]
            },
            "fulfillmentAvailability": [
                {
                    "fulfillmentChannelCode": "DEFAULT",
                    "marketplaceId": binding.marketplace_id,
                    "quantity": live_quantity,
                }
            ],
            "_commerce_twin": {
                "coverage": "stateful",
                "canonicalSku": sku,
                "sellerSku": binding.seller_sku_for(sku),
                "submittedQuantity": inventory.available,
                "liveQuantity": live_quantity,
                "snapshotVersion": inventory.source_version,
            },
        }

    def patch_listing_quantity(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: AmazonPlatformBinding,
        seller_id: str,
        platform_sku: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        if _simulate_rate_limit(body):
            return self._rate_limit(
                session_id=session_id,
                twin=twin,
                operation="patchListingsItem",
            )
        sku, _ = binding.resolve_sku(platform_sku)
        if not sku:
            raise ValueError(f"unknown Amazon SKU: {platform_sku}")
        quantity = _extract_quantity(body)
        twin.add_event(
            actor=body.get("actor", "amazon_like_agent"),
            event="amazon_listing_quantity_patch_submitted",
            message=f"Amazon-shaped listing quantity patch submitted for {sku}.",
            details={
                "seller_id": seller_id,
                "known_seller": binding.is_known_seller(seller_id),
                "marketplace_id": binding.marketplace_id,
                "sku": sku,
                "quantity": quantity,
                "processing_state": "accepted_not_processed",
            },
        )
        return 202, {
            "ok": True,
            "session_id": session_id,
            "sku": sku,
            "status": "ACCEPTED",
            "_commerce_twin": {
                "coverage": "stateful",
                "processing_state": "accepted_not_processed",
                "retryable": True,
                "next_step": "read feed or listing processing report before trusting submitted quantity",
            },
        }

    def create_feed(
        self,
        *,
        session_id: str,
        twin: Any,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        session = self.tools.manager.get_session(session_id)
        with session.lock:
            feed_id = f"feed_{session.next_amazon_feed:03d}"
            session.next_amazon_feed += 1
            message_count = (
                len(body.get("messages", []))
                if isinstance(body.get("messages"), list)
                else 1
            )
            result_document_id = f"feed_result_{feed_id}"
            feed = {
                "feedId": feed_id,
                "feedType": body.get("feedType", "POST_ORDER_FULFILLMENT_DATA"),
                "processingStatus": "IN_QUEUE",
                "resultFeedDocumentId": result_document_id,
                "processingReport": {
                    "documentId": result_document_id,
                    "processingSummary": {
                        "messagesProcessed": message_count,
                        "messagesSuccessful": message_count,
                        "messagesWithError": 0,
                        "messagesWithWarning": 0,
                    },
                    "results": [],
                },
                "_commerce_twin": {
                    "coverage": "stateful",
                    "processing_state": "accepted_not_processed",
                    "report_available_after": "getFeed",
                },
            }
            session.amazon_feeds[feed_id] = feed
            twin.add_event(
                actor=body.get("actor", "amazon_like_agent"),
                event="amazon_feed_submitted",
                message=f"Amazon-shaped feed {feed_id} submitted.",
                details=dict(feed),
            )
            return 202, {"ok": True, "session_id": session_id, "payload": dict(feed)}

    def get_feed(
        self,
        *,
        session_id: str,
        feed_id: str,
        twin: Any | None = None,
    ) -> tuple[int, dict[str, Any]]:
        session = self.tools.manager.get_session(session_id)
        with session.lock:
            feed = session.amazon_feeds.get(feed_id)
            if not feed:
                return 404, {
                    "ok": False,
                    "error": {
                        "code": "amazon_feed_not_found",
                        "message": f"Amazon feed not found in this session: {feed_id}",
                        "status": 404,
                    },
                }
            if feed["processingStatus"] == "IN_QUEUE":
                feed["processingStatus"] = "DONE"
                feed["_commerce_twin"]["processing_state"] = "processed_with_report"
                if twin is not None:
                    twin.add_event(
                        actor="amazon_seller_ops_skin",
                        event="amazon_feed_processing_report_ready",
                        message=(
                            f"Amazon-shaped feed {feed_id} finished with a "
                            "processing report."
                        ),
                        details={
                            "feedId": feed_id,
                            "processingStatus": feed["processingStatus"],
                            "resultFeedDocumentId": feed["resultFeedDocumentId"],
                            "processingSummary": feed["processingReport"][
                                "processingSummary"
                            ],
                        },
                    )
            return 200, {"ok": True, "session_id": session_id, "payload": dict(feed)}

    def get_order(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: AmazonPlatformBinding,
        amazon_order_id: str,
    ) -> tuple[int, dict[str, Any]]:
        order_id, _ = binding.resolve_order_id(amazon_order_id)
        if not order_id:
            raise ValueError(f"unknown Amazon order: {amazon_order_id}")
        order = twin.orders[order_id]
        return 200, {
            "ok": True,
            "session_id": session_id,
            "payload": {
                "AmazonOrderId": amazon_order_id,
                "OrderStatus": _amazon_order_status(order.order_status),
                "FulfillmentChannel": "MFN",
                "NumberOfItemsShipped": 0,
                "NumberOfItemsUnshipped": sum(item.quantity for item in order.line_items),
                "_commerce_twin": {"canonicalOrderId": order_id},
            },
        }

    def get_order_items(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: AmazonPlatformBinding,
        amazon_order_id: str,
    ) -> tuple[int, dict[str, Any]]:
        order_id, _ = binding.resolve_order_id(amazon_order_id)
        if not order_id:
            raise ValueError(f"unknown Amazon order: {amazon_order_id}")
        order = twin.orders[order_id]
        items = []
        for index, item in enumerate(order.line_items):
            items.append(
                {
                    "OrderItemId": f"{amazon_order_id}-{index}",
                    "SellerSKU": binding.seller_sku_for(item.sku),
                    "ASIN": binding.asin_for_sku(item.sku),
                    "QuantityOrdered": item.quantity,
                    "_commerce_twin": {"canonicalSku": item.sku},
                }
            )
        return 200, {"ok": True, "session_id": session_id, "payload": {"OrderItems": items}}

    def confirm_shipment(
        self,
        *,
        session_id: str,
        binding: AmazonPlatformBinding,
        amazon_order_id: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        if _simulate_rate_limit(body):
            session = self.tools.manager.get_session(session_id)
            return self._rate_limit(
                session_id=session_id,
                twin=session.twin,
                operation="confirmShipment",
            )
        order_id, _ = binding.resolve_order_id(amazon_order_id)
        if not order_id:
            raise ValueError(f"unknown Amazon order: {amazon_order_id}")
        session = self.tools.manager.get_session(session_id)
        order = session.twin.orders[order_id]
        warehouse_job = next(
            (job for job in session.twin.warehouse_jobs if job.order_id == order_id),
            None,
        )
        cancel_events = [
            event
            for event in session.twin.timeline
            if event.event == "cancel_request_received"
            and event.details.get("order_id") == order_id
        ]
        before_confirmation = {
            "order_status": order.order_status,
            "cancel_requested": order.cancel_requested,
            "warehouse_status": warehouse_job.status if warehouse_job else None,
            "warehouse_hold_status": warehouse_job.hold_status if warehouse_job else None,
            "cancel_event_ids": [event.details.get("id") for event in cancel_events],
        }
        result = self.tools.call_tool(
            "commerce.warehouse_continue_fulfillment",
            {
                "session_id": session_id,
                "order_id": order_id,
                "actor": body.get("actor", "amazon_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or f"amazon_confirm_shipment_{amazon_order_id}",
                "new_status": "shipped",
            },
        )
        session.twin.add_event(
            actor=body.get("actor", "amazon_like_agent"),
            event="amazon_shipment_confirmed",
            message=f"Amazon-shaped confirmShipment was called for {amazon_order_id}.",
            details={
                "amazon_order_id": amazon_order_id,
                "canonical_order_id": order_id,
                "packageDetail": body.get("packageDetail", {}),
                "before_confirmation": before_confirmation,
                "cancel_requested_before_confirmation": before_confirmation[
                    "cancel_requested"
                ],
                "warehouse_status_before_confirmation": before_confirmation[
                    "warehouse_status"
                ],
                "risk_signal": (
                    "confirmShipment_after_buyer_cancel"
                    if before_confirmation["cancel_requested"]
                    else None
                ),
            },
        )
        return 200, {
            "ok": True,
            "session_id": session_id,
            "payload": {
                "AmazonOrderId": amazon_order_id,
                "shipmentStatus": "confirmed",
                "warehouseJob": result["warehouse_job"],
            },
        }

    def inject_notification(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: AmazonPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        notification_type = body.get("notificationType")
        payload = body.get("payload") or {}
        if notification_type == "ORDER_CHANGE":
            amazon_order_id = payload.get("AmazonOrderId")
            order_id, _ = binding.resolve_order_id(amazon_order_id)
            if not order_id:
                raise ValueError(f"unknown Amazon order: {amazon_order_id}")
            order = twin.orders[order_id]
            event = {
                "type": "cancel_request",
                "id": f"amazon_order_change_{amazon_order_id}",
                "order_id": order_id,
                "amount": order.captured_amount or 0,
                "reason": "buyer_cancelled",
                "amazon_order_id": amazon_order_id,
                "raw_notification_type": notification_type,
            }
            twin.receive_cancel_request(event)
            twin.add_event(
                actor="amazon_seller_ops_skin",
                event="amazon_buyer_cancel_received",
                message=(
                    f"Amazon ORDER_CHANGE buyer cancellation received for "
                    f"{amazon_order_id}."
                ),
                details={
                    "amazon_order_id": amazon_order_id,
                    "canonical_order_id": order_id,
                    "order_change_type": payload.get("OrderChangeType"),
                    "warehouse_jobs_at_cancel": [
                        to_plain(job)
                        for job in twin.warehouse_jobs
                        if job.order_id == order_id
                    ],
                    "next_safe_step": (
                        "place workflow hold and request warehouse cancellation "
                        "before confirmShipment"
                    ),
                },
            )
            return 202, {"ok": True, "session_id": session_id, "event": event}
        if notification_type == "LISTINGS_ITEM_MFN_QUANTITY_CHANGE":
            seller_sku = payload.get("SellerSKU") or payload.get("sellerSku")
            sku, _ = binding.resolve_sku(seller_sku)
            if not sku:
                raise ValueError(f"unknown Amazon SKU: {seller_sku}")
            event = {
                "type": "inventory_quantity_change",
                "id": f"amazon_mfn_quantity_change_{sku}",
                "sku": sku,
                "seller_sku": seller_sku,
                "quantity": payload.get("Quantity") or payload.get("quantity"),
                "raw_notification_type": notification_type,
            }
            twin.add_event(
                actor="amazon_seller_ops_skin",
                event="amazon_inventory_quantity_change_received",
                message=f"Amazon MFN quantity change received for {sku}.",
                details=event,
            )
            return 202, {"ok": True, "session_id": session_id, "event": event}
        _, response = self.stub_response(
            session_id=session_id,
            surface=f"notification:{notification_type}",
            reason="unsupported_notification",
        )
        response["event"] = {
            "type": "unsupported_notification",
            "raw_notification_type": notification_type,
        }
        return 202, response

    def promise_fulfillment(
        self,
        *,
        session_id: str,
        binding: AmazonPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        order_id = _resolve_order_id_or_raise(binding, body)
        sku = _resolve_sku_or_raise(binding, body)
        result = self.tools.call_tool(
            "commerce.promise_fulfillment",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "quantity": int(body.get("quantity", body.get("Quantity", 1))),
                "actor": body.get("actor", "amazon_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
                "reservation_id": body.get("reservationId"),
            },
        )
        return 200, result

    def route_manual_review(
        self,
        *,
        session_id: str,
        binding: AmazonPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        order_id = _resolve_order_id_or_raise(binding, body)
        sku = _resolve_sku_or_raise(binding, body)
        result = self.tools.call_tool(
            "commerce.route_manual_review",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "actor": body.get("actor", "amazon_like_agent"),
                "reason": body.get("reason", "manual_review_required"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def cancel_order(
        self,
        *,
        session_id: str,
        binding: AmazonPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        order_id = _resolve_order_id_or_raise(binding, body)
        result = self.tools.call_tool(
            "commerce.cancel_order",
            {
                "session_id": session_id,
                "order_id": order_id,
                "actor": body.get("actor", "amazon_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def place_workflow_hold(
        self,
        *,
        session_id: str,
        binding: AmazonPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        order_id = _resolve_order_id_or_raise(binding, body)
        sku = _resolve_sku_or_raise(binding, body, required=False)
        result = self.tools.call_tool(
            "commerce.place_workflow_hold",
            {
                "session_id": session_id,
                "order_id": order_id,
                "sku": sku,
                "actor": body.get("actor", "amazon_like_agent"),
                "reason": body.get("reason", "workflow_hold_required"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def submit_warehouse_cancellation_request(
        self,
        *,
        session_id: str,
        binding: AmazonPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        order_id = _resolve_order_id_or_raise(binding, body)
        result = self.tools.call_tool(
            "commerce.submit_warehouse_cancellation_request",
            {
                "session_id": session_id,
                "order_id": order_id,
                "actor": body.get("actor", "amazon_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def _rate_limit(
        self,
        *,
        session_id: str,
        twin: Any,
        operation: str,
        retry_after_seconds: int = 2,
    ) -> tuple[int, dict[str, Any]]:
        twin.add_event(
            actor="amazon_seller_ops_skin",
            event="amazon_rate_limit_injected",
            message=(
                f"Amazon-shaped {operation} returned a retryable 429 rate limit."
            ),
            details={
                "operation": operation,
                "retry_after_seconds": retry_after_seconds,
                "retryable": True,
            },
        )
        return 429, {
            "ok": False,
            "session_id": session_id,
            "error": "rate_limited",
            "message": "Amazon-shaped operation hit a retryable rate limit.",
            "retryAfterSeconds": retry_after_seconds,
            "_commerce_twin": {
                "coverage": "stateful",
                "fault": "rate_limit_429",
                "operation": operation,
                "retryable": True,
            },
        }


def _resolve_order_id_or_raise(
    binding: AmazonPlatformBinding,
    body: dict[str, Any],
) -> str:
    order_id, _ = binding.resolve_order_id(
        body.get("amazonOrderId")
        or body.get("AmazonOrderId")
        or body.get("order_id")
        or body.get("orderId")
    )
    if not order_id:
        raise ValueError("Amazon action requires a known amazonOrderId")
    return order_id


def _resolve_sku_or_raise(
    binding: AmazonPlatformBinding,
    body: dict[str, Any],
    *,
    required: bool = True,
) -> str | None:
    sku, _ = binding.resolve_sku(
        body.get("sellerSku")
        or body.get("SellerSKU")
        or body.get("sku")
        or body.get("asin")
        or body.get("ASIN")
    )
    if required and not sku:
        raise ValueError("Amazon action requires a known sellerSku")
    return sku


def _extract_quantity(body: dict[str, Any]) -> int:
    if "quantity" in body:
        return int(body["quantity"])
    patches = body.get("patches") or []
    for patch in patches:
        value = patch.get("value") if isinstance(patch, dict) else None
        if isinstance(value, list) and value and isinstance(value[0], dict):
            if "quantity" in value[0]:
                return int(value[0]["quantity"])
    return 0


def _simulate_rate_limit(body: dict[str, Any]) -> bool:
    return bool(body.get("simulateRateLimit")) or body.get("faultType") == "rate_limit_429"


def _amazon_order_status(status: str) -> str:
    mapping = {
        "open": "Unshipped",
        "paid": "Unshipped",
        "pending_promise": "Unshipped",
        "cancelled": "Canceled",
        "fulfilled": "Shipped",
    }
    return mapping.get(status, status)
