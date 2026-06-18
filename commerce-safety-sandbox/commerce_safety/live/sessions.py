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
from ..reporting import (
    build_environment_state_diff,
    build_markdown_report,
    build_saas_markdown_report,
    build_state_diff,
    is_saas_scenario,
)
from ..twin import CommerceTwin
from .environment import SandboxEnvironment, ToolCallEvent
from .github_check_summary import (
    build_github_check_summary,
    build_github_check_summary_markdown,
)
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
    environment: SandboxEnvironment
    initial_state: dict[str, Any]
    initial_environment_state: dict[str, Any]
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

    @property
    def twin(self) -> CommerceTwin:
        return self.environment.commerce

    @property
    def events(self) -> list[ToolCallEvent]:
        return self.environment.events


SAAS_TRACE_SERVICES = ("stripe", "slack", "github")


def _environment_source_state(
    snapshot: dict[str, Any],
    *,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    if not is_saas_scenario(scenario):
        return deepcopy(snapshot)
    return {
        service: deepcopy(snapshot[service])
        for service in SAAS_TRACE_SERVICES
        if service in snapshot
    }


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
        environment = SandboxEnvironment.from_legacy_commerce(twin)
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
            environment=environment,
            initial_state=twin.snapshot_summary(),
            initial_environment_state=environment.snapshot_summary(),
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
                "ttl_expired": self._ttl_expired(session),
                "retention_expires_at": session.retention_expires_at,
                "output_path": str(session.output_path),
            }
            for session in self._sessions.values()
            if workspace_id is None or session.workspace_id == workspace_id
        ]

    def session_status(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        with session.lock:
            total_tasks = len(session.scenario.get("events", []))
            return {
                "session_id": session.session_id,
                "workspace_id": session.workspace_id,
                "scenario_id": session.scenario_id,
                "scenario_name": session.scenario_name,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at,
                "ttl_expires_at": session.ttl_expires_at,
                "ttl_expired": self._ttl_expired(session),
                "retention_expires_at": session.retention_expires_at,
                "next_event_index": session.next_event_index,
                "tasks_total": total_tasks,
                "tasks_remaining": max(total_tasks - session.next_event_index, 0),
                "output_path": str(session.output_path),
            }

    def reset_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        with session.lock:
            scenario_file, scenario = self.scenario_registry.load(
                scenario_id=session.scenario_id,
            )
            twin = CommerceTwin(scenario)
            environment = SandboxEnvironment.from_legacy_commerce(twin)
            session.scenario_path = scenario_file
            session.scenario = scenario
            session.environment = environment
            session.initial_state = twin.snapshot_summary()
            session.initial_environment_state = environment.snapshot_summary()
            session.status = "open"
            session.completed_at = None
            session.next_event_index = 0
            session.amazon_feeds = {}
            session.next_amazon_feed = 1
        return self.session_status(session_id)

    def teardown_session(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            return {
                "session_id": session_id,
                "workspace_id": "unknown",
                "scenario_id": "unknown",
                "status": "torn_down",
                "output_path": "",
            }
        return {
            "session_id": session.session_id,
            "workspace_id": session.workspace_id,
            "scenario_id": session.scenario_id,
            "status": "torn_down",
            "output_path": str(session.output_path),
        }

    def _ttl_expired(self, session: LiveSession) -> bool:
        if session.ttl_expires_at is None:
            return False
        return datetime.now(timezone.utc) >= datetime.fromisoformat(
            session.ttl_expires_at
        )

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
            policy_engine = PolicyEngine()
            policy_packs = list(policy_engine.resolve_policy_packs(session.scenario))
            findings = findings_to_plain(
                policy_engine.evaluate_environment(
                    session.environment,
                    scenario=session.scenario,
                )
            )
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

            saas_scenario = is_saas_scenario(session.scenario)
            final_state = session.twin.snapshot_summary()
            final_environment_state = session.environment.snapshot_summary()
            event_ledger = [to_plain(event) for event in session.environment.events]
            trace_initial_environment_state = _environment_source_state(
                session.initial_environment_state,
                scenario=session.scenario,
            )
            trace_final_environment_state = _environment_source_state(
                final_environment_state,
                scenario=session.scenario,
            )
            trace_initial_state = (
                trace_initial_environment_state if saas_scenario else session.initial_state
            )
            trace_final_state = (
                trace_final_environment_state if saas_scenario else final_state
            )
            if saas_scenario:
                state_diff = build_environment_state_diff(
                    trace_initial_environment_state,
                    trace_final_environment_state,
                    events=event_ledger,
                )
            else:
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
                    "state_source": "environment" if saas_scenario else "commerce_twin",
                    "source_of_truth": {
                        "kind": "sandbox_environment"
                        if saas_scenario
                        else "commerce_twin",
                        "services": list(SAAS_TRACE_SERVICES)
                        if saas_scenario
                        else ["commerce"],
                    },
                    "initial_state": trace_initial_state,
                    "final_state": trace_final_state,
                    "initial_environment_state": trace_initial_environment_state,
                    "final_environment_state": trace_final_environment_state,
                    "environment_state": trace_final_environment_state,
                    "event_ledger": event_ledger,
                    "timeline_source": (
                        "legacy_session_timeline"
                        if saas_scenario
                        else "commerce_twin_timeline"
                    ),
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
                    "evaluation_source": (
                        "sandbox_environment"
                        if saas_scenario
                        else "commerce_twin"
                    ),
                    "policy_packs": policy_packs,
                    "findings": findings,
                },
                POLICY_REPORT_SCHEMA_VERSION,
            )
            if saas_scenario:
                report = build_saas_markdown_report(
                    run_id=session.session_id,
                    scenario=session.scenario,
                    runner_name=runner_name,
                    status=status,
                    findings=findings,
                    state_diff=state_diff,
                )
            else:
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
            github_check_summary = build_github_check_summary(
                policy_report=policy_report,
                patch_hints=patch_hints,
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
                    state_diff=state_diff,
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
            write_json(
                session.output_path / "github_check_summary.json",
                github_check_summary,
            )
            write_text(
                session.output_path / "github_check_summary.md",
                build_github_check_summary_markdown(github_check_summary),
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
                    "github_check_summary.json",
                    "github_check_summary.md",
                ],
            )

        return {
            "run_id": session.session_id,
            "session_id": session.session_id,
            "run_path": str(session.output_path),
            "status": status,
            "policy_packs": policy_packs,
            "findings": findings,
        }

    def _record_scenario_event(
        self,
        session: LiveSession,
        event: dict[str, Any],
    ) -> None:
        event_type = event["type"]
        state_before = session.environment.snapshot_summary()
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
        elif event_type in {"billing_upgrade_task", "saas_validation_task"}:
            session.twin.add_event(
                actor="scenario",
                event=f"{event_type}_received",
                message=f"SaaS validation task {event['id']} received.",
                details=deepcopy(event),
            )
        else:
            raise ValueError(f"Unsupported event type: {event_type}")
        session.environment.record_tool_call(
            actor="scenario",
            service="scenario",
            operation=event_type,
            request=event,
            response={"recorded": True},
            fault=event.get("fault", {}).get("type"),
            state_before=state_before,
            state_after=session.environment.snapshot_summary(),
            source_event_id=event.get("id"),
        )
