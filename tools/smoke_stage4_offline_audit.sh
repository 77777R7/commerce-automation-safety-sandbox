#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-offline-audit.XXXXXX")"
SAMPLE_DIR="$ROOT_DIR/commerce-safety-sandbox/offline_samples/p0_audit"
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

echo "Running Stage 4 offline audit smoke check..."
audit_output="$("$CLI" offline-audit \
  --orders "$SAMPLE_DIR/orders.csv" \
  --inventory "$SAMPLE_DIR/inventory.csv" \
  --fulfillments "$SAMPLE_DIR/fulfillments.csv" \
  --refunds "$SAMPLE_DIR/refunds.csv" \
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
assert_file "$audit_dir/redacted_inputs/inventory.csv"
assert_file "$audit_dir/redacted_inputs/fulfillments.csv"
assert_file "$audit_dir/redacted_inputs/refunds.csv"

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
report = (audit_dir / "report.md").read_text()

if manifest["audit_id"] != audit_dir.name:
    raise SystemExit("manifest should preserve audit id")

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

if policy["risk_score"] <= 0:
    raise SystemExit("risk score should be positive for risky sample")
if policy["status"] != "failed":
    raise SystemExit("risky sample should fail policy audit")
for finding in policy["findings"]:
    for key in [
        "policy_id",
        "severity",
        "status",
        "evidence",
        "business_impact",
        "recommendation",
    ]:
        if key not in finding:
            raise SystemExit(f"finding missing structured key: {key}")
if quality["datasets"]["orders"]["row_count"] != 4:
    raise SystemExit("expected 4 order rows")
for key in [
    "duplicate_order_lines",
    "orphan_fulfillments",
    "orphan_refunds",
    "unknown_inventory_skus",
    "negative_inventory",
]:
    if key not in quality["issues"]:
        raise SystemExit(f"data quality missing issue bucket: {key}")
if "sku_over" not in state["inventory"]:
    raise SystemExit("expected sku_over in reconstructed inventory")
if state["inventory"]["sku_over"]["available"] != -1:
    raise SystemExit("expected sku_over available inventory to be -1")
if "Offline Fulfillment Automation Audit" not in report:
    raise SystemExit("report should have the offline audit title")
if "Risk score" not in report:
    raise SystemExit("report should include risk score")

with (audit_dir / "redacted_inputs" / "orders.csv").open(newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))
buyer_ids = {row["buyer_id"] for row in rows}
if any("@" in buyer_id for buyer_id in buyer_ids):
    raise SystemExit("buyer identifiers should be redacted")
if not all(buyer_id.startswith("buyer_") for buyer_id in buyer_ids):
    raise SystemExit("redacted buyer identifiers should be stable buyer hashes")
PY

echo "Stage 4 offline audit smoke gate passed."
