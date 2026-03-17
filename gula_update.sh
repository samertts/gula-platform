#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

log() { printf '[gula_update] %s\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  log "docker is not installed or not in PATH"
  exit 2
fi

COMPOSE_CMD=(docker compose)
if ! "${COMPOSE_CMD[@]}" version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
fi

COMPOSE_FILE="${GULA_COMPOSE_FILE:-}"
if [ -z "$COMPOSE_FILE" ]; then
  if [ -f "$BASE_DIR/docker-compose.full.yml" ]; then
    COMPOSE_FILE="$BASE_DIR/docker-compose.full.yml"
  elif [ -f "$BASE_DIR/docker-compose.yml" ]; then
    COMPOSE_FILE="$BASE_DIR/docker-compose.yml"
  else
    log "No compose file found (expected docker-compose.full.yml or docker-compose.yml)"
    exit 2
  fi
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
  "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --build --remove-orphans
  ./gula_health.sh || true
}

trap 'rollback' ERR

log "Using compose file: $COMPOSE_FILE"
log "Fetching latest code"
git fetch --all --prune
git reset --hard origin/main

log "Validating compose configuration"
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" config >/dev/null

log "Pulling and starting updated services"
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" pull --ignore-pull-failures
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --build --remove-orphans

log "Waiting for healthy services (up to 3 minutes)"
for _ in $(seq 1 36); do
  if GULA_COMPOSE_FILE="$COMPOSE_FILE" ./gula_health.sh; then
    log "Deployment completed successfully"
    exit 0
  fi
  sleep 5
done

log "Health checks did not pass in time"
exit 1
