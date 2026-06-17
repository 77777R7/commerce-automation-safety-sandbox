from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import load_yaml


DEFAULT_POLICY_PACK_ROOT = Path(__file__).resolve().parents[2] / "policy_packs"


@dataclass(frozen=True)
class PolicyPackManifest:
    pack_id: str
    path: Path
    raw: dict[str, Any]

    @property
    def policy_ids(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.raw.get("policy_ids", []))

    @property
    def applicable_scenarios(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.raw.get("applicable_scenarios", []))

    @property
    def required_artifacts(self) -> tuple[str, ...]:
        artifact_contract = self.raw.get("artifact_contract", {})
        return tuple(
            str(item) for item in artifact_contract.get("required_artifacts", [])
        )


class PolicyPackRegistry:
    def __init__(
        self,
        root: Path | str = DEFAULT_POLICY_PACK_ROOT,
    ):
        self.root = Path(root)
        self._manifests = self._load_manifests()

    def ids(self) -> tuple[str, ...]:
        return tuple(self._manifests)

    def get(self, pack_id: str) -> PolicyPackManifest:
        try:
            return self._manifests[pack_id]
        except KeyError as error:
            raise ValueError(f"Unknown policy pack: {pack_id}") from error

    def _load_manifests(self) -> dict[str, PolicyPackManifest]:
        manifests: dict[str, PolicyPackManifest] = {}
        for path in sorted(self.root.glob("*.yaml")):
            data = load_yaml(path)
            pack_id = str(data.get("id", "")).strip()
            if not pack_id:
                raise ValueError(f"Policy pack manifest missing id: {path}")
            if pack_id in manifests:
                raise ValueError(f"Duplicate policy pack id: {pack_id}")
            manifests[pack_id] = PolicyPackManifest(
                pack_id=pack_id,
                path=path,
                raw=data,
            )
        if not manifests:
            raise ValueError(f"No policy pack manifests found in {self.root}")
        return manifests
