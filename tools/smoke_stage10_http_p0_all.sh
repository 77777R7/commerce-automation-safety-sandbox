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

"$PYTHON_BIN" "$CLI" --runs-dir "$RUNS_DIR" live serve --host 127.0.0.1 --port "$PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

if ! "$PYTHON_BIN" - "http://127.0.0.1:$PORT" "$SERVER_PID" <<'PY'
import os
import sys
import time
import urllib.error
import urllib.request

base_url = sys.argv[1]
server_pid = int(sys.argv[2])
deadline = time.time() + 90

while time.time() < deadline:
    try:
        urllib.request.urlopen(f"{base_url}/sessions/not-real/trace", timeout=0.5)
    except urllib.error.HTTPError:
        raise SystemExit(0)
    except Exception:
        try:
            os.kill(server_pid, 0)
        except OSError:
            raise SystemExit("live server exited before it was ready")
        time.sleep(0.1)

raise SystemExit("live server did not become ready")
PY
then
  cat "$SERVER_LOG" >&2
  exit 1
fi

"$PYTHON_BIN" tools/stage10_p0_harness.py http \
  --root "$ROOT_DIR" \
  --runs-dir "$RUNS_DIR" \
  --base-url "http://127.0.0.1:$PORT"

echo "Stage 10 full P0 HTTP gate passed."
