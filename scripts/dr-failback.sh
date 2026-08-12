#!/bin/bash
set -euo pipefail

REGION_PRIMARY="me-central1"
REGION_DR="eu-west1"
NAMESPACE="gula"
CLOUDFLARE_ZONE_ID="${CF_ZONE_ID}"
PRIMARY_HEALTH_URL="https://api.gula.health/health"
WEBHOOK_URL="${ALERT_WEBHOOK_URL}"

log() { printf '[DR-FAILBACK] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }
notify() { log "$*"; curl -sf -X POST -H "Content-Type: application/json" -d "{\"text\":\"[DR-FAILBACK] $*\"}" "$WEBHOOK_URL" 2>/dev/null || true; }

log "Starting DR failback: $REGION_DR -> $REGION_PRIMARY"

log "Step 1: Verifying primary region recovered..."
if ! curl -sf --max-time 10 "$PRIMARY_HEALTH_URL" >/dev/null 2>&1; then
    log "Primary region not healthy. Aborting failback."
    notify "DR failback aborted — primary region not healthy"
    exit 1
fi
log "Primary region confirmed healthy."

log "Step 2: Syncing data from DR to primary..."
kubectl exec -n "$NAMESPACE" postgres-0 -- pg_basebackup -h postgres-dr -D /var/lib/postgresql/data -P -U replicator --wal-method=stream
log "Data sync complete."

log "Step 3: Reversing replication direction..."
kubectl exec -n "$NAMESPACE" postgres-dr-0 -- patronictl switchover --force
sleep 10
log "Replication reversed."

log "Step 4: Switching DNS back to primary..."
if [ -n "$CLOUDFLARE_ZONE_ID" ] && [ -n "${CF_API_TOKEN:-}" ]; then
    curl -sf -X PATCH "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"content":"'"$PRIMARY_IP"'","name":"api.gula.health","type":"A","proxied":true}'
    log "DNS switched back to primary region."
fi

log "Step 5: Verifying primary health..."
for i in $(seq 1 30); do
    if curl -sf --max-time 10 "$PRIMARY_HEALTH_URL" >/dev/null 2>&1; then
        log "Primary region healthy after failback."
        notify "DR failback complete — primary region active"
        exit 0
    fi
    sleep 10
done

log "ERROR: Primary health check failed after failback."
notify "DR failback FAILED — manual intervention required"
exit 1
