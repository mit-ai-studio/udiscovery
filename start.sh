#!/usr/bin/env bash
set -euo pipefail

# Root dir
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

export NODE_ENV=production
export PORT="${PORT:-3000}"

echo "[start.sh] Setting up Python backend..."
cd "$APP_DIR/backend/backend"

# Create venv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv || python -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[start.sh] Starting Node frontend server..."
cd "$APP_DIR/frontend"

# Install prod deps
if command -v npm >/dev/null 2>&1; then
  npm ci --only=production || npm install --only=production
else
  echo "npm not found" >&2
  exit 1
fi

# Ensure Python child process output is clean
export NO_COLOR=1
export TERM=dumb

node server.js


