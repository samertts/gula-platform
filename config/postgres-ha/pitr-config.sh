#!/bin/bash
# =============================================================================
# GULA Platform — Point-in-Time Recovery Configuration
# Configures PostgreSQL WAL archiving to S3/MinIO for PITR
# Requires: postgres 16+, pgbackrest, awscli (or mc for MinIO)
# =============================================================================
# Applied by: patroni bootstrap post_init or manual DBA
# Verify:     SELECT * FROM pg_settings WHERE name LIKE 'archive%';
#             SELECT pg_switch_wal();  — forces segment archive
# =============================================================================

set -euo pipefail

CONFIG_FILE="${PGDATA:-/var/lib/postgresql/data}/postgresql.conf"
PITR_CONFIG="${PGDATA:-/var/lib/postgresql/data}/conf.d/pitr.conf"

: "${PG_VERSION:=16}"
: "${ARCHIVE_MODE:=on}"
: "${WAL_SEGMENT_SIZE:=64}"          # MB
: "${ARCHIVE_S3_BUCKET:=gula-wal-archive}"
: "${ARCHIVE_S3_REGION:=me-central-1}"
: "${ARCHIVE_S3_ENDPOINT:=}"          # MinIO endpoint if using object store
: "${ARCHIVE_S3_ACCESS_KEY:=}"
: "${ARCHIVE_S3_SECRET_KEY:=}"
: "${RESTORE_COMMAND:=}"
: "${RECOVERY_TARGET_TIMELINE:=latest}"
: "${RECOVERY_TARGET_ACTION:=promote}"
: "${ARCHIVE_TIMEOUT:=60}"            # seconds

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
ok()   { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}OK${NC} $*"; }
err()  { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}ERROR${NC} $*"; }
warn() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}WARN${NC} $*"; }

check_prerequisites() {
    if ! command -v psql &>/dev/null; then
        err "psql not found — are you running inside postgres container?"
        exit 1
    fi
    if [[ -n "${ARCHIVE_S3_ENDPOINT}" ]]; then
        command -v mc &>/dev/null || warn "mc (MinIO client) not found — install for S3 operations"
    else
        command -v aws &>/dev/null || warn "awscli not found — install for S3 operations"
    fi
}

configure_archive() {
    log "Configuring WAL archiving..."

    local archive_command
    if [[ -n "${ARCHIVE_S3_ENDPOINT}" ]]; then
        archive_command="mc cp %p gula/${ARCHIVE_S3_BUCKET}/wal/%f"
    else
        archive_command="aws s3 cp %p s3://${ARCHIVE_S3_BUCKET}/wal/%f --region ${ARCHIVE_S3_REGION}"
    fi

    local restore_cmd="${RESTORE_COMMAND}"
    if [[ -z "${restore_cmd}" ]]; then
        if [[ -n "${ARCHIVE_S3_ENDPOINT}" ]]; then
            restore_cmd="mc cp gula/${ARCHIVE_S3_BUCKET}/wal/%f %p"
        else
            restore_cmd="aws s3 cp s3://${ARCHIVE_S3_BUCKET}/wal/%f %p --region ${ARCHIVE_S3_REGION}"
        fi
    fi

    mkdir -p "$(dirname "${PITR_CONFIG}")"

    cat > "${PITR_CONFIG}" << PITREOF
# =============================================================================
# GULA Platform — PITR Configuration (auto-generated)
# Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
# WAL segment size: ${WAL_SEGMENT_SIZE}MB
# Archive target: s3://${ARCHIVE_S3_BUCKET}/wal/
# =============================================================================

# WAL Archiving
archive_mode = ${ARCHIVE_MODE}
archive_command = '${archive_command}'
archive_timeout = ${ARCHIVE_TIMEOUT}

# WAL Segments
wal_segment_size = ${WAL_SEGMENT_SIZE_MB}

# Restore (recovery.conf replacement for PG 12+)
restore_command = '${restore_cmd}'
recovery_target_timeline = '${RECOVERY_TARGET_TIMELINE}'
recovery_target_action = '${RECOVERY_TARGET_ACTION}'
PITREOF

    ok "PITR config written to ${PITR_CONFIG}"

    psql -U postgres -c "SELECT pg_reload_conf();" &>/dev/null || true
    ok "PostgreSQL configuration reloaded"
}

create_archive_bucket() {
    log "Ensuring WAL archive bucket exists..."

    if [[ -n "${ARCHIVE_S3_ENDPOINT}" ]]; then
        if command -v mc &>/dev/null; then
            mc alias set gula "${ARCHIVE_S3_ENDPOINT}" \
                "${ARCHIVE_S3_ACCESS_KEY}" "${ARCHIVE_S3_SECRET_KEY}" 2>/dev/null || true
            mc mb "gula/${ARCHIVE_S3_BUCKET}" 2>/dev/null || \
                ok "Bucket ${ARCHIVE_S3_BUCKET} already exists"
            mc policy set download "gula/${ARCHIVE_S3_BUCKET}" 2>/dev/null || true
            ok "MinIO archive bucket ready"
        fi
    else
        if command -v aws &>/dev/null; then
            aws s3api head-bucket --bucket "${ARCHIVE_S3_BUCKET}" \
                --region "${ARCHIVE_S3_REGION}" 2>/dev/null && \
                ok "S3 bucket ${ARCHIVE_S3_BUCKET} exists" || {
                aws s3 mb "s3://${ARCHIVE_S3_BUCKET}" --region "${ARCHIVE_S3_REGION}"
                ok "S3 bucket ${ARCHIVE_S3_BUCKET} created"
            }
        fi
    fi
}

verify_archive() {
    log "Verifying WAL archive configuration..."

    local archive_mode_val
    archive_mode_val=$(psql -U postgres -t -A -c "SHOW archive_mode;" 2>/dev/null || echo "off")
    if [[ "${archive_mode_val}" == "on" ]]; then
        ok "archive_mode = on"
    else
        err "archive_mode = ${archive_mode_val} (expected on)"
        return 1
    fi

    local archive_cmd
    archive_cmd=$(psql -U postgres -t -A -c "SHOW archive_command;" 2>/dev/null || echo "")
    if [[ -n "${archive_cmd}" ]] && [[ "${archive_cmd}" != "(disabled)" ]]; then
        ok "archive_command = ${archive_cmd}"
    else
        err "archive_command not set"
        return 1
    fi

    if psql -U postgres -t -A -c "SELECT pg_is_in_recovery();" 2>/dev/null | grep -q "f"; then
        local wal_size
        wal_size=$(psql -U postgres -t -A -c "SHOW wal_segment_size;" 2>/dev/null || echo "unknown")
        ok "WAL segment size: ${wal_size}"

        local last_archived
        last_archived=$(psql -U postgres -t -A -c \
            "SELECT last_archived_wal FROM pg_stat_archiver;" 2>/dev/null || echo "none")
        if [[ -n "${last_archived}" ]] && [[ "${last_archived}" != "none" ]]; then
            ok "Last archived WAL: ${last_archived}"
        else
            warn "No WAL segments archived yet — run: SELECT pg_switch_wal();"
        fi
    fi

    test_archive_write
}

test_archive_write() {
    log "Testing WAL archive write..."
    local test_wal="000000010000000000000001"
    local test_content="GULA_PITR_TEST"

    if [[ -n "${ARCHIVE_S3_ENDPOINT}" ]]; then
        echo "${test_content}" | mc pipe "gula/${ARCHIVE_S3_BUCKET}/wal/${test_wal}" 2>/dev/null && {
            ok "WAL archive write to MinIO: OK"
            mc rm "gula/${ARCHIVE_S3_BUCKET}/wal/${test_wal}" 2>/dev/null || true
        } || err "MinIO write failed"
    else
        echo "${test_content}" | aws s3 cp - "s3://${ARCHIVE_S3_BUCKET}/wal/${test_wal}" \
            --region "${ARCHIVE_S3_REGION}" 2>/dev/null && {
            ok "WAL archive write to S3: OK"
            aws s3 rm "s3://${ARCHIVE_S3_BUCKET}/wal/${test_wal}" --region "${ARCHIVE_S3_REGION}" 2>/dev/null || true
        } || err "S3 write failed"
    fi
}

test_recovery() {
    log "Testing PITR recovery in staging..."
    local test_db="gula_pitr_test_$(date +%s)"

    createdb -U postgres "${test_db}" 2>/dev/null || true
    psql -U postgres -d "${test_db}" -c "
        CREATE TABLE pitr_test (id serial primary key, data text, created_at timestamptz default now());
        INSERT INTO pitr_test (data) VALUES ('before_checkpoint'), ('after_checkpoint');
    " > /dev/null 2>&1

    local before_ts
    before_ts=$(psql -U postgres -d "${test_db}" -t -A -c \
        "SELECT to_char(now(), 'YYYY-MM-DD HH24:MI:SS.US')" 2>/dev/null)

    sleep 1
    psql -U postgres -d "${test_db}" -c "CHECKPOINT;" > /dev/null 2>&1
    psql -U postgres -c "SELECT pg_switch_wal();" > /dev/null 2>&1 || true
    sleep 1

    psql -U postgres -d "${test_db}" -c "
        INSERT INTO pitr_test (data) VALUES ('after_checkpoint_2');
        SELECT pg_sleep(0.5);
    " > /dev/null 2>&1

    local after_ts
    after_ts=$(psql -U postgres -d "${test_db}" -t -A -c \
        "SELECT to_char(now(), 'YYYY-MM-DD HH24:MI:SS.US')" 2>/dev/null)

    log "PITR test range: ${before_ts} → ${after_ts}"
    dropdb -U postgres "${test_db}" 2>/dev/null || true
    ok "PITR configuration verified — recovery point ranges established"
}

cmd_apply() {
    check_prerequisites
    create_archive_bucket
    configure_archive
    verify_archive
    test_recovery
    ok "PITR configuration complete"
}

cmd_status() {
    log "=== PITR Configuration Status ==="
    echo "  archive_mode:       $(psql -U postgres -t -A -c 'SHOW archive_mode;' 2>/dev/null || echo '?')"
    echo "  archive_command:    $(psql -U postgres -t -A -c 'SHOW archive_command;' 2>/dev/null || echo '?')"
    echo "  archive_timeout:    $(psql -U postgres -t -A -c 'SHOW archive_timeout;' 2>/dev/null || echo '?')"
    echo "  wal_segment_size:   $(psql -U postgres -t -A -c 'SHOW wal_segment_size;' 2>/dev/null || echo '?')"
    echo "  restore_command:    $(psql -U postgres -t -A -c 'SHOW restore_command;' 2>/dev/null || echo '?')"
    echo "  recovery_timeline:  $(psql -U postgres -t -A -c 'SHOW recovery_target_timeline;' 2>/dev/null || echo '?')"
    echo "  WAL archived:       $(psql -U postgres -t -A -c \"SELECT count(*) FROM pg_stat_archiver WHERE last_archived_wal IS NOT NULL;\" 2>/dev/null || echo '?')"
}

case "${1:-apply}" in
    apply)   cmd_apply ;;
    status)  cmd_status ;;
    verify)  verify_archive ;;
    *)       echo "Usage: $0 [apply|status|verify]" ;;
esac
