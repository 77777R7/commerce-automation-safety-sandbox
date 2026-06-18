from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SubscriptionStatus = Literal["trialing", "active", "incomplete", "past_due", "canceled"]
InvoiceStatus = Literal["draft", "open", "paid", "void", "uncollectible"]
PaymentIntentStatus = Literal[
    "requires_payment_method",
    "requires_action",
    "processing",
    "succeeded",
]
RefundStatus = Literal["pending", "succeeded", "failed", "canceled"]


@dataclass
class StripeCustomer:
    customer_id: str
    email: str | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StripePaymentIntent:
    payment_intent_id: str
    customer_id: str
    invoice_id: str
    amount: int
    currency: str = "usd"
    status: PaymentIntentStatus = "succeeded"
    last_payment_error: str | None = None


@dataclass
class StripeInvoice:
    invoice_id: str
    customer_id: str
    subscription_id: str
    payment_intent_id: str
    amount_due: int
    amount_paid: int = 0
    currency: str = "usd"
    status: InvoiceStatus = "open"


@dataclass
class StripeSubscription:
    subscription_id: str
    customer_id: str
    price_id: str
    latest_invoice_id: str
    status: SubscriptionStatus = "active"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StripeRefund:
    refund_id: str
    payment_intent_id: str
    invoice_id: str
    amount: int
    currency: str = "usd"
    status: RefundStatus = "succeeded"
    reason: str | None = None
    approval_id: str | None = None
    created_by: str = "external_agent"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StripeEvent:
    event_id: str
    type: str
    object_id: str
    payload: dict[str, Any]
    delivered_count: int = 0
    duplicate_delivery_count: int = 0
