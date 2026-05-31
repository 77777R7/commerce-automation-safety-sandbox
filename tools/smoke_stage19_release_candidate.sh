#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python3}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/commerce-safety-pycache}"

PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}" \
  "$PYTHON_BIN" tools/check_stage19_release_candidate.py

echo "Stage 19 release candidate cleanup gate passed."
