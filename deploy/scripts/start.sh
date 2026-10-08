#!/usr/bin/env bash
# Local development only; all services bind to this machine.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PYTHON="$ROOT_DIR/.venv/bin/python"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    trap - EXIT INT TERM
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
    done
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        if [[ -n "$pid" ]]; then wait "$pid" 2>/dev/null || true; fi
    done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "$ROOT_DIR"
command -v uv >/dev/null || { echo "Install uv to manage the project's Python 3.11 environment." >&2; exit 1; }
command -v npm >/dev/null || { echo "Node.js 24+ and npm are required." >&2; exit 1; }
node -e 'if (Number(process.versions.node.split(".")[0]) < 24) process.exit(1)' || {
    echo "Node.js 24+ is required (including native TypeScript tests)." >&2; exit 1;
}
if [[ ! -x "$PYTHON" ]]; then uv venv --python 3.11 "$ROOT_DIR/.venv"; fi
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Project .venv must use Python 3.11"'
# Fail before installing or migrating if either requested local port is occupied.
"$PYTHON" - "$BACKEND_PORT" "$FRONTEND_PORT" <<'PY'
import socket, sys
ports = sys.argv[1:]
if len(set(ports)) != 2:
    sys.exit("Backend and frontend ports must differ.")
for value in ports:
    try:
        port = int(value)
        assert 1 <= port <= 65535
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
    except (ValueError, AssertionError, OSError):
        sys.exit(f"Local port {value} is invalid or occupied. Choose BACKEND_PORT/FRONTEND_PORT; existing servers will not be stopped.")
PY

# Exact top-level versions plus transitive constraints; npm's committed lockfile.
uv pip install --python "$PYTHON" -r backend/requirements.txt
npm --prefix frontend ci --no-audit --no-fund
"$PYTHON" -m alembic upgrade head

"$PYTHON" -m uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" &
BACKEND_PID=$!
# Run Vite directly so cleanup owns the actual server process, not an npm wrapper.
(
    cd "$ROOT_DIR/frontend"
    export VITE_API_BASE_URL="http://127.0.0.1:$BACKEND_PORT/api/v1"
    exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort
) &
FRONTEND_PID=$!
printf 'Frontend: http://127.0.0.1:%s\nBackend: http://127.0.0.1:%s/docs\nPress Ctrl+C to stop both local services.\n' "$FRONTEND_PORT" "$BACKEND_PORT"

# Compatible with macOS Bash 3.2 (which does not support wait -n).
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do sleep 1; done
echo "A local service exited; stopping the other service." >&2
exit 1
