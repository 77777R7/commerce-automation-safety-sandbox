from __future__ import annotations

import re
from typing import Any

from ...models import to_plain
from .binding import ShopifyPlatformBinding
from .coverage import load_shopify_coverage
from .response_shapes import (
    fulfillment_create_success,
    fulfillment_create_timeout,
    unsupported_mutation_response,
)


MUTATION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


class ShopifyGraphQLMappingError(ValueError):
    pass


def identify_mutation(body: dict[str, Any]) -> str | None:
    operation_name = body.get("operationName")
    if operation_name in {"fulfillmentCreate", "refundCreate", "productCreate"}:
        return str(operation_name)

    query = str(body.get("query", ""))
    for known_name in ("fulfillmentCreate", "refundCreate", "productCreate"):
        if re.search(rf"\b{known_name}\s*\(", query):
            return known_name
    for match in MUTATION_RE.finditer(query):
        name = match.group(1)
        if name not in {"mutation", "query"} and not name[:1].isupper():
            return name
    return None


def extract_fulfillment_create_action(
    body: dict[str, Any],
    *,
    actor: str,
    binding: ShopifyPlatformBinding | None = None,
) -> dict[str, Any]:
    variables = body.get("variables") or {}
    fulfillment = variables.get("fulfillment") or variables.get("input") or {}
    if not isinstance(fulfillment, dict):
        raise ShopifyGraphQLMappingError("fulfillment variables must be an object")

    metadata = fulfillment.get("metadata") or variables.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ShopifyGraphQLMappingError("metadata must be an object")

    line_item_shape = _first_line_item_shape(fulfillment, binding)
    order_id = (
        fulfillment.get("order_id")
        or fulfillment.get("orderId")
        or metadata.get("commerce_order_id")
        or line_item_shape.get("order_id")
    )
    sku = fulfillment.get("sku") or metadata.get("commerce_sku") or line_item_shape.get("sku")
    quantity = fulfillment.get("quantity", line_item_shape.get("quantity", 1))
    if not order_id:
        raise ShopifyGraphQLMappingError("fulfillmentCreate requires order_id")
    if not sku:
        raise ShopifyGraphQLMappingError("fulfillmentCreate requires sku")

    return {
        "order_id": str(order_id),
        "sku": str(sku),
        "quantity": int(quantity),
        "actor": actor,
        "webhook_id": fulfillment.get("webhook_id") or metadata.get("webhook_id"),
        "idempotency_key": fulfillment.get("idempotency_key")
        or metadata.get("idempotency_key"),
        "request_id": fulfillment.get("request_id") or metadata.get("request_id"),
        "source_event_id": fulfillment.get("source_event_id")
        or metadata.get("source_event_id"),
        "fault_type": fulfillment.get("fault_type") or metadata.get("fault_type"),
    }


def _first_line_item_shape(
    fulfillment: dict[str, Any],
    binding: ShopifyPlatformBinding | None,
) -> dict[str, Any]:
    groups = fulfillment.get("lineItemsByFulfillmentOrder") or []
    if not isinstance(groups, list) or not groups:
        return {}
    first_group = groups[0]
    if not isinstance(first_group, dict):
        return {}
    line_items = (
        first_group.get("fulfillmentOrderLineItems")
        or first_group.get("lineItems")
        or []
    )
    first_line = line_items[0] if isinstance(line_items, list) and line_items else {}
    if not isinstance(first_line, dict):
        first_line = {}
    bound_line = binding.resolve_line_item(first_line.get("id")) if binding else None
    order_id = first_group.get("orderId") or first_group.get("order_id")
    if not order_id and binding:
        order_id, _ = binding.resolve_order_id(first_group.get("fulfillmentOrderId"))
    return {
        "order_id": order_id or (bound_line or {}).get("order_id"),
        "sku": first_line.get("sku") or (bound_line or {}).get("sku"),
        "quantity": first_line.get("quantity", 1),
    }


class ShopifyGraphQLRouter:
    def __init__(self, tools: Any):
        self.tools = tools
        self.coverage = load_shopify_coverage()

    def handle(
        self,
        *,
        session_id: str,
        body: dict[str, Any],
        actor: str = "shopify_like_agent",
        binding: ShopifyPlatformBinding | None = None,
    ) -> tuple[int, dict[str, Any]]:
        mutation_name = identify_mutation(body)
        if self.coverage.mutation_status(mutation_name or "") != "stateful":
            return 200, unsupported_mutation_response(mutation_name)

        if mutation_name != "fulfillmentCreate":
            return 200, unsupported_mutation_response(mutation_name)

        action = extract_fulfillment_create_action(
            body,
            actor=actor,
            binding=binding,
        )
        result = self.tools.call_tool(
            "commerce.create_fulfillment",
            {"session_id": session_id, **action},
        )
        if result.get("error") == "timeout_after_commit":
            return 504, fulfillment_create_timeout(
                session_id=session_id,
                fulfillment_id=str(result["fulfillment_id"]),
            )
        if not result.get("ok"):
            return 400, {
                "data": None,
                "errors": [{"message": str(result.get("error", "unknown_error"))}],
                "extensions": {"_commerce_twin": {"skin": "shopify_like"}},
            }
        return 200, fulfillment_create_success(
            to_plain(result["fulfillment"]),
            session_id=session_id,
        )
