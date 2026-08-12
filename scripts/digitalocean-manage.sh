#!/usr/bin/env bash
# =============================================================================
# GULA Platform — DigitalOcean Management Console
# =============================================================================
#
# Usage (run on the server or via SSH):
#   ./scripts/digitalocean-manage.sh <command> [args]
#
# Commands:
#   status              — health overview of all containers
#   logs [service]      — follow logs (default: backend)
#   restart [service]   — graceful restart (default: all)
#   deploy [tag]        — pull latest image and redeploy
#   backup              — create DB backup immediately
#   scale <N>           — scale backend to N instances (HAProxy mode)
#   kill-switch on      — activate kill switch via Redis
#   kill-switch off     — deactivate kill switch via Redis
#   kill-switch status  — check kill switch state
#   metrics             — show Prometheus metrics snapshot
#   top                 — live resource usage per container
#   db-shell            — open psql shell inside postgres container
#   redis-cli           — open redis-cli inside redis container
#   audit               — run one self-audit cycle (report only)
#   cleanup             — prune stopped containers and old images
#   ssl-renew           — force Let's Encrypt certificate renewal
#
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ── Colours ─────────────────────────────────────────────────────────────────
RED='\033[1;31m'; GREEN='\033[1;32m'; CYAN='\033[1;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

log()  { printf "${CYAN}[gula]${NC} %s\n"   "$*"; }
ok()   { printf "${GREEN}[✓]${NC} %s\n"     "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n"    "$*"; }
err()  { printf "${RED}[✗]${NC} %s\n" "$*" >&2; exit 1; }
sep()  { printf "${BOLD}%s${NC}\n" "─────────────────────────────────────────────"; }

# ── Docker Compose detection ─────────────────────────────────────────────────
if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose &>/dev/null; then
    DC="docker-compose"
else
    err "docker compose not found — is Docker installed?"
fi

cd "$PROJECT_DIR"

# ── Load .env if present (for METRICS_BEARER_TOKEN etc.) ────────────────────
[ -f .env ] && set -a && source .env && set +a

CMD="${1:-help}"
shift || true


# =============================================================================
cmd_status() {
    sep
    log "Container health:"
    $DC ps
    sep
    log "System resources:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        2>/dev/null || true
    sep
    log "Quick health check:"
    curl -sf "http://localhost:8080/health" | python3 -m json.tool 2>/dev/null \
        || warn "Health endpoint not responding"
}

cmd_logs() {
    SERVICE="${1:-gula-backend}"
    log "Following logs for: $SERVICE (Ctrl+C to stop)"
    $DC logs -f --tail=100 "$SERVICE"
}

cmd_restart() {
    SERVICE="${1:-}"
    if [ -z "$SERVICE" ]; then
        log "Restarting all services with zero-downtime rolling restart..."
        # Restart backend last, after infrastructure is healthy
        for svc in postgres redis gula-backend nginx; do
            if $DC ps --services 2>/dev/null | grep -q "^${svc}$"; then
                log "  Restarting $svc..."
                $DC restart "$svc"
                sleep 3
            fi
        done
    else
        log "Restarting $SERVICE..."
        $DC restart "$SERVICE"
    fi
    ok "Restart complete"
}

cmd_deploy() {
    TAG="${1:-latest}"
    log "Deploying tag: $TAG"
    bash "$SCRIPT_DIR/deploy.sh" ${TAG:+--branch "$TAG"}
}

cmd_backup() {
    log "Running immediate backup..."
    bash "$SCRIPT_DIR/backup.sh"
}

cmd_scale() {
    REPLICAS="${1:-}"
    [ -z "$REPLICAS" ] && err "Usage: scale <N>"
    [[ "$REPLICAS" =~ ^[0-9]+$ ]] || err "N must be a positive integer"
    log "Scaling backend to $REPLICAS instances..."
    $DC -f docker-compose.yml -f docker-compose.scale.yml \
        up -d --scale gula-backend="$REPLICAS" --no-recreate
    ok "Backend scaled to $REPLICAS instances"
    log "HAProxy stats: http://localhost:8404/stats"
}

cmd_kill_switch() {
    SUBCMD="${1:-status}"
    REDIS_CMD="$DC exec redis redis-cli"

    case "$SUBCMD" in
        on|activate)
            $REDIS_CMD SET gula:kill_switch 1 EX 86400
            ok "Kill switch ACTIVATED — all autonomous actions halted"
            warn "Deactivate with: $0 kill-switch off"
            ;;
        off|deactivate)
            $REDIS_CMD DEL gula:kill_switch
            ok "Kill switch DEACTIVATED — autonomous actions resumed"
            ;;
        status)
            VAL=$($REDIS_CMD GET gula:kill_switch 2>/dev/null || echo "nil")
            if [ "$VAL" = "1" ]; then
                warn "Kill switch: ACTIVE"
            else
                ok "Kill switch: inactive"
            fi
            ;;
        *)
            err "Usage: kill-switch {on|off|status}"
            ;;
    esac
}

cmd_metrics() {
    TOKEN="${METRICS_BEARER_TOKEN:-}"
    METRICS_URL="http://localhost:8080/metrics/prom"
    log "Fetching metrics from $METRICS_URL"
    if [ -n "$TOKEN" ]; then
        curl -sf -H "Authorization: Bearer $TOKEN" "$METRICS_URL" \
            | grep -E "^gula_" | sort
    else
        curl -sf "$METRICS_URL" | grep -E "^gula_" | sort
    fi
}

cmd_top() {
    log "Live container resource usage (Ctrl+C to stop)"
    docker stats --format \
        "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
}

cmd_db_shell() {
    log "Opening PostgreSQL shell..."
    $DC exec postgres psql \
        -U "${POSTGRES_USER:-gula}" \
        -d "${POSTGRES_DB:-gula_db}"
}

cmd_redis_cli() {
    log "Opening Redis CLI..."
    $DC exec redis redis-cli
}

cmd_audit() {
    log "Running self-audit (report only)..."
    if [ -f "$SCRIPT_DIR/self_audit_agent.py" ]; then
        ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
            python3 "$SCRIPT_DIR/self_audit_agent.py" --report-only
    else
        err "self_audit_agent.py not found"
    fi
}

cmd_cleanup() {
    log "Pruning stopped containers..."
    docker container prune -f
    log "Pruning dangling images..."
    docker image prune -f
    log "Pruning unused volumes (skipping named volumes)..."
    docker volume prune -f --filter "label!=keep" 2>/dev/null || true
    ok "Cleanup complete"
    docker system df
}

cmd_ssl_renew() {
    log "Forcing certificate renewal..."
    if command -v certbot &>/dev/null; then
        certbot renew --force-renewal
        systemctl reload nginx 2>/dev/null || true
        ok "Certificate renewed and nginx reloaded"
    else
        warn "certbot not found — is Let's Encrypt configured?"
    fi
}

cmd_help() {
    cat <<'EOF'

  GULA Platform — Management Console

  USAGE:  ./scripts/digitalocean-manage.sh <command> [args]

  STATUS
    status                    Health overview of all containers
    top                       Live resource usage per container
    metrics                   Prometheus metrics snapshot

  LOGS & DEBUG
    logs [service]            Follow logs (default: gula-backend)
    db-shell                  Open psql shell
    redis-cli                 Open Redis CLI

  OPERATIONS
    restart [service]         Graceful restart (all if omitted)
    deploy [branch/tag]       Pull latest and redeploy
    backup                    Create immediate DB backup
    scale <N>                 Scale backend to N instances
    cleanup                   Prune stopped containers and old images
    ssl-renew                 Force Let's Encrypt renewal

  SAFETY
    kill-switch on            Halt all autonomous AI/repair actions
    kill-switch off           Resume autonomous actions
    kill-switch status        Check current state

  SELF-HEALING
    audit                     Run one self-audit cycle (report only)

  Examples:
    ./scripts/digitalocean-manage.sh status
    ./scripts/digitalocean-manage.sh logs gula-backend
    ./scripts/digitalocean-manage.sh scale 3
    ./scripts/digitalocean-manage.sh kill-switch on
    ./scripts/digitalocean-manage.sh metrics

EOF
}


# =============================================================================
# Dispatch
# =============================================================================
case "$CMD" in
    status)        cmd_status ;;
    logs)          cmd_logs "$@" ;;
    restart)       cmd_restart "$@" ;;
    deploy)        cmd_deploy "$@" ;;
    backup)        cmd_backup ;;
    scale)         cmd_scale "$@" ;;
    kill-switch)   cmd_kill_switch "$@" ;;
    metrics)       cmd_metrics ;;
    top)           cmd_top ;;
    db-shell)      cmd_db_shell ;;
    redis-cli)     cmd_redis_cli ;;
    audit)         cmd_audit ;;
    cleanup)       cmd_cleanup ;;
    ssl-renew)     cmd_ssl_renew ;;
    help|--help|-h) cmd_help ;;
    *)
        warn "Unknown command: $CMD"
        cmd_help
        exit 1
        ;;
esac
