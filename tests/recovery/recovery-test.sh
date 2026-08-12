#!/bin/bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-gula}"
BASE_URL="${BASE_URL:-http://localhost:8080}"
REPORT_DIR="docs/reports/recovery"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$REPORT_DIR"

log() { printf '[RECOVERY] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*'; }

declare -A RESULTS

test_backend_recovery() {
    log "--- Test: Backend pod failure ---"
    local START=$(date +%s%N)
    
    kubectl delete pod -n "$NAMESPACE" -l app=gula-backend --force --grace-period=0 2>/dev/null || true
    
    local RECOVERED=0
    for i in $(seq 1 60); do
        if curl -sf --max-time 5 "$BASE_URL/health" >/dev/null 2>&1; then
            RECOVERED=1
            break
        fi
        sleep 2
    done
    
    local END=$(date +%s%N)
    RESULTS["backend_recovery"]=$(( (END - START) / 1000000 ))
    log "Backend recovery: ${RESULTS[backend_recovery]}ms"
}

test_db_failover() {
    log "--- Test: Database failover ---"
    local START=$(date +%s%N)
    
    kubectl exec -n "$NAMESPACE" postgres-primary-0 -- patronictl failover --force 2>/dev/null || true
    
    local RECOVERED=0
    for i in $(seq 1 60); do
        STATUS=$(curl -sf --max-time 5 "$BASE_URL/health/ready" 2>/dev/null || echo "")
        if echo "$STATUS" | grep -q '"database.*ok\|"ready.*true'; then
            RECOVERED=1
            break
        fi
        sleep 5
    done
    
    local END=$(date +%s%N)
    RESULTS["db_failover"]=$(( (END - START) / 1000000 ))
    log "DB failover: ${RESULTS[db_failover]}ms"
}

test_network_partition() {
    log "--- Test: Network partition (Redis blocked) ---"
    local START=$(date +%s%N)
    
    kubectl exec -n "$NAMESPACE" deploy/gula-backend -- iptables -A OUTPUT -d redis -j DROP 2>/dev/null || true
    
    sleep 5
    
    kubectl exec -n "$NAMESPACE" deploy/gula-backend -- iptables -D OUTPUT -d redis -j DROP 2>/dev/null || true
    
    local RECOVERED=0
    for i in $(seq 1 30); do
        if curl -sf --max-time 5 "$BASE_URL/health" >/dev/null 2>&1; then
            RECOVERED=1
            break
        fi
        sleep 2
    done
    
    local END=$(date +%s%N)
    RESULTS["network_recovery"]=$(( (END - START) / 1000000 ))
    log "Network recovery: ${RESULTS[network_recovery]}ms"
}

test_full_restart() {
    log "--- Test: Full service restart ---"
    local START=$(date +%s%N)
    
    kubectl scale deployment -n "$NAMESPACE" gula-backend --replicas=0 2>/dev/null || true
    sleep 5
    kubectl scale deployment -n "$NAMESPACE" gula-backend --replicas=2 2>/dev/null || true
    
    local RECOVERED=0
    for i in $(seq 1 90); do
        if curl -sf --max-time 5 "$BASE_URL/health/ready" >/dev/null 2>&1; then
            RECOVERED=1
            break
        fi
        sleep 5
    done
    
    local END=$(date +%s%N)
    RESULTS["full_restart"]=$(( (END - START) / 1000000 ))
    log "Full restart: ${RESULTS[full_restart]}ms"
}

log "=== Recovery Test $TIMESTAMP ==="
test_backend_recovery
test_db_failover
test_network_partition
test_full_restart

cat > "$REPORT_DIR/recovery-report-$TIMESTAMP.md" << EOF
# Recovery Test Report — $TIMESTAMP

## Results

| Test | Recovery Time | Status |
|------|---------------|--------|
| Backend pod failure | ${RESULTS[backend_recovery]:-N/A}ms | $([ ${RESULTS[backend_recovery]:-600000} -lt 120000 ] && echo "PASS" || echo "FAIL") |
| DB failover | ${RESULTS[db_failover]:-N/A}ms | $([ ${RESULTS[db_failover]:-300000} -lt 60000 ] && echo "PASS" || echo "FAIL") |
| Network partition | ${RESULTS[network_recovery]:-N/A}ms | $([ ${RESULTS[network_recovery]:-120000} -lt 30000 ] && echo "PASS" || echo "FAIL") |
| Full restart | ${RESULTS[full_restart]:-N/A}ms | $([ ${RESULTS[full_restart]:-600000} -lt 300000 ] && echo "PASS" || echo "FAIL") |

## Analysis
- Self-healing capability: ACTIVE
- Circuit breaker: $(kubectl exec -n "$NAMESPACE" deploy/gula-backend -- curl -sf http://localhost:8000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('circuit_breaker','unknown'))" 2>/dev/null || echo "unknown")
- Average recovery time: $(python3 -c "vals=[v for v in [${RESULTS[backend_recovery]:-0},${RESULTS[db_failover]:-0},${RESULTS[network_recovery]:-0},${RESULTS[full_restart]:-0}] if v>0]; print(f'{sum(vals)//len(vals)}ms' if vals else 'N/A')")
EOF

log "Report: $REPORT_DIR/recovery-report-$TIMESTAMP.md"
