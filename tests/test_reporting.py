from __future__ import annotations

from pathlib import Path

from commerce_safety.engine import run_scenario
from commerce_safety.reporting import build_state_diff


ROOT = Path(__file__).resolve().parents[1]


def test_state_diff_flags_duplicate_fulfillment_and_excess_reservation(
    tmp_path: Path,
) -> None:
    result = run_scenario(
        scenario_path=ROOT / "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml",
        runner_name="bad_runner",
        runs_dir=tmp_path,
    )
    state_diff_path = Path(result["run_path"]) / "state_diff.json"

    import json

    state_diff = json.loads(state_diff_path.read_text(encoding="utf-8"))

    assert state_diff["accident_signals"]["duplicate_fulfillment"] is True
    assert state_diff["accident_signals"]["duplicated_reserved_inventory"] is True
    assert state_diff["after"]["fulfillments"] == 2


def test_report_places_business_summary_before_json_evidence(tmp_path: Path) -> None:
    result = run_scenario(
        scenario_path=ROOT
        / "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml",
        runner_name="bad_runner",
        runs_dir=tmp_path,
    )
    report = (Path(result["run_path"]) / "report.md").read_text(encoding="utf-8")

    business_index = report.index("## Business Risk Summary")
    findings_index = report.index("## Findings")
    evidence_index = report.index("```json")

    assert business_index < findings_index < evidence_index
    assert "- Risk:" in report
    assert "- Possible impact:" in report
    assert "- Recommended control:" in report


def test_build_state_diff_uses_order_quantity_for_expected_reservation() -> None:
    before = {
        "counts": {
            "fulfillments": 0,
            "reservations": 0,
            "fulfillment_promises": 0,
            "refunds": 0,
            "approval_requests": 0,
            "inventory_releases": 0,
            "workflow_holds": 0,
            "warehouse_cancellation_requests": 0,
            "reserved_inventory": {"sku_bulk": 0},
        },
        "orders": {
            "order_bulk": {
                "line_items": [{"sku": "sku_bulk", "quantity": 2}],
            }
        },
        "reservations": [],
        "fulfillments": [],
    }
    after = {
        **before,
        "counts": {
            **before["counts"],
            "reserved_inventory": {"sku_bulk": 2},
        },
    }

    state_diff = build_state_diff(before, after)

    assert state_diff["expected"]["reserved_inventory"]["sku_bulk"] == 2
    assert state_diff["accident_signals"]["duplicated_reserved_inventory"] is False
