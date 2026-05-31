from __future__ import annotations

import json

from commerce_safety.live.http_api import LiveAPI


SCN003 = "commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml"
SCN005 = "commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml"


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


def _complete(api: LiveAPI, session_id: str, runner_name: str):
    return _request(
        api,
        "POST",
        f"/sessions/{session_id}/complete",
        {"runner_name": runner_name},
    )


def test_amazon_scn003_unsafe_stale_inventory_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, inventory = _request(
        api,
        "GET",
        f"/sessions/{session_id}/amazon/sp-api/fba/inventory/v1/summaries?sellerSkus=sku_stale_1",
    )
    assert status == 200
    summary = inventory["payload"]["inventorySummaries"][0]
    assert summary["sellerSku"] == "sku_stale_1" or summary["sellerSku"] == "SELLER-0001"
    assert summary["inventoryDetails"]["fulfillableQuantity"] == 1
    assert summary["_commerce_twin"]["trueAvailable"] == 0
    assert summary["_commerce_twin"]["snapshotVersion"] == "stale"
    assert summary["_commerce_twin"]["sellerId"] == "A1COMMERCESELLER"
    assert summary["_commerce_twin"]["marketplaceIds"] == ["ATVPDKIKX0DER"]

    status, promise = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/actions/promise_fulfillment",
        {
            "amazonOrderId": "AMZ-3001",
            "sellerSku": "sku_stale_1",
            "quantity": 1,
            "sourceEventId": "task_promise_3001",
        },
    )
    assert status == 200
    assert promise["promise"]["promise_id"] == "promise_001"

    status, complete = _complete(api, session_id, "amazon_like_unsafe_agent")
    assert status == 200
    assert complete["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in complete["findings"]}
    assert "amazon_no_promise_from_stale_inventory_summary" in policy_ids
    assert "reservation_required_before_promise" in policy_ids
    assert "no_oversell" in policy_ids


def test_amazon_scn003_safe_stale_inventory_path_passes_with_review(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, listing = _request(
        api,
        "GET",
        f"/sessions/{session_id}/amazon/sp-api/listings/2021-08-01/items/seller_123/sku_stale_1",
    )
    assert status == 200
    assert listing["fulfillmentAvailability"][0]["quantity"] == 0
    assert listing["sellerBinding"]["knownSeller"] is True
    assert listing["summaries"][0]["marketplaceId"] == "ATVPDKIKX0DER"

    status, review = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/actions/route_manual_review",
        {
            "amazonOrderId": "AMZ-3001",
            "sellerSku": "sku_stale_1",
            "reason": "fresh_inventory_unavailable",
            "sourceEventId": "task_promise_3001",
        },
    )
    assert status == 200
    assert review["ok"] is True

    status, complete = _complete(api, session_id, "amazon_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []


def test_amazon_scn005_unsafe_cancel_after_pick_pack_path_fails(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN005)

    status, notification = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/notifications",
        {
            "notificationType": "ORDER_CHANGE",
            "payload": {
                "AmazonOrderId": "AMZ-5001",
                "OrderChangeType": "BuyerRequestedCancel",
            },
        },
    )
    assert status == 202
    assert notification["event"]["type"] == "cancel_request"

    status, cancelled = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/actions/cancel_order",
        {"amazonOrderId": "AMZ-5001", "sourceEventId": "amazon_order_change_AMZ-5001"},
    )
    assert status == 200
    assert cancelled["ok"] is True

    status, shipment = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/sp-api/orders/v0/orders/AMZ-5001/shipmentConfirmation",
        {
            "packageDetail": {
                "packageReferenceId": "1",
                "trackingNumber": "1Z999",
                "carrierCode": "UPS",
                "orderItems": [
                    {
                        "orderItemId": "AMZ-5001-0",
                        "quantity": 1,
                    }
                ],
            }
        },
    )
    assert status == 200
    assert shipment["payload"]["shipmentStatus"] == "confirmed"
    status, trace = _request(api, "GET", f"/sessions/{session_id}/trace")
    assert status == 200
    event_names = [event["event"] for event in trace["timeline"]]
    assert "amazon_buyer_cancel_received" in event_names
    shipment_event = next(
        event for event in trace["timeline"] if event["event"] == "amazon_shipment_confirmed"
    )
    assert shipment_event["details"]["risk_signal"] == "confirmShipment_after_buyer_cancel"
    assert shipment_event["details"]["cancel_requested_before_confirmation"] is True
    assert shipment_event["details"]["warehouse_status_before_confirmation"] == "picked"

    status, complete = _complete(api, session_id, "amazon_like_unsafe_agent")
    assert status == 200
    assert complete["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in complete["findings"]}
    assert "amazon_no_confirm_shipment_after_buyer_cancel_without_review" in policy_ids
    assert "warehouse_conflict_requires_hold" in policy_ids
    assert "no_ship_after_cancel" in policy_ids


def test_amazon_scn005_safe_cancel_after_pick_pack_path_passes_with_hold(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN005)

    _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/notifications",
        {
            "notificationType": "ORDER_CHANGE",
            "payload": {
                "AmazonOrderId": "AMZ-5001",
                "OrderChangeType": "BuyerRequestedCancel",
            },
        },
    )
    status, hold = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/actions/place_workflow_hold",
        {
            "amazonOrderId": "AMZ-5001",
            "sellerSku": "sku_pickpack_1",
            "reason": "buyer_cancel_after_pick_pack",
            "sourceEventId": "amazon_order_change_AMZ-5001",
        },
    )
    assert status == 200
    assert hold["workflow_hold"]["hold_id"] == "hold_001"

    status, cancellation = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/actions/submit_warehouse_cancellation_request",
        {
            "amazonOrderId": "AMZ-5001",
            "sourceEventId": "amazon_order_change_AMZ-5001",
        },
    )
    assert status == 200
    assert cancellation["warehouse_cancellation_request"]["cancellation_request_id"] == "wh_cancel_001"

    status, complete = _complete(api, session_id, "amazon_like_safe_agent")
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []


def test_amazon_coverage_endpoint_exposes_stateful_surface(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, response = _request(api, "GET", f"/sessions/{session_id}/amazon/coverage")

    assert status == 200
    assert response["coverage"]["skin"] == "amazon_seller_ops"
    assert response["coverage"]["routes"]["getInventorySummaries"] == "stateful"
    assert response["coverage"]["routes"]["confirmShipment"] == "stateful"
    assert response["coverage"]["routes"]["getFeed"] == "stateful_with_processing_report"
    assert response["coverage"]["binding"]["sellerId"]["canonical"] == "A1COMMERCESELLER"


def test_amazon_feed_processing_report_is_available_after_poll(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, submitted = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/sp-api/feeds/2021-06-30/feeds",
        {
            "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
            "messages": [{"sellerSku": "SELLER-0001", "quantity": 0}],
        },
    )
    assert status == 202
    feed_id = submitted["payload"]["feedId"]
    assert submitted["payload"]["processingStatus"] == "IN_QUEUE"
    assert submitted["payload"]["resultFeedDocumentId"] == f"feed_result_{feed_id}"

    status, polled = _request(
        api,
        "GET",
        f"/sessions/{session_id}/amazon/sp-api/feeds/2021-06-30/feeds/{feed_id}",
    )
    assert status == 200
    assert polled["payload"]["processingStatus"] == "DONE"
    report = polled["payload"]["processingReport"]
    assert report["processingSummary"]["messagesProcessed"] == 1
    assert report["processingSummary"]["messagesWithError"] == 0

    status, trace = _request(api, "GET", f"/sessions/{session_id}/trace")
    assert status == 200
    assert any(
        event["event"] == "amazon_feed_processing_report_ready"
        for event in trace["timeline"]
    )


def test_amazon_rate_limit_then_retry_inventory_summary(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, limited = _request(
        api,
        "GET",
        f"/sessions/{session_id}/amazon/sp-api/fba/inventory/v1/summaries"
        "?sellerSkus=SELLER-0001&simulateRateLimit=true",
    )
    assert status == 429
    assert limited["error"] == "rate_limited"
    assert limited["retryAfterSeconds"] == 2
    assert limited["_commerce_twin"]["retryable"] is True

    status, retried = _request(
        api,
        "GET",
        f"/sessions/{session_id}/amazon/sp-api/fba/inventory/v1/summaries"
        "?sellerSkus=SELLER-0001",
    )
    assert status == 200
    assert retried["payload"]["inventorySummaries"][0]["_commerce_twin"][
        "canonicalSku"
    ] == "sku_stale_1"
    status, trace = _request(api, "GET", f"/sessions/{session_id}/trace")
    assert status == 200
    rate_limit_event = next(
        event for event in trace["timeline"] if event["event"] == "amazon_rate_limit_injected"
    )
    assert rate_limit_event["details"]["operation"] == "getInventorySummaries"
    assert rate_limit_event["details"]["retryable"] is True


def test_amazon_unsupported_surface_returns_stub_metadata(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    session_id = _start(api, SCN003)

    status, notification = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/notifications",
        {"notificationType": "ANY_OFFER_CHANGED", "payload": {}},
    )
    assert status == 202
    assert notification["_commerce_twin_stub"] is True
    assert notification["stub"]["contract"] == "explicit_stub_not_full_sp_api"
    assert notification["_commerce_twin"]["coverage"] == "stub"

    status, action = _request(
        api,
        "POST",
        f"/sessions/{session_id}/amazon/actions/create_return",
        {"amazonOrderId": "AMZ-3001"},
    )
    assert status == 200
    assert action["_commerce_twin_stub"] is True
    assert action["stub"]["surface"] == "actions/create_return"
