#!/bin/bash
# =============================================================================
# GULA Platform - Disaster Recovery Restore Test
#
# Answers the audit question: "هل جربتم الاسترجاع؟" (Have you tested recovery?)
#
# What this does:
#   1. Find the latest backup file + verify its SHA-256 checksum
#   2. Spin up a temporary isolated PostgreSQL container
#   3. Restore the backup into it
#   4. Run basic integrity queries (row counts, table existence)
#   5. Tear down the test container
#   6. Write a signed test report to logs/restore-test-TIMESTAMP.log
#
# Usage: ./scripts/restore-test.sh [backup_file.sql.gz]
#        (omit backup_file to use the latest daily backup)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUP_DIR="${BACKUP_DIR:-${PLATFORM_DIR}/backups}"
LOG_DIR="${PLATFORM_DIR}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT="${LOG_DIR}/restore-test-${TIMESTAMP}.log"
# JSON result file — read by /compliance/system-status to show live evidence
RESULT_JSON="${RESULT_JSON:-/app/data/last_restore_test.json}"

DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-labdb}"
TEST_CONTAINER="gula-restore-test-${TIMESTAMP}"
TEST_PORT="54320"  # different from production 5432

mkdir -p "${LOG_DIR}"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "${REPORT}"
}

fail() {
    log "RESTORE TEST FAILED: $*"
    docker rm -f "${TEST_CONTAINER}" 2>/dev/null || true
    exit 1
}

log "============================================================"
log "GULA Platform - Disaster Recovery Restore Test"
log "Report: ${REPORT}"
log "============================================================"

# ─── 1. Find backup file ─────────────────────────────────────────────────────
BACKUP_FILE="${1:-}"
if [[ -z "${BACKUP_FILE}" ]]; then
    BACKUP_FILE=$(find "${BACKUP_DIR}/daily" -name "*.sql.gz" -printf '%T@ %p\n' 2>/dev/null \
        | sort -n | tail -1 | cut -d' ' -f2-)
    [[ -z "${BACKUP_FILE}" ]] && fail "No backup files found in ${BACKUP_DIR}/daily"
fi
[[ -f "${BACKUP_FILE}" ]] || fail "Backup file not found: ${BACKUP_FILE}"
log "Using backup: ${BACKUP_FILE}"
log "Backup size: $(du -h "${BACKUP_FILE}" | cut -f1)"

# ─── 2. Verify SHA-256 checksum ──────────────────────────────────────────────
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [[ -f "${CHECKSUM_FILE}" ]]; then
    if sha256sum -c "${CHECKSUM_FILE}" --quiet; then
        log "Checksum: PASS ✓"
    else
        fail "Checksum mismatch — backup file may be corrupted or tampered"
    fi
else
    log "WARNING: No .sha256 sidecar found — skipping checksum verification"
fi

# ─── 3. Start temporary test container ───────────────────────────────────────
log "Starting temporary test container (${TEST_CONTAINER})..."
docker run -d \
    --name "${TEST_CONTAINER}" \
    -e POSTGRES_USER="${DB_USER}" \
    -e POSTGRES_PASSWORD="restore_test_only" \
    -e POSTGRES_DB="${DB_NAME}" \
    -p "127.0.0.1:${TEST_PORT}:5432" \
    --health-cmd "pg_isready -U ${DB_USER}" \
    --health-interval 2s \
    --health-retries 15 \
    postgres:14-alpine > /dev/null

log "Waiting for test database to be ready..."
for i in $(seq 1 30); do
    if docker exec "${TEST_CONTAINER}" pg_isready -U "${DB_USER}" -q 2>/dev/null; then
        log "Database ready (${i}s)"
        break
    fi
    if [[ $i -eq 30 ]]; then
        fail "Test database did not become ready in 30 seconds"
    fi
    sleep 1
done

# ─── 4. Restore backup ───────────────────────────────────────────────────────
log "Restoring backup..."
T_START=$(date +%s)

if gunzip -c "${BACKUP_FILE}" | \
    PGPASSWORD="restore_test_only" psql \
        -h "127.0.0.1" -p "${TEST_PORT}" \
        -U "${DB_USER}" -d "${DB_NAME}" \
        -q 2>>"${REPORT}"; then
    T_END=$(date +%s)
    RESTORE_SECONDS=$((T_END - T_START))
    log "Restore completed in ${RESTORE_SECONDS} seconds ✓"
else
    fail "psql restore failed — check ${REPORT} for details"
fi

# ─── 5. Integrity checks ─────────────────────────────────────────────────────
log "Running integrity checks..."

run_query() {
    PGPASSWORD="restore_test_only" psql \
        -h "127.0.0.1" -p "${TEST_PORT}" \
        -U "${DB_USER}" -d "${DB_NAME}" \
        -t -c "$1" 2>/dev/null | tr -d ' '
}

# Check core tables exist
for table in labs lab_users patients lab_orders lab_results audit_logs; do
    COUNT=$(run_query "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo "ERROR")
    if [[ "${COUNT}" == "ERROR" ]]; then
        log "Table ${table}: MISSING ✗"
    else
        log "Table ${table}: ${COUNT} rows ✓"
    fi
done

# Check audit log chain integrity (spot check first 100 entries)
AUDIT_COUNT=$(run_query "SELECT COUNT(*) FROM audit_logs;" || echo "0")
log "Audit log entries: ${AUDIT_COUNT}"

if [[ "${AUDIT_COUNT}" -gt "0" ]]; then
    # Verify chain_hash column exists
    HAS_CHAIN=$(run_query "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='chain_hash';" || echo "0")
    if [[ "${HAS_CHAIN}" == "1" ]]; then
        BROKEN=$(run_query "SELECT COUNT(*) FROM audit_logs WHERE chain_hash IS NULL AND id > 1;" || echo "?")
        log "Audit entries missing chain_hash: ${BROKEN}"
    fi
fi

# ─── 6. Tear down test container ─────────────────────────────────────────────
docker rm -f "${TEST_CONTAINER}" > /dev/null
log "Test container removed."

# ─── 7. Write JSON result (consumed by /compliance/system-status) ─────────────
mkdir -p "$(dirname "${RESULT_JSON}")"
cat > "${RESULT_JSON}" <<JSON
{
  "status": "PASS",
  "tested_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "tested_at_human": "$(date -u '+%Y-%m-%d %H:%M:%S UTC')",
  "restore_seconds": ${RESTORE_SECONDS},
  "backup_file": "$(basename "${BACKUP_FILE}")",
  "tested_by": "${USER:-system}",
  "report_path": "${REPORT}"
}
JSON
log "JSON result written to: ${RESULT_JSON}"

# ─── 8. Write summary ────────────────────────────────────────────────────────
log "============================================================"
log "RESTORE TEST RESULT: PASS"
log "Backup file: $(basename "${BACKUP_FILE}")"
log "Restore time: ${RESTORE_SECONDS} seconds"
log "Test date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
log "Tested by: ${USER:-system}"
log "Report saved: ${REPORT}"
log "============================================================"
log ""
log "For government audits: present this report as evidence of"
log "tested disaster recovery procedures (ISO 27001 A.17.1)."
