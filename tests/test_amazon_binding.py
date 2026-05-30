from __future__ import annotations

from pathlib import Path

from commerce_safety.platform_skins.amazon.binding import AmazonPlatformBinding
from commerce_safety.twin import CommerceTwin
from commerce_safety.io import load_yaml


def test_amazon_binding_maps_platform_ids_to_canonical_state():
    twin = CommerceTwin(
        load_yaml(Path("commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml"))
    )

    binding = AmazonPlatformBinding.from_twin(twin)

    assert binding.resolve_order_id("AMZ-3001") == ("order_3001", "amazon_order_id")
    assert binding.resolve_order_id("order_3001") == ("order_3001", "canonical_or_metadata")
    assert binding.resolve_sku("sku_stale_1") == ("sku_stale_1", "seller_sku")
    assert binding.resolve_sku("B0003001") == ("sku_stale_1", "asin")
    assert binding.resolve_order_item_id("AMZ-3001-0") == {
        "order_id": "order_3001",
        "sku": "sku_stale_1",
    }
