from __future__ import annotations

import json
from typing import Any


def is_saas_scenario(scenario: dict[str, Any]) -> bool:
    scenario_id = str(scenario.get("id", ""))
    if scenario_id.startswith("SAAS-"):
        return True
    policies = scenario.get("policies", {}).get("primary", [])
    return any(str(policy).startswith(("billing_", "slack_", "github_")) for policy in policies)


def _sentence(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    return text if text.endswith((".", "!", "?")) else f"{text}."


def _service_label(service: str) -> str:
    return {
        "stripe": "Stripe",
        "slack": "Slack",
        "github": "GitHub",
    }.get(service, service.title())


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


def build_incident_cards(
    *,
    findings: list[dict[str, Any]],
    run_id: str,
) -> list[str]:
    if not findings:
        return []

    lines = [
        "## Incident Cards",
        "",
    ]
    for finding in findings:
        evidence = finding.get("evidence", {})
        action = evidence.get("action") or evidence.get("event") or "unsafe automation action"
        entity = (
            evidence.get("order_id")
            or evidence.get("sku")
            or evidence.get("fulfillment_id")
            or "the tested commerce state"
        )
        lines.extend(
            [
                f"### Incident Card: {finding['policy_id']}",
                "",
                f"- What happened: `{action}` changed {entity} into an unsafe state.",
                f"- Why it matters: {_sentence(finding['business_impact'])}",
                f"- Evidence: see the JSON evidence for `{finding['policy_id']}` below.",
                f"- Recommended guardrail: {_sentence(finding['recommendation'])}",
                (
                    "- How to retest: apply the guardrail, rerun the same scenario, "
                    f"and confirm `commerce-safety replay runs/{run_id}` shows no policy findings."
                ),
                "",
            ]
        )
    return lines


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
    after_tracking_uploads = after.get("tracking_uploads", [])
    after_support_tickets = after.get("support_tickets", [])
    tracking_uploads_before_first_scan = [
        upload
        for upload in after_tracking_uploads
        if not upload.get("first_carrier_scan_seen")
        and upload.get("carrier_status_at_upload")
        not in {"first_scan", "carrier_scanned", "accepted", "in_transit", "shipped"}
    ]
    support_tickets_from_early_tracking = [
        ticket
        for ticket in after_support_tickets
        if ticket.get("tracking_upload_id")
        and ticket.get("reason") == "tracking_visible_before_first_carrier_scan"
    ]
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
            "tracking_uploads": before["counts"].get("tracking_uploads", 0),
            "support_tickets": before["counts"].get("support_tickets", 0),
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
            "tracking_uploads": after["counts"].get("tracking_uploads", 0),
            "support_tickets": after["counts"].get("support_tickets", 0),
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
            "tracking_uploads_detail": after_tracking_uploads,
            "support_tickets_detail": after_support_tickets,
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
            "tracking_uploads_added": after["counts"].get("tracking_uploads", 0)
            - before["counts"].get("tracking_uploads", 0),
            "support_tickets_added": after["counts"].get("support_tickets", 0)
            - before["counts"].get("support_tickets", 0),
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
            "tracking_upload_before_first_carrier_scan": bool(
                tracking_uploads_before_first_scan
            ),
            "support_ticket_from_early_tracking": bool(
                support_tickets_from_early_tracking
            ),
            "warehouse_conflict_without_hold": warehouse_conflict_without_hold,
            "ship_after_cancel": ship_after_cancel,
            "refund_and_inventory_release_while_warehouse_continued": (
                refund_and_inventory_release_while_warehouse_continued
            ),
        },
    }


def _counts_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int]:
    before_counts = before.get("counts", {})
    after_counts = after.get("counts", {})
    deltas: dict[str, int] = {}
    for key in sorted(set(before_counts) | set(after_counts)):
        before_value = before_counts.get(key, 0)
        after_value = after_counts.get(key, 0)
        if isinstance(before_value, int) and isinstance(after_value, int):
            deltas[f"{key}_delta"] = after_value - before_value
    return deltas


def _first_value(mapping: dict[str, Any]) -> dict[str, Any] | None:
    if not mapping:
        return None
    return next(iter(mapping.values()))


def _event_request_field(event: dict[str, Any], key: str) -> Any:
    request = event.get("request") or {}
    return request.get(key)


def _event_response_field(event: dict[str, Any], *path: str) -> Any:
    value: Any = event.get("response") or {}
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _agent_event_sequence(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sequence: list[dict[str, Any]] = []
    for event in events:
        service = event.get("service")
        operation = event.get("operation")
        item = {
            "step": event.get("step"),
            "actor": event.get("actor"),
            "service": service,
            "operation": operation,
            "fault": event.get("fault"),
        }
        if service == "stripe" and operation == "subscriptions.create":
            item["payment_intent_status"] = _event_response_field(
                event,
                "payment_intent",
                "status",
            )
            item["invoice_status"] = _event_response_field(event, "invoice", "status")
            item["subscription_status"] = _event_response_field(
                event,
                "subscription",
                "status",
            )
        elif service == "slack" and operation == "chat.postMessage":
            item["channel_id"] = _event_request_field(event, "channel_id")
            item["message_kind"] = (
                (_event_request_field(event, "metadata") or {}).get("kind")
                if isinstance(_event_request_field(event, "metadata"), dict)
                else None
            )
            item["delivered"] = _event_response_field(event, "message", "delivered")
        elif service == "github" and operation == "checks.create":
            item["check_name"] = _event_response_field(event, "check_run", "name")
            item["head_sha"] = _event_response_field(event, "check_run", "head_sha")
            item["conclusion"] = _event_response_field(
                event,
                "check_run",
                "conclusion",
            )
        elif service == "github" and operation == "issues.create":
            item["title"] = _event_response_field(event, "issue", "title")
        elif service == "github" and operation == "pulls.comment":
            item["pull_number"] = _event_response_field(event, "comment", "pull_number")
        sequence.append({key: value for key, value in item.items() if value is not None})
    return sequence


def _duplicate_side_effect_groups(
    items: list[dict[str, Any]],
    duplicate_event_ids: set[str],
    *,
    side_effect_type: str,
    dedupe_key_field: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in items:
        metadata = item.get("metadata") or {}
        event_id = metadata.get("stripe_event_id")
        if event_id not in duplicate_event_ids:
            continue
        dedupe_key = str(item.get(dedupe_key_field) or metadata.get("kind") or "item")
        grouped.setdefault((event_id, dedupe_key), []).append(item)
    return [
        {
            "stripe_event_id": event_id,
            "side_effect_type": side_effect_type,
            "dedupe_key": dedupe_key,
            "items": group,
        }
        for (event_id, dedupe_key), group in grouped.items()
        if len(group) > 1
    ]


def build_environment_state_diff(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    events = events or []
    stripe_before = before.get("stripe", {})
    stripe_after = after.get("stripe", {})
    slack_before = before.get("slack", {})
    slack_after = after.get("slack", {})
    github_before = before.get("github", {})
    github_after = after.get("github", {})

    latest_invoice = _first_value(stripe_after.get("invoices", {}))
    latest_payment_intent = _first_value(stripe_after.get("payment_intents", {}))
    latest_subscription = _first_value(stripe_after.get("subscriptions", {}))
    stripe_events = list(stripe_after.get("events", {}).values())
    duplicate_stripe_events = [
        event
        for event in stripe_events
        if int(event.get("duplicate_delivery_count", 0)) > 0
    ]
    duplicate_stripe_event_ids = {
        event["event_id"] for event in duplicate_stripe_events if event.get("event_id")
    }
    check_runs = list(github_after.get("check_runs", {}).values())
    issues = list(github_after.get("issues", {}).values())
    pr_comments = list(github_after.get("pr_comments", {}).values())
    success_checks = [
        check for check in check_runs if check.get("conclusion") == "success"
    ]
    action_required_checks = [
        check for check in check_runs if check.get("conclusion") == "action_required"
    ]
    slack_messages = slack_after.get("messages", [])
    failed_alerts = [
        message
        for message in slack_messages
        if message.get("metadata", {}).get("kind") == "billing_failure_alert"
        and not message.get("delivered")
    ]
    delivered_alerts = [
        message
        for message in slack_messages
        if message.get("metadata", {}).get("kind") == "billing_failure_alert"
        and message.get("delivered")
    ]
    success_messages = [
        message
        for message in slack_messages
        if message.get("metadata", {}).get("kind") == "success_notification"
    ]
    duplicate_slack_side_effects = _duplicate_side_effect_groups(
        [
            message
            for message in slack_messages
            if message.get("delivered")
            and message.get("metadata", {}).get("kind") == "billing_failure_alert"
        ],
        duplicate_stripe_event_ids,
        side_effect_type="slack_message",
        dedupe_key_field="channel_id",
    )
    duplicate_github_side_effects = []
    duplicate_github_side_effects.extend(
        _duplicate_side_effect_groups(
            check_runs,
            duplicate_stripe_event_ids,
            side_effect_type="github_check_run",
            dedupe_key_field="name",
        )
    )
    duplicate_github_side_effects.extend(
        _duplicate_side_effect_groups(
            issues,
            duplicate_stripe_event_ids,
            side_effect_type="github_issue",
            dedupe_key_field="title",
        )
    )
    duplicate_github_side_effects.extend(
        _duplicate_side_effect_groups(
            pr_comments,
            duplicate_stripe_event_ids,
            side_effect_type="github_pr_comment",
            dedupe_key_field="body",
        )
    )
    event_sequence = _agent_event_sequence(events)
    slack_faults = [
        event for event in event_sequence if event.get("service") == "slack" and event.get("fault")
    ]
    github_success_after_slack_fault = False
    first_slack_fault_step = min(
        (int(event["step"]) for event in slack_faults if event.get("step") is not None),
        default=None,
    )
    if first_slack_fault_step is not None:
        github_success_after_slack_fault = any(
            event.get("service") == "github"
            and event.get("operation") == "checks.create"
            and event.get("conclusion") == "success"
            and int(event.get("step", 0)) > first_slack_fault_step
            for event in event_sequence
        )

    accident_signals = {
        "stripe_failed_payment": bool(
            stripe_after.get("signals", {}).get("has_failed_payment")
        ),
        "slack_billing_alert_failed": bool(failed_alerts),
        "slack_billing_alert_delivered": bool(delivered_alerts),
        "slack_success_notification_after_failed_payment": bool(success_messages),
        "github_success_check_after_failed_payment": bool(success_checks),
        "github_action_required_check": bool(action_required_checks),
        "github_review_artifact_created": bool(
            action_required_checks or github_after.get("signals", {}).get("has_pr_feedback")
        ),
        "github_success_after_slack_fault": github_success_after_slack_fault,
        "stripe_duplicate_webhook_delivery": bool(duplicate_stripe_events),
        "duplicate_slack_side_effects_from_stripe_webhook": bool(
            duplicate_slack_side_effects
        ),
        "duplicate_github_side_effects_from_stripe_webhook": bool(
            duplicate_github_side_effects
        ),
    }

    return {
        "artifact_kind": "environment_state_diff",
        "services": ["stripe", "slack", "github"],
        "before": {
            "stripe": {
                "counts": stripe_before.get("counts", {}),
                "signals": stripe_before.get("signals", {}),
            },
            "slack": {
                "counts": slack_before.get("counts", {}),
                "signals": slack_before.get("signals", {}),
            },
            "github": {
                "counts": github_before.get("counts", {}),
                "signals": github_before.get("signals", {}),
            },
        },
        "after": {
            "stripe": {
                "counts": stripe_after.get("counts", {}),
                "signals": stripe_after.get("signals", {}),
                "latest_subscription": latest_subscription,
                "latest_invoice": latest_invoice,
                "latest_payment_intent": latest_payment_intent,
            },
            "slack": {
                "counts": slack_after.get("counts", {}),
                "signals": slack_after.get("signals", {}),
                "messages": slack_messages,
            },
            "github": {
                "counts": github_after.get("counts", {}),
                "signals": github_after.get("signals", {}),
                "check_runs": check_runs,
                "issues": list(github_after.get("issues", {}).values()),
                "pr_comments": list(github_after.get("pr_comments", {}).values()),
            },
        },
        "delta": {
            "stripe": _counts_delta(stripe_before, stripe_after),
            "slack": _counts_delta(slack_before, slack_after),
            "github": _counts_delta(github_before, github_after),
        },
        "service_summaries": [
            {
                "service": "stripe",
                "state": (
                    "failed_payment"
                    if accident_signals["stripe_failed_payment"]
                    else "no_failed_payment"
                ),
                "summary": (
                    "Initial subscription payment requires a new payment method."
                    if accident_signals["stripe_failed_payment"]
                    else "No failed payment signal was recorded."
                ),
                "payment_intent_status": (
                    latest_payment_intent or {}
                ).get("status"),
                "invoice_status": (latest_invoice or {}).get("status"),
                "subscription_status": (latest_subscription or {}).get("status"),
                "duplicate_webhook_deliveries": stripe_after.get("counts", {}).get(
                    "duplicate_webhook_deliveries",
                    0,
                ),
            },
            {
                "service": "slack",
                "state": (
                    "alert_failed"
                    if accident_signals["slack_billing_alert_failed"]
                    else "duplicate_alerts_delivered"
                    if accident_signals[
                        "duplicate_slack_side_effects_from_stripe_webhook"
                    ]
                    else "alert_delivered"
                    if accident_signals["slack_billing_alert_delivered"]
                    else "no_billing_alert"
                ),
                "summary": (
                    "Billing alert failed to deliver."
                    if accident_signals["slack_billing_alert_failed"]
                    else "Duplicate billing alerts were delivered for the same Stripe event."
                    if accident_signals[
                        "duplicate_slack_side_effects_from_stripe_webhook"
                    ]
                    else "Billing alert reached a deliverable channel."
                    if accident_signals["slack_billing_alert_delivered"]
                    else "No delivered billing alert was recorded."
                ),
                "failed_alert_channels": [
                    message.get("channel_id") for message in failed_alerts
                ],
                "delivered_alert_channels": [
                    message.get("channel_id") for message in delivered_alerts
                ],
            },
            {
                "service": "github",
                "state": (
                    "false_success"
                    if accident_signals["github_success_check_after_failed_payment"]
                    else "duplicate_action_required_checks"
                    if accident_signals[
                        "duplicate_github_side_effects_from_stripe_webhook"
                    ]
                    else "action_required"
                    if accident_signals["github_action_required_check"]
                    else "no_policy_check"
                ),
                "summary": (
                    "GitHub check reported success despite failed billing state."
                    if accident_signals["github_success_check_after_failed_payment"]
                    else "Duplicate GitHub recovery checks were created for the same Stripe event."
                    if accident_signals[
                        "duplicate_github_side_effects_from_stripe_webhook"
                    ]
                    else "GitHub check kept the workflow in action-required state."
                    if accident_signals["github_action_required_check"]
                    else "No GitHub policy check was recorded."
                ),
                "check_conclusions": [
                    check.get("conclusion") for check in check_runs
                ],
                "review_artifacts": {
                    "action_required_checks": len(action_required_checks),
                    "issues": github_after.get("counts", {}).get("issues", 0),
                    "pr_comments": github_after.get("counts", {}).get("pr_comments", 0),
                },
            },
        ],
        "agent_behavior_signals": {
            "slack_faults": slack_faults,
            "github_success_after_slack_fault": github_success_after_slack_fault,
            "duplicate_stripe_events": duplicate_stripe_events,
            "duplicate_slack_side_effects": duplicate_slack_side_effects,
            "duplicate_github_side_effects": duplicate_github_side_effects,
            "event_sequence": event_sequence,
        },
        "expected": {
            "when_stripe_payment_fails": [
                "deliver a billing failure alert to a reachable Slack channel",
                "create a review artifact for billing recovery",
                "keep GitHub check state non-success until recovery is complete",
            ]
        },
        "accident_signals": accident_signals,
    }


def build_saas_markdown_report(
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
        f"# SaaS Agent Validation Report: {title}",
        "",
        f"- Run ID: `{run_id}`",
        f"- Runner: `{runner_name}`",
        f"- Status: `{status}`",
        "- Services: `Stripe`, `Slack`, `GitHub`",
        "",
    ]
    lines.extend(
        build_business_risk_summary(
            title=title,
            findings=findings,
            scenario_report=scenario_report,
        )
    )
    lines.extend(["## Executive Summary", ""])
    summary_key = "passed_summary" if status == "passed" else "failed_summary"
    lines.extend(
        scenario_report.get(
            summary_key,
            [
                "The agent completed the scenario.",
                "Review the cross-service state and policy findings below.",
            ],
        )
    )

    lines.extend(["", "## Cross-Service State", ""])
    for item in state_diff.get("service_summaries", []):
        lines.extend(
            [
                f"### {_service_label(item['service'])}",
                "",
                f"- State: `{item['state']}`",
                f"- Summary: {item['summary']}",
            ]
        )
        if item["service"] == "stripe":
            lines.extend(
                [
                    f"- Subscription status: `{item.get('subscription_status')}`",
                    f"- Invoice status: `{item.get('invoice_status')}`",
                    f"- Payment intent status: `{item.get('payment_intent_status')}`",
                    f"- Duplicate webhook deliveries: `{item.get('duplicate_webhook_deliveries', 0)}`",
                ]
            )
        elif item["service"] == "slack":
            lines.extend(
                [
                    f"- Failed alert channels: `{item.get('failed_alert_channels', [])}`",
                    f"- Delivered alert channels: `{item.get('delivered_alert_channels', [])}`",
                ]
            )
        elif item["service"] == "github":
            lines.extend(
                [
                    f"- Check conclusions: `{item.get('check_conclusions', [])}`",
                    f"- Review artifacts: `{item.get('review_artifacts', {})}`",
                ]
            )
        lines.append("")

    lines.extend(["## Agent Behavior Timeline", ""])
    for event in state_diff.get("agent_behavior_signals", {}).get("event_sequence", []):
        detail = []
        for key in (
            "payment_intent_status",
            "message_kind",
            "delivered",
            "fault",
            "conclusion",
            "title",
        ):
            if key in event:
                detail.append(f"{key}={event[key]}")
        suffix = f" ({', '.join(detail)})" if detail else ""
        lines.append(
            f"- Step {event.get('step')}: `{event.get('service')}.{event.get('operation')}` by `{event.get('actor')}`{suffix}"
        )
    if not state_diff.get("agent_behavior_signals", {}).get("event_sequence"):
        lines.append("- No agent tool calls were recorded.")
    lines.append("")

    lines.extend(["## Policy Findings", ""])
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
        lines.extend(
            [
                "## Repair Contract",
                "",
                scenario_report.get(
                    "fix",
                    "Treat failed billing as a blocking state, verify Slack delivery, and keep GitHub non-success until recovery is complete.",
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## What Worked",
                "",
                "The agent preserved failed billing as non-success state, delivered a human-visible alert, and created GitHub recovery artifacts.",
                "",
            ]
        )

    lines.extend(
        [
            "## Replay",
            "",
            f"Run `commerce-safety replay runs/{run_id}` to print the recorded scenario timeline from `trace.json`.",
            "",
        ]
    )
    return "\n".join(lines)


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
            f"- Tracking uploads before: `{state_diff['before']['tracking_uploads']}`",
            f"- Tracking uploads after: `{state_diff['after']['tracking_uploads']}`",
            f"- Support tickets before: `{state_diff['before']['support_tickets']}`",
            f"- Support tickets after: `{state_diff['after']['support_tickets']}`",
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
        lines[-2:] = build_incident_cards(findings=findings, run_id=run_id) + [
            "## Findings",
            "",
        ]
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
