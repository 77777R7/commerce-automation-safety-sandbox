#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage3-runs.XXXXXX")"
REGRESSIONS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage3-regressions.XXXXXX")"
SCENARIO="$ROOT_DIR/commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"
CLI="$ROOT_DIR/commerce-safety"

cleanup() {
  rm -rf "$RUNS_DIR" "$REGRESSIONS_DIR"
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

echo "Running failed scenario to capture a regression candidate..."
bad_output="$("$CLI" --runs-dir "$RUNS_DIR" run "$SCENARIO" --runner bad_runner 2>&1)"
bad_exit=$?
echo "$bad_output"
[[ "$bad_exit" -eq 1 ]] || fail "bad_runner should exit 1, got $bad_exit"

bad_run_id="$(printf '%s\n' "$bad_output" | awk -F': ' '/^Run ID:/ {print $2}')"
[[ -n "$bad_run_id" ]] || fail "could not parse bad run id"
bad_run_dir="$RUNS_DIR/$bad_run_id"

assert_file "$bad_run_dir/scenario.yaml"
assert_file "$bad_run_dir/trace.json"
assert_file "$bad_run_dir/policy_report.json"
assert_file "$bad_run_dir/state_diff.json"
assert_file "$bad_run_dir/report.md"

echo "Saving failed run as a regression scenario..."
save_output="$("$CLI" \
  --runs-dir "$RUNS_DIR" \
  save-regression "$bad_run_id" \
  --name "Timeout Retry Regression" \
  --regressions-dir "$REGRESSIONS_DIR" 2>&1)"
save_exit=$?
echo "$save_output"
[[ "$save_exit" -eq 0 ]] || fail "save-regression should exit 0, got $save_exit"

regression_dir="$REGRESSIONS_DIR/timeout-retry-regression"
assert_file "$regression_dir/scenario.yaml"
assert_file "$regression_dir/trace.json"
assert_file "$regression_dir/policy_report.json"
assert_file "$regression_dir/state_diff.json"
assert_file "$regression_dir/summary.md"

python3 - "$regression_dir" "$bad_run_id" <<'PY'
import json
import pathlib
import sys

regression_dir = pathlib.Path(sys.argv[1])
run_id = sys.argv[2]
trace = json.loads((regression_dir / "trace.json").read_text())
policy = json.loads((regression_dir / "policy_report.json").read_text())
summary = (regression_dir / "summary.md").read_text()
scenario = (regression_dir / "scenario.yaml").read_text()

if trace["run_id"] != run_id:
    raise SystemExit("saved trace should preserve the source run id")

policy_ids = {finding["policy_id"] for finding in policy["findings"]}
required = {
    "idempotency_required_for_mutating_retries",
    "no_duplicate_fulfillment",
}
missing = required - policy_ids
if missing:
    raise SystemExit(f"missing policy findings: {sorted(missing)}")

if "Regression gate" not in summary and "Regression Gate" not in summary:
    raise SystemExit("summary should explain the regression gate")
if run_id not in summary:
    raise SystemExit("summary should include the source run id")
if "id: SCN-002" not in scenario:
    raise SystemExit("saved scenario.yaml should preserve the source scenario")
PY

regression_replay="$("$CLI" replay "$regression_dir")"
echo "$regression_replay"
printf '%s\n' "$regression_replay" | grep -q "Replay from trace.json" || fail "regression replay did not read trace.json"
printf '%s\n' "$regression_replay" | grep -q "returned timeout_after_commit" || fail "regression replay missing timeout fault"

echo "Verifying passed runs are not saved as failed regressions..."
good_output="$("$CLI" --runs-dir "$RUNS_DIR" run "$SCENARIO" --runner good_runner 2>&1)"
good_exit=$?
echo "$good_output"
[[ "$good_exit" -eq 0 ]] || fail "good_runner should exit 0, got $good_exit"

good_run_id="$(printf '%s\n' "$good_output" | awk -F': ' '/^Run ID:/ {print $2}')"
[[ -n "$good_run_id" ]] || fail "could not parse good run id"

good_save_output="$("$CLI" \
  --runs-dir "$RUNS_DIR" \
  save-regression "$good_run_id" \
  --name "Should Not Save Passed Run" \
  --regressions-dir "$REGRESSIONS_DIR" 2>&1)"
good_save_exit=$?
echo "$good_save_output"
[[ "$good_save_exit" -ne 0 ]] || fail "save-regression should reject passed runs"

echo "Stage 3 regression smoke gate passed."
