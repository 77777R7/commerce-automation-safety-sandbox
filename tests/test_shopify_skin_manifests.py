from __future__ import annotations

from commerce_safety.platform_skins.shopify.coverage import load_shopify_coverage


def test_shopify_skin_v0_coverage_is_explicit_and_narrow():
    coverage = load_shopify_coverage()

    assert coverage.skin == "shopify_like"
    assert coverage.stage == "Stage 12+"
    assert coverage.is_supported_webhook("orders/paid")
    assert coverage.is_supported_webhook("orders/cancelled")
    assert not coverage.is_supported_webhook("refunds/create")
    assert coverage.mutation_status("fulfillmentCreate") == "stateful"
    assert coverage.mutation_status("inventoryAdjustQuantities") == "stateful"
    assert coverage.mutation_status("refundCreate") == "stateful"
    assert coverage.mutation_status("refundApprovalRequestCreate") == "stateful"
    assert coverage.mutation_status("orderCancel") == "stateful"
    assert coverage.mutation_status("fulfillmentOrderHold") == "stateful"
    assert coverage.mutation_status("fulfillmentOrderSubmitCancellationRequest") == "stateful"
    assert coverage.mutation_status("productCreate") == "unsupported"
    assert coverage.route_status("inventoryLevels") == "stateful"
    assert coverage.route_status("inventoryAdjust") == "stateful"
    assert coverage.action_status("promise_fulfillment") == "stateful"
    assert coverage.action_status("route_manual_review") == "stateful"
    assert coverage.supported_scenarios == [
        "duplicate_webhook",
        "SCN-002",
        "SCN-003",
        "SCN-004",
        "SCN-005",
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
    assert binding["webhooks"]["orders/cancelled"]["commerce_event"] == (
        "cancel_request_received"
    )
    assert binding["mutations"]["refundCreate"]["commerce_action"] == (
        "commerce.create_refund"
    )
