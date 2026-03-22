#!/bin/bash
# =============================================================================
# GULA Platform — Uptime Monitor
# Usage: ./scripts/monitor.sh
# Cron (every minute):  * * * * * /path/to/gula-platform/scripts/monitor.sh
#
# Optional env vars:
#   HEALTH_URL          default: http://localhost:8080/health
#   TELEGRAM_TOKEN      Telegram bot token for alerts
#   TELEGRAM_CHAT_ID    Telegram chat/group ID
#   ALERT_COOLDOWN      Seconds between repeated alerts (default: 300)
#   LOG_FILE            default: /var/log/gula/monitor.log
# =============================================================================

HEALTH_URL="${HEALTH_URL:-http://localhost:8080/health/ready}"
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
ALERT_COOLDOWN="${ALERT_COOLDOWN:-300}"
LOG_FILE="${LOG_FILE:-/var/log/gula/monitor.log}"
LOCK_FILE="/tmp/gula_monitor_alert.lock"

mkdir -p "$(dirname "$LOG_FILE")"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

# ── Send Telegram alert (rate-limited by ALERT_COOLDOWN) ─────────────────────
send_alert() {
    local msg="$1"

    # Skip if no Telegram credentials configured
    if [[ -z "$TELEGRAM_TOKEN" || -z "$TELEGRAM_CHAT_ID" ]]; then
        return
    fi

    # Cooldown: don't spam if the problem persists
    if [[ -f "$LOCK_FILE" ]]; then
        local last
        last=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
        local now
        now=$(date +%s)
        if (( now - last < ALERT_COOLDOWN )); then
            return
        fi
    fi

    date +%s > "$LOCK_FILE"

    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="${msg}" \
        -d parse_mode="Markdown" \
        --max-time 10 > /dev/null 2>&1 || true
}

# ── Health check ──────────────────────────────────────────────────────────────
response=$(curl -sf --max-time 10 "$HEALTH_URL" 2>/dev/null)
exit_code=$?

if [[ $exit_code -ne 0 || -z "$response" ]]; then
    log "FAIL — $HEALTH_URL unreachable (exit=$exit_code)"

    # Collect diagnostics
    container_status=$(docker compose -f /home/samertts/gula-platform/docker-compose.yml ps 2>/dev/null \
        | grep -E "(gula-backend|api-gateway)" | head -5 || echo "unavailable")

    send_alert "🚨 *GULA DOWN*
Host: $(hostname)
URL: ${HEALTH_URL}
Time: $(date '+%Y-%m-%d %H:%M:%S')
Containers:
\`\`\`
${container_status}
\`\`\`"
    exit 1
fi

# ── Service is healthy — clear cooldown lock and log OK ──────────────────────
# /health/ready returns 200 only when DB is reachable (503 otherwise),
# so a successful curl here means both the service AND database are up.
rm -f "$LOCK_FILE"
log "OK — $HEALTH_URL"
