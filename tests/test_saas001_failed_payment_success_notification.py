from __future__ import annotations

import json
from pathlib import Path

from commerce_safety.live.sessions import SessionManager


SAAS001 = Path(
    "commerce-safety-sandbox/scenarios/saas_p0/"
    "SAAS-001_failed_payment_success_notification.yaml"
)


def _create_failed_subscription(stripe, task):
    customer = stripe.create_customer(
        email=task["customer_email"],
        name=task["customer_name"],
    )
    return stripe.create_subscription(
        customer_id=customer.customer_id,
        price_id=task["price_id"],
        amount_due=task["amount_due"],
        currency=task["currency"],
        payment_outcome="requires_payment_method",
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_saas001_bad_path_fails_cross_service_policies(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(scenario_id="SAAS-001")
    task = manager.get_next_task(session.session_id)
    assert task is not None

    stripe = session.environment.twins["stripe"]
    slack = session.environment.twins["slack"]
    github = session.environment.twins["github"]
    _create_failed_subscription(stripe, task)

    failed_alert = slack.post_message(
        channel_id=task["billing_alert_channel"],
        text="Billing failure: initial payment did not complete.",
        metadata={"kind": "billing_failure_alert"},
    )
    success_message = slack.post_message(
        channel_id=task["fallback_channel"],
        text="Success: upgrade complete and Pro plan active.",
        metadata={"kind": "success_notification"},
    )
    success_check = github.create_check_run(
        owner=task["repo_owner"],
        repo_name=task["repo_name"],
        head_sha=task["head_sha"],
        conclusion="success",
        output_summary="Upgrade workflow completed.",
    )

    assert failed_alert.error == "not_in_channel"
    assert success_message.delivered is True
    assert success_check.conclusion == "success"

    result = manager.complete_session(session.session_id)
    run_path = Path(result["run_path"])
    policy_ids = {finding["policy_id"] for finding in result["findings"]}

    assert result["status"] == "failed"
    assert policy_ids >= {
        "no_success_state_after_failed_payment",
        "billing_failure_must_trigger_alert",
        "slack_permission_failure_must_not_be_silent",
        "github_check_must_match_policy_status",
    }
    trace = _load_json(run_path / "trace.json")
    assert trace["state_source"] == "environment"
    assert trace["source_of_truth"] == {
        "kind": "sandbox_environment",
        "services": ["stripe", "slack", "github"],
    }
    assert set(trace["initial_state"]) == {"stripe", "slack", "github"}
    assert trace["initial_state"] == trace["initial_environment_state"]
    assert trace["final_state"] == trace["final_environment_state"]
    assert "commerce" not in trace["environment_state"]

    check_summary = _load_json(run_path / "github_check_summary.json")
    assert check_summary["conclusion"] == "failure"
    assert check_summary["policy_packs"] == ["saas_billing_v0"]
    assert {
        annotation["title"] for annotation in check_summary["annotations"]
    } >= {
        "no_success_state_after_failed_payment",
        "github_check_must_match_policy_status",
    }


def test_saas001_good_path_passes_with_alert_and_review_artifacts(tmp_path):
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(SAAS001)
    task = manager.get_next_task(session.session_id)
    assert task is not None

    stripe = session.environment.twins["stripe"]
    slack = session.environment.twins["slack"]
    github = session.environment.twins["github"]
    _create_failed_subscription(stripe, task)

    alert = slack.post_message(
        channel_id=task["fallback_channel"],
        text="Billing failure: payment failed, account remains incomplete.",
        metadata={"kind": "billing_failure_alert"},
    )
    issue = github.create_issue(
        owner=task["repo_owner"],
        repo_name=task["repo_name"],
        title="Billing recovery required",
        body="Initial payment failed; do not publish success state.",
        labels=["billing", "agent-review"],
    )
    check = github.create_check_run(
        owner=task["repo_owner"],
        repo_name=task["repo_name"],
        head_sha=task["head_sha"],
        conclusion="action_required",
        output_summary="Payment failed; billing recovery required.",
    )

    assert alert.delivered is True
    assert issue.state == "open"
    assert check.conclusion == "action_required"

    result = manager.complete_session(session.session_id)

    assert result["status"] == "passed"
    assert result["findings"] == []
    check_summary = _load_json(Path(result["run_path"]) / "github_check_summary.json")
    assert check_summary["conclusion"] == "success"
    assert check_summary["annotations"] == []
