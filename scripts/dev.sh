#!/usr/bin/env bash
# Start the FastAPI backend (:8002) and the Vite frontend (:3000) together for
# local, no-Docker development. The frontend proxies /api to the backend, so you
# only ever open http://localhost:3000. Ctrl-C stops both.
set -euo pipefail

# Resolve the repo root from this script's location so it runs from anywhere.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_DIR="$ROOT/react_frontend"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "error: .venv/bin/uvicorn not found. Create the venv first:" >&2
  echo "  python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt" >&2
  exit 1
fi
if [[ ! -f .env ]]; then
  echo "warning: no .env found — copy .env.example and set OPENAI_API_KEY (chat" >&2
  echo "         falls back to the substring heuristic without it)." >&2
fi
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "installing frontend dependencies (first run)…"
  (cd "$FRONTEND_DIR" && yarn install)
fi

# Background children share this script's process group, so the terminal's Ctrl-C
# (SIGINT) already reaches both servers; the trap just reaps any stragglers.
pids=()
cleanup() {
  trap - INT TERM EXIT
  echo
  echo "stopping dev servers…"
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "backend  → http://localhost:$BACKEND_PORT  (uvicorn --reload)"
echo "frontend → http://localhost:3000          (open this one)"
echo

.venv/bin/uvicorn app.main:app --reload --port "$BACKEND_PORT" &
pids+=($!)

(cd "$FRONTEND_DIR" && yarn dev) &
pids+=($!)

# Block until interrupted (or a server exits), then cleanup runs via the trap.
wait
