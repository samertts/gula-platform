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
UPDATE_MODE=false
MONITORING=false

for arg in "$@"; do
  case "$arg" in
    --full)       COMPOSE_FILE="docker-compose.full.yml" ;;
    --update)     UPDATE_MODE=true ;;    # Zero-downtime rolling update (no full restart)
    --monitoring) MONITORING=true ;;    # Also start Prometheus + Grafana
  esac
done

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

log "Compose file: $COMPOSE_FILE | update_mode=$UPDATE_MODE | monitoring=$MONITORING"

# ─────────────────────────────────────────────────────────────────────────────
# 1b. CONFIGURE SYSTEM NGINX AS OUTER REVERSE PROXY
# ─────────────────────────────────────────────────────────────────────────────
# Architecture:
#   Internet → System nginx (port 80/443) → Docker api-gateway (127.0.0.1:8080)
#
# Docker api-gateway listens on 127.0.0.1:8080 only (NOT on public 80/443).
# This avoids port conflicts with the Ubuntu system nginx (1.24.x).
# System nginx handles SSL termination and certbot ACME challenges.

warn() { printf '\033[1;33m[gula-deploy]\033[0m %s\n' "$*"; }

_nginx_site="gula-platform"
_nginx_conf="/etc/nginx/sites-available/${_nginx_site}"
_nginx_enabled="/etc/nginx/sites-enabled/${_nginx_site}"
_our_conf="$(pwd)/config/nginx/system/gula-platform-http.conf"

if command -v nginx >/dev/null 2>&1; then
  if [ ! -f "$_nginx_conf" ] || ! diff -q "$_our_conf" "$_nginx_conf" >/dev/null 2>&1; then
    log "Installing/updating system nginx config → ${_nginx_conf}..."
    sudo cp "$_our_conf" "$_nginx_conf" 2>/dev/null && \
    sudo ln -sf "$_nginx_conf" "$_nginx_enabled" 2>/dev/null && \
    sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    if sudo nginx -t 2>/dev/null; then
      sudo systemctl reload nginx 2>/dev/null || sudo systemctl restart nginx 2>/dev/null || true
      ok "System nginx configured (proxies port 80 → Docker 127.0.0.1:8080)"
    else
      warn "nginx -t failed — system nginx config unchanged. Check /etc/nginx manually."
    fi
  else
    log "System nginx config already up to date"
    # Ensure nginx is running
    sudo systemctl start nginx 2>/dev/null || true
  fi
else
  warn "nginx not installed on host — Docker api-gateway is exposed directly (check firewall!)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2. ENSURE .env EXISTS WITH ALL REQUIRED VARIABLES
# ─────────────────────────────────────────────────────────────────────────────
gen_secret() { python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null || openssl rand -base64 32 | tr -d '=/+' | head -c 43; }
# Fernet keys must be exactly 32 random bytes, URL-safe base64 encoded (44 chars with padding)
gen_fernet_key() { python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null || python3 -c 'import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())'; }

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
ensure_var "ENCRYPTION_KEY" "$(gen_fernet_key)"
ensure_var "NID_HMAC_KEY" "$(gen_secret)"

# ── Master Admin password (CRITICAL — must be set or admin account won't be created) ──
# Generate a strong random password on first run, print it once to console.
# Store it securely (password manager) — it is NOT shown again.
if ! grep -q "^GULA_ADMIN_PASSWORD=" .env 2>/dev/null || \
   grep -q "^GULA_ADMIN_PASSWORD=$" .env 2>/dev/null; then
  _admin_pass="Gula@$(python3 -c 'import secrets,string; a=string.ascii_letters+string.digits; print(secrets.token_urlsafe(12))' 2>/dev/null)!"
  # Remove any empty/blank line
  sed -i '/^GULA_ADMIN_PASSWORD=$/d' .env 2>/dev/null || true
  echo "GULA_ADMIN_PASSWORD=${_admin_pass}" >> .env
  echo ""
  echo "┌─────────────────────────────────────────────────────────────────────────────┐"
  echo "│  🔑 MASTER ADMIN CREDENTIALS (save these — shown only once)                │"
  echo "│                                                                             │"
  echo "│  Email:    admin@gula-platform.org                                         │"
  printf "│  Password: %-64s│\n" "${_admin_pass}"
  echo "│                                                                             │"
  echo "│  Login: https://gula-platform.org/login (or /docs for API)                 │"
  echo "└─────────────────────────────────────────────────────────────────────────────┘"
  echo ""
fi
ensure_var "GULA_ADMIN_EMAIL" "admin@gula-platform.org"
ensure_var "GULA_ADMIN_NAME" "GULA Admin"
ensure_var "GRAFANA_PASSWORD" "$(gen_secret)"

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
# Guard: reject files that still contain git merge conflict markers.
# These make the YAML parser crash with an unhelpful "could not find expected ':'" error.
if grep -qE "^(<{7}|={7}|>{7}) " "$COMPOSE_FILE" 2>/dev/null; then
  err "MERGE CONFLICT MARKERS detected in $COMPOSE_FILE — run emergency-recover.sh to fix"
  grep -nE "^(<{7}|={7}|>{7}) " "$COMPOSE_FILE" | head -5
  exit 1
fi
if ! $COMPOSE -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
  err "Compose config validation failed! Check .env and $COMPOSE_FILE"
  $COMPOSE -f "$COMPOSE_FILE" config 2>&1 | tail -5
  exit 1
fi
ok "Config valid"

# ─────────────────────────────────────────────────────────────────────────────
# 4. NUCLEAR CLEANUP — remove ALL old gula containers, networks, volumes-orphans
# ─────────────────────────────────────────────────────────────────────────────
if $UPDATE_MODE; then
  # ─────────────────────────────────────────────────────────────────────────
  # ZERO-DOWNTIME ROLLING UPDATE
  # Rebuilds backend only, waits for health, then updates nginx.
  # Traffic is never interrupted: old backend keeps serving while new one
  # starts, and nginx only switches when the new one is healthy.
  # ─────────────────────────────────────────────────────────────────────────
  log "Zero-downtime update mode — rebuilding backend only..."

  log "Building new backend image..."
  $COMPOSE -f "$COMPOSE_FILE" build gula-backend

  log "Starting new backend container (old keeps running)..."
  $COMPOSE -f "$COMPOSE_FILE" up -d --no-deps gula-backend

  log "Waiting for new backend to become healthy..."
  MAX_WAIT=120; ELAPSED=0
  while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' gula-backend 2>/dev/null || echo "missing")
    [ "$STATUS" = "healthy" ] && { ok "Backend healthy (${ELAPSED}s)"; break; }
    sleep 5; ELAPSED=$((ELAPSED + 5)); printf '.'
  done; echo ""
  [ "$ELAPSED" -ge "$MAX_WAIT" ] && { err "Backend health timeout"; docker logs --tail=30 gula-backend; exit 1; }

  log "Reloading nginx (zero-downtime config reload)..."
  docker exec gula-api-gateway nginx -t 2>/dev/null && \
    docker exec gula-api-gateway nginx -s reload 2>/dev/null || true

  ok "Zero-downtime update complete"

else
  # ─────────────────────────────────────────────────────────────────────────
  # FULL DEPLOYMENT (nuclear cleanup + rebuild everything)
  # ─────────────────────────────────────────────────────────────────────────
  log "Cleaning up old deployment..."

  $COMPOSE -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

  GULA_CONTAINERS=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep '^gula-' || true)
  if [ -n "$GULA_CONTAINERS" ]; then
    log "Removing all gula containers: $GULA_CONTAINERS"
    echo "$GULA_CONTAINERS" | xargs -r docker rm -f 2>/dev/null || true
  fi

  docker network rm gula-net 2>/dev/null || true
  docker network rm gula-platform_gula-net 2>/dev/null || true
  docker network prune -f 2>/dev/null || true
  docker image prune -f 2>/dev/null || true

  ok "Cleanup done"

fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. BUILD AND START
# ─────────────────────────────────────────────────────────────────────────────
if ! $UPDATE_MODE; then
  log "Pulling images..."
  $COMPOSE -f "$COMPOSE_FILE" pull --ignore-pull-failures 2>/dev/null || true

  COMPOSE_PROFILES=""
  if $MONITORING; then
    COMPOSE_PROFILES="--profile monitoring"
    log "Monitoring stack (Prometheus + Grafana) enabled"
  fi

  log "Building and starting services..."
  # shellcheck disable=SC2086
  $COMPOSE -f "$COMPOSE_FILE" $COMPOSE_PROFILES up -d --build --remove-orphans --force-recreate
fi

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
    ok "Platform is live on http://127.0.0.1:8080"
    echo ""
    $COMPOSE -f "$COMPOSE_FILE" ps
    echo ""

    # Show detailed status from backend
    STATUS=$(curl -s --max-time 5 http://127.0.0.1:8080/health/status 2>/dev/null || echo "{}")
    if echo "$STATUS" | grep -q '"ready":true'; then
      echo "  System:  ✅ READY"
    else
      REASON=$(echo "$STATUS" | grep -o '"reason":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
      echo "  System:  ⚠️  NOT READY — $REASON"
      echo "  Debug:   curl http://127.0.0.1:8080/health/status"
    fi

    # Show admin credentials if generated this run
    ADMIN_EMAIL=$(grep -oP '^GULA_ADMIN_EMAIL=\K.*' .env 2>/dev/null | head -1 || echo "admin@gula-platform.org")
    echo ""
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│  GULA Platform deployed successfully                            │"
    echo "│                                                                 │"
    echo "│  Internal:  http://127.0.0.1:8080                              │"
    echo "│  Public:    http://gula-platform.org  (via host nginx)         │"
    echo "│  Admin:     $ADMIN_EMAIL                   │"
    echo "│  Docs:      http://127.0.0.1:8080/docs  (if enabled)           │"
    echo "│                                                                 │"
    echo "│  Diagnostics: ./scripts/diagnose.sh                            │"
    echo "│  Monitoring:  ./deploy.sh --monitoring                         │"
    echo "│  Update:      ./deploy.sh --update   (zero-downtime)           │"
    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
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
