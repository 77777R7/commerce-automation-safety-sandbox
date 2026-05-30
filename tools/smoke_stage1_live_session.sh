#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage1-live.XXXXXX")"

cleanup() {
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

python3 - "$RUNS_DIR" <<'PY'
import json
import pathlib
import sys

from commerce_safety.live.sessions import SessionManager
from commerce_safety.twin import TimeoutAfterCommit

runs_dir = pathlib.Path(sys.argv[1])
scenario_path = pathlib.Path(
    "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"
)


def artifact_json(run_path, name):
    return json.loads((run_path / name).read_text(encoding="utf-8"))


def assert_artifacts(run_path):
    required = [
        "trace.json",
        "policy_report.json",
        "state_diff.json",
        "report.md",
        "patch_hints.md",
        "patch_hints.json",
    ]
    missing = [name for name in required if not (run_path / name).is_file()]
    if missing:
        raise SystemExit(f"missing artifacts: {missing}")


manager = SessionManager(runs_dir=runs_dir)

bad = manager.create_session(scenario_path)
task = bad.scenario["events"][0]
bad.twin.receive_fulfillment_task(task)
try:
    bad.twin.create_fulfillment(
        order_id=task["order_id"],
        sku="sku_retry_1",
        quantity=1,
        actor="external_agent",
        webhook_id=None,
        idempotency_key=None,
        request_id="req_timeout_1",
        source_event_id=task["id"],
        fault_type=task["fault"]["type"],
    )
except TimeoutAfterCommit:
    pass
else:
    raise SystemExit("expected timeout_after_commit fault")
bad.twin.create_fulfillment(
    order_id=task["order_id"],
    sku="sku_retry_1",
    quantity=1,
    actor="external_agent",
    webhook_id=None,
    idempotency_key=None,
    request_id="req_retry_2",
    source_event_id=task["id"],
)
bad_result = manager.complete_session(bad.session_id, runner_name="external_bad_agent")
if bad_result["status"] != "failed":
    raise SystemExit("bad live session should fail")
bad_path = pathlib.Path(bad_result["run_path"])
assert_artifacts(bad_path)
bad_policy_ids = {
    finding["policy_id"]
    for finding in artifact_json(bad_path, "policy_report.json")["findings"]
}
expected_bad = {
    "idempotency_required_for_mutating_retries",
    "no_duplicate_fulfillment",
}
if not expected_bad.issubset(bad_policy_ids):
    raise SystemExit(f"missing bad live findings: {sorted(expected_bad - bad_policy_ids)}")
bad_hints = artifact_json(bad_path, "patch_hints.json")
if len(bad_hints["hints"]) < 2:
    raise SystemExit("bad live session should produce patch hints")

good = manager.create_session(scenario_path)
task = good.scenario["events"][0]
good.twin.receive_fulfillment_task(task)
stable_key = f"{task['order_id']}:sku_retry_1:create_fulfillment"
try:
    good.twin.create_fulfillment(
        order_id=task["order_id"],
        sku="sku_retry_1",
        quantity=1,
        actor="external_agent",
        webhook_id=None,
        idempotency_key=stable_key,
        request_id="req_timeout_1",
        source_event_id=task["id"],
        fault_type=task["fault"]["type"],
    )
except TimeoutAfterCommit:
    pass
else:
    raise SystemExit("expected timeout_after_commit fault")
good.twin.create_fulfillment(
    order_id=task["order_id"],
    sku="sku_retry_1",
    quantity=1,
    actor="external_agent",
    webhook_id=None,
    idempotency_key=stable_key,
    request_id="req_retry_2",
    source_event_id=task["id"],
)
good_result = manager.complete_session(good.session_id, runner_name="external_good_agent")
if good_result["status"] != "passed":
    raise SystemExit("good live session should pass")
good_path = pathlib.Path(good_result["run_path"])
assert_artifacts(good_path)
if artifact_json(good_path, "policy_report.json")["findings"]:
    raise SystemExit("good live session should not produce findings")
if artifact_json(good_path, "patch_hints.json")["hints"]:
    raise SystemExit("good live session should not produce patch hints")

isolated = manager.create_session(scenario_path)
if isolated.twin.snapshot_summary()["counts"]["fulfillments"] != 0:
    raise SystemExit("new live session must start with isolated twin state")

print("Stage 1 live session gate passed.")
PY
