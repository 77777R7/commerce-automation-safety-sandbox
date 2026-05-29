#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-offline-audit-clean.XXXXXX")"
SAMPLE_DIR="$ROOT_DIR/commerce-safety-sandbox/offline_samples/clean_audit"
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

echo "Running Stage 4 clean offline audit smoke check..."
audit_output="$("$CLI" offline-audit \
  --orders "$SAMPLE_DIR/orders.csv" \
  --inventory "$SAMPLE_DIR/inventory.csv" \
  --fulfillments "$SAMPLE_DIR/fulfillments.csv" \
  --refunds "$SAMPLE_DIR/refunds.csv" \
  --output-dir "$OUTPUT_DIR" 2>&1)"
audit_exit=$?
echo "$audit_output"
[[ "$audit_exit" -eq 0 ]] || fail "clean offline audit should exit 0, got $audit_exit"

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
policy = json.loads((audit_dir / "policy_report.json").read_text())
quality = json.loads((audit_dir / "data_quality.json").read_text())
state = json.loads((audit_dir / "state_reconstruction.json").read_text())
report = (audit_dir / "report.md").read_text()

if policy["status"] != "passed":
    raise SystemExit("clean audit should pass")
if policy["risk_score"] != 0:
    raise SystemExit("clean audit should have risk score 0")
if policy["findings"]:
    raise SystemExit("clean audit should not have findings")
if quality["datasets"]["orders"]["missing_headers"]:
    raise SystemExit("canonical clean sample should not need mapping")
if state["inventory"]["sku_clean"]["available"] != 4:
    raise SystemExit("expected sku_clean available inventory to be 4")
if "No policy findings were detected" not in report:
    raise SystemExit("clean report should explain that no findings were detected")

with (audit_dir / "redacted_inputs" / "orders.csv").open(newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))
if rows[0]["buyer_id"] == "ops@example.com" or "@" in rows[0]["buyer_id"]:
    raise SystemExit("buyer identifier should be redacted even on clean audits")
PY

echo "Stage 4 clean offline audit smoke gate passed."
