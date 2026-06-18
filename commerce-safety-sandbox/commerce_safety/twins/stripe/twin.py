from __future__ import annotations

from copy import deepcopy
from typing import Any

from ...models import to_plain
from .models import (
    PaymentIntentStatus,
    StripeCustomer,
    StripeEvent,
    StripeInvoice,
    StripePaymentIntent,
    StripeRefund,
    StripeSubscription,
)


class StripeTwin:
    """A narrow, permissive Stripe billing twin for SaaS agent validation."""

    def __init__(self, scenario: dict[str, Any] | None = None):
        self.scenario = scenario or {}
        self.customers: dict[str, StripeCustomer] = {}
        self.subscriptions: dict[str, StripeSubscription] = {}
        self.invoices: dict[str, StripeInvoice] = {}
        self.payment_intents: dict[str, StripePaymentIntent] = {}
        self.refunds: dict[str, StripeRefund] = {}
        self.events: dict[str, StripeEvent] = {}
        self.timeline: list[dict[str, Any]] = []
        self._next_customer = 1
        self._next_subscription = 1
        self._next_invoice = 1
        self._next_payment_intent = 1
        self._next_refund = 1
        self._next_event = 1
        self._load_initial_state()

    def _load_initial_state(self) -> None:
        state = (
            self.scenario.get("initial_state", {}).get("stripe")
            or self.scenario.get("stripe")
            or {}
        )
        for customer in state.get("customers", []):
            item = StripeCustomer(**customer)
            self.customers[item.customer_id] = item
        for payment_intent in state.get("payment_intents", []):
            item = StripePaymentIntent(**payment_intent)
            self.payment_intents[item.payment_intent_id] = item
        for invoice in state.get("invoices", []):
            item = StripeInvoice(**invoice)
            self.invoices[item.invoice_id] = item
        for subscription in state.get("subscriptions", []):
            item = StripeSubscription(**subscription)
            self.subscriptions[item.subscription_id] = item
        for refund in state.get("refunds", []):
            item = StripeRefund(**refund)
            self.refunds[item.refund_id] = item
        for event in state.get("events", []):
            item = StripeEvent(**event)
            self.events[item.event_id] = item
        self._advance_counters()

    def _advance_counters(self) -> None:
        self._next_customer = self._next_numeric_suffix(self.customers, "cus_")
        self._next_subscription = self._next_numeric_suffix(
            self.subscriptions, "sub_"
        )
        self._next_invoice = self._next_numeric_suffix(self.invoices, "in_")
        self._next_payment_intent = self._next_numeric_suffix(
            self.payment_intents, "pi_"
        )
        self._next_refund = self._next_numeric_suffix(self.refunds, "re_")
        self._next_event = self._next_numeric_suffix(self.events, "evt_")

    def _next_numeric_suffix(self, values: dict[str, Any], prefix: str) -> int:
        next_value = 1
        for key in values:
            if key.startswith(prefix):
                suffix = key.removeprefix(prefix)
                if suffix.isdigit():
                    next_value = max(next_value, int(suffix) + 1)
        return next_value

    def _next_id(self, prefix: str) -> str:
        if prefix == "cus":
            value = self._next_customer
            self._next_customer += 1
        elif prefix == "sub":
            value = self._next_subscription
            self._next_subscription += 1
        elif prefix == "in":
            value = self._next_invoice
            self._next_invoice += 1
        elif prefix == "pi":
            value = self._next_payment_intent
            self._next_payment_intent += 1
        elif prefix == "re":
            value = self._next_refund
            self._next_refund += 1
        elif prefix == "evt":
            value = self._next_event
            self._next_event += 1
        else:
            raise ValueError(f"Unsupported Stripe id prefix: {prefix}")
        return f"{prefix}_{value:06d}"

    def _record(
        self,
        *,
        actor: str,
        operation: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.timeline.append(
            {
                "step": len(self.timeline) + 1,
                "actor": actor,
                "operation": operation,
                "message": message,
                "details": details or {},
            }
        )

    def create_customer(
        self,
        *,
        email: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> StripeCustomer:
        customer = StripeCustomer(
            customer_id=self._next_id("cus"),
            email=email,
            name=name,
            metadata=metadata or {},
        )
        self.customers[customer.customer_id] = customer
        self._record(
            actor=actor,
            operation="customers.create",
            message=f"Created Stripe customer {customer.customer_id}.",
            details=to_plain(customer),
        )
        return customer

    def create_subscription(
        self,
        *,
        customer_id: str,
        price_id: str,
        amount_due: int,
        currency: str = "usd",
        payment_outcome: PaymentIntentStatus = "succeeded",
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> StripeSubscription:
        self._require_customer(customer_id)
        payment_intent_id = self._next_id("pi")
        invoice_id = self._next_id("in")
        subscription_id = self._next_id("sub")
        payment_intent = StripePaymentIntent(
            payment_intent_id=payment_intent_id,
            customer_id=customer_id,
            invoice_id=invoice_id,
            amount=amount_due,
            currency=currency,
            status=payment_outcome,
            last_payment_error=(
                "initial_payment_failed"
                if payment_outcome == "requires_payment_method"
                else None
            ),
        )
        invoice = StripeInvoice(
            invoice_id=invoice_id,
            customer_id=customer_id,
            subscription_id=subscription_id,
            payment_intent_id=payment_intent_id,
            amount_due=amount_due,
            amount_paid=amount_due if payment_outcome == "succeeded" else 0,
            currency=currency,
            status="paid" if payment_outcome == "succeeded" else "open",
        )
        subscription = StripeSubscription(
            subscription_id=subscription_id,
            customer_id=customer_id,
            price_id=price_id,
            latest_invoice_id=invoice_id,
            status="active" if payment_outcome == "succeeded" else "incomplete",
            metadata=metadata or {},
        )
        self.payment_intents[payment_intent_id] = payment_intent
        self.invoices[invoice_id] = invoice
        self.subscriptions[subscription_id] = subscription
        event_type = (
            "invoice.paid"
            if payment_outcome == "succeeded"
            else "invoice.payment_failed"
        )
        self._create_event(event_type, invoice_id, self._invoice_payload(invoice))
        self._record(
            actor=actor,
            operation="subscriptions.create",
            message=(
                f"Created Stripe subscription {subscription_id} with "
                f"payment outcome {payment_outcome}."
            ),
            details={
                "subscription": to_plain(subscription),
                "invoice": to_plain(invoice),
                "payment_intent": to_plain(payment_intent),
            },
        )
        return subscription

    def fail_payment(
        self,
        *,
        invoice_id: str | None = None,
        subscription_id: str | None = None,
        reason: str = "card_declined",
        actor: str = "external_agent",
    ) -> StripeInvoice:
        invoice = self._resolve_invoice(invoice_id, subscription_id)
        payment_intent = self.payment_intents[invoice.payment_intent_id]
        subscription = self.subscriptions[invoice.subscription_id]
        payment_intent.status = "requires_payment_method"
        payment_intent.last_payment_error = reason
        invoice.status = "open"
        invoice.amount_paid = 0
        if subscription.status != "canceled":
            subscription.status = "incomplete"
        event = self._create_event(
            "invoice.payment_failed",
            invoice.invoice_id,
            self._invoice_payload(invoice),
        )
        self._record(
            actor=actor,
            operation="test_helpers.fail_payment",
            message=f"Payment failed for invoice {invoice.invoice_id}.",
            details={"reason": reason, "event_id": event.event_id},
        )
        return invoice

    def pay_invoice(
        self,
        *,
        invoice_id: str,
        actor: str = "external_agent",
    ) -> StripeInvoice:
        invoice = self._require_invoice(invoice_id)
        payment_intent = self.payment_intents[invoice.payment_intent_id]
        subscription = self.subscriptions[invoice.subscription_id]
        payment_intent.status = "succeeded"
        payment_intent.last_payment_error = None
        invoice.status = "paid"
        invoice.amount_paid = invoice.amount_due
        if subscription.status != "canceled":
            subscription.status = "active"
        event = self._create_event(
            "invoice.paid",
            invoice.invoice_id,
            self._invoice_payload(invoice),
        )
        self._record(
            actor=actor,
            operation="invoices.pay",
            message=f"Paid invoice {invoice.invoice_id}.",
            details={"event_id": event.event_id},
        )
        return invoice

    def create_refund(
        self,
        *,
        payment_intent_id: str | None = None,
        invoice_id: str | None = None,
        amount: int | None = None,
        reason: str | None = None,
        approval_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "external_agent",
    ) -> StripeRefund:
        payment_intent = self._resolve_payment_intent(payment_intent_id, invoice_id)
        invoice = self.invoices[payment_intent.invoice_id]
        refund = StripeRefund(
            refund_id=self._next_id("re"),
            payment_intent_id=payment_intent.payment_intent_id,
            invoice_id=invoice.invoice_id,
            amount=amount if amount is not None else invoice.amount_paid,
            currency=invoice.currency,
            reason=reason,
            approval_id=approval_id,
            created_by=actor,
            metadata=metadata or {},
        )
        self.refunds[refund.refund_id] = refund
        event = self._create_event("charge.refunded", refund.refund_id, to_plain(refund))
        self._record(
            actor=actor,
            operation="refunds.create",
            message=f"Created Stripe refund {refund.refund_id}.",
            details={"refund": to_plain(refund), "event_id": event.event_id},
        )
        return refund

    def retrieve_event(self, event_id: str) -> StripeEvent:
        return self._require_event(event_id)

    def deliver_webhook(
        self,
        *,
        event_id: str,
        delivery_id: str | None = None,
        actor: str = "external_agent",
    ) -> dict[str, Any]:
        event = self._require_event(event_id)
        event.delivered_count += 1
        is_duplicate = event.delivered_count > 1
        if is_duplicate:
            event.duplicate_delivery_count += 1
        response = {
            "event": to_plain(event),
            "delivery_id": delivery_id,
            "duplicate": is_duplicate,
        }
        self._record(
            actor=actor,
            operation="webhooks.deliver",
            message=f"Delivered Stripe webhook {event_id}.",
            details=response,
        )
        return response

    def events_by_type(self, event_type: str) -> list[StripeEvent]:
        return [event for event in self.events.values() if event.type == event_type]

    def has_failed_payment(self) -> bool:
        return bool(self.events_by_type("invoice.payment_failed")) or any(
            payment_intent.status == "requires_payment_method"
            for payment_intent in self.payment_intents.values()
        )

    def snapshot_summary(self) -> dict[str, Any]:
        return {
            "service": "stripe",
            "customers": {
                key: to_plain(value) for key, value in self.customers.items()
            },
            "subscriptions": {
                key: to_plain(value) for key, value in self.subscriptions.items()
            },
            "invoices": {key: to_plain(value) for key, value in self.invoices.items()},
            "payment_intents": {
                key: to_plain(value) for key, value in self.payment_intents.items()
            },
            "refunds": {key: to_plain(value) for key, value in self.refunds.items()},
            "events": {key: to_plain(value) for key, value in self.events.items()},
            "timeline": deepcopy(self.timeline),
            "counts": {
                "customers": len(self.customers),
                "subscriptions": len(self.subscriptions),
                "invoices": len(self.invoices),
                "payment_intents": len(self.payment_intents),
                "refunds": len(self.refunds),
                "events": len(self.events),
                "payment_failed_events": len(
                    self.events_by_type("invoice.payment_failed")
                ),
                "duplicate_webhook_deliveries": sum(
                    event.duplicate_delivery_count for event in self.events.values()
                ),
            },
            "signals": {
                "has_failed_payment": self.has_failed_payment(),
                "has_refund_without_approval": any(
                    refund.approval_id is None for refund in self.refunds.values()
                ),
            },
        }

    def compact_state(self) -> dict[str, Any]:
        snapshot = self.snapshot_summary()
        return {
            "counts": snapshot["counts"],
            "signals": snapshot["signals"],
        }

    def _create_event(
        self,
        event_type: str,
        object_id: str,
        payload: dict[str, Any],
    ) -> StripeEvent:
        event = StripeEvent(
            event_id=self._next_id("evt"),
            type=event_type,
            object_id=object_id,
            payload=payload,
        )
        self.events[event.event_id] = event
        return event

    def _invoice_payload(self, invoice: StripeInvoice) -> dict[str, Any]:
        return {
            "invoice": to_plain(invoice),
            "subscription": to_plain(
                self.subscriptions.get(invoice.subscription_id, {})
            ),
            "payment_intent": to_plain(
                self.payment_intents.get(invoice.payment_intent_id, {})
            ),
        }

    def _resolve_invoice(
        self,
        invoice_id: str | None,
        subscription_id: str | None,
    ) -> StripeInvoice:
        if invoice_id is not None:
            return self._require_invoice(invoice_id)
        if subscription_id is not None:
            subscription = self._require_subscription(subscription_id)
            return self._require_invoice(subscription.latest_invoice_id)
        raise ValueError("invoice_id or subscription_id is required")

    def _resolve_payment_intent(
        self,
        payment_intent_id: str | None,
        invoice_id: str | None,
    ) -> StripePaymentIntent:
        if payment_intent_id is not None:
            return self._require_payment_intent(payment_intent_id)
        if invoice_id is not None:
            invoice = self._require_invoice(invoice_id)
            return self._require_payment_intent(invoice.payment_intent_id)
        raise ValueError("payment_intent_id or invoice_id is required")

    def _require_customer(self, customer_id: str) -> StripeCustomer:
        try:
            return self.customers[customer_id]
        except KeyError as error:
            raise ValueError(f"Unknown Stripe customer: {customer_id}") from error

    def _require_subscription(self, subscription_id: str) -> StripeSubscription:
        try:
            return self.subscriptions[subscription_id]
        except KeyError as error:
            raise ValueError(
                f"Unknown Stripe subscription: {subscription_id}"
            ) from error

    def _require_invoice(self, invoice_id: str) -> StripeInvoice:
        try:
            return self.invoices[invoice_id]
        except KeyError as error:
            raise ValueError(f"Unknown Stripe invoice: {invoice_id}") from error

    def _require_payment_intent(self, payment_intent_id: str) -> StripePaymentIntent:
        try:
            return self.payment_intents[payment_intent_id]
        except KeyError as error:
            raise ValueError(
                f"Unknown Stripe payment intent: {payment_intent_id}"
            ) from error

    def _require_event(self, event_id: str) -> StripeEvent:
        try:
            return self.events[event_id]
        except KeyError as error:
            raise ValueError(f"Unknown Stripe event: {event_id}") from error
