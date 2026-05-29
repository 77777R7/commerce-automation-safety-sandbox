#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-week1.XXXXXX")"
SCENARIO="$ROOT_DIR/commerce-safety-sandbox/scenarios/duplicate_webhook.yaml"
CLI="$ROOT_DIR/commerce-safety"

cleanup() {
  rm -rf "$RUNS_DIR"
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

echo "Running bad_runner smoke check..."
bad_output="$("$CLI" --runs-dir "$RUNS_DIR" run "$SCENARIO" --runner bad_runner 2>&1)"
bad_exit=$?
echo "$bad_output"
[[ "$bad_exit" -eq 1 ]] || fail "bad_runner should exit 1, got $bad_exit"

bad_run_id="$(printf '%s\n' "$bad_output" | awk -F': ' '/^Run ID:/ {print $2}')"
[[ -n "$bad_run_id" ]] || fail "could not parse bad run id"
bad_run_dir="$RUNS_DIR/$bad_run_id"

assert_file "$bad_run_dir/trace.json"
assert_file "$bad_run_dir/policy_report.json"
assert_file "$bad_run_dir/state_diff.json"
assert_file "$bad_run_dir/report.md"

python3 - "$bad_run_dir" <<'PY'
import json
import pathlib
import sys

run_dir = pathlib.Path(sys.argv[1])
policy = json.loads((run_dir / "policy_report.json").read_text())
state = json.loads((run_dir / "state_diff.json").read_text())

policy_ids = {finding["policy_id"] for finding in policy["findings"]}
required = {"no_duplicate_fulfillment", "webhook_dedup_required"}
missing = required - policy_ids
if missing:
    raise SystemExit(f"missing policy findings: {sorted(missing)}")

if state["before"]["fulfillments"] != 0:
    raise SystemExit("expected bad before fulfillments to be 0")
if state["after"]["fulfillments"] != 2:
    raise SystemExit("expected bad after fulfillments to be 2")
if state["expected"]["reserved_inventory"].get("sku_widget_1") != 1:
    raise SystemExit("expected reserved inventory should be 1")
if state["after"]["reserved_inventory"].get("sku_widget_1") != 2:
    raise SystemExit("actual reserved inventory should be 2")
if not state["accident_signals"]["duplicated_reserved_inventory"]:
    raise SystemExit("expected duplicated reserved inventory signal")

webhook = next(
    finding for finding in policy["findings"]
    if finding["policy_id"] == "webhook_dedup_required"
)
side_effect_types = {
    item["type"]
    for item in webhook["evidence"]["side_effects_from_same_webhook"]
}
if not {"reservation", "fulfillment"}.issubset(side_effect_types):
    raise SystemExit("duplicate webhook evidence must include reservation and fulfillment side effects")
PY

bad_replay="$("$CLI" --runs-dir "$RUNS_DIR" replay "$bad_run_id")"
echo "$bad_replay"
printf '%s\n' "$bad_replay" | grep -q "Replay from trace.json" || fail "replay did not read trace.json"
printf '%s\n' "$bad_replay" | grep -q "Policy violation detected: no_duplicate_fulfillment" || fail "bad replay missing policy violation"

echo "Running good_runner smoke check..."
good_output="$("$CLI" --runs-dir "$RUNS_DIR" run "$SCENARIO" --runner good_runner 2>&1)"
good_exit=$?
echo "$good_output"
[[ "$good_exit" -eq 0 ]] || fail "good_runner should exit 0, got $good_exit"

good_run_id="$(printf '%s\n' "$good_output" | awk -F': ' '/^Run ID:/ {print $2}')"
[[ -n "$good_run_id" ]] || fail "could not parse good run id"
good_run_dir="$RUNS_DIR/$good_run_id"

assert_file "$good_run_dir/trace.json"
assert_file "$good_run_dir/policy_report.json"
assert_file "$good_run_dir/state_diff.json"
assert_file "$good_run_dir/report.md"

python3 - "$good_run_dir" <<'PY'
import json
import pathlib
import sys

run_dir = pathlib.Path(sys.argv[1])
policy = json.loads((run_dir / "policy_report.json").read_text())
state = json.loads((run_dir / "state_diff.json").read_text())

if policy["status"] != "passed":
    raise SystemExit("good run should pass")
if policy["findings"]:
    raise SystemExit("good run should not have findings")
if state["after"]["fulfillments"] != 1:
    raise SystemExit("good run should create one fulfillment")
if state["after"]["reserved_inventory"].get("sku_widget_1") != 1:
    raise SystemExit("good run should reserve one unit")
if state["accident_signals"]["duplicated_reserved_inventory"]:
    raise SystemExit("good run should not signal duplicated inventory")
PY

good_replay="$("$CLI" --runs-dir "$RUNS_DIR" replay "$good_run_id")"
echo "$good_replay"
printf '%s\n' "$good_replay" | grep -q "Replay from trace.json" || fail "good replay did not read trace.json"
printf '%s\n' "$good_replay" | grep -q "skips duplicate webhook" || fail "good replay missing duplicate skip"

echo "Week 1 smoke gate passed."
