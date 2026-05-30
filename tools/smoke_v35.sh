#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "$ROOT_DIR"

./tools/smoke_stage0_rebaseline.sh
"$PYTHON_BIN" -m pytest
./tools/smoke_stage1_live_session.sh
./tools/smoke_stage2_http_scn002.sh
./tools/smoke_stage3_mcp_scn002.sh
./tools/smoke_live_all.sh
./tools/smoke_stage5_action_log_gate.sh
./tools/smoke_stage6_repair_loop.sh
./tools/smoke_stage7_demo_pack.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage9_real_mcp.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage9_api_hardening.sh

echo "V3.5 live agent sandbox gate passed."
