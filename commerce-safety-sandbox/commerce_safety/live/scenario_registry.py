from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..io import load_yaml


@dataclass(frozen=True)
class ScenarioRegistryError(ValueError):
    code: str
    message: str
    status_code: int = 400

    def __str__(self) -> str:
        return self.message


class ScenarioRegistry:
    """Resolve scenario IDs and paths through a repo-local allowlist."""

    def __init__(self, scenario_root: Path | str = "commerce-safety-sandbox/scenarios"):
        self.scenario_root = Path(scenario_root).resolve()

    def resolve(
        self,
        *,
        scenario_id: str | None = None,
        scenario_path: Path | str | None = None,
    ) -> Path:
        if scenario_id:
            return self._resolve_id(scenario_id)
        if scenario_path:
            return self._resolve_path(Path(scenario_path))
        raise ScenarioRegistryError(
            code="scenario_required",
            message="scenario_id or scenario_path is required",
        )

    def load(
        self,
        *,
        scenario_id: str | None = None,
        scenario_path: Path | str | None = None,
    ) -> tuple[Path, dict[str, Any]]:
        resolved = self.resolve(scenario_id=scenario_id, scenario_path=scenario_path)
        return resolved, load_yaml(resolved)

    def _resolve_id(self, scenario_id: str) -> Path:
        scenario_id = scenario_id.strip()
        for path in sorted(self.scenario_root.rglob("*.yaml")):
            scenario = load_yaml(path)
            aliases = {
                str(scenario.get("id", "")),
                str(scenario.get("name", "")),
                path.stem,
            }
            if scenario_id in aliases:
                return path.resolve()
        raise ScenarioRegistryError(
            code="scenario_not_found",
            message=f"Unknown scenario_id: {scenario_id}",
            status_code=404,
        )

    def _resolve_path(self, scenario_path: Path) -> Path:
        candidate = scenario_path
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        else:
            candidate = candidate.resolve()

        try:
            candidate.relative_to(self.scenario_root)
        except ValueError as error:
            raise ScenarioRegistryError(
                code="scenario_not_allowed",
                message=(
                    "Scenario paths must reference an allowlisted scenario in this repository."
                ),
            ) from error

        if not candidate.is_file():
            raise ScenarioRegistryError(
                code="scenario_not_found",
                message=f"Scenario not found: {scenario_path}",
                status_code=404,
            )
        if candidate.suffix not in {".yaml", ".yml"}:
            raise ScenarioRegistryError(
                code="scenario_not_allowed",
                message="Scenario path must point to a YAML scenario file.",
            )
        return candidate
