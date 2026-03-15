#!/bin/bash
# =============================================================================
# GULA Platform - Database Backup Script
# Supports both v1 (simple) and production (docker) deployments
# Usage: ./scripts/backup.sh [daily|hourly]
# Schedule with cron: 0 2 * * * /path/to/gula-platform/scripts/backup.sh daily
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/home/user/gula-platform/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-gula}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-daily}"

mkdir -p "${BACKUP_DIR}/daily"
mkdir -p "${BACKUP_DIR}/hourly"
mkdir -p "${BACKUP_DIR}/logs"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${BACKUP_DIR}/logs/backup.log"; }

log "Starting ${BACKUP_TYPE} backup..."

case "${BACKUP_TYPE}" in
    daily|full)
        DEST="${BACKUP_DIR}/daily/gula_full_${TIMESTAMP}.sql.gz"
        PGPASSWORD="${PGPASSWORD:-postgres}" pg_dump \
            -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" \
            --no-owner --no-privileges \
            | gzip > "${DEST}" && log "Daily backup: ${DEST} ($(du -h "${DEST}" | cut -f1))" \
            || log "ERROR: Daily backup failed"
        ;;
    hourly|incremental)
        DEST="${BACKUP_DIR}/hourly/gula_hourly_${TIMESTAMP}.sql.gz"
        PGPASSWORD="${PGPASSWORD:-postgres}" pg_dump \
            -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" \
            --no-owner --no-privileges \
            | gzip > "${DEST}" && log "Hourly backup: ${DEST} ($(du -h "${DEST}" | cut -f1))" \
            || log "ERROR: Hourly backup failed"
        ;;
esac

# Cleanup old backups
find "${BACKUP_DIR}/hourly" -name "*.gz" -mtime +2 -delete 2>/dev/null || true
find "${BACKUP_DIR}/daily"  -name "*.gz" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true

log "Backup complete. Cleanup done."
log "Current backups: $(find "${BACKUP_DIR}" -name "*.gz" | wc -l) files"
