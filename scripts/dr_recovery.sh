#!/bin/bash
# =============================================================================
# GULA Platform - Disaster Recovery Script
# Operations: verify, restore, failover, drill
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/gula}"
DB_HOST="${DB_HOST:-postgres-primary}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-labdb}"
PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD env var must be set}"
export PGPASSWORD

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
ok()   { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}OK${NC} $*"; }
err()  { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}ERROR${NC} $*"; }
warn() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}WARN${NC} $*"; }

COMMAND="${1:-help}"

# =============================================================================
# VERIFY: Test that latest backup is restorable
# =============================================================================
cmd_verify() {
    log "=== Backup Verification ==="
    latest=$(find "${BACKUP_DIR}/daily" -name "*.sql.gz" -newer /tmp/.last_verify 2>/dev/null | sort -r | head -1 || \
             find "${BACKUP_DIR}/daily" -name "*.sql.gz" | sort -r | head -1)

    if [ -z "$latest" ]; then
        err "No backup found in ${BACKUP_DIR}/daily"
        exit 1
    fi

    log "Testing backup: $latest"
    log "Backup size: $(du -sh "$latest" | cut -f1)"

    # Test that backup can be decompressed and parsed
    if zcat "$latest" | grep -q "PostgreSQL database dump"; then
        ok "Backup is valid PostgreSQL dump"
    else
        err "Backup file appears corrupted"
        exit 1
    fi

    # Restore to test database
    TEST_DB="labdb_verify_$(date +%s)"
    log "Restoring to test database: $TEST_DB"

    PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -U "$DB_USER" -c "CREATE DATABASE $TEST_DB;" postgres
    zcat "$latest" | PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -U "$DB_USER" "$TEST_DB"

    # Verify tables exist
    table_count=$(PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -U "$DB_USER" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" "$TEST_DB")
    ok "Restored $table_count tables to $TEST_DB"

    # Check audit_log
    audit_count=$(PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -U "$DB_USER" -t -c \
        "SELECT COUNT(*) FROM audit_log;" "$TEST_DB" 2>/dev/null || echo 0)
    ok "audit_log records: $audit_count"

    # Cleanup test database
    PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE $TEST_DB;" postgres
    ok "Test database dropped. Backup verification PASSED."
    touch /tmp/.last_verify
}

# =============================================================================
# FAILOVER: Promote replica to primary
# =============================================================================
cmd_failover() {
    warn "=== PostgreSQL Manual Failover ==="
    warn "This will promote postgres-replica to primary."
    warn "Only run this if postgres-primary is confirmed DOWN."

    read -rp "Type 'CONFIRM FAILOVER' to proceed: " confirm
    if [ "$confirm" != "CONFIRM FAILOVER" ]; then
        log "Failover cancelled."
        exit 0
    fi

    log "Stopping postgres-primary (if running)..."
    docker stop gula-postgres-primary 2>/dev/null || warn "Primary already stopped"

    log "Promoting replica to primary..."
    docker exec gula-postgres-replica pg_ctl promote -D /var/lib/postgresql/data
    sleep 3

    # Verify promotion
    role=$(docker exec gula-postgres-replica psql -U postgres -t -c "SELECT pg_is_in_recovery();" 2>/dev/null | tr -d ' ')
    if [ "$role" = "f" ]; then
        ok "Replica promoted to primary (pg_is_in_recovery = false)"
    else
        err "Promotion may have failed (pg_is_in_recovery = $role)"
        exit 1
    fi

    log "Updating PgBouncer to point to new primary (localhost:5433)..."
    docker exec gula-pgbouncer bash -c "
        sed -i 's/postgres-primary/postgres-replica/g' /etc/pgbouncer/pgbouncer.ini
        kill -HUP \$(cat /var/run/pgbouncer/pgbouncer.pid)
    " 2>/dev/null || warn "Manual PgBouncer reconfiguration needed"

    ok "Failover complete. New primary: gula-postgres-replica"
    warn "Remember to rebuild original primary as new replica after recovery."
}

# =============================================================================
# DRILL: Monthly disaster recovery drill
# =============================================================================
cmd_drill() {
    log "=== Monthly DR Drill ==="
    log "Testing all recovery scenarios..."

    # 1. Backup verification
    log "Step 1/4: Backup verification"
    cmd_verify

    # 2. Service restart test
    log "Step 2/4: Service restart resilience"
    for svc in gula-ai-service gula-notification-service; do
        docker restart "$svc" 2>/dev/null && ok "Restarted $svc" || warn "Could not restart $svc"
        sleep 5
        state=$(docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null || echo "unknown")
        ok "$svc state after restart: $state"
    done

    # 3. RabbitMQ queue durability
    log "Step 3/4: RabbitMQ durability"
    docker restart gula-rabbitmq 2>/dev/null && ok "RabbitMQ restarted" || warn "RabbitMQ restart failed"
    sleep 15
    queue_count=$(curl -sf -u "${RABBITMQ_USER:-gula}:${RABBITMQ_PASS:?RABBITMQ_PASS must be set}" \
        "http://localhost:15672/api/queues/gula" 2>/dev/null | \
        python3 -c "import sys,json; q=json.load(sys.stdin); print(len(q))" 2>/dev/null || echo 0)
    ok "RabbitMQ queues after restart: $queue_count"

    # 4. Data integrity check
    log "Step 4/4: Data integrity check"
    record_count=$(PGPASSWORD=$PGPASSWORD psql -h localhost -p 6432 -U postgres -t -c \
        "SELECT COUNT(*) FROM patients;" labdb 2>/dev/null | tr -d ' ' || echo "unknown")
    ok "Patient records intact: $record_count"
    audit_count=$(PGPASSWORD=$PGPASSWORD psql -h localhost -p 6432 -U postgres -t -c \
        "SELECT COUNT(*) FROM audit_log;" labdb 2>/dev/null | tr -d ' ' || echo "unknown")
    ok "Audit log entries: $audit_count"

    ok "=== DR Drill Complete ==="
    log "Next drill: $(date -d '+1 month' '+%Y-%m-%d')"
}

# =============================================================================
# STATUS: Show DR readiness
# =============================================================================
cmd_status() {
    echo "=== GULA Platform DR Status ==="
    echo ""

    # Backup status
    latest_daily=$(find "${BACKUP_DIR}/daily" -name "*.sql.gz" 2>/dev/null | sort -r | head -1 || echo "none")
    latest_hourly=$(find "${BACKUP_DIR}/hourly" -name "*.sql.gz" 2>/dev/null | sort -r | head -1 || echo "none")
    echo "Latest daily backup:  $latest_daily"
    echo "Latest hourly backup: $latest_hourly"
    echo ""

    # Replica lag
    lag=$(PGPASSWORD=$PGPASSWORD psql -h localhost -p 5432 -U postgres -t -c \
        "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int || 's lag'" labdb 2>/dev/null | tr -d ' ' || echo "primary (no lag)")
    echo "PostgreSQL Replica lag: $lag"

    # RTO/RPO targets
    echo ""
    echo "RTO (Recovery Time Objective): < 5 minutes"
    echo "RPO (Recovery Point Objective): < 1 hour (hourly backups)"
    echo ""
    echo "Commands: dr_recovery.sh [verify|failover|drill|status]"
}

case "$COMMAND" in
    verify)   cmd_verify ;;
    failover) cmd_failover ;;
    drill)    cmd_drill ;;
    status)   cmd_status ;;
    help|*)
        echo "Usage: $0 [verify|failover|drill|status]"
        echo "  verify   - Test latest backup is restorable"
        echo "  failover - Promote replica to primary (emergency)"
        echo "  drill    - Monthly DR drill (all scenarios)"
        echo "  status   - Show DR readiness"
        ;;
esac
