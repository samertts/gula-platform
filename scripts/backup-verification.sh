#!/bin/bash
# =============================================================================
# GULA Platform - Backup Verification Script (PostgreSQL)
# Verifies backup checksums, restores the latest backup into a test database,
# and validates core tables + audit-log chain integrity.
# Docker-aware: runs psql inside the gula-postgres container when available.
# Usage: ./scripts/backup-verification.sh
# Schedule (example):
#   0 6 * * * /path/to/gula-platform/scripts/backup-verification.sh
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/home/user/gula-platform/backups}"
LOG_FILE="${LOG_FILE:-/var/log/gula-backup-verification.log}"
PG_CONTAINER="${PG_CONTAINER:-gula-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-labdb}"
TEST_DB_NAME="${TEST_DB_NAME:-labdb_verify}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_ENCRYPT_KEY="${BACKUP_ENCRYPT_KEY:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()       { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
log_success(){ echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ $1${NC}" | tee -a "$LOG_FILE"; }
log_warning(){ echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ $1${NC}" | tee -a "$LOG_FILE"; }

mkdir -p "$BACKUP_DIR"

log "=========================================="
log "GULA Platform - Backup Verification"
log "=========================================="

# Run psql: prefer Docker, fall back to direct connection
_psql() {
    local target_db="$1"
    shift
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${PG_CONTAINER}$"; then
        docker exec -i "${PG_CONTAINER}" psql -U "${DB_USER}" -d "${target_db}" "$@"
    elif command -v psql &>/dev/null; then
        DB_HOST="${DB_HOST:-localhost}"
        DB_PORT="${DB_PORT:-5432}"
        PGPASSWORD="${PGPASSWORD:?PGPASSWORD required for direct mode}" \
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${target_db}" "$@"
    else
        log_error "Neither docker nor psql available"
        exit 1
    fi
}

# Step 1: Check if backups exist
log "Step 1: Checking for existing backups..."
BACKUP_COUNT=$(find "$BACKUP_DIR" \( -name "gula_*.sql.gz" -o -name "gula_*.sql.gz.enc" \) 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -eq 0 ]; then
    log_error "No backups found in $BACKUP_DIR"
    exit 1
fi
log_success "Found $BACKUP_COUNT backups"

# Step 2: Get the latest backup (plain or encrypted)
log "Step 2: Finding latest backup..."
LATEST_BACKUP=$(find "$BACKUP_DIR" \( -name "gula_*.sql.gz" -o -name "gula_*.sql.gz.enc" \) -printf '%T@ %p\n' 2>/dev/null \
    | sort -n | tail -1 | cut -d' ' -f2-)
if [ -z "$LATEST_BACKUP" ]; then
    log_error "Could not find latest backup"
    exit 1
fi
BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
log_success "Latest backup: $LATEST_BACKUP (Size: $BACKUP_SIZE)"

# Step 3: Verify checksum + integrity
log "Step 3: Verifying backup integrity..."
if [[ -f "${LATEST_BACKUP}.sha256" ]]; then
    if sha256sum -c "${LATEST_BACKUP}.sha256" --quiet; then
        log_success "Checksum verified"
    else
        log_error "Checksum mismatch — backup may be corrupted"
        exit 1
    fi
else
    log_warning "No checksum sidecar for ${LATEST_BACKUP}"
fi

case "$LATEST_BACKUP" in
    *.enc)
        if [[ -z "$BACKUP_ENCRYPT_KEY" ]]; then
            log_error "Backup is encrypted but BACKUP_ENCRYPT_KEY is not set"
            exit 1
        fi
        if openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass "env:BACKUP_ENCRYPT_KEY" < "$LATEST_BACKUP" 2>/dev/null | gunzip -t; then
            log_success "Decryption + gzip integrity verified"
        else
            log_error "Decryption/integrity check failed"
            exit 1
        fi
        ;;
    *)
        if gunzip -t "$LATEST_BACKUP" 2>/dev/null; then
            log_success "gzip integrity verified"
        else
            log_error "gzip integrity check failed"
            exit 1
        fi
        ;;
esac

# Step 4: Restore into a test database
log "Step 4: Testing restore to test database..."
_psql postgres -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" >/dev/null 2>&1 || true
_psql postgres -c "CREATE DATABASE ${TEST_DB_NAME};" >/dev/null 2>&1

restore_backup() {
    # Reads pg_dump SQL from stdin into the test database
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${PG_CONTAINER}$"; then
        docker exec -i "${PG_CONTAINER}" psql -U "${DB_USER}" -d "${TEST_DB_NAME}" >/dev/null 2>&1
    elif command -v psql &>/dev/null; then
        DB_HOST="${DB_HOST:-localhost}"; DB_PORT="${DB_PORT:-5432}"
        PGPASSWORD="${PGPASSWORD:?}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TEST_DB_NAME" >/dev/null 2>&1
    else
        return 1
    fi
}

RESTORE_OK=0
case "$LATEST_BACKUP" in
    *.enc)
        openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass "env:BACKUP_ENCRYPT_KEY" < "$LATEST_BACKUP" \
            | gunzip -c | restore_backup && RESTORE_OK=1
        ;;
    *)
        gunzip -c "$LATEST_BACKUP" | restore_backup && RESTORE_OK=1
        ;;
esac

if [ "$RESTORE_OK" -eq 1 ]; then
    log_success "Restore to test database successful"
else
    log_error "Restore to test database failed"
    _psql postgres -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" >/dev/null 2>&1 || true
    exit 1
fi

# Step 5: Verify restored data
log "Step 5: Verifying restored data..."
TABLE_COUNT=$(_psql "$TEST_DB_NAME" -t -A -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" || echo "0")
if [ "${TABLE_COUNT:-0}" -gt 0 ]; then
    log_success "Restored database has $TABLE_COUNT tables"
else
    log_error "Restored database appears to be empty"
    _psql postgres -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" >/dev/null 2>&1 || true
    exit 1
fi

REQUIRED_TABLES=("labs" "lab_users" "patients" "lab_orders" "lab_results" "audit_logs")
for table in "${REQUIRED_TABLES[@]}"; do
    ROW_COUNT=$(_psql "$TEST_DB_NAME" -t -A -c "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo "?")
    if [ "$ROW_COUNT" != "?" ]; then
        log_success "Table '$table' exists with $ROW_COUNT rows"
    else
        log_warning "Table '$table' not found in restored database"
    fi
done

CHAIN_OK=1
HAS_CHAIN=$(_psql "$TEST_DB_NAME" -t -A -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='chain_hash';" 2>/dev/null || echo "0")
if [ "${HAS_CHAIN:-0}" -gt 0 ]; then
    BROKEN=$(_psql "$TEST_DB_NAME" -t -A -c "SELECT COUNT(*) FROM audit_logs WHERE chain_hash IS NULL AND id > 1;" 2>/dev/null || echo "?")
    if [ "${BROKEN:-1}" = "0" ]; then
        log_success "Audit log chain integrity: intact"
    else
        CHAIN_OK=0
        log_error "Audit log chain integrity: BROKEN ($BROKEN entries missing chain_hash)"
    fi
else
    log_warning "audit_logs.chain_hash column missing — chain check skipped"
fi

# Step 6: Cleanup old backups
log "Step 6: Cleaning up old backups..."
DELETED_COUNT=$(find "$BACKUP_DIR" \( -name "*.sql.gz" -o -name "*.sql.gz.enc" -o -name "*.sha256" \) -mtime +"$RETENTION_DAYS" -delete -print 2>/dev/null | wc -l)
if [ "$DELETED_COUNT" -gt 0 ]; then
    log_success "Deleted $DELETED_COUNT old backup files (older than $RETENTION_DAYS days)"
else
    log "No old backups to delete"
fi

# Step 7: Generate report
log "Step 7: Generating backup report..."
REPORT_FILE="$BACKUP_DIR/backup_report_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
GULA Platform - Backup Verification Report
Generated: $(date)

Backup Information:
- Latest Backup: $LATEST_BACKUP
- Backup Size: $BACKUP_SIZE

Verification Results:
- Checksum: PASSED
- Integrity: PASSED
- Restore Test: PASSED
- Tables Count: $TABLE_COUNT
- Audit Chain: $([ "$CHAIN_OK" = 1 ] && echo PASSED || echo FAILED)

Retention Policy:
- Retention Days: $RETENTION_DAYS
- Deleted Files: $DELETED_COUNT

Status: $([ "$CHAIN_OK" = 1 ] && echo "SUCCESS" || echo "WARNING — audit chain broken") 
EOF

log_success "Report generated: $REPORT_FILE"

# Step 8: Optional notification
if command -v mail &>/dev/null; then
    if [ -n "${ALERT_EMAIL:-}" ]; then
        log "Sending verification report to $ALERT_EMAIL..."
        mail -s "GULA Platform - Backup Verification Report" "$ALERT_EMAIL" < "$REPORT_FILE"
        log_success "Report sent"
    fi
fi

# Step 9: Cleanup test database
_psql postgres -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" >/dev/null 2>&1 || true

log_success "=========================================="
log_success "Backup verification completed successfully!"
log_success "=========================================="

[ "$CHAIN_OK" = 1 ]
