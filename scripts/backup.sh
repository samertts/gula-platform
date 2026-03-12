#!/bin/bash
# =============================================================================
# GULA Platform - Database Backup Script
# Executive Order 20: Hourly backups + Daily full backups
# =============================================================================

set -euo pipefail

BACKUP_DIR="/backups/gula"
DB_HOST="postgres-primary"
DB_USER="postgres"
DB_NAME="labdb"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-incremental}"

mkdir -p "${BACKUP_DIR}/hourly"
mkdir -p "${BACKUP_DIR}/daily"
mkdir -p "${BACKUP_DIR}/logs"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${BACKUP_DIR}/logs/backup.log"; }

log "Starting ${BACKUP_TYPE} backup..."

case "${BACKUP_TYPE}" in
    daily|full)
        DEST="${BACKUP_DIR}/daily/full_${TIMESTAMP}.sql.gz"
        PGPASSWORD="${POSTGRES_PASSWORD:-gula_secure_2024}" pg_dump \
            -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" \
            --format=custom --compress=9 \
            --file="${DEST}" && log "Daily backup: ${DEST}" || log "ERROR: Daily backup failed"
        ;;
    hourly|incremental)
        DEST="${BACKUP_DIR}/hourly/hourly_${TIMESTAMP}.sql.gz"
        PGPASSWORD="${POSTGRES_PASSWORD:-gula_secure_2024}" pg_dump \
            -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" \
            | gzip > "${DEST}" && log "Hourly backup: ${DEST}" || log "ERROR: Hourly backup failed"
        ;;
esac

# Cleanup old backups
find "${BACKUP_DIR}/hourly" -name "*.gz" -mtime +2 -delete
find "${BACKUP_DIR}/daily"  -name "*.gz" -mtime +"${RETENTION_DAYS}" -delete

log "Backup complete. Cleanup done."
