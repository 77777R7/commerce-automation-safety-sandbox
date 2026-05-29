from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import (
    ApprovalRequest,
    Event,
    Fulfillment,
    FulfillmentPromise,
    Inventory,
    InventoryRelease,
    LineItem,
    Order,
    Reservation,
    Refund,
    WarehouseCancellationRequest,
    WarehouseJob,
    WorkflowHold,
    to_plain,
)


class TimeoutAfterCommit(Exception):
    def __init__(self, fulfillment: Fulfillment):
        super().__init__("timeout_after_commit")
        self.fulfillment = fulfillment


class CommerceTwin:
    """A permissive commerce twin.

    The twin intentionally allows unsafe mutations. It records the state and
    trace first; policy evaluation happens after the run.
    """

    def __init__(self, scenario: dict[str, Any]):
        self.scenario = scenario
        state = scenario["initial_state"]
        order_data = state["order"]
        self.orders: dict[str, Order] = {
            order_data["order_id"]: Order(
                order_id=order_data["order_id"],
                payment_status=order_data["payment_status"],
                order_status=order_data["order_status"],
                line_items=[
                    LineItem(sku=item["sku"], quantity=int(item["quantity"]))
                    for item in order_data["line_items"]
                ],
                fulfillment_status=order_data.get("fulfillment_status"),
                shipment_status=order_data.get("shipment_status"),
                refund_status=order_data.get("refund_status"),
                captured_amount=(
                    float(order_data["captured_amount"])
                    if "captured_amount" in order_data
                    else None
                ),
                cancel_requested=bool(order_data.get("cancel_requested", False)),
            )
        }
        self.inventory: dict[str, Inventory] = {
            item["sku"]: Inventory(
                sku=item["sku"],
                on_hand=int(item["on_hand"]),
                reserved=int(item.get("reserved", 0)),
                available=(
                    int(item["available"])
                    if "available" in item
                    else (
                        int(item["local_available"])
                        if "local_available" in item
                        else int(item["on_hand"]) - int(item.get("reserved", 0))
                    )
                ),
                committed=int(item.get("committed", 0)),
                true_available=(
                    int(item["true_available"])
                    if "true_available" in item
                    else None
                ),
                source_version=item.get("source_version"),
                last_synced_at=item.get("last_synced_at"),
            )
            for item in state["inventory"]
        }
        self.reservations: list[Reservation] = []
        self.fulfillments: list[Fulfillment] = []
        self.fulfillment_promises: list[FulfillmentPromise] = []
        self.refunds: list[Refund] = []
        self.approval_requests: list[ApprovalRequest] = []
        self.warehouse_jobs: list[WarehouseJob] = [
            WarehouseJob(
                warehouse_job_id=item["warehouse_job_id"],
                order_id=item["order_id"],
                sku=item["sku"],
                quantity=int(item["quantity"]),
                status=item["status"],
                cancellation_requested=bool(
                    item.get("cancellation_requested", False)
                ),
                hold_status=item.get("hold_status"),
                continued_after_cancel=bool(
                    item.get("continued_after_cancel", False)
                ),
            )
            for item in state.get("warehouse", [])
        ]
        self.inventory_releases: list[InventoryRelease] = []
        self.workflow_holds: list[WorkflowHold] = []
        self.warehouse_cancellation_requests: list[
            WarehouseCancellationRequest
        ] = []
        self.timeline: list[Event] = []
        self._next_reservation = 1
        self._next_fulfillment = 1
        self._next_promise = 1
        self._next_refund = 1
        self._next_approval = 1
        self._next_release = 1
        self._next_hold = 1
        self._next_warehouse_cancel = 1
        self._fulfillment_by_idempotency_key: dict[str, Fulfillment] = {}

    def snapshot_summary(self) -> dict[str, Any]:
        return {
            "orders": {key: to_plain(value) for key, value in self.orders.items()},
            "inventory": {key: to_plain(value) for key, value in self.inventory.items()},
            "reservations": [to_plain(item) for item in self.reservations],
            "fulfillments": [to_plain(item) for item in self.fulfillments],
            "fulfillment_promises": [
                to_plain(item) for item in self.fulfillment_promises
            ],
            "refunds": [to_plain(item) for item in self.refunds],
            "approval_requests": [
                to_plain(item) for item in self.approval_requests
            ],
            "warehouse_jobs": [to_plain(item) for item in self.warehouse_jobs],
            "inventory_releases": [
                to_plain(item) for item in self.inventory_releases
            ],
            "workflow_holds": [to_plain(item) for item in self.workflow_holds],
            "warehouse_cancellation_requests": [
                to_plain(item) for item in self.warehouse_cancellation_requests
            ],
            "counts": {
                "fulfillments": len(self.fulfillments),
                "reservations": len(self.reservations),
                "fulfillment_promises": len(self.fulfillment_promises),
                "refunds": len(self.refunds),
                "approval_requests": len(self.approval_requests),
                "warehouse_jobs": len(self.warehouse_jobs),
                "inventory_releases": len(self.inventory_releases),
                "workflow_holds": len(self.workflow_holds),
                "warehouse_cancellation_requests": len(
                    self.warehouse_cancellation_requests
                ),
                "reserved_inventory": {
                    sku: inventory.reserved for sku, inventory in self.inventory.items()
                },
            },
        }

    def compact_state(self) -> dict[str, Any]:
        return {
            "fulfillments": len(self.fulfillments),
            "fulfillment_promises": len(self.fulfillment_promises),
            "refunds": len(self.refunds),
            "approval_requests": len(self.approval_requests),
            "inventory_releases": len(self.inventory_releases),
            "workflow_holds": len(self.workflow_holds),
            "warehouse_cancellation_requests": len(
                self.warehouse_cancellation_requests
            ),
            "reserved_inventory": {
                sku: inventory.reserved for sku, inventory in self.inventory.items()
            },
        }

    def add_event(
        self,
        actor: str,
        event: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.timeline.append(
            Event(
                step=len(self.timeline) + 1,
                actor=actor,
                event=event,
                message=message,
                details=details or {},
            )
        )

    def receive_webhook(self, webhook: dict[str, Any]) -> None:
        self.add_event(
            actor="scenario",
            event="webhook_received",
            message=f"Webhook {webhook['id']} received for order {webhook['order_id']}.",
            details=deepcopy(webhook),
        )

    def receive_fulfillment_task(self, task: dict[str, Any]) -> None:
        fault = task.get("fault", {})
        fault_text = f" with fault {fault['type']}" if fault else ""
        self.add_event(
            actor="scenario",
            event="fulfillment_task_received",
            message=(
                f"Fulfillment task {task['id']} received for order "
                f"{task['order_id']}{fault_text}."
            ),
            details=deepcopy(task),
        )

    def receive_inventory_promise_task(self, task: dict[str, Any]) -> None:
        fault = task.get("fault", {})
        fault_text = f" with fault {fault['type']}" if fault else ""
        self.add_event(
            actor="scenario",
            event="inventory_promise_task_received",
            message=(
                f"Inventory promise task {task['id']} received for order "
                f"{task['order_id']}{fault_text}."
            ),
            details=deepcopy(task),
        )

    def receive_refund_request(self, request: dict[str, Any]) -> None:
        self.add_event(
            actor="scenario",
            event="refund_request_received",
            message=(
                f"Refund request {request['id']} received for order "
                f"{request['order_id']} in the amount of {request['amount']}."
            ),
            details=deepcopy(request),
        )

    def receive_cancel_request(self, request: dict[str, Any]) -> None:
        order_id = request["order_id"]
        if order_id in self.orders:
            self.orders[order_id].cancel_requested = True
        details = deepcopy(request)
        details["warehouse_jobs_at_request"] = [
            to_plain(job) for job in self._warehouse_jobs_for_order(order_id)
        ]
        self.add_event(
            actor="scenario",
            event="cancel_request_received",
            message=f"Cancel request {request['id']} received for order {order_id}.",
            details=details,
        )

    def reserve_inventory(
        self,
        *,
        order_id: str,
        sku: str,
        quantity: int,
        actor: str,
        webhook_id: str | None,
    ) -> Reservation:
        if sku not in self.inventory:
            self.inventory[sku] = Inventory(sku=sku, on_hand=0, reserved=0)
        self.inventory[sku].reserved += quantity
        reservation = Reservation(
            reservation_id=f"res_{self._next_reservation:03d}",
            order_id=order_id,
            sku=sku,
            quantity=quantity,
            created_by=actor,
            webhook_id=webhook_id,
        )
        self._next_reservation += 1
        self.reservations.append(reservation)
        self.add_event(
            actor=actor,
            event="inventory_reserved",
            message=(
                f"{actor} reserves {quantity} unit(s) of {sku}; "
                f"reserved inventory is now {self.inventory[sku].reserved}."
            ),
            details=to_plain(reservation),
        )
        return reservation

    def promise_fulfillment(
        self,
        *,
        order_id: str,
        sku: str,
        quantity: int,
        actor: str,
        source_event_id: str | None,
        reservation_id: str | None = None,
    ) -> FulfillmentPromise:
        inventory = self.inventory[sku]
        promise = FulfillmentPromise(
            promise_id=f"promise_{self._next_promise:03d}",
            order_id=order_id,
            sku=sku,
            quantity=quantity,
            created_by=actor,
            source_event_id=source_event_id,
            based_on_available=inventory.available,
            true_available_at_commit=inventory.true_available,
            snapshot_version=inventory.source_version,
            last_synced_at=inventory.last_synced_at,
            reservation_id=reservation_id,
        )
        self._next_promise += 1
        self.fulfillment_promises.append(promise)
        self.add_event(
            actor=actor,
            event="fulfillment_promised",
            message=(
                f"{actor} promises fulfillment for order {order_id}, sku {sku}, "
                f"using available={inventory.available} without confirmed reservation."
            ),
            details=to_plain(promise),
        )
        return promise

    def refresh_inventory_snapshot(self, *, sku: str, actor: str) -> Inventory:
        inventory = self.inventory[sku]
        before = to_plain(inventory)
        if inventory.true_available is not None:
            inventory.available = inventory.true_available
        inventory.last_synced_at = "fresh"
        inventory.source_version = "refreshed"
        self.add_event(
            actor=actor,
            event="inventory_refreshed",
            message=(
                f"{actor} refreshes inventory for {sku}; available is now "
                f"{inventory.available}."
            ),
            details={"before": before, "after": to_plain(inventory)},
        )
        return inventory

    def route_manual_review(
        self,
        *,
        order_id: str,
        sku: str,
        actor: str,
        reason: str,
        source_event_id: str | None,
    ) -> None:
        self.add_event(
            actor=actor,
            event="manual_review_routed",
            message=f"{actor} routes order {order_id}, sku {sku} to manual review.",
            details={
                "order_id": order_id,
                "sku": sku,
                "reason": reason,
                "source_event_id": source_event_id,
            },
        )

    def place_workflow_hold(
        self,
        *,
        order_id: str,
        sku: str | None,
        actor: str,
        reason: str,
        source_event_id: str | None,
    ) -> WorkflowHold:
        warehouse_job = self._first_warehouse_job_for_order(order_id)
        hold = WorkflowHold(
            hold_id=f"hold_{self._next_hold:03d}",
            order_id=order_id,
            sku=sku,
            reason=reason,
            created_by=actor,
            source_event_id=source_event_id,
            warehouse_status_at_hold=warehouse_job.status if warehouse_job else None,
        )
        self._next_hold += 1
        self.workflow_holds.append(hold)
        if warehouse_job:
            warehouse_job.hold_status = "held_for_review"
        self.add_event(
            actor=actor,
            event="workflow_hold_created",
            message=f"{actor} places order {order_id} on hold for {reason}.",
            details=to_plain(hold),
        )
        return hold

    def cancel_order(
        self,
        *,
        order_id: str,
        actor: str,
        source_event_id: str | None,
    ) -> None:
        order = self.orders[order_id]
        before = to_plain(order)
        order.order_status = "cancelled"
        order.cancel_requested = True
        self.add_event(
            actor=actor,
            event="order_cancelled",
            message=f"{actor} marks order {order_id} as cancelled.",
            details={
                "source_event_id": source_event_id,
                "before": before,
                "after": to_plain(order),
            },
        )

    def release_inventory(
        self,
        *,
        order_id: str,
        sku: str,
        quantity: int,
        actor: str,
        source_event_id: str | None,
    ) -> InventoryRelease:
        inventory = self.inventory[sku]
        warehouse_job = self._first_warehouse_job_for_order(order_id)
        inventory.reserved -= quantity
        release = InventoryRelease(
            release_id=f"release_{self._next_release:03d}",
            order_id=order_id,
            sku=sku,
            quantity=quantity,
            created_by=actor,
            source_event_id=source_event_id,
            warehouse_status_at_release=warehouse_job.status if warehouse_job else None,
            order_status_at_release=self.orders[order_id].order_status,
        )
        self._next_release += 1
        self.inventory_releases.append(release)
        self.add_event(
            actor=actor,
            event="inventory_released",
            message=(
                f"{actor} releases {quantity} unit(s) of {sku}; reserved "
                f"inventory is now {inventory.reserved}."
            ),
            details=to_plain(release),
        )
        return release

    def submit_warehouse_cancellation_request(
        self,
        *,
        order_id: str,
        actor: str,
        source_event_id: str | None,
    ) -> WarehouseCancellationRequest:
        warehouse_job = self._first_warehouse_job_for_order(order_id)
        if warehouse_job is None:
            raise ValueError(f"No warehouse job for order: {order_id}")
        request = WarehouseCancellationRequest(
            cancellation_request_id=f"wh_cancel_{self._next_warehouse_cancel:03d}",
            order_id=order_id,
            warehouse_job_id=warehouse_job.warehouse_job_id,
            created_by=actor,
            source_event_id=source_event_id,
            warehouse_status_at_request=warehouse_job.status,
        )
        self._next_warehouse_cancel += 1
        self.warehouse_cancellation_requests.append(request)
        warehouse_job.cancellation_requested = True
        self.add_event(
            actor=actor,
            event="warehouse_cancellation_requested",
            message=(
                f"{actor} asks warehouse to cancel job "
                f"{warehouse_job.warehouse_job_id} while status is {warehouse_job.status}."
            ),
            details=to_plain(request),
        )
        return request

    def warehouse_continue_fulfillment(
        self,
        *,
        order_id: str,
        actor: str,
        source_event_id: str | None,
        new_status: str = "shipped",
    ) -> WarehouseJob:
        warehouse_job = self._first_warehouse_job_for_order(order_id)
        if warehouse_job is None:
            raise ValueError(f"No warehouse job for order: {order_id}")
        before = to_plain(warehouse_job)
        warehouse_job.status = new_status
        warehouse_job.continued_after_cancel = True
        order = self.orders[order_id]
        order.fulfillment_status = new_status
        order.shipment_status = new_status
        self.add_event(
            actor="warehouse_twin",
            event="warehouse_fulfillment_continued",
            message=(
                f"Warehouse continues job {warehouse_job.warehouse_job_id} "
                f"for cancelled order {order_id}; status is now {new_status}."
            ),
            details={
                "source_event_id": source_event_id,
                "triggered_by": actor,
                "before": before,
                "after": to_plain(warehouse_job),
            },
        )
        return warehouse_job

    def create_approval_request(
        self,
        *,
        order_id: str,
        amount: float,
        reason: str,
        actor: str,
        source_event_id: str | None,
        required_policy: str,
    ) -> ApprovalRequest:
        approval = ApprovalRequest(
            approval_id=f"approval_{self._next_approval:03d}",
            order_id=order_id,
            amount=amount,
            reason=reason,
            created_by=actor,
            source_event_id=source_event_id,
            required_policy=required_policy,
        )
        self._next_approval += 1
        self.approval_requests.append(approval)
        if order_id in self.orders:
            self.orders[order_id].refund_status = "approval_pending"
        self.add_event(
            actor=actor,
            event="approval_request_created",
            message=(
                f"{actor} creates approval request {approval.approval_id} "
                f"before refunding order {order_id}."
            ),
            details=to_plain(approval),
        )
        return approval

    def create_refund(
        self,
        *,
        order_id: str,
        amount: float,
        reason: str,
        actor: str,
        source_event_id: str | None,
        approval_id: str | None = None,
        approved_by: str | None = None,
    ) -> Refund:
        order = self.orders[order_id]
        refund = Refund(
            refund_id=f"refund_{self._next_refund:03d}",
            order_id=order_id,
            amount=amount,
            reason=reason,
            created_by=actor,
            source_event_id=source_event_id,
            approval_id=approval_id,
            approved_by=approved_by,
            order_fulfillment_status_at_issue=order.fulfillment_status,
            shipment_status_at_issue=order.shipment_status,
        )
        self._next_refund += 1
        self.refunds.append(refund)
        order.refund_status = "issued"
        self.add_event(
            actor=actor,
            event="refund_issued",
            message=(
                f"{actor} issues refund {refund.refund_id} for order "
                f"{order_id} without blocking platform mutation."
            ),
            details=to_plain(refund),
        )
        return refund

    def create_fulfillment(
        self,
        *,
        order_id: str,
        sku: str,
        quantity: int,
        actor: str,
        webhook_id: str | None,
        idempotency_key: str | None,
        request_id: str | None = None,
        source_event_id: str | None = None,
        fault_type: str | None = None,
    ) -> Fulfillment:
        if idempotency_key and idempotency_key in self._fulfillment_by_idempotency_key:
            fulfillment = self._fulfillment_by_idempotency_key[idempotency_key]
            self.add_event(
                actor="commerce_twin",
                event="idempotency_replay_returned_existing",
                message=(
                    f"Idempotency key {idempotency_key} returns existing "
                    f"fulfillment {fulfillment.fulfillment_id}."
                ),
                details={
                    "idempotency_key": idempotency_key,
                    "fulfillment_id": fulfillment.fulfillment_id,
                    "request_id": request_id,
                    "source_event_id": source_event_id,
                },
            )
            return fulfillment

        fulfillment = Fulfillment(
            fulfillment_id=f"ful_{self._next_fulfillment:03d}",
            order_id=order_id,
            sku=sku,
            quantity=quantity,
            created_by=actor,
            webhook_id=webhook_id,
            idempotency_key=idempotency_key,
            request_id=request_id,
            source_event_id=source_event_id,
        )
        self._next_fulfillment += 1
        self.fulfillments.append(fulfillment)
        if idempotency_key:
            self._fulfillment_by_idempotency_key[idempotency_key] = fulfillment
        self.add_event(
            actor=actor,
            event="fulfillment_created",
            message=(
                f"{actor} creates fulfillment {fulfillment.fulfillment_id} "
                f"for order {order_id}, sku {sku}."
            ),
            details=to_plain(fulfillment),
        )
        if fault_type == "timeout_after_commit":
            self.add_event(
                actor="commerce_twin",
                event="fault_injected",
                message=(
                    f"Twin committed fulfillment {fulfillment.fulfillment_id}, "
                    "then returned timeout_after_commit."
                ),
                details={
                    "type": "timeout_after_commit",
                    "action": "create_fulfillment",
                    "fulfillment_id": fulfillment.fulfillment_id,
                    "order_id": order_id,
                    "sku": sku,
                    "idempotency_key": idempotency_key,
                    "request_id": request_id,
                    "source_event_id": source_event_id,
                },
            )
            raise TimeoutAfterCommit(fulfillment)
        return fulfillment

    def find_fulfillment(
        self,
        *,
        order_id: str,
        sku: str,
        idempotency_key: str | None = None,
    ) -> Fulfillment | None:
        if idempotency_key and idempotency_key in self._fulfillment_by_idempotency_key:
            return self._fulfillment_by_idempotency_key[idempotency_key]
        for fulfillment in reversed(self.fulfillments):
            if fulfillment.order_id == order_id and fulfillment.sku == sku:
                return fulfillment
        return None

    def mark_duplicate_skipped(self, actor: str, webhook: dict[str, Any]) -> None:
        self.add_event(
            actor=actor,
            event="duplicate_webhook_skipped",
            message=f"{actor} skips duplicate webhook {webhook['id']}.",
            details=deepcopy(webhook),
        )

    def _warehouse_jobs_for_order(self, order_id: str) -> list[WarehouseJob]:
        return [job for job in self.warehouse_jobs if job.order_id == order_id]

    def _first_warehouse_job_for_order(self, order_id: str) -> WarehouseJob | None:
        jobs = self._warehouse_jobs_for_order(order_id)
        return jobs[0] if jobs else None
