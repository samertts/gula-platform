#!/bin/bash
# =============================================================================
# GULA Platform — Full Integration Test Suite
# 10 checks covering: Auth · Patients · Orders · Results · Audit ·
#                     RabbitMQ · Redis · AI · Compliance · Security
# Usage: bash scripts/integration_test.sh [BASE_URL]
#   BASE_URL defaults to http://localhost
# =============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost}"
API="${BASE_URL}/api"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0; FAIL=0; WARN=0
RESULTS=()

pass() { echo -e "  ${GREEN}✓ PASS${NC}  $1"; PASS=$((PASS+1)); RESULTS+=("PASS: $1"); }
fail() { echo -e "  ${RED}✗ FAIL${NC}  $1"; FAIL=$((FAIL+1)); RESULTS+=("FAIL: $1"); }
warn() { echo -e "  ${YELLOW}⚠ WARN${NC}  $1"; WARN=$((WARN+1)); RESULTS+=("WARN: $1"); }
info() { echo -e "  ${BLUE}►${NC} $1"; }
header() { echo -e "\n${BOLD}━━━ CHECK $1 — $2 ━━━${NC}"; }

# ─── helpers ─────────────────────────────────────────────────────────────────

http_get() {
    curl -sf --max-time 10 \
        ${AUTH_HEADER:+-H "Authorization: Bearer ${AUTH_HEADER}"} \
        "$1" 2>/dev/null
}

http_post() {
    curl -sf --max-time 15 \
        -X POST \
        -H "Content-Type: application/json" \
        ${AUTH_HEADER:+-H "Authorization: Bearer ${AUTH_HEADER}"} \
        -d "${2:-{}}" \
        "$1" 2>/dev/null
}

http_status() {
    curl -so /dev/null -w "%{http_code}" --max-time 10 \
        ${AUTH_HEADER:+-H "Authorization: Bearer ${AUTH_HEADER}"} \
        "$1" 2>/dev/null || echo "000"
}

AUTH_HEADER=""

# ─── banner ──────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       GULA Platform — Integration Test Suite             ║${NC}"
echo -e "${BOLD}║       Target: ${BASE_URL}$(printf '%-35s' '')║${NC}"
echo -e "${BOLD}║       $(date '+%Y-%m-%d %H:%M:%S')$(printf '%-35s' '')║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"

# =============================================================================
# CHECK 1 — Platform Health (gateway + backend)
# =============================================================================
header 1 "Platform Health"

info "Testing API gateway /health ..."
HEALTH=$(http_get "${BASE_URL}/health" 2>/dev/null || echo "{}")
if echo "$HEALTH" | grep -q '"status"'; then
    STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    pass "API gateway healthy (status: ${STATUS})"
else
    fail "API gateway /health returned unexpected response: ${HEALTH}"
fi

info "Testing backend /health/ready ..."
READY=$(http_get "${API}/health/ready" 2>/dev/null || http_get "${BASE_URL}/health/ready" 2>/dev/null || echo "{}")
if echo "$READY" | grep -q '"status"\|"ready"'; then
    pass "Backend readiness probe OK"
else
    warn "Backend /health/ready not reachable or unexpected response"
fi

# =============================================================================
# CHECK 2 — Authentication (login + JWT)
# =============================================================================
header 2 "Authentication & JWT"

# Use test credentials from env or defaults
TEST_EMAIL="${TEST_EMAIL:-admin@gula-platform.org}"
TEST_PASS="${TEST_PASS:-}"

if [ -z "$TEST_PASS" ]; then
    # Try to get admin password from .env
    if [ -f "$(dirname "$0")/../.env" ]; then
        TEST_PASS=$(grep -oP '^GULA_ADMIN_PASSWORD=\K.*' "$(dirname "$0")/../.env" 2>/dev/null | head -1 || echo "")
    fi
fi

if [ -n "$TEST_PASS" ]; then
    info "Attempting login as ${TEST_EMAIL} ..."
    LOGIN_RESP=$(http_post "${API}/login" \
        "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASS}\"}" 2>/dev/null || echo "{}")
    TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',d.get('token','')))" 2>/dev/null || echo "")

    if [ -n "$TOKEN" ]; then
        AUTH_HEADER="$TOKEN"
        pass "Authentication: login succeeded, JWT issued"

        # Verify JWT works
        ME_STATUS=$(http_status "${API}/users/me")
        if [ "$ME_STATUS" = "200" ]; then
            pass "Authentication: JWT accepted on /users/me"
        else
            warn "Authentication: /users/me returned HTTP ${ME_STATUS}"
        fi
    else
        warn "Authentication: login did not return a token (response: ${LOGIN_RESP})"
    fi
else
    warn "Authentication: TEST_PASS not set — skipping login check (set GULA_ADMIN_PASSWORD in .env)"
fi

# =============================================================================
# CHECK 3 — Patient CRUD
# =============================================================================
header 3 "Patient CRUD"

PATIENTS_STATUS=$(http_status "${API}/patients?limit=1")
case "$PATIENTS_STATUS" in
    200) pass "Patients: GET /patients returned 200" ;;
    401) warn "Patients: GET /patients returned 401 (auth required — expected if no token)" ;;
    000) fail "Patients: GET /patients unreachable (connection refused)" ;;
    *)   fail "Patients: GET /patients returned unexpected HTTP ${PATIENTS_STATUS}" ;;
esac

if [ -n "$AUTH_HEADER" ]; then
    NEW_PT=$(http_post "${API}/patients" \
        '{"first_name":"Integration","last_name":"Test","date_of_birth":"1990-01-01","gender":"M","national_id":"IT_TEST_'$(date +%s)'"}' \
        2>/dev/null || echo "{}")
    if echo "$NEW_PT" | grep -q '"id"'; then
        PATIENT_ID=$(echo "$NEW_PT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
        pass "Patients: POST /patients created patient id=${PATIENT_ID}"
    else
        warn "Patients: POST /patients — unexpected response (may require unique NID)"
    fi
fi

# =============================================================================
# CHECK 4 — Orders & Workflow
# =============================================================================
header 4 "Orders & Workflow"

ORDERS_STATUS=$(http_status "${API}/orders?limit=1")
case "$ORDERS_STATUS" in
    200) pass "Orders: GET /orders returned 200" ;;
    401) warn "Orders: GET /orders returned 401 (auth required)" ;;
    000) fail "Orders: GET /orders unreachable" ;;
    *)   fail "Orders: GET /orders returned unexpected HTTP ${ORDERS_STATUS}" ;;
esac

TESTS_STATUS=$(http_status "${BASE_URL}/test-types")
if [ "$TESTS_STATUS" = "200" ]; then
    pass "Orders: GET /test-types returned 200"
else
    warn "Orders: GET /test-types returned HTTP ${TESTS_STATUS}"
fi

# =============================================================================
# CHECK 5 — Results & MinIO Upload
# =============================================================================
header 5 "Results & Storage"

RESULTS_STATUS=$(http_status "${API}/results?limit=1")
case "$RESULTS_STATUS" in
    200) pass "Results: GET /results returned 200" ;;
    401) warn "Results: GET /results returned 401 (auth required)" ;;
    000) fail "Results: GET /results unreachable" ;;
    *)   fail "Results: GET /results returned unexpected HTTP ${RESULTS_STATUS}" ;;
esac

# Check MinIO health if accessible
MINIO_STATUS=$(curl -so /dev/null -w "%{http_code}" --max-time 5 http://localhost:9003/minio/health/live 2>/dev/null || echo "000")
if [ "$MINIO_STATUS" = "200" ]; then
    pass "Results: MinIO object storage healthy"
elif [ "$MINIO_STATUS" = "000" ]; then
    warn "Results: MinIO not reachable on :9003 (may be in K8s or different port)"
else
    warn "Results: MinIO health returned HTTP ${MINIO_STATUS}"
fi

# =============================================================================
# CHECK 6 — Audit Log Integrity (Executive Order 5)
# =============================================================================
header 6 "Audit Log Integrity"

AUDIT_RESP=$(http_get "${API}/compliance/audit-integrity" 2>/dev/null || echo "{}")
if echo "$AUDIT_RESP" | grep -q '"status"'; then
    AUDIT_STATUS=$(echo "$AUDIT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    HMAC_FAILURES=$(echo "$AUDIT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('hmac_failures',0))" 2>/dev/null || echo "0")
    if [ "$AUDIT_STATUS" = "intact" ] && [ "$HMAC_FAILURES" = "0" ]; then
        pass "Audit: chain intact, HMAC failures: 0"
    elif [ "$AUDIT_STATUS" = "intact" ]; then
        warn "Audit: status intact but HMAC failures=${HMAC_FAILURES}"
    else
        fail "Audit: integrity check returned status=${AUDIT_STATUS}"
    fi
else
    AUDIT_HTTP=$(http_status "${API}/compliance/audit-integrity")
    if [ "$AUDIT_HTTP" = "401" ] || [ "$AUDIT_HTTP" = "403" ]; then
        warn "Audit: /compliance/audit-integrity requires auth (HTTP ${AUDIT_HTTP})"
    elif [ "$AUDIT_HTTP" = "000" ]; then
        fail "Audit: /compliance/audit-integrity unreachable"
    else
        warn "Audit: unexpected response (HTTP ${AUDIT_HTTP})"
    fi
fi

# =============================================================================
# CHECK 7 — RabbitMQ Queues (Executive Order 2 & 6)
# =============================================================================
header 7 "RabbitMQ Durable Queues"

RABBITMQ_USER="${RABBITMQ_USER:-gula}"
RABBITMQ_PASS="${RABBITMQ_PASS:-}"

# Try to get from .env
if [ -z "$RABBITMQ_PASS" ] && [ -f "$(dirname "$0")/../.env" ]; then
    RABBITMQ_PASS=$(grep -oP '^RABBITMQ_PASS=\K.*' "$(dirname "$0")/../.env" 2>/dev/null | head -1 || echo "")
fi

MQ_STATUS=$(curl -so /dev/null -w "%{http_code}" --max-time 5 \
    -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" \
    "http://localhost:15672/api/queues/gula" 2>/dev/null || echo "000")

if [ "$MQ_STATUS" = "200" ]; then
    QUEUES=$(curl -sf --max-time 5 \
        -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" \
        "http://localhost:15672/api/queues/gula" 2>/dev/null || echo "[]")
    QUEUE_NAMES=$(echo "$QUEUES" | python3 -c "
import sys,json
try:
    qs=json.load(sys.stdin)
    names=[q['name'] for q in qs]
    required={'orders.events','samples.events','results.events','alerts.events','audit.events'}
    missing=required-set(names)
    print('NAMES=' + ','.join(names))
    print('MISSING=' + ','.join(missing) if missing else 'MISSING=')
except: print('NAMES=error\nMISSING=')
" 2>/dev/null || echo "NAMES=error")

    MISSING=$(echo "$QUEUE_NAMES" | grep '^MISSING=' | cut -d= -f2)
    if [ -z "$MISSING" ]; then
        pass "RabbitMQ: all required durable queues present"
    else
        fail "RabbitMQ: missing queues: ${MISSING}"
    fi
elif [ "$MQ_STATUS" = "401" ]; then
    warn "RabbitMQ: management API requires credentials (set RABBITMQ_USER/PASS)"
elif [ "$MQ_STATUS" = "000" ]; then
    warn "RabbitMQ: management API not reachable on :15672 (may be in K8s or different network)"
else
    warn "RabbitMQ: management API returned HTTP ${MQ_STATUS}"
fi

# =============================================================================
# CHECK 8 — Redis Cache (Executive Order 9)
# =============================================================================
header 8 "Redis Cache"

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASS="${REDIS_PASS:-}"

if [ -z "$REDIS_PASS" ] && [ -f "$(dirname "$0")/../.env" ]; then
    REDIS_PASS=$(grep -oP '^REDIS_PASSWORD=\K.*' "$(dirname "$0")/../.env" 2>/dev/null | head -1 || echo "")
fi

if command -v redis-cli &>/dev/null; then
    if [ -n "$REDIS_PASS" ]; then
        REDIS_PONG=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASS" --no-auth-warning ping 2>/dev/null || echo "FAIL")
    else
        REDIS_PONG=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null || echo "FAIL")
    fi
    if [ "$REDIS_PONG" = "PONG" ]; then
        pass "Redis: PING → PONG (cache operational)"
        # Check memory
        USED_MEM=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
            ${REDIS_PASS:+-a "$REDIS_PASS"} --no-auth-warning \
            info memory 2>/dev/null | grep 'used_memory_human' | cut -d: -f2 | tr -d '[:space:]' || echo "?")
        info "Redis memory in use: ${USED_MEM}"
    else
        fail "Redis: PING failed (response: ${REDIS_PONG})"
    fi
else
    # Fallback: TCP connectivity check
    if python3 -c "import socket; s=socket.create_connection(('${REDIS_HOST}',${REDIS_PORT}),timeout=3); s.close()" 2>/dev/null; then
        pass "Redis: TCP connection on ${REDIS_HOST}:${REDIS_PORT} OK (redis-cli not installed)"
    else
        warn "Redis: TCP connection failed on ${REDIS_HOST}:${REDIS_PORT}"
    fi
fi

# =============================================================================
# CHECK 9 — AI Service (Executive Orders 3 & 4)
# =============================================================================
header 9 "AI Service (Local Ollama)"

AI_HEALTH=$(http_get "http://localhost:9000/health" 2>/dev/null || echo "{}")
if echo "$AI_HEALTH" | grep -q '"status"'; then
    pass "AI service: healthy on :9000"
else
    AI_STATUS=$(curl -so /dev/null -w "%{http_code}" --max-time 5 http://localhost:9000/health 2>/dev/null || echo "000")
    if [ "$AI_STATUS" = "000" ]; then
        warn "AI service: not reachable on :9000 (may be in K8s or not started)"
    else
        warn "AI service: returned HTTP ${AI_STATUS}"
    fi
fi

# Check Ollama model availability
OLLAMA_TAGS=$(http_get "http://localhost:11434/api/tags" 2>/dev/null || echo "{}")
if echo "$OLLAMA_TAGS" | grep -q '"models"\|llama'; then
    MODEL=$(echo "$OLLAMA_TAGS" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    models=[m.get('name','?') for m in d.get('models',[])]
    print(','.join(models) if models else 'none')
except: print('unknown')
" 2>/dev/null || echo "unknown")
    pass "AI service: Ollama reachable, models: ${MODEL}"
else
    OLLAMA_STATUS=$(curl -so /dev/null -w "%{http_code}" --max-time 5 http://localhost:11434/api/tags 2>/dev/null || echo "000")
    if [ "$OLLAMA_STATUS" = "000" ]; then
        warn "AI service: Ollama not reachable on :11434 (run: make pull-ai)"
    else
        warn "AI service: Ollama returned HTTP ${OLLAMA_STATUS}"
    fi
fi

# Verify AI provider is set to local (Executive Order 4 — no external AI)
if [ -f "$(dirname "$0")/../.env" ]; then
    AI_PROVIDER=$(grep -oP '^AI_PROVIDER=\K.*' "$(dirname "$0")/../.env" 2>/dev/null | head -1 || echo "")
    AI_FALLBACK=$(grep -oP '^AI_FALLBACK=\K.*' "$(dirname "$0")/../.env" 2>/dev/null | head -1 || echo "")
    if [ "$AI_PROVIDER" = "ollama" ] && [ "$AI_FALLBACK" = "false" ]; then
        pass "AI service: using local Ollama only (no external AI providers)"
    else
        warn "AI service: AI_PROVIDER=${AI_PROVIDER:-unset}, AI_FALLBACK=${AI_FALLBACK:-unset} — should be ollama/false"
    fi
fi

# =============================================================================
# CHECK 10 — Security Headers & Rate Limiting (Executive Order 15)
# =============================================================================
header 10 "Security Headers & Rate Limiting"

HEADERS=$(curl -sI --max-time 10 "${BASE_URL}/health" 2>/dev/null || echo "")
if [ -n "$HEADERS" ]; then
    PASS_SEC=0; FAIL_SEC=0
    for header in "X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection"; do
        if echo "$HEADERS" | grep -qi "$header"; then
            PASS_SEC=$((PASS_SEC+1))
        else
            FAIL_SEC=$((FAIL_SEC+1))
            info "Missing security header: ${header}"
        fi
    done
    if [ "$FAIL_SEC" -eq 0 ]; then
        pass "Security: all security headers present (${PASS_SEC}/3)"
    else
        warn "Security: ${PASS_SEC}/3 security headers present (${FAIL_SEC} missing)"
    fi

    # Check that server header doesn't leak version info
    if echo "$HEADERS" | grep -qi "server: nginx/[0-9]"; then
        warn "Security: Server header exposes nginx version"
    else
        pass "Security: Server header does not expose detailed version"
    fi
else
    warn "Security: could not fetch headers from ${BASE_URL}/health"
fi

# Rate limit check: send 5 quick requests, verify no crash
RL_FAIL=0
for _ in 1 2 3 4 5; do
    CODE=$(curl -so /dev/null -w "%{http_code}" --max-time 5 "${BASE_URL}/health" 2>/dev/null || echo "000")
    [ "$CODE" = "000" ] && RL_FAIL=$((RL_FAIL+1))
done
if [ "$RL_FAIL" -eq 0 ]; then
    pass "Security: gateway handles burst requests without crashing"
else
    warn "Security: ${RL_FAIL}/5 burst requests failed"
fi

# =============================================================================
# SUMMARY
# =============================================================================

TOTAL=$((PASS+FAIL+WARN))
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Integration Test Results${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}PASS: ${PASS}${NC}   ${YELLOW}WARN: ${WARN}${NC}   ${RED}FAIL: ${FAIL}${NC}   Total: ${TOTAL}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "  ${RED}Failed checks:${NC}"
    for r in "${RESULTS[@]}"; do
        [[ "$r" == FAIL:* ]] && echo -e "  ${RED}  • ${r#FAIL: }${NC}"
    done
    echo ""
fi

if [ "$WARN" -gt 0 ]; then
    echo -e "  ${YELLOW}Warnings:${NC}"
    for r in "${RESULTS[@]}"; do
        [[ "$r" == WARN:* ]] && echo -e "  ${YELLOW}  • ${r#WARN: }${NC}"
    done
    echo ""
fi

# Write machine-readable result
RESULT_FILE="$(dirname "$0")/../last_integration_test.json"
python3 -c "
import json
from datetime import datetime, timezone
print(json.dumps({
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'pass': ${PASS},
    'warn': ${WARN},
    'fail': ${FAIL},
    'total': ${TOTAL},
    'result': '$( [ "$FAIL" -eq 0 ] && echo PASS || echo FAIL )'
}, indent=2))
" > "$RESULT_FILE" 2>/dev/null && info "Results saved to last_integration_test.json" || true

if [ "$FAIL" -gt 0 ]; then
    echo -e "  ${RED}${BOLD}OVERALL: FAIL${NC}"
    exit 1
else
    echo -e "  ${GREEN}${BOLD}OVERALL: PASS${NC}"
    exit 0
fi
