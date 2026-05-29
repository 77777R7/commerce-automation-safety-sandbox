#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

python3 -m pytest tests/test_live_p0_coverage.py

echo "Stage 4 five P0 live gate passed."
