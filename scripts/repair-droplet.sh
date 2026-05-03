#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Droplet Repair Script
# =============================================================================
#
# Fixes the four P0 issues identified by scripts/diagnose-droplet.sh:
#
#   1. Broken systemd `gula.service` stuck in restart loop
#      ("uvicorn app.main :app" — note the bad space).
#      Action: disable + remove the rogue unit. The correct unit is
#      `gula-platform.service` from server-setup.sh.
#
#   2. system nginx in `start-pre` loop because it cannot read
#      Let's Encrypt certs (nginx running without root).
#      Action: reset failed state, ensure nginx-ensure.sh runs as root,
#      fall back to HTTP-only config if HTTPS cert is unreadable.
#
#   3. Alembic revision drift — DB at 20260405_0015, code head at
#      20260428_0001 (Edge Platform).
#      Action: backup DB, then `alembic upgrade head`.
#
#   4. api-gateway unhealthy (cascading from #1 / Docker churn).
#      Action: clean `docker compose down && up -d` after #1 is fixed.
#
# Plus:
#   - Mandatory DB backup BEFORE any destructive action
#   - SSH hardening (PasswordAuthentication no) — prompted, not automatic
#   - Docker cleanup of dangling images (saves ~8GB based on diagnosis)
#
# Usage (as the deploy user, e.g. samertts):
#
#   chmod +x scripts/repair-droplet.sh
#   sudo ./scripts/repair-droplet.sh             # interactive, asks before risky steps
#   sudo ./scripts/repair-droplet.sh --yes       # non-interactive (CI / scripted)
#   sudo ./scripts/repair-droplet.sh --skip-migrate  # skip alembic step
#
# This script is idempotent — safe to re-run.
# =============================================================================

set -uo pipefail

# ── Args ────────────────────────────────────────────────────────────────────
ASSUME_YES=0
SKIP_MIGRATE=0
SKIP_HARDEN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --yes|-y)         ASSUME_YES=1; shift ;;
        --skip-migrate)   SKIP_MIGRATE=1; shift ;;
        --skip-harden)    SKIP_HARDEN=1; shift ;;
        -h|--help)        sed -n '2,40p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

# ── Colours ─────────────────────────────────────────────────────────────────
RED=$'\033[1;31m'; GREEN=$'\033[1;32m'; YELLOW=$'\033[1;33m'
CYAN=$'\033[1;36m'; BOLD=$'\033[1m'; NC=$'\033[0m'

log()   { printf "%s[*]%s %s\n"  "$CYAN"   "$NC" "$*"; }
ok()    { printf "%s[✓]%s %s\n" "$GREEN"  "$NC" "$*"; }
warn()  { printf "%s[!]%s %s\n"  "$YELLOW" "$NC" "$*"; }
err()   { printf "%s[✗]%s %s\n" "$RED"    "$NC" "$*" >&2; }
fatal() { err "$*"; exit 1; }
step()  { printf "\n%s%s%s\n%s%s%s\n" "$BOLD" "$(printf '=%.0s' {1..70})" "$NC" "$BOLD" "  $*" "$NC"; }

ask() {
    # ask "Question" → returns 0 if user says yes (or --yes was passed)
    [ "$ASSUME_YES" -eq 1 ] && return 0
    local prompt="$1"
    local reply
    printf "%s%s%s [y/N]: " "$YELLOW" "$prompt" "$NC"
    read -r reply
    case "$reply" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# ── Pre-flight ──────────────────────────────────────────────────────────────
[ "$(id -u)" -eq 0 ] || fatal "Run with sudo: sudo $0"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR" || fatal "Cannot cd to $REPO_DIR"

# Detect deploy user (owner of repo)
DEPLOY_USER="$(stat -c '%U' "$REPO_DIR")"
[ -n "$DEPLOY_USER" ] || DEPLOY_USER="samertts"

# Detect docker compose
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DC="docker-compose"
else
    fatal "docker compose not found"
fi

log "Repo dir    : $REPO_DIR"
log "Deploy user : $DEPLOY_USER"
log "Compose CLI : $DC"
log "Mode        : $([ "$ASSUME_YES" -eq 1 ] && echo non-interactive || echo interactive)"

# =============================================================================
step "Step 0/7 — Mandatory database backup"
# =============================================================================
BACKUP_DIR="$REPO_DIR/backups"
mkdir -p "$BACKUP_DIR"
chown "$DEPLOY_USER:$DEPLOY_USER" "$BACKUP_DIR" 2>/dev/null || true

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="$BACKUP_DIR/pre-repair-${TS}.sql.gz"

if $DC ps postgres 2>/dev/null | grep -q "Up"; then
    log "Dumping all databases to $BACKUP_FILE ..."
    if $DC exec -T postgres pg_dumpall -U postgres 2>/dev/null | gzip > "$BACKUP_FILE"; then
        SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
        ok "Backup created: $BACKUP_FILE ($SIZE)"
    else
        rm -f "$BACKUP_FILE"
        fatal "pg_dumpall failed — refusing to continue without a backup"
    fi
else
    warn "Postgres container not running — skipping backup (nothing to back up)"
fi

# =============================================================================
step "Step 1/7 — Disable broken gula.service"
# =============================================================================
if systemctl list-unit-files gula.service >/dev/null 2>&1; then
    log "Found gula.service — checking state..."
    systemctl status gula.service --no-pager 2>&1 | head -5 || true

    if ask "Disable and remove the broken gula.service unit?"; then
        systemctl stop    gula.service 2>/dev/null || true
        systemctl disable gula.service 2>/dev/null || true
        systemctl reset-failed gula.service 2>/dev/null || true

        # Remove the broken unit file (only if it's the rogue one — never the repo's)
        for unit_path in /etc/systemd/system/gula.service /lib/systemd/system/gula.service; do
            if [ -f "$unit_path" ]; then
                if grep -q "uvicorn app.main :app" "$unit_path" 2>/dev/null; then
                    log "Removing broken unit: $unit_path"
                    mv "$unit_path" "${unit_path}.broken-${TS}"
                    ok "Moved to ${unit_path}.broken-${TS}"
                else
                    warn "$unit_path exists but doesn't match the broken signature — leaving it alone"
                fi
            fi
        done
        systemctl daemon-reload
        ok "gula.service disabled"
    else
        warn "Skipped (gula.service still in restart loop — fix manually)"
    fi
else
    ok "No gula.service unit installed"
fi

# Verify the correct unit (gula-platform.service from server-setup.sh) exists
if systemctl list-unit-files gula-platform.service >/dev/null 2>&1; then
    ok "Correct unit gula-platform.service is present"
else
    warn "gula-platform.service not installed — Docker stack will only run while terminal is open."
    warn "  To install it:  sudo bash $REPO_DIR/scripts/server-setup.sh  (re-run partial)"
    warn "  Or copy:        sudo cp $REPO_DIR/scripts/gula.service /etc/systemd/system/gula-platform.service"
fi

# =============================================================================
step "Step 2/7 — Stop nginx loop & repair its systemd state"
# =============================================================================
if systemctl list-unit-files nginx.service >/dev/null 2>&1; then
    log "Stopping nginx (was in start-pre loop)..."
    systemctl stop nginx 2>/dev/null || true
    systemctl reset-failed nginx 2>/dev/null || true

    DROPIN_DIR="/etc/systemd/system/nginx.service.d"
    DROPIN_FILE="$DROPIN_DIR/gula-restart.conf"
    if [ -f "$DROPIN_FILE" ]; then
        log "Inspecting drop-in: $DROPIN_FILE"
        cat "$DROPIN_FILE" | sed 's/^/    /'
    fi

    # The drop-in calls nginx-ensure.sh which needs root + the right env
    NGINX_ENSURE="$REPO_DIR/scripts/nginx-ensure.sh"
    if [ -x "$NGINX_ENSURE" ]; then
        log "Running nginx-ensure.sh as root (chooses HTTP-only or HTTPS based on certs)..."
        if GULA_DIR="$REPO_DIR" bash "$NGINX_ENSURE" 2>&1 | sed 's/^/    /'; then
            ok "nginx-ensure.sh completed"
        else
            warn "nginx-ensure.sh exited non-zero — see /var/log/gula-nginx-ensure.log"
        fi
    fi

    # nginx-ensure.sh starts nginx itself, but verify
    sleep 2
    if systemctl is-active --quiet nginx; then
        ok "nginx is active"
        ss -tlnp 2>/dev/null | grep -E ':80\s|:443\s' | sed 's/^/    /' || true
    else
        warn "nginx still not active. Run for details:"
        warn "  sudo systemctl status nginx --no-pager"
        warn "  sudo tail -50 /var/log/gula-nginx-ensure.log"
        warn "  sudo nginx -t"
    fi
else
    warn "system nginx not installed — skipping"
fi

# =============================================================================
step "Step 3/7 — Restart Docker stack cleanly"
# =============================================================================
log "Bringing stack down..."
$DC down --remove-orphans 2>&1 | tail -5 || true

log "Starting stack..."
$DC up -d 2>&1 | tail -10

log "Waiting 30s for containers to settle..."
sleep 30

log "Container state:"
$DC ps 2>&1 | sed 's/^/    /'

# =============================================================================
step "Step 4/7 — Apply pending Alembic migrations"
# =============================================================================
if [ "$SKIP_MIGRATE" -eq 1 ]; then
    warn "Skipped (--skip-migrate)"
else
    log "Current revision before migration:"
    $DC exec -T gula-backend alembic current 2>&1 | sed 's/^/    /' || true

    log "Heads in code:"
    $DC exec -T gula-backend alembic heads 2>&1 | sed 's/^/    /' || true

    if ask "Apply 'alembic upgrade head' now? (backup already taken in Step 0)"; then
        if $DC exec -T gula-backend alembic upgrade head 2>&1 | sed 's/^/    /'; then
            ok "Migration applied"
            log "Revision after migration:"
            $DC exec -T gula-backend alembic current 2>&1 | sed 's/^/    /' || true
        else
            err "Migration failed — DB is unchanged from backup at $BACKUP_FILE"
            err "Inspect: $DC exec gula-backend alembic upgrade head"
            err "If needed, restore: gunzip -c $BACKUP_FILE | $DC exec -T postgres psql -U postgres"
            exit 1
        fi
    else
        warn "Skipped — DB still at older revision; backend may complain"
    fi
fi

# =============================================================================
step "Step 5/7 — Verify backend health"
# =============================================================================
log "Waiting up to 60s for backend to become ready..."
for i in $(seq 1 30); do
    if curl -fsS --max-time 3 http://127.0.0.1:8080/health/ready >/dev/null 2>&1; then
        ok "Backend ready (after ${i}x2s)"
        break
    fi
    [ "$i" -eq 30 ] && warn "Backend did not become ready within 60s"
    sleep 2
done

log "GET /health/deep:"
curl -fsS --max-time 5 http://127.0.0.1:8080/health/deep 2>&1 \
    | python3 -m json.tool 2>/dev/null \
    | sed 's/^/    /' \
    || warn "  /health/deep did not return JSON — inspect: $DC logs gula-backend"

# =============================================================================
step "Step 6/7 — Optional security hardening"
# =============================================================================
if [ "$SKIP_HARDEN" -eq 1 ]; then
    warn "Skipped (--skip-harden)"
else
    SSHD_FILE="/etc/ssh/sshd_config"
    if grep -qE '^PasswordAuthentication\s+yes' "$SSHD_FILE"; then
        warn "SSH PasswordAuthentication is currently 'yes' — this allows brute-force attacks."
        warn "Before changing, MAKE SURE you can log in via SSH key. Test from another terminal:"
        warn "    ssh -o PasswordAuthentication=no $DEPLOY_USER@<server-ip>"
        if ask "Set 'PasswordAuthentication no' in $SSHD_FILE?"; then
            cp "$SSHD_FILE" "${SSHD_FILE}.bak-${TS}"
            sed -i 's/^PasswordAuthentication\s\+yes/PasswordAuthentication no/' "$SSHD_FILE"
            if sshd -t 2>&1; then
                systemctl reload ssh 2>/dev/null || systemctl reload sshd
                ok "Password auth disabled. Backup: ${SSHD_FILE}.bak-${TS}"
            else
                err "sshd config test failed — restoring backup"
                mv "${SSHD_FILE}.bak-${TS}" "$SSHD_FILE"
            fi
        else
            warn "Skipped — recommend doing this manually after verifying key-based login."
        fi
    else
        ok "SSH PasswordAuthentication already disabled"
    fi
fi

# =============================================================================
step "Step 7/7 — Docker cleanup (reclaim disk)"
# =============================================================================
log "Before cleanup:"
docker system df 2>&1 | sed 's/^/    /'

if ask "Run 'docker image prune -a' to reclaim ~8GB of unused images?"; then
    docker image prune -af 2>&1 | tail -3 | sed 's/^/    /'
    docker builder prune -af 2>&1 | tail -3 | sed 's/^/    /'
    ok "Cleanup done"
    log "After cleanup:"
    docker system df 2>&1 | sed 's/^/    /'
else
    warn "Skipped"
fi

# =============================================================================
step "Repair complete"
# =============================================================================
ok "All requested steps finished."
log ""
log "Summary of artifacts:"
log "  DB backup        : $BACKUP_FILE"
log "  SSH config bak   : ${SSHD_FILE}.bak-${TS} (if SSH was hardened)"
log "  Broken unit bak  : /etc/systemd/system/gula.service.broken-${TS} (if it existed)"
log ""
log "Next manual checks:"
log "  1. From your laptop:  curl -I https://gula-platform.org/health"
log "  2. Container status:  $DC ps        (all should be 'Up (healthy)')"
log "  3. Backend logs:      $DC logs --tail=50 gula-backend"
log "  4. SSL renewal:       sudo certbot renew --dry-run"
log "  5. Schedule backup cron (if not already):"
log "       echo '0 3 * * * cd $REPO_DIR && bash scripts/backup.sh' | sudo -u $DEPLOY_USER crontab -"
