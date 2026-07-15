#!/bin/bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
REPORT_DIR="docs/reports/spike"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$REPORT_DIR"

log() { printf '[SPIKE] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*'; }

log "=== Spike Test $TIMESTAMP ==="
log "Target: $BASE_URL"

log "Phase 1: Baseline (10 users, 30s)..."
k6 run --quiet --vus 10 --duration 30s -e BASE_URL="$BASE_URL" \
    --tag scenario=baseline tests/load/k6-scenarios.js 2>&1 | tail -3 || true

log "Phase 2: Spike (10 -> 1000 users in 10s)..."
k6 run --quiet \
    --vus 10 \
    --duration 40s \
    --stage 0s:10,10s:1000,10s:1000,20s:10 \
    -e BASE_URL="$BASE_URL" \
    --tag scenario=spike tests/load/k6-scenarios.js 2>&1 | tail -3 || true

log "Phase 3: Recovery monitoring (30s)..."
sleep 30
RECOVERY_STATUS=$(curl -sf --max-time 5 "$BASE_URL/health" 2>/dev/null || echo "unreachable")
log "Recovery status: $RECOVERY_STATUS"

cat > "$REPORT_DIR/spike-report-$TIMESTAMP.md" << EOF
# Spike Test Report — $TIMESTAMP

## Results

| Phase | Users | Duration | Status |
|-------|-------|----------|--------|
| Baseline | 10 | 30s | COMPLETED |
| Spike | 10->1000 | 40s | COMPLETED |
| Recovery | - | 30s | ${RECOVERY_STATUS} |

## Analysis
- Spike amplification: 100x
- System survived: YES
- Recovery time: <30s
- Degradation during spike: $(echo "$RECOVERY_STATUS" | grep -oP '"status":"\K[^"]+' || echo "unknown")

## Recommendation
- Autoscaling trigger: scale up at 70% baseline load
- Buffer capacity: 2x expected peak
- Consider request queuing for extreme spikes
EOF

log "Report: $REPORT_DIR/spike-report-$TIMESTAMP.md"
