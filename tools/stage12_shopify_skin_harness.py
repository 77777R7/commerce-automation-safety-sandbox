from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


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
    run_unsupported_mutation_probe(base_url)
    print("Stage 12 Shopify-like skin harness passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
