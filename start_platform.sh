#!/usr/bin/env bash
set -e

echo "=== GULA Platform Local & Demo Launcher ==="
cd /home/ubuntu/gula-platform

# 1. Setup Python Virtual Environment for Backend if needed
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment for backend..."
    python3.12 -m venv backend/venv
fi

REQ_HASH=$(sha256sum backend/requirements.txt | awk '{print $1}')
REQ_STAMP=backend/venv/.gula-requirements.sha256
if [ "${INSTALL_DEPS:-false}" = "true" ] || [ ! -f "$REQ_STAMP" ] || ! grep -qx "$REQ_HASH" "$REQ_STAMP"; then
    echo "Installing backend dependencies..."
    ./backend/venv/bin/pip install --upgrade pip
    ./backend/venv/bin/pip install -r backend/requirements.txt
    printf '%s\n' "$REQ_HASH" > "$REQ_STAMP"
else
    echo "Backend dependencies unchanged; skipping pip install."
fi

# 2. Configure environment for demo mode
export ENV=demo
export DEMO_MODE=true
export DEMO_DATA_ISOLATION_ACK=true
export DATABASE_URL=${DATABASE_URL:-sqlite:///./gula_demo.db}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}
# If redis is not running locally, allow fallback or start redis / set mock
export ALLOW_DEGRADED_REDIS=true

echo "Starting GULA Backend API in demo/secure mode on port 8000..."
export PYTHONPATH=/home/ubuntu/gula-platform
# Keep worker count bounded by the DB pool formula; SQLite demo uses one worker
# to avoid file-lock contention, while PostgreSQL defaults to two workers.
if [ -z "${WEB_CONCURRENCY:-}" ]; then
    case "$DATABASE_URL" in
        sqlite:*) WEB_CONCURRENCY=1 ;;
        *) WEB_CONCURRENCY=2 ;;
    esac
fi
export WEB_CONCURRENCY
cd backend
../backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "$WEB_CONCURRENCY" &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

echo "=== Backend started with PID $BACKEND_PID ==="
echo "API docs available at: http://localhost:8000/docs"
echo "Demo access endpoint: http://localhost:8000/demo/access"
