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
    assert "oneOf" in evidence
    assert evidence["oneOf"]
    assert not evidence.get("additionalProperties")


def test_schemathesis_warning_allowlist_is_explicit_and_narrow():
    allowlist = (
        SPEC_PATH.parent / "schemathesis_warning_allowlist.yaml"
    ).read_text(encoding="utf-8")
    data = yaml.safe_load(allowlist)

    assert data["allowed_warnings"] == ["schema_validation_mismatch_for_session_bound_paths"]
    assert set(data["session_bound_paths"]) == {
        "/sessions/{session_id}/tasks/next",
        "/sessions/{session_id}/trace",
        "/sessions/{session_id}/complete",
        "/sessions/{session_id}/twin/create_fulfillment",
        "/sessions/{session_id}/twin/reserve_inventory",
        "/sessions/{session_id}/twin/promise_fulfillment",
        "/sessions/{session_id}/twin/refresh_inventory",
        "/sessions/{session_id}/twin/route_manual_review",
        "/sessions/{session_id}/twin/find_fulfillment",
        "/sessions/{session_id}/twin/create_refund",
        "/sessions/{session_id}/twin/create_approval_request",
        "/sessions/{session_id}/twin/cancel_order",
        "/sessions/{session_id}/twin/release_inventory",
        "/sessions/{session_id}/twin/place_workflow_hold",
        "/sessions/{session_id}/twin/submit_warehouse_cancellation_request",
        "/sessions/{session_id}/twin/warehouse_continue_fulfillment",
        "/sessions/{session_id}/twin/skip_duplicate_webhook",
    }
