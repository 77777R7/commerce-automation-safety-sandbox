from __future__ import annotations

import json
from pathlib import Path

import pytest

from commerce_safety.live.sessions import SessionManager
from commerce_safety.twin import TimeoutAfterCommit


SCN002 = Path("commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml")


def test_failed_live_session_writes_agent_repair_artifacts(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)
    task = manager.get_next_task(session.session_id)

    with pytest.raises(TimeoutAfterCommit):
        session.twin.create_fulfillment(
            order_id=task["order_id"],
            sku="sku_retry_1",
            quantity=1,
            actor="external_bad_agent",
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
        actor="external_bad_agent",
        webhook_id=None,
        idempotency_key=None,
        request_id="req_retry_2",
        source_event_id=task["id"],
    )

    result = manager.complete_session(
        session.session_id,
        runner_name="external_bad_agent",
    )
    run_path = Path(result["run_path"])

    for artifact in [
        "patch_hints.json",
        "patch_hints.md",
        "agent_summary.md",
        "failure_explain.md",
    ]:
        assert (run_path / artifact).exists(), artifact

    patch_hints = json.loads((run_path / "patch_hints.json").read_text())
    assert patch_hints["replay_command"] == f"commerce-safety replay runs/{result['run_id']}"
    assert "Use a stable idempotency key for create_fulfillment." in patch_hints[
        "likely_guardrails"
    ]

    agent_summary = (run_path / "agent_summary.md").read_text(encoding="utf-8")
    assert "idempotency_required_for_mutating_retries" in agent_summary
    assert "commerce-safety replay" in agent_summary
    assert "req_timeout_1" in agent_summary

    failure_explain = (run_path / "failure_explain.md").read_text(encoding="utf-8")
    assert "Root Cause" in failure_explain
    assert "timeout_after_commit" in failure_explain
    assert "ful_002" in failure_explain
