#!/bin/bash
# =============================================================================
# GULA Platform — Quick Start Script
# Fixes 502 Bad Gateway and ensures all containers are running.
# Run as root: bash scripts/start.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }
err()  { echo "[ERR] $*" >&2; }

cd "$PROJECT_DIR"

log "GULA Platform — Starting up..."

# ── 1. Ensure logs directory exists ──────────────────────────────────────────
mkdir -p logs/nginx

# ── 2. Check Docker is running ───────────────────────────────────────────────
if ! docker info > /dev/null 2>&1; then
    err "Docker daemon not running. Starting..."
    systemctl start docker || { err "Cannot start Docker. Run: systemctl start docker"; exit 1; }
fi
ok "Docker daemon running"

# ── 3. Bring up containers ────────────────────────────────────────────────────
log "Starting containers..."
docker compose up -d --remove-orphans
ok "Containers started"

# ── 4. Wait for backend to be healthy ────────────────────────────────────────
log "Waiting for backend to become healthy (max 60s)..."
for i in $(seq 1 30); do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' gula-backend 2>/dev/null || echo "missing")
    if [[ "$STATUS" == "healthy" ]]; then
        ok "Backend healthy after $((i * 2))s"
        break
    fi
    if [[ "$STATUS" == "unhealthy" ]]; then
        warn "Backend is unhealthy — showing logs:"
        docker logs gula-backend --tail 40
        break
    fi
    if [[ $i -eq 30 ]]; then
        warn "Backend not yet healthy after 60s — check: docker logs gula-backend"
    fi
    sleep 2
done

# ── 5. Show status ────────────────────────────────────────────────────────────
log "Container status:"
docker compose ps

# ── 6. Quick API test ────────────────────────────────────────────────────────
log "Testing API health endpoint..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null || echo "000")
if [[ "$HEALTH_CODE" == "200" ]]; then
    ok "API health check passed (HTTP 200)"
elif [[ "$HEALTH_CODE" == "000" ]]; then
    warn "API unreachable on port 80. Check: docker compose logs api-gateway"
else
    warn "API returned HTTP $HEALTH_CODE"
fi

log "=== Start complete. Platform at: https://gula-platform.org ==="
