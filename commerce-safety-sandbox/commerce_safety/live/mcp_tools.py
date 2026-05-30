from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..io import read_json
from ..models import to_plain
from ..platform_skins.amazon import AmazonPlatformBinding, AmazonSellerOpsRouter
from ..twin import TimeoutAfterCommit
from .sessions import SessionManager


class CommerceMCPTools:
    """MVP MCP tool surface for live commerce sessions.

    This class intentionally keeps the tool semantics independent from any one
    MCP transport. Stage 3 locks the agent-facing tool names and payloads; a
    stdio/server wrapper can sit on top without changing the core behavior.
    """

    def __init__(self, runs_dir: Path | str = Path("runs")):
        self.manager = SessionManager(runs_dir=runs_dir)
        self.amazon = AmazonSellerOpsRouter(self)
        self._tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "commerce.start_session": self._start_session,
            "commerce.get_task": self._get_task,
            "commerce.create_fulfillment": self._create_fulfillment,
            "commerce.find_fulfillment": self._find_fulfillment,
            "commerce.reserve_inventory": self._reserve_inventory,
            "commerce.promise_fulfillment": self._promise_fulfillment,
            "commerce.refresh_inventory": self._refresh_inventory,
            "commerce.route_manual_review": self._route_manual_review,
            "commerce.create_refund": self._create_refund,
            "commerce.create_approval_request": self._create_approval_request,
            "commerce.cancel_order": self._cancel_order,
            "commerce.release_inventory": self._release_inventory,
            "commerce.place_workflow_hold": self._place_workflow_hold,
            "commerce.submit_warehouse_cancellation_request": (
                self._submit_warehouse_cancellation_request
            ),
            "commerce.warehouse_continue_fulfillment": (
                self._warehouse_continue_fulfillment
            ),
            "commerce.skip_duplicate_webhook": self._skip_duplicate_webhook,
            "commerce.complete_session": self._complete_session,
            "commerce.get_trace": self._get_trace,
            "commerce.get_policy_report": self._get_policy_report,
            "commerce.get_patch_hints": self._get_patch_hints,
            "amazon.get_inventory_summaries": self._amazon_get_inventory_summaries,
            "amazon.get_listing_item": self._amazon_get_listing_item,
            "amazon.patch_listing_quantity": self._amazon_patch_listing_quantity,
            "amazon.submit_feed": self._amazon_submit_feed,
            "amazon.get_feed_status": self._amazon_get_feed_status,
            "amazon.get_order": self._amazon_get_order,
            "amazon.get_order_items": self._amazon_get_order_items,
            "amazon.confirm_shipment": self._amazon_confirm_shipment,
            "amazon.inject_notification": self._amazon_inject_notification,
            "amazon.promise_fulfillment": self._amazon_promise_fulfillment,
            "amazon.route_manual_review": self._amazon_route_manual_review,
            "amazon.cancel_order": self._amazon_cancel_order,
            "amazon.place_workflow_hold": self._amazon_place_workflow_hold,
            "amazon.submit_warehouse_cancellation_request": (
                self._amazon_submit_warehouse_cancellation_request
            ),
            "amazon.get_coverage": self._amazon_get_coverage,
        }

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": name, "description": self._description_for(name)}
            for name in self._tools
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Unknown commerce MCP tool: {name}")
        return self._tools[name](arguments)

    def _start_session(self, arguments: dict[str, Any]) -> dict[str, Any]:
        scenario_path = arguments.get("scenario_path")
        if not scenario_path:
            raise ValueError("scenario_path is required")
        session = self.manager.create_session(Path(scenario_path))
        return {
            "ok": True,
            "session_id": session.session_id,
            "scenario_id": session.scenario_id,
            "scenario_name": session.scenario_name,
            "status": session.status,
        }

    def _get_task(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session_id = arguments["session_id"]
        task = self.manager.get_next_task(session_id)
        return {
            "ok": True,
            "session_id": session_id,
            "task": task,
            "done": task is None,
        }

    def _create_fulfillment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        try:
            fulfillment = session.twin.create_fulfillment(
                order_id=arguments["order_id"],
                sku=arguments["sku"],
                quantity=int(arguments.get("quantity", 1)),
                actor=arguments.get("actor", "mcp_agent"),
                webhook_id=arguments.get("webhook_id"),
                idempotency_key=arguments.get("idempotency_key"),
                request_id=arguments.get("request_id"),
                source_event_id=arguments.get("source_event_id"),
                fault_type=arguments.get("fault_type"),
            )
        except TimeoutAfterCommit as error:
            return {
                "ok": False,
                "error": "timeout_after_commit",
                "message": "Twin committed the mutation before returning a timeout.",
                "fulfillment_id": error.fulfillment.fulfillment_id,
            }
        return {
            "ok": True,
            "session_id": session.session_id,
            "fulfillment": to_plain(fulfillment),
        }

    def _find_fulfillment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        fulfillment = session.twin.find_fulfillment(
            order_id=arguments["order_id"],
            sku=arguments["sku"],
            idempotency_key=arguments.get("idempotency_key"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "fulfillment": to_plain(fulfillment) if fulfillment else None,
        }

    def _reserve_inventory(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        reservation = session.twin.reserve_inventory(
            order_id=arguments["order_id"],
            sku=arguments["sku"],
            quantity=int(arguments.get("quantity", 1)),
            actor=arguments.get("actor", "mcp_agent"),
            webhook_id=arguments.get("webhook_id"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "reservation": to_plain(reservation),
        }

    def _promise_fulfillment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        promise = session.twin.promise_fulfillment(
            order_id=arguments["order_id"],
            sku=arguments["sku"],
            quantity=int(arguments.get("quantity", 1)),
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
            reservation_id=arguments.get("reservation_id"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "promise": to_plain(promise),
        }

    def _refresh_inventory(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        inventory = session.twin.refresh_inventory_snapshot(
            sku=arguments["sku"],
            actor=arguments.get("actor", "mcp_agent"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "inventory": to_plain(inventory),
        }

    def _route_manual_review(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        session.twin.route_manual_review(
            order_id=arguments["order_id"],
            sku=arguments["sku"],
            actor=arguments.get("actor", "mcp_agent"),
            reason=arguments.get("reason", "manual_review_required"),
            source_event_id=arguments.get("source_event_id"),
        )
        return {"ok": True, "session_id": session.session_id}

    def _create_refund(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        refund = session.twin.create_refund(
            order_id=arguments["order_id"],
            amount=float(arguments["amount"]),
            reason=arguments.get("reason", "buyer_request"),
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
            approval_id=arguments.get("approval_id"),
            approved_by=arguments.get("approved_by"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "refund": to_plain(refund),
        }

    def _create_approval_request(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        approval = session.twin.create_approval_request(
            order_id=arguments["order_id"],
            amount=float(arguments["amount"]),
            reason=arguments.get("reason", "buyer_request"),
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
            required_policy=arguments["required_policy"],
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "approval_request": to_plain(approval),
        }

    def _cancel_order(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        session.twin.cancel_order(
            order_id=arguments["order_id"],
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
        )
        return {"ok": True, "session_id": session.session_id}

    def _release_inventory(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        release = session.twin.release_inventory(
            order_id=arguments["order_id"],
            sku=arguments["sku"],
            quantity=int(arguments.get("quantity", 1)),
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "inventory_release": to_plain(release),
        }

    def _place_workflow_hold(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        hold = session.twin.place_workflow_hold(
            order_id=arguments["order_id"],
            sku=arguments.get("sku"),
            actor=arguments.get("actor", "mcp_agent"),
            reason=arguments.get("reason", "workflow_hold_required"),
            source_event_id=arguments.get("source_event_id"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "workflow_hold": to_plain(hold),
        }

    def _submit_warehouse_cancellation_request(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        request = session.twin.submit_warehouse_cancellation_request(
            order_id=arguments["order_id"],
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "warehouse_cancellation_request": to_plain(request),
        }

    def _warehouse_continue_fulfillment(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        job = session.twin.warehouse_continue_fulfillment(
            order_id=arguments["order_id"],
            actor=arguments.get("actor", "mcp_agent"),
            source_event_id=arguments.get("source_event_id"),
            new_status=arguments.get("new_status", "shipped"),
        )
        return {
            "ok": True,
            "session_id": session.session_id,
            "warehouse_job": to_plain(job),
        }

    def _skip_duplicate_webhook(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        session.twin.mark_duplicate_skipped(
            actor=arguments.get("actor", "mcp_agent"),
            webhook=arguments["webhook"],
        )
        return {"ok": True, "session_id": session.session_id}

    def _complete_session(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            **self.manager.complete_session(
                arguments["session_id"],
                runner_name=arguments.get("runner_name", "mcp_agent"),
            ),
        }

    def _get_trace(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        trace_path = session.output_path / "trace.json"
        if trace_path.exists():
            return read_json(trace_path)
        return {
            "run_id": session.session_id,
            "session_id": session.session_id,
            "scenario_id": session.scenario_id,
            "scenario_name": session.scenario_name,
            "status": session.status,
            "initial_state": session.initial_state,
            "current_state": session.twin.snapshot_summary(),
            "timeline": [to_plain(event) for event in session.twin.timeline],
        }

    def _get_policy_report(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        return read_json(session.output_path / "policy_report.json")

    def _get_patch_hints(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        return read_json(session.output_path / "patch_hints.json")

    def _amazon_binding(self, session_id: str):
        session = self.manager.get_session(session_id)
        return session, AmazonPlatformBinding.from_twin(session.twin)

    def _amazon_get_inventory_summaries(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        session, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.get_inventory_summaries(
            session_id=session.session_id,
            twin=session.twin,
            binding=binding,
            seller_skus=arguments.get("sellerSkus") or arguments.get("seller_skus"),
        )
        return body

    def _amazon_get_listing_item(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.get_listing_item(
            session_id=session.session_id,
            twin=session.twin,
            binding=binding,
            seller_id=arguments.get("sellerId", "seller_123"),
            platform_sku=arguments["sellerSku"],
        )
        return body

    def _amazon_patch_listing_quantity(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        session, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.patch_listing_quantity(
            session_id=session.session_id,
            twin=session.twin,
            binding=binding,
            seller_id=arguments.get("sellerId", "seller_123"),
            platform_sku=arguments["sellerSku"],
            body=arguments,
        )
        return body

    def _amazon_submit_feed(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session, _ = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.create_feed(
            session_id=session.session_id,
            twin=session.twin,
            body=arguments,
        )
        return body

    def _amazon_get_feed_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        _, body = self.amazon.get_feed(
            session_id=session.session_id,
            feed_id=arguments["feedId"],
        )
        return body

    def _amazon_get_order(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.get_order(
            session_id=session.session_id,
            twin=session.twin,
            binding=binding,
            amazon_order_id=arguments["amazonOrderId"],
        )
        return body

    def _amazon_get_order_items(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.get_order_items(
            session_id=session.session_id,
            twin=session.twin,
            binding=binding,
            amazon_order_id=arguments["amazonOrderId"],
        )
        return body

    def _amazon_confirm_shipment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.confirm_shipment(
            session_id=arguments["session_id"],
            binding=binding,
            amazon_order_id=arguments["amazonOrderId"],
            body=arguments,
        )
        return body

    def _amazon_inject_notification(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.inject_notification(
            session_id=session.session_id,
            twin=session.twin,
            binding=binding,
            body=arguments,
        )
        return body

    def _amazon_promise_fulfillment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.promise_fulfillment(
            session_id=arguments["session_id"],
            binding=binding,
            body=arguments,
        )
        return body

    def _amazon_route_manual_review(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.route_manual_review(
            session_id=arguments["session_id"],
            binding=binding,
            body=arguments,
        )
        return body

    def _amazon_cancel_order(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.cancel_order(
            session_id=arguments["session_id"],
            binding=binding,
            body=arguments,
        )
        return body

    def _amazon_place_workflow_hold(self, arguments: dict[str, Any]) -> dict[str, Any]:
        _, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.place_workflow_hold(
            session_id=arguments["session_id"],
            binding=binding,
            body=arguments,
        )
        return body

    def _amazon_submit_warehouse_cancellation_request(
        self,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        _, binding = self._amazon_binding(arguments["session_id"])
        _, body = self.amazon.submit_warehouse_cancellation_request(
            session_id=arguments["session_id"],
            binding=binding,
            body=arguments,
        )
        return body

    def _amazon_get_coverage(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.manager.get_session(arguments["session_id"])
        _, body = self.amazon.coverage_response(session.session_id)
        return body

    def _description_for(self, name: str) -> str:
        descriptions = {
            "commerce.start_session": "Start a live commerce validation session.",
            "commerce.get_task": "Return the next seeded scenario task.",
            "commerce.create_fulfillment": "Create fulfillment in the permissive twin.",
            "commerce.find_fulfillment": "Find an existing fulfillment by order, sku, or key.",
            "commerce.reserve_inventory": "Reserve inventory in the permissive twin.",
            "commerce.promise_fulfillment": "Record a customer-facing fulfillment promise.",
            "commerce.refresh_inventory": "Refresh inventory from true availability.",
            "commerce.route_manual_review": "Route an order line to manual review.",
            "commerce.create_refund": "Issue a refund in the permissive twin.",
            "commerce.create_approval_request": "Create an approval request before risky action.",
            "commerce.cancel_order": "Mark an order cancelled in the permissive twin.",
            "commerce.release_inventory": "Release reserved inventory.",
            "commerce.place_workflow_hold": "Place a workflow hold for review.",
            "commerce.submit_warehouse_cancellation_request": (
                "Request warehouse cancellation for an active job."
            ),
            "commerce.warehouse_continue_fulfillment": (
                "Advance warehouse fulfillment despite cancellation."
            ),
            "commerce.skip_duplicate_webhook": "Record that a repeated webhook was skipped.",
            "commerce.complete_session": "Evaluate policies and write artifacts.",
            "commerce.get_trace": "Read the live trace timeline.",
            "commerce.get_policy_report": "Read structured policy findings.",
            "commerce.get_patch_hints": "Read agent-readable repair hints.",
            "amazon.get_inventory_summaries": "Read Amazon-shaped FBA inventory summaries.",
            "amazon.get_listing_item": "Read an Amazon-shaped listing item.",
            "amazon.patch_listing_quantity": "Submit an Amazon-shaped listing quantity patch.",
            "amazon.submit_feed": "Submit an Amazon-shaped feed.",
            "amazon.get_feed_status": "Read Amazon-shaped feed processing status.",
            "amazon.get_order": "Read an Amazon-shaped order.",
            "amazon.get_order_items": "Read Amazon-shaped order items.",
            "amazon.confirm_shipment": "Confirm shipment through an Amazon-shaped order path.",
            "amazon.inject_notification": "Inject an Amazon-shaped notification.",
            "amazon.promise_fulfillment": "Record a seller automation fulfillment promise.",
            "amazon.route_manual_review": "Route an Amazon-shaped case to manual review.",
            "amazon.cancel_order": "Cancel an order from an Amazon-shaped agent action.",
            "amazon.place_workflow_hold": "Place a workflow hold from an Amazon-shaped action.",
            "amazon.submit_warehouse_cancellation_request": (
                "Request warehouse cancellation from an Amazon-shaped action."
            ),
            "amazon.get_coverage": "Read Amazon Seller Ops skin coverage.",
        }
        return descriptions[name]
