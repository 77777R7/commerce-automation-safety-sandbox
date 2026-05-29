from __future__ import annotations

from commerce_safety.offline_audit import (
    evaluate_offline_policies,
    normalize_status,
    parse_float,
    parse_int,
    reconstruct_state,
    redact_identifier,
)


def test_redact_identifier_is_deterministic_and_hides_raw_value() -> None:
    first = redact_identifier("customer@example.com")
    second = redact_identifier("customer@example.com")

    assert first == second
    assert first.startswith("buyer_")
    assert "customer" not in first
    assert "example" not in first


def test_status_and_number_parsing_helpers() -> None:
    assert normalize_status("Carrier Scanned") == "carrier_scanned"
    assert normalize_status("cancel-requested") == "cancel_requested"
    assert parse_int("2.0") == 2
    assert parse_int("bad", default=7) == 7
    assert parse_float("12.50") == 12.5
    assert parse_float("", default=3.5) == 3.5


def test_evaluate_offline_policies_detects_duplicate_fulfillment() -> None:
    state = reconstruct_state(
        orders=[
            {
                "order_id": "order_1",
                "buyer_id": "buyer_1",
                "sku": "sku_1",
                "quantity": "1",
                "payment_status": "paid",
                "order_status": "open",
                "created_at": "2026-05-01T00:00:00Z",
            }
        ],
        inventory=[
            {
                "sku": "sku_1",
                "on_hand": "5",
                "reserved": "1",
                "warehouse": "warehouse_a",
            }
        ],
        fulfillments=[
            {
                "order_id": "order_1",
                "sku": "sku_1",
                "quantity": "2",
                "fulfillment_status": "fulfilled",
                "tracking_number": "TRACK1",
                "warehouse_status": "shipped",
            }
        ],
        refunds=[],
    )

    policy_ids = {finding["policy_id"] for finding in evaluate_offline_policies(state)}

    assert "offline_duplicate_fulfillment" in policy_ids
