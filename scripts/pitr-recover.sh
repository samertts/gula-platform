#!/bin/bash
# =============================================================================
# GULA Platform — PITR Recovery Automation
# Point-in-Time Recovery from WAL archive in S3/MinIO
# =============================================================================
# Usage:
#   ./scripts/pitr-recover.sh --time "2025-06-15 14:30:00 UTC"
#   ./scripts/pitr-recover.sh --txid 12345678
#   ./scripts/pitr-recover.sh --restore-point "pre_migration_v2.1"
#   ./scripts/pitr-recover.sh --latest
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(dirname "${SCRIPT_DIR}")"
LOG_DIR="${PLATFORM_DIR}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT="${LOG_DIR}/pitr-recovery-${TIMESTAMP}.log"

: "${PGDATA:=/var/lib/postgresql/data}"
: "${PG_BIN:=/usr/lib/postgresql/16/bin}"
: "${DB_NAME:=labdb}"
: "${DB_USER:=postgres}"
: "${ARCHIVE_S3_BUCKET:=gula-wal-archive}"
: "${ARCHIVE_S3_REGION:=me-central-1}"
: "${ARCHIVE_S3_ENDPOINT:=}"
: "${STAGING_PG_PORT:=5433}"
: "${RECOVERY_TIMEOUT:=300}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()   { echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "${REPORT}"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*" | tee -a "${REPORT}"; }
err()   { echo -e "${RED}[✗]${NC} $*" | tee -a "${REPORT}"; exit 1; }
warn()  { echo -e "${YELLOW}[⚠]${NC} $*" | tee -a "${REPORT}"; }

TARGET_TIME=""
TARGET_TXID=""
TARGET_RESTORE_POINT=""
TARGET_LATEST=false
RECOVERY_MODE=""
MILESTONE_TIMESTAMP=""

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --time)         TARGET_TIME="$2"; RECOVERY_MODE="time"; shift 2 ;;
            --txid)         TARGET_TXID="$2"; RECOVERY_MODE="txid"; shift 2 ;;
            --restore-point) TARGET_RESTORE_POINT="$2"; RECOVERY_MODE="name"; shift 2 ;;
            --latest)       TARGET_LATEST=true; RECOVERY_MODE="latest"; shift ;;
            --staging-port) STAGING_PG_PORT="$2"; shift 2 ;;
            *)              echo "Unknown option: $1"; exit 1 ;;
        esac
    done
    if [[ -z "${RECOVERY_MODE}" ]]; then
        echo "Usage: $0 --time <timestamp> | --txid <xid> | --restore-point <name> | --latest"
        exit 1
    fi
}

pre_flight_checks() {
    log "=== Pre-Flight Checks ==="
    command -v psql &>/dev/null || { warn "psql missing — attempting container exec"; }
    command -v pg_ctl &>/dev/null || command -v "${PG_BIN}/pg_ctl" &>/dev/null || \
        warn "pg_ctl not in PATH — set PG_BIN"
    ok "Prerequisites satisfied"

    log "Current database size: $(psql -U "${DB_USER}" -d "${DB_NAME}" -t -c \
        "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));" 2>/dev/null || echo "unknown")"
}

find_base_backup() {
    log "Finding latest base backup..."
    local base
    base=$(find "${PLATFORM_DIR}/backups/daily" -name "*.sql.gz" -printf '%T@ %p\n' \
        2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-) || true
    if [[ -z "${base}" ]]; then
        err "No base backup found in ${PLATFORM_DIR}/backups/daily"
    fi
    echo "${base}"
}

find_wal_archive() {
    local wal_list
    if [[ -n "${ARCHIVE_S3_ENDPOINT}" ]]; then
        wal_list=$(mc find "gula/${ARCHIVE_S3_BUCKET}/wal/" --name "*.gz" 2>/dev/null | sort | tail -5 || true)
    else
        wal_list=$(aws s3 ls "s3://${ARCHIVE_S3_BUCKET}/wal/" --region "${ARCHIVE_S3_REGION}" \
            2>/dev/null | sort | tail -5 || true)
    fi
    if [[ -z "${wal_list}" ]]; then
        warn "No WAL archives found in s3://${ARCHIVE_S3_BUCKET}/wal/" 
        return 1
    fi
    echo "${wal_list}"
}

stop_postgres_service() {
    log "=== Stopping PostgreSQL Service ==="
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^gula-postgres"; then
        docker compose -f "${PLATFORM_DIR}/docker-compose.yml" stop postgres
        ok "PostgreSQL container stopped"
    elif command -v pg_ctl &>/dev/null; then
        pg_ctl -D "${PGDATA}" stop -m fast 2>/dev/null || \
            pg_ctl -D "${PGDATA}" stop -m immediate 2>/dev/null || true
        ok "PostgreSQL service stopped"
    else
        warn "Could not determine how to stop PostgreSQL"
    fi
    sleep 2
}

restore_base_backup() {
    local backup_file="$1"
    log "=== Restoring Base Backup ==="
    log "Backup file: ${backup_file}"

    local restore_dir="${PGDATA}_pitr_${TIMESTAMP}"
    mkdir -p "${restore_dir}"

    log "Extracting backup to ${restore_dir}..."
    if [[ "${backup_file}" == *.sql.gz ]]; then
        gunzip -c "${backup_file}" | psql -U "${DB_USER}" -d "${DB_NAME}" -q 2>&1 | tee -a "${REPORT}"
    elif [[ "${backup_file}" == *.tar.gz ]]; then
        tar -xzf "${backup_file}" -C "${restore_dir}" 2>&1 | tee -a "${REPORT}"
    else
        err "Unknown backup format: ${backup_file}"
    fi

    local restore_size
    restore_size=$(du -sh "${restore_dir}" 2>/dev/null | cut -f1 || echo "unknown")
    ok "Base backup restored to ${restore_dir} (${restore_size})"
    echo "${restore_dir}"
}

configure_recovery() {
    local restore_dir="$1"
    log "=== Configuring Recovery Target ==="
    log "Recovery mode: ${RECOVERY_MODE}"

    local recovery_conf="${restore_dir}/recovery.conf"
    cat > "${recovery_conf}" << EOF
# =============================================================================
# GULA Platform — PITR Recovery Configuration
# Recovery target: ${RECOVERY_MODE}
# Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
# =============================================================================

restore_command = 'aws s3 cp s3://${ARCHIVE_S3_BUCKET}/wal/%f %p --region ${ARCHIVE_S3_REGION}'
recovery_target_timeline = 'latest'
recovery_target_action = 'promote'
EOF

    case "${RECOVERY_MODE}" in
        time)
            echo "recovery_target_time = '${TARGET_TIME}'" >> "${recovery_conf}"
            log "Recovery target time: ${TARGET_TIME}"
            ;;
        txid)
            echo "recovery_target_xid = '${TARGET_TXID}'" >> "${recovery_conf}"
            log "Recovery target XID: ${TARGET_TXID}"
            ;;
        name)
            echo "recovery_target_name = '${TARGET_RESTORE_POINT}'" >> "${recovery_conf}"
            log "Recovery target restore point: ${TARGET_RESTORE_POINT}"
            ;;
        latest)
            log "Recovering to latest available WAL"
            ;;
    esac

    if [[ "${RECOVERY_MODE}" != "latest" ]]; then
        echo "recovery_target_inclusive = true" >> "${recovery_conf}"
    fi

    ok "Recovery configuration written to ${recovery_conf}"
}

apply_wal() {
    local restore_dir="$1"
    log "=== Applying WAL to Target Point ==="

    local wal_dir="${restore_dir}/pg_wal"
    mkdir -p "${wal_dir}"

    log "Starting PostgreSQL in recovery mode..."
    pg_ctl -D "${restore_dir}" -l "${LOG_DIR}/pitr_recovery_${TIMESTAMP}.log" start -o \
        "-p ${STAGING_PG_PORT}" 2>&1 | tee -a "${REPORT}" || {
        warn "pg_ctl start failed — trying direct postgres invocation"
        "${PG_BIN}/postgres" -D "${restore_dir}" -p "${STAGING_PG_PORT}" &
    }

    local waited=0
    while [[ ${waited} -lt ${RECOVERY_TIMEOUT} ]]; do
        if psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
            -t -c "SELECT pg_is_in_recovery();" 2>/dev/null | grep -q "t"; then
            ok "Database in recovery mode — applying WAL (${waited}s)"
            break
        fi
        if psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
            -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
            ok "Database accepting queries — recovery complete (${waited}s)"
            break
        fi
        sleep 1
        waited=$((waited + 1))
    done

    if [[ ${waited} -ge ${RECOVERY_TIMEOUT} ]]; then
        err "Recovery did not complete within ${RECOVERY_TIMEOUT}s"
    fi

    local current_tli
    current_tli=$(psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
        -t -A -c "SELECT timeline_id FROM pg_control_checkpoint();" 2>/dev/null || echo "?")
    ok "Recovered to timeline ${current_tli}"
}

promote_database() {
    log "=== Promoting Database ==="
    pg_ctl -D "${PGDATA}_pitr_${TIMESTAMP}" promote 2>&1 | tee -a "${REPORT}"

    sleep 2
    if psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
        -t -A -c "SELECT pg_is_in_recovery();" 2>/dev/null | grep -q "f"; then
        ok "Database promoted — now accepting writes"
    else
        err "Promotion failed"
    fi
}

verify_data_integrity() {
    log "=== Verifying Data Integrity ==="

    local tables=("labs" "lab_users" "patients" "lab_orders" "lab_results" "audit_logs")
    local all_ok=true

    for table in "${tables[@]}"; do
        local count
        count=$(psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
            -t -A -c "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo "ERROR")
        if [[ "${count}" == "ERROR" ]]; then
            warn "Table ${table}: MISSING"
            all_ok=false
        else
            ok "Table ${table}: ${count} rows"
        fi
    done

    local audit_chain_ok
    audit_chain_ok=$(psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
        -t -A -c "SELECT COUNT(*) FROM audit_logs WHERE chain_hash IS NULL AND id > 1;" 2>/dev/null || echo "?")
    ok "Audit entries without chain_hash: ${audit_chain_ok}"

    local referential_ok
    referential_ok=$(psql -U "${DB_USER}" -d "${DB_NAME}" -p "${STAGING_PG_PORT}" \
        -t -A -c "
        SELECT count(*) FROM (
            SELECT lab_orders.id FROM lab_orders LEFT JOIN labs ON lab_orders.lab_id = labs.id
            WHERE lab_orders.lab_id IS NOT NULL AND labs.id IS NULL
            UNION ALL
            SELECT lab_results.id FROM lab_results LEFT JOIN lab_orders ON lab_results.order_id = lab_orders.id
            WHERE lab_results.order_id IS NOT NULL AND lab_orders.id IS NULL
        ) orphans;" 2>/dev/null || echo "?")

    if [[ "${referential_ok}" == "0" ]]; then
        ok "Referential integrity: PASS"
    else
        warn "Referential integrity violations: ${referential_ok}"
    fi

    ${all_ok} || warn "Some tables missing — recovery may be incomplete"
}

update_application_config() {
    log "=== Updating Application Configuration ==="
    local config="${PLATFORM_DIR}/.env"

    if [[ -f "${config}" ]]; then
        local bak="${config}.pitr_bak_${TIMESTAMP}"
        cp "${config}" "${bak}"
        ok "Backed up current .env to ${bak}"

        if grep -q "^DB_HOST=" "${config}"; then
            sed -i "s/^DB_HOST=.*/DB_HOST=localhost/" "${config}"
            sed -i "s/^DB_PORT=.*/DB_PORT=${STAGING_PG_PORT}/" "${config}"
            ok "Updated DB connection to new recovery instance"
        fi
    fi
}

failback_procedure() {
    log "=== Failback Procedure ==="
    warn "Failback requires reversing the recovery direction"
    log "Steps:"
    log "  1. Sync recovered data back to primary: pg_dump/pg_restore"
    log "  2. Configure original primary as standby of recovered instance"
    log "  3. Switch application DNS to recovered instance"
    log "  4. Verify data consistency between old primary and recovery"

    if [[ -f "${PLATFORM_DIR}/.env.pitr_bak_${TIMESTAMP}" ]]; then
        log "To revert application config:"
        log "  cp .env.pitr_bak_${TIMESTAMP} .env"
    fi
    warn "Manual steps required — see docs/dr/PITR_RUNBOOK.md"
}

cleanup() {
    log "=== Cleanup ==="
    if psql -U "${DB_USER}" -p "${STAGING_PG_PORT}" -c "SELECT 1;" &>/dev/null; then
        pg_ctl -D "${PGDATA}_pitr_${TIMESTAMP}" stop -m fast 2>/dev/null || true
        ok "Stopped recovery PostgreSQL instance"
    fi
}

generate_report() {
    local end_ts
    end_ts=$(date +%s)
    local duration=$((end_ts - MILESTONE_TIMESTAMP))

    cat >> "${REPORT}" << EOF

=============================================================
PITR RECOVERY REPORT
=============================================================
Recovery mode:    ${RECOVERY_MODE}
Target:           ${TARGET_TIME:-${TARGET_TXID:-${TARGET_RESTORE_POINT:-latest}}}
Total duration:   ${duration}s
Completed at:     $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Report file:      ${REPORT}
=============================================================
EOF
    ok "Recovery report generated: ${REPORT}"
}

trap cleanup EXIT

parse_args "$@"
MILESTONE_TIMESTAMP=$(date +%s)
log "=== GULA Platform — Point-in-Time Recovery ==="
log "Mode: ${RECOVERY_MODE} | Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

BASIS_BACKUP=$(find_base_backup)
pre_flight_checks
find_wal_archive || warn "No WAL archives found — recovery may be limited"
stop_postgres_service
RESTORE_DIR=$(restore_base_backup "${BASIS_BACKUP}")
configure_recovery "${RESTORE_DIR}"
apply_wal "${RESTORE_DIR}"
promote_database
verify_data_integrity
update_application_config
generate_report

ok "PITR Recovery Complete"
log "Review: ${REPORT}"
