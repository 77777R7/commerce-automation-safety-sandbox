#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-scn003.XXXXXX")"
SCENARIO="$ROOT_DIR/commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml"
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

echo "Running SCN-003 bad_runner smoke check..."
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
required = {
    "reservation_required_before_promise",
    "no_inventory_commit_from_stale_snapshot",
    "no_oversell",
}
missing = required - policy_ids
if missing:
    raise SystemExit(f"missing policy findings: {sorted(missing)}")

if state["before"]["fulfillment_promises"] != 0:
    raise SystemExit("expected before fulfillment promises to be 0")
if state["after"]["fulfillment_promises"] != 1:
    raise SystemExit("expected bad after fulfillment promises to be 1")
if not state["accident_signals"]["unreserved_fulfillment_promise"]:
    raise SystemExit("expected unreserved fulfillment promise signal")
if not state["accident_signals"]["oversell_risk"]:
    raise SystemExit("expected oversell risk signal")
if state["after"]["reserved_inventory"].get("sku_stale_1") != 1:
    raise SystemExit("bad run should not create a fresh reservation")

reservation = next(
    finding for finding in policy["findings"]
    if finding["policy_id"] == "reservation_required_before_promise"
)
if reservation["evidence"]["reservation_id"] is not None:
    raise SystemExit("bad promise should not have reservation_id")
if reservation["evidence"]["true_available_at_commit"] != 0:
    raise SystemExit("true availability should be 0")
PY

bad_replay="$("$CLI" --runs-dir "$RUNS_DIR" replay "$bad_run_id")"
echo "$bad_replay"
printf '%s\n' "$bad_replay" | grep -q "Replay from trace.json" || fail "bad replay did not read trace.json"
printf '%s\n' "$bad_replay" | grep -q "reads stale inventory" || fail "bad replay missing stale inventory read"
printf '%s\n' "$bad_replay" | grep -q "promises fulfillment" || fail "bad replay missing unsafe promise"

echo "Running SCN-003 good_runner smoke check..."
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
if state["after"]["fulfillment_promises"] != 0:
    raise SystemExit("good run should not promise fulfillment")
if state["accident_signals"]["unreserved_fulfillment_promise"]:
    raise SystemExit("good run should not signal unreserved promise")
if state["accident_signals"]["oversell_risk"]:
    raise SystemExit("good run should not signal oversell risk")
PY

good_replay="$("$CLI" --runs-dir "$RUNS_DIR" replay "$good_run_id")"
echo "$good_replay"
printf '%s\n' "$good_replay" | grep -q "Replay from trace.json" || fail "good replay did not read trace.json"
printf '%s\n' "$good_replay" | grep -q "refreshes inventory" || fail "good replay missing inventory refresh"
printf '%s\n' "$good_replay" | grep -q "manual review" || fail "good replay missing manual review route"

echo "SCN-003 smoke gate passed."
