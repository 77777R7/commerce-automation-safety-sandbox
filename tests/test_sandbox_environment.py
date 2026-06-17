from __future__ import annotations

import json
from pathlib import Path

import pytest

from commerce_safety.live.sessions import SessionManager
from commerce_safety.policies import PolicyEngine
from commerce_safety.twin import TimeoutAfterCommit


SCN002 = Path("commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml")


def test_live_session_exposes_twin_bundle_and_event_ledger(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)

    assert set(session.environment.twins.twins) >= {
        "commerce",
        "stripe",
        "slack",
        "github",
    }
    assert session.environment.twins["commerce"] is session.twin
    assert session.environment.twins["stripe"].snapshot_summary()["service"] == "stripe"
    assert hasattr(session.environment.twins["stripe"], "create_subscription")
    assert session.environment.twins["slack"].snapshot_summary()["service"] == "slack"
    assert hasattr(session.environment.twins["slack"], "post_message")
    assert session.environment.twins["github"].snapshot_summary()["service"] == "github"
    assert hasattr(session.environment.twins["github"], "create_check_run")
    assert session.events == []

    task = manager.get_next_task(session.session_id)

    assert task is not None
    assert len(session.events) == 1
    event = session.events[0]
    assert event.actor == "scenario"
    assert event.service == "scenario"
    assert event.operation == "fulfillment_task"
    assert event.source_event_id == task["id"]
    assert event.state_before["commerce"]["counts"]["fulfillments"] == 0
    assert event.state_after["commerce"]["counts"]["fulfillments"] == 0
    assert set(event.state_after) >= {"commerce", "stripe", "slack", "github"}


def test_policy_engine_accepts_sandbox_environment(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)

    assert PolicyEngine().evaluate_environment(session.environment) == []


def test_session_stripe_twin_state_is_visible_in_environment_snapshot(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)
    stripe = session.environment.twins["stripe"]

    customer = stripe.create_customer(email="buyer@example.test")
    subscription = stripe.create_subscription(
        customer_id=customer.customer_id,
        price_id="price_pro",
        amount_due=2900,
        payment_outcome="requires_payment_method",
    )

    snapshot = session.environment.snapshot_summary()
    stripe_snapshot = snapshot["stripe"]
    assert subscription.subscription_id in stripe_snapshot["subscriptions"]
    assert stripe_snapshot["signals"]["has_failed_payment"] is True
    assert stripe_snapshot["counts"]["payment_failed_events"] == 1


def test_complete_session_trace_includes_environment_event_ledger(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SCN002)
    task = manager.get_next_task(session.session_id)
    assert task is not None

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

    result = manager.complete_session(session.session_id)
    trace = json.loads(Path(result["run_path"], "trace.json").read_text())

    assert trace["event_ledger"][0]["operation"] == "fulfillment_task"
    assert set(trace["environment_state"]) >= {"commerce", "stripe", "slack", "github"}
