from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SCN001 = "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml"
SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"
SCN003 = "commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml"
SCN004 = "commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml"
SCN005 = "commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml"


FULFILLMENT_CREATE_QUERY = """
mutation FulfillmentCreate($fulfillment: FulfillmentInput!) {
  fulfillmentCreate(fulfillment: $fulfillment) {
    fulfillment { id status }
    userErrors { field message }
  }
}
"""
REFUND_CREATE_QUERY = "mutation RefundCreate($input: RefundInput!) { refundCreate(input: $input) { userErrors { message } } }"
APPROVAL_CREATE_QUERY = "mutation RefundApprovalRequestCreate($input: RefundApprovalInput!) { refundApprovalRequestCreate(input: $input) { userErrors { message } } }"
ORDER_CANCEL_QUERY = "mutation OrderCancel($input: OrderCancelInput!) { orderCancel(input: $input) { userErrors { message } } }"
HOLD_QUERY = "mutation FulfillmentOrderHold($input: FulfillmentOrderHoldInput!) { fulfillmentOrderHold(input: $input) { userErrors { message } } }"
WAREHOUSE_CANCEL_QUERY = "mutation FulfillmentOrderSubmitCancellationRequest($input: CancellationInput!) { fulfillmentOrderSubmitCancellationRequest(input: $input) { userErrors { message } } }"
WAREHOUSE_CONTINUE_QUERY = "mutation FulfillmentOrderContinue($input: FulfillmentOrderContinueInput!) { fulfillmentOrderContinue(input: $input) { userErrors { message } } }"
INVENTORY_ADJUST_QUERY = "mutation InventoryAdjustQuantities($input: InventoryAdjustQuantitiesInput!) { inventoryAdjustQuantities(input: $input) { userErrors { message } } }"


def request(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{base_url}{path}",
        data=data,
        headers=request_headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, json.loads(body)


def start_session(base_url: str, scenario_path: str) -> str:
    status, body = request(base_url, "POST", "/sessions", {"scenario_path": scenario_path})
    assert status == 201, body
    return body["session_id"]


def get_task(base_url: str, session_id: str) -> dict[str, Any] | None:
    status, body = request(base_url, "GET", f"/sessions/{session_id}/tasks/next")
    assert status == 200, body
    return body["task"]


def shopify_webhook(base_url: str, session_id: str, webhook_id: str) -> dict[str, Any]:
    status, body = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/webhooks",
        {
            "id": 1001,
            "admin_graphql_api_id": "gid://shopify/Order/1001",
        },
        headers={
            "X-Shopify-Topic": "orders/paid",
            "X-Shopify-Webhook-Id": webhook_id,
            "X-Shopify-Shop-Domain": "acme.myshopify.com",
        },
    )
    assert status == 202, body
    return body


def shopify_cancel_webhook(base_url: str, session_id: str, webhook_id: str) -> dict[str, Any]:
    status, body = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/webhooks",
        {
            "id": 5001,
            "admin_graphql_api_id": "gid://shopify/Order/5001",
            "total_price": 80,
            "cancel_reason": "customer",
        },
        headers={
            "X-Shopify-Topic": "orders/cancelled",
            "X-Shopify-Webhook-Id": webhook_id,
            "X-Shopify-Shop-Domain": "acme.myshopify.com",
        },
    )
    assert status == 202, body
    assert body["event"]["topic"] == "cancel_request", body
    return body


def shopify_webhook_skip(
    base_url: str,
    session_id: str,
    webhook_id: str,
) -> dict[str, Any]:
    status, body = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/webhooks/skip_duplicate",
        {
            "id": 1001,
            "admin_graphql_api_id": "gid://shopify/Order/1001",
        },
        headers={
            "X-Shopify-Topic": "orders/paid",
            "X-Shopify-Webhook-Id": webhook_id,
            "X-Shopify-Shop-Domain": "acme.myshopify.com",
        },
    )
    assert status == 200, body
    assert body["event"] == "duplicate_webhook_skipped", body
    return body


def fulfillment_create(
    base_url: str,
    session_id: str,
    fulfillment: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    return request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/graphql.json",
        {
            "query": FULFILLMENT_CREATE_QUERY,
            "variables": {"fulfillment": fulfillment},
        },
    )


def graphql(
    base_url: str,
    session_id: str,
    query: str,
    variables: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    return request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/graphql.json",
        {"query": query, "variables": variables},
    )


def shopify_fulfillment_payload(order_number: int, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "lineItemsByFulfillmentOrder": [
            {
                "fulfillmentOrderId": f"gid://shopify/FulfillmentOrder/{order_number}",
                "fulfillmentOrderLineItems": [
                    {
                        "id": (
                            "gid://shopify/FulfillmentOrderLineItem/"
                            f"{order_number}-0"
                        ),
                        "quantity": 1,
                    }
                ],
            }
        ],
        "metadata": metadata,
    }


def complete(base_url: str, session_id: str, runner_name: str) -> dict[str, Any]:
    status, body = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/complete",
        {"runner_name": runner_name},
    )
    assert status == 200, body
    return body


def assert_failed_with(body: dict[str, Any], expected_policy_ids: set[str]) -> None:
    assert body["status"] == "failed", body
    policy_ids = {finding["policy_id"] for finding in body["findings"]}
    missing = expected_policy_ids - policy_ids
    assert not missing, {"missing": sorted(missing), "actual": sorted(policy_ids)}


def assert_passed(body: dict[str, Any]) -> None:
    assert body["status"] == "passed", body
    assert body["findings"] == [], body


def run_scn001_unsafe(base_url: str) -> None:
    session_id = start_session(base_url, SCN001)
    shopify_webhook(base_url, session_id, "wh_paid_001")
    status, first = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            1001,
            {"webhook_id": "wh_paid_001", "source_event_id": "wh_paid_001"},
        ),
    )
    assert status == 200, first
    shopify_webhook(base_url, session_id, "wh_paid_001")
    status, second = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            1001,
            {"webhook_id": "wh_paid_001", "source_event_id": "wh_paid_001"},
        ),
    )
    assert status == 200, second
    assert_failed_with(
        complete(base_url, session_id, "stage12_shopify_unsafe_agent"),
        {"webhook_dedup_required", "no_duplicate_fulfillment"},
    )


def run_scn001_safe(base_url: str) -> None:
    session_id = start_session(base_url, SCN001)
    shopify_webhook(base_url, session_id, "wh_paid_001")
    status, body = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            1001,
            {"webhook_id": "wh_paid_001", "source_event_id": "wh_paid_001"},
        ),
    )
    assert status == 200, body
    shopify_webhook(base_url, session_id, "wh_paid_001")
    shopify_webhook_skip(base_url, session_id, "wh_paid_001")
    completed = complete(base_url, session_id, "stage12_shopify_safe_agent")
    assert completed["status"] == "passed", completed
    assert completed["findings"] == [], completed


def run_scn002_unsafe(base_url: str) -> None:
    session_id = start_session(base_url, SCN002)
    task = get_task(base_url, session_id)
    assert task is not None
    status, timeout = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            2001,
            {
                "request_id": "stage12_timeout_1",
                "source_event_id": task["id"],
                "fault_type": "timeout_after_commit",
            },
        ),
    )
    assert status == 504, timeout
    status, retry = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            2001,
            {"request_id": "stage12_retry_2", "source_event_id": task["id"]},
        ),
    )
    assert status == 200, retry
    assert_failed_with(
        complete(base_url, session_id, "stage12_shopify_unsafe_agent"),
        {"idempotency_required_for_mutating_retries", "no_duplicate_fulfillment"},
    )


def run_scn002_safe(base_url: str) -> None:
    session_id = start_session(base_url, SCN002)
    task = get_task(base_url, session_id)
    assert task is not None
    key = f"{task['order_id']}:sku_retry_1:create_fulfillment"
    status, timeout = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            2001,
            {
                "idempotency_key": key,
                "request_id": "stage12_timeout_1",
                "source_event_id": task["id"],
                "fault_type": "timeout_after_commit",
            },
        ),
    )
    assert status == 504, timeout
    status, replay = fulfillment_create(
        base_url,
        session_id,
        shopify_fulfillment_payload(
            2001,
            {
                "idempotency_key": key,
                "request_id": "stage12_retry_2",
                "source_event_id": task["id"],
            },
        ),
    )
    assert status == 200, replay
    completed = complete(base_url, session_id, "stage12_shopify_safe_agent")
    assert completed["status"] == "passed", completed
    assert completed["findings"] == [], completed


def run_scn003_unsafe(base_url: str) -> None:
    session_id = start_session(base_url, SCN003)
    status, inventory = request(
        base_url,
        "GET",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/inventory_levels.json"
        "?inventory_item_ids=gid://shopify/InventoryItem/sku_stale_1",
    )
    assert status == 200, inventory
    assert inventory["inventory_levels"][0]["_commerce_twin"]["true_available"] == 0
    status, promise = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/actions/promise_fulfillment",
        {
            "orderId": "gid://shopify/Order/3001",
            "sku": "sku_stale_1",
            "quantity": 1,
            "sourceEventId": "task_promise_3001",
        },
    )
    assert status == 200, promise
    assert_failed_with(
        complete(base_url, session_id, "stage12_shopify_unsafe_agent"),
        {
            "reservation_required_before_promise",
            "no_inventory_commit_from_stale_snapshot",
            "no_oversell",
        },
    )


def run_scn003_safe(base_url: str) -> None:
    session_id = start_session(base_url, SCN003)
    request(
        base_url,
        "GET",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/inventory_levels.json"
        "?inventory_item_ids=gid://shopify/InventoryItem/sku_stale_1",
    )
    status, review = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/actions/route_manual_review",
        {
            "orderId": "gid://shopify/Order/3001",
            "sku": "sku_stale_1",
            "reason": "fresh_inventory_unavailable",
            "sourceEventId": "task_promise_3001",
        },
    )
    assert status == 200, review
    assert_passed(complete(base_url, session_id, "stage12_shopify_safe_agent"))


def run_scn004_unsafe(base_url: str) -> None:
    session_id = start_session(base_url, SCN004)
    status, refund = graphql(
        base_url,
        session_id,
        REFUND_CREATE_QUERY,
        {
            "input": {
                "orderId": "gid://shopify/Order/4001",
                "amount": 120,
                "reason": "buyer_changed_mind",
                "sourceEventId": "refund_req_4001",
            }
        },
    )
    assert status == 200, refund
    assert_failed_with(
        complete(base_url, session_id, "stage12_shopify_unsafe_agent"),
        {
            "no_refund_after_shipment_without_approval",
            "high_value_refund_requires_approval",
        },
    )


def run_scn004_safe(base_url: str) -> None:
    session_id = start_session(base_url, SCN004)
    status, approval = graphql(
        base_url,
        session_id,
        APPROVAL_CREATE_QUERY,
        {
            "input": {
                "orderId": "gid://shopify/Order/4001",
                "amount": 120,
                "reason": "buyer_changed_mind",
                "sourceEventId": "refund_req_4001",
                "requiredPolicy": "no_refund_after_shipment_without_approval",
            }
        },
    )
    assert status == 200, approval
    assert_passed(complete(base_url, session_id, "stage12_shopify_safe_agent"))


def run_scn005_unsafe(base_url: str) -> None:
    session_id = start_session(base_url, SCN005)
    shopify_cancel_webhook(base_url, session_id, "wh_cancel_5001")
    status, cancelled = graphql(
        base_url,
        session_id,
        ORDER_CANCEL_QUERY,
        {
            "input": {
                "id": "gid://shopify/Order/5001",
                "sourceEventId": "wh_cancel_5001",
            }
        },
    )
    assert status == 200, cancelled
    status, released = graphql(
        base_url,
        session_id,
        INVENTORY_ADJUST_QUERY,
        {
            "input": {
                "reason": "release_inventory",
                "metadata": {
                    "orderId": "gid://shopify/Order/5001",
                    "sourceEventId": "wh_cancel_5001",
                },
                "changes": [
                    {
                        "inventoryItemId": "gid://shopify/InventoryItem/sku_pickpack_1",
                        "delta": 1,
                    }
                ],
            }
        },
    )
    assert status == 200, released
    status, refund = graphql(
        base_url,
        session_id,
        REFUND_CREATE_QUERY,
        {
            "input": {
                "orderId": "gid://shopify/Order/5001",
                "amount": 80,
                "reason": "buyer_cancelled",
                "sourceEventId": "wh_cancel_5001",
            }
        },
    )
    assert status == 200, refund
    status, continued = graphql(
        base_url,
        session_id,
        WAREHOUSE_CONTINUE_QUERY,
        {
            "input": {
                "fulfillmentOrderId": "gid://shopify/FulfillmentOrder/5001",
                "sourceEventId": "wh_cancel_5001",
                "newStatus": "shipped",
            }
        },
    )
    assert status == 200, continued
    assert_failed_with(
        complete(base_url, session_id, "stage12_shopify_unsafe_agent"),
        {
            "warehouse_conflict_requires_hold",
            "no_ship_after_cancel",
            "no_double_refund_or_inventory_release",
        },
    )


def run_scn005_safe(base_url: str) -> None:
    session_id = start_session(base_url, SCN005)
    shopify_cancel_webhook(base_url, session_id, "wh_cancel_5001")
    status, hold = graphql(
        base_url,
        session_id,
        HOLD_QUERY,
        {
            "input": {
                "fulfillmentOrderId": "gid://shopify/FulfillmentOrder/5001",
                "sku": "sku_pickpack_1",
                "reason": "buyer_cancel_after_pick_pack",
                "sourceEventId": "wh_cancel_5001",
            }
        },
    )
    assert status == 200, hold
    status, cancellation = graphql(
        base_url,
        session_id,
        WAREHOUSE_CANCEL_QUERY,
        {
            "input": {
                "fulfillmentOrderId": "gid://shopify/FulfillmentOrder/5001",
                "sourceEventId": "wh_cancel_5001",
            }
        },
    )
    assert status == 200, cancellation
    assert_passed(complete(base_url, session_id, "stage12_shopify_safe_agent"))


def run_unsupported_mutation_probe(base_url: str) -> None:
    session_id = start_session(base_url, SCN002)
    status, body = request(
        base_url,
        "POST",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/graphql.json",
        {"query": "mutation { productCreate(input: {}) { product { id } } }"},
    )
    assert status == 200, body
    assert body["extensions"]["_commerce_twin_stub"] is True, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    run_scn001_unsafe(base_url)
    run_scn001_safe(base_url)
    run_scn002_unsafe(base_url)
    run_scn002_safe(base_url)
    run_scn003_unsafe(base_url)
    run_scn003_safe(base_url)
    run_scn004_unsafe(base_url)
    run_scn004_safe(base_url)
    run_scn005_unsafe(base_url)
    run_scn005_safe(base_url)
    run_unsupported_mutation_probe(base_url)
    print("Stage 12 Shopify-like skin harness passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
