#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

python3 -m pytest tests/test_agent_repair_artifacts.py

echo "Stage 6 agent-readable repair loop gate passed."
