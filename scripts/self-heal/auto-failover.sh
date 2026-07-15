#!/bin/bash
# =============================================================================
# GULA Platform — Automated Failover Orchestrator
# =============================================================================
# Detects service failures, checks circuit breaker state, triggers appropriate
# failover for each service type:
#   - DB failover via Patroni
#   - Redis failover via Sentinel
#   - RabbitMQ node promotion
#   - MinIO drive replacement
#
# Usage:
#   ./scripts/self-heal/auto-failover.sh              # Run once (dry-run)
#   DRY_RUN=false ./scripts/self-heal/auto-failover.sh # Actually execute
#   ./scripts/self-heal/auto-failover.sh --watch       # Continuous monitoring
#
# Exit codes:
#   0 — All systems healthy
#   1 — Healed successfully after failover
#   2 — Failover failed — manual intervention required
# =============================================================================

set -euo pipefail

# ── Configuration (override via environment) ─────────────────────────────────
DRY_RUN="${DRY_RUN:-true}"
WATCH_INTERVAL="${WATCH_INTERVAL:-30}"
MAX_FAILOVER_ATTEMPTS="${MAX_FAILOVER_ATTEMPTS:-2}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
PROJECT_DIR="${GULA_DIR:-/home/samertts/gula-platform}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
LOG_FILE="/var/log/gula/auto-failover.log"
HEALTH_PROBE_SCRIPT="${PROJECT_DIR}/scripts/health-probes/check-all.sh"

mkdir -p "$(dirname "$LOG_FILE")"

# ── Colors & Logging ─────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"; }
ok()   { log "${GREEN}✓${NC} $*"; }
warn() { log "${YELLOW}⚠${NC} $*"; }
err()  { log "${RED}✗${NC} $*"; }

# ── Circuit Breaker Check ────────────────────────────────────────────────────

check_circuit_breaker() {
    # Check if the backend's circuit breaker is open by querying health/deep
    local state
    state=$(curl -sf --max-time 5 http://gula-backend:8000/health/deep 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('circuit_breaker','unknown'))" 2>/dev/null || echo "unknown")
    echo "$state"
}

# ── Alert ────────────────────────────────────────────────────────────────────

send_alert() {
    local level="$1"
    local message="$2"
    if [[ -n "$ALERT_WEBHOOK_URL" ]]; then
        curl -sf -X POST --max-time 5 \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[GULA Auto-Failover] ${level}: ${message}\",\"service\":\"auto-failover\",\"event\":\"failover\"}" \
            "$ALERT_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# ── PostgreSQL Failover (Patroni) ────────────────────────────────────────────

failover_postgres() {
    log "=== PostgreSQL Failover ==="
    local patroni_hosts="${PATRONI_HOSTS:-patroni-0:8008 patroni-1:8008 patroni-2:8008}"
    local patroni_user="${PATRONI_RESTAPI_USER:-patroni}"
    local patroni_pass="${PATRONI_RESTAPI_PASSWORD:-}"
    local api_endpoint=""

    # Find responsive Patroni API
    for host in $patroni_hosts; do
        if curl -sf --max-time 3 "http://${host}/cluster" > /dev/null 2>&1; then
            api_endpoint="$host"
            break
        fi
    done

    if [[ -z "$api_endpoint" ]]; then
        err "No Patroni API reachable — cannot failover PostgreSQL"
        return 1
    fi
    ok "Patroni API: $api_endpoint"

    # Get cluster state
    local cluster_state
    cluster_state=$(curl -sf --max-time 5 "http://${api_endpoint}/cluster" 2>/dev/null || echo "{}")
    local leader
    leader=$(echo "$cluster_state" | python3 -c "import sys,json; print(json.load(sys.stdin).get('leader',''))" 2>/dev/null || echo "")

    if [[ -z "$leader" ]]; then
        warn "No leader found — attempting forced failover to best replica"
    else
        ok "Current leader: $leader"
        # Check if leader is healthy
        if curl -sf --max-time 3 "http://${leader}:8008/health" > /dev/null 2>&1; then
            ok "Leader $leader is healthy — no failover needed"
            return 0
        fi
        warn "Leader $leader is unhealthy — initiating failover"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN: would execute Patroni failover from $leader to best replica"
        return 0
    fi

    # Get all members and find best candidate
    local members
    members=$(echo "$cluster_state" | python3 -c "
import sys,json
data=json.load(sys.stdin)
members=data.get('members', [])
for m in members:
    if m.get('role') in ('replica', 'sync_standby'):
        print(f\"{m.get('name')}|{m.get('lag', '999')}\")
" 2>/dev/null)

    local best_candidate=""
    local best_lag="999"
    while IFS='|' read -r name lag; do
        if [[ "$name" == "$leader" ]]; then continue; fi
        if [[ "$lag" -lt "$best_lag" ]]; then
            best_candidate="$name"
            best_lag="$lag"
        fi
    done <<< "$members"

    if [[ -z "$best_candidate" ]]; then
        err "No suitable replica candidate found"
        return 1
    fi
    ok "Best candidate: $best_candidate (lag=${best_lag}s)"

    # Execute failover
    local payload
    payload=$(cat <<EOF
{"action":"failover","leader":"$leader","candidate":"$best_candidate","force":true}
EOF
)
    if curl -sf -X POST --max-time 30 \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://${api_endpoint}/failover" > /dev/null 2>&1; then
        ok "Patroni failover triggered: ${leader} → ${best_candidate}"
        send_alert "WARNING" "PostgreSQL failover: ${leader} → ${best_candidate}"
        # Wait for new leader
        for i in $(seq 1 15); do
            sleep 2
            local new_leader
            new_leader=$(curl -sf --max-time 3 "http://${api_endpoint}/cluster" 2>/dev/null | \
                python3 -c "import sys,json; print(json.load(sys.stdin).get('leader',''))" 2>/dev/null || echo "")
            if [[ -n "$new_leader" ]] && [[ "$new_leader" != "$leader" ]]; then
                ok "New leader confirmed: $new_leader"
                return 0
            fi
        done
        err "New leader not confirmed after 30s — manual check required"
        return 1
    else
        err "Patroni failover API call failed"
        return 1
    fi
}

# ── Redis Failover (Sentinel) ────────────────────────────────────────────────

failover_redis() {
    log "=== Redis Failover ==="
    local sentinel_host="${1:-redis-sentinel-1}"
    local sentinel_port="26379"
    local master_name="gula-redis-primary"

    # Check current master
    local current_master
    current_master=$(redis-cli -h "$sentinel_host" -p "$sentinel_port" SENTINEL get-master-addr-by-name "$master_name" 2>/dev/null | head -1 || echo "")

    if [[ -z "$current_master" ]]; then
        warn "Cannot determine Redis master — checking node health..."
        # Try alternate sentinel
        for sentinel in redis-sentinel-2 redis-sentinel-3; do
            current_master=$(redis-cli -h "$sentinel" -p "$sentinel_port" SENTINEL get-master-addr-by-name "$master_name" 2>/dev/null | head -1 || echo "")
            if [[ -n "$current_master" ]]; then
                sentinel_host="$sentinel"
                break
            fi
        done
    fi

    if [[ -z "$current_master" ]]; then
        err "Redis master unknown — cannot proceed with failover"
        return 1
    fi
    ok "Current Redis master: $current_master"

    # Check if master is healthy
    if redis-cli -h "$current_master" -p 6379 -a "${REDIS_PASSWORD:-}" ping 2>/dev/null | grep -q PONG; then
        ok "Redis master $current_master is healthy — no failover needed"
        return 0
    fi
    warn "Redis master $current_master is unhealthy"

    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN: would trigger Redis sentinel failover"
        return 0
    fi

    # Sentinel failover happens automatically when quorum detects failure
    # Force failover if needed
    local failover_result
    failover_result=$(redis-cli -h "$sentinel_host" -p "$sentinel_port" SENTINEL failover "$master_name" 2>&1 || echo "FAILED")

    if [[ "$failover_result" == "OK" ]]; then
        ok "Redis Sentinel failover triggered"
        send_alert "WARNING" "Redis failover triggered via Sentinel"
        sleep 5
        local new_master
        new_master=$(redis-cli -h "$sentinel_host" -p "$sentinel_port" SENTINEL get-master-addr-by-name "$master_name" 2>/dev/null | head -1 || echo "")
        if [[ -n "$new_master" ]] && [[ "$new_master" != "$current_master" ]]; then
            ok "New Redis master: $new_master"
            return 0
        else
            warn "Sentinel did not report a new master yet — giving time to converge"
            return 0
        fi
    else
        err "Sentinel failover command failed: $failover_result"
        return 1
    fi
}

# ── RabbitMQ Failover / Node Promotion ───────────────────────────────────────

failover_rabbitmq() {
    log "=== RabbitMQ Node Health Check ==="
    local nodes
    nodes=$(curl -sf -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" \
        "http://${RABBITMQ_HOST:-rabbitmq-lb}:15672/api/nodes" 2>/dev/null | \
        python3 -c "
import sys,json
data=json.load(sys.stdin)
for n in data:
    print(f\"{n.get('name','')}|{n.get('running',False)}|{n.get('alarms',[])}\")
" 2>/dev/null || true)

    if [[ -z "$nodes" ]]; then
        warn "Cannot query RabbitMQ nodes — management API unreachable"
        return 1
    fi

    local unhealthy_nodes=0
    while IFS='|' read -r name running alarms; do
        if [[ "$running" != "True" ]]; then
            warn "RabbitMQ node $name is NOT running"
            unhealthy_nodes=$((unhealthy_nodes + 1))
        fi
        if [[ "$alarms" != "[]" ]]; then
            warn "RabbitMQ node $name has alarms: $alarms"
        fi
    done <<< "$nodes"

    if [[ "$unhealthy_nodes" -eq 0 ]]; then
        ok "All RabbitMQ nodes running"
        return 0
    fi

    warn "$unhealthy_nodes RabbitMQ node(s) unhealthy"
    if [[ "$DRY_RUN" == "false" ]]; then
        # RabbitMQ auto-heals quorum queues — just restart the unhealthy node
        local unhealthy_node_name=""
        while IFS='|' read -r name running alarms; do
            if [[ "$running" != "True" ]]; then
                unhealthy_node_name=$(echo "$name" | cut -d@ -f2 | cut -d. -f1)
                break
            fi
        done <<< "$nodes"

        if [[ -n "$unhealthy_node_name" ]]; then
            warn "Restarting unhealthy RabbitMQ node: $unhealthy_node_name"
            docker compose -f "$COMPOSE_FILE" restart "$unhealthy_node_name" 2>/dev/null || \
                docker restart "$unhealthy_node_name" 2>/dev/null || true
            send_alert "WARNING" "RabbitMQ node restarted: $unhealthy_node_name"
            sleep 10
        fi
    else
        warn "DRY RUN: would restart unhealthy RabbitMQ node"
    fi
    return 0
}

# ── MinIO Drive Replacement Check ────────────────────────────────────────────

check_minio_health() {
    log "=== MinIO Drive Health Check ==="
    local offline_drives
    offline_drives=$(curl -sf --max-time 5 \
        "http://${MINIO_HOST:-minio-lb}:${MINIO_PORT:-9000}/minio/health/cluster" 2>/dev/null | \
        python3 -c "
import sys,json
d=json.load(sys.stdin)
offline = d.get('offline_drives', 0)
total = d.get('total_drives', 0)
print(f'{offline}/{total}')
" 2>/dev/null || echo "unknown")

    if [[ "$offline_drives" == "0/"* ]]; then
        ok "All MinIO drives online"
        return 0
    elif [[ "$offline_drives" == "unknown" ]]; then
        warn "Cannot determine MinIO drive health"
        return 1
    else
        local offline_count="${offline_drives%%/*}"
        local total_count="${offline_drives##*/}"
        warn "MinIO: ${offline_count}/${total_count} drives offline"
        if [[ "$offline_count" -ge 2 ]]; then
            err "Critical: ${offline_count} drives offline — data at risk"
            send_alert "CRITICAL" "MinIO: ${offline_count}/${total_count} drives offline"
            return 2
        fi
        return 1
    fi
}

# ── Container Restart Helper ─────────────────────────────────────────────────

restart_container() {
    local service="$1"
    local max_restarts="${MAX_FAILOVER_ATTEMPTS:-2}"
    local restart_count_file="/tmp/gula-failover-restart-count"
    local file_age restart_count

    if [[ -f "$restart_count_file" ]]; then
        file_age=$(( $(date +%s) - $(stat -c %Y "$restart_count_file" 2>/dev/null || echo 0) ))
        if [[ "$file_age" -gt 3600 ]]; then
            echo "0" > "$restart_count_file"
        fi
    else
        echo "0" > "$restart_count_file"
    fi
    restart_count=$(cat "$restart_count_file" 2>/dev/null || echo 0)

    if [[ "$restart_count" -ge "$max_restarts" ]]; then
        err "Max restarts ($max_restarts/hour) reached for $service — not restarting"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN: would restart $service"
        return 0
    fi

    warn "Restarting $service (attempt $((restart_count + 1))/${max_restarts})..."
    docker compose -f "$COMPOSE_FILE" restart "$service" 2>/dev/null || \
        docker compose -f "$COMPOSE_FILE" up -d "$service" 2>/dev/null || true

    echo "$((restart_count + 1))" > "$restart_count_file"
    send_alert "WARNING" "Container restarted: $service"
    return 0
}

# ── Main Orchestration ──────────────────────────────────────────────────────

orchestrate() {
    log "========================================="
    log "GULA Auto-Failover Orchestrator (dry-run=${DRY_RUN})"
    log "========================================="

    local exit_code=0

    # Step 1: Comprehensive health check
    log "Step 1: Running comprehensive health probe..."
    if [[ -x "$HEALTH_PROBE_SCRIPT" ]]; then
        local health_status
        health_status=$("$HEALTH_PROBE_SCRIPT" --json 2>/dev/null || echo '{"overall_status":"UNKNOWN"}')
        local overall
        overall=$(echo "$health_status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('overall_status','UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
        log "Health status: $overall"
    else
        warn "Health probe script not found at $HEALTH_PROBE_SCRIPT"
    fi

    # Step 2: Check circuit breaker
    log "Step 2: Checking circuit breaker state..."
    local cb_state
    cb_state=$(check_circuit_breaker)
    if [[ "$cb_state" == "open" ]]; then
        warn "Circuit breaker is OPEN — system in degraded mode"
        send_alert "WARNING" "Circuit breaker open — failover may not succeed"
    else
        ok "Circuit breaker state: ${cb_state:-unknown}"
    fi

    # Step 3: PostgreSQL failover check
    log "Step 3: Checking PostgreSQL..."
    if ! failover_postgres; then
        warn "PostgreSQL failover had issues"
        exit_code=1
    fi

    # Step 4: Redis failover check
    log "Step 4: Checking Redis..."
    if ! failover_redis; then
        warn "Redis failover had issues"
        exit_code=1
    fi

    # Step 5: RabbitMQ node check
    log "Step 5: Checking RabbitMQ..."
    if ! failover_rabbitmq; then
        warn "RabbitMQ had issues"
        exit_code=1
    fi

    # Step 6: MinIO health check
    log "Step 6: Checking MinIO..."
    if ! check_minio_health; then
        warn "MinIO had issues"
        exit_code=1
    fi

    # Step 7: Verify backend health
    log "Step 7: Verifying backend health after failover..."
    sleep 5
    if curl -sf --max-time 5 "http://gula-backend:8000/health/ready" > /dev/null 2>&1; then
        ok "Backend healthy after failover operations"
    else
        warn "Backend not healthy after failover — may need manual intervention"
        exit_code=2
    fi

    # Summary
    log "========================================="
    if [[ "$exit_code" -eq 0 ]]; then
        ok "Auto-failover orchestrator completed — all systems healthy"
    elif [[ "$exit_code" -eq 1 ]]; then
        warn "Auto-failover orchestrator completed with warnings"
    else
        err "Auto-failover orchestrator FAILED — manual intervention required"
        send_alert "CRITICAL" "Auto-failover orchestrator FAILED — manual intervention required"
    fi
    log "========================================="

    return "$exit_code"
}

# ── Watch Mode ───────────────────────────────────────────────────────────────

watch_loop() {
    log "Starting watch mode (interval=${WATCH_INTERVAL}s)..."
    while true; do
        if ! orchestrate; then
            err "Watch cycle failed — continuing monitoring"
        fi
        sleep "$WATCH_INTERVAL"
    done
}

# ── Main Entry ───────────────────────────────────────────────────────────────

main() {
    case "${1:-}" in
        --watch|-w)
            watch_loop
            ;;
        --dry-run)
            DRY_RUN=true
            orchestrate
            ;;
        --help|-h)
            cat << HELP
Usage: $0 [options]

Options:
  --watch       Continuous monitoring (every ${WATCH_INTERVAL}s)
  --dry-run     Show what would be done (default)
  DRY_RUN=false Execute failovers (set via env)

Environment:
  DRY_RUN=true           Dry-run mode (no actual changes)
  ALERT_WEBHOOK_URL      Alerting webhook URL
  PATRONI_RESTAPI_PASSWORD  Patroni REST API password
  REDIS_PASSWORD         Redis password
  RABBITMQ_USER/PASS     RabbitMQ credentials
HELP
            exit 0
            ;;
        *)
            orchestrate
            ;;
    esac
}

main "$@"
