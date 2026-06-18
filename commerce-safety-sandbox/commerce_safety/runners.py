from __future__ import annotations

from typing import Any, Protocol

from .twin import CommerceTwin, TimeoutAfterCommit


class Runner(Protocol):
    name: str

    def handle_webhook(self, twin: CommerceTwin, webhook: dict[str, Any]) -> None:
        ...

    def handle_fulfillment_task(self, twin: CommerceTwin, task: dict[str, Any]) -> None:
        ...

    def handle_inventory_promise_task(
        self, twin: CommerceTwin, task: dict[str, Any]
    ) -> None:
        ...

    def handle_refund_request(self, twin: CommerceTwin, request: dict[str, Any]) -> None:
        ...

    def handle_tracking_upload_task(
        self, twin: CommerceTwin, task: dict[str, Any]
    ) -> None:
        ...

    def handle_cancel_request(self, twin: CommerceTwin, request: dict[str, Any]) -> None:
        ...


class BadRunner:
    name = "bad_runner"

    def handle_webhook(self, twin: CommerceTwin, webhook: dict[str, Any]) -> None:
        order = twin.orders[webhook["order_id"]]
        line_item = order.line_items[0]
        twin.add_event(
            actor=self.name,
            event="webhook_processing_started",
            message=f"{self.name} starts processing webhook {webhook['id']} without dedupe.",
            details={"webhook_id": webhook["id"], "order_id": order.order_id},
        )
        twin.reserve_inventory(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            webhook_id=webhook["id"],
        )
        twin.create_fulfillment(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            webhook_id=webhook["id"],
            idempotency_key=None,
            source_event_id=webhook["id"],
        )

    def handle_fulfillment_task(self, twin: CommerceTwin, task: dict[str, Any]) -> None:
        order = twin.orders[task["order_id"]]
        line_item = order.line_items[0]
        twin.add_event(
            actor=self.name,
            event="fulfillment_task_processing_started",
            message=(
                f"{self.name} starts task {task['id']} without an idempotency key."
            ),
            details={"task_id": task["id"], "order_id": order.order_id},
        )
        fault = task.get("fault", {})
        try:
            twin.create_fulfillment(
                order_id=order.order_id,
                sku=line_item.sku,
                quantity=line_item.quantity,
                actor=self.name,
                webhook_id=None,
                idempotency_key=None,
                request_id=f"{task['id']}:attempt_1",
                source_event_id=task["id"],
                fault_type=fault.get("type"),
            )
        except TimeoutAfterCommit:
            twin.add_event(
                actor=self.name,
                event="timeout_received",
                message=(
                    f"{self.name} receives timeout_after_commit and assumes the "
                    "fulfillment failed."
                ),
                details={"task_id": task["id"], "retry_strategy": "blind_retry"},
            )
            twin.create_fulfillment(
                order_id=order.order_id,
                sku=line_item.sku,
                quantity=line_item.quantity,
                actor=self.name,
                webhook_id=None,
                idempotency_key=None,
                request_id=f"{task['id']}:attempt_2",
                source_event_id=task["id"],
            )

    def handle_inventory_promise_task(
        self, twin: CommerceTwin, task: dict[str, Any]
    ) -> None:
        order = twin.orders[task["order_id"]]
        line_item = order.line_items[0]
        inventory = twin.inventory[line_item.sku]
        twin.add_event(
            actor=self.name,
            event="inventory_snapshot_read",
            message=(
                f"{self.name} reads stale inventory for {line_item.sku}: "
                f"available={inventory.available}, true_available={inventory.true_available}."
            ),
            details={
                "task_id": task["id"],
                "sku": line_item.sku,
                "available": inventory.available,
                "true_available": inventory.true_available,
                "last_synced_at": inventory.last_synced_at,
            },
        )
        if (inventory.available or 0) >= line_item.quantity:
            twin.promise_fulfillment(
                order_id=order.order_id,
                sku=line_item.sku,
                quantity=line_item.quantity,
                actor=self.name,
                source_event_id=task["id"],
                reservation_id=None,
            )
        else:
            twin.route_manual_review(
                order_id=order.order_id,
                sku=line_item.sku,
                actor=self.name,
                reason="local_inventory_unavailable",
                source_event_id=task["id"],
            )

    def handle_refund_request(self, twin: CommerceTwin, request: dict[str, Any]) -> None:
        order = twin.orders[request["order_id"]]
        twin.add_event(
            actor=self.name,
            event="refund_request_processing_started",
            message=(
                f"{self.name} starts refund request {request['id']} without "
                "checking shipment approval requirements."
            ),
            details={
                "request_id": request["id"],
                "order_id": order.order_id,
                "fulfillment_status": order.fulfillment_status,
                "shipment_status": order.shipment_status,
                "amount": request["amount"],
            },
        )
        twin.create_refund(
            order_id=order.order_id,
            amount=float(request["amount"]),
            reason=request.get("reason", "buyer_request"),
            actor=self.name,
            source_event_id=request["id"],
            approval_id=None,
            approved_by=None,
        )

    def handle_tracking_upload_task(
        self, twin: CommerceTwin, task: dict[str, Any]
    ) -> None:
        order = twin.orders[task["order_id"]]
        twin.add_event(
            actor=self.name,
            event="tracking_upload_processing_started",
            message=(
                f"{self.name} uploads tracking for order {order.order_id} as soon "
                "as the label is created."
            ),
            details={
                "task_id": task["id"],
                "order_id": order.order_id,
                "tracking_number": task["tracking_number"],
                "carrier_status": task.get("carrier_status"),
                "first_carrier_scan_seen": task.get("first_carrier_scan_seen"),
            },
        )
        upload = twin.upload_tracking(
            order_id=order.order_id,
            tracking_number=task["tracking_number"],
            carrier_status=task.get("carrier_status", "unknown"),
            first_carrier_scan_seen=bool(task.get("first_carrier_scan_seen", False)),
            actor=self.name,
            source_event_id=task["id"],
            customer_notified=bool(task.get("customer_notified", True)),
        )
        if not upload.first_carrier_scan_seen and upload.customer_notified:
            twin.create_support_ticket(
                order_id=order.order_id,
                reason="tracking_visible_before_first_carrier_scan",
                actor=self.name,
                source_event_id=task["id"],
                tracking_upload_id=upload.tracking_upload_id,
                carrier_status=upload.carrier_status_at_upload,
            )

    def handle_cancel_request(self, twin: CommerceTwin, request: dict[str, Any]) -> None:
        order = twin.orders[request["order_id"]]
        line_item = order.line_items[0]
        twin.add_event(
            actor=self.name,
            event="cancel_request_processing_started",
            message=(
                f"{self.name} treats cancel request {request['id']} as a simple "
                "order cancellation despite warehouse progress."
            ),
            details={
                "request_id": request["id"],
                "order_id": order.order_id,
                "warehouse_jobs_at_request": request.get(
                    "warehouse_jobs_at_request", []
                ),
            },
        )
        twin.cancel_order(
            order_id=order.order_id,
            actor=self.name,
            source_event_id=request["id"],
        )
        twin.release_inventory(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            source_event_id=request["id"],
        )
        twin.create_refund(
            order_id=order.order_id,
            amount=float(request["amount"]),
            reason=request.get("reason", "buyer_cancelled"),
            actor=self.name,
            source_event_id=request["id"],
            approval_id=None,
            approved_by=None,
        )
        twin.warehouse_continue_fulfillment(
            order_id=order.order_id,
            actor=self.name,
            source_event_id=request["id"],
            new_status="shipped",
        )


class GoodRunner:
    name = "good_runner"

    def __init__(self) -> None:
        self.processed_webhooks: set[str] = set()

    def handle_webhook(self, twin: CommerceTwin, webhook: dict[str, Any]) -> None:
        if webhook["id"] in self.processed_webhooks:
            twin.mark_duplicate_skipped(self.name, webhook)
            return

        self.processed_webhooks.add(webhook["id"])
        order = twin.orders[webhook["order_id"]]
        line_item = order.line_items[0]
        twin.add_event(
            actor=self.name,
            event="webhook_processing_started",
            message=f"{self.name} starts processing webhook {webhook['id']} with dedupe.",
            details={"webhook_id": webhook["id"], "order_id": order.order_id},
        )
        twin.reserve_inventory(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            webhook_id=webhook["id"],
        )
        twin.create_fulfillment(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            webhook_id=webhook["id"],
            idempotency_key=f"fulfillment:{order.order_id}:{line_item.sku}",
            source_event_id=webhook["id"],
        )

    def handle_fulfillment_task(self, twin: CommerceTwin, task: dict[str, Any]) -> None:
        order = twin.orders[task["order_id"]]
        line_item = order.line_items[0]
        idempotency_key = f"fulfillment:{order.order_id}:{line_item.sku}:create"
        twin.add_event(
            actor=self.name,
            event="fulfillment_task_processing_started",
            message=(
                f"{self.name} starts task {task['id']} with stable idempotency key."
            ),
            details={
                "task_id": task["id"],
                "order_id": order.order_id,
                "idempotency_key": idempotency_key,
            },
        )
        fault = task.get("fault", {})
        try:
            twin.create_fulfillment(
                order_id=order.order_id,
                sku=line_item.sku,
                quantity=line_item.quantity,
                actor=self.name,
                webhook_id=None,
                idempotency_key=idempotency_key,
                request_id=f"{task['id']}:attempt_1",
                source_event_id=task["id"],
                fault_type=fault.get("type"),
            )
        except TimeoutAfterCommit:
            twin.add_event(
                actor=self.name,
                event="timeout_received",
                message=(
                    f"{self.name} receives timeout_after_commit and checks "
                    "existing fulfillment state before retrying."
                ),
                details={"task_id": task["id"], "retry_strategy": "query_before_retry"},
            )
            existing = twin.find_fulfillment(
                order_id=order.order_id,
                sku=line_item.sku,
                idempotency_key=idempotency_key,
            )
            if existing:
                twin.add_event(
                    actor=self.name,
                    event="existing_fulfillment_confirmed",
                    message=(
                        f"{self.name} confirms fulfillment "
                        f"{existing.fulfillment_id} already committed."
                    ),
                    details={
                        "task_id": task["id"],
                        "fulfillment_id": existing.fulfillment_id,
                        "idempotency_key": idempotency_key,
                    },
                )
            else:
                twin.create_fulfillment(
                    order_id=order.order_id,
                    sku=line_item.sku,
                    quantity=line_item.quantity,
                    actor=self.name,
                    webhook_id=None,
                    idempotency_key=idempotency_key,
                    request_id=f"{task['id']}:attempt_2",
                    source_event_id=task["id"],
                )

    def handle_inventory_promise_task(
        self, twin: CommerceTwin, task: dict[str, Any]
    ) -> None:
        order = twin.orders[task["order_id"]]
        line_item = order.line_items[0]
        inventory = twin.refresh_inventory_snapshot(sku=line_item.sku, actor=self.name)
        if (inventory.available or 0) < line_item.quantity:
            twin.route_manual_review(
                order_id=order.order_id,
                sku=line_item.sku,
                actor=self.name,
                reason="fresh_inventory_unavailable",
                source_event_id=task["id"],
            )
            return

        reservation = twin.reserve_inventory(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            webhook_id=None,
        )
        twin.promise_fulfillment(
            order_id=order.order_id,
            sku=line_item.sku,
            quantity=line_item.quantity,
            actor=self.name,
            source_event_id=task["id"],
            reservation_id=reservation.reservation_id,
        )

    def handle_refund_request(self, twin: CommerceTwin, request: dict[str, Any]) -> None:
        order = twin.orders[request["order_id"]]
        twin.add_event(
            actor=self.name,
            event="refund_request_processing_started",
            message=(
                f"{self.name} checks shipment state before refunding order "
                f"{order.order_id}."
            ),
            details={
                "request_id": request["id"],
                "order_id": order.order_id,
                "fulfillment_status": order.fulfillment_status,
                "shipment_status": order.shipment_status,
                "amount": request["amount"],
            },
        )
        shipped_or_scanned = order.fulfillment_status == "shipped" or (
            order.shipment_status in {"carrier_scanned", "shipped"}
        )
        threshold = float(
            twin.scenario.get("approval_rules", {}).get(
                "high_value_refund_threshold", 100
            )
        )
        high_value = float(request["amount"]) >= threshold
        if shipped_or_scanned or high_value:
            policy = (
                "no_refund_after_shipment_without_approval"
                if shipped_or_scanned
                else "high_value_refund_requires_approval"
            )
            approval = twin.create_approval_request(
                order_id=order.order_id,
                amount=float(request["amount"]),
                reason=request.get("reason", "buyer_request"),
                actor=self.name,
                source_event_id=request["id"],
                required_policy=policy,
            )
            twin.add_event(
                actor=self.name,
                event="refund_held_for_review",
                message=(
                    f"{self.name} holds refund request {request['id']} until "
                    f"approval request {approval.approval_id} is reviewed."
                ),
                details={
                    "request_id": request["id"],
                    "approval_id": approval.approval_id,
                    "order_id": order.order_id,
                    "required_policy": policy,
                },
            )
            return

        twin.create_refund(
            order_id=order.order_id,
            amount=float(request["amount"]),
            reason=request.get("reason", "buyer_request"),
            actor=self.name,
            source_event_id=request["id"],
            approval_id=None,
            approved_by=None,
        )

    def handle_tracking_upload_task(
        self, twin: CommerceTwin, task: dict[str, Any]
    ) -> None:
        order = twin.orders[task["order_id"]]
        line_item = order.line_items[0]
        carrier_status = task.get("carrier_status", "unknown")
        first_scan_seen = bool(task.get("first_carrier_scan_seen", False))
        twin.add_event(
            actor=self.name,
            event="tracking_upload_processing_started",
            message=(
                f"{self.name} checks carrier scan state before notifying "
                f"customer for order {order.order_id}."
            ),
            details={
                "task_id": task["id"],
                "order_id": order.order_id,
                "tracking_number": task["tracking_number"],
                "carrier_status": carrier_status,
                "first_carrier_scan_seen": first_scan_seen,
            },
        )
        if not first_scan_seen:
            twin.hold_tracking_until_first_scan(
                order_id=order.order_id,
                tracking_number=task["tracking_number"],
                carrier_status=carrier_status,
                actor=self.name,
                source_event_id=task["id"],
            )
            twin.route_manual_review(
                order_id=order.order_id,
                sku=line_item.sku,
                actor=self.name,
                reason="carrier_first_scan_missing",
                source_event_id=task["id"],
            )
            return

        twin.upload_tracking(
            order_id=order.order_id,
            tracking_number=task["tracking_number"],
            carrier_status=carrier_status,
            first_carrier_scan_seen=first_scan_seen,
            actor=self.name,
            source_event_id=task["id"],
            customer_notified=bool(task.get("customer_notified", True)),
        )

    def handle_cancel_request(self, twin: CommerceTwin, request: dict[str, Any]) -> None:
        order = twin.orders[request["order_id"]]
        line_item = order.line_items[0]
        twin.add_event(
            actor=self.name,
            event="cancel_request_processing_started",
            message=(
                f"{self.name} checks warehouse progress before resolving "
                f"cancel request {request['id']}."
            ),
            details={
                "request_id": request["id"],
                "order_id": order.order_id,
                "warehouse_jobs_at_request": request.get(
                    "warehouse_jobs_at_request", []
                ),
            },
        )
        twin.place_workflow_hold(
            order_id=order.order_id,
            sku=line_item.sku,
            actor=self.name,
            reason="warehouse_pick_pack_conflict",
            source_event_id=request["id"],
        )
        twin.submit_warehouse_cancellation_request(
            order_id=order.order_id,
            actor=self.name,
            source_event_id=request["id"],
        )
        twin.add_event(
            actor=self.name,
            event="cancel_resolution_held",
            message=(
                f"{self.name} does not refund, release inventory, or mark order "
                f"{order.order_id} cancelled until warehouse confirms the stop."
            ),
            details={
                "request_id": request["id"],
                "order_id": order.order_id,
                "held_actions": [
                    "cancel_order",
                    "release_inventory",
                    "issue_refund",
                ],
            },
        )


def get_runner(name: str) -> Runner:
    if name == "bad_runner":
        return BadRunner()
    if name == "good_runner":
        return GoodRunner()
    raise ValueError(f"Unknown runner: {name}")
