#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

python3 -m pytest tests/test_live_demo_pack.py

echo "Stage 7 live agent validation demo pack gate passed."
