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

PREVIOUS_COMMIT="$(git rev-parse HEAD)"
rollback() {
  log "Deployment failed - rolling back to ${PREVIOUS_COMMIT}"
  git reset --hard "$PREVIOUS_COMMIT"
  $COMPOSE up -d --build --remove-orphans
  ./gula_health.sh || true
}

trap 'rollback' ERR

log "Fetching latest code"
git fetch --all --prune
git reset --hard origin/main

log "Pulling and starting updated services"
$COMPOSE pull --ignore-pull-failures
$COMPOSE up -d --build --remove-orphans

log "Waiting for healthy services (up to 2 minutes)"
for _ in {1..24}; do
  if ./gula_health.sh; then
    log "Deployment completed successfully"
    exit 0
  fi
  sleep 5
done

log "Health checks did not pass in time"
exit 1
