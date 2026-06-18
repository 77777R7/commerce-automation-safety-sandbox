#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python3}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/commerce-safety-pycache}"

PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_release_candidate.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_auth_rbac.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_tenant_isolation.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_artifacts_audit.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_limits_redaction.sh
PYTHON="$PYTHON_BIN" ./tools/smoke_stage19_p0_hosted_live.sh

echo "Stage 19 Hosted Design Partner Trust Gate passed."
