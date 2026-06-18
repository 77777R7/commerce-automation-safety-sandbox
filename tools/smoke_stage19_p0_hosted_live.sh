#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python3}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/commerce-safety-pycache}"
PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}" \
  "$PYTHON_BIN" -m pytest -q tests/test_stage19_hosted_trust_gate.py \
  -k "all_p0"

echo "Stage 19 hosted P0 MCP/HTTP gate passed."
