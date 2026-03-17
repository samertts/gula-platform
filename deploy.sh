#!/usr/bin/env bash
# =============================================================================
# GULA PLATFORM - Production Deployment Script
# Usage: ./deploy.sh [--full]
#
# This is the ONLY script you need to deploy GULA.
# It handles: .env generation, cleanup, build, health check.
# =============================================================================
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

log() { printf '\033[1;36m[gula-deploy]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[gula-deploy]\033[0m %s\n' "$*" >&2; }
ok()  { printf '\033[1;32m[gula-deploy]\033[0m %s\n' "$*"; }

# ─────────────────────────────────────────────────────────────────────────────
# 1. SELECT COMPOSE FILE
# ─────────────────────────────────────────────────────────────────────────────
COMPOSE_FILE="docker-compose.yml"
if [ "${1:-}" = "--full" ]; then
  COMPOSE_FILE="docker-compose.full.yml"
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  err "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

# Detect compose command
COMPOSE="docker compose"
if ! $COMPOSE version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
fi
if ! command -v docker >/dev/null 2>&1; then
  err "Docker is not installed!"
  exit 2
fi

log "Compose file: $COMPOSE_FILE"

# ─────────────────────────────────────────────────────────────────────────────
# 2. ENSURE .env EXISTS WITH ALL REQUIRED VARIABLES
# ─────────────────────────────────────────────────────────────────────────────
gen_secret() { python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null || openssl rand -base64 32 | tr -d '=/+' | head -c 43; }

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    log "No .env found — generating from .env.example with random passwords..."
    cp .env.example .env
  else
    log "No .env found — creating minimal .env..."
    touch .env
  fi
fi

# Auto-generate ALL required variables if missing
ensure_var() {
  local var="$1" val="$2"
  if ! grep -q "^${var}=" .env 2>/dev/null || grep -q "^${var}=CHANGE_ME" .env 2>/dev/null; then
    # Remove old CHANGE_ME line if present
    sed -i "/^${var}=CHANGE_ME/d" .env 2>/dev/null || true
    echo "${var}=${val}" >> .env
    log "Generated: $var"
  fi
}

PG_PASS="$(gen_secret)"
REDIS_PASS="$(gen_secret)"

ensure_var "POSTGRES_PASSWORD" "$PG_PASS"
ensure_var "REDIS_PASSWORD" "$REDIS_PASS"
ensure_var "SECRET_KEY" "$(gen_secret)"
ensure_var "ENCRYPTION_KEY" "$(gen_secret)"
ensure_var "NID_HMAC_KEY" "$(gen_secret)"

# Read actual passwords from .env for dependent vars
ACTUAL_PG_PASS=$(grep -oP '^POSTGRES_PASSWORD=\K.*' .env | head -1)
ACTUAL_REDIS_PASS=$(grep -oP '^REDIS_PASSWORD=\K.*' .env | head -1)

ensure_var "DATABASE_URL" "postgresql://postgres:${ACTUAL_PG_PASS}@postgres:5432/labdb"
ensure_var "REDIS_URL" "redis://:${ACTUAL_REDIS_PASS}@redis:6379"

# Full stack extras
if [ "$COMPOSE_FILE" = "docker-compose.full.yml" ]; then
  ensure_var "MINIO_ACCESS_KEY" "gula_minio"
  ensure_var "MINIO_SECRET_KEY" "$(gen_secret)"
  RABBIT_PASS=$(grep -oP '^RABBITMQ_PASS=\K.*' .env | head -1 || echo "$(gen_secret)")
  ensure_var "RABBITMQ_PASS" "$RABBIT_PASS"
  ensure_var "RABBITMQ_URL" "amqp://gula:${RABBIT_PASS}@rabbitmq:5672/gula"
fi

log "Environment: $(grep -c '=' .env) variables loaded"

# ─────────────────────────────────────────────────────────────────────────────
# 3. VALIDATE COMPOSE CONFIG (catches errors BEFORE destroying running containers)
# ─────────────────────────────────────────────────────────────────────────────
log "Validating compose configuration..."
if ! $COMPOSE -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
  err "Compose config validation failed! Check .env and $COMPOSE_FILE"
  $COMPOSE -f "$COMPOSE_FILE" config 2>&1 | tail -5
  exit 1
fi
ok "Config valid"

# ─────────────────────────────────────────────────────────────────────────────
# 4. NUCLEAR CLEANUP — remove ALL old gula containers, networks, volumes-orphans
# ─────────────────────────────────────────────────────────────────────────────
log "Cleaning up old deployment..."

# Stop current compose project
$COMPOSE -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

# Kill ALL gula-* containers (catches ghosts like gula-core-server)
GULA_CONTAINERS=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep '^gula-' || true)
if [ -n "$GULA_CONTAINERS" ]; then
  log "Removing all gula containers: $GULA_CONTAINERS"
  echo "$GULA_CONTAINERS" | xargs -r docker rm -f 2>/dev/null || true
fi

# Clean up networks
docker network rm gula-net 2>/dev/null || true
docker network rm gula-platform_gula-net 2>/dev/null || true
docker network prune -f 2>/dev/null || true

# Remove dangling images
docker image prune -f 2>/dev/null || true

ok "Cleanup done"

# ─────────────────────────────────────────────────────────────────────────────
# 5. BUILD AND START
# ─────────────────────────────────────────────────────────────────────────────
log "Pulling images..."
$COMPOSE -f "$COMPOSE_FILE" pull --ignore-pull-failures 2>/dev/null || true

log "Building and starting services..."
$COMPOSE -f "$COMPOSE_FILE" up -d --build --remove-orphans --force-recreate

log "Containers started. Waiting for health..."

# ─────────────────────────────────────────────────────────────────────────────
# 6. HEALTH CHECK (wait up to 3 minutes)
# ─────────────────────────────────────────────────────────────────────────────
MAX_WAIT=180
ELAPSED=0

# First wait for backend to be healthy (it takes longest)
log "Waiting for backend..."
while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  BACKEND_STATUS=$(docker inspect --format='{{.State.Health.Status}}' gula-backend 2>/dev/null || echo "missing")
  if [ "$BACKEND_STATUS" = "healthy" ]; then
    ok "Backend healthy (${ELAPSED}s)"
    break
  fi
  if [ "$BACKEND_STATUS" = "missing" ]; then
    err "Backend container not found!"
    $COMPOSE -f "$COMPOSE_FILE" ps
    exit 1
  fi
  sleep 5
  ELAPSED=$((ELAPSED + 5))
  printf '.'
done
echo ""

if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
  err "Backend did not become healthy in ${MAX_WAIT}s"
  log "Backend logs:"
  docker logs --tail=30 gula-backend 2>/dev/null || true
  exit 1
fi

# Then check the full platform via api-gateway
log "Checking api-gateway..."
sleep 3
for i in $(seq 1 12); do
  if curl -fsS --max-time 5 http://127.0.0.1:8080/health >/dev/null 2>&1; then
    ok "Platform is live!"
    echo ""
    $COMPOSE -f "$COMPOSE_FILE" ps
    echo ""
    ok "=== GULA PLATFORM DEPLOYED SUCCESSFULLY ==="
    exit 0
  fi
  sleep 5
done

# Gateway not responding - show debug info
err "API gateway not responding on port 8080"
echo ""
log "Container status:"
$COMPOSE -f "$COMPOSE_FILE" ps
echo ""
log "API Gateway logs:"
docker logs --tail=20 gula-api-gateway 2>/dev/null || true
echo ""
log "Backend logs:"
docker logs --tail=20 gula-backend 2>/dev/null || true
echo ""
log "System nginx status:"
sudo systemctl status nginx --no-pager 2>/dev/null || echo "  (no system nginx)"
echo ""
log "Ports listening:"
ss -tlnp | grep -E ':(80|443|8080|8443)\s' 2>/dev/null || echo "  (none on expected ports)"
exit 1
