from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class LineItem:
    sku: str
    quantity: int


@dataclass
class Order:
    order_id: str
    payment_status: str
    order_status: str
    line_items: list[LineItem]
    fulfillment_status: str | None = None
    shipment_status: str | None = None
    refund_status: str | None = None
    captured_amount: float | None = None
    cancel_requested: bool = False


@dataclass
class Inventory:
    sku: str
    on_hand: int
    reserved: int = 0
    available: int | None = None
    committed: int = 0
    true_available: int | None = None
    source_version: str | None = None
    last_synced_at: str | None = None


@dataclass
class Reservation:
    reservation_id: str
    order_id: str
    sku: str
    quantity: int
    created_by: str
    webhook_id: str | None = None


@dataclass
class Fulfillment:
    fulfillment_id: str
    order_id: str
    sku: str
    quantity: int
    created_by: str
    webhook_id: str | None = None
    idempotency_key: str | None = None
    request_id: str | None = None
    source_event_id: str | None = None


@dataclass
class FulfillmentPromise:
    promise_id: str
    order_id: str
    sku: str
    quantity: int
    created_by: str
    source_event_id: str | None = None
    based_on_available: int | None = None
    true_available_at_commit: int | None = None
    snapshot_version: str | None = None
    last_synced_at: str | None = None
    reservation_id: str | None = None


@dataclass
class Refund:
    refund_id: str
    order_id: str
    amount: float
    reason: str
    created_by: str
    source_event_id: str | None = None
    approval_id: str | None = None
    approved_by: str | None = None
    order_fulfillment_status_at_issue: str | None = None
    shipment_status_at_issue: str | None = None


@dataclass
class ApprovalRequest:
    approval_id: str
    order_id: str
    amount: float
    reason: str
    created_by: str
    source_event_id: str | None = None
    status: str = "pending"
    required_policy: str | None = None


@dataclass
class WarehouseJob:
    warehouse_job_id: str
    order_id: str
    sku: str
    quantity: int
    status: str
    cancellation_requested: bool = False
    hold_status: str | None = None
    continued_after_cancel: bool = False


@dataclass
class InventoryRelease:
    release_id: str
    order_id: str
    sku: str
    quantity: int
    created_by: str
    source_event_id: str | None = None
    warehouse_status_at_release: str | None = None
    order_status_at_release: str | None = None


@dataclass
class WorkflowHold:
    hold_id: str
    order_id: str
    sku: str | None
    reason: str
    created_by: str
    source_event_id: str | None = None
    warehouse_status_at_hold: str | None = None


@dataclass
class WarehouseCancellationRequest:
    cancellation_request_id: str
    order_id: str
    warehouse_job_id: str
    created_by: str
    source_event_id: str | None = None
    status: str = "requested"
    warehouse_status_at_request: str | None = None


@dataclass
class Event:
    step: int
    actor: str
    event: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyFinding:
    policy_id: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    status: Literal["passed", "failed"]
    evidence: dict[str, Any]
    business_impact: str
    recommendation: str


def to_plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    return value
