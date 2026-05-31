from __future__ import annotations

import json

from commerce_safety.live.http_api import LiveAPI


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

REFUND_CREATE_QUERY = """
mutation RefundCreate($input: RefundInput!) {
  refundCreate(input: $input) { userErrors { field message } }
}
"""

APPROVAL_CREATE_QUERY = """
mutation RefundApprovalRequestCreate($input: RefundApprovalInput!) {
  refundApprovalRequestCreate(input: $input) { userErrors { field message } }
}
"""

ORDER_CANCEL_QUERY = """
mutation OrderCancel($input: OrderCancelInput!) {
  orderCancel(input: $input) { userErrors { field message } }
}
"""

HOLD_QUERY = """
mutation FulfillmentOrderHold($input: FulfillmentOrderHoldInput!) {
  fulfillmentOrderHold(input: $input) { userErrors { field message } }
}
"""

WAREHOUSE_CANCEL_QUERY = """
mutation FulfillmentOrderSubmitCancellationRequest($input: CancellationInput!) {
  fulfillmentOrderSubmitCancellationRequest(input: $input) { userErrors { field message } }
}
"""

WAREHOUSE_CONTINUE_QUERY = """
mutation FulfillmentOrderContinue($input: FulfillmentOrderContinueInput!) {
  fulfillmentOrderContinue(input: $input) { userErrors { field message } }
}
"""

INVENTORY_ADJUST_QUERY = """
mutation InventoryAdjustQuantities($input: InventoryAdjustQuantitiesInput!) {
  inventoryAdjustQuantities(input: $input) { userErrors { field message } }
}
"""


def _request(
    api: LiveAPI,
    method: str,
    path: str,
    payload: dict | None = None,
    headers: dict | None = None,
):
    status, body = api.handle(method, path, payload or {}, headers=headers or {})
    return status, json.loads(json.dumps(body))


def _start(api: LiveAPI, scenario_path: str) -> str:
    status, body = _request(api, "POST", "/sessions", {"scenario_path": scenario_path})
    assert status == 201
    return body["session_id"]


def _shopify_webhook(api: LiveAPI, session_id: str, webhook_id: str):
    return _request(
        api,
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


def _shopify_webhook_skip(api: LiveAPI, session_id: str, webhook_id: str):
    return _request(
        api,
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


def _fulfillment_create(api: LiveAPI, session_id: str, fulfillment: dict):
    return _request(
        api,
        "POST",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/graphql.json",
        {
            "query": FULFILLMENT_CREATE_QUERY,
            "variables": {"fulfillment": fulfillment},
        },
    )


def _graphql(api: LiveAPI, session_id: str, query: str, variables: dict):
    return _request(
        api,
        "POST",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/graphql.json",
        {
            "query": query,
            "variables": variables,
        },
    )


def _shopify_fulfillment_payload(order_number: int, metadata: dict) -> dict:
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


def _complete(api: LiveAPI, session_id: str, runner_name: str):
    return _request(
        api,
        "POST",
        f"/sessions/{session_id}/complete",
        {"runner_name": runner_name},
    )


def _assert_failed_with(body: dict, expected_policy_ids: set[str]):
    assert body["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in body["findings"]}
    missing = expected_policy_ids - policy_ids
    assert not missing, {"missing": sorted(missing), "actual": sorted(policy_ids)}


def test_shopify_scn001_unsafe_duplicate_webhook_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN001)

    status, first_webhook = _shopify_webhook(api, session_id, "wh_paid_001")
    assert status == 202
    assert first_webhook["event"]["id"] == "wh_paid_001"
    status, first = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            1001,
            {"webhook_id": "wh_paid_001", "source_event_id": "wh_paid_001"},
        ),
    )
    assert status == 200
    assert first["data"]["fulfillmentCreate"]["fulfillment"]["id"].endswith("/ful_001")

    status, duplicate_webhook = _shopify_webhook(api, session_id, "wh_paid_001")
    assert status == 202
    assert duplicate_webhook["event"]["raw_topic"] == "orders/paid"
    status, second = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            1001,
            {"webhook_id": "wh_paid_001", "source_event_id": "wh_paid_001"},
        ),
    )
    assert status == 200
    assert second["data"]["fulfillmentCreate"]["fulfillment"]["id"].endswith("/ful_002")

    status, complete = _complete(api, session_id, "shopify_like_unsafe_agent")
    assert status == 200
    assert complete["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in complete["findings"]}
    assert "webhook_dedup_required" in policy_ids
    assert "no_duplicate_fulfillment" in policy_ids


def test_shopify_webhook_accepts_realistic_payload_without_canonical_order_id(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN001)

    status, webhook = _request(
        api,
        "POST",
        f"/sessions/{session_id}/shopify/webhooks",
        {
            "id": 1001,
            "admin_graphql_api_id": "gid://shopify/Order/1001",
        },
        headers={
            "X-Shopify-Topic": "orders/paid",
            "X-Shopify-Webhook-Id": "wh_paid_realistic_001",
        },
    )

    assert status == 202
    assert webhook["event"]["order_id"] == "order_1001"
    assert webhook["event"]["binding_source"] == "shopify_order_id"


def test_shopify_scn001_safe_duplicate_webhook_path_passes_when_agent_dedupes(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN001)

    _shopify_webhook(api, session_id, "wh_paid_001")
    status, first = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            1001,
            {"webhook_id": "wh_paid_001", "source_event_id": "wh_paid_001"},
        ),
    )
    assert status == 200
    assert first["data"]["fulfillmentCreate"]["userErrors"] == []

    _shopify_webhook(api, session_id, "wh_paid_001")
    status, skipped = _shopify_webhook_skip(api, session_id, "wh_paid_001")
    assert status == 200
    assert skipped["event"] == "duplicate_webhook_skipped"

    status, complete = _complete(api, session_id, "shopify_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []

    status, trace = _request(api, "GET", f"/sessions/{session_id}/trace")
    assert status == 200
    assert any(event["event"] == "duplicate_webhook_skipped" for event in trace["timeline"])


def test_shopify_scn002_unsafe_timeout_retry_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN002)
    _, task = _request(api, "GET", f"/sessions/{session_id}/tasks/next")

    status, timeout = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            2001,
            {
                "request_id": "shopify_req_timeout_1",
                "source_event_id": task["task"]["id"],
                "fault_type": "timeout_after_commit",
            },
        ),
    )
    assert status == 504
    assert timeout["extensions"]["_commerce_twin"]["error"] == "timeout_after_commit"

    status, retry = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            2001,
            {
                "request_id": "shopify_req_retry_2",
                "source_event_id": task["task"]["id"],
            },
        ),
    )
    assert status == 200
    assert retry["data"]["fulfillmentCreate"]["fulfillment"]["id"].endswith("/ful_002")

    status, complete = _complete(api, session_id, "shopify_like_unsafe_agent")
    assert status == 200
    assert complete["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in complete["findings"]}
    assert "idempotency_required_for_mutating_retries" in policy_ids
    assert "no_duplicate_fulfillment" in policy_ids


def test_shopify_scn002_safe_timeout_retry_path_passes_with_idempotency_key(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN002)
    _, task = _request(api, "GET", f"/sessions/{session_id}/tasks/next")
    key = f"{task['task']['order_id']}:sku_retry_1:create_fulfillment"

    status, timeout = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            2001,
            {
                "idempotency_key": key,
                "request_id": "shopify_req_timeout_1",
                "source_event_id": task["task"]["id"],
                "fault_type": "timeout_after_commit",
            },
        ),
    )
    assert status == 504
    assert timeout["extensions"]["_commerce_twin"]["fulfillment_id"] == "ful_001"

    status, replay = _fulfillment_create(
        api,
        session_id,
        _shopify_fulfillment_payload(
            2001,
            {
                "idempotency_key": key,
                "request_id": "shopify_req_retry_2",
                "source_event_id": task["task"]["id"],
            },
        ),
    )
    assert status == 200
    assert replay["data"]["fulfillmentCreate"]["fulfillment"]["id"].endswith("/ful_001")

    status, complete = _complete(api, session_id, "shopify_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []


def test_shopify_graphql_accepts_platform_fulfillment_ids(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN002)
    _, task = _request(api, "GET", f"/sessions/{session_id}/tasks/next")
    key = "order_2001:sku_retry_1:create_fulfillment"

    status, timeout = _fulfillment_create(
        api,
        session_id,
        {
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
                "idempotency_key": key,
                "request_id": "shopify_platform_req_timeout_1",
                "source_event_id": task["task"]["id"],
                "fault_type": "timeout_after_commit",
            },
        },
    )

    assert status == 504
    assert timeout["extensions"]["_commerce_twin"]["fulfillment_id"] == "ful_001"


def test_shopify_scn003_unsafe_stale_inventory_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, inventory = _request(
        api,
        "GET",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/inventory_levels.json"
        "?inventory_item_ids=gid://shopify/InventoryItem/sku_stale_1",
    )
    assert status == 200
    level = inventory["inventory_levels"][0]
    assert level["available"] == 1
    assert level["_commerce_twin"]["true_available"] == 0
    assert level["_commerce_twin"]["source_version"] == "stale"

    status, promise = _request(
        api,
        "POST",
        f"/sessions/{session_id}/shopify/actions/promise_fulfillment",
        {
            "orderId": "gid://shopify/Order/3001",
            "sku": "sku_stale_1",
            "quantity": 1,
            "sourceEventId": "task_promise_3001",
        },
    )
    assert status == 200
    assert promise["promise"]["promise_id"] == "promise_001"

    status, complete = _complete(api, session_id, "shopify_like_unsafe_agent")
    assert status == 200
    _assert_failed_with(
        complete,
        {
            "reservation_required_before_promise",
            "no_inventory_commit_from_stale_snapshot",
            "no_oversell",
        },
    )


def test_shopify_scn003_safe_stale_inventory_path_passes_with_review(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, inventory = _request(
        api,
        "GET",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/inventory_levels.json"
        "?inventory_item_ids=gid://shopify/InventoryItem/sku_stale_1",
    )
    assert status == 200
    assert inventory["inventory_levels"][0]["_commerce_twin"]["true_available"] == 0

    status, review = _request(
        api,
        "POST",
        f"/sessions/{session_id}/shopify/actions/route_manual_review",
        {
            "orderId": "gid://shopify/Order/3001",
            "sku": "sku_stale_1",
            "reason": "fresh_inventory_unavailable",
            "sourceEventId": "task_promise_3001",
        },
    )
    assert status == 200
    assert review["ok"] is True

    status, complete = _complete(api, session_id, "shopify_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []


def test_shopify_inventory_adjust_reservation_maps_to_permissive_twin(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, response = _graphql(
        api,
        session_id,
        INVENTORY_ADJUST_QUERY,
        {
            "input": {
                "reason": "reservation",
                "metadata": {"orderId": "gid://shopify/Order/3001"},
                "changes": [
                    {
                        "inventoryItemId": "gid://shopify/InventoryItem/sku_stale_1",
                        "delta": -1,
                    }
                ],
            }
        },
    )

    assert status == 200
    result = response["data"]["inventoryAdjustQuantities"]["result"]
    assert result["inventory_adjustment"]["action"] == "reserve_inventory"
    assert result["inventory_adjustment"]["reservation"]["reservation_id"] == "res_001"


def test_shopify_scn004_unsafe_refund_after_shipment_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN004)

    status, refund = _graphql(
        api,
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
    assert status == 200
    assert refund["data"]["refundCreate"]["result"]["refund"]["refund_id"] == "refund_001"

    status, complete = _complete(api, session_id, "shopify_like_unsafe_agent")
    assert status == 200
    _assert_failed_with(
        complete,
        {
            "no_refund_after_shipment_without_approval",
            "high_value_refund_requires_approval",
        },
    )


def test_shopify_scn004_safe_refund_after_shipment_path_passes_with_approval(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN004)

    status, approval = _graphql(
        api,
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
    assert status == 200
    approval_result = approval["data"]["refundApprovalRequestCreate"]["result"]
    assert approval_result["approval_request"]["approval_id"] == "approval_001"

    status, complete = _complete(api, session_id, "shopify_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []


def test_shopify_scn005_unsafe_cancel_after_pick_pack_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN005)

    status, cancel_webhook = _request(
        api,
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
            "X-Shopify-Webhook-Id": "wh_cancel_5001",
        },
    )
    assert status == 202
    assert cancel_webhook["event"]["topic"] == "cancel_request"

    status, cancelled = _graphql(
        api,
        session_id,
        ORDER_CANCEL_QUERY,
        {
            "input": {
                "id": "gid://shopify/Order/5001",
                "sourceEventId": "wh_cancel_5001",
            }
        },
    )
    assert status == 200
    assert cancelled["data"]["orderCancel"]["result"]["ok"] is True

    status, released = _graphql(
        api,
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
    assert status == 200
    assert released["data"]["inventoryAdjustQuantities"]["result"][
        "inventory_adjustment"
    ]["action"] == "release_inventory"

    status, refund = _graphql(
        api,
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
    assert status == 200
    assert refund["data"]["refundCreate"]["result"]["refund"]["refund_id"] == "refund_001"

    status, continued = _graphql(
        api,
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
    assert status == 200
    assert continued["data"]["fulfillmentOrderContinue"]["result"][
        "warehouse_job"
    ]["continued_after_cancel"] is True

    status, complete = _complete(api, session_id, "shopify_like_unsafe_agent")
    assert status == 200
    _assert_failed_with(
        complete,
        {
            "warehouse_conflict_requires_hold",
            "no_ship_after_cancel",
            "no_double_refund_or_inventory_release",
        },
    )


def test_shopify_scn005_safe_cancel_after_pick_pack_path_passes_with_hold(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN005)

    _request(
        api,
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
            "X-Shopify-Webhook-Id": "wh_cancel_5001",
        },
    )
    status, hold = _graphql(
        api,
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
    assert status == 200
    assert hold["data"]["fulfillmentOrderHold"]["result"]["workflow_hold"][
        "hold_id"
    ] == "hold_001"

    status, cancellation = _graphql(
        api,
        session_id,
        WAREHOUSE_CANCEL_QUERY,
        {
            "input": {
                "fulfillmentOrderId": "gid://shopify/FulfillmentOrder/5001",
                "sourceEventId": "wh_cancel_5001",
            }
        },
    )
    assert status == 200
    assert cancellation["data"]["fulfillmentOrderSubmitCancellationRequest"][
        "result"
    ]["warehouse_cancellation_request"]["cancellation_request_id"] == "wh_cancel_001"

    status, complete = _complete(api, session_id, "shopify_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []


def test_shopify_unsupported_mutation_returns_explicit_stub(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN002)

    status, response = _request(
        api,
        "POST",
        f"/sessions/{session_id}/shopify/admin/api/2026-04/graphql.json",
        {"query": "mutation { productCreate(input: {}) { product { id } } }"},
    )

    assert status == 200
    assert response["extensions"]["_commerce_twin_stub"] is True
    assert response["extensions"]["coverage"] == "unsupported"


def test_shopify_coverage_endpoint_exposes_binding_status(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN002)

    status, response = _request(
        api,
        "GET",
        f"/sessions/{session_id}/shopify/coverage",
    )

    assert status == 200
    assert response["coverage"]["skin"] == "shopify_like"
    assert response["coverage"]["mutations"]["fulfillmentCreate"] == "stateful"
