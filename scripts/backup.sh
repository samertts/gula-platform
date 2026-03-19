#!/bin/bash
# =============================================================================
# GULA Platform - Database Backup Script
# Docker-aware: runs pg_dump inside the gula-postgres container
# Usage: ./scripts/backup.sh [daily|hourly|verify]
# Schedule:
#   0 2 * * * /path/to/gula-platform/scripts/backup.sh daily
#   0 * * * * /path/to/gula-platform/scripts/backup.sh hourly
#   0 6 * * * /path/to/gula-platform/scripts/backup.sh verify
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/home/user/gula-platform/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-daily}"

# Docker container name for postgres
PG_CONTAINER="${PG_CONTAINER:-gula-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-labdb}"

mkdir -p "${BACKUP_DIR}/daily"
mkdir -p "${BACKUP_DIR}/hourly"
mkdir -p "${BACKUP_DIR}/logs"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${BACKUP_DIR}/logs/backup.log"; }

# Run pg_dump: prefer Docker (no network exposure), fall back to direct
_pg_dump() {
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${PG_CONTAINER}$"; then
        # Docker-aware: execute inside container — password already configured there
        docker exec "${PG_CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" \
            --no-owner --no-privileges
    elif command -v pg_dump &>/dev/null; then
        # Fallback: direct connection (requires DB_HOST, DB_PORT, PGPASSWORD)
        DB_HOST="${DB_HOST:-localhost}"
        DB_PORT="${DB_PORT:-5432}"
        PGPASSWORD="${PGPASSWORD:?PGPASSWORD required for direct mode}" \
        pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" \
            --no-owner --no-privileges
    else
        log "ERROR: neither docker nor pg_dump available"
        exit 1
    fi
}

# Dump, compress, and write SHA-256 checksum sidecar
_do_backup() {
    local dest="$1"
    log "Dumping ${DB_NAME} to ${dest}..."
    if _pg_dump | gzip > "${dest}"; then
        sha256sum "${dest}" > "${dest}.sha256"
        local size
        size=$(du -h "${dest}" | cut -f1)
        log "Backup OK: ${dest} (${size})"
        log "Checksum:  $(cat "${dest}.sha256")"
    else
        log "ERROR: backup failed"
        rm -f "${dest}"
        exit 1
    fi
}

# Verify a backup file using its .sha256 sidecar
verify_backup() {
    local file="${1:?usage: verify_backup <file.sql.gz>}"
    if [[ ! -f "${file}.sha256" ]]; then
        log "WARN: no checksum sidecar for ${file}"
        return 1
    fi
    if sha256sum -c "${file}.sha256" --quiet; then
        log "VERIFY OK: ${file}"
    else
        log "VERIFY FAILED: ${file} — checksum mismatch (file may be corrupted)"
        return 1
    fi
}

log "Starting ${BACKUP_TYPE} backup (container=${PG_CONTAINER}, db=${DB_NAME})..."

case "${BACKUP_TYPE}" in
    daily|full)
        _do_backup "${BACKUP_DIR}/daily/gula_full_${TIMESTAMP}.sql.gz"
        find "${BACKUP_DIR}/daily" -name "*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
        find "${BACKUP_DIR}/daily" -name "*.sha256"  -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
        ;;
    hourly|incremental)
        _do_backup "${BACKUP_DIR}/hourly/gula_hourly_${TIMESTAMP}.sql.gz"
        find "${BACKUP_DIR}/hourly" -name "*.sql.gz" -mtime +2 -delete 2>/dev/null || true
        find "${BACKUP_DIR}/hourly" -name "*.sha256"  -mtime +2 -delete 2>/dev/null || true
        ;;
    verify)
        LATEST=$(find "${BACKUP_DIR}/daily" -name "*.sql.gz" -printf '%T@ %p\n' 2>/dev/null \
            | sort -n | tail -1 | cut -d' ' -f2-)
        if [[ -z "${LATEST}" ]]; then
            log "No backup files found to verify."
            exit 1
        fi
        verify_backup "${LATEST}"
        ;;
    *)
        echo "Usage: $0 [daily|hourly|verify]"
        exit 1
        ;;
esac

log "Done. Total backups: $(find "${BACKUP_DIR}" -name '*.sql.gz' | wc -l) files"
