#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-scn005.XXXXXX")"

cleanup() {
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox" python3 - "$ROOT_DIR" "$RUNS_DIR" <<'PY'
import json
import pathlib
import sys

from commerce_safety.engine import run_scenario


root = pathlib.Path(sys.argv[1])
runs_dir = pathlib.Path(sys.argv[2])
scenario = root / "commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def assert_file(path: pathlib.Path) -> None:
    if not path.is_file():
        fail(f"missing file: {path}")


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def print_replay(trace: dict) -> None:
    print(f"Replay from trace.json: {trace['run_id']}")
    print(f"Scenario: {trace['scenario_name']}")
    print(f"Runner: {trace['runner']}")
    print(f"Status: {trace['status']}")
    print("")
    for event in trace["timeline"]:
        print(f"Step {event['step']}: {event['message']}")


print("Running SCN-005 bad_runner smoke check...")
bad = run_scenario(scenario, "bad_runner", runs_dir)
print(f"Run ID: {bad['run_id']}")
print(f"Status: {bad['status']}")
print(f"Artifacts: {bad['run_path']}")
for finding in bad["findings"]:
    print(f"- {finding['policy_id']} ({finding['severity']})")
if bad["status"] != "failed":
    fail("bad_runner should fail")
if not bad["findings"]:
    fail("bad_runner should have policy findings and would exit non-zero via CLI")

bad_run_dir = pathlib.Path(bad["run_path"])
for filename in ("trace.json", "policy_report.json", "state_diff.json", "report.md"):
    assert_file(bad_run_dir / filename)

bad_policy = load_json(bad_run_dir / "policy_report.json")
bad_state = load_json(bad_run_dir / "state_diff.json")
bad_trace = load_json(bad_run_dir / "trace.json")

policy_ids = {finding["policy_id"] for finding in bad_policy["findings"]}
required = {
    "warehouse_conflict_requires_hold",
    "no_ship_after_cancel",
    "no_double_refund_or_inventory_release",
}
missing = required - policy_ids
if missing:
    fail(f"missing policy findings: {sorted(missing)}")

if bad_state["before"]["reserved_inventory"].get("sku_pickpack_1") != 1:
    fail("expected before reserved inventory to be 1")
if bad_state["after"]["reserved_inventory"].get("sku_pickpack_1") != 0:
    fail("expected bad run to release reserved inventory")
if bad_state["after"]["refunds"] != 1:
    fail("expected bad run to issue one refund")
if bad_state["after"]["inventory_releases"] != 1:
    fail("expected bad run to create one inventory release")
if bad_state["after"]["workflow_holds"] != 0:
    fail("bad run should not create workflow hold")
if bad_state["after"]["warehouse_cancellation_requests"] != 0:
    fail("bad run should not ask warehouse to cancel")
if not bad_state["accident_signals"]["warehouse_conflict_without_hold"]:
    fail("expected warehouse conflict without hold signal")
if not bad_state["accident_signals"]["ship_after_cancel"]:
    fail("expected ship-after-cancel signal")
if not bad_state["accident_signals"]["refund_and_inventory_release_while_warehouse_continued"]:
    fail("expected refund/release while warehouse continued signal")

bad_order = bad_state["after"]["orders"]["order_5001"]
if bad_order["order_status"] != "cancelled":
    fail("bad run should mark order cancelled")
bad_job = bad_state["after"]["warehouse_jobs"][0]
if bad_job["status"] != "shipped" or not bad_job["continued_after_cancel"]:
    fail("bad run should let warehouse continue to shipped")

print_replay(bad_trace)
bad_messages = "\n".join(event["message"] for event in bad_trace["timeline"])
for expected in (
    "Cancel request cancel_req_5001 received",
    "marks order order_5001 as cancelled",
    "releases 1 unit",
    "issues refund",
    "Warehouse continues job",
):
    if expected not in bad_messages:
        fail(f"bad replay missing: {expected}")

print("Running SCN-005 good_runner smoke check...")
good = run_scenario(scenario, "good_runner", runs_dir)
print(f"Run ID: {good['run_id']}")
print(f"Status: {good['status']}")
print(f"Artifacts: {good['run_path']}")
if good["status"] != "passed":
    fail("good_runner should pass")
if good["findings"]:
    fail("good_runner should not have policy findings")

good_run_dir = pathlib.Path(good["run_path"])
for filename in ("trace.json", "policy_report.json", "state_diff.json", "report.md"):
    assert_file(good_run_dir / filename)

good_policy = load_json(good_run_dir / "policy_report.json")
good_state = load_json(good_run_dir / "state_diff.json")
good_trace = load_json(good_run_dir / "trace.json")

if good_policy["findings"]:
    fail("good run should not have findings")
if good_state["after"]["refunds"] != 0:
    fail("good run should not issue refund")
if good_state["after"]["inventory_releases"] != 0:
    fail("good run should not release inventory")
if good_state["after"]["workflow_holds"] != 1:
    fail("good run should create one workflow hold")
if good_state["after"]["warehouse_cancellation_requests"] != 1:
    fail("good run should ask warehouse to cancel")
if good_state["after"]["reserved_inventory"].get("sku_pickpack_1") != 1:
    fail("good run should keep reserved inventory pending")
if good_state["accident_signals"]["warehouse_conflict_without_hold"]:
    fail("good run should not signal warehouse conflict without hold")
if good_state["accident_signals"]["ship_after_cancel"]:
    fail("good run should not signal ship after cancel")
if good_state["accident_signals"]["refund_and_inventory_release_while_warehouse_continued"]:
    fail("good run should not signal refund/release while warehouse continued")

good_order = good_state["after"]["orders"]["order_5001"]
if good_order["order_status"] != "open":
    fail("good run should not mark order cancelled yet")
good_job = good_state["after"]["warehouse_jobs"][0]
if good_job["status"] != "picked":
    fail("good run should keep warehouse job in picked state")
if not good_job["cancellation_requested"]:
    fail("good run should submit warehouse cancellation request")

print_replay(good_trace)
good_messages = "\n".join(event["message"] for event in good_trace["timeline"])
for expected in (
    "checks warehouse progress",
    "places order order_5001 on hold",
    "asks warehouse to cancel job",
    "does not refund, release inventory",
):
    if expected not in good_messages:
        fail(f"good replay missing: {expected}")

print("SCN-005 smoke gate passed.")
PY
