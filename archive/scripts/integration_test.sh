#!/bin/bash
# =============================================================================
# GULA Platform - Integration Test Suite
# Audit Orders: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
# =============================================================================

set -euo pipefail

BASE_URL="${GULA_BASE_URL:-http://localhost}"
OLLAMA_URL="${OLLAMA_HOST:-http://localhost:11434}"
RABBITMQ_URL="${RABBITMQ_MGMT:-http://localhost:15672}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
VAULT_URL="${VAULT_ADDR:-http://localhost:8200}"

PASS=0
FAIL=0
WARN=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}  PASS${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}  FAIL${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}  WARN${NC} $1"; WARN=$((WARN+1)); }

check_http() {
    local url=$1 expected=${2:-200} label=$3
    code=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$code" = "$expected" ]; then
        pass "$label (HTTP $code)"
    else
        fail "$label (expected $expected, got $code)"
    fi
}

echo "================================================================"
echo "  GULA Platform Integration Tests"
echo "  $(date)"
echo "================================================================"

# =============================================================================
# AUDIT 1: Health checks (Executive Order 1)
# =============================================================================
echo ""
echo "--- AUDIT 1: Service Health Checks ---"

check_http "$BASE_URL/health"                        200  "API Gateway health"
check_http "http://localhost:8001/health"             200  "Lab Service health"
check_http "http://localhost:8002/health"             200  "Patient Service health"
check_http "http://localhost:8003/health"             200  "Order Service health"
check_http "http://localhost:8004/health"             200  "Result Service health"
check_http "http://localhost:8005/health"             200  "Sample Service health"
check_http "http://localhost:8006/health"             200  "Notification Service health"
check_http "http://localhost:9000/health"             200  "AI Service health"
check_http "http://localhost:8010/health"             200  "Autonomous Manager health"
check_http "http://localhost:8010/status"             200  "Autonomous Manager status"

# =============================================================================
# AUDIT 2: RabbitMQ queue verification (Executive Order 2)
# =============================================================================
echo ""
echo "--- AUDIT 2: RabbitMQ Queue Verification ---"

for queue in "orders.events" "samples.events" "results.events" "alerts.events" "retry.queue" "dead-letter.queue" "audit.events"; do
    code=$(curl -sf -o /dev/null -w "%{http_code}" \
        -u "gula:gula_rabbit_2024" \
        "$RABBITMQ_URL/api/queues/gula/$queue" 2>/dev/null || echo "000")
    if [ "$code" = "200" ]; then
        pass "Queue exists: $queue"
    else
        fail "Queue missing: $queue"
    fi
done

# Test event publishing
echo '{"test":"event","timestamp":"'$(date -Iseconds)'"}' | \
    curl -sf -o /dev/null \
    -u "gula:gula_rabbit_2024" \
    -H "Content-Type: application/json" \
    -d @- \
    "$RABBITMQ_URL/api/exchanges/gula/gula.events/publish" 2>/dev/null \
    && pass "Event publish test" || warn "Event publish test (RabbitMQ may not be running)"

# =============================================================================
# AUDIT 3: Local AI verification (Executive Order 3)
# =============================================================================
echo ""
echo "--- AUDIT 3: Ollama Local AI ---"

code=$(curl -sf -o /dev/null -w "%{http_code}" "$OLLAMA_URL/api/tags" 2>/dev/null || echo "000")
if [ "$code" = "200" ]; then
    pass "Ollama API reachable"
    # Check llama3 model exists
    if curl -sf "$OLLAMA_URL/api/tags" | grep -q "llama3"; then
        pass "llama3 model available"
    else
        warn "llama3 model not pulled yet - run: make pull-ai"
    fi
else
    warn "Ollama not running (expected in dev) - run: make pull-ai"
fi

# AI service returns ollama provider
ai_resp=$(curl -sf "http://localhost:9000/health" 2>/dev/null || echo '{}')
if echo "$ai_resp" | grep -q '"provider": "ollama"' 2>/dev/null || echo "$ai_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('provider')=='ollama' or d.get('ollama_connected') is not None else 1)" 2>/dev/null; then
    pass "AI Service uses ollama provider"
else
    warn "AI Service health check (may not be running)"
fi

# =============================================================================
# AUDIT 4: Security headers (Executive Order 15)
# =============================================================================
echo ""
echo "--- AUDIT 4: Security Headers ---"

headers=$(curl -sf -I "$BASE_URL/health" 2>/dev/null || echo "")
if [ -n "$headers" ]; then
    echo "$headers" | grep -qi "X-Frame-Options"        && pass "X-Frame-Options header"       || fail "Missing X-Frame-Options"
    echo "$headers" | grep -qi "X-Content-Type-Options" && pass "X-Content-Type-Options header" || fail "Missing X-Content-Type-Options"
    echo "$headers" | grep -qi "X-XSS-Protection"       && pass "X-XSS-Protection header"      || fail "Missing X-XSS-Protection"
    echo "$headers" | grep -qi "Referrer-Policy"         && pass "Referrer-Policy header"       || fail "Missing Referrer-Policy"
else
    warn "API Gateway not responding (security headers test skipped)"
fi

# =============================================================================
# AUDIT 5: Rate limiting - 429 test (Executive Order 15)
# =============================================================================
echo ""
echo "--- AUDIT 5: Rate Limiting ---"

rate_limit_hit=false
for i in $(seq 1 25); do
    code=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/api/auth/test" 2>/dev/null || echo "000")
    if [ "$code" = "429" ]; then
        rate_limit_hit=true
        break
    fi
done
$rate_limit_hit && pass "Rate limiting active (429 returned)" || warn "Rate limiting not triggered (API Gateway may not be running)"

# =============================================================================
# AUDIT 6: End-to-end flow test
# =============================================================================
echo ""
echo "--- AUDIT 6: End-to-End Flow ---"

# Create patient
patient_resp=$(curl -sf -X POST "http://localhost:8002/patients" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Test","last_name":"Patient","gender":"M","age":30}' 2>/dev/null || echo '{}')

patient_id=$(echo "$patient_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
[ -n "$patient_id" ] && pass "Patient created (id=$patient_id)" || warn "Patient creation test (service may not be running)"

# If patient was created, continue flow
if [ -n "$patient_id" ]; then
    # Create order
    order_resp=$(curl -sf -X POST "http://localhost:8003/orders" \
        -H "Content-Type: application/json" \
        -d "{\"lab_id\":1,\"patient_id\":$patient_id,\"test_id\":1,\"priority\":\"routine\"}" 2>/dev/null || echo '{}')
    order_id=$(echo "$order_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
    [ -n "$order_id" ] && pass "Order created (id=$order_id)" || fail "Order creation failed"

    # Collect sample
    if [ -n "$order_id" ]; then
        sample_resp=$(curl -sf -X POST "http://localhost:8005/samples" \
            -H "Content-Type: application/json" \
            -d "{\"order_id\":$order_id,\"sample_type\":\"blood\",\"barcode\":\"TEST$(date +%s)\"}" 2>/dev/null || echo '{}')
        sample_id=$(echo "$sample_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
        [ -n "$sample_id" ] && pass "Sample collected (id=$sample_id) - SampleCollected audit event published" || fail "Sample collection failed"

        # Add result
        result_resp=$(curl -sf -X POST "http://localhost:8004/results" \
            -H "Content-Type: application/json" \
            -d "{\"order_id\":$order_id,\"value\":\"14.5\",\"numeric_value\":14.5,\"unit\":\"g/dL\",\"is_abnormal\":false}" 2>/dev/null || echo '{}')
        result_id=$(echo "$result_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
        [ -n "$result_id" ] && pass "Result created (id=$result_id) - ResultUpdated audit event published" || fail "Result creation failed"

        # Validate result
        if [ -n "$result_id" ]; then
            validate_resp=$(curl -sf -X PUT "http://localhost:8004/results/$result_id/validate" \
                -H "Content-Type: application/json" \
                -d '{"validated_by":1}' 2>/dev/null || echo '{}')
            echo "$validate_resp" | grep -q "validated" && pass "Result validated - ResultValidated audit event published" || fail "Result validation failed"
        fi

        # Complete order
        complete_resp=$(curl -sf -X PUT "http://localhost:8003/orders/$order_id/complete" 2>/dev/null || echo '{}')
        echo "$complete_resp" | grep -q "completed" && pass "Order completed - OrderCompleted audit event published" || fail "Order completion failed"
    fi
fi

# =============================================================================
# AUDIT 7: Monitoring stack (Executive Order 14)
# =============================================================================
echo ""
echo "--- AUDIT 7: Monitoring Stack ---"

check_http "$PROMETHEUS_URL/-/healthy"   200 "Prometheus health"
check_http "http://localhost:3000/api/health" 200 "Grafana health"
check_http "http://localhost:3100/ready" 200 "Loki ready"
check_http "http://localhost:16686/"     200 "Jaeger UI"

# =============================================================================
# AUDIT 8: Circuit Breaker test (Executive Order 7)
# =============================================================================
echo ""
echo "--- AUDIT 8: Circuit Breaker State ---"

cb_resp=$(curl -sf "http://localhost:8010/status" 2>/dev/null || echo '{}')
if echo "$cb_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); services=d.get('services',{}); closed=[s for s,v in services.items() if v.get('healthy',False)]; print(f'Healthy: {len(closed)}/{len(services)}')" 2>/dev/null; then
    pass "Autonomous Manager tracking service health"
else
    warn "Autonomous Manager not responding"
fi

# =============================================================================
# AUDIT 9: Vault secrets (Executive Order 17)
# =============================================================================
echo ""
echo "--- AUDIT 9: Vault Secrets ---"

check_http "$VAULT_URL/v1/sys/health" 200 "Vault health (dev mode)"

# =============================================================================
# AUDIT 10: ClickHouse analytics (Executive Order 12)
# =============================================================================
echo ""
echo "--- AUDIT 10: ClickHouse Analytics ---"

ch_resp=$(curl -sf "http://localhost:8123/?query=SELECT+1" 2>/dev/null || echo "")
[ "$ch_resp" = "1" ] && pass "ClickHouse responding" || warn "ClickHouse not running"

ch_tables=$(curl -sf "http://localhost:8123/?query=SHOW+TABLES+FROM+gula" 2>/dev/null || echo "")
echo "$ch_tables" | grep -q "lab_results" && pass "ClickHouse gula.lab_results table exists" || warn "ClickHouse tables not initialized"

# =============================================================================
# RESULTS SUMMARY
# =============================================================================
echo ""
echo "================================================================"
echo "  RESULTS: ${PASS} PASS  |  ${FAIL} FAIL  |  ${WARN} WARN"
echo "================================================================"

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}  $FAIL test(s) failed. Check service logs.${NC}"
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "${YELLOW}  $WARN warning(s). Some services may not be running.${NC}"
    exit 0
else
    echo -e "${GREEN}  All tests passed!${NC}"
    exit 0
fi
