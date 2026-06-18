from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AmazonPlatformBinding:
    order_ids: dict[str, str] = field(default_factory=dict)
    skus: dict[str, str] = field(default_factory=dict)
    order_items: dict[str, dict[str, str]] = field(default_factory=dict)
    marketplace_id: str = "ATVPDKIKX0DER"
    seller_id: str = "A1COMMERCESELLER"
    seller_aliases: tuple[str, ...] = ("seller_123", "A1COMMERCESELLER")
    marketplace_ids: tuple[str, ...] = ("ATVPDKIKX0DER",)

    @classmethod
    def from_twin(cls, twin: Any) -> "AmazonPlatformBinding":
        order_ids: dict[str, str] = {}
        skus: dict[str, str] = {}
        order_items: dict[str, dict[str, str]] = {}

        for order in twin.orders.values():
            canonical_order_id = order.order_id
            numeric_id = _last_digit_run(canonical_order_id) or canonical_order_id
            amazon_order_id = f"AMZ-{numeric_id}"
            for key in {canonical_order_id, amazon_order_id, numeric_id}:
                order_ids[key] = canonical_order_id

            for index, line_item in enumerate(order.line_items):
                sku_numeric_id = _last_digit_run(line_item.sku) or numeric_id
                asin = _asin_for(sku_numeric_id)
                fnsku = _fnsku_for(sku_numeric_id)
                order_asin = _asin_for(numeric_id)
                order_fnsku = _fnsku_for(numeric_id)
                seller_sku = _seller_sku_for(line_item.sku, sku_numeric_id)
                for key in {
                    line_item.sku,
                    seller_sku,
                    asin,
                    fnsku,
                    order_asin,
                    order_fnsku,
                }:
                    skus[key] = line_item.sku
                order_item_id = f"{amazon_order_id}-{index}"
                order_items[order_item_id] = {
                    "order_id": canonical_order_id,
                    "sku": line_item.sku,
                    "seller_sku": seller_sku,
                    "asin": order_asin,
                    "fnsku": order_fnsku,
                }

        return cls(order_ids=order_ids, skus=skus, order_items=order_items)

    def resolve_order_id(self, platform_id: Any) -> tuple[str | None, str | None]:
        if platform_id is None:
            return None, None
        key = str(platform_id)
        if key in self.order_ids:
            return self.order_ids[key], _order_binding_source_for(key)
        return None, None

    def resolve_sku(self, platform_sku: Any) -> tuple[str | None, str | None]:
        if platform_sku is None:
            return None, None
        key = str(platform_sku)
        if key in self.skus:
            return self.skus[key], _sku_binding_source_for(key)
        return None, None

    def resolve_order_item_id(self, order_item_id: Any) -> dict[str, str] | None:
        if order_item_id is None:
            return None
        value = self.order_items.get(str(order_item_id))
        return dict(value) if value else None

    def amazon_order_id_for(self, canonical_order_id: str) -> str:
        numeric_id = _last_digit_run(canonical_order_id) or canonical_order_id
        return f"AMZ-{numeric_id}"

    def is_known_seller(self, seller_id: str | None) -> bool:
        return seller_id is None or seller_id in self.seller_aliases

    def marketplace_ids_for_sku(self, sku: str) -> list[str]:
        return list(self.marketplace_ids)

    def seller_sku_for(self, sku: str) -> str:
        numeric_id = _last_digit_run(sku) or "1"
        return _seller_sku_for(sku, numeric_id)

    def asin_for_sku(self, sku: str) -> str:
        numeric_id = _last_digit_run(sku) or _last_digit_run(self.skus.get(sku, "")) or "1"
        return _asin_for(numeric_id)

    def fnsku_for_sku(self, sku: str) -> str:
        numeric_id = _last_digit_run(sku) or _last_digit_run(self.skus.get(sku, "")) or "1"
        return _fnsku_for(numeric_id)

    def as_dict(self) -> dict[str, Any]:
        return {
            "order_ids": dict(self.order_ids),
            "skus": dict(self.skus),
            "order_items": {
                key: dict(value) for key, value in self.order_items.items()
            },
            "marketplace_id": self.marketplace_id,
            "marketplace_ids": list(self.marketplace_ids),
            "seller_id": self.seller_id,
            "seller_aliases": list(self.seller_aliases),
        }


def _last_digit_run(value: str) -> str | None:
    match = re.search(r"(\d+)$", value)
    return match.group(1) if match else None


def _asin_for(numeric_id: str) -> str:
    return f"B{int(numeric_id):07d}" if numeric_id.isdigit() else f"B{numeric_id}"


def _fnsku_for(numeric_id: str) -> str:
    return f"X{int(numeric_id):07d}" if numeric_id.isdigit() else f"X{numeric_id}"


def _seller_sku_for(canonical_sku: str, numeric_id: str) -> str:
    if canonical_sku.startswith("sku_"):
        return f"SELLER-{numeric_id.zfill(4)}"
    return canonical_sku


def _order_binding_source_for(key: str) -> str:
    if key.startswith("AMZ-"):
        return "amazon_order_id"
    if key.isdigit():
        return "amazon_numeric_order_id"
    return "canonical_or_metadata"


def _sku_binding_source_for(key: str) -> str:
    if key.startswith("B"):
        return "asin"
    if key.startswith("X"):
        return "fnsku"
    return "seller_sku"
