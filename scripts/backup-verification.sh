#!/bin/bash

# GULA Platform - Backup Verification Script
# This script verifies that backups are working correctly and can be restored

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/gula}"
LOG_FILE="${LOG_FILE:-/var/log/gula-backup-verification.log}"
DB_USER="${DB_USER:-gula_user}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-gula_platform}"
TEST_DB_NAME="${TEST_DB_NAME:-gula_platform_test}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ $1${NC}" | tee -a "$LOG_FILE"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "=========================================="
log "GULA Platform - Backup Verification"
log "=========================================="

# Step 1: Check if backups exist
log "Step 1: Checking for existing backups..."
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "db_*.sql.gz" | wc -l)

if [ $BACKUP_COUNT -eq 0 ]; then
    log_error "No backups found in $BACKUP_DIR"
    exit 1
fi

log_success "Found $BACKUP_COUNT backups"

# Step 2: Get the latest backup
log "Step 2: Finding latest backup..."
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_*.sql.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    log_error "Could not find latest backup"
    exit 1
fi

BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
log_success "Latest backup: $LATEST_BACKUP (Size: $BACKUP_SIZE)"

# Step 3: Verify backup integrity
log "Step 3: Verifying backup integrity..."
if gunzip -t "$LATEST_BACKUP" 2>/dev/null; then
    log_success "Backup integrity verified"
else
    log_error "Backup integrity check failed"
    exit 1
fi

# Step 4: Test restore to test database
log "Step 4: Testing restore to test database..."

# Drop test database if it exists
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "DROP DATABASE IF EXISTS $TEST_DB_NAME;" 2>/dev/null || true

# Create test database
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE $TEST_DB_NAME;" 2>/dev/null

# Restore backup
if gunzip -c "$LATEST_BACKUP" | mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TEST_DB_NAME" 2>/dev/null; then
    log_success "Restore to test database successful"
else
    log_error "Restore to test database failed"
    exit 1
fi

# Step 5: Verify restored data
log "Step 5: Verifying restored data..."

# Check table count
TABLE_COUNT=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TEST_DB_NAME" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$TEST_DB_NAME';" 2>/dev/null | tail -1)

if [ "$TABLE_COUNT" -gt 0 ]; then
    log_success "Restored database has $TABLE_COUNT tables"
else
    log_error "Restored database appears to be empty"
    exit 1
fi

# Check specific tables
REQUIRED_TABLES=("users" "patients" "samples" "results" "audit_logs")
for table in "${REQUIRED_TABLES[@]}"; do
    TABLE_EXISTS=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TEST_DB_NAME" -e "SHOW TABLES LIKE '$table';" 2>/dev/null | grep -c "$table" || true)
    
    if [ "$TABLE_EXISTS" -gt 0 ]; then
        ROW_COUNT=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$TEST_DB_NAME" -e "SELECT COUNT(*) FROM $table;" 2>/dev/null | tail -1)
        log_success "Table '$table' exists with $ROW_COUNT rows"
    else
        log_warning "Table '$table' not found in restored database"
    fi
done

# Step 6: Cleanup old backups
log "Step 6: Cleaning up old backups..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)

if [ "$DELETED_COUNT" -gt 0 ]; then
    log_success "Deleted $DELETED_COUNT old backups (older than $RETENTION_DAYS days)"
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
- Backup Age: $(find "$LATEST_BACKUP" -printf '%T@' | xargs -I {} date -d @{} +%s | xargs -I {} echo "$(( ($(date +%s) - {}) / 86400 )) days old")

Verification Results:
- Integrity Check: PASSED
- Restore Test: PASSED
- Data Verification: PASSED
- Tables Count: $TABLE_COUNT

Retention Policy:
- Retention Days: $RETENTION_DAYS
- Deleted Backups: $DELETED_COUNT

Status: SUCCESS ✓
EOF

log_success "Report generated: $REPORT_FILE"

# Step 8: Send notification (optional)
if command -v mail &> /dev/null; then
    ALERT_EMAIL="${ALERT_EMAIL:-}"
    if [ -n "$ALERT_EMAIL" ]; then
        log "Sending verification report to $ALERT_EMAIL..."
        mail -s "GULA Platform - Backup Verification Report" "$ALERT_EMAIL" < "$REPORT_FILE"
        log_success "Report sent"
    fi
fi

# Drop test database
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "DROP DATABASE $TEST_DB_NAME;" 2>/dev/null

log_success "=========================================="
log_success "Backup verification completed successfully!"
log_success "=========================================="

exit 0
