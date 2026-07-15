#!/bin/bash
set -euo pipefail

REGION_PRIMARY="me-central1"
REGION_DR="eu-west1"
NAMESPACE="gula"
CLOUDFLARE_ZONE_ID="${CF_ZONE_ID}"
DR_HEALTH_URL="https://dr.gula.health/health"
PRIMARY_HEALTH_URL="https://api.gula.health/health"
WEBHOOK_URL="${ALERT_WEBHOOK_URL}"

log() { printf '[DR-FAILOVER] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

notify() { log "$*"; curl -sf -X POST -H "Content-Type: application/json" -d "{\"text\":\"[DR-FAILOVER] $*\"}" "$WEBHOOK_URL" 2>/dev/null || true; }

log "Starting DR failover: $REGION_PRIMARY -> $REGION_DR"

log "Step 1: Checking primary region health..."
if curl -sf --max-time 10 "$PRIMARY_HEALTH_URL" >/dev/null 2>&1; then
    log "Primary region still healthy. Aborting failover."
    notify "Primary region healthy — failover aborted"
    exit 1
fi
log "Primary region confirmed down."

log "Step 2: Promoting DR PostgreSQL to primary..."
kubectl exec -n "$NAMESPACE" postgres-dr-0 -- patronictl failover --candidate postgres-dr-0 --force
sleep 10
kubectl exec -n "$NAMESPACE" postgres-dr-0 -- pg_isready -U postgres
log "DR PostgreSQL promoted to primary."

log "Step 3: Activating DR Redis..."
kubectl patch svc redis -n "$NAMESPACE" --type=json -p '[{"op":"replace","path":"/spec/selector/role","value":"dr"}]'
notify "DR Redis activated"

log "Step 4: Activating DR MinIO..."
kubectl exec -n "$NAMESPACE" minio-dr-0 -- mc admin promote minio-dr
notify "DR MinIO activated"

log "Step 5: Switching RabbitMQ upstream..."
kubectl exec -n "$NAMESPACE" rabbitmq-dr-0 -- rabbitmqctl set_cluster_name gula-dr
notify "DR RabbitMQ activated"

log "Step 6: Updating DNS to DR region..."
if [ -n "$CLOUDFLARE_ZONE_ID" ] && [ -n "${CF_API_TOKEN:-}" ]; then
    curl -sf -X PATCH "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"content":"'"$DR_IP"'","name":"api.gula.health","type":"A","proxied":true}'
    log "DNS updated to DR region."
fi

log "Step 7: Verifying DR health..."
for i in $(seq 1 30); do
    if curl -sf --max-time 10 "$DR_HEALTH_URL" >/dev/null 2>&1; then
        log "DR region healthy after failover."
        notify "DR failover complete — DR region active"
        exit 0
    fi
    sleep 10
done

log "ERROR: DR health check failed after failover."
notify "DR failover FAILED — manual intervention required"
exit 1
