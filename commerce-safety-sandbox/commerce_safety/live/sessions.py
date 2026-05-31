from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from ..artifacts import (
    POLICY_REPORT_SCHEMA_VERSION,
    STATE_DIFF_SCHEMA_VERSION,
    TRACE_SCHEMA_VERSION,
    add_schema_version,
    write_run_manifest,
)
from ..io import write_json, write_text
from ..models import to_plain
from ..policies import PolicyEngine, findings_to_plain
from ..reporting import build_markdown_report, build_state_diff
from ..twin import CommerceTwin
from .patch_hints import (
    build_agent_summary_markdown,
    build_failure_explain_markdown,
    build_patch_hints,
    build_patch_hints_markdown,
)
from .scenario_registry import ScenarioRegistry


class SessionNotFoundError(Exception):
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Live session not found: {session_id}")


@dataclass
class LiveSession:
    session_id: str
    workspace_id: str
    scenario_id: str
    scenario_name: str
    scenario_path: Path
    scenario: dict[str, Any]
    twin: CommerceTwin
    initial_state: dict[str, Any]
    output_path: Path
    status: str = "open"
    created_at: str = ""
    completed_at: str | None = None
    created_by: str | None = None
    ttl_expires_at: str | None = None
    retention_expires_at: str | None = None
    next_event_index: int = 0
    lock: Any = field(default_factory=RLock, repr=False, compare=False)
    amazon_feeds: dict[str, dict[str, Any]] = field(default_factory=dict)
    next_amazon_feed: int = 1


class SessionManager:
    def __init__(
        self,
        runs_dir: Path | str = Path("runs"),
        *,
        scenario_registry: ScenarioRegistry | None = None,
    ):
        self.runs_dir = Path(runs_dir)
        self.scenario_registry = scenario_registry or ScenarioRegistry()
        self._sessions: dict[str, LiveSession] = {}
        self._lock = RLock()

    def create_session(
        self,
        scenario_path: Path | str | None = None,
        *,
        scenario_id: str | None = None,
        workspace_id: str = "local",
        created_by: str | None = None,
        ttl_seconds: int | None = None,
        retention_days: int | None = None,
    ) -> LiveSession:
        scenario_file, scenario = self.scenario_registry.load(
            scenario_id=scenario_id,
            scenario_path=scenario_path,
        )
        twin = CommerceTwin(scenario)
        now = datetime.now(timezone.utc)
        stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
        session_id = f"sess_{stamp}_{scenario['id']}_{uuid4().hex[:8]}"
        output_path = self.runs_dir / session_id
        if workspace_id != "local":
            output_path = self.runs_dir / workspace_id / session_id
        session = LiveSession(
            session_id=session_id,
            workspace_id=workspace_id,
            scenario_id=scenario["id"],
            scenario_name=scenario.get("name", scenario["id"]),
            scenario_path=scenario_file,
            scenario=scenario,
            twin=twin,
            initial_state=twin.snapshot_summary(),
            output_path=output_path,
            created_at=now.isoformat(),
            created_by=created_by,
            ttl_expires_at=(
                (now + timedelta(seconds=ttl_seconds)).isoformat()
                if ttl_seconds is not None
                else None
            ),
            retention_expires_at=(
                (now + timedelta(days=retention_days)).isoformat()
                if retention_days is not None
                else None
            ),
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> LiveSession:
        try:
            with self._lock:
                return self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFoundError(session_id) from error

    def list_sessions(self, *, workspace_id: str | None = None) -> list[dict[str, Any]]:
        return [
            {
                "session_id": session.session_id,
                "workspace_id": session.workspace_id,
                "scenario_id": session.scenario_id,
                "scenario_name": session.scenario_name,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at,
                "ttl_expires_at": session.ttl_expires_at,
                "retention_expires_at": session.retention_expires_at,
                "output_path": str(session.output_path),
            }
            for session in self._sessions.values()
            if workspace_id is None or session.workspace_id == workspace_id
        ]

    def get_next_task(self, session_id: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
        with session.lock:
            events = session.scenario.get("events", [])
            if session.next_event_index >= len(events):
                return None

            event = deepcopy(events[session.next_event_index])
            session.next_event_index += 1
            self._record_scenario_event(session, event)
            return event

    def complete_session(
        self,
        session_id: str,
        *,
        runner_name: str = "external_agent",
    ) -> dict[str, Any]:
        session = self.get_session(session_id)
        with session.lock:
            findings = findings_to_plain(PolicyEngine().evaluate(session.twin))
            status = "failed" if findings else "passed"
            session.status = status
            session.completed_at = datetime.now(timezone.utc).isoformat()

            if findings:
                for finding in findings:
                    session.twin.add_event(
                        actor="policy_engine",
                        event="policy_violation_detected",
                        message=(
                            f"Policy violation detected: {finding['policy_id']} "
                            f"({finding['severity']})."
                        ),
                        details=finding,
                    )
            else:
                session.twin.add_event(
                    actor="policy_engine",
                    event="policy_check_passed",
                    message="Policy check passed with no violations.",
                    details={"status": "passed"},
                )

            final_state = session.twin.snapshot_summary()
            state_diff = build_state_diff(
                session.initial_state,
                final_state,
                high_value_refund_threshold=float(
                    session.scenario.get("approval_rules", {}).get(
                        "high_value_refund_threshold",
                        100,
                    )
                ),
            )
            state_diff = add_schema_version(state_diff, STATE_DIFF_SCHEMA_VERSION)
            trace = add_schema_version(
                {
                    "run_id": session.session_id,
                    "session_id": session.session_id,
                    "scenario_id": session.scenario_id,
                    "scenario_name": session.scenario_name,
                    "runner": runner_name,
                    "status": status,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "initial_state": session.initial_state,
                    "final_state": final_state,
                    "timeline": [to_plain(event) for event in session.twin.timeline],
                },
                TRACE_SCHEMA_VERSION,
            )
            policy_report = add_schema_version(
                {
                    "run_id": session.session_id,
                    "session_id": session.session_id,
                    "scenario_id": session.scenario_id,
                    "runner": runner_name,
                    "status": status,
                    "findings": findings,
                },
                POLICY_REPORT_SCHEMA_VERSION,
            )
            report = build_markdown_report(
                run_id=session.session_id,
                scenario=session.scenario,
                runner_name=runner_name,
                status=status,
                findings=findings,
                state_diff=state_diff,
            )
            patch_hints = build_patch_hints(
                run_id=session.session_id,
                scenario=session.scenario,
                status=status,
                findings=findings,
            )

            write_text(
                session.output_path / "scenario.yaml",
                session.scenario_path.read_text(encoding="utf-8"),
            )
            write_json(session.output_path / "trace.json", trace)
            write_json(session.output_path / "policy_report.json", policy_report)
            write_json(session.output_path / "state_diff.json", state_diff)
            write_text(session.output_path / "report.md", report)
            write_json(session.output_path / "patch_hints.json", patch_hints)
            write_text(
                session.output_path / "patch_hints.md",
                build_patch_hints_markdown(patch_hints),
            )
            write_text(
                session.output_path / "agent_summary.md",
                build_agent_summary_markdown(
                    patch_hints=patch_hints,
                    findings=findings,
                ),
            )
            write_text(
                session.output_path / "failure_explain.md",
                build_failure_explain_markdown(
                    patch_hints=patch_hints,
                    findings=findings,
                    trace=trace,
                    state_diff=state_diff,
                ),
            )
            write_run_manifest(
                run_path=session.output_path,
                run_id=session.session_id,
                session_id=session.session_id,
                workspace_id=session.workspace_id,
                scenario_id=session.scenario_id,
                scenario_name=session.scenario_name,
                runner=runner_name,
                status=status,
                retention_expires_at=session.retention_expires_at,
                artifacts=[
                    "scenario.yaml",
                    "trace.json",
                    "policy_report.json",
                    "state_diff.json",
                    "report.md",
                    "patch_hints.json",
                    "patch_hints.md",
                    "agent_summary.md",
                    "failure_explain.md",
                ],
            )

        return {
            "run_id": session.session_id,
            "session_id": session.session_id,
            "run_path": str(session.output_path),
            "status": status,
            "findings": findings,
        }

    def _record_scenario_event(
        self,
        session: LiveSession,
        event: dict[str, Any],
    ) -> None:
        event_type = event["type"]
        if event_type == "webhook":
            session.twin.receive_webhook(event)
        elif event_type == "fulfillment_task":
            session.twin.receive_fulfillment_task(event)
        elif event_type == "inventory_promise_task":
            session.twin.receive_inventory_promise_task(event)
        elif event_type == "refund_request":
            session.twin.receive_refund_request(event)
        elif event_type == "cancel_request":
            session.twin.receive_cancel_request(event)
        else:
            raise ValueError(f"Unsupported event type: {event_type}")
