from __future__ import annotations

import json
from typing import Any


def _sentence(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    return text if text.endswith((".", "!", "?")) else f"{text}."


def build_business_risk_summary(
    *,
    title: str,
    findings: list[dict[str, Any]],
    scenario_report: dict[str, Any],
) -> list[str]:
    if findings:
        primary = findings[0]
        risk = scenario_report.get(
            "risk",
            f"{title} triggered `{primary['policy_id']}`.",
        )
        impact = scenario_report.get(
            "possible_impact",
            primary["business_impact"],
        )
        control = scenario_report.get(
            "recommended_control",
            primary["recommendation"],
        )
    else:
        risk = scenario_report.get(
            "risk",
            f"{title} completed without policy findings.",
        )
        impact = scenario_report.get(
            "possible_impact",
            "No immediate commerce accident was detected in this run.",
        )
        control = scenario_report.get(
            "recommended_control",
            "Keep the same guardrails and rerun this scenario after automation changes.",
        )

    return [
        "## Business Risk Summary",
        "",
        f"- Risk: {_sentence(risk)}",
        f"- Possible impact: {_sentence(impact)}",
        f"- Recommended control: {_sentence(control)}",
        "",
    ]


def build_state_diff(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    high_value_refund_threshold: float = 100.0,
) -> dict[str, Any]:
    before_reserved = before["counts"]["reserved_inventory"]
    after_reserved = after["counts"]["reserved_inventory"]
    all_skus = sorted(set(before_reserved) | set(after_reserved))
    reserved_delta = {
        sku: after_reserved.get(sku, 0) - before_reserved.get(sku, 0)
        for sku in all_skus
    }
    expected_reserved: dict[str, int] = {}
    for order in after["orders"].values():
        for line_item in order["line_items"]:
            sku = line_item["sku"]
            expected_reserved[sku] = expected_reserved.get(sku, 0) + int(
                line_item["quantity"]
            )
    excess_reserved = {
        sku: after_reserved.get(sku, 0) - expected_reserved.get(sku, 0)
        for sku in sorted(set(after_reserved) | set(expected_reserved))
        if after_reserved.get(sku, 0) > expected_reserved.get(sku, 0)
    }
    after_promises = after.get("fulfillment_promises", [])
    unreserved_promises = [
        promise
        for promise in after_promises
        if not promise.get("reservation_id")
    ]
    oversell_promises = [
        promise
        for promise in after_promises
        if promise.get("true_available_at_commit") is not None
        and int(promise["quantity"]) > int(promise["true_available_at_commit"])
    ]
    after_refunds = after.get("refunds", [])
    after_approval_requests = after.get("approval_requests", [])
    refund_amount_before = sum(float(refund["amount"]) for refund in before.get("refunds", []))
    refund_amount_after = sum(float(refund["amount"]) for refund in after_refunds)
    post_shipment_refunds_without_approval = [
        refund
        for refund in after_refunds
        if (
            refund.get("order_fulfillment_status_at_issue") == "shipped"
            or refund.get("shipment_status_at_issue") in {"carrier_scanned", "shipped"}
        )
        and not refund.get("approval_id")
        and not refund.get("approved_by")
    ]
    high_value_refunds_without_approval = [
        refund
        for refund in after_refunds
        if float(refund["amount"]) >= high_value_refund_threshold
        and not refund.get("approval_id")
        and not refund.get("approved_by")
    ]
    after_warehouse_jobs = after.get("warehouse_jobs", [])
    after_inventory_releases = after.get("inventory_releases", [])
    after_workflow_holds = after.get("workflow_holds", [])
    after_warehouse_cancellations = after.get("warehouse_cancellation_requests", [])
    cancelled_orders_after = {
        order_id: order
        for order_id, order in after.get("orders", {}).items()
        if order.get("order_status") == "cancelled"
    }
    continued_after_cancel_jobs = [
        job for job in after_warehouse_jobs if job.get("continued_after_cancel")
    ]
    warehouse_conflict_without_hold = bool(
        continued_after_cancel_jobs
        and not after_workflow_holds
        and not after_warehouse_cancellations
    )
    ship_after_cancel = any(
        job.get("order_id") in cancelled_orders_after
        and job.get("continued_after_cancel")
        and job.get("status") in {"shipped", "carrier_scanned"}
        for job in after_warehouse_jobs
    )
    refund_and_inventory_release_while_warehouse_continued = bool(
        after_refunds and after_inventory_releases and continued_after_cancel_jobs
    )
    return {
        "before": {
            "fulfillments": before["counts"]["fulfillments"],
            "fulfillment_promises": before["counts"].get("fulfillment_promises", 0),
            "refunds": before["counts"].get("refunds", 0),
            "approval_requests": before["counts"].get("approval_requests", 0),
            "inventory_releases": before["counts"].get("inventory_releases", 0),
            "workflow_holds": before["counts"].get("workflow_holds", 0),
            "warehouse_cancellation_requests": before["counts"].get(
                "warehouse_cancellation_requests", 0
            ),
            "warehouse_jobs": before.get("warehouse_jobs", []),
            "orders": before.get("orders", {}),
            "refund_amount_issued": refund_amount_before,
            "reserved_inventory": before_reserved,
        },
        "after": {
            "fulfillments": after["counts"]["fulfillments"],
            "fulfillment_promises": after["counts"].get("fulfillment_promises", 0),
            "refunds": after["counts"].get("refunds", 0),
            "approval_requests": after["counts"].get("approval_requests", 0),
            "inventory_releases": after["counts"].get("inventory_releases", 0),
            "workflow_holds": after["counts"].get("workflow_holds", 0),
            "warehouse_cancellation_requests": after["counts"].get(
                "warehouse_cancellation_requests", 0
            ),
            "refund_amount_issued": refund_amount_after,
            "reserved_inventory": after_reserved,
            "reservations": after["reservations"],
            "fulfillments_detail": after["fulfillments"],
            "fulfillment_promises_detail": after_promises,
            "refunds_detail": after_refunds,
            "approval_requests_detail": after_approval_requests,
            "warehouse_jobs": after_warehouse_jobs,
            "inventory_releases_detail": after_inventory_releases,
            "workflow_holds_detail": after_workflow_holds,
            "warehouse_cancellation_requests_detail": after_warehouse_cancellations,
            "orders": after.get("orders", {}),
        },
        "delta": {
            "fulfillments_added": after["counts"]["fulfillments"]
            - before["counts"]["fulfillments"],
            "fulfillment_promises_added": after["counts"].get("fulfillment_promises", 0)
            - before["counts"].get("fulfillment_promises", 0),
            "refunds_added": after["counts"].get("refunds", 0)
            - before["counts"].get("refunds", 0),
            "approval_requests_added": after["counts"].get("approval_requests", 0)
            - before["counts"].get("approval_requests", 0),
            "inventory_releases_added": after["counts"].get("inventory_releases", 0)
            - before["counts"].get("inventory_releases", 0),
            "workflow_holds_added": after["counts"].get("workflow_holds", 0)
            - before["counts"].get("workflow_holds", 0),
            "warehouse_cancellation_requests_added": after["counts"].get(
                "warehouse_cancellation_requests", 0
            )
            - before["counts"].get("warehouse_cancellation_requests", 0),
            "refund_amount_delta": refund_amount_after - refund_amount_before,
            "reservations_added": after["counts"]["reservations"]
            - before["counts"]["reservations"],
            "reserved_inventory_delta": reserved_delta,
        },
        "expected": {
            "reserved_inventory": expected_reserved,
        },
        "accident_signals": {
            "duplicate_fulfillment": after["counts"]["fulfillments"] > 1,
            "duplicated_reserved_inventory": bool(excess_reserved),
            "excess_reserved_inventory": excess_reserved,
            "unreserved_fulfillment_promise": bool(unreserved_promises),
            "oversell_risk": bool(oversell_promises),
            "post_shipment_refund_without_approval": bool(
                post_shipment_refunds_without_approval
            ),
            "high_value_refund_without_approval": bool(
                high_value_refunds_without_approval
            ),
            "warehouse_conflict_without_hold": warehouse_conflict_without_hold,
            "ship_after_cancel": ship_after_cancel,
            "refund_and_inventory_release_while_warehouse_continued": (
                refund_and_inventory_release_while_warehouse_continued
            ),
        },
    }


def build_markdown_report(
    *,
    run_id: str,
    scenario: dict[str, Any],
    runner_name: str,
    status: str,
    findings: list[dict[str, Any]],
    state_diff: dict[str, Any],
) -> str:
    title = scenario.get("name", scenario.get("id", "Scenario"))
    scenario_report = scenario.get("report", {})
    lines = [
        f"# Commerce Safety Report: {title}",
        "",
        f"- Run ID: `{run_id}`",
        f"- Runner: `{runner_name}`",
        f"- Status: `{status}`",
        "",
    ]
    lines.extend(
        build_business_risk_summary(
            title=title,
            findings=findings,
            scenario_report=scenario_report,
        )
    )
    lines.extend(
        [
        "## Executive Summary",
        "",
        ]
    )
    if status == "passed":
        passed_summary = scenario_report.get("passed_summary") or [
            "The automation handled the scenario without creating a business accident.",
            "The final commerce state stayed within policy.",
        ]
        lines.extend(passed_summary)
    else:
        failed_summary = scenario_report.get("failed_summary") or [
            "The automation created a critical commerce incident.",
            "The final commerce state violated policy and needs review.",
        ]
        lines.extend(failed_summary)

    lines.extend(
        [
            "",
            "## State Change",
            "",
            f"- Fulfillments before: `{state_diff['before']['fulfillments']}`",
            f"- Fulfillments after: `{state_diff['after']['fulfillments']}`",
            f"- Fulfillment promises before: `{state_diff['before']['fulfillment_promises']}`",
            f"- Fulfillment promises after: `{state_diff['after']['fulfillment_promises']}`",
            f"- Refunds before: `{state_diff['before']['refunds']}`",
            f"- Refunds after: `{state_diff['after']['refunds']}`",
            f"- Approval requests before: `{state_diff['before']['approval_requests']}`",
            f"- Approval requests after: `{state_diff['after']['approval_requests']}`",
            f"- Inventory releases before: `{state_diff['before']['inventory_releases']}`",
            f"- Inventory releases after: `{state_diff['after']['inventory_releases']}`",
            f"- Workflow holds before: `{state_diff['before']['workflow_holds']}`",
            f"- Workflow holds after: `{state_diff['after']['workflow_holds']}`",
            f"- Warehouse cancellation requests before: `{state_diff['before']['warehouse_cancellation_requests']}`",
            f"- Warehouse cancellation requests after: `{state_diff['after']['warehouse_cancellation_requests']}`",
            f"- Refund amount issued before: `{state_diff['before']['refund_amount_issued']}`",
            f"- Refund amount issued after: `{state_diff['after']['refund_amount_issued']}`",
            f"- Reserved inventory before: `{state_diff['before']['reserved_inventory']}`",
            f"- Reserved inventory after: `{state_diff['after']['reserved_inventory']}`",
            f"- Expected reserved inventory: `{state_diff['expected']['reserved_inventory']}`",
            "",
            "## Findings",
            "",
        ]
    )

    if not findings:
        lines.append("No policy violations were detected.")
    else:
        for finding in findings:
            evidence = json.dumps(finding["evidence"], indent=2, ensure_ascii=False)
            lines.extend(
                [
                    f"### {finding['policy_id']}",
                    "",
                    f"- Severity: `{finding['severity']}`",
                    f"- Status: `{finding['status']}`",
                    f"- Business impact: {finding['business_impact']}",
                    f"- Recommendation: {finding['recommendation']}",
                    "",
                    "Evidence:",
                    "",
                    "```json",
                    evidence,
                    "```",
                    "",
                ]
            )

    if findings:
        fix_text = scenario_report.get(
            "fix",
            "Use webhook ID deduplication before mutating order state. For fulfillment actions, also check existing fulfillment state and use an idempotency key for mutating retries.",
        )
        lines.extend(
            [
                "## How To Fix",
                "",
                fix_text,
                "",
            ]
        )
    else:
        what_worked = scenario_report.get(
            "what_worked",
            "The automation avoided unsafe duplicate mutation and kept the state within policy.",
        )
        lines.extend(
            [
                "## What Worked",
                "",
                what_worked,
                "",
            ]
        )

    lines.extend(
        [
            "## Replay",
            "",
            f"Run `commerce-safety replay runs/{run_id}` to print the recorded timeline from `trace.json`.",
            "",
        ]
    )
    return "\n".join(lines)
