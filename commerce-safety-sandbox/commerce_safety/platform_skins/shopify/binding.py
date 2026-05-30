from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ShopifyPlatformBinding:
    order_ids: dict[str, str] = field(default_factory=dict)
    line_items: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_twin(cls, twin: Any) -> "ShopifyPlatformBinding":
        order_ids: dict[str, str] = {}
        line_items: dict[str, dict[str, str]] = {}
        for order in twin.orders.values():
            canonical_order_id = order.order_id
            order_keys = {canonical_order_id}
            numeric_id = _last_digit_run(canonical_order_id)
            if numeric_id:
                order_keys.update(
                    {
                        numeric_id,
                        f"gid://shopify/Order/{numeric_id}",
                        f"gid://shopify/FulfillmentOrder/{numeric_id}",
                    }
                )
            order_keys.add(f"gid://shopify/FulfillmentOrder/{canonical_order_id}")
            for key in order_keys:
                order_ids[key] = canonical_order_id

            for index, line_item in enumerate(order.line_items):
                line_record = {"order_id": canonical_order_id, "sku": line_item.sku}
                item_keys = {
                    line_item.sku,
                    f"gid://shopify/FulfillmentOrderLineItem/{canonical_order_id}-{index}",
                    f"gid://shopify/LineItem/{canonical_order_id}-{index}",
                }
                if numeric_id:
                    item_keys.update(
                        {
                            f"gid://shopify/FulfillmentOrderLineItem/{numeric_id}-{index}",
                            f"gid://shopify/LineItem/{numeric_id}-{index}",
                        }
                    )
                for key in item_keys:
                    line_items[key] = dict(line_record)
        return cls(order_ids=order_ids, line_items=line_items)

    def resolve_order_id(self, *platform_ids: Any) -> tuple[str | None, str | None]:
        for platform_id in platform_ids:
            if platform_id is None:
                continue
            key = str(platform_id)
            if key in self.order_ids:
                return self.order_ids[key], _binding_source_for(key)
        return None, None

    def resolve_line_item(
        self,
        *platform_ids: Any,
    ) -> dict[str, str] | None:
        for platform_id in platform_ids:
            if platform_id is None:
                continue
            key = str(platform_id)
            if key in self.line_items:
                return self.line_items[key]
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "order_ids": dict(self.order_ids),
            "line_items": {key: dict(value) for key, value in self.line_items.items()},
        }


def _last_digit_run(value: str) -> str | None:
    match = re.search(r"(\d+)$", value)
    return match.group(1) if match else None


def _binding_source_for(key: str) -> str:
    if key.startswith("gid://shopify/"):
        return "shopify_gid"
    if key.isdigit():
        return "shopify_order_id"
    return "canonical_or_metadata"
