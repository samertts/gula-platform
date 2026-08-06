#!/bin/bash
# =============================================================================
# GULA Platform — Continuous Backup
# Self-hosted-first: writes local dumps by default. Optional off-site copy via
# S3 only when AWS_ACCESS_KEY_ID is set (documented exception, never required).
# =============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
S3_BUCKET="${S3_BUCKET:-s3://gula-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
RETENTION_WEEKS="${RETENTION_WEEKS:-12}"
RETENTION_MONTHS="${RETENTION_MONTHS:-12}"
DB_NAME="${DB_NAME:-labdb}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DATE=$(date +%Y%m%d-%H%M%S)

log() { printf '[BACKUP] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

upload_remote() {
    if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && command -v aws >/dev/null 2>&1; then
        aws s3 cp "$1" "$2" --storage-class STANDARD_IA 2>/dev/null && return 0
    fi
    log "Remote upload skipped (no AWS credentials / aws cli) — local copy retained"
    return 0
}

do_full_backup() {
    log "Starting full backup..."
    mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"
    PGPASSWORD="${DB_PASSWORD:-}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -Fc -f "$BACKUP_DIR/daily/${DB_NAME}_${DATE}.dump"
    gzip "$BACKUP_DIR/daily/${DB_NAME}_${DATE}.dump"
    local FILE="$BACKUP_DIR/daily/${DB_NAME}_${DATE}.dump.gz"
    upload_remote "$FILE" "$S3_BUCKET/daily/"
    log "Full backup complete: $FILE"
}

do_wal_archive() {
    log "Archiving WAL files..."
    if command -v aws >/dev/null 2>&1 && [ -n "${AWS_ACCESS_KEY_ID:-}" ]; then
        aws s3 sync /var/lib/postgresql/data/pg_wal/ "$S3_BUCKET/wal/" --exclude "archive_status/*" 2>/dev/null || true
    fi
}

do_weekly_retention() {
    local DOW=$(date +%u)
    [ "$DOW" -ne 7 ] && return
    log "Running weekly retention..."
    local LATEST=$(ls -t "$BACKUP_DIR/daily/${DB_NAME}"_*.dump.gz 2>/dev/null | head -1)
    [ -n "$LATEST" ] || return
    cp "$LATEST" "$BACKUP_DIR/weekly/"
    upload_remote "$BACKUP_DIR/weekly/$(basename "$LATEST")" "$S3_BUCKET/weekly/"
}

do_monthly_retention() {
    local DOM=$(date +%d)
    [ "$DOM" -ne 1 ] && return
    log "Running monthly retention..."
    local LATEST=$(ls -t "$BACKUP_DIR/daily/${DB_NAME}"_*.dump.gz 2>/dev/null | head -1)
    [ -n "$LATEST" ] || return
    cp "$LATEST" "$BACKUP_DIR/monthly/"
    upload_remote "$BACKUP_DIR/monthly/$(basename "$LATEST")" "$S3_BUCKET/monthly/"
}

do_cleanup() {
    log "Cleaning backups older than ${RETENTION_DAYS}d..."
    find "$BACKUP_DIR/daily" -name "*.dump.gz" -mtime +"$RETENTION_DAYS" -delete
    find "$BACKUP_DIR/weekly" -name "*.dump.gz" -mtime +$((RETENTION_WEEKS * 7)) -delete
    find "$BACKUP_DIR/monthly" -name "*.dump.gz" -mtime +$((RETENTION_MONTHS * 30)) -delete
    log "Cleanup complete."
}

do_metrics() {
    local BACKUP_SIZE=$(du -sh "$BACKUP_DIR/daily" 2>/dev/null | cut -f1)
    local BACKUP_AGE=0
    local LATEST=$(ls -t "$BACKUP_DIR/daily"/*.dump.gz 2>/dev/null | head -1)
    [ -n "$LATEST" ] && BACKUP_AGE=$(($(date +%s) - $(stat -c %Y "$LATEST")))
    echo "gula_backup_size_bytes $(du -sb "$BACKUP_DIR/daily" 2>/dev/null | cut -f1)" | curl -sf --data-binary @- http://localhost:9091/metrics/job/backup 2>/dev/null || true
    echo "gula_backup_age_seconds $BACKUP_AGE" | curl -sf --data-binary @- http://localhost:9091/metrics/job/backup 2>/dev/null || true
    log "Metrics: size=$BACKUP_SIZE, age=${BACKUP_AGE}s"
}

case "${1:-full}" in
    full)     do_full_backup; do_cleanup ;;
    wal)      do_wal_archive ;;
    weekly)   do_weekly_retention ;;
    monthly)  do_monthly_retention ;;
    cleanup)  do_cleanup ;;
    metrics)  do_metrics ;;
    *)
        do_full_backup
        do_wal_archive
        do_cleanup
        do_metrics
        ;;
esac
log "Backup operation '${1:-all}' complete."
