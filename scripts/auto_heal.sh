#!/usr/bin/env bash
# =============================================================================
# GULA Platform - Self-Healing Script
# Run via cron: */5 * * * * /home/samertts/gula-platform/scripts/auto_heal.sh >> /var/log/gula-heal.log 2>&1
# =============================================================================
set -euo pipefail

PROJECT_DIR="${GULA_DIR:-/home/samertts/gula-platform}"
MAX_RESTARTS_PER_HOUR=3
RESTART_COUNT_FILE="/tmp/gula-restart-count"

cd "$PROJECT_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [HEAL] $*"
}

COMPOSE_CMD=(docker compose)
if ! "${COMPOSE_CMD[@]}" version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
fi

COMPOSE_FILE="${GULA_COMPOSE_FILE:-}"
if [ -z "$COMPOSE_FILE" ]; then
    if [ -f "$PROJECT_DIR/docker-compose.full.yml" ]; then
        COMPOSE_FILE="$PROJECT_DIR/docker-compose.full.yml"
    elif [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
        COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
    else
        log "ERROR: No compose file found"
        exit 2
    fi
fi

compose() {
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" "$@"
}

# Reset restart counter every hour
if [ -f "$RESTART_COUNT_FILE" ]; then
    file_age=$(( $(date +%s) - $(stat -c %Y "$RESTART_COUNT_FILE" 2>/dev/null || echo 0) ))
    if [ "$file_age" -gt 3600 ]; then
        echo "0" > "$RESTART_COUNT_FILE"
    fi
else
    echo "0" > "$RESTART_COUNT_FILE"
fi

restart_count=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo 0)

# Service names (docker compose service keys, not container names)
CRITICAL_SERVICES=(
    "api-gateway"
    "gula-backend"
    "frontend"
    "postgres-primary"
    "redis"
    "pgbouncer"
)

NON_CRITICAL_SERVICES=(
    "rabbitmq"
    "lab-service"
    "patient-service"
    "order-service"
    "result-service"
    "sample-service"
    "notification-service"
)

is_running() {
    compose ps --status running --services 2>/dev/null | grep -qx "$1"
}

restart_service() {
    local service=$1
    if [ "$restart_count" -ge "$MAX_RESTARTS_PER_HOUR" ]; then
        log "ERROR: Max restarts ($MAX_RESTARTS_PER_HOUR/hour) reached. Skipping restart of $service"
        return 1
    fi

    log "Restarting $service..."
    compose restart "$service" 2>/dev/null || compose up -d "$service" 2>/dev/null || true
    restart_count=$((restart_count + 1))
    echo "$restart_count" > "$RESTART_COUNT_FILE"
    log "Restarted $service (restart #$restart_count this hour)"
}

critical_down=0
for service in "${CRITICAL_SERVICES[@]}"; do
    if ! is_running "$service"; then
        log "CRITICAL: $service is DOWN"
        restart_service "$service" || true
        critical_down=$((critical_down + 1))
    fi
done

for service in "${NON_CRITICAL_SERVICES[@]}"; do
    if ! is_running "$service"; then
        log "WARNING: $service is down"
        restart_service "$service" || true
    fi
done

if command -v curl &>/dev/null; then
    if ! curl -sf --max-time 5 "http://localhost/health" >/dev/null 2>&1; then
        log "WARNING: API gateway health check failed"
        if is_running "api-gateway"; then
            restart_service "api-gateway" || true
        fi
    fi
fi

disk_usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$disk_usage" -gt 90 ]; then
    log "WARNING: Disk usage at ${disk_usage}%. Cleaning up..."
    docker system prune -f --volumes 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
fi

mem_available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo 999999)
if [ "$mem_available" -lt 256000 ]; then
    log "WARNING: Low memory (${mem_available}KB available). Restarting non-critical services..."
    for service in "${NON_CRITICAL_SERVICES[@]}"; do
        if is_running "$service"; then
            compose restart "$service" 2>/dev/null || true
        fi
    done
fi

if [ "$critical_down" -eq 0 ]; then
    log "OK: All critical services running"
fi
