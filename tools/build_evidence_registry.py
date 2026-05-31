#!/usr/bin/env python3
"""Build the canonical Failure Intelligence evidence registry.

The source discovery outputs under outputs/ are ignored working artifacts. This
script promotes approved, reviewed evidence into a small repo-visible registry
without carrying raw public comments, handles, avatars, or long page text.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def short_text(value: str, limit: int = 320) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


SCENARIO_DEFAULTS = {
    "duplicate_webhook_fulfillment_variant": {
        "priority": "P0_existing_variant",
        "mechanism": "duplicate_webhook_creates_duplicate_side_effect",
        "policies": ["webhook_dedup_required", "no_duplicate_fulfillment"],
    },
    "timeout_after_commit_retry_variant": {
        "priority": "P0_existing_variant",
        "mechanism": "retry_without_idempotency_creates_duplicate_fulfillment",
        "policies": ["idempotency_required_for_mutating_retries", "no_duplicate_fulfillment"],
    },
    "stale_inventory_oversell_variant": {
        "priority": "P0_existing_variant",
        "mechanism": "stale_inventory_or_sync_lag_causes_oversell",
        "policies": ["no_oversell", "stale_inventory_guard_required"],
    },
    "refund_after_shipment_bypass_variant": {
        "priority": "P0_existing_variant",
        "mechanism": "refund_or_reshipment_policy_bypass",
        "policies": ["refund_after_shipment_requires_approval", "high_value_refund_requires_human_approval"],
    },
    "cancel_after_pick_pack_conflict_variant": {
        "priority": "P0_existing_variant",
        "mechanism": "cancel_after_fulfillment_before_warehouse_processing",
        "policies": ["warehouse_conflict_requires_hold", "no_release_before_resolution"],
    },
}


def normalize_record(item: dict[str, Any], index: int, batch_id: str) -> dict[str, Any]:
    source = item.get("source") or item
    codex_review = item.get("codex_review") or {}
    analysis = item.get("analysis") or {}
    recommended = analysis.get("recommended_scenario") or {}
    source_family = source.get("source_family") or item.get("source_family") or "unknown"
    source_id = source.get("source_id") or item.get("source_id") or f"source_{index:03d}"
    product_use = codex_review.get("product_use") or item.get("product_use") or ""
    mechanism = item.get("mechanism") or analysis.get("mechanism")
    scenario_id = codex_review.get("scenario_id") or item.get("scenario_id") or recommended.get("scenario_id")
    scenario_priority = item.get("scenario_priority") or recommended.get("priority")
    policies = item.get("policies") or recommended.get("policies") or []

    defaults = SCENARIO_DEFAULTS.get(scenario_id or "")
    if defaults:
        scenario_priority = scenario_priority or defaults["priority"]
        # If Codex review overrode the automatic scenario, prefer the reviewed
        # scenario's mechanism so the registry stays analytically consistent.
        if codex_review.get("scenario_id") and codex_review.get("scenario_id") != recommended.get("scenario_id"):
            mechanism = defaults["mechanism"]
            policies = defaults["policies"]
        else:
            mechanism = mechanism or defaults["mechanism"]
            policies = policies or defaults["policies"]

    if not scenario_id and "SCN-003" in product_use:
        scenario_id = "stale_inventory_oversell_variant"
        scenario_priority = "P0_existing_variant"
        mechanism = mechanism or "stale_inventory_or_sync_lag_causes_oversell"
        policies = policies or ["no_oversell", "stale_inventory_guard_required"]
    elif not scenario_id and ("SCN-001" in product_use or "duplicate" in product_use.lower()):
        scenario_id = "duplicate_webhook_fulfillment_variant"
        scenario_priority = "P0_existing_variant"
        mechanism = mechanism or "duplicate_webhook_creates_duplicate_side_effect"
        policies = policies or ["webhook_dedup_required", "no_duplicate_fulfillment"]
    elif not scenario_id and "SCN-004" in product_use:
        scenario_id = "refund_after_shipment_bypass_variant"
        scenario_priority = "P0_existing_variant"
        mechanism = mechanism or "refund_or_reshipment_policy_bypass"
        policies = policies or ["refund_after_shipment_requires_approval", "high_value_refund_requires_human_approval"]
    elif not scenario_id and "SCN-005" in product_use:
        scenario_id = "cancel_after_pick_pack_conflict_variant"
        scenario_priority = "P0_existing_variant"
        mechanism = mechanism or "cancel_after_fulfillment_before_warehouse_processing"
        policies = policies or ["warehouse_conflict_requires_hold", "no_release_before_resolution"]
    elif not scenario_id and "tracking" in product_use.lower():
        scenario_id = "tracking_uploaded_before_first_carrier_scan"
        scenario_priority = "P1_candidate"
        mechanism = mechanism or "tracking_uploaded_before_first_carrier_scan"
        policies = policies or ["customer_notification_requires_carrier_visibility"]

    return {
        "evidence_id": f"FI-{index:04d}",
        "batch_id": item.get("batch_id") or batch_id,
        "source_id": source_id,
        "source_family": source_family,
        "source_url": source.get("url") or item.get("source_url") or "",
        "source_title": source.get("title") or item.get("source_title") or item.get("title") or "",
        "review_status": codex_review.get("review_status") or item.get("review_status") or "approved",
        "mechanism": mechanism,
        "scenario_id": scenario_id,
        "scenario_priority": scenario_priority,
        "policies": policies,
        "product_use": product_use,
        "evidence_summary": short_text(codex_review.get("review_summary") or item.get("evidence_summary") or item.get("codex_review_note") or ""),
        "gate_decision": item.get("gate_decision") or analysis.get("decision"),
        "gate_score": item.get("gate_score") if item.get("gate_score") is not None else analysis.get("score"),
        "fetch_status": source.get("fetch_status") or item.get("fetch_status"),
        "privacy_note": "Registry stores mechanism summaries and public URLs only; no usernames, avatars, or long raw comments.",
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        key = canonical_url(row.get("source_url") or "") or row.get("source_title") or ""
        if key not in merged:
            order.append(key)
        merged[key] = row

    deduped = [merged[key] for key in order]
    for index, row in enumerate(deduped, start=1):
        row["evidence_id"] = f"FI-{index:04d}"
    return deduped


def canonical_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlsplit(value)
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), path, "", ""))


def summary_markdown(rows: list[dict[str, Any]], source_label: str, generated_at: str) -> str:
    by_family = Counter(row["source_family"] for row in rows)
    by_scenario = Counter(row["scenario_id"] or "unmapped" for row in rows)
    by_mechanism = Counter(row["mechanism"] or "manual_review_mapping" for row in rows)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["scenario_id"] or "unmapped"].append(row)

    lines = [
        "# Failure Intelligence Evidence Registry",
        "",
        f"Generated at: `{generated_at}`",
        f"Source file(s): `{source_label}`",
        "",
        "This registry promotes approved public research signals into reusable",
        "Commerce Automation Safety Sandbox scenario evidence. It intentionally",
        "stores short mechanism summaries and source URLs, not raw public comments",
        "or user-identifying details.",
        "",
        "## Counts",
        "",
        f"- Approved evidence records: {len(rows)}",
        f"- Source families: {dict(by_family)}",
        f"- Scenario coverage: {dict(by_scenario)}",
        f"- Mechanisms: {dict(by_mechanism)}",
        "",
        "## Scenario Evidence",
        "",
    ]
    for scenario_id, scenario_rows in sorted(grouped.items()):
        lines.append(f"### {scenario_id}")
        lines.append("")
        for row in scenario_rows:
            lines.append(
                f"- `{row['evidence_id']}` {row['source_title']} "
                f"({row['source_family']})"
            )
            lines.append(f"  - Product use: {row['product_use']}")
            lines.append(f"  - Summary: {row['evidence_summary']}")
            lines.append(f"  - Source: {row['source_url']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build canonical FI evidence registry from approved reviewed candidates.")
    parser.add_argument("--input", required=True, help="approved_scenario_candidates.jsonl")
    parser.add_argument("--existing", default="", help="Optional existing evidence_registry.jsonl to merge and dedupe.")
    parser.add_argument("--output-dir", default="failure_intelligence")
    parser.add_argument("--batch-id", default="")
    args = parser.parse_args()

    source_path = Path(args.input)
    batch_id = args.batch_id or source_path.parent.name
    generated_at = datetime.now(timezone.utc).isoformat()
    approved: list[dict[str, Any]] = []
    source_labels: list[str] = []
    if args.existing:
        existing_path = Path(args.existing)
        approved.extend(load_jsonl(existing_path))
        source_labels.append(str(existing_path))
    approved.extend(load_jsonl(source_path))
    source_labels.append(str(source_path))

    rows = [normalize_record(item, index + 1, batch_id) for index, item in enumerate(approved)]
    rows = dedupe_rows(rows)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "evidence_registry.jsonl", rows)
    (output_dir / "evidence_registry.md").write_text(
        summary_markdown(rows, ", ".join(source_labels), generated_at),
        encoding="utf-8",
    )
    print(json.dumps({"records": len(rows), "output_dir": str(output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
