from __future__ import annotations

from typing import Any

from ...models import to_plain
from .binding import ShopifyPlatformBinding
from .coverage import load_shopify_coverage


class ShopifyOpsRouter:
    def __init__(self, tools: Any):
        self.tools = tools
        self.coverage = load_shopify_coverage()

    def coverage_response(self, session_id: str) -> tuple[int, dict[str, Any]]:
        return 200, {
            "ok": True,
            "session_id": session_id,
            "coverage": self.coverage.as_dict(),
        }

    def get_inventory_levels(
        self,
        *,
        session_id: str,
        twin: Any,
        binding: ShopifyPlatformBinding,
        inventory_item_ids: list[str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        levels = []
        for sku, inventory in twin.inventory.items():
            if inventory_item_ids:
                resolved = [
                    binding.resolve_sku(inventory_item_id)[0]
                    for inventory_item_id in inventory_item_ids
                ]
                if sku not in resolved and sku not in inventory_item_ids:
                    continue
            levels.append(
                {
                    "inventory_item_id": _shopify_inventory_item_gid(sku),
                    "sku": sku,
                    "location_id": "gid://shopify/Location/primary",
                    "available": inventory.available,
                    "_commerce_twin": {
                        "coverage": "stateful",
                        "reserved": inventory.reserved,
                        "committed": inventory.committed,
                        "true_available": inventory.true_available,
                        "source_version": inventory.source_version,
                        "last_synced_at": inventory.last_synced_at,
                    },
                }
            )
        twin.add_event(
            actor="shopify_like_skin",
            event="shopify_inventory_levels_read",
            message="Shopify-like inventory levels were read.",
            details={
                "inventory_item_ids": inventory_item_ids,
                "level_count": len(levels),
            },
        )
        return 200, {
            "ok": True,
            "session_id": session_id,
            "inventory_levels": levels,
        }

    def adjust_inventory_level(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        action = _inventory_action(body)
        order_id = _resolve_order_id_or_raise(binding, body)
        sku = _resolve_sku_or_raise(binding, body)
        quantity = _positive_quantity(body)
        actor = body.get("actor", "shopify_like_agent")
        source_event_id = body.get("sourceEventId") or body.get("source_event_id")
        webhook_id = body.get("webhookId") or body.get("webhook_id")

        if action == "reserve_inventory":
            result = self.tools.call_tool(
                "commerce.reserve_inventory",
                {
                    "session_id": session_id,
                    "order_id": order_id,
                    "sku": sku,
                    "quantity": quantity,
                    "actor": actor,
                    "webhook_id": webhook_id,
                },
            )
            return 200, {
                "ok": True,
                "session_id": session_id,
                "inventory_adjustment": {
                    "action": action,
                    "sku": sku,
                    "quantity": quantity,
                    "reservation": result.get("reservation"),
                },
            }

        if action == "release_inventory":
            result = self.tools.call_tool(
                "commerce.release_inventory",
                {
                    "session_id": session_id,
                    "order_id": order_id,
                    "sku": sku,
                    "quantity": quantity,
                    "actor": actor,
                    "source_event_id": source_event_id,
                },
            )
            return 200, {
                "ok": True,
                "session_id": session_id,
                "inventory_adjustment": {
                    "action": action,
                    "sku": sku,
                    "quantity": quantity,
                    "inventory_release": result.get("inventory_release"),
                },
            }

        return 200, {
            "ok": True,
            "session_id": session_id,
            "_commerce_twin_stub": True,
            "coverage": "contract_only",
            "message": "Inventory adjustment reason is recorded as contract-only.",
        }

    def run_action(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        action: str,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        actions = {
            "promise_fulfillment": self.promise_fulfillment,
            "route_manual_review": self.route_manual_review,
            "create_approval_request": self.create_approval_request,
            "cancel_order": self.cancel_order,
            "release_inventory": self.release_inventory,
            "place_fulfillment_hold": self.place_fulfillment_hold,
            "submit_fulfillment_cancellation_request": (
                self.submit_fulfillment_cancellation_request
            ),
            "warehouse_continue_fulfillment": self.warehouse_continue_fulfillment,
        }
        if action not in actions:
            return 404, {"ok": False, "error": "not_found"}
        return actions[action](
            session_id=session_id,
            binding=binding,
            body=body,
        )

    def promise_fulfillment(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.promise_fulfillment",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "sku": _resolve_sku_or_raise(binding, body),
                "quantity": _positive_quantity(body),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
                "reservation_id": body.get("reservationId")
                or body.get("reservation_id"),
            },
        )
        return 200, result

    def route_manual_review(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.route_manual_review",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "sku": _resolve_sku_or_raise(binding, body),
                "actor": body.get("actor", "shopify_like_agent"),
                "reason": body.get("reason", "manual_review_required"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def create_approval_request(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.create_approval_request",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "amount": float(body.get("amount") or body.get("Amount")),
                "reason": body.get("reason", "buyer_request"),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
                "required_policy": body.get(
                    "requiredPolicy",
                    body.get(
                        "required_policy",
                        "no_refund_after_shipment_without_approval",
                    ),
                ),
            },
        )
        return 200, result

    def cancel_order(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.cancel_order",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def release_inventory(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.release_inventory",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "sku": _resolve_sku_or_raise(binding, body),
                "quantity": _positive_quantity(body),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def place_fulfillment_hold(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.place_workflow_hold",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "sku": _resolve_sku(binding, body),
                "actor": body.get("actor", "shopify_like_agent"),
                "reason": body.get("reason", "fulfillment_hold_required"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def submit_fulfillment_cancellation_request(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.submit_warehouse_cancellation_request",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
            },
        )
        return 200, result

    def warehouse_continue_fulfillment(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.warehouse_continue_fulfillment",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
                "new_status": body.get("newStatus")
                or body.get("new_status", "shipped"),
            },
        )
        return 200, result

    def create_refund(
        self,
        *,
        session_id: str,
        binding: ShopifyPlatformBinding,
        body: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        result = self.tools.call_tool(
            "commerce.create_refund",
            {
                "session_id": session_id,
                "order_id": _resolve_order_id_or_raise(binding, body),
                "amount": float(body.get("amount") or body.get("Amount")),
                "reason": body.get("reason", "buyer_request"),
                "actor": body.get("actor", "shopify_like_agent"),
                "source_event_id": body.get("sourceEventId")
                or body.get("source_event_id"),
                "approval_id": body.get("approvalId") or body.get("approval_id"),
                "approved_by": body.get("approvedBy") or body.get("approved_by"),
            },
        )
        return 200, result


def _resolve_order_id_or_raise(
    binding: ShopifyPlatformBinding,
    body: dict[str, Any],
) -> str:
    order_id, _ = binding.resolve_order_id(
        body.get("orderId")
        or body.get("order_id")
        or body.get("id")
        or body.get("admin_graphql_api_id")
        or body.get("fulfillmentOrderId")
        or body.get("fulfillment_order_id")
    )
    if not order_id:
        raise ValueError("Shopify action requires a known orderId")
    return order_id


def _resolve_sku_or_raise(
    binding: ShopifyPlatformBinding,
    body: dict[str, Any],
) -> str:
    sku = _resolve_sku(binding, body)
    if not sku:
        raise ValueError("Shopify action requires a known sku or inventoryItemId")
    return sku


def _resolve_sku(
    binding: ShopifyPlatformBinding,
    body: dict[str, Any],
) -> str | None:
    sku, _ = binding.resolve_sku(
        body.get("sku")
        or body.get("SKU")
        or body.get("inventoryItemId")
        or body.get("inventory_item_id")
    )
    if sku:
        return sku
    line = binding.resolve_line_item(
        body.get("fulfillmentOrderLineItemId")
        or body.get("lineItemId")
        or body.get("line_item_id")
    )
    return line.get("sku") if line else None


def _positive_quantity(body: dict[str, Any]) -> int:
    if "quantity" in body:
        return abs(int(body["quantity"]))
    if "Quantity" in body:
        return abs(int(body["Quantity"]))
    if "available_adjustment" in body:
        return abs(int(body["available_adjustment"]))
    if "availableAdjustment" in body:
        return abs(int(body["availableAdjustment"]))
    changes = body.get("changes") or []
    for change in changes:
        if isinstance(change, dict):
            if "delta" in change:
                return abs(int(change["delta"]))
            if "quantity" in change:
                return abs(int(change["quantity"]))
    return 1


def _inventory_action(body: dict[str, Any]) -> str:
    reason = str(
        body.get("reason")
        or body.get("name")
        or body.get("commerce_action")
        or body.get("commerceAction")
        or ""
    ).lower()
    if "release" in reason:
        return "release_inventory"
    if "reserve" in reason or "reservation" in reason:
        return "reserve_inventory"
    adjustment = body.get("available_adjustment", body.get("availableAdjustment"))
    if adjustment is not None and int(adjustment) < 0:
        return "reserve_inventory"
    return "contract_only"


def _shopify_inventory_item_gid(sku: str) -> str:
    return f"gid://shopify/InventoryItem/{sku}"


def first_inventory_change(body: dict[str, Any]) -> dict[str, Any]:
    variables = body.get("variables") or {}
    input_data = variables.get("input") or variables.get("inventoryAdjustQuantities") or {}
    changes = input_data.get("changes") or variables.get("changes") or []
    change = changes[0] if isinstance(changes, list) and changes else {}
    if not isinstance(change, dict):
        change = {}
    metadata = input_data.get("metadata") or variables.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    input_fields = {
        key: value
        for key, value in input_data.items()
        if key not in {"changes", "metadata"}
    }
    return {**input_fields, **metadata, **change, "changes": changes}


def input_object(body: dict[str, Any], *names: str) -> dict[str, Any]:
    variables = body.get("variables") or {}
    for name in names:
        value = variables.get(name)
        if isinstance(value, dict):
            return value
    value = variables.get("input")
    if isinstance(value, dict):
        return value
    return {}


def mutation_success(
    mutation_name: str,
    result: dict[str, Any],
    *,
    session_id: str,
) -> dict[str, Any]:
    return {
        "data": {
            mutation_name: {
                "result": result,
                "userErrors": [],
            }
        },
        "extensions": {
            "_commerce_twin": {
                "skin": "shopify_like",
                "session_id": session_id,
                "coverage": "stateful",
            }
        },
    }
