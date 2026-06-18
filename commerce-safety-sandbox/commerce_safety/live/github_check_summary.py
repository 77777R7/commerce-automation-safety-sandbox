from __future__ import annotations

import json
from typing import Any

from ..artifacts import GITHUB_CHECK_SUMMARY_SCHEMA_VERSION


def _annotation_level(severity: str) -> str:
    if severity in {"critical", "high"}:
        return "failure"
    if severity == "medium":
        return "warning"
    return "notice"


def _title(status: str, scenario_name: str) -> str:
    if status == "passed":
        return f"Agent validation passed: {scenario_name}"
    return f"Agent validation failed: {scenario_name}"


def _summary(
    *,
    status: str,
    findings: list[dict[str, Any]],
    patch_hints: dict[str, Any],
    incident: dict[str, Any] | None = None,
) -> str:
    if not findings:
        return (
            "Policy evaluation completed with no findings. The agent behavior is "
            "safe for this sandbox scenario."
        )

    if incident:
        return (
            f"A duplicate Stripe `{incident['stripe_event_type']}` delivery created "
            "duplicate downstream side effects. Expected exactly one Slack billing "
            f"alert and one GitHub recovery check; observed "
            f"{incident['observed']['slack_billing_alerts']} Slack alert(s) and "
            f"{incident['observed']['github_recovery_checks']} GitHub check(s). "
            "Required fix: persist processed Stripe event IDs before Slack or "
            "GitHub mutations."
        )

    policy_ids = ", ".join(f"`{finding['policy_id']}`" for finding in findings)
    guardrail_count = len(patch_hints.get("likely_guardrails", []))
    return (
        f"Policy evaluation returned `{status}` with {len(findings)} finding(s): "
        f"{policy_ids}. {guardrail_count} repair guardrail(s) were generated."
    )


def _count_duplicate_items(groups: list[dict[str, Any]], item_key: str) -> int:
    return sum(len(group.get(item_key, [])) for group in groups)


def _duplicate_stripe_incident(
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for finding in findings:
        evidence = finding.get("evidence", {})
        duplicate_events = evidence.get("duplicate_stripe_events") or []
        duplicate_slack = evidence.get("duplicate_slack_side_effects") or []
        duplicate_github = evidence.get("duplicate_github_side_effects") or []
        if not duplicate_events or not (duplicate_slack or duplicate_github):
            continue

        event = duplicate_events[0]
        return {
            "title": "One Stripe event created duplicate recovery work.",
            "stripe_event_id": event.get("event_id"),
            "stripe_event_type": event.get("type", "webhook"),
            "stripe_deliveries": event.get("delivered_count"),
            "duplicate_deliveries": event.get("duplicate_delivery_count"),
            "expected": {
                "logical_stripe_events": 1,
                "slack_billing_alerts": 1,
                "github_recovery_checks": 1,
            },
            "observed": {
                "stripe_deliveries": event.get("delivered_count"),
                "slack_billing_alerts": _count_duplicate_items(
                    duplicate_slack,
                    "messages",
                ),
                "github_recovery_checks": _count_duplicate_items(
                    duplicate_github,
                    "items",
                ),
            },
            "required_guardrail": (
                "Persist processed Stripe event IDs before creating Slack or "
                "GitHub side effects."
            ),
        }
    return None


def build_github_check_summary(
    *,
    policy_report: dict[str, Any],
    patch_hints: dict[str, Any],
) -> dict[str, Any]:
    """Render policy output into a GitHub Checks-style artifact.

    This is an offline artifact, not a real GitHub API call. It gives an
    external agent builder the same review shape they would expect from a PR
    check: conclusion, output summary, annotations, and requested repairs.
    """

    findings = list(policy_report.get("findings", []))
    status = str(policy_report.get("status", "failed"))
    conclusion = "failure" if findings or status == "failed" else "success"
    scenario_name = str(
        patch_hints.get("scenario_name")
        or policy_report.get("scenario_name")
        or policy_report.get("scenario_id")
        or "Scenario"
    )
    annotations = []
    for finding in findings:
        annotations.append(
            {
                "path": "policy_report.json",
                "start_line": 1,
                "end_line": 1,
                "annotation_level": _annotation_level(str(finding["severity"])),
                "title": finding["policy_id"],
                "message": finding.get(
                    "business_impact",
                    "Policy violation detected.",
                ),
                "raw_details": {
                    "severity": finding["severity"],
                    "recommendation": finding.get("recommendation"),
                    "evidence": finding.get("evidence", {}),
                },
            }
        )
    incident = _duplicate_stripe_incident(findings)

    return {
        "schema_version": GITHUB_CHECK_SUMMARY_SCHEMA_VERSION,
        "name": "agent-validation/policy-pack",
        "status": "completed",
        "conclusion": conclusion,
        "policy_status": status,
        "run_id": policy_report.get("run_id"),
        "session_id": policy_report.get("session_id"),
        "scenario_id": policy_report.get("scenario_id"),
        "runner": policy_report.get("runner"),
        "policy_packs": policy_report.get("policy_packs", []),
        "output": {
            "title": _title(status, scenario_name),
            "summary": _summary(
                status=status,
                findings=findings,
                patch_hints=patch_hints,
                incident=incident,
            ),
            "incident": incident,
        },
        "annotations": annotations,
        "repair_hints": [
            {
                "policy_id": hint["policy_id"],
                "root_cause": hint["root_cause"],
                "guardrails": hint["guardrails"],
            }
            for hint in patch_hints.get("hints", [])
        ],
        "artifact_refs": {
            "trace": "trace.json",
            "policy_report": "policy_report.json",
            "patch_hints": "patch_hints.json",
            "state_diff": "state_diff.json",
        },
    }


def build_github_check_summary_markdown(check_summary: dict[str, Any]) -> str:
    output = check_summary.get("output", {})
    incident = output.get("incident")
    lines = [
        f"# GitHub Check Summary: {output.get('title', check_summary['name'])}",
        "",
        f"- Check: `{check_summary['name']}`",
        f"- Status: `{check_summary['status']}`",
        f"- Conclusion: `{check_summary['conclusion']}`",
        f"- Policy status: `{check_summary['policy_status']}`",
        f"- Run ID: `{check_summary['run_id']}`",
        f"- Policy packs: `{check_summary.get('policy_packs', [])}`",
        "",
        "## Summary",
        "",
        str(output.get("summary", "")),
        "",
    ]

    if incident:
        lines.extend(
            [
                "## Incident Card",
                "",
                str(incident.get("title", "Duplicate side effect detected.")),
                "",
                f"- Stripe event: `{incident.get('stripe_event_id')}`",
                f"- Event type: `{incident.get('stripe_event_type')}`",
                f"- Deliveries observed: `{incident.get('stripe_deliveries')}`",
                f"- Required guardrail: {incident.get('required_guardrail')}",
                "",
                "| Signal | Expected | Observed |",
                "| --- | ---: | ---: |",
                (
                    "| Stripe logical event | "
                    f"{incident['expected']['logical_stripe_events']} | "
                    f"{incident['observed']['stripe_deliveries']} deliveries |"
                ),
                (
                    "| Slack billing alerts | "
                    f"{incident['expected']['slack_billing_alerts']} | "
                    f"{incident['observed']['slack_billing_alerts']} |"
                ),
                (
                    "| GitHub recovery checks | "
                    f"{incident['expected']['github_recovery_checks']} | "
                    f"{incident['observed']['github_recovery_checks']} |"
                ),
                "",
            ]
        )

    annotations = check_summary.get("annotations", [])
    lines.extend(["## Annotations", ""])
    if not annotations:
        lines.append("No policy annotations were generated.")
    else:
        for annotation in annotations:
            lines.extend(
                [
                    f"### {annotation['title']}",
                    "",
                    f"- Level: `{annotation['annotation_level']}`",
                    f"- Path: `{annotation['path']}`",
                    f"- Message: {annotation['message']}",
                    f"- Severity: `{annotation.get('raw_details', {}).get('severity')}`",
                    "- Raw evidence: see `policy_report.json`.",
                    "",
                ]
            )

    repair_hints = check_summary.get("repair_hints", [])
    lines.extend(["", "## Repair Hints", ""])
    if not repair_hints:
        lines.append("No repair hints were generated.")
    else:
        for hint in repair_hints:
            lines.extend(
                [
                    f"### {hint['policy_id']}",
                    "",
                    f"- Root cause: {hint['root_cause']}",
                    "- Guardrails:",
                ]
            )
            for guardrail in hint.get("guardrails", []):
                lines.append(f"  - {guardrail}")
            lines.append("")

    lines.extend(
        [
            "## Artifact Refs",
            "",
            "```json",
            json.dumps(
                check_summary.get("artifact_refs", {}),
                indent=2,
                ensure_ascii=False,
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)
