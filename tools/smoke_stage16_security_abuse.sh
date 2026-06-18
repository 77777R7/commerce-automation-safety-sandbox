#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$PYTHON_BIN" tools/check_security_hardening.py \
  --root "$ROOT_DIR" \
  --config security_hardening.yaml

"$PYTHON_BIN" -m pytest tests/test_stage16_security_abuse.py

echo "Stage 16 security / abuse hardening gate passed."

