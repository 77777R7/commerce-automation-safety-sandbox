#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

./tools/smoke_stage0_rebaseline.sh
python3 -m pytest
./tools/smoke_stage1_live_session.sh
./tools/smoke_stage2_http_scn002.sh
./tools/smoke_stage3_mcp_scn002.sh
./tools/smoke_live_all.sh
./tools/smoke_stage5_action_log_gate.sh
./tools/smoke_stage6_repair_loop.sh
./tools/smoke_stage7_demo_pack.sh

echo "V3.5 live agent sandbox gate passed."
