#!/bin/bash
# =============================================================================
# GULA Platform — Emergency Server Fix Script
# Run as root on the DigitalOcean server:
#   bash scripts/fix-server.sh
# =============================================================================

set -euo pipefail
log() { echo "[$(date '+%H:%M:%S')] $*"; }
ok()  { echo "[OK] $*"; }
err() { echo "[ERR] $*" >&2; }

# ── 1. Fix broken git config ──────────────────────────────────────────────────
log "Fixing git config..."
git config --global pull.rebase true
git config --global --unset pull.rebase 2>/dev/null || true  # remove broken value first
git config --global pull.rebase true
ok "git config pull.rebase = true"

# ── 2. Pull latest code ────────────────────────────────────────────────────────
log "Pulling latest code from main..."
git fetch origin main
git reset --hard origin/main
ok "Code updated to: $(git log -1 --oneline)"

# ── 3. Check containers ────────────────────────────────────────────────────────
log "Container status:"
docker compose ps

# ── 4. Restart all containers ─────────────────────────────────────────────────
log "Restarting containers..."
docker compose down --remove-orphans
docker compose up -d --build
ok "Containers started"

# ── 5. Wait for backend health ────────────────────────────────────────────────
log "Waiting for backend to become healthy..."
for i in $(seq 1 20); do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        ok "Backend healthy after ${i}s"
        break
    fi
    if [[ $i -eq 20 ]]; then
        err "Backend not healthy after 40s. Logs:"
        docker logs gula-backend --tail 30
        exit 1
    fi
    sleep 2
done

# ── 6. Test login endpoint ────────────────────────────────────────────────────
log "Testing API endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/api/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test"}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "401" ]]; then
    ok "API is responding correctly (401 = server is up, wrong credentials expected)"
elif [[ "$HTTP_CODE" == "000" ]]; then
    err "API unreachable — check nginx proxy"
else
    log "API returned HTTP $HTTP_CODE"
fi

log "=== Fix complete ==="
log "  Health URL: http://localhost:8080/health"
log "  Test in browser: https://gula-platform.org/login.html"
docker compose ps
