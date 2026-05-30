from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AmazonCoverage:
    data: dict[str, Any]

    def route_status(self, route_name: str) -> str:
        return str(self.data.get("routes", {}).get(route_name, "stub"))

    def as_dict(self) -> dict[str, Any]:
        return dict(self.data)


def load_amazon_coverage() -> AmazonCoverage:
    path = Path(__file__).with_name("coverage.yaml")
    return AmazonCoverage(yaml.safe_load(path.read_text(encoding="utf-8")))
