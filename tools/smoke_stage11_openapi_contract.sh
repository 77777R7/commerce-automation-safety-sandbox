#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$PYTHON_BIN" -m pytest tests/test_openapi_contract_shape.py
PYTHON="$PYTHON_BIN" ./tools/smoke_stage9_api_hardening.sh

echo "Stage 11 strict OpenAPI contract gate passed."
