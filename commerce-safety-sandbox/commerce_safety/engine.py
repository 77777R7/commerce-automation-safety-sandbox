from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import (
    POLICY_REPORT_SCHEMA_VERSION,
    STATE_DIFF_SCHEMA_VERSION,
    TRACE_SCHEMA_VERSION,
    add_schema_version,
    write_run_manifest,
)
from .io import load_yaml, write_json, write_text
from .models import to_plain
from .policies import PolicyEngine, findings_to_plain
from .reporting import build_markdown_report, build_state_diff
from .runners import get_runner
from .twin import CommerceTwin


def make_run_id(scenario_id: str, runner_name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"run_{stamp}_{scenario_id}_{runner_name}"


def run_scenario(
    scenario_path: Path,
    runner_name: str,
    runs_dir: Path,
) -> dict[str, Any]:
    scenario = load_yaml(scenario_path)
    runner = get_runner(runner_name)
    twin = CommerceTwin(scenario)
    before = twin.snapshot_summary()

    for event in scenario["events"]:
        if event["type"] == "webhook":
            twin.receive_webhook(event)
            runner.handle_webhook(twin, event)
        elif event["type"] == "fulfillment_task":
            twin.receive_fulfillment_task(event)
            runner.handle_fulfillment_task(twin, event)
        elif event["type"] == "inventory_promise_task":
            twin.receive_inventory_promise_task(event)
            runner.handle_inventory_promise_task(twin, event)
        elif event["type"] == "refund_request":
            twin.receive_refund_request(event)
            runner.handle_refund_request(twin, event)
        elif event["type"] == "tracking_upload_task":
            twin.receive_tracking_upload_task(event)
            runner.handle_tracking_upload_task(twin, event)
        elif event["type"] == "cancel_request":
            twin.receive_cancel_request(event)
            runner.handle_cancel_request(twin, event)
        else:
            raise ValueError(f"Unsupported event type: {event['type']}")

    policy_engine = PolicyEngine()
    findings = findings_to_plain(policy_engine.evaluate(twin))
    status = "failed" if findings else "passed"
    if findings:
        for finding in findings:
            twin.add_event(
                actor="policy_engine",
                event="policy_violation_detected",
                message=(
                    f"Policy violation detected: {finding['policy_id']} "
                    f"({finding['severity']})."
                ),
                details=finding,
            )
    else:
        twin.add_event(
            actor="policy_engine",
            event="policy_check_passed",
            message="Policy check passed with no violations.",
            details={"status": "passed"},
        )

    after = twin.snapshot_summary()
    state_diff = build_state_diff(
        before,
        after,
        high_value_refund_threshold=float(
            scenario.get("approval_rules", {}).get("high_value_refund_threshold", 100)
        ),
    )
    state_diff = add_schema_version(state_diff, STATE_DIFF_SCHEMA_VERSION)
    run_id = make_run_id(scenario["id"], runner_name)
    run_path = runs_dir / run_id

    trace = add_schema_version(
        {
            "run_id": run_id,
            "scenario_id": scenario["id"],
            "scenario_name": scenario.get("name", scenario["id"]),
            "runner": runner_name,
            "status": status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "initial_state": before,
            "final_state": after,
            "timeline": [to_plain(event) for event in twin.timeline],
        },
        TRACE_SCHEMA_VERSION,
    )
    policy_report = add_schema_version(
        {
            "run_id": run_id,
            "scenario_id": scenario["id"],
            "runner": runner_name,
            "status": status,
            "findings": findings,
        },
        POLICY_REPORT_SCHEMA_VERSION,
    )
    report = build_markdown_report(
        run_id=run_id,
        scenario=scenario,
        runner_name=runner_name,
        status=status,
        findings=findings,
        state_diff=state_diff,
    )

    write_text(run_path / "scenario.yaml", scenario_path.read_text(encoding="utf-8"))
    write_json(run_path / "trace.json", trace)
    write_json(run_path / "policy_report.json", policy_report)
    write_json(run_path / "state_diff.json", state_diff)
    write_text(run_path / "report.md", report)
    write_run_manifest(
        run_path=run_path,
        run_id=run_id,
        scenario_id=scenario["id"],
        scenario_name=scenario.get("name", scenario["id"]),
        runner=runner_name,
        status=status,
        artifacts=[
            "scenario.yaml",
            "trace.json",
            "policy_report.json",
            "state_diff.json",
            "report.md",
        ],
    )

    return {
        "run_id": run_id,
        "run_path": str(run_path),
        "status": status,
        "findings": findings,
    }
