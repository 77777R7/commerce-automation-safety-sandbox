#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage17-runs.XXXXXX")"

cleanup() {
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$PYTHON_BIN" -m pytest tests/test_stage17_run_manifest.py

set +e
bad_output="$("$PYTHON_BIN" ./commerce-safety --runs-dir "$RUNS_DIR" run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner bad_runner 2>&1)"
bad_status=$?
set -e

if [[ "$bad_status" -ne 1 ]]; then
  echo "$bad_output" >&2
  echo "FAIL: bad_runner should fail policy gate with exit 1" >&2
  exit 1
fi

bad_run_id="$(printf '%s\n' "$bad_output" | awk -F': ' '/Run ID:/ {print $2; exit}')"
bad_run_path="$RUNS_DIR/$bad_run_id"

for artifact in trace.json policy_report.json state_diff.json report.md run_manifest.json; do
  if [[ ! -f "$bad_run_path/$artifact" ]]; then
    echo "FAIL: missing Stage 17 artifact $artifact" >&2
    exit 1
  fi
done

"$PYTHON_BIN" tools/check_run_manifest.py "$bad_run_path"

"$PYTHON_BIN" - "$bad_run_path" <<'PY'
import json
import pathlib
import sys

run_path = pathlib.Path(sys.argv[1])
manifest = json.loads((run_path / "run_manifest.json").read_text(encoding="utf-8"))
assert manifest["schema_version"] == "commerce_safety.run_manifest.v1"
assert manifest["artifact_schema_version"] == "commerce_safety.artifacts.v1"
paths = {artifact["path"] for artifact in manifest["artifacts"]}
assert {"trace.json", "policy_report.json", "state_diff.json", "report.md"}.issubset(paths)
assert json.loads((run_path / "trace.json").read_text(encoding="utf-8"))["schema_version"] == "commerce_safety.trace.v1"
assert json.loads((run_path / "policy_report.json").read_text(encoding="utf-8"))["schema_version"] == "commerce_safety.policy_report.v1"
assert json.loads((run_path / "state_diff.json").read_text(encoding="utf-8"))["schema_version"] == "commerce_safety.state_diff.v1"
PY

echo "Stage 17 run manifest + artifact schema gate passed."

