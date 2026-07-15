#!/bin/bash
set -euo pipefail

NAMESPACE="gula"
TEST_DATE=$(date +%Y%m%d-%H%M%S)
LOG_FILE="/tmp/dr-test-$TEST_DATE.log"
REPORT_FILE="docs/reports/dr-test-$TEST_DATE.md"

log() { printf '[DR-TEST] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG_FILE"; }

log "=== DR Test $TEST_DATE ==="
log "Pre-test health check..."
HEALTH_BEFORE=$(curl -sf --max-time 10 http://localhost:8080/health/deep 2>/dev/null || echo '{"status":"unreachable"}')
log "Pre-test health: $(echo "$HEALTH_BEFORE" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("grade","UNKNOWN"))')"

START_TIME=$(date +%s)

log "Simulating primary region failure..."
kubectl scale deployment gula-backend -n "$NAMESPACE" --replicas=0
sleep 5

log "Triggering failover..."
bash scripts/dr-failover.sh 2>&1 | tee -a "$LOG_FILE" || true
FAILOVER_TIME=$(($(date +%s) - START_TIME))

log "Measuring recovery..."
RECOVERY_START=$(date +%s)
for i in $(seq 1 60); do
    HEALTH=$(curl -sf --max-time 10 http://localhost:8080/health 2>/dev/null || echo "")
    if [ -n "$HEALTH" ]; then
        RECOVERY_TIME=$(($(date +%s) - RECOVERY_START))
        log "Recovery complete in ${RECOVERY_TIME}s"
        break
    fi
    sleep 5
done

log "Verifying data integrity..."
INTEGRITY=$(python3 -c "
from backend.app.database import SessionLocal
from backend.app.models import Patient, LabOrder, LabResult
db = SessionLocal()
try:
    patients = db.query(Patient).count()
    orders = db.query(LabOrder).count()
    results = db.query(LabResult).count()
    print(f'Patients: {patients}, Orders: {orders}, Results: {results}')
finally:
    db.close()
" 2>/dev/null || echo "INTEGRITY_CHECK_FAILED")

log "Data integrity: $INTEGRITY"

log "Restoring services..."
kubectl scale deployment gula-backend -n "$NAMESPACE" --replicas=2

sleep 10
HEALTH_AFTER=$(curl -sf --max-time 10 http://localhost:8080/health/deep 2>/dev/null || echo '{"status":"unreachable"}')
log "Post-test health: $(echo "$HEALTH_AFTER" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("grade","UNKNOWN"))')"

cat > "$REPORT_FILE" << EOF
# DR Test Report — $TEST_DATE

## Results

| Metric | Value |
|--------|-------|
| Failover time | ${FAILOVER_TIME}s |
| Recovery time | ${RECOVERY_TIME:-TIMEOUT}s |
| Data integrity | ${INTEGRITY} |
| Pre-test health | $(echo "$HEALTH_BEFORE" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("grade","UNKNOWN"))') |
| Post-test health | $(echo "$HEALTH_AFTER" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("grade","UNKNOWN"))') |

## Verdict

**$([ ${RECOVERY_TIME:-300} -lt 300 ] && echo "PASS" || echo "FAIL")** — RTO target: 5 minutes
EOF

log "DR test complete. Report: $REPORT_FILE"
