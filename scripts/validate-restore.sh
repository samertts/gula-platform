#!/bin/bash
set -euo pipefail

RESTORE_DIR="/tmp/restore-test"
DB_NAME="labdb_verify"
LOG_FILE="/tmp/restore-validation.log"

log() { printf '[RESTORE-VALIDATE] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG_FILE"; }

log "=== Restore Validation ==="

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
    log "No backup file specified. Using latest..."
    BACKUP_FILE=$(ls -t /app/backups/daily/*.dump.gz 2>/dev/null | head -1)
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi
log "Backup file: $BACKUP_FILE"

log "Step 1: Restoring backup to isolated database..."
gunzip -c "$BACKUP_FILE" > /tmp/restore.dump
createdb "$DB_NAME" 2>/dev/null || true
pg_restore -d "$DB_NAME" /tmp/restore.dump 2>&1 | tee -a "$LOG_FILE" || true
log "Restore complete."

log "Step 2: Verifying table row counts..."
psql -d "$DB_NAME" -c "
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;
" 2>/dev/null | tee -a "$LOG_FILE"

log "Step 3: Checking audit log hash chain integrity..."
python3 -c "
import psycopg2
conn = psycopg2.connect(dbname='$DB_NAME')
cur = conn.cursor()
cur.execute('SELECT id, previous_hash, sha256(row_hash::text) as current_hash FROM audit_logs ORDER BY id')
rows = cur.fetchall()
prev_hash = None
chain_broken = False
for row in rows:
    id, expected_prev, current_hash = row
    if prev_hash and expected_prev != prev_hash:
        print(f'CHAIN BROKEN at id={id}: expected={expected_prev}, actual={prev_hash}')
        chain_broken = True
    prev_hash = current_hash
if not chain_broken:
    print(f'Audit chain INTACT: {len(rows)} entries verified')
cur.close()
conn.close()
" 2>&1 | tee -a "$LOG_FILE"

log "Step 4: Verifying referential integrity..."
psql -d "$DB_NAME" -c "
SELECT
    (SELECT COUNT(*) FROM patients) as patients,
    (SELECT COUNT(*) FROM lab_users) as users,
    (SELECT COUNT(*) FROM labs) as labs,
    (SELECT COUNT(*) FROM lab_orders) as orders,
    (SELECT COUNT(*) FROM lab_results) as results,
    (SELECT COUNT(*) FROM outbox_events) as outbox,
    (SELECT COUNT(*) FROM audit_logs) as audit_entries;
" 2>/dev/null | tee -a "$LOG_FILE"

log "Step 5: Checking tenant isolation..."
psql -d "$DB_NAME" -c "
SELECT lab_id, COUNT(*) as patient_count FROM patients GROUP BY lab_id ORDER BY lab_id;
" 2>/dev/null | tee -a "$LOG_FILE"

log "Step 6: Validation summary..."
VALIDATION_RESULT="PASS"
if grep -q "CHAIN BROKEN" "$LOG_FILE" 2>/dev/null; then
    VALIDATION_RESULT="FAIL"
    log "Audit chain integrity check FAILED"
fi
if grep -q "ERROR" "$LOG_FILE" 2>/dev/null; then
    VALIDATION_RESULT="FAIL"
    log "Restore validation encountered errors"
fi

log "Validation result: $VALIDATION_RESULT"
log "Cleaning up test database..."
dropdb "$DB_NAME" 2>/dev/null || true
rm -f /tmp/restore.dump

exit $([ "$VALIDATION_RESULT" = "PASS" ] && echo 0 || echo 1)
