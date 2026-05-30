from __future__ import annotations

import json
from pathlib import Path

from commerce_safety.cli import build_parser
from commerce_safety.live.http_api import LiveAPI


SCN002 = "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"


def test_cli_live_serve_command_is_registered():
    args = build_parser().parse_args(["live", "serve", "--host", "127.0.0.1", "--port", "0"])

    assert args.command == "live"
    assert args.live_command == "serve"
    assert args.host == "127.0.0.1"
    assert args.port == 0


def _request(method: str, api: LiveAPI, path: str, payload: dict | None = None):
    status, body = api.handle(method, path, payload or {})
    return status, json.loads(json.dumps(body))


def test_http_scn002_bad_external_agent_fails_after_unsafe_retry(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    status, created = _request("POST", api, "/sessions", {"scenario_path": SCN002})
    assert status == 201
    session_id = created["session_id"]

    status, task = _request("GET", api, f"/sessions/{session_id}/tasks/next")
    assert status == 200
    assert task["task"]["id"] == "task_fulfill_2001"

    status, first = _request(
        "POST",
        api,
        f"/sessions/{session_id}/twin/create_fulfillment",
        {
            "order_id": task["task"]["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "external_bad_agent",
            "request_id": "http_req_timeout_1",
            "source_event_id": task["task"]["id"],
            "fault_type": task["task"]["fault"]["type"],
        },
    )
    assert status == 504
    assert first["error"] == "timeout_after_commit"

    status, retry = _request(
        "POST",
        api,
        f"/sessions/{session_id}/twin/create_fulfillment",
        {
            "order_id": task["task"]["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "external_bad_agent",
            "request_id": "http_req_retry_2",
            "source_event_id": task["task"]["id"],
        },
    )
    assert status == 200
    assert retry["ok"] is True
    assert retry["fulfillment"]["fulfillment_id"] == "ful_002"

    status, trace = _request("GET", api, f"/sessions/{session_id}/trace")
    assert status == 200
    assert any(event["event"] == "fault_injected" for event in trace["timeline"])

    status, complete = _request(
        "POST",
        api,
        f"/sessions/{session_id}/complete",
        {"runner_name": "external_bad_agent"},
    )
    assert status == 200
    assert complete["status"] == "failed"
    policy_ids = {finding["policy_id"] for finding in complete["findings"]}
    assert "idempotency_required_for_mutating_retries" in policy_ids
    assert "no_duplicate_fulfillment" in policy_ids
    run_path = Path(complete["run_path"])
    assert (run_path / "trace.json").exists()
    assert (run_path / "patch_hints.json").exists()


def test_http_create_session_returns_400_for_missing_scenario_file(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)

    status, body = _request("POST", api, "/sessions", {"scenario_path": "not-real.yaml"})

    assert status == 400
    assert body["ok"] is False
    assert "not-real.yaml" in body["error"]


def test_http_scn002_good_external_agent_passes_with_stable_idempotency_key(tmp_path):
    api = LiveAPI(runs_dir=tmp_path)
    status, created = _request("POST", api, "/sessions", {"scenario_path": SCN002})
    assert status == 201
    session_id = created["session_id"]
    _, task = _request("GET", api, f"/sessions/{session_id}/tasks/next")
    stable_key = f"{task['task']['order_id']}:sku_retry_1:create_fulfillment"

    status, first = _request(
        "POST",
        api,
        f"/sessions/{session_id}/twin/create_fulfillment",
        {
            "order_id": task["task"]["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "external_good_agent",
            "idempotency_key": stable_key,
            "request_id": "http_req_timeout_1",
            "source_event_id": task["task"]["id"],
            "fault_type": task["task"]["fault"]["type"],
        },
    )
    assert status == 504
    assert first["error"] == "timeout_after_commit"

    status, replay = _request(
        "POST",
        api,
        f"/sessions/{session_id}/twin/create_fulfillment",
        {
            "order_id": task["task"]["order_id"],
            "sku": "sku_retry_1",
            "quantity": 1,
            "actor": "external_good_agent",
            "idempotency_key": stable_key,
            "request_id": "http_req_retry_2",
            "source_event_id": task["task"]["id"],
        },
    )
    assert status == 200
    assert replay["fulfillment"]["fulfillment_id"] == "ful_001"

    status, complete = _request(
        "POST",
        api,
        f"/sessions/{session_id}/complete",
        {"runner_name": "external_good_agent"},
    )
    assert status == 200
    assert complete["status"] == "passed"
    assert complete["findings"] == []
