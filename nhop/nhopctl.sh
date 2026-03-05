
#!/usr/bin/env bash

# ==========================================================
# NHOP CONTROL TOOL
# Sovereign System Manager
# ==========================================================

set -e

APP_NAME="NHOP"
BACKEND_PORT=3000
FRONTEND_PORT=5173

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

ok() { echo -e "${GREEN}✔ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
fail() { echo -e "${RED}✖ $1${NC}"; }

# ----------------------------------------------------------
# Check Command Exists
# ----------------------------------------------------------

require_cmd () {
  command -v "$1" >/dev/null 2>&1 || {
    fail "$1 not installed"
    exit 1
  }
}

# ----------------------------------------------------------
# Environment Check
# ----------------------------------------------------------

doctor () {

  echo "Running NHOP diagnostics..."
  echo "--------------------------------"

  require_cmd node
  require_cmd npm

  ok "Node installed ($(node -v))"
  ok "NPM installed ($(npm -v))"

  [ -f server.js ] && ok "server.js found" || fail "server.js missing"

  [ -d ../nhop-frontend ] \
  && ok "Frontend detected" \
  || warn "Frontend missing" || warn "Frontend missing"

  [ -d core ] && ok "Core system detected" || warn "Core folder missing"

  check_ports

  echo "--------------------------------"
  ok "Doctor check completed"
}

# ----------------------------------------------------------
# Port Check
# ----------------------------------------------------------

check_ports () {

  if lsof -i :$BACKEND_PORT >/dev/null 2>&1; then
    warn "Backend port $BACKEND_PORT already in use"
  else
    ok "Backend port free"
  fi

  if lsof -i :$FRONTEND_PORT >/dev/null 2>&1; then
    warn "Frontend port $FRONTEND_PORT already in use"
  else
    ok "Frontend port free"
  fi
}

# ----------------------------------------------------------
# Start Backend
# ----------------------------------------------------------

start_backend () {

  echo "Starting Backend..."

  if lsof -i :$BACKEND_PORT >/dev/null 2>&1; then
    warn "Backend already running"
    return
  fi

  node server.js &
  echo $! > .backend.pid

  ok "Backend started"
}

# ----------------------------------------------------------
# Start Frontend
# ----------------------------------------------------------

start_frontend () {

  FRONTEND_DIR="../nhop-frontend"

  if [ ! -d "$FRONTEND_DIR" ]; then
    warn "Frontend directory not found"
    return
  fi

  echo "Starting Frontend..."

  cd "$FRONTEND_DIR"

  if ! grep -q '"dev"' package.json; then
    fail "No dev script in frontend package.json"
    cd - >/dev/null
    return
  fi

  npm run dev &
  echo $! > ../.frontend.pid

  cd - >/dev/null

  ok "Frontend started"
}
# ----------------------------------------------------------
# Stop Services
# ----------------------------------------------------------

stop_all () {

  echo "Stopping NHOP..."

  [ -f .backend.pid ] && kill $(cat .backend.pid) && rm .backend.pid || true
  [ -f .frontend.pid ] && kill $(cat .frontend.pid) && rm .frontend.pid || true

  ok "Services stopped"
}

# ----------------------------------------------------------
# Status
# ----------------------------------------------------------

status () {

  echo "NHOP STATUS"
  echo "--------------------"

  lsof -i :$BACKEND_PORT >/dev/null 2>&1 \
    && ok "Backend running" \
    || warn "Backend stopped"

  lsof -i :$FRONTEND_PORT >/dev/null 2>&1 \
    && ok "Frontend running" \
    || warn "Frontend stopped"
}

# ----------------------------------------------------------
# Install Dependencies
# ----------------------------------------------------------

install () {

  echo "Installing dependencies..."

  npm install

  ok "Dependencies installed"
}

# ----------------------------------------------------------
# Command Router
# ----------------------------------------------------------

case "$1" in
  doctor)
    doctor
    ;;
  start)
    doctor
    start_backend
    start_frontend
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_backend
    start_frontend
    ;;
  status)
    status
    ;;
  install)
    install
    ;;
  *)
    echo "Usage:"
    echo "./nhopctl.sh doctor   - system check"
    echo "./nhopctl.sh start    - start system"
    echo "./nhopctl.sh stop     - stop system"
    echo "./nhopctl.sh restart  - restart"
    echo "./nhopctl.sh status   - show status"
    echo "./nhopctl.sh install  - install deps"
    ;;
esac
