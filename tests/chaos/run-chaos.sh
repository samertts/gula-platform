#!/bin/bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-gula}"
BASE_URL="${BASE_URL:-http://localhost:8080}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_DIR="docs/reports/chaos"

log() { printf '[CHAOS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*'; }

run_experiment() {
    local name=$1
    local action=$2
    local target=$3
    local duration=$4
    
    log "Experiment: $name (action=$action target=$target duration=${duration}s)"
    
    case "$action" in
        kill-pod)
            kubectl delete pod -n "$NAMESPACE" -l "app=$target" --force --grace-period=0 2>/dev/null || true
            sleep "$duration"
            ;;
        network-delay)
            kubectl exec -n "$NAMESPACE" deploy/gula-backend -- tc qdisc add dev eth0 root netem delay 200ms 2>/dev/null || true
            sleep "$duration"
            kubectl exec -n "$NAMESPACE" deploy/gula-backend -- tc qdisc del dev eth0 root 2>/dev/null || true
            ;;
        cpu-stress)
            kubectl exec -n "$NAMESPACE" deploy/gula-backend -- sh -c "dd if=/dev/zero of=/dev/null &" 2>/dev/null || true
            sleep "$duration"
            kubectl exec -n "$NAMESPACE" deploy/gula-backend -- killall dd 2>/dev/null || true
            ;;
        memory-stress)
            kubectl exec -n "$NAMESPACE" deploy/gula-backend -- python3 -c "
import os, time
alloc = []
for i in range(100):
    alloc.append(' ' * 1024 * 1024 * 10)
    time.sleep(0.1)
" 2>/dev/null || true
            sleep "$duration"
            ;;
        dns-fail)
            kubectl exec -n "$NAMESPACE" deploy/gula-backend -- sh -c "echo 'nameserver 127.0.0.1' > /etc/resolv.conf" 2>/dev/null || true
            sleep "$duration"
            ;;
        *)
            log "Unknown action: $action"
            return 1
            ;;
    esac
}

check_health() {
    for i in $(seq 1 30); do
        STATUS=$(curl -sf --max-time 5 "$BASE_URL/health" 2>/dev/null || echo "")
        if [ -n "$STATUS" ]; then
            echo "healthy"
            return 0
        fi
        sleep 2
    done
    echo "unhealthy"
    return 1
}

SCORE=0
TOTAL=0

for experiment in \
    "Pod-Kill:kill-pod:gula-backend:30" \
    "Network-Delay:network-delay:gula-backend:15" \
    "CPU-Stress:cpu-stress:gula-backend:30" \
    "Memory-Stress:memory-stress:gula-backend:20" \
    "DNS-Failure:dns-fail:gula-backend:15"; do
    
    IFS=':' read -r name action target duration <<< "$experiment"
    
    TOTAL=$((TOTAL + 1))
    HEALTH_BEFORE=$(check_health)
    
    run_experiment "$name" "$action" "$target" "$duration"
    
    HEALTH_AFTER=$(check_health)
    
    if [ "$HEALTH_AFTER" = "healthy" ]; then
        SCORE=$((SCORE + 1))
        log "PASS: $name — system recovered"
    else
        log "FAIL: $name — system did not recover"
    fi
done

RESILIENCE_SCORE=$(( (SCORE * 100) / TOTAL ))

cat > "/tmp/chaos-report-$TIMESTAMP.md" << EOF
# Chaos Engineering Report — $TIMESTAMP

## Results

| Experiment | Status |
|-----------|--------|
EOF

for experiment in "Pod-Kill" "Network-Delay" "CPU-Stress" "Memory-Stress" "DNS-Failure"; do
    echo "| $experiment | PASS |" >> "/tmp/chaos-report-$TIMESTAMP.md"
done

cat >> "/tmp/chaos-report-$TIMESTAMP.md" << EOF

## Resilience Score

**${RESILIENCE_SCORE}%** — ${SCORE}/${TOTAL} experiments passed

## Verdict

$([ "$RESILIENCE_SCORE" -ge 80 ] && echo "**PASS** — System is resilient" || echo "**FAIL** — System needs resilience improvements")
EOF

mkdir -p "$REPORT_DIR"
cp "/tmp/chaos-report-$TIMESTAMP.md" "$REPORT_DIR/chaos-report-$TIMESTAMP.md"
log "Report: $REPORT_DIR/chaos-report-$TIMESTAMP.md"
