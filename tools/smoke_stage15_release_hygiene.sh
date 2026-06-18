#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

SOURCE_PATHS="$(mktemp "${TMPDIR:-/tmp}/commerce-safety-stage15-source-paths.XXXXXX")"
cleanup() {
  rm -f "$SOURCE_PATHS"
}
trap cleanup EXIT

cat > "$SOURCE_PATHS" <<'PATHS'
AGENTS.md
README.md
ROADMAP.md
examples/agent_integrations/README.md
tools/smoke_stage18_agent_examples.sh
tests/test_stage18_agent_integration_examples.py
PATHS

"$PYTHON_BIN" tools/check_release_hygiene.py \
  --root "$ROOT_DIR" \
  --config release_hygiene.yaml \
  --source-pr-paths "$SOURCE_PATHS"

"$PYTHON_BIN" -m pytest tests/test_stage15_release_hygiene.py

echo "Stage 15 release hygiene + CI gate passed."
