from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import to_plain
from ..twins.github import GitHubTwin
from ..twins.slack import SlackTwin
from ..twins.stripe import StripeTwin


@dataclass
class ToolCallEvent:
    step: int
    actor: str
    service: str
    operation: str
    request: dict[str, Any]
    response: dict[str, Any]
    fault: str | None = None
    state_before: dict[str, Any] = field(default_factory=dict)
    state_after: dict[str, Any] = field(default_factory=dict)
    source_event_id: str | None = None


@dataclass
class StateSnapshotTwin:
    service: str
    state: dict[str, Any] = field(default_factory=dict)

    def snapshot_summary(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "state": to_plain(self.state),
            "counts": {},
        }

    def compact_state(self) -> dict[str, Any]:
        return self.snapshot_summary()


@dataclass
class TwinBundle:
    twins: dict[str, Any]

    @classmethod
    def from_legacy_commerce(cls, commerce_twin: Any) -> "TwinBundle":
        return cls(
            twins={
                "commerce": commerce_twin,
                "stripe": StripeTwin(getattr(commerce_twin, "scenario", None)),
                "slack": SlackTwin(getattr(commerce_twin, "scenario", None)),
                "github": GitHubTwin(getattr(commerce_twin, "scenario", None)),
            }
        )

    def __getitem__(self, service: str) -> Any:
        return self.twins[service]

    @property
    def commerce(self) -> Any:
        return self.twins["commerce"]

    @property
    def stripe(self) -> Any:
        return self.twins["stripe"]

    @property
    def slack(self) -> Any:
        return self.twins["slack"]

    @property
    def github(self) -> Any:
        return self.twins["github"]

    def snapshot_summary(self) -> dict[str, Any]:
        return {
            service: twin.snapshot_summary()
            for service, twin in self.twins.items()
            if hasattr(twin, "snapshot_summary")
        }


@dataclass
class SandboxEnvironment:
    twins: TwinBundle
    events: list[ToolCallEvent] = field(default_factory=list)

    @classmethod
    def from_legacy_commerce(cls, commerce_twin: Any) -> "SandboxEnvironment":
        return cls(twins=TwinBundle.from_legacy_commerce(commerce_twin))

    @property
    def commerce(self) -> Any:
        return self.twins.commerce

    def snapshot_summary(self) -> dict[str, Any]:
        return self.twins.snapshot_summary()

    def record_tool_call(
        self,
        *,
        actor: str,
        service: str,
        operation: str,
        request: dict[str, Any],
        response: dict[str, Any],
        fault: str | None = None,
        state_before: dict[str, Any] | None = None,
        state_after: dict[str, Any] | None = None,
        source_event_id: str | None = None,
    ) -> ToolCallEvent:
        event = ToolCallEvent(
            step=len(self.events) + 1,
            actor=actor,
            service=service,
            operation=operation,
            request=to_plain(request),
            response=to_plain(response),
            fault=fault,
            state_before=state_before or {},
            state_after=state_after or {},
            source_event_id=source_event_id,
        )
        self.events.append(event)
        return event
