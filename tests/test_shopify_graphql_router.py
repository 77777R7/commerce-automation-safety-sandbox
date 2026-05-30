from __future__ import annotations

from commerce_safety.platform_skins.shopify.graphql_router import (
    extract_fulfillment_create_action,
    identify_mutation,
)
from commerce_safety.platform_skins.shopify.binding import ShopifyPlatformBinding
from commerce_safety.platform_skins.shopify.response_shapes import (
    shopify_fulfillment_gid,
    unsupported_mutation_response,
)


FULFILLMENT_CREATE_QUERY = """
mutation FulfillmentCreate($fulfillment: FulfillmentInput!) {
  fulfillmentCreate(fulfillment: $fulfillment) {
    fulfillment { id status }
    userErrors { field message }
  }
}
"""


def test_identify_mutation_detects_fulfillment_create():
    assert identify_mutation({"query": FULFILLMENT_CREATE_QUERY}) == "fulfillmentCreate"


def test_extract_fulfillment_create_action_maps_variables_to_commerce_action():
    action = extract_fulfillment_create_action(
        {
            "query": FULFILLMENT_CREATE_QUERY,
            "variables": {
                "fulfillment": {
                    "order_id": "order_2001",
                    "sku": "sku_retry_1",
                    "quantity": 1,
                    "idempotency_key": "order_2001:sku_retry_1:create_fulfillment",
                    "request_id": "shopify_req_1",
                    "source_event_id": "task_fulfill_2001",
                    "fault_type": "timeout_after_commit",
                }
            },
        },
        actor="shopify_like_agent",
    )

    assert action == {
        "order_id": "order_2001",
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "shopify_like_agent",
        "webhook_id": None,
        "idempotency_key": "order_2001:sku_retry_1:create_fulfillment",
        "request_id": "shopify_req_1",
        "source_event_id": "task_fulfill_2001",
        "fault_type": "timeout_after_commit",
    }


def test_extract_fulfillment_create_action_supports_shopifyish_line_item_shape():
    action = extract_fulfillment_create_action(
        {
            "variables": {
                "fulfillment": {
                    "lineItemsByFulfillmentOrder": [
                        {
                            "orderId": "order_1001",
                            "lineItems": [
                                {
                                    "sku": "sku_widget_1",
                                    "quantity": 1,
                                }
                            ],
                        }
                    ],
                    "metadata": {
                        "webhook_id": "wh_paid_001",
                        "source_event_id": "wh_paid_001",
                    },
                }
            }
        },
        actor="shopify_like_agent",
    )

    assert action["order_id"] == "order_1001"
    assert action["sku"] == "sku_widget_1"
    assert action["webhook_id"] == "wh_paid_001"
    assert action["source_event_id"] == "wh_paid_001"


def test_extract_fulfillment_create_action_resolves_shopify_platform_ids():
    binding = ShopifyPlatformBinding(
        order_ids={
            "gid://shopify/FulfillmentOrder/2001": "order_2001",
        },
        line_items={
            "gid://shopify/FulfillmentOrderLineItem/2001-0": {
                "order_id": "order_2001",
                "sku": "sku_retry_1",
            }
        },
    )

    action = extract_fulfillment_create_action(
        {
            "variables": {
                "fulfillment": {
                    "lineItemsByFulfillmentOrder": [
                        {
                            "fulfillmentOrderId": (
                                "gid://shopify/FulfillmentOrder/2001"
                            ),
                            "fulfillmentOrderLineItems": [
                                {
                                    "id": (
                                        "gid://shopify/FulfillmentOrderLineItem/2001-0"
                                    ),
                                    "quantity": 1,
                                }
                            ],
                        }
                    ],
                    "metadata": {
                        "idempotency_key": (
                            "order_2001:sku_retry_1:create_fulfillment"
                        ),
                        "source_event_id": "task_fulfill_2001",
                    },
                }
            }
        },
        actor="shopify_like_agent",
        binding=binding,
    )

    assert action["order_id"] == "order_2001"
    assert action["sku"] == "sku_retry_1"
    assert action["quantity"] == 1
    assert action["idempotency_key"] == "order_2001:sku_retry_1:create_fulfillment"


def test_unsupported_mutation_response_is_an_explicit_stub():
    response = unsupported_mutation_response("productCreate")

    assert response["data"] is None
    assert response["extensions"]["_commerce_twin_stub"] is True
    assert response["extensions"]["coverage"] == "unsupported"
    assert "productCreate" in response["errors"][0]["message"]


def test_shopify_fulfillment_gid_keeps_internal_id_visible_but_namespaced():
    assert shopify_fulfillment_gid("ful_001") == "gid://shopify/Fulfillment/ful_001"
