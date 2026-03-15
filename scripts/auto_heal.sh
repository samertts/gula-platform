#!/usr/bin/env bash
# =============================================================================
# GULA Platform - Self-Healing Script
# Run via cron: */5 * * * * /home/samertts/gula-platform/scripts/auto_heal.sh >> /var/log/gula-heal.log 2>&1
# =============================================================================
set -euo pipefail

PROJECT_DIR="${GULA_DIR:-/home/samertts/gula-platform}"
LOG_FILE="/var/log/gula-heal.log"
MAX_RESTARTS_PER_HOUR=3
RESTART_COUNT_FILE="/tmp/gula-restart-count"

cd "$PROJECT_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [HEAL] $*"
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

# Critical services that must be running
CRITICAL_SERVICES=(
    "gula-api-gateway"
    "gula-backend"
    "gula-frontend"
    "gula-postgres-primary"
    "gula-redis"
    "gula-pgbouncer"
)

# Non-critical services (restart if down, but don't alarm)
NON_CRITICAL_SERVICES=(
    "gula-rabbitmq"
    "gula-lab-service"
    "gula-patient-service"
    "gula-order-service"
    "gula-result-service"
    "gula-sample-service"
    "gula-notification-service"
)

is_running() {
    docker ps --format '{{.Names}}' | grep -q "^${1}$"
}

is_healthy() {
    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "$1" 2>/dev/null || echo "none")
    [ "$health" = "healthy" ] || [ "$health" = "none" ]
}

restart_service() {
    local service=$1
    if [ "$restart_count" -ge "$MAX_RESTARTS_PER_HOUR" ]; then
        log "ERROR: Max restarts ($MAX_RESTARTS_PER_HOUR/hour) reached. Skipping restart of $service"
        return 1
    fi

    log "Restarting $service..."
    docker compose restart "$service" 2>/dev/null || docker compose up -d "$service" 2>/dev/null || true
    restart_count=$((restart_count + 1))
    echo "$restart_count" > "$RESTART_COUNT_FILE"
    log "Restarted $service (restart #$restart_count this hour)"
}

# Check critical services
critical_down=0
for service in "${CRITICAL_SERVICES[@]}"; do
    if ! is_running "$service"; then
        log "CRITICAL: $service is DOWN"
        restart_service "$service" || true
        critical_down=$((critical_down + 1))
    fi
done

# Check non-critical services
for service in "${NON_CRITICAL_SERVICES[@]}"; do
    if ! is_running "$service"; then
        log "WARNING: $service is down"
        restart_service "$service" || true
    fi
done

# Health check via HTTP
if command -v curl &>/dev/null; then
    if ! curl -sf --max-time 5 "http://localhost/health" >/dev/null 2>&1; then
        log "WARNING: API gateway health check failed"
        if is_running "gula-api-gateway"; then
            restart_service "gula-api-gateway" || true
        fi
    fi
fi

# Disk space check
disk_usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$disk_usage" -gt 90 ]; then
    log "WARNING: Disk usage at ${disk_usage}%. Cleaning up..."
    docker system prune -f --volumes 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
fi

# Memory check
mem_available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo 999999)
if [ "$mem_available" -lt 256000 ]; then  # Less than 256MB
    log "WARNING: Low memory (${mem_available}KB available). Restarting non-critical services..."
    for service in "${NON_CRITICAL_SERVICES[@]}"; do
        if is_running "$service"; then
            docker compose restart "$service" 2>/dev/null || true
        fi
    done
fi

if [ "$critical_down" -eq 0 ]; then
    log "OK: All critical services running"
fi
