from __future__ import annotations

from pathlib import Path

from commerce_safety.io import load_yaml
from commerce_safety.policies import PolicyEngine, findings_to_plain
from commerce_safety.runners import BadRunner
from commerce_safety.twin import CommerceTwin


ROOT = Path(__file__).resolve().parents[1]


def test_duplicate_webhook_bad_runner_triggers_expected_policies() -> None:
    scenario = load_yaml(ROOT / "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml")
    twin = CommerceTwin(scenario)
    runner = BadRunner()

    for event in scenario["events"]:
        twin.receive_webhook(event)
        runner.handle_webhook(twin, event)

    findings = findings_to_plain(PolicyEngine().evaluate(twin))
    policy_ids = {finding["policy_id"] for finding in findings}

    assert "no_duplicate_fulfillment" in policy_ids
    assert "webhook_dedup_required" in policy_ids

    webhook = next(
        finding
        for finding in findings
        if finding["policy_id"] == "webhook_dedup_required"
    )
    side_effect_types = {
        item["type"]
        for item in webhook["evidence"]["side_effects_from_same_webhook"]
    }

    assert {"reservation", "fulfillment"}.issubset(side_effect_types)
