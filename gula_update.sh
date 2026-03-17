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

if [ ! -f "$BASE_DIR/docker-compose.yml" ]; then
  log "docker-compose.yml not found in $BASE_DIR"
  exit 2
fi

if [ ! -f "$BASE_DIR/.env" ]; then
  log "ERROR: .env file not found. Production requires a configured .env."
  log "Copy .env.example and set all values before deploying."
  exit 1
fi

# Deploy lock to prevent concurrent deployments
lock_file="/tmp/gula-deploy.lock"
exec 9>"$lock_file"
if ! flock -n 9; then
  log "Another deployment is running (lock: $lock_file). Exiting."
  exit 1
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

log "Validating compose configuration"
$COMPOSE config >/dev/null

log "Pulling and starting updated services"
$COMPOSE pull --ignore-pull-failures
$COMPOSE up -d --build --remove-orphans

log "Waiting for healthy services (up to 3 minutes)"
for _ in $(seq 1 36); do
  if ./gula_health.sh; then
    log "Deployment completed successfully"
    exit 0
  fi
  sleep 5
done

log "Health checks did not pass in time"
exit 1
