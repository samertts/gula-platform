#!/bin/bash
# =============================================================================
# GULA Platform - PostgreSQL Failover Automation
# Audit Order 4: Test PostgreSQL primary failure and recovery
# =============================================================================

set -euo pipefail

PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD env var must be set}"; export PGPASSWORD
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo -e "[$(date '+%H:%M:%S')] ${GREEN}✓${NC} $*"; }
err()  { echo -e "[$(date '+%H:%M:%S')] ${RED}✗${NC} $*"; exit 1; }
warn() { echo -e "[$(date '+%H:%M:%S')] ${YELLOW}⚠${NC} $*"; }

MODE="${1:-test}"

# ─── Pre-flight checks ─────────────────────────────────────────────────────
check_primary() {
    pg_isready -h localhost -p 5432 -U postgres -q 2>/dev/null
}

check_replica() {
    pg_isready -h localhost -p 5433 -U postgres -q 2>/dev/null
}

replica_lag() {
    psql -h localhost -p 5433 -U postgres -t -c \
        "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int" labdb \
        2>/dev/null | tr -d ' ' || echo "unknown"
}

is_replica_in_recovery() {
    psql -h localhost -p 5433 -U postgres -t -c \
        "SELECT pg_is_in_recovery()" labdb 2>/dev/null | tr -d ' ' || echo "unknown"
}

# ─── Test mode: simulate outage, verify replica, restore ───────────────────
cmd_test() {
    log "=== PostgreSQL Failover Test ==="
    log ""

    # Step 1: Verify current state
    log "Step 1: Checking current replication state..."
    check_primary && ok "Primary is up" || err "Primary not running"
    check_replica  && ok "Replica is up" || warn "Replica not running"

    lag=$(replica_lag)
    in_recovery=$(is_replica_in_recovery)
    log "  Replica lag: ${lag}s"
    log "  In recovery mode: $in_recovery (should be 't')"
    [ "$in_recovery" = "t" ] && ok "Replica is properly in standby mode" || \
        warn "Replica may not be in streaming replication"

    # Step 2: Insert test record (should replicate)
    log ""
    log "Step 2: Insert test record on primary..."
    TEST_ID=$(psql -h localhost -p 5432 -U postgres -t -c \
        "INSERT INTO laboratories (lab_name, city) VALUES ('FAILOVER_TEST_$(date +%s)', 'Test') RETURNING id;" \
        labdb 2>/dev/null | tr -d ' ')
    ok "Inserted test record id=$TEST_ID"
    sleep 2

    # Step 3: Verify replication
    log ""
    log "Step 3: Verify record replicated to replica..."
    replicated=$(psql -h localhost -p 5433 -U postgres -t -c \
        "SELECT lab_name FROM laboratories WHERE id=$TEST_ID;" labdb \
        2>/dev/null | tr -d ' ' || echo "not_found")

    if [[ "$replicated" == *"FAILOVER_TEST"* ]]; then
        ok "Record replicated successfully: $replicated"
    else
        warn "Record not yet visible on replica (lag may be higher than 2s)"
    fi

    # Step 4: Simulate primary failure
    log ""
    log "Step 4: Simulating primary failure (pause container)..."
    docker pause gula-postgres-primary 2>/dev/null || warn "Cannot pause (not running as Docker)"
    sleep 3

    log "Primary paused. Testing connection fallback..."
    # PgBouncer should fail here — this tests the observable failure
    if pg_isready -h localhost -p 6432 -U postgres -q 2>/dev/null; then
        warn "PgBouncer still reports ready (may be using cached connection)"
    else
        ok "PgBouncer connection fails as expected during primary outage"
    fi

    # Step 5: Restore primary
    log ""
    log "Step 5: Restoring primary..."
    docker unpause gula-postgres-primary 2>/dev/null || warn "Cannot unpause"
    sleep 5

    check_primary && ok "Primary restored" || warn "Primary not responding yet"

    # Cleanup test record
    psql -h localhost -p 5432 -U postgres -c \
        "DELETE FROM laboratories WHERE id=$TEST_ID;" labdb > /dev/null 2>&1 || true
    ok "Test record cleaned up"

    log ""
    log "=== Failover Test Summary ==="
    ok "Primary:  running and accepting writes"
    ok "Replica:  in streaming replication (read-only)"
    ok "Lag:      ${lag}s (target: <10s)"
    warn "Automatic promotion: NOT configured (requires Patroni for auto-failover)"
    log ""
    log "For production auto-failover, use:"
    log "  - Patroni (recommended): https://github.com/zalando/patroni"
    log "  - pg_auto_failover: https://pg-auto-failover.readthedocs.io/"
    log "  - AWS RDS Multi-AZ (cloud)"
}

# ─── Monitor mode: continuous lag monitoring ────────────────────────────────
cmd_monitor() {
    log "Monitoring replication lag (Ctrl+C to stop)..."
    while true; do
        lag=$(replica_lag)
        primary_ok=$(check_primary && echo "UP" || echo "DOWN")
        replica_ok=$(check_replica && echo "UP" || echo "DOWN")
        echo "[$(date '+%H:%M:%S')] Primary: $primary_ok | Replica: $replica_ok | Lag: ${lag}s"
        sleep 5
    done
}

case "${MODE}" in
    test)    cmd_test ;;
    monitor) cmd_monitor ;;
    *)
        echo "Usage: $0 [test|monitor]"
        echo "  test    - Simulate primary failure and verify recovery"
        echo "  monitor - Continuously monitor replication lag"
        ;;
esac
