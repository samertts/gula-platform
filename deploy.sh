#!/usr/bin/env bash
# =============================================================================
# GULA PLATFORM - Safe Deployment Script
# Usage: ./deploy.sh [--full]
# =============================================================================
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

log() { printf '\033[1;36m[deploy]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[deploy]\033[0m %s\n' "$*" >&2; }

# Select compose file
COMPOSE_FILE="docker-compose.yml"
if [ "${1:-}" = "--full" ]; then
  COMPOSE_FILE="docker-compose.full.yml"
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  err "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

if [ ! -f .env ]; then
  err "No .env file found. Copy .env.example and configure it."
  exit 1
fi

log "Using: $COMPOSE_FILE"

# 1. Stop old containers and remove orphans (prevents gula-core-server ghost)
log "Stopping old containers and removing orphans..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

# 2. Remove any stale containers not in current compose file
STALE_CONTAINERS=$(docker ps -a --filter "network=gula-net" --format '{{.Names}}' 2>/dev/null | grep -v -E '^(gula-postgres|gula-redis|gula-backend|gula-frontend|gula-api-gateway)$' || true)
if [ -n "$STALE_CONTAINERS" ]; then
  log "Removing stale containers: $STALE_CONTAINERS"
  echo "$STALE_CONTAINERS" | xargs -r docker rm -f 2>/dev/null || true
fi

# 3. Clean up dangling networks
docker network prune -f 2>/dev/null || true

# 4. Build and start
log "Building and starting services..."
docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans

# 5. Wait for health
log "Waiting for services to become healthy..."
MAX_WAIT=120
ELAPSED=0
while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  if curl -fsS --max-time 5 http://127.0.0.1:8080/health >/dev/null 2>&1; then
    log "Platform is healthy! (${ELAPSED}s)"
    docker compose -f "$COMPOSE_FILE" ps
    exit 0
  fi
  sleep 5
  ELAPSED=$((ELAPSED + 5))
  printf '.'
done

echo ""
err "Health check failed after ${MAX_WAIT}s"
log "Container status:"
docker compose -f "$COMPOSE_FILE" ps
log "Backend logs (last 30 lines):"
docker compose -f "$COMPOSE_FILE" logs --tail=30 gula-backend 2>/dev/null || true
log "API Gateway logs (last 15 lines):"
docker compose -f "$COMPOSE_FILE" logs --tail=15 api-gateway 2>/dev/null || true
exit 1
