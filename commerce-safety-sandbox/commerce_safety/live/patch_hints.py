from __future__ import annotations

import json
from typing import Any

from ..artifacts import PATCH_HINTS_SCHEMA_VERSION


POLICY_HINTS = {
    "idempotency_required_for_mutating_retries": {
        "root_cause": (
            "The agent retried a mutating fulfillment action after timeout as a "
            "new request instead of treating the result as uncertain."
        ),
        "guardrails": [
            "Use a stable idempotency key for create_fulfillment.",
            "After timeout, query existing fulfillment state before retrying.",
            "Never create a second fulfillment for the same order line without checking state.",
        ],
    },
    "no_duplicate_fulfillment": {
        "root_cause": (
            "The agent created more fulfillment quantity than the order line requires."
        ),
        "guardrails": [
            "Check existing fulfillments by order_id and sku before creating another fulfillment.",
            "Use order_id + sku + action_type as the stable fulfillment key.",
        ],
    },
    "webhook_dedup_required": {
        "root_cause": "The agent produced side effects from repeated webhook delivery.",
        "guardrails": [
            "Persist processed webhook delivery IDs.",
            "Skip repeated webhook IDs before mutating fulfillment, refund, or inventory state.",
        ],
    },
    "reservation_required_before_promise": {
        "root_cause": "The agent promised fulfillment without a confirmed reservation.",
        "guardrails": [
            "Reserve inventory before making a customer-facing fulfillment promise.",
            "Route the order to manual review when reservation fails.",
        ],
    },
    "no_inventory_commit_from_stale_snapshot": {
        "root_cause": "The agent committed action from an outdated inventory snapshot.",
        "guardrails": [
            "Refresh inventory before committing fulfillment promises.",
            "Block or review actions when inventory data is stale.",
        ],
    },
    "no_oversell": {
        "root_cause": "The agent promised more inventory than was truly available.",
        "guardrails": [
            "Compare requested quantity against fresh available inventory.",
            "Only promise after a successful reservation.",
        ],
    },
    "no_refund_after_shipment_without_approval": {
        "root_cause": "The agent issued a refund after shipment without approval.",
        "guardrails": [
            "Create an approval request when an order is shipped or carrier-scanned.",
            "Hold the refund until a reviewer approves the after-shipment action.",
        ],
    },
    "high_value_refund_requires_approval": {
        "root_cause": "The agent issued a high-value refund without approval.",
        "guardrails": [
            "Require approval for refunds above the scenario threshold.",
            "Record approval_id or approved_by before issuing the refund.",
        ],
    },
    "warehouse_conflict_requires_hold": {
        "root_cause": "The agent handled cancellation while the warehouse was already processing.",
        "guardrails": [
            "Place the workflow on hold when warehouse status is picked or packed.",
            "Submit a warehouse cancellation request before refunding or releasing inventory.",
        ],
    },
    "no_ship_after_cancel": {
        "root_cause": "The workflow allowed shipment to continue after cancellation.",
        "guardrails": [
            "Block automatic shipment continuation after order cancellation.",
            "Resolve warehouse cancellation state before final refund or inventory release.",
        ],
    },
    "no_double_refund_or_inventory_release": {
        "root_cause": "The agent refunded or released inventory while fulfillment continued.",
        "guardrails": [
            "Do not release inventory or issue final refund while warehouse fulfillment is unresolved.",
            "Use a manual review state for cancellation and warehouse race conditions.",
        ],
    },
}


def build_patch_hints(
    *,
    run_id: str,
    scenario: dict[str, Any],
    status: str,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    hints: list[dict[str, Any]] = []
    for finding in findings:
        policy_id = finding["policy_id"]
        default_hint = POLICY_HINTS.get(policy_id, {})
        hints.append(
            {
                "policy_id": policy_id,
                "severity": finding["severity"],
                "root_cause": default_hint.get(
                    "root_cause",
                    finding.get("business_impact", "Policy violation detected."),
                ),
                "guardrails": default_hint.get(
                    "guardrails",
                    [finding.get("recommendation", "Add a guardrail for this policy.")],
                ),
                "evidence": finding.get("evidence", {}),
            }
        )

    return {
        "schema_version": PATCH_HINTS_SCHEMA_VERSION,
        "run_id": run_id,
        "scenario_id": scenario["id"],
        "scenario_name": scenario.get("name", scenario["id"]),
        "status": status,
        "replay_command": f"commerce-safety replay runs/{run_id}",
        "likely_guardrails": _likely_guardrails(hints),
        "hints": hints,
    }


def build_patch_hints_markdown(patch_hints: dict[str, Any]) -> str:
    lines = [
        f"# Patch Hints: {patch_hints['scenario_name']}",
        "",
        f"- Run ID: `{patch_hints['run_id']}`",
        f"- Status: `{patch_hints['status']}`",
        "",
    ]
    if not patch_hints["hints"]:
        lines.extend(
            [
                "No patch hints were generated because the policy check passed.",
                "",
            ]
        )
        return "\n".join(lines)

    for hint in patch_hints["hints"]:
        lines.extend(
            [
                f"## {hint['policy_id']}",
                "",
                f"- Severity: `{hint['severity']}`",
                f"- Root cause: {hint['root_cause']}",
                "- Guardrails:",
            ]
        )
        for guardrail in hint["guardrails"]:
            lines.append(f"  - {guardrail}")
        lines.append("")
    return "\n".join(lines)


def build_agent_summary_markdown(
    *,
    patch_hints: dict[str, Any],
    findings: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Agent Summary: {patch_hints['scenario_name']}",
        "",
        f"- Run ID: `{patch_hints['run_id']}`",
        f"- Status: `{patch_hints['status']}`",
        f"- Replay: `{patch_hints['replay_command']}`",
        "",
    ]
    if not findings:
        lines.extend(
            [
                "No policy findings were detected. Keep these guardrails in place.",
                "",
            ]
        )
        return "\n".join(lines)

    first = findings[0]
    lines.extend(
        [
            "## Failure",
            "",
            f"- Primary policy: `{first['policy_id']}`",
            f"- Severity: `{first['severity']}`",
            f"- Business impact: {first['business_impact']}",
            "",
            "## Likely Guardrails",
            "",
        ]
    )
    for guardrail in patch_hints["likely_guardrails"]:
        lines.append(f"- {guardrail}")
    lines.extend(["", "## Evidence", "", "```json"])
    lines.append(json.dumps(first.get("evidence", {}), indent=2, ensure_ascii=False))
    lines.extend(["```", ""])
    return "\n".join(lines)


def build_failure_explain_markdown(
    *,
    patch_hints: dict[str, Any],
    findings: list[dict[str, Any]],
    trace: dict[str, Any],
    state_diff: dict[str, Any],
) -> str:
    lines = [
        f"# Failure Explain: {patch_hints['scenario_name']}",
        "",
        f"- Run ID: `{patch_hints['run_id']}`",
        f"- Replay: `{patch_hints['replay_command']}`",
        "",
        "## Root Cause",
        "",
    ]
    if findings:
        for hint in patch_hints["hints"]:
            lines.append(f"- `{hint['policy_id']}`: {hint['root_cause']}")
    else:
        lines.append("- No root cause detected; the run passed policy evaluation.")

    lines.extend(["", "## Timeline", ""])
    for event in trace["timeline"]:
        lines.append(f"- Step {event['step']}: {event['message']}")
        details = event.get("details") or {}
        if details:
            lines.append("  ```json")
            lines.append(json.dumps(details, indent=2, ensure_ascii=False))
            lines.append("  ```")

    lines.extend(
        [
            "",
            "## State Diff Signals",
            "",
            "```json",
            json.dumps(state_diff.get("accident_signals", {}), indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _likely_guardrails(hints: list[dict[str, Any]]) -> list[str]:
    guardrails: list[str] = []
    seen: set[str] = set()
    for hint in hints:
        for guardrail in hint["guardrails"]:
            if guardrail not in seen:
                seen.add(guardrail)
                guardrails.append(guardrail)
    return guardrails
