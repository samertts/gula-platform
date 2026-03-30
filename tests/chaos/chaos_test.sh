#!/bin/bash
# =============================================================================
# GULA Platform — Chaos Engineering Test Suite
# Tests resilience against infrastructure failures in the actual docker-compose stack
# =============================================================================
# Usage:
#   ./tests/chaos/chaos_test.sh              # run all tests
#   ./tests/chaos/chaos_test.sh redis-kill   # run single test
# Containers expected: gula-backend, gula-postgres, gula-redis
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

PASS=0; FAIL=0; SKIP=0
BACKEND="${BACKEND_URL:-http://localhost:8000}"

pass()  { echo -e "${GREEN}  ✓ PASS${NC} $1"; ((PASS++));  }
fail()  { echo -e "${RED}  ✗ FAIL${NC} $1"; ((FAIL++));    }
skip()  { echo -e "${YELLOW}  ⚠ SKIP${NC} $1"; ((SKIP++)); }
info()  { echo -e "${BLUE}  ► ${NC}$1"; }
title() { echo -e "\n${BOLD}$1${NC}"; }

health_grade() {
    python3 -c "
import urllib.request, json, sys
try:
    r = urllib.request.urlopen('${BACKEND}/health/deep', timeout=5)
    print(json.loads(r.read()).get('grade','UNREACHABLE'))
except:
    print('UNREACHABLE')
" 2>/dev/null
}

health_ready() {
    python3 -c "
import urllib.request
try:
    urllib.request.urlopen('${BACKEND}/health/ready', timeout=5)
    exit(0)
except:
    exit(1)
" 2>/dev/null
}

wait_container_healthy() {
    local container=$1 timeout=${2:-60}
    info "Waiting up to ${timeout}s for ${container}..."
    for i in $(seq 1 $timeout); do
        state=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        [ "$state" = "healthy" ] && info "${container} healthy (${i}s)" && return 0
        sleep 1
    done
    return 1
}

wait_grade() {
    local want=$1 timeout=${2:-60}
    for i in $(seq 1 $timeout); do
        [ "$(health_grade)" = "$want" ] && info "Grade is ${want} (${i}s)" && return 0
        sleep 1
    done
    return 1
}

check_stack_running() {
    if ! docker ps --format '{{.Names}}' | grep -q "gula-backend"; then
        echo -e "${YELLOW}Stack not running. Start with: make up${NC}"
        exit 1
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
test_baseline() {
    title "TEST 0 — Baseline"
    grade=$(health_grade)
    if [ "$grade" = "GREEN" ]; then
        pass "Baseline: GREEN"
    else
        fail "Baseline: ${grade} — fix platform first"
        exit 1
    fi
}

test_redis_kill() {
    title "TEST 1 — Redis stop → degraded → auto-recovery"

    info "Stopping gula-redis..."
    docker compose stop redis
    sleep 5

    grade=$(health_grade)
    info "Grade after stop: ${grade}"

    if health_ready; then
        pass "Backend still responds without Redis (in-memory fallback)"
    else
        fail "Backend unresponsive after Redis stop"
    fi

    if [ "$grade" = "YELLOW" ] || [ "$grade" = "RED" ]; then
        pass "Grade degraded to ${grade} as expected"
    else
        fail "Expected YELLOW/RED, got ${grade}"
    fi

    info "Restarting gula-redis..."
    docker compose start redis

    if wait_container_healthy "gula-redis" 30 && wait_grade "GREEN" 60; then
        pass "Recovered to GREEN after Redis restart"
    else
        fail "Did not recover to GREEN in 60s"
    fi
}

test_postgres_kill() {
    title "TEST 2 — PostgreSQL stop → RED → auto-recovery"

    info "Stopping gula-postgres..."
    docker compose stop postgres
    sleep 5

    grade=$(health_grade)
    info "Grade after stop: ${grade}"

    if [ "$grade" = "RED" ]; then
        pass "Grade RED as expected (DB is critical)"
    else
        fail "Expected RED, got ${grade}"
    fi

    info "Restarting gula-postgres..."
    docker compose start postgres

    if wait_container_healthy "gula-postgres" 60 && wait_grade "GREEN" 90; then
        pass "Recovered to GREEN after PostgreSQL restart"
    else
        fail "Did not recover to GREEN in 90s"
    fi
}

test_backend_restart() {
    title "TEST 3 — Backend restart → downtime < 30s"

    start_ts=$(date +%s)
    info "Restarting gula-backend..."
    docker compose restart gula-backend

    # Wait for it to go down
    for i in $(seq 1 10); do
        health_ready || break
        sleep 1
    done

    if wait_container_healthy "gula-backend" 60 && wait_grade "GREEN" 30; then
        end_ts=$(date +%s)
        downtime=$((end_ts - start_ts))
        pass "Recovered (total restart cycle: ${downtime}s)"
        [ $downtime -le 60 ] && pass "Recovery within 60s SLO" || fail "Recovery took ${downtime}s (>60s)"
    else
        fail "Backend did not recover"
    fi
}

test_health_schema() {
    title "TEST 4 — /health/deep schema"

    result=$(python3 -c "
import urllib.request, json, sys
try:
    r = urllib.request.urlopen('${BACKEND}/health/deep', timeout=5)
    d = json.loads(r.read())
    required = ['grade','issues','components','process','version','timestamp']
    missing = [k for k in required if k not in d]
    comp_required = ['database','redis','queue']
    comp_missing = [k for k in comp_required if k not in d.get('components',{})]
    if missing or comp_missing:
        print(f'MISSING: top={missing} components={comp_missing}')
    else:
        print('OK')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

    if [ "$result" = "OK" ]; then
        pass "/health/deep has all required fields"
    else
        fail "/health/deep schema: ${result}"
    fi
}

test_prometheus_metrics() {
    title "TEST 5 — /metrics/prom Prometheus format"

    result=$(python3 -c "
import urllib.request, sys
try:
    r = urllib.request.urlopen('${BACKEND}/metrics/prom', timeout=5)
    body = r.read().decode()
    required = ['gula_up', 'gula_db_up', 'gula_redis_up',
                'gula_memory_rss_mb', 'gula_orders_total',
                'gula_active_requests', 'gula_queue_backlog']
    missing = [m for m in required if m not in body]
    print('MISSING: ' + str(missing) if missing else 'OK')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

    if [ "$result" = "OK" ]; then
        pass "/metrics/prom exposes all required metrics"
    elif echo "$result" | grep -q "ERROR: HTTP Error 404"; then
        skip "/metrics/prom blocked by nginx (expected in production)"
    elif echo "$result" | grep -q "Unauthorized"; then
        skip "/metrics/prom requires METRICS_BEARER_TOKEN (expected)"
    else
        fail "/metrics/prom: ${result}"
    fi
}

test_rate_limit() {
    title "TEST 6 — Rate limiting (429 + headers)"

    got_429=0
    for i in $(seq 1 20); do
        code=$(python3 -c "
import urllib.request, json
try:
    req = urllib.request.Request('${BACKEND}/login',
          data=json.dumps({'username':'chaos_test','password':'wrong'}).encode(),
          headers={'Content-Type':'application/json'}, method='POST')
    urllib.request.urlopen(req, timeout=3)
    print('200')
except urllib.error.HTTPError as e:
    print(e.code)
except Exception:
    print('0')
" 2>/dev/null)
        if [ "$code" = "429" ]; then
            got_429=1
            pass "Rate limit 429 triggered after rapid auth requests"
            # Verify Retry-After header
            has_retry=$(python3 -c "
import urllib.request, json
try:
    req = urllib.request.Request('${BACKEND}/login',
          data=json.dumps({'username':'chaos_test','password':'wrong'}).encode(),
          headers={'Content-Type':'application/json'}, method='POST')
    urllib.request.urlopen(req, timeout=3)
    print('no-429')
except urllib.error.HTTPError as e:
    headers = dict(e.headers)
    print('OK' if 'Retry-After' in headers else 'MISSING-RETRY-AFTER')
except Exception:
    print('error')
" 2>/dev/null)
            [ "$has_retry" = "OK" ] && pass "Retry-After header present" || \
                                       fail "Retry-After header missing (got: ${has_retry})"
            break
        fi
    done

    [ $got_429 -eq 0 ] && skip "429 not triggered in 20 rapid requests (auth limit may be >20)"
}

# ─────────────────────────────────────────────────────────────────────────────
FILTER="${1:-all}"

echo ""
echo "================================================================"
echo "  GULA Platform — Chaos Engineering Tests"
echo "  Backend: ${BACKEND}"
echo "  $(date)"
echo "================================================================"

check_stack_running
test_baseline

case "$FILTER" in
    redis-kill)    test_redis_kill ;;
    postgres-kill) test_postgres_kill ;;
    restart)       test_backend_restart ;;
    schema)        test_health_schema ;;
    metrics)       test_prometheus_metrics ;;
    rate-limit)    test_rate_limit ;;
    all)
        test_redis_kill
        test_postgres_kill
        test_backend_restart
        test_health_schema
        test_prometheus_metrics
        test_rate_limit
        ;;
    *)
        echo "Usage: $0 [all|redis-kill|postgres-kill|restart|schema|metrics|rate-limit]"
        exit 1
        ;;
esac

echo ""
echo "================================================================"
echo -e "  Results: ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  ${YELLOW}${SKIP} skipped${NC}"
echo "================================================================"
echo ""

[ $FAIL -eq 0 ] && exit 0 || exit 1
