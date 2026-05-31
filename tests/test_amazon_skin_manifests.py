from __future__ import annotations

from commerce_safety.platform_skins.amazon.coverage import load_amazon_coverage


def test_amazon_coverage_manifest_declares_v0_surface():
    coverage = load_amazon_coverage()

    assert coverage.as_dict()["skin"] == "amazon_seller_ops"
    assert coverage.route_status("getInventorySummaries") == "stateful"
    assert coverage.route_status("getListingsItem") == "stateful"
    assert coverage.route_status("confirmShipment") == "stateful"
    assert coverage.route_status("createFeed") == "stateful"
    assert coverage.route_status("getFeed") == "stateful_with_processing_report"
    assert coverage.route_status("unknownOperation") == "stub"
    data = coverage.as_dict()
    assert data["binding"]["sellerId"]["canonical"] == "A1COMMERCESELLER"
    assert "seller_123" in data["binding"]["sellerId"]["aliases"]
    assert data["faults"]["rate_limit_429"]["retryable"] is True
    assert data["stubs"]["unsupported_notifications"] == "explicit_stub"
