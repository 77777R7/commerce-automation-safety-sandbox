from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


@dataclass(frozen=True)
class SchemathesisFixtureValues:
    sessions: dict[str, str]
    feed_id: str = "feed_001"


OPERATION_SCENARIOS = {
    "getNextTask": "SCN-002",
    "getSessionStatus": "LIFECYCLE_STATUS",
    "resetSession": "LIFECYCLE_RESET",
    "teardownSession": "LIFECYCLE_TEARDOWN",
    "createFulfillment": "SCN-002",
    "findFulfillment": "SCN-002",
    "getTrace": "SCN-002",
    "completeSession": "SCN-002",
    "reserveInventory": "SCN-001",
    "skipDuplicateWebhook": "SCN-001",
    "promiseFulfillment": "SCN-003",
    "refreshInventory": "SCN-003",
    "routeManualReview": "SCN-003",
    "createRefund": "SCN-004",
    "createApprovalRequest": "SCN-004",
    "cancelOrder": "SCN-005",
    "releaseInventory": "SCN-005",
    "placeWorkflowHold": "SCN-005",
    "submitWarehouseCancellationRequest": "SCN-005",
    "warehouseContinueFulfillment": "SCN-005",
    "stripeCreateCustomer": "SAAS-001",
    "stripeCreateSubscription": "SAAS-001",
    "stripeDeliverWebhook": "SAAS-003",
    "slackPostMessage": "SAAS-001",
    "githubCreateCheckRun": "SAAS-001",
    "githubCreateIssue": "SAAS-001",
    "githubCommentOnPr": "SAAS-001",
    "shopifyReceiveWebhook": "SCN-001",
    "shopifySkipDuplicateWebhook": "SCN-001",
    "shopifyGraphQL": "SCN-002",
    "shopifyInventoryLevels": "SCN-003",
    "shopifyInventoryAdjust": "SCN-003",
    "shopifyOpsAction": "SCN-003",
    "shopifyCoverage": "SCN-003",
    "amazonGetInventorySummaries": "SCN-003",
    "amazonGetListingItem": "SCN-003",
    "amazonPatchListingQuantity": "SCN-003",
    "amazonCreateFeed": "SCN-003",
    "amazonGetFeed": "SCN-003",
    "amazonSellerOpsAction": "SCN-003",
    "amazonCoverage": "SCN-003",
    "amazonGetOrder": "SCN-005",
    "amazonGetOrderItems": "SCN-005",
    "amazonConfirmShipment": "SCN-005",
    "amazonInjectNotification": "SCN-005",
}


REQUEST_BODY_FIXTURES: dict[str, dict[str, Any]] = {
    "startSession": {"scenario_id": "SCN-002"},
    "createFulfillment": {
        "order_id": "order_2001",
        "sku": "sku_retry_1",
        "quantity": 1,
        "actor": "schemathesis_fixture_agent",
        "request_id": "schemathesis_fixture_req_1",
        "source_event_id": "task_fulfill_2001",
    },
    "reserveInventory": {
        "order_id": "order_1001",
        "sku": "sku_widget_1",
        "quantity": 1,
        "actor": "schemathesis_fixture_agent",
        "webhook_id": "wh_paid_001",
    },
    "promiseFulfillment": {
        "order_id": "order_3001",
        "sku": "sku_stale_1",
        "quantity": 1,
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "task_promise_3001",
    },
    "refreshInventory": {
        "sku": "sku_stale_1",
        "actor": "schemathesis_fixture_agent",
    },
    "routeManualReview": {
        "order_id": "order_3001",
        "sku": "sku_stale_1",
        "actor": "schemathesis_fixture_agent",
        "reason": "schemathesis_contract_fixture",
        "source_event_id": "task_promise_3001",
    },
    "findFulfillment": {
        "order_id": "order_2001",
        "sku": "sku_retry_1",
        "idempotency_key": "order_2001:sku_retry_1:create_fulfillment",
    },
    "createRefund": {
        "order_id": "order_4001",
        "amount": 120,
        "reason": "buyer_changed_mind",
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "refund_req_4001",
    },
    "createApprovalRequest": {
        "order_id": "order_4001",
        "amount": 120,
        "required_policy": "no_refund_after_shipment_without_approval",
        "reason": "buyer_changed_mind",
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "refund_req_4001",
    },
    "cancelOrder": {
        "order_id": "order_5001",
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "cancel_req_5001",
    },
    "releaseInventory": {
        "order_id": "order_5001",
        "sku": "sku_pickpack_1",
        "quantity": 1,
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "cancel_req_5001",
    },
    "placeWorkflowHold": {
        "order_id": "order_5001",
        "sku": "sku_pickpack_1",
        "reason": "warehouse_pick_pack_conflict",
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "cancel_req_5001",
    },
    "submitWarehouseCancellationRequest": {
        "order_id": "order_5001",
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "cancel_req_5001",
    },
    "warehouseContinueFulfillment": {
        "order_id": "order_5001",
        "new_status": "shipped",
        "actor": "schemathesis_fixture_agent",
        "source_event_id": "cancel_req_5001",
    },
    "skipDuplicateWebhook": {
        "actor": "schemathesis_fixture_agent",
        "webhook": {
            "type": "webhook",
            "id": "wh_paid_001",
            "topic": "order_paid",
            "order_id": "order_1001",
        },
    },
    "stripeCreateCustomer": {
        "email": "customer@example.test",
        "name": "Example Customer",
        "actor": "schemathesis_fixture_agent",
    },
    "stripeCreateSubscription": {
        "customer_id": "cus_000001",
        "price_id": "price_pro_monthly",
        "amount_due": 2900,
        "currency": "usd",
        "payment_outcome": "requires_payment_method",
        "actor": "schemathesis_fixture_agent",
    },
    "stripeDeliverWebhook": {
        "event_id": "evt_000003",
        "delivery_id": "deliv_schemathesis_1",
        "actor": "schemathesis_fixture_agent",
    },
    "slackPostMessage": {
        "channel_id": "C_INCIDENTS",
        "text": "Billing failure: payment failed.",
        "metadata": {"kind": "billing_failure_alert"},
        "actor": "schemathesis_fixture_agent",
    },
    "githubCreateCheckRun": {
        "owner": "acme",
        "repo_name": "billing-agent",
        "head_sha": "abc123",
        "conclusion": "action_required",
        "output_summary": "Payment failed; billing recovery required.",
        "actor": "schemathesis_fixture_agent",
    },
    "githubCreateIssue": {
        "owner": "acme",
        "repo_name": "billing-agent",
        "title": "Billing recovery required",
        "body": "Initial payment failed; do not publish success state.",
        "labels": ["billing", "agent-review"],
        "actor": "schemathesis_fixture_agent",
    },
    "githubCommentOnPr": {
        "owner": "acme",
        "repo_name": "billing-agent",
        "pull_number": 42,
        "body": "Policy check requires billing recovery before merge.",
        "actor": "schemathesis_fixture_agent",
    },
    "shopifyReceiveWebhook": {
        "id": 1001,
        "admin_graphql_api_id": "gid://shopify/Order/1001",
    },
    "shopifySkipDuplicateWebhook": {
        "id": 1001,
        "admin_graphql_api_id": "gid://shopify/Order/1001",
    },
    "shopifyGraphQL": {
        "query": (
            "mutation FulfillmentCreate($fulfillment: FulfillmentInput!) "
            "{ fulfillmentCreate(fulfillment: $fulfillment) "
            "{ fulfillment { id status } userErrors { field message } } }"
        ),
        "variables": {
            "fulfillment": {
                "lineItemsByFulfillmentOrder": [
                    {
                        "fulfillmentOrderId": "gid://shopify/FulfillmentOrder/2001",
                        "fulfillmentOrderLineItems": [
                            {
                                "id": "gid://shopify/FulfillmentOrderLineItem/2001-0",
                                "quantity": 1,
                            }
                        ],
                    }
                ],
                "metadata": {
                    "idempotency_key": "order_2001:sku_retry_1:create_fulfillment",
                    "source_event_id": "task_fulfill_2001",
                    "request_id": "schemathesis_fixture_req_1",
                },
            }
        },
    },
    "shopifyInventoryAdjust": {
        "orderId": "gid://shopify/Order/3001",
        "inventoryItemId": "gid://shopify/InventoryItem/sku_stale_1",
        "quantity": 1,
        "reason": "schemathesis_contract_fixture",
        "sourceEventId": "task_promise_3001",
    },
    "shopifyOpsAction": {
        "orderId": "gid://shopify/Order/3001",
        "inventoryItemId": "gid://shopify/InventoryItem/sku_stale_1",
        "sku": "sku_stale_1",
        "quantity": 1,
        "reason": "schemathesis_contract_fixture",
        "sourceEventId": "task_promise_3001",
    },
    "amazonPatchListingQuantity": {
        "productType": "PRODUCT",
        "patches": [
            {
                "op": "replace",
                "path": "/attributes/fulfillment_availability",
                "value": [
                    {
                        "fulfillment_channel_code": "DEFAULT",
                        "quantity": 0,
                    }
                ],
            }
        ],
        "actor": "schemathesis_fixture_agent",
    },
    "amazonConfirmShipment": {
        "packageDetail": {
            "packageReferenceId": "1",
            "trackingNumber": "1Z999",
            "carrierCode": "UPS",
            "orderItems": [{"orderItemId": "AMZ-5001-0", "quantity": 1}],
        },
        "actor": "schemathesis_fixture_agent",
        "sourceEventId": "amazon_order_change_AMZ-5001",
    },
    "amazonCreateFeed": {
        "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
        "marketplaceIds": ["ATVPDKIKX0DER"],
        "messages": [{"sellerSku": "SELLER-0001", "quantity": 0}],
        "actor": "schemathesis_fixture_agent",
    },
    "amazonInjectNotification": {
        "notificationType": "ORDER_CHANGE",
        "payload": {
            "AmazonOrderId": "AMZ-5001",
            "OrderChangeType": "BuyerRequestedCancel",
        },
        "actor": "schemathesis_fixture_agent",
    },
    "amazonSellerOpsAction": {
        "amazonOrderId": "AMZ-3001",
        "sellerSku": "SELLER-0001",
        "quantity": 1,
        "reason": "schemathesis_contract_fixture",
        "actor": "schemathesis_fixture_agent",
        "sourceEventId": "task_promise_3001",
    },
    "completeSession": {"runner_name": "schemathesis_fixture_agent"},
}


PATH_PARAMETER_FIXTURES = {
    "api_version": {
        "shopifyGraphQL": "2026-04",
        "shopifyInventoryLevels": "2026-04",
        "shopifyInventoryAdjust": "2026-04",
        "amazonGetListingItem": "2021-08-01",
        "amazonPatchListingQuantity": "2021-08-01",
        "amazonCreateFeed": "2021-06-30",
        "amazonGetFeed": "2021-06-30",
    },
    "seller_id": {"*": "seller_123"},
    "sku": {"*": "sku_stale_1"},
    "amazon_order_id": {
        "amazonGetOrder": "AMZ-5001",
        "amazonGetOrderItems": "AMZ-5001",
        "amazonConfirmShipment": "AMZ-5001",
    },
    "amazon_action": {"amazonSellerOpsAction": "promise_fulfillment"},
    "shopify_action": {"shopifyOpsAction": "promise_fulfillment"},
}


QUERY_AND_HEADER_FIXTURES = {
    "inventory_item_ids": "gid://shopify/InventoryItem/sku_stale_1",
    "X-Shopify-Topic": "orders/paid",
    "X-Shopify-Webhook-Id": "wh_paid_001",
    "X-Shopify-Shop-Domain": "acme.myshopify.com",
}


def build_schemathesis_fixture_spec(
    spec: dict[str, Any],
    values: SchemathesisFixtureValues,
) -> dict[str, Any]:
    fixture_spec = deepcopy(spec)
    components = fixture_spec.get("components", {})

    for path_item in fixture_spec.get("paths", {}).values():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not operation_id:
                continue
            operation["parameters"] = [
                _fixture_parameter(parameter, components, operation_id, values)
                for parameter in operation.get("parameters", [])
            ]
            _fixture_request_body(operation, operation_id)

    return fixture_spec


def _fixture_parameter(
    parameter: dict[str, Any],
    components: dict[str, Any],
    operation_id: str,
    values: SchemathesisFixtureValues,
) -> dict[str, Any]:
    resolved = deepcopy(_resolve_parameter(parameter, components))
    name = resolved.get("name")
    fixture_value = _parameter_fixture_value(name, operation_id, values)
    if fixture_value is None:
        return resolved

    resolved["schema"] = {
        "type": "string",
        "enum": [fixture_value],
    }
    resolved["example"] = fixture_value
    return resolved


def _resolve_parameter(
    parameter: dict[str, Any],
    components: dict[str, Any],
) -> dict[str, Any]:
    ref = parameter.get("$ref")
    if not ref:
        return parameter
    prefix = "#/components/parameters/"
    if not ref.startswith(prefix):
        return parameter
    name = ref.removeprefix(prefix)
    return components.get("parameters", {}).get(name, parameter)


def _parameter_fixture_value(
    name: str | None,
    operation_id: str,
    values: SchemathesisFixtureValues,
) -> str | None:
    if name == "session_id":
        scenario_id = OPERATION_SCENARIOS.get(operation_id)
        return values.sessions.get(scenario_id or "")
    if name == "feed_id":
        return values.feed_id
    if name in QUERY_AND_HEADER_FIXTURES:
        return QUERY_AND_HEADER_FIXTURES[name]
    operation_map = PATH_PARAMETER_FIXTURES.get(name or "", {})
    return operation_map.get(operation_id) or operation_map.get("*")


def _fixture_request_body(operation: dict[str, Any], operation_id: str) -> None:
    body = REQUEST_BODY_FIXTURES.get(operation_id)
    if body is None:
        return
    content = operation.get("requestBody", {}).get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return
    json_content["schema"] = {
        "type": "object",
        "enum": [body],
    }
    json_content["examples"] = {
        "schemathesis_fixture": {
            "value": body,
        }
    }
