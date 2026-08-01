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
        mkdir -p /tmp/restore
        tar xzf "/app/snapshots/${SNAPSHOT_NAME}.tar.gz" -C /tmp/restore
        log "Restored to /tmp/restore"
        return 0
    fi

    # ── Cloud restore (non-destructive: never touches the source volume) ──
    # GCP: create a fresh disk from the snapshot, then (optionally) attach it
    # to an instance when SNAPSHOT_ATTACH_INSTANCE is set. The original disk
    # is never deleted or modified; the operator picks up the new disk id.
    if command -v gcloud >/dev/null 2>&1 \
        && gcloud compute snapshots describe "${SNAPSHOT_NAME}" >/dev/null 2>&1; then
        local DISK_NAME="gula-restored-$(date +%Y%m%d-%H%M%S)"
        local ZONE="${SNAPSHOT_ZONE:-$(gcloud config get-value compute/zone 2>/dev/null || echo us-central1-a)}"
        log "Creating disk ${DISK_NAME} from GCP snapshot ${SNAPSHOT_NAME}..."
        gcloud compute disks create "${DISK_NAME}" \
            --source-snapshot="${SNAPSHOT_NAME}" \
            --zone="${ZONE}"
        log "GCP disk created: ${DISK_NAME}"
        if [ -n "${SNAPSHOT_ATTACH_INSTANCE:-}" ]; then
            gcloud compute instances attach-disk "${SNAPSHOT_ATTACH_INSTANCE}" \
                --disk="${DISK_NAME}" --zone="${ZONE}"
            log "Attached ${DISK_NAME} to ${SNAPSHOT_ATTACH_INSTANCE}"
        else
            log "Attach manually: gcloud compute instances attach-disk <INSTANCE> --disk=${DISK_NAME}"
        fi
        return 0
    fi

    # AWS: create a fresh EBS volume from the snapshot (same AZ as the
    # source instance when SNAPSHOT_AZ is set, else the instance's AZ).
    if command -v aws >/dev/null 2>&1 \
        && aws ec2 describe-snapshots --snapshot-ids "${SNAPSHOT_NAME}" >/dev/null 2>&1; then
        local AZ="${SNAPSHOT_AZ:-$(aws ec2 describe-availability-zones --query 'AvailabilityZones[0].ZoneName' --output text)}"
        local VOL_ID
        VOL_ID=$(aws ec2 create-volume \
            --snapshot-id "${SNAPSHOT_NAME}" \
            --availability-zone "${AZ}" \
            --query 'VolumeId' --output text)
        log "AWS volume created: ${VOL_ID} (AZ ${AZ})"
        log "Attach manually: aws ec2 attach-volume --volume-id ${VOL_ID} --instance-id <INSTANCE> --device /dev/sdf"
        return 0
    fi

    log "Snapshot not found locally and no cloud provider match — nothing restored"
    return 1
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
