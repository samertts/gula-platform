#!/bin/bash
# =============================================================================
# GULA Platform — Safe Deploy Script
# Usage: ./scripts/deploy.sh [--skip-backup] [--branch <name>]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_DIR}/logs/deploy.log"
HEALTH_URL="${HEALTH_URL:-http://localhost:8080/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"   # seconds to wait for health
SKIP_BACKUP=false
BRANCH=""

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-backup) SKIP_BACKUP=true ;;
        --branch) BRANCH="$2"; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
    shift
done

mkdir -p "$(dirname "$LOG_FILE")"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
ok()   { log "✓ $*"; }
fail() { log "✗ $*"; exit 1; }

log "========================================"
log "GULA Deploy started (user=$(whoami))"
log "========================================"

cd "$PROJECT_DIR"

# ── Step 1: Backup database before any change ─────────────────────────────────
if [[ "$SKIP_BACKUP" == "false" ]]; then
    log "Step 1/6: Backing up database..."
    if bash scripts/backup.sh daily >> "$LOG_FILE" 2>&1; then
        ok "Database backup complete"
    else
        fail "Backup failed — deploy aborted (use --skip-backup to override)"
    fi
else
    log "Step 1/6: Backup skipped (--skip-backup)"
fi

# ── Step 2: Pull latest code ──────────────────────────────────────────────────
log "Step 2/6: Pulling latest code..."
if [[ -n "$BRANCH" ]]; then
    git fetch origin "$BRANCH" || fail "git fetch failed"
    git checkout "$BRANCH"     || fail "git checkout failed"
fi
git pull || fail "git pull failed"
ok "Code updated — $(git log -1 --oneline)"

# ── Step 3: Build images (fail fast — do not touch running containers) ────────
log "Step 3/6: Building Docker images..."
if docker compose build --pull 2>&1 | tee -a "$LOG_FILE"; then
    ok "Build successful"
else
    fail "Build failed — running containers are untouched"
fi

# ── Step 4: Run database migrations ──────────────────────────────────────────
log "Step 4/6: Running database migrations (alembic upgrade head)..."
# Start only postgres first, run migrations, then bring up the rest
docker compose up -d postgres 2>&1 | tee -a "$LOG_FILE"
sleep 5  # wait for postgres to be ready
if docker compose run --rm --no-deps gula-backend \
        sh -c "cd /app && alembic upgrade head" 2>&1 | tee -a "$LOG_FILE"; then
    ok "Migrations applied"
else
    fail "Migration failed — database is untouched, no containers started"
fi

# ── Step 5: Start / update containers ────────────────────────────────────────
log "Step 5/7: Starting containers..."
docker compose up -d --remove-orphans 2>&1 | tee -a "$LOG_FILE"
ok "Containers started"

# ── Step 6: Health check (wait up to HEALTH_TIMEOUT seconds) ─────────────────
log "Step 6/7: Waiting for health check (timeout=${HEALTH_TIMEOUT}s)..."
START=$SECONDS
until curl -sf "$HEALTH_URL" > /dev/null 2>&1; do
    if (( SECONDS - START >= HEALTH_TIMEOUT )); then
        log "Health check timed out after ${HEALTH_TIMEOUT}s"
        log "Container status:"
        docker compose ps 2>&1 | tee -a "$LOG_FILE"
        log "Recent backend logs:"
        docker logs gula-backend --tail 30 2>&1 | tee -a "$LOG_FILE"
        fail "Deploy FAILED — check logs above. Manual rollback: git revert HEAD && docker compose up -d --build"
    fi
    sleep 3
done
ok "Health check passed (${HEALTH_URL})"

# ── Step 7: Reload system nginx (pick up any config changes) ─────────────────
log "Step 7/7: Reloading system nginx..."
if systemctl is-active --quiet nginx 2>/dev/null; then
    nginx -t 2>&1 | tee -a "$LOG_FILE" \
        && systemctl reload nginx \
        && ok "System nginx reloaded" \
        || log "WARN: nginx config test failed — not reloading (old config still active)"
else
    log "INFO: system nginx not running, skipping reload"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
log "========================================"
log "Deploy SUCCESSFUL"
log "  Commit : $(git log -1 --oneline)"
log "  Health : $HEALTH_URL"
log "  Rollback command (if needed):"
log "    git revert HEAD && docker compose up -d --build"
log "========================================"
