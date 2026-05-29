#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-offline-audit-xlsx.XXXXXX")"
SAMPLE_DIR="$ROOT_DIR/commerce-safety-sandbox/offline_samples/p0_audit"
WORKBOOK="$OUTPUT_DIR/p0_audit.xlsx"
CLI="$ROOT_DIR/commerce-safety"

cleanup() {
  rm -rf "$OUTPUT_DIR"
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing file: $path"
}

echo "Building Stage 4 Excel sample workbook..."
python3 "$ROOT_DIR/tools/build_stage4_xlsx_sample.py" "$SAMPLE_DIR" "$WORKBOOK" || fail "could not build xlsx sample"
assert_file "$WORKBOOK"

echo "Running Stage 4 Excel offline audit smoke check..."
audit_output="$("$CLI" offline-audit \
  --orders "$WORKBOOK" \
  --orders-sheet Orders \
  --inventory "$WORKBOOK" \
  --inventory-sheet Inventory \
  --fulfillments "$WORKBOOK" \
  --fulfillments-sheet Fulfillments \
  --refunds "$WORKBOOK" \
  --refunds-sheet Refunds \
  --mapping "$SAMPLE_DIR/mapping.yaml" \
  --output-dir "$OUTPUT_DIR" 2>&1)"
audit_exit=$?
echo "$audit_output"
[[ "$audit_exit" -eq 1 ]] || fail "offline audit should exit 1 when policy findings exist, got $audit_exit"

audit_id="$(printf '%s\n' "$audit_output" | awk -F': ' '/^Audit ID:/ {print $2}')"
[[ -n "$audit_id" ]] || fail "could not parse audit id"
audit_dir="$OUTPUT_DIR/$audit_id"

assert_file "$audit_dir/manifest.json"
assert_file "$audit_dir/data_quality.json"
assert_file "$audit_dir/state_reconstruction.json"
assert_file "$audit_dir/policy_report.json"
assert_file "$audit_dir/report.md"
assert_file "$audit_dir/redacted_inputs/orders.csv"

python3 - "$audit_dir" <<'PY'
import csv
import json
import pathlib
import sys

audit_dir = pathlib.Path(sys.argv[1])
manifest = json.loads((audit_dir / "manifest.json").read_text())
quality = json.loads((audit_dir / "data_quality.json").read_text())
state = json.loads((audit_dir / "state_reconstruction.json").read_text())
policy = json.loads((audit_dir / "policy_report.json").read_text())

expected_sheets = {
    "orders": "Orders",
    "inventory": "Inventory",
    "fulfillments": "Fulfillments",
    "refunds": "Refunds",
}
if manifest["input_sheets"] != expected_sheets:
    raise SystemExit("manifest should preserve worksheet mapping")

for dataset, sheet in expected_sheets.items():
    profile = quality["datasets"][dataset]
    if profile["source_format"] != "xlsx":
        raise SystemExit(f"{dataset} should be read as xlsx")
    if profile["sheet_name"] != sheet:
        raise SystemExit(f"{dataset} should preserve sheet name")

policy_ids = {finding["policy_id"] for finding in policy["findings"]}
required = {
    "offline_duplicate_fulfillment",
    "offline_negative_available_inventory",
    "offline_paid_order_inventory_shortage",
    "offline_refund_after_shipment_without_approval",
    "offline_cancel_after_pick_pack_conflict",
}
missing = required - policy_ids
if missing:
    raise SystemExit(f"missing policy findings: {sorted(missing)}")

if state["inventory"]["sku_over"]["available"] != -1:
    raise SystemExit("expected sku_over available inventory to be -1")

with (audit_dir / "redacted_inputs" / "orders.csv").open(newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))
if any("@" in row["buyer_id"] for row in rows):
    raise SystemExit("buyer identifiers should be redacted from xlsx audit output")
PY

echo "Stage 4 Excel offline audit smoke gate passed."
