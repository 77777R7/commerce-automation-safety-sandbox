from __future__ import annotations

import pytest

from commerce_safety.platform_skins.shopify.webhook_mapper import (
    ShopifyWebhookMappingError,
    map_shopify_webhook,
)


def test_orders_paid_webhook_maps_shopify_headers_to_normalized_event():
    event = map_shopify_webhook(
        {
            "X-Shopify-Topic": "orders/paid",
            "X-Shopify-Webhook-Id": "wh_paid_001",
            "X-Shopify-Shop-Domain": "acme.myshopify.com",
        },
        {
            "id": 1001,
            "order_id": "order_1001",
            "admin_graphql_api_id": "gid://shopify/Order/1001",
        },
    )

    assert event == {
        "id": "wh_paid_001",
        "topic": "order_paid",
        "raw_topic": "orders/paid",
        "order_id": "order_1001",
        "platform": "shopify_like",
        "shop_domain": "acme.myshopify.com",
        "shopify_order_id": "1001",
        "admin_graphql_api_id": "gid://shopify/Order/1001",
        "binding_source": "canonical_order_id",
    }


def test_webhook_mapper_accepts_case_insensitive_headers():
    event = map_shopify_webhook(
        {
            "x-shopify-topic": "orders/paid",
            "x-shopify-webhook-id": "wh_paid_002",
        },
        {"order_id": "order_1001"},
    )

    assert event["id"] == "wh_paid_002"
    assert event["raw_topic"] == "orders/paid"


def test_webhook_mapper_resolves_shopify_order_id_through_binding():
    event = map_shopify_webhook(
        {
            "X-Shopify-Topic": "orders/paid",
            "X-Shopify-Webhook-Id": "wh_paid_003",
        },
        {
            "id": 1001,
            "admin_graphql_api_id": "gid://shopify/Order/1001",
        },
        order_id_binding={
            "1001": "order_1001",
            "gid://shopify/Order/1001": "order_1001",
        },
    )

    assert event["order_id"] == "order_1001"
    assert event["shopify_order_id"] == "1001"


def test_orders_cancelled_webhook_maps_to_cancel_request_event():
    event = map_shopify_webhook(
        {
            "X-Shopify-Topic": "orders/cancelled",
            "X-Shopify-Webhook-Id": "wh_cancel_5001",
        },
        {
            "id": 5001,
            "admin_graphql_api_id": "gid://shopify/Order/5001",
            "total_price": "80",
            "cancel_reason": "customer",
        },
        order_id_binding={
            "5001": "order_5001",
            "gid://shopify/Order/5001": "order_5001",
        },
    )

    assert event["topic"] == "cancel_request"
    assert event["type"] == "cancel_request"
    assert event["order_id"] == "order_5001"
    assert event["amount"] == "80"
    assert event["reason"] == "customer"


def test_webhook_mapper_rejects_unsupported_topics_explicitly():
    with pytest.raises(ShopifyWebhookMappingError) as error:
        map_shopify_webhook(
            {
                "X-Shopify-Topic": "refunds/create",
                "X-Shopify-Webhook-Id": "wh_refund_001",
            },
            {"order_id": "order_1001"},
        )

    assert "unsupported Shopify webhook topic" in str(error.value)
