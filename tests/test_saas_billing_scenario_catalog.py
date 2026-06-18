from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "scenarios" / "saas_billing_agent_safety_catalog.md"
CARDS = ROOT / "docs" / "scenarios" / "cards"
SAAS003_PACK = ROOT / "demo_pack" / "saas003_duplicate_webhook"


def test_saas_billing_scenario_catalog_routes_key_readers() -> None:
    text = CATALOG.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert CATALOG.is_file()
    assert "SaaS Billing Agent Safety Scenario Catalog" in text
    assert "Investor" in text
    assert "Design partner" in text
    assert "External agent builder" in text
    assert "Engineer or auditor" in text
    assert "Investor demo" in readme
    assert "Design partner POC" in readme
    assert "External agent builder" in readme


def test_saas_billing_catalog_explains_three_risk_templates() -> None:
    text = CATALOG.read_text(encoding="utf-8")

    for category in [
        "Billing Core",
        "Permission & Fallback Failures",
        "Stateful External-Service Edge Cases",
        "PR Check / Recovery Workflow Safety",
    ]:
        assert category in text

    for scenario_name in [
        "Failed Payment Marked Successful",
        "Billing Alert Blocked by Slack Permissions",
        "Duplicate Webhook Created Duplicate Recovery Work",
    ]:
        assert scenario_name in text


def test_scenario_cards_are_buyer_readable_and_actionable() -> None:
    required_sections = [
        "Business Risk",
        "Twins Used",
        "Seeded State",
        "Unsafe Agent Behavior",
        "Safe Agent Behavior",
        "Policy Pack",
        "Artifacts Produced",
        "Five-Minute Demo Path",
        "Customization Points",
        "Investor Explanation",
        "Design Partner Question",
        "External Agent Prompt",
    ]

    for filename in [
        "failed_payment_marked_successful.md",
        "billing_alert_blocked_by_slack_permissions.md",
        "duplicate_webhook_created_duplicate_recovery_work.md",
    ]:
        text = (CARDS / filename).read_text(encoding="utf-8")
        for section in required_sections:
            assert section in text, f"{filename} missing {section}"
        assert "saas_billing_v0" in text
        assert "Stripe" in text
        assert "Slack" in text
        assert "GitHub" in text


def test_saas003_demo_pack_has_card_and_external_agent_prompt() -> None:
    card = (SAAS003_PACK / "scenario_card.md").read_text(encoding="utf-8")
    prompt = (SAAS003_PACK / "external_agent_prompt.md").read_text(
        encoding="utf-8"
    )
    readme = (SAAS003_PACK / "README.md").read_text(encoding="utf-8")

    assert "Scenario Card: Duplicate Webhook Created Duplicate Recovery Work" in card
    assert "One Stripe event created duplicate recovery work." in card
    assert "external_agent_prompt.md" in readme
    assert "scenario_card.md" in readme

    for tool_name in [
        "sandbox.start_session",
        "sandbox.get_task",
        "stripe.deliver_webhook",
        "slack.post_message",
        "github.create_check_run",
        "sandbox.complete_session",
        "sandbox.get_policy_report",
        "sandbox.get_patch_hints",
    ]:
        assert tool_name in prompt

    assert "session.environment.twins" in prompt
