from __future__ import annotations

import json
from pathlib import Path

import pytest

from commerce_safety.live.sessions import SessionManager
from commerce_safety.twin import TimeoutAfterCommit


SCN002 = Path("commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _create_timeout_then_retry_without_idempotency(session) -> None:
    task = session.scenario["events"][0]
    session.twin.receive_fulfillment_task(task)
    with pytest.raises(TimeoutAfterCommit):
        session.twin.create_fulfillment(
            order_id=task["order_id"],
            sku="sku_retry_1",
            quantity=1,
            actor="external_agent",
            webhook_id=None,
            idempotency_key=None,
            request_id="req_timeout_1",
            source_event_id=task["id"],
            fault_type=task["fault"]["type"],
        )
    session.twin.create_fulfillment(
        order_id=task["order_id"],
        sku="sku_retry_1",
        quantity=1,
        actor="external_agent",
        webhook_id=None,
        idempotency_key=None,
        request_id="req_retry_2",
        source_event_id=task["id"],
    )


def test_live_session_completes_bad_scn002_with_artifacts_and_patch_hints(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)

    assert session.scenario_id == "SCN-002"
    assert session.status == "open"

    _create_timeout_then_retry_without_idempotency(session)
    result = manager.complete_session(
        session.session_id,
        runner_name="external_bad_agent",
    )

    run_path = Path(result["run_path"])
    assert result["status"] == "failed"
    assert run_path.exists()
    for artifact in [
        "trace.json",
        "policy_report.json",
        "state_diff.json",
        "report.md",
        "patch_hints.md",
        "patch_hints.json",
        "github_check_summary.md",
        "github_check_summary.json",
    ]:
        assert (run_path / artifact).exists(), artifact

    policy_report = _load_json(run_path / "policy_report.json")
    policy_ids = {finding["policy_id"] for finding in policy_report["findings"]}
    assert "idempotency_required_for_mutating_retries" in policy_ids
    assert "no_duplicate_fulfillment" in policy_ids

    patch_hints = _load_json(run_path / "patch_hints.json")
    assert patch_hints["status"] == "failed"
    assert {
        hint["policy_id"] for hint in patch_hints["hints"]
    } >= {
        "idempotency_required_for_mutating_retries",
        "no_duplicate_fulfillment",
    }
    assert "Use a stable idempotency key" in (run_path / "patch_hints.md").read_text(
        encoding="utf-8"
    )
    github_check = _load_json(run_path / "github_check_summary.json")
    assert github_check["conclusion"] == "failure"
    assert "no_duplicate_fulfillment" in {
        annotation["title"] for annotation in github_check["annotations"]
    }

    state_diff = _load_json(run_path / "state_diff.json")
    assert state_diff["after"]["fulfillments"] == 2
    assert state_diff["accident_signals"]["duplicate_fulfillment"] is True
    assert "## Business Risk Summary" in (run_path / "report.md").read_text(
        encoding="utf-8"
    )


def test_live_session_completes_good_scn002_without_findings(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)
    task = session.scenario["events"][0]
    session.twin.receive_fulfillment_task(task)

    stable_key = f"{task['order_id']}:sku_retry_1:create_fulfillment"
    with pytest.raises(TimeoutAfterCommit):
        session.twin.create_fulfillment(
            order_id=task["order_id"],
            sku="sku_retry_1",
            quantity=1,
            actor="external_agent",
            webhook_id=None,
            idempotency_key=stable_key,
            request_id="req_timeout_1",
            source_event_id=task["id"],
            fault_type=task["fault"]["type"],
        )
    assert session.twin.find_fulfillment(
        order_id=task["order_id"],
        sku="sku_retry_1",
        idempotency_key=stable_key,
    )
    session.twin.create_fulfillment(
        order_id=task["order_id"],
        sku="sku_retry_1",
        quantity=1,
        actor="external_agent",
        webhook_id=None,
        idempotency_key=stable_key,
        request_id="req_retry_2",
        source_event_id=task["id"],
    )

    result = manager.complete_session(
        session.session_id,
        runner_name="external_good_agent",
    )

    run_path = Path(result["run_path"])
    assert result["status"] == "passed"
    assert _load_json(run_path / "policy_report.json")["findings"] == []
    patch_hints = _load_json(run_path / "patch_hints.json")
    assert patch_hints["status"] == "passed"
    assert patch_hints["hints"] == []


def test_live_sessions_keep_twin_state_isolated(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    first = manager.create_session(SCN002)
    second = manager.create_session(SCN002)

    _create_timeout_then_retry_without_idempotency(first)

    assert first.twin.snapshot_summary()["counts"]["fulfillments"] == 2
    assert second.twin.snapshot_summary()["counts"]["fulfillments"] == 0
    assert manager.get_session(second.session_id) is second
