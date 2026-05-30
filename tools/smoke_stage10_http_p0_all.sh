#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/commerce-safety-stage10-http-runs.XXXXXX")"
SERVER_LOG="$(mktemp "${TMPDIR:-/tmp}/commerce-safety-stage10-http-server.XXXXXX.log")"
CLI="$ROOT_DIR/commerce-safety"
PYTHON_BIN="${PYTHON:-python3}"
PORT="$((19765 + (RANDOM % 1000)))"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$RUNS_DIR"
  rm -f "$SERVER_LOG"
}
trap cleanup EXIT

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/commerce-safety-sandbox:${PYTHONPATH:-}"

"$CLI" --runs-dir "$RUNS_DIR" live serve --host 127.0.0.1 --port "$PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

for _ in {1..50}; do
  if grep -q "Commerce Safety live server listening" "$SERVER_LOG"; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cat "$SERVER_LOG" >&2
    echo "FAIL: live server exited before it was ready" >&2
    exit 1
  fi
  sleep 0.1
done

grep -q "Commerce Safety live server listening" "$SERVER_LOG" || {
  cat "$SERVER_LOG" >&2
  echo "FAIL: live server did not become ready" >&2
  exit 1
}

"$PYTHON_BIN" tools/stage10_p0_harness.py http \
  --root "$ROOT_DIR" \
  --runs-dir "$RUNS_DIR" \
  --base-url "http://127.0.0.1:$PORT"

echo "Stage 10 full P0 HTTP gate passed."
