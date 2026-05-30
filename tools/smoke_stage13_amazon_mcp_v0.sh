#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage13-mcp.XXXXXX")"
PYTHON_BIN="${PYTHON:-python3}"

cleanup() {
  rm -rf "$RUNS_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$PYTHON_BIN" tools/stage13_amazon_skin_harness.py mcp \
  --root "$ROOT_DIR" \
  --runs-dir "$RUNS_DIR"

echo "Stage 13 Amazon Seller Ops skin MCP gate passed."
