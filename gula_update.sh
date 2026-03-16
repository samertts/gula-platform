#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

log() { printf '[gula_update] %s\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  log "docker is not installed or not in PATH"
  exit 2
fi

COMPOSE="docker compose"
if ! $COMPOSE version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
fi

rollback() {
  log "Deployment failed - rolling back to previous commit"
  git reset --hard HEAD~1
  $COMPOSE up -d --build
  ./gula_health.sh || true
}

trap 'rollback' ERR

log "Fetching latest code"
git fetch --all --prune
git reset --hard origin/main

log "Pulling and starting updated services"
$COMPOSE pull --ignore-pull-failures
$COMPOSE up -d --build --remove-orphans

log "Waiting for containers to initialize"
sleep 15

log "Validating health endpoints"
./gula_health.sh

log "Deployment completed successfully"
