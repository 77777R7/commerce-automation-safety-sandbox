#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/commerce-safety-pycache}"

cd "$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit(
        "V3.5 gate requires Python 3.10+ for MCP/API hardening dependencies. "
        f"Current: {sys.version.split()[0]} at {sys.executable}. "
        "Run with PYTHON=python3.12 ./tools/smoke_v35.sh."
    )
PY

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
PYTHON="$PYTHON_BIN" ./tools/smoke_stage10_mcp_p0_all.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage10_http_p0_all.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage11_openapi_contract.sh
./tools/smoke_stage12_shopify_skin_v0.sh
./tools/smoke_stage13_amazon_skin_v0.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage13_amazon_mcp_v0.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage15_release_hygiene.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage16_security_abuse.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage17_run_manifest.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage18_agent_examples.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_saas001_demo_pack.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_hosted_enterprise_poc.sh

echo "V3.5 live agent sandbox gate passed."
