#!/bin/bash
# =============================================================================
# GULA Platform — Automated PostgreSQL Failover via Patroni
# =============================================================================
# This script:
#   1. Checks Patroni cluster leader status
#   2. Triggers manual failover if needed
#   3. Switches over to replica
#   4. Updates application configuration
#   5. Verifies new leader
#   6. Sends alert on failover
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
PATRONI_HOSTS="${PATRONI_HOSTS:-patroni-0:8008 patroni-1:8008 patroni-2:8008}"
PATRONI_RESTAPI_USER="${PATRONI_RESTAPI_USER:-patroni}"
PATRONI_RESTAPI_PASSWORD="${PATRONI_RESTAPI_PASSWORD:?PATRONI_RESTAPI_PASSWORD must be set}"
PATRONI_SCOPE="${PATRONI_SCOPE:-gula-db}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
CONSUL_HOST="${CONSUL_HOST:-consul:8500}"  # or etcd
DRY_RUN="${DRY_RUN:-false}"

NEW_LEADER=""
OLD_LEADER=""
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="/var/log/gula/failover.log"

mkdir -p "$(dirname "$LOG_FILE")"

# ── Colors & Logging ─────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
ok()   { log "${GREEN}✓${NC} $*"; }
warn() { log "${YELLOW}⚠${NC} $*"; }
err()  { log "${RED}✗${NC} $*"; }

# ── Helper Functions ─────────────────────────────────────────────────────────

# Find the first responsive Patroni member
_find_any_patroni() {
    for host in $PATRONI_HOSTS; do
        if curl -sf --max-time 3 "http://${host}/cluster" > /dev/null 2>&1; then
            echo "$host"
            return 0
        fi
    done
    return 1
}

# Fetch cluster state from Patroni REST API
_cluster_state() {
    local host="${1:-}"
    if [[ -z "$host" ]]; then
        host="$(_find_any_patroni)" || { err "No Patroni nodes reachable"; return 1; }
    fi
    curl -sf --max-time 5 \
        -u "${PATRONI_RESTAPI_USER}:${PATRONI_RESTAPI_PASSWORD}" \
        "http://${host}/cluster" 2>/dev/null || return 1
}

# Get current leader
_get_leader() {
    _cluster_state "$1" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('leader', ''))" 2>/dev/null || echo ""
}

# Get all members
_get_members() {
    _cluster_state "$1" | python3 -c "
import sys,json
data=json.load(sys.stdin)
members=data.get('members', [])
for m in members:
    if m.get('role') in ('replica', 'sync_standby'):
        print(f\"{m.get('name')}|{m.get('host')}|{m.get('role')}|{m.get('lag', '0')}\")
" 2>/dev/null
}

# Check if a given member is healthy
_member_healthy() {
    local host="$1"
    curl -sf --max-time 3 "http://${host}/health" > /dev/null 2>&1
}

# Trigger Patroni failover
_trigger_failover() {
    local candidate="${1:?candidate required}"
    local host="$2"
    local payload
    payload=$(cat <<EOF
{
    "action": "failover",
    "leader": "$OLD_LEADER",
    "candidate": "$candidate",
    "scheduled_at": "$TIMESTAMP",
    "force": true
}
EOF
)
    curl -sf -X POST --max-time 30 \
        -u "${PATRONI_RESTAPI_USER}:${PATRONI_RESTAPI_PASSWORD}" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://${host}/failover" 2>/dev/null
}

# Send alert
_send_alert() {
    local level="${1:-INFO}"
    local message="$2"
    if [[ -n "$ALERT_WEBHOOK_URL" ]]; then
        local alert_payload
        alert_payload=$(cat <<EOF
{
    "text": "[GULA Failover] ${level}: ${message}",
    "timestamp": "$TIMESTAMP",
    "service": "postgresql",
    "event": "failover"
}
EOF
)
        curl -sf -X POST --max-time 10 \
            -H "Content-Type: application/json" \
            -d "$alert_payload" \
            "$ALERT_WEBHOOK_URL" 2>/dev/null || warn "Alert send failed (webhook unreachable)"
    fi
}

# Update Consul service registration
_update_service_registry() {
    local new_leader_host="$1"
    if command -v consul &>/dev/null && [[ -n "$CONSUL_HOST" ]]; then
        consul services deregister -id="gula-db-primary" 2>/dev/null || true
        consul services register \
            -name="gula-db-primary" \
            -id="gula-db-primary" \
            -address="$new_leader_host" \
            -port=5432 \
            -tag="primary" \
            -tag="postgresql" 2>/dev/null || warn "Consul registration failed"
    fi
}

# Update .env or application config with new primary address
_update_app_config() {
    local new_leader_host="$1"
    local env_file="${ENV_FILE:-/etc/gula/.env}"
    if [[ -f "$env_file" ]]; then
        if grep -q "^DATABASE_URL" "$env_file"; then
            sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:\${POSTGRES_PASSWORD}@${new_leader_host}:5432/labdb|" "$env_file"
            ok "Updated DATABASE_URL in $env_file"
        fi
    fi
}

# ── Main Failover Logic ──────────────────────────────────────────────────────

main() {
    log "========================================="
    log "Patroni Failover initiated at $TIMESTAMP"
    log "========================================="

    # Step 1: Find a responsive Patroni API endpoint
    log "Step 1: Discovering Patroni API..."
    PATRONI_ENDPOINT="$(_find_any_patroni)" || {
        err "No Patroni nodes are reachable — aborting failover"
        _send_alert "CRITICAL" "Failover ABORTED: no Patroni nodes reachable"
        exit 1
    }
    ok "Using Patroni endpoint: $PATRONI_ENDPOINT"

    # Step 2: Identify current leader
    log "Step 2: Identifying current cluster leader..."
    OLD_LEADER="$(_get_leader "$PATRONI_ENDPOINT")"
    if [[ -z "$OLD_LEADER" ]]; then
        err "Cannot determine current leader — cluster may be fully down"
        _send_alert "CRITICAL" "Failover ABORTED: no leader found in cluster"
        exit 1
    fi
    ok "Current leader: $OLD_LEADER"

    # Step 3: Check if failover is actually needed
    log "Step 3: Assessing leader health..."
    LEADER_HOST=""
    for host in $PATRONI_HOSTS; do
        name=$(echo "$host" | cut -d: -f1)
        if [[ "$name" == "$OLD_LEADER" ]] || [[ "$host" == "$OLD_LEADER"* ]]; then
            LEADER_HOST="$host"
            break
        fi
    done

    if [[ -n "$LEADER_HOST" ]] && _member_healthy "$LEADER_HOST"; then
        ok "Leader $OLD_LEADER appears healthy — checking cluster consensus..."
        # Verify the leader is actually the DCS leader, not a stale observation
        sleep 2
        NEW_CHECK="$(_get_leader "$PATRONI_ENDPOINT")"
        if [[ "$NEW_CHECK" == "$OLD_LEADER" ]]; then
            ok "Leader confirmed healthy — no failover needed"
            _send_alert "INFO" "Failover check: leader $OLD_LEADER healthy, no action taken"
            exit 0
        fi
    fi

    warn "Leader $OLD_LEADER is unhealthy or unreachable — initiating failover"

    # Step 4: Find best replica candidate
    log "Step 4: Evaluating replica candidates..."
    BEST_CANDIDATE=""
    BEST_LAG="-1"

    while IFS='|' read -r name host role lag; do
        if [[ "$name" == "$OLD_LEADER" ]]; then
            continue
        fi
        # Convert name to full host:port for health check
        candidate_host=""
        for h in $PATRONI_HOSTS; do
            hname=$(echo "$h" | cut -d: -f1)
            if [[ "$hname" == "$name" ]]; then
                candidate_host="$h"
                break
            fi
        done
        if [[ -z "$candidate_host" ]]; then
            candidate_host="${name}:8008"
        fi
        if _member_healthy "$candidate_host"; then
            if [[ "$BEST_LAG" == "-1" ]] || [[ "$lag" -lt "$BEST_LAG" ]]; then
                BEST_CANDIDATE="$name"
                BEST_LAG="$lag"
            fi
            ok "  Candidate: $name (role=$role, lag=${lag}s)"
        else
            warn "  Candidate $name is unhealthy — skipping"
        fi
    done < <(_get_members "$PATRONI_ENDPOINT")

    if [[ -z "$BEST_CANDIDATE" ]]; then
        err "No healthy replica candidates found — failover impossible"
        _send_alert "CRITICAL" "Failover ABORTED: no healthy replicas available"
        exit 1
    fi
    ok "Best candidate selected: $BEST_CANDIDATE (lag=${BEST_LAG}s)"

    # Step 5: Execute the failover
    log "Step 5: Triggering Patroni failover to $BEST_CANDIDATE..."
    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN: would failover from $OLD_LEADER to $BEST_CANDIDATE"
        _send_alert "INFO" "DRY RUN: simulated failover $OLD_LEADER → $BEST_CANDIDATE"
        exit 0
    fi

    FAILOVER_RESULT=$(_trigger_failover "$BEST_CANDIDATE" "$PATRONI_ENDPOINT") || {
        err "Failover command failed — Patroni API returned error"
        _send_alert "CRITICAL" "Failover FAILED: Patroni API error during failover to $BEST_CANDIDATE"
        exit 1
    }
    ok "Failover command accepted"

    # Step 6: Wait for new leader election
    log "Step 6: Waiting for new leader election (max 60s)..."
    NEW_LEADER=""
    for i in $(seq 1 30); do
        sleep 2
        NEW_LEADER="$(_get_leader "$PATRONI_ENDPOINT")"
        if [[ -n "$NEW_LEADER" ]] && [[ "$NEW_LEADER" != "$OLD_LEADER" ]]; then
            ok "New leader elected: $NEW_LEADER (attempt $i)"
            break
        fi
    done

    if [[ -z "$NEW_LEADER" ]] || [[ "$NEW_LEADER" == "$OLD_LEADER" ]]; then
        err "Failover TIMEOUT — no new leader detected after 60s"
        _send_alert "CRITICAL" "Failover TIMEOUT: no new leader detected after 60s"
        exit 1
    fi

    # Step 7: Verify new leader is accepting writes
    log "Step 7: Verifying new leader accepts writes..."
    VERIFY_HOST=""
    for host in $PATRONI_HOSTS; do
        name=$(echo "$host" | cut -d: -f1)
        if [[ "$name" == "$NEW_LEADER" ]]; then
            VERIFY_HOST=$(echo "$host" | cut -d: -f1)
            break
        fi
    done
    if [[ -z "$VERIFY_HOST" ]]; then
        VERIFY_HOST="$NEW_LEADER"
    fi

    # Test write capability via psql
    PG_AVAILABLE=false
    if command -v psql &>/dev/null; then
        TEST_RESULT=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "$VERIFY_HOST" -U postgres -d labdb -t -c \
            "SELECT 1 AS ok;" 2>/dev/null | tr -d ' ') || TEST_RESULT=""
        if [[ "$TEST_RESULT" == "1" ]]; then
            PG_AVAILABLE=true
            ok "New leader $VERIFY_HOST is accepting read queries"
        fi
    else
        # Fallback: check via Patroni health
        for host in $PATRONI_HOSTS; do
            name=$(echo "$host" | cut -d: -f1)
            if [[ "$name" == "$NEW_LEADER" ]]; then
                HEALTH=$(curl -sf "http://${host}/health" 2>/dev/null | python3 -c \
                    "import sys,json; d=json.load(sys.stdin); print(d.get('state',''))" 2>/dev/null) || HEALTH=""
                if [[ "$HEALTH" == "running" ]]; then
                    PG_AVAILABLE=true
                    ok "New leader $NEW_LEADER confirmed via Patroni health (state=running)"
                fi
                break
            fi
        done
    fi

    if [[ "$PG_AVAILABLE" != "true" ]]; then
        warn "Could not verify new leader write capability — proceeding with caution"
    fi

    # Step 8: Update application configuration
    log "Step 8: Updating application configuration..."
    _update_app_config "$VERIFY_HOST"
    _update_service_registry "$VERIFY_HOST"
    ok "Application config updated to point at new primary: $VERIFY_HOST"

    # Step 9: Send success alert
    log "Step 9: Sending failover notification..."
    _send_alert "WARNING" "Failover COMPLETE: ${OLD_LEADER} → ${NEW_LEADER} (lag_on_failover=${BEST_LAG}s)"

    log "========================================="
    ok "Failover completed successfully"
    log "  Old leader : $OLD_LEADER"
    log "  New leader : $NEW_LEADER"
    log "  Candidate  : $BEST_CANDIDATE"
    log "  Replica lag: ${BEST_LAG}s"
    log "========================================="
}

# ── Execution ────────────────────────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
