from __future__ import annotations

from commerce_safety.twins.stripe import StripeTwin


def test_stripe_twin_failed_payment_maps_billing_state():
    twin = StripeTwin()
    customer = twin.create_customer(email="buyer@example.test")
    subscription = twin.create_subscription(
        customer_id=customer.customer_id,
        price_id="price_pro_monthly",
        amount_due=2900,
    )

    invoice = twin.fail_payment(
        subscription_id=subscription.subscription_id,
        reason="card_declined",
    )
    payment_intent = twin.payment_intents[invoice.payment_intent_id]
    subscription = twin.subscriptions[subscription.subscription_id]

    assert subscription.status == "incomplete"
    assert invoice.status == "open"
    assert invoice.amount_paid == 0
    assert payment_intent.status == "requires_payment_method"
    assert payment_intent.last_payment_error == "card_declined"
    assert twin.has_failed_payment() is True

    snapshot = twin.snapshot_summary()
    assert snapshot["counts"]["payment_failed_events"] == 1
    assert snapshot["signals"]["has_failed_payment"] is True


def test_stripe_twin_pay_invoice_recovers_subscription_state():
    twin = StripeTwin()
    customer = twin.create_customer()
    subscription = twin.create_subscription(
        customer_id=customer.customer_id,
        price_id="price_team",
        amount_due=4900,
        payment_outcome="requires_payment_method",
    )

    paid_invoice = twin.pay_invoice(invoice_id=subscription.latest_invoice_id)
    payment_intent = twin.payment_intents[paid_invoice.payment_intent_id]

    assert paid_invoice.status == "paid"
    assert paid_invoice.amount_paid == 4900
    assert payment_intent.status == "succeeded"
    assert twin.subscriptions[subscription.subscription_id].status == "active"
    assert twin.events_by_type("invoice.paid")


def test_stripe_twin_duplicate_webhook_delivery_is_tracked():
    twin = StripeTwin()
    customer = twin.create_customer()
    subscription = twin.create_subscription(
        customer_id=customer.customer_id,
        price_id="price_pro",
        amount_due=1900,
        payment_outcome="requires_payment_method",
    )
    failed_event = twin.events_by_type("invoice.payment_failed")[0]

    first = twin.deliver_webhook(event_id=failed_event.event_id, delivery_id="deliv_1")
    second = twin.deliver_webhook(event_id=failed_event.event_id, delivery_id="deliv_2")

    assert subscription.status == "incomplete"
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert twin.retrieve_event(failed_event.event_id).delivered_count == 2
    assert (
        twin.snapshot_summary()["counts"]["duplicate_webhook_deliveries"] == 1
    )


def test_stripe_twin_is_permissive_for_refund_without_approval():
    twin = StripeTwin()
    customer = twin.create_customer()
    subscription = twin.create_subscription(
        customer_id=customer.customer_id,
        price_id="price_enterprise",
        amount_due=12000,
    )

    refund = twin.create_refund(
        invoice_id=subscription.latest_invoice_id,
        amount=12000,
        reason="customer_request",
        approval_id=None,
    )

    assert refund.status == "succeeded"
    assert refund.approval_id is None
    assert twin.snapshot_summary()["signals"]["has_refund_without_approval"] is True
