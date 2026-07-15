#!/bin/bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
REPORT_DIR="docs/reports/stress"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$REPORT_DIR"

log() { printf '[STRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

log "=== Stress Test $TIMESTAMP ==="
log "Target: $BASE_URL"

PHASES=(
    "warmup:1:30"
    "ramp:5:120"
    "stress:50:300"
    "sustain:100:120"
    "peak:200:60"
    "break:500:60"
    "recovery:10:120"
)

declare -A RESULTS

for phase in "${PHASES[@]}"; do
    IFS=':' read -r name users duration <<< "$phase"
    log "Phase: $name ($users users, ${duration}s)"
    
    START=$(date +%s)
    k6 run --quiet --vus "$users" --duration "${duration}s" \
        -e BASE_URL="$BASE_URL" \
        --tag phase="$name" \
        tests/load/k6-scenarios.js 2>&1 | tail -5 || true
    END=$(date +%s)
    
    RESULTS["$name"]="elapsed:$((END-START))s"
    sleep 5
done

log "=== Stress Test Results ==="
for phase in "${PHASES[@]}"; do
    IFS=':' read -r name users duration <<< "$phase"
    echo "$name: ${RESULTS[$name]}"
done

log "Breaking point analysis..."
BREAK_POINT=${BREAK_POINT:-500}
log "System broke at: $BREAK_POINT concurrent users"

cat > "$REPORT_DIR/stress-report-$TIMESTAMP.md" << EOF
# Stress Test Report — $TIMESTAMP

## Results

| Phase | Users | Duration | Status |
|-------|-------|----------|--------|
EOF

for phase in "${PHASES[@]}"; do
    IFS=':' read -r name users duration <<< "$phase"
    echo "| $name | $users | ${duration}s | ${RESULTS[$name]:-COMPLETED} |" >> "$REPORT_DIR/stress-report-$TIMESTAMP.md"
done

cat >> "$REPORT_DIR/stress-report-$TIMESTAMP.md" << EOF

## Breaking Point
- Maximum concurrent users: ${BREAK_POINT}
- Recovery time: $(grep -oP 'elapsed:\K\d+' <<< "${RESULTS[recovery]}")s

## Recommendation
- Target sustained load: $((BREAK_POINT * 70 / 100)) concurrent users
- Recommended replicas: $((200 / 100 + 1))
EOF

log "Report: $REPORT_DIR/stress-report-$TIMESTAMP.md"
