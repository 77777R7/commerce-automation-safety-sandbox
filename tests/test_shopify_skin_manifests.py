from __future__ import annotations

from commerce_safety.platform_skins.shopify.coverage import load_shopify_coverage


def test_shopify_skin_v0_coverage_is_explicit_and_narrow():
    coverage = load_shopify_coverage()

    assert coverage.skin == "shopify_like"
    assert coverage.stage == "Stage 12"
    assert coverage.is_supported_webhook("orders/paid")
    assert not coverage.is_supported_webhook("refunds/create")
    assert coverage.mutation_status("fulfillmentCreate") == "stateful"
    assert coverage.mutation_status("refundCreate") == "unsupported"
    assert coverage.mutation_status("productCreate") == "unsupported"
    assert coverage.supported_scenarios == [
        "duplicate_webhook",
        "SCN-002",
    ]


def test_shopify_skin_v0_binding_keeps_policy_out_of_adapter():
    coverage = load_shopify_coverage()
    binding = coverage.binding

    assert binding["principle"] == "permissive_twin_policy_check"
    assert binding["mutations"]["fulfillmentCreate"]["commerce_action"] == (
        "commerce.create_fulfillment"
    )
    assert binding["mutations"]["fulfillmentCreate"]["policy_layer"] == (
        "commerce_safety.PolicyEngine"
    )
    assert binding["webhooks"]["orders/paid"]["commerce_event"] == "webhook_received"
