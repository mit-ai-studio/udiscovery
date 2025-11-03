#!/usr/bin/env sh
# POSIX-compatible: avoid bash-only options like -o pipefail
set -eu

# Root dir
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

export NODE_ENV=production
export PORT="${PORT:-3000}"

echo "[start.sh] Setting up Python backend..."
cd "$APP_DIR/backend"

# Prefer the bundled backend Python if present (committed venv)
BACKEND_VENV_PY="$APP_DIR/backend/venv/bin/python3"
if [ -x "$BACKEND_VENV_PY" ]; then
  echo "[start.sh] Using bundled backend Python: $BACKEND_VENV_PY"
  # No install needed; dependencies are included in the bundled venv
else
  # Detect system python to create venv if needed
  PY_CMD=""
  if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
  elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
  fi

  if [ -n "$PY_CMD" ]; then
    if [ ! -d "venv" ]; then
      $PY_CMD -m venv venv || true
    fi
    if [ -f "venv/bin/activate" ]; then
      . venv/bin/activate
      $PY_CMD -m pip install --upgrade pip
      pip install -r requirements.txt || true
    else
      echo "[start.sh] Warning: venv not created; continuing without backend setup." >&2
    fi
  else
    echo "[start.sh] Warning: No Python found and no bundled venv. Backend demo API may not work." >&2
  fi
fi

echo "[start.sh] Starting Node frontend server..."
cd "$APP_DIR/frontend"

# Install prod deps
if command -v npm >/dev/null 2>&1; then
  # Prefer clean install; fall back to production install
  npm ci --omit=dev || npm install --production
else
  echo "npm not found" >&2
  exit 1
fi

# Ensure Python child process output is clean
export NO_COLOR=1
export TERM=dumb

node server.js

