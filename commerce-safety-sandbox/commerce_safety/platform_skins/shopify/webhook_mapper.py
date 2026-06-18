from __future__ import annotations

from typing import Any

from .coverage import load_shopify_coverage


class ShopifyWebhookMappingError(ValueError):
    pass


def _headers_lower(headers: dict[str, Any]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def map_shopify_webhook(
    headers: dict[str, Any],
    body: dict[str, Any],
    order_id_binding: dict[str, str] | None = None,
) -> dict[str, Any]:
    normalized_headers = _headers_lower(headers)
    topic = normalized_headers.get("x-shopify-topic")
    webhook_id = normalized_headers.get("x-shopify-webhook-id")
    if not topic:
        raise ShopifyWebhookMappingError("missing X-Shopify-Topic")
    if not webhook_id:
        raise ShopifyWebhookMappingError("missing X-Shopify-Webhook-Id")

    coverage = load_shopify_coverage()
    if not coverage.is_supported_webhook(topic):
        raise ShopifyWebhookMappingError(f"unsupported Shopify webhook topic: {topic}")

    order_id, binding_source = _resolve_order_id(body, order_id_binding or {})
    if not order_id:
        raise ShopifyWebhookMappingError(
            "Shopify webhook body must include order_id, "
            "metadata.commerce_order_id, or a Shopify order id known to the session"
        )

    spec = coverage.webhooks[topic]
    event: dict[str, Any] = {
        "id": webhook_id,
        "topic": spec["normalized_topic"],
        "raw_topic": topic,
        "order_id": str(order_id),
        "platform": "shopify_like",
        "shop_domain": normalized_headers.get("x-shopify-shop-domain"),
        "shopify_order_id": str(body["id"]) if body.get("id") is not None else None,
        "admin_graphql_api_id": body.get("admin_graphql_api_id"),
        "binding_source": binding_source,
    }
    if topic == "orders/cancelled":
        event.update(
            {
                "type": "cancel_request",
                "amount": body.get("total_price")
                or body.get("amount")
                or body.get("captured_amount")
                or 0,
                "reason": body.get("cancel_reason") or body.get("reason") or "cancelled",
            }
        )
    return event


def _resolve_order_id(
    body: dict[str, Any],
    order_id_binding: dict[str, str],
) -> tuple[str | None, str | None]:
    metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
    for key, source in [
        ("order_id", "canonical_order_id"),
        ("commerce_order_id", "commerce_order_id"),
    ]:
        value = body.get(key) or metadata.get(key)
        if value:
            return str(value), source
    for value in [body.get("id"), body.get("admin_graphql_api_id")]:
        if value is None:
            continue
        mapped = order_id_binding.get(str(value))
        if mapped:
            source = "shopify_gid" if str(value).startswith("gid://shopify/") else "shopify_order_id"
            return mapped, source
    return None, None
