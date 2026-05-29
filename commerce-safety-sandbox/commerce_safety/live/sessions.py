from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..io import load_yaml, write_json, write_text
from ..models import to_plain
from ..policies import PolicyEngine, findings_to_plain
from ..reporting import build_markdown_report, build_state_diff
from ..twin import CommerceTwin
from .patch_hints import build_patch_hints, build_patch_hints_markdown


@dataclass
class LiveSession:
    session_id: str
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
    next_event_index: int = 0


class SessionManager:
    def __init__(self, runs_dir: Path | str = Path("runs")):
        self.runs_dir = Path(runs_dir)
        self._sessions: dict[str, LiveSession] = {}

    def create_session(self, scenario_path: Path | str) -> LiveSession:
        scenario_file = Path(scenario_path)
        scenario = load_yaml(scenario_file)
        twin = CommerceTwin(scenario)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        session_id = f"sess_{stamp}_{scenario['id']}_{uuid4().hex[:8]}"
        session = LiveSession(
            session_id=session_id,
            scenario_id=scenario["id"],
            scenario_name=scenario.get("name", scenario["id"]),
            scenario_path=scenario_file,
            scenario=scenario,
            twin=twin,
            initial_state=twin.snapshot_summary(),
            output_path=self.runs_dir / session_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> LiveSession:
        try:
            return self._sessions[session_id]
        except KeyError as error:
            raise KeyError(f"Live session not found: {session_id}") from error

    def list_sessions(self) -> list[dict[str, Any]]:
        return [
            {
                "session_id": session.session_id,
                "scenario_id": session.scenario_id,
                "scenario_name": session.scenario_name,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at,
                "output_path": str(session.output_path),
            }
            for session in self._sessions.values()
        ]

    def get_next_task(self, session_id: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
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
        trace = {
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
        }
        policy_report = {
            "run_id": session.session_id,
            "session_id": session.session_id,
            "scenario_id": session.scenario_id,
            "runner": runner_name,
            "status": status,
            "findings": findings,
        }
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
