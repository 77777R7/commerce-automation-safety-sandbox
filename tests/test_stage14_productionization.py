from __future__ import annotations

from pathlib import Path

import yaml

from commerce_safety.live.http_api import LiveAPI
from commerce_safety.live.sessions import SessionManager


SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"
SCN003 = "commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml"
SPEC_PATH = Path(__file__).resolve().parents[1] / "docs/openapi/live_twin_api.yaml"


def _request(
    api: LiveAPI,
    method: str,
    path: str,
    payload: dict | None = None,
    headers: dict | None = None,
):
    return api.handle(method, path, payload or {}, headers=headers or {})


def test_http_api_can_require_local_auth_token(tmp_path):
    api = LiveAPI(runs_dir=tmp_path, api_token="stage14-token")

    status, unauthenticated = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
    )

    assert status == 401
    assert unauthenticated == {
        "ok": False,
        "error": {
            "code": "unauthorized",
            "message": "Missing or invalid local auth token.",
            "status": 401,
        },
    }

    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        headers={"Authorization": "Bearer stage14-token"},
    )

    assert status == 201
    assert created["scenario_id"] == "SCN-002"


def test_scenario_registry_supports_ids_and_rejects_paths_outside_allowlist(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)

    status, created = _request(api, "POST", "/sessions", {"scenario_id": "SCN-002"})

    assert status == 201
    assert created["scenario_id"] == "SCN-002"

    outside = tmp_path / "outside.yaml"
    outside.write_text(Path(SCN002).read_text(encoding="utf-8"), encoding="utf-8")

    status, rejected = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_path": str(outside)},
    )

    assert status == 400
    assert rejected["error"]["code"] == "scenario_not_allowed"
    assert "allowlisted scenario" in rejected["error"]["message"]


def test_http_errors_use_consistent_error_envelope(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)

    status, body = _request(api, "GET", "/sessions/not-real/trace")

    assert status == 404
    assert body == {
        "ok": False,
        "error": {
            "code": "session_not_found",
            "message": "Live session not found: not-real",
            "status": 404,
        },
    }


def test_amazon_feed_state_is_session_scoped(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)

    status, first = _request(api, "POST", "/sessions", {"scenario_id": "SCN-003"})
    assert status == 201
    status, second = _request(api, "POST", "/sessions", {"scenario_id": "SCN-003"})
    assert status == 201

    first_id = first["session_id"]
    second_id = second["session_id"]
    status, submitted = _request(
        api,
        "POST",
        f"/sessions/{first_id}/amazon/sp-api/feeds/2021-06-30/feeds",
        {
            "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
            "messages": [{"sellerSku": "SELLER-0001", "quantity": 0}],
        },
    )
    assert status == 202
    feed_id = submitted["payload"]["feedId"]

    status, wrong_session = _request(
        api,
        "GET",
        f"/sessions/{second_id}/amazon/sp-api/feeds/2021-06-30/feeds/{feed_id}",
    )

    assert status == 404
    assert wrong_session["error"]["code"] == "amazon_feed_not_found"


def test_live_session_has_per_session_lock(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(scenario_id="SCN-002")

    assert hasattr(session, "lock")


def test_python_preflight_rejects_python_before_310():
    from commerce_safety.cli import python_supports_agent_interfaces

    assert python_supports_agent_interfaces((3, 9, 18)) is False
    assert python_supports_agent_interfaces((3, 10, 0)) is True


def test_openapi_has_tight_amazon_response_shapes():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    schemas = spec["components"]["schemas"]
    paths = spec["paths"]

    for schema_name in [
        "AmazonInventorySummariesResponse",
        "AmazonFeedResponse",
        "AmazonShipmentConfirmationResponse",
        "AmazonStubResponse",
    ]:
        assert schemas[schema_name]["additionalProperties"] is False

    assert (
        paths["/sessions/{session_id}/amazon/sp-api/fba/inventory/v1/summaries"][
            "get"
        ]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/AmazonInventorySummariesResponse"
    )
    assert (
        paths["/sessions/{session_id}/amazon/sp-api/feeds/{api_version}/feeds"][
            "post"
        ]["responses"]["202"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/AmazonFeedResponse"
    )


def test_stage14_documents_source_vs_generated_pr_split():
    doc = Path("docs/STAGE14_PRODUCTIONIZATION_GATE.md")

    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "source PR" in text
    assert "generated artifacts PR" in text
