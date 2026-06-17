from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "demo_pack" / "saas_agent_validation"
PROMPT = ROOT / "demo_pack" / "prompts" / "saas001_mcp_agent_test.md"
EXAMPLES = ROOT / "examples" / "agent_integrations"


EXPECTED_POLICIES = {
    "no_success_state_after_failed_payment",
    "billing_failure_must_trigger_alert",
    "slack_permission_failure_must_not_be_silent",
    "github_check_must_match_policy_status",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_saas001_demo_pack_reader_materials_exist() -> None:
    for relative in [
        "README.md",
        "demo_walkthrough.md",
        "investor_demo_script.md",
        "design_partner_walkthrough.md",
        "http_curl_bad_good.md",
    ]:
        assert (PACK / relative).is_file(), relative
    assert PROMPT.is_file()


def test_saas001_demo_pack_is_external_agent_facing() -> None:
    text = (PACK / "README.md").read_text(encoding="utf-8")
    prompt = PROMPT.read_text(encoding="utf-8")

    assert "Crash-test AI agents before they touch Stripe, Slack, and GitHub" in text
    assert "Permissive Twin + Policy Check" in text
    assert "Agent builders" in text
    assert "Investors" in text
    assert "Design partners" in text
    assert "No production Stripe keys" in text
    assert "sandbox.start_session" in prompt
    assert "stripe.create_subscription" in prompt
    assert "github.create_check_run" in prompt


def test_saas001_sample_outputs_keep_required_artifact_contract() -> None:
    for status_dir in ["failed", "passed"]:
        root = PACK / "sample_outputs" / status_dir
        for artifact in [
            "trace.json",
            "policy_report.json",
            "state_diff.json",
            "patch_hints.json",
            "github_check_summary.json",
            "run_manifest.json",
            "agent_summary.md",
            "trace_excerpt.json",
        ]:
            assert (root / artifact).is_file(), f"{status_dir}/{artifact}"

    failed_policy = _load_json(PACK / "sample_outputs" / "failed" / "policy_report.json")
    passed_policy = _load_json(PACK / "sample_outputs" / "passed" / "policy_report.json")
    failed_trace = _load_json(PACK / "sample_outputs" / "failed" / "trace_excerpt.json")
    failed_check = _load_json(
        PACK / "sample_outputs" / "failed" / "github_check_summary.json"
    )
    passed_check = _load_json(
        PACK / "sample_outputs" / "passed" / "github_check_summary.json"
    )

    assert failed_policy["status"] == "failed"
    assert failed_policy["policy_packs"] == ["saas_billing_v0"]
    assert failed_check["conclusion"] == "failure"
    assert passed_check["conclusion"] == "success"
    assert EXPECTED_POLICIES.issubset(
        {finding["policy_id"] for finding in failed_policy["findings"]}
    )
    assert passed_policy["status"] == "passed"
    assert passed_policy["policy_packs"] == ["saas_billing_v0"]
    assert passed_policy["findings"] == []
    assert {"stripe", "slack", "github"}.issubset(
        {event["service"] for event in failed_trace["event_ledger"]}
    )
    assert any(event["fault"] == "not_in_channel" for event in failed_trace["event_ledger"])


def test_saas001_sample_artifacts_are_saas_agent_validation_first() -> None:
    failed_root = PACK / "sample_outputs" / "failed"
    passed_root = PACK / "sample_outputs" / "passed"
    failed_state = _load_json(failed_root / "state_diff.json")
    passed_state = _load_json(passed_root / "state_diff.json")
    failed_report = (failed_root / "report.md").read_text(encoding="utf-8")
    failed_summary = (failed_root / "agent_summary.md").read_text(encoding="utf-8")
    failed_explain = (failed_root / "failure_explain.md").read_text(encoding="utf-8")
    passed_report = (passed_root / "report.md").read_text(encoding="utf-8")

    assert failed_state["artifact_kind"] == "environment_state_diff"
    assert failed_state["services"] == ["stripe", "slack", "github"]
    assert failed_state["accident_signals"]["stripe_failed_payment"] is True
    assert failed_state["accident_signals"]["slack_billing_alert_failed"] is True
    assert failed_state["accident_signals"]["github_success_after_slack_fault"] is True
    assert passed_state["accident_signals"]["slack_billing_alert_delivered"] is True
    assert passed_state["accident_signals"]["github_action_required_check"] is True

    assert failed_report.startswith("# SaaS Agent Validation Report")
    assert "## Cross-Service State" in failed_report
    assert "## Agent Behavior Timeline" in failed_report
    assert "Stripe" in failed_report and "Slack" in failed_report and "GitHub" in failed_report
    assert "Fulfillments before" not in failed_report
    assert "Reserved inventory" not in failed_report
    assert "## What Worked" in passed_report

    assert "Validation surface: `Stripe + Slack + GitHub`" in failed_summary
    assert "## Unsafe Chain" in failed_summary
    assert "## Repair Contract" in failed_summary
    assert "## Agent Event Ledger" in failed_explain
    assert "github.checks.create" in failed_explain


def test_saas001_examples_and_smoke_are_packaged() -> None:
    for relative in [
        "http_saas001_failed_payment_agent.py",
        "mcp_saas001_failed_payment_agent.py",
    ]:
        text = (EXAMPLES / relative).read_text(encoding="utf-8")
        assert "SAAS-001" in text
        assert '"run_path"' in text
        assert '"findings"' in text
        assert "sk_live_" not in text
        assert "xoxb-" not in text

    smoke = (ROOT / "tools" / "smoke_saas001_demo_pack.sh").read_text(
        encoding="utf-8"
    )
    assert "http_saas001_failed_payment_agent.py" in smoke
    assert "mcp_saas001_failed_payment_agent.py" in smoke
    assert "generate_saas001_demo_pack.py" in smoke
