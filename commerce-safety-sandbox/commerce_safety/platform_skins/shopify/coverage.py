from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ShopifyCoverage:
    skin: str
    stage: str
    webhooks: dict[str, dict[str, Any]]
    mutations: dict[str, dict[str, Any]]
    routes: dict[str, dict[str, Any]]
    actions: dict[str, dict[str, Any]]
    supported_scenarios: list[str]
    binding: dict[str, Any]

    def is_supported_webhook(self, topic: str) -> bool:
        return self.webhooks.get(topic, {}).get("status") == "stateful"

    def mutation_status(self, mutation_name: str) -> str:
        return self.mutations.get(mutation_name, {}).get("status", "unsupported")

    def route_status(self, route_name: str) -> str:
        return self.routes.get(route_name, {}).get("status", "unsupported")

    def action_status(self, action_name: str) -> str:
        return self.actions.get(action_name, {}).get("status", "unsupported")

    def as_dict(self) -> dict[str, Any]:
        return {
            "skin": self.skin,
            "stage": self.stage,
            "supported_scenarios": self.supported_scenarios,
            "webhooks": {
                topic: spec.get("status", "unsupported")
                for topic, spec in self.webhooks.items()
            },
            "mutations": {
                name: spec.get("status", "unsupported")
                for name, spec in self.mutations.items()
            },
            "routes": {
                name: spec.get("status", "unsupported")
                for name, spec in self.routes.items()
            },
            "actions": {
                name: spec.get("status", "unsupported")
                for name, spec in self.actions.items()
            },
            "binding_principle": self.binding.get("principle"),
        }


def _load_yaml(filename: str) -> dict[str, Any]:
    path = Path(__file__).with_name(filename)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{filename} must contain a YAML mapping")
    return data


def load_shopify_coverage() -> ShopifyCoverage:
    coverage = _load_yaml("coverage.yaml")
    binding = _load_yaml("binding.yaml")
    return ShopifyCoverage(
        skin=str(coverage["skin"]),
        stage=str(coverage["stage"]),
        webhooks=dict(coverage.get("webhooks", {})),
        mutations=dict(coverage.get("mutations", {})),
        routes=dict(coverage.get("routes", {})),
        actions=dict(coverage.get("actions", {})),
        supported_scenarios=list(coverage.get("supported_scenarios", [])),
        binding=binding,
    )
