from __future__ import annotations

import json

from commerce_safety.live.http_api import LiveAPI


SCN001 = "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml"
SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


FULFILLMENT_CREATE_QUERY = """
mutation FulfillmentCreate($fulfillment: FulfillmentInput!) {
  fulfillmentCreate(fulfillment: $fulfillment) {
    fulfillment { id status }
    userErrors { field message }
  }
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
