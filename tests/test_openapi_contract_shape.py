from __future__ import annotations

from pathlib import Path

import yaml


SPEC_PATH = Path(__file__).resolve().parents[1] / "docs/openapi/live_twin_api.yaml"


def _spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def test_openapi_has_stage10_generic_commerce_action_paths():
    spec = _spec()
    action_names = {
        "reserve_inventory",
        "promise_fulfillment",
        "refresh_inventory",
        "route_manual_review",
        "find_fulfillment",
        "create_refund",
        "create_approval_request",
        "cancel_order",
        "release_inventory",
        "place_workflow_hold",
        "submit_warehouse_cancellation_request",
        "warehouse_continue_fulfillment",
        "skip_duplicate_webhook",
    }

    for action in action_names:
        assert f"/sessions/{{session_id}}/twin/{action}" in spec["paths"]


def test_openapi_has_stage12_shopify_like_skin_paths():
    paths = _spec()["paths"]

    assert "/sessions/{session_id}/shopify/webhooks" in paths
    assert "/sessions/{session_id}/shopify/webhooks/skip_duplicate" in paths
    assert "/sessions/{session_id}/shopify/admin/api/{api_version}/graphql.json" in paths
    assert "/sessions/{session_id}/shopify/admin/api/{api_version}/inventory_levels.json" in paths
    assert "/sessions/{session_id}/shopify/admin/api/{api_version}/inventory_levels/adjust.json" in paths
    assert "/sessions/{session_id}/shopify/actions/{shopify_action}" in paths
    assert "/sessions/{session_id}/shopify/coverage" in paths


def test_openapi_has_stage13_amazon_seller_ops_skin_paths():
    paths = _spec()["paths"]

    assert "/sessions/{session_id}/amazon/sp-api/fba/inventory/v1/summaries" in paths
    assert "/sessions/{session_id}/amazon/sp-api/listings/{api_version}/items/{seller_id}/{sku}" in paths
    assert "/sessions/{session_id}/amazon/sp-api/orders/v0/orders/{amazon_order_id}" in paths
    assert "/sessions/{session_id}/amazon/sp-api/orders/v0/orders/{amazon_order_id}/orderItems" in paths
    assert "/sessions/{session_id}/amazon/sp-api/orders/v0/orders/{amazon_order_id}/shipmentConfirmation" in paths
    assert "/sessions/{session_id}/amazon/sp-api/feeds/{api_version}/feeds" in paths
    assert "/sessions/{session_id}/amazon/sp-api/feeds/{api_version}/feeds/{feed_id}" in paths
    assert "/sessions/{session_id}/amazon/notifications" in paths
    assert "/sessions/{session_id}/amazon/actions/{amazon_action}" in paths
    assert "/sessions/{session_id}/amazon/coverage" in paths


def test_openapi_stage11_tightens_task_and_fulfillment_shapes():
    schemas = _spec()["components"]["schemas"]

    task_schema = schemas["TaskResponse"]["properties"]["task"]
    assert "oneOf" in task_schema
    assert not task_schema.get("additionalProperties")

    fulfillment_schema = schemas["FulfillmentResponse"]["properties"]["fulfillment"]
    assert fulfillment_schema == {"$ref": "#/components/schemas/Fulfillment"}
    assert "additionalProperties" not in schemas["Fulfillment"]


def test_openapi_stage11_tightens_trace_timeline_and_policy_evidence():
    schemas = _spec()["components"]["schemas"]

    timeline_item = schemas["TraceResponse"]["properties"]["timeline"]["items"]
    assert timeline_item == {"$ref": "#/components/schemas/TraceEvent"}
    assert "additionalProperties" not in schemas["TraceEvent"]

    evidence = schemas["PolicyFinding"]["properties"]["evidence"]
    assert "anyOf" in evidence
    assert evidence["anyOf"]
    assert not evidence.get("additionalProperties")


def test_schemathesis_warning_allowlist_is_explicit_and_narrow():
    allowlist = (
        SPEC_PATH.parent / "schemathesis_warning_allowlist.yaml"
    ).read_text(encoding="utf-8")
    data = yaml.safe_load(allowlist)

    assert data["allowed_warnings"] == []
    assert data["policy"] == "zero_schemathesis_warnings"
    assert data["fixture_generator"] == "commerce_safety.live.schemathesis_fixtures"
