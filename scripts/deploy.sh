#!/bin/bash
# =============================================================================
# GULA Platform — Safe Deploy Script
# Usage: ./scripts/deploy.sh [--skip-backup] [--branch <name>]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_DIR}/logs/deploy.log"
# Nginx listens on port 80 inside the Docker network; use localhost:80 for smoke tests
HEALTH_URL="${HEALTH_URL:-http://localhost/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-180}"   # seconds to wait for health
SKIP_BACKUP=false
BRANCH=""
LOCK_FILE="/tmp/gula_deploy.lock"

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
fail() { log "✗ $*"; rm -f "$LOCK_FILE"; exit 1; }

# ── Deploy lock (prevent concurrent runs) ────────────────────────────────────
if [[ -f "$LOCK_FILE" ]]; then
    echo "ERROR: Another deploy is in progress (lock: $LOCK_FILE). Aborting."
    exit 1
fi
trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

log "========================================"
log "GULA Deploy started (user=$(whoami))"
log "========================================"

cd "$PROJECT_DIR"

# ── Pre-flight: secrets validation ────────────────────────────────────────────
log "Pre-flight: checking required secrets..."
if [[ ! -f ".env" ]]; then
    fail ".env file not found — run: cp .env.example .env  then fill in the values"
fi
REQUIRED_SECRETS=(
    "SECRET_KEY" "REFRESH_TOKEN_SECRET" "ENCRYPTION_KEY"
    "NID_HMAC_KEY" "POSTGRES_PASSWORD" "REDIS_PASSWORD"
)
MISSING=0
for secret in "${REQUIRED_SECRETS[@]}"; do
    value=$(grep -E "^${secret}=" .env | cut -d= -f2- | tr -d '"' | tr -d "'" | head -1 || true)
    if [[ -z "$value" || "$value" == *"CHANGE_ME"* ]]; then
        log "  MISSING: $secret"
        MISSING=$((MISSING + 1))
    fi
done
[[ $MISSING -gt 0 ]] && fail "$MISSING required secret(s) not set — fill in .env before deploying"
ok "All required secrets present"

# ── Pre-flight: disk space (need at least 3 GB free) ─────────────────────────
DISK_FREE_MB=$(df -m "$PROJECT_DIR" | awk 'NR==2 {print $4}')
if [[ $DISK_FREE_MB -lt 3072 ]]; then
    fail "Only ${DISK_FREE_MB} MB disk free — need 3 GB. Run: docker system prune -f"
fi
ok "Disk free: ${DISK_FREE_MB} MB"

# ── Step 1: Backup database before any change ─────────────────────────────────
if [[ "$SKIP_BACKUP" == "false" ]]; then
    log "Step 1/7: Backing up database..."
    if bash scripts/backup.sh daily >> "$LOG_FILE" 2>&1; then
        ok "Database backup complete"
    else
        fail "Backup failed — deploy aborted (use --skip-backup to override)"
    fi
else
    log "Step 1/7: Backup skipped (--skip-backup)"
fi

# ── Step 2: Pull latest code ──────────────────────────────────────────────────
log "Step 2/7: Pulling latest code..."
if [[ -n "$BRANCH" ]]; then
    git fetch origin "$BRANCH" || fail "git fetch failed"
    git checkout "$BRANCH"     || fail "git checkout failed"
fi
git pull || fail "git pull failed"
ok "Code updated — $(git log -1 --oneline)"

# ── Step 3: Build images (fail fast — do not touch running containers) ────────
log "Step 3/7: Building Docker images..."
if docker compose build --pull 2>&1 | tee -a "$LOG_FILE"; then
    ok "Build successful"
else
    fail "Build failed — running containers are untouched"
fi

# ── Step 4: Run database migrations ──────────────────────────────────────────
log "Step 4/7: Running database migrations (alembic upgrade head)..."
docker compose up -d postgres 2>&1 | tee -a "$LOG_FILE"

# Wait for postgres to be genuinely ready (not just started)
log "Waiting for postgres to accept connections..."
for i in $(seq 1 30); do
    if docker compose exec -T postgres pg_isready -q 2>/dev/null; then
        ok "Postgres ready (attempt $i)"
        break
    fi
    if [[ $i -eq 30 ]]; then
        fail "Postgres did not become ready after 60s"
    fi
    sleep 2
done

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

# ── Step 7: Recreate api-gateway + reload system nginx ────────────────────────
log "Step 7/7: Applying nginx configs..."

# Force-recreate api-gateway so it always boots with the current config from disk.
# `nginx -s reload` can fail silently or miss volume changes; recreate is definitive.
log "Recreating api-gateway container..."
if docker compose up -d --force-recreate --no-deps api-gateway 2>&1 | tee -a "$LOG_FILE"; then
    ok "api-gateway recreated with current config"
else
    fail "api-gateway recreate failed — check docker compose logs above"
fi

# System nginx — reload to pick up any changes to /etc/nginx/sites-available/
if systemctl is-active --quiet nginx 2>/dev/null; then
    nginx -t 2>&1 | tee -a "$LOG_FILE" \
        && systemctl reload nginx \
        && ok "System nginx reloaded" \
        || log "WARN: system nginx config test failed — not reloading (old config still active)"
else
    log "INFO: system nginx not running, skipping reload"
fi

# ── Step 7b: Smoke tests ──────────────────────────────────────────────────────
log "Smoke tests..."
SMOKE_PASS=0; SMOKE_FAIL=0

_smoke() {
    local desc="$1" url="$2" expected="$3"
    local code
    code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "ERR")
    if [[ "$code" == "$expected" ]]; then
        ok "  [$code] $desc"
        SMOKE_PASS=$((SMOKE_PASS + 1))
    else
        log "  WARN [$code != $expected] $desc"
        SMOKE_FAIL=$((SMOKE_FAIL + 1))
    fi
}

_smoke "Health liveness"   "http://localhost/health"             "200"
_smoke "Health readiness"  "http://localhost/health/ready"       "200"
_smoke "Health deep"       "http://localhost/health/deep"        "200"
_smoke "Auth gate (401)"   "http://localhost/api/patients"       "401"
_smoke "AI providers"      "http://localhost/api/ai/providers"   "200"
_smoke "Optimizer metrics" "http://localhost/api/optimizer/metrics" "401"

log "Smoke: ${SMOKE_PASS} passed, ${SMOKE_FAIL} failed"
[[ $SMOKE_FAIL -ge 3 ]] && log "WARN: multiple smoke failures — check logs"

# ── Done ──────────────────────────────────────────────────────────────────────
log "========================================"
log "Deploy SUCCESSFUL"
log "  Commit  : $(git log -1 --oneline)"
log "  Branch  : $(git rev-parse --abbrev-ref HEAD)"
log "  Health  : $HEALTH_URL"
log "  Smoke   : ${SMOKE_PASS} pass / ${SMOKE_FAIL} fail"
log "  Rollback: git revert HEAD && bash scripts/deploy.sh --skip-backup"
log "========================================"
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || docker compose ps
