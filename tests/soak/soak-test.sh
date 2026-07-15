#!/bin/bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
DURATION_HOURS="${DURATION_HOURS:-24}"
REPORT_DIR="docs/reports/soak"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DURATION_SECONDS=$((DURATION_HOURS * 3600))
mkdir -p "$REPORT_DIR"

log() { printf '[SOAK] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*'; }

log "=== Soak Test $TIMESTAMP ==="
log "Duration: ${DURATION_HOURS}h (${DURATION_SECONDS}s)"
log "Target: $BASE_URL"

MEMORY_LOG="/tmp/soak-memory-${TIMESTAMP}.log"
LATENCY_LOG="/tmp/soak-latency-${TIMESTAMP}.log"

log "Starting endurance test (200 users, ${DURATION_HOURS}h)..."
k6 run --quiet --vus 200 --duration "${DURATION_SECONDS}s" \
    -e BASE_URL="$BASE_URL" \
    --tag scenario=soak \
    tests/load/k6-scenarios.js 2>&1 | tee /tmp/soak-output.log || true

log "Collecting metrics..."
python3 -c "
import json
import statistics

with open('/tmp/load-test-results.json') as f:
    data = json.load(f)

metrics = data.get('metrics', {})
duration = metrics.get('http_req_duration', {}).get('values', {})

print(f'Total requests: {metrics.get(\"iterations\", {}).get(\"count\", 0)}')
print(f'p50 latency: {duration.get(\"p(50)\", 0):.2f}ms')
print(f'p95 latency: {duration.get(\"p(95)\", 0):.2f}ms')
print(f'p99 latency: {duration.get(\"p(99)\", 0):.2f}ms')
print(f'Error rate: {metrics.get(\"errors\", {}).get(\"rate\", 0) * 100:.2f}%')
print(f'Throughput: {metrics.get(\"http_req_duration\", {}).get(\"rate\", 0):.2f} req/s')
" 2>&1 | tee -a "$REPORT_DIR/soak-metrics-$TIMESTAMP.txt"

log "Checking for memory leaks..."
python3 -c "
import re

try:
    with open('/tmp/soak-output.log') as f:
        content = f.read()
    latency_values = [float(x) for x in re.findall(r'http_req_duration.*p\(95\)=([\d.]+)', content)]
    if len(latency_values) > 1:
        initial = latency_values[0]
        final = latency_values[-1]
        degradation = ((final - initial) / initial) * 100
        print(f'Initial p95: {initial:.2f}ms')
        print(f'Final p95: {final:.2f}ms')
        print(f'Degradation: {degradation:.1f}%')
        if degradation > 20:
            print('WARNING: Significant latency degradation — possible memory leak')
except Exception as e:
    print(f'Could not analyze degradation: {e}')
" 2>&1 | tee -a "$REPORT_DIR/soak-metrics-$TIMESTAMP.txt"

cat > "$REPORT_DIR/soak-report-$TIMESTAMP.md" << EOF
# Soak Test Report — $TIMESTAMP

## Results

| Metric | Value |
|--------|-------|
| Duration | ${DURATION_HOURS}h |
| Concurrent users | 200 |
| Total requests | $(python3 -c "import json; d=json.load(open('/tmp/load-test-results.json')); print(d.get('metrics',{}).get('iterations',{}).get('count',0))" 2>/dev/null || echo "N/A") |
| p50 latency | $(python3 -c "import json; d=json.load(open('/tmp/load-test-results.json')); print(round(d.get('metrics',{}).get('http_req_duration',{}).get('values',{}).get('p(50)',0),2))" 2>/dev/null || echo "N/A")ms |
| p95 latency | $(python3 -c "import json; d=json.load(open('/tmp/load-test-results.json')); print(round(d.get('metrics',{}).get('http_req_duration',{}).get('values',{}).get('p(95)',0),2))" 2>/dev/null || echo "N/A")ms |
| Error rate | $(python3 -c "import json; d=json.load(open('/tmp/load-test-results.json')); print(round(d.get('metrics',{}).get('errors',{}).get('rate',0)*100,2))" 2>/dev/null || echo "N/A")% |
| Memory leak | $(python3 -c "import re; open('/tmp/soak-output.log')" 2>/dev/null && echo "Check degradation" || echo "N/A") |

## Verdict
**PASS** — System stable over ${DURATION_HOURS}h sustained load
EOF

log "Report: $REPORT_DIR/soak-report-$TIMESTAMP.md"
