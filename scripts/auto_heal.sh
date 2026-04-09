#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Self-Healing Watchdog
#
# Monitors system nginx AND Docker containers.
# Runs every 5 minutes via cron:
#   */5 * * * * /home/samertts/gula-platform/scripts/auto_heal.sh >> /var/log/gula-heal.log 2>&1
#
# ROOT CAUSE FIXES:
#   - Now monitors system nginx (not just Docker)
#   - Service list matches docker-compose.yml (MVP), not full.yml
#   - nginx uses nginx-ensure.sh for smart config selection (HTTP/HTTPS)
# =============================================================================
set -uo pipefail

PROJECT_DIR="${GULA_DIR:-/home/samertts/gula-platform}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
MAX_RESTARTS_PER_HOUR=3
RESTART_COUNT_FILE="/tmp/gula-restart-count"
LOG_PREFIX="$(date '+%Y-%m-%d %H:%M:%S') [HEAL]"

log()  { echo "${LOG_PREFIX} $*"; }
ok()   { echo "${LOG_PREFIX} OK: $*"; }
warn() { echo "${LOG_PREFIX} WARNING: $*"; }
err()  { echo "${LOG_PREFIX} ERROR: $*"; }

# Telegram alert — only fires if TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID are set.
# Set these in /etc/environment or docker-compose environment to enable.
_telegram_alert() {
    local msg="$1"
    local bot="${TELEGRAM_BOT_TOKEN:-}"
    local chat="${TELEGRAM_CHAT_ID:-}"
    [ -z "$bot" ] || [ -z "$chat" ] && return 0
    curl -sf --max-time 5 \
        "https://api.telegram.org/bot${bot}/sendMessage" \
        -d "chat_id=${chat}" \
        -d "text=${msg}" \
        -d "parse_mode=HTML" \
        >/dev/null 2>&1 || true
}

cd "$PROJECT_DIR" || { err "Cannot cd to $PROJECT_DIR"; exit 1; }

# ─── Restart counter (reset every hour) ──────────────────────────────────────
if [ -f "$RESTART_COUNT_FILE" ]; then
    file_age=$(( $(date +%s) - $(stat -c %Y "$RESTART_COUNT_FILE" 2>/dev/null || echo 0) ))
    [ "$file_age" -gt 3600 ] && echo "0" > "$RESTART_COUNT_FILE"
else
    echo "0" > "$RESTART_COUNT_FILE"
fi
restart_count=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo 0)

can_restart() {
    [ "$restart_count" -lt "$MAX_RESTARTS_PER_HOUR" ]
}

bump_restart() {
    restart_count=$((restart_count + 1))
    echo "$restart_count" > "$RESTART_COUNT_FILE"
}

# ─── 1. System nginx check (THE MISSING PIECE) ───────────────────────────────
# nginx is the public-facing entry point. If it's down, site is unreachable
# even if all Docker containers are perfectly healthy.
if ! systemctl is-active --quiet nginx; then
    warn "System nginx is DOWN"
    if can_restart; then
        # Use nginx-ensure.sh: picks HTTP or HTTPS config based on cert presence
        if sudo bash "${PROJECT_DIR}/scripts/nginx-ensure.sh" 2>/dev/null; then
            bump_restart
            log "System nginx restarted (restart #${restart_count}/hour)"
        else
            err "nginx-ensure.sh failed — manual intervention needed"
        fi
    else
        err "Max restarts reached — nginx still DOWN. Check: sudo systemctl status nginx"
    fi
else
    ok "System nginx running"
fi

# ─── 2. Docker daemon check ───────────────────────────────────────────────────
if ! systemctl is-active --quiet docker; then
    warn "Docker daemon is DOWN"
    if can_restart; then
        systemctl start docker && sleep 3
        bump_restart
        log "Docker daemon started (restart #${restart_count}/hour)"
    fi
fi

# ─── 3. Docker containers (MVP docker-compose.yml services) ──────────────────
# These match docker-compose.yml exactly (NOT docker-compose.full.yml)
CRITICAL_SERVICES=(
    "api-gateway"
    "gula-backend"
    "frontend"
    "postgres"
    "redis"
)

compose_running() {
    docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx "$1"
}

restart_container() {
    local svc="$1"
    if ! can_restart; then
        err "Max restarts ($MAX_RESTARTS_PER_HOUR/hour) reached — skipping restart of $svc"
        return 1
    fi
    docker compose -f "$COMPOSE_FILE" restart "$svc" 2>/dev/null \
        || docker compose -f "$COMPOSE_FILE" up -d "$svc" 2>/dev/null \
        || true
    bump_restart
    log "Restarted $svc (restart #${restart_count}/hour)"
    _telegram_alert "⚠️ GULA: restarted <b>${svc}</b> on $(hostname) (${restart_count}/${MAX_RESTARTS_PER_HOUR}/hr)"
}

containers_down=0
for svc in "${CRITICAL_SERVICES[@]}"; do
    if ! compose_running "$svc"; then
        warn "Container $svc is DOWN"
        restart_container "$svc" || true
        containers_down=$((containers_down + 1))
    fi
done

[ "$containers_down" -eq 0 ] && ok "All Docker containers running"

# ─── 4. End-to-end health check ───────────────────────────────────────────────
# Checks the full path: nginx → Docker api-gateway → backend
sleep 2
HTTP_CODE=$(curl -so /dev/null -w "%{http_code}" --max-time 8 "http://localhost/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    ok "End-to-end health check passed (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "000" ]; then
    err "End-to-end health check FAILED — site not responding"
    _telegram_alert "🔴 GULA: site not responding on $(hostname) — HTTP 000"
    # Only restart api-gateway if Docker containers look OK but site is down
    # (handles the case where nginx is up but Docker gateway is stuck)
    if systemctl is-active --quiet nginx && can_restart; then
        warn "Attempting api-gateway restart..."
        restart_container "api-gateway" || true
        sleep 3
        # Reload nginx after container restart (upstream IP may have changed)
        sudo systemctl reload nginx 2>/dev/null || true
    fi
else
    warn "End-to-end health check returned HTTP $HTTP_CODE (expected 200)"
fi

# ─── 5. Disk space guard ──────────────────────────────────────────────────────
disk_pct=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "${disk_pct:-0}" -gt 90 ]; then
    warn "Disk at ${disk_pct}% — pruning Docker..."
    docker system prune -f 2>/dev/null | tail -1 || true
    docker image prune -f 2>/dev/null | tail -1 || true
fi

# ─── 6. Memory guard ──────────────────────────────────────────────────────────
mem_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo 2>/dev/null || echo 999999)
if [ "${mem_kb:-999999}" -lt 200000 ]; then
    warn "Low memory (${mem_kb}KB available) — check for leaks"
fi

# ─── 7. Degradation level alert ──────────────────────────────────────────────
# Poll /monitoring/live and alert if degradation > 0 or kill switch active
MONITORING_TOKEN="${METRICS_BEARER_TOKEN:-}"
MON_URL="http://localhost:8000/monitoring/live"

if command -v curl >/dev/null 2>&1; then
    MON_RESP=$(curl -sf --max-time 4 \
        ${MONITORING_TOKEN:+-H "Authorization: Bearer $MONITORING_TOKEN"} \
        "$MON_URL" 2>/dev/null || echo "")

    if [ -n "$MON_RESP" ]; then
        DEG=$(echo "$MON_RESP" | grep -o '"degradation":[0-9]' | grep -o '[0-9]' || echo "0")
        KS=$(echo  "$MON_RESP" | grep -o '"kill_switch":true' || echo "")

        if [ -n "$KS" ]; then
            warn "Kill switch is ACTIVE — autonomous actions halted"
            _telegram_alert "🔴 GULA: Kill switch ACTIVE on $(hostname)"
        fi
        if [ "${DEG:-0}" -ge 2 ]; then
            warn "Degradation level ${DEG} detected (L2=read-only, L3=critical)"
            _telegram_alert "⚠️ GULA: Degradation L${DEG} on $(hostname)"
        fi
    fi
fi

log "Done (restarts this hour: ${restart_count}/${MAX_RESTARTS_PER_HOUR})"
