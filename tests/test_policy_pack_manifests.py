from __future__ import annotations

from pathlib import Path

from commerce_safety.io import load_yaml
from commerce_safety.policies import PolicyEngine
from commerce_safety.policy_packs import PolicyPackRegistry


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "commerce-safety-sandbox" / "scenarios"

SAAS_BILLING_POLICIES = {
    "no_success_state_after_failed_payment",
    "billing_failure_must_trigger_alert",
    "slack_permission_failure_must_not_be_silent",
    "github_check_must_match_policy_status",
}

REQUIRED_ARTIFACTS = {
    "trace.json",
    "policy_report.json",
    "state_diff.json",
    "report.md",
    "patch_hints.json",
    "run_manifest.json",
}


def test_saas_billing_v0_manifest_is_auditable_policy_pack():
    manifest = PolicyPackRegistry().get("saas_billing_v0")

    assert manifest.raw["status"] == "active"
    assert set(manifest.raw["service_twins"]) == {"stripe", "slack", "github"}
    assert set(manifest.policy_ids) == SAAS_BILLING_POLICIES
    assert {"SAAS-001", "SAAS-002"}.issubset(set(manifest.applicable_scenarios))
    assert REQUIRED_ARTIFACTS.issubset(set(manifest.required_artifacts))
    assert "policy_packs" in manifest.raw["artifact_contract"][
        "required_policy_report_fields"
    ]
    assert "environment_state" in manifest.raw["artifact_contract"][
        "required_trace_fields"
    ]
    assert any(
        "Shopify" in non_goal or "Amazon" in non_goal
        for non_goal in manifest.raw["non_goals"]
    )


def test_policy_engine_supported_packs_are_manifest_backed():
    registry = PolicyPackRegistry()
    engine = PolicyEngine(policy_pack_registry=registry)

    assert engine.supported_policy_packs == {"legacy_commerce", "saas_billing_v0"}
    assert engine.resolve_policy_packs() == ("legacy_commerce", "saas_billing_v0")


def test_declared_scenario_policy_packs_have_manifests():
    registry = PolicyPackRegistry()
    supported = set(registry.ids())

    for path in sorted(SCENARIOS.rglob("*.yaml")):
        scenario = load_yaml(path)
        declared = scenario.get("policy_packs", [])
        unknown = set(declared) - supported
        assert not unknown, f"{path} declares unknown policy packs: {unknown}"
        if scenario["id"].startswith("SAAS-"):
            assert declared == ["saas_billing_v0"]
            manifest = registry.get("saas_billing_v0")
            assert scenario["id"] in manifest.applicable_scenarios
