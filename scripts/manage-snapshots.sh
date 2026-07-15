#!/bin/bash
set -euo pipefail

SNAPSHOT_PREFIX="gula-snapshot"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
VOLUME_PATTERN="${VOLUME_PATTERN:-pd-ssd}"

log() { printf '[SNAPSHOT] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

create_snapshot() {
    local NAME="${SNAPSHOT_PREFIX}-$(date +%Y%m%d-%H%M%S)"
    log "Creating snapshot: $NAME"
    gcloud compute disks snapshot "$(gcloud compute disks list --filter="name~${VOLUME_PATTERN}" --format='value(name)' | head -1)" \
        --snapshot-names="$NAME" \
        --description="GULA Platform auto-snapshot $(date)" 2>/dev/null || {
        aws ec2 create-snapshot \
            --volume-id "$(aws ec2 describe-volumes --filters "Name=tag:Name,Values=gula-*" --query 'Volumes[0].VolumeId' --output text)" \
            --description "GULA Platform auto-snapshot $(date)" 2>/dev/null || log "No cloud provider detected — using local snapshot"
            mkdir -p /app/snapshots
            tar czf "/app/snapshots/${NAME}.tar.gz" /app/data /app/backups
    }
    log "Snapshot created: $NAME"
}

list_snapshots() {
    log "Listing snapshots..."
    gcloud compute snapshots list --filter="name~${SNAPSHOT_PREFIX}" --format="table(name,creationTimestamp,status,sourceDisk)" 2>/dev/null ||
    aws ec2 describe-snapshots --filters "Name=description,Values=GULA*" --query 'Snapshots[*].[SnapshotId,StartTime,State,VolumeId]' --output table 2>/dev/null ||
    ls -lt /app/snapshots/ 2>/dev/null
}

restore_snapshot() {
    local SNAPSHOT_NAME="${1:-latest}"
    log "Restoring snapshot: $SNAPSHOT_NAME"
    if [ -f "/app/snapshots/${SNAPSHOT_NAME}.tar.gz" ]; then
        tar xzf "/app/snapshots/${SNAPSHOT_NAME}.tar.gz" -C /tmp/restore
        log "Restored to /tmp/restore"
    else
        log "Snapshot not found locally — attempting cloud restore not implemented"
    fi
}

delete_old_snapshots() {
    log "Deleting snapshots older than ${RETENTION_DAYS}d..."
    gcloud compute snapshots list --filter="name~${SNAPSHOT_PREFIX} AND creationTimestamp<$(date -d "-${RETENTION_DAYS} days" -I)" --format='value(name)' | while read snap; do
        gcloud compute snapshots delete "$snap" --quiet
        log "Deleted old snapshot: $snap"
    done 2>/dev/null || true
    find /app/snapshots -name "${SNAPSHOT_PREFIX}-*.tar.gz" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
}

case "${1:-create}" in
    create) create_snapshot ;;
    list) list_snapshots ;;
    restore) restore_snapshot "${2:-latest}" ;;
    cleanup) delete_old_snapshots ;;
    *) echo "Usage: $0 {create|list|restore|cleanup}" ;;
esac
