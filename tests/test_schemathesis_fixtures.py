from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "docs/openapi/live_twin_api.yaml"


def _load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _parameter(operation: dict, name: str) -> dict:
    for parameter in operation.get("parameters", []):
        if parameter.get("name") == name:
            return parameter
    raise AssertionError(f"missing parameter {name}")


def test_schemathesis_fixture_spec_rewrites_session_bound_parameters() -> None:
    from commerce_safety.live.schemathesis_fixtures import (
        SchemathesisFixtureValues,
        build_schemathesis_fixture_spec,
    )

    fixture_spec = build_schemathesis_fixture_spec(
        _load_spec(),
        SchemathesisFixtureValues(
            sessions={
                "SCN-001": "sess_fixture_scn001",
                "SCN-002": "sess_fixture_scn002",
                "SCN-003": "sess_fixture_scn003",
                "SCN-004": "sess_fixture_scn004",
                "SCN-005": "sess_fixture_scn005",
            },
            feed_id="feed_fixture_001",
        ),
    )

    next_task = fixture_spec["paths"]["/sessions/{session_id}/tasks/next"]["get"]
    assert _parameter(next_task, "session_id")["schema"]["enum"] == [
        "sess_fixture_scn002"
    ]

    amazon_feed = fixture_spec["paths"][
        "/sessions/{session_id}/amazon/sp-api/feeds/{api_version}/feeds/{feed_id}"
    ]["get"]
    assert _parameter(amazon_feed, "session_id")["schema"]["enum"] == [
        "sess_fixture_scn003"
    ]
    assert _parameter(amazon_feed, "api_version")["schema"]["enum"] == ["2021-06-30"]
    assert _parameter(amazon_feed, "feed_id")["schema"]["enum"] == [
        "feed_fixture_001"
    ]


def test_schemathesis_fixture_spec_constrains_action_paths_and_bodies() -> None:
    from commerce_safety.live.schemathesis_fixtures import (
        SchemathesisFixtureValues,
        build_schemathesis_fixture_spec,
    )

    fixture_spec = build_schemathesis_fixture_spec(
        _load_spec(),
        SchemathesisFixtureValues(
            sessions={
                "SCN-001": "sess_fixture_scn001",
                "SCN-002": "sess_fixture_scn002",
                "SCN-003": "sess_fixture_scn003",
                "SCN-004": "sess_fixture_scn004",
                "SCN-005": "sess_fixture_scn005",
            },
            feed_id="feed_fixture_001",
        ),
    )

    amazon_action = fixture_spec["paths"]["/sessions/{session_id}/amazon/actions/{amazon_action}"][
        "post"
    ]
    assert _parameter(amazon_action, "amazon_action")["schema"]["enum"] == [
        "promise_fulfillment"
    ]
    amazon_body_schema = amazon_action["requestBody"]["content"]["application/json"][
        "schema"
    ]
    assert amazon_body_schema["enum"] == [
        {
            "amazonOrderId": "AMZ-3001",
            "sellerSku": "SELLER-0001",
            "quantity": 1,
            "reason": "schemathesis_contract_fixture",
            "actor": "schemathesis_fixture_agent",
            "sourceEventId": "task_promise_3001",
        }
    ]

    shopify_action = fixture_spec["paths"]["/sessions/{session_id}/shopify/actions/{shopify_action}"][
        "post"
    ]
    assert _parameter(shopify_action, "shopify_action")["schema"]["enum"] == [
        "promise_fulfillment"
    ]
    shopify_body_schema = shopify_action["requestBody"]["content"]["application/json"][
        "schema"
    ]
    assert shopify_body_schema["enum"] == [
        {
            "orderId": "gid://shopify/Order/3001",
            "inventoryItemId": "gid://shopify/InventoryItem/sku_stale_1",
            "sku": "sku_stale_1",
            "quantity": 1,
            "reason": "schemathesis_contract_fixture",
            "sourceEventId": "task_promise_3001",
        }
    ]
