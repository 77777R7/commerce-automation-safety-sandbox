from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "demo_pack" / "saas003_duplicate_webhook"

DUPLICATE_POLICY = "stripe_duplicate_webhook_side_effects_must_be_deduped"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_saas003_demo_pack_reader_materials_exist() -> None:
    for relative in [
        "README.md",
        "index.html",
        "runbook.md",
        "investor_demo_script.md",
        "design_partner_walkthrough.md",
    ]:
        assert (PACK / relative).is_file(), relative


def test_saas003_demo_pack_is_stateful_external_service_story() -> None:
    readme = (PACK / "README.md").read_text(encoding="utf-8")
    runbook = (PACK / "runbook.md").read_text(encoding="utf-8")
    design_partner = (PACK / "design_partner_walkthrough.md").read_text(
        encoding="utf-8"
    )

    assert "duplicate Stripe invoice.payment_failed webhook" in readme
    assert "PR-check-style" in design_partner
    assert "stripe_deliver_webhook" in runbook
    assert "stripe_event_id = evt_000003" in runbook
    assert "No production Stripe keys" in readme
    assert "External Agent Prompt" in runbook
    assert "Do not inspect Python objects" in runbook


def test_saas003_demo_pack_has_investor_first_viewer() -> None:
    viewer = (PACK / "index.html").read_text(encoding="utf-8")
    investor_script = (PACK / "investor_demo_script.md").read_text(encoding="utf-8")

    assert "One Stripe event created duplicate recovery work." in viewer
    assert "Expected" in viewer
    assert "Observed" in viewer
    assert "Why this is not a mock" in viewer
    assert "sample_outputs/failed/github_check_summary.md" in viewer
    assert "Who Pays" in investor_script
    assert "Why Now" in investor_script
    assert "Why This Is Not A Mock" in investor_script


def test_saas003_sample_outputs_keep_required_artifact_contract() -> None:
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
    failed_check = _load_json(
        PACK / "sample_outputs" / "failed" / "github_check_summary.json"
    )
    passed_check = _load_json(
        PACK / "sample_outputs" / "passed" / "github_check_summary.json"
    )
    failed_manifest = _load_json(
        PACK / "sample_outputs" / "failed" / "run_manifest.json"
    )

    assert failed_policy["status"] == "failed"
    assert failed_policy["policy_packs"] == ["saas_billing_v0"]
    assert {finding["policy_id"] for finding in failed_policy["findings"]} == {
        DUPLICATE_POLICY
    }
    assert failed_check["conclusion"] == "failure"
    assert failed_check["output"]["incident"]["stripe_event_id"] == "evt_000003"
    assert failed_check["output"]["incident"]["observed"]["slack_billing_alerts"] == 2
    assert failed_manifest["product_name"] == "Agent Integration Safety Sandbox"
    assert failed_manifest["product_surface"] == "SaaS Agent Validation Sandbox"
    assert failed_manifest["artifact_schema_alias"] == "agent_validation.artifacts.v1"
    assert passed_policy["status"] == "passed"
    assert passed_policy["policy_packs"] == ["saas_billing_v0"]
    assert passed_policy["findings"] == []
    assert passed_check["conclusion"] == "success"


def test_saas003_sample_artifacts_show_duplicate_delivery_without_safe_side_effects() -> None:
    failed_state = _load_json(PACK / "sample_outputs" / "failed" / "state_diff.json")
    passed_state = _load_json(PACK / "sample_outputs" / "passed" / "state_diff.json")
    failed_excerpt = _load_json(PACK / "sample_outputs" / "failed" / "trace_excerpt.json")
    passed_excerpt = _load_json(PACK / "sample_outputs" / "passed" / "trace_excerpt.json")
    failed_summary = (
        PACK / "sample_outputs" / "failed" / "agent_summary.md"
    ).read_text(encoding="utf-8")
    failed_check_markdown = (
        PACK / "sample_outputs" / "failed" / "github_check_summary.md"
    ).read_text(encoding="utf-8")

    assert failed_state["artifact_kind"] == "environment_state_diff"
    assert failed_state["accident_signals"]["stripe_duplicate_webhook_delivery"] is True
    assert (
        failed_state["accident_signals"][
            "duplicate_slack_side_effects_from_stripe_webhook"
        ]
        is True
    )
    assert (
        failed_state["accident_signals"][
            "duplicate_github_side_effects_from_stripe_webhook"
        ]
        is True
    )
    assert passed_state["accident_signals"]["stripe_duplicate_webhook_delivery"] is True
    assert (
        passed_state["accident_signals"][
            "duplicate_slack_side_effects_from_stripe_webhook"
        ]
        is False
    )
    assert (
        passed_state["accident_signals"][
            "duplicate_github_side_effects_from_stripe_webhook"
        ]
        is False
    )
    assert failed_excerpt["state_source"] == "environment"
    assert passed_excerpt["state_source"] == "environment"
    assert any(
        event["fault"] == "duplicate_webhook"
        for event in failed_excerpt["event_ledger"]
    )
    assert DUPLICATE_POLICY in failed_summary
    assert "## Incident Card" in failed_check_markdown
    assert "| Slack billing alerts | 1 | 2 |" in failed_check_markdown
    assert "Raw evidence: see `policy_report.json`." in failed_check_markdown


def test_saas_billing_policy_pack_has_commercial_page() -> None:
    policy_page = ROOT / "policy_packs" / "saas_billing_v0.md"
    text = policy_page.read_text(encoding="utf-8")

    assert policy_page.is_file()
    assert "SaaS Billing Agent Safety Pack V0" in text
    assert "Duplicate webhook created duplicate recovery work" in text
    assert "Five-Minute Demo Path" in text


def test_saas003_generator_is_packaged() -> None:
    generator = ROOT / "tools" / "generate_saas003_demo_pack.py"
    text = generator.read_text(encoding="utf-8")

    assert generator.is_file()
    assert "SAAS-003" in text
    assert "stripe_deliver_webhook" in text
    assert "session.environment.twins" not in text
