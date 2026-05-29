#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "== P0 scenario smoke gates =="
./tools/smoke_week1.sh
./tools/smoke_scn002.sh
./tools/smoke_scn003.sh
./tools/smoke_scn004.sh
./tools/smoke_scn005.sh

echo "== Regression smoke gate =="
./tools/smoke_stage3_regression.sh

echo "== Offline Audit smoke gates =="
./tools/smoke_stage4_offline_audit.sh
./tools/smoke_stage4_offline_audit_xlsx.sh
./tools/smoke_stage4_offline_audit_clean.sh

echo "== Demo pack generation and verification =="
python3 tools/generate_demo_pack.py
python3 - <<'PY'
from pathlib import Path

root = Path("demo_pack")
scenarios = [
    "SCN-001_duplicate_webhook_fulfillment",
    "SCN-002_timeout_after_commit_retry",
    "SCN-003_stale_inventory_oversell",
    "SCN-004_refund_after_shipment_bypass",
    "SCN-005_cancel_after_pick_pack_conflict",
]
top_level = [
    "README.md",
    "executive_summary.md",
    "sales_one_pager.md",
    "demo_walkthrough.md",
]
scenario_files = [
    "bad_report.md",
    "good_report.md",
    "trace_summary.md",
    "policy_findings.md",
    "scenario.yaml",
]
raw_artifacts = [
    "trace.json",
    "policy_report.json",
    "state_diff.json",
    "report.md",
]

missing = []
for filename in top_level:
    if not (root / filename).is_file():
        missing.append(str(root / filename))

for scenario in scenarios:
    base = root / scenario
    for filename in scenario_files:
        if not (base / filename).is_file():
            missing.append(str(base / filename))
    for side in ("bad", "good"):
        for filename in raw_artifacts:
            if not (base / side / filename).is_file():
                missing.append(str(base / side / filename))

if missing:
    raise SystemExit("Missing demo pack files:\n" + "\n".join(missing))

print("Demo pack verification passed.")
PY

echo "All MVP smoke gates passed."
