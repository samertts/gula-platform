#!/bin/bash

# GULA Platform - Load Testing Script
# Usage: ./scripts/load-test.sh [base_url] [num_users] [duration_seconds]

BASE_URL="${1:-http://localhost:3000}"
NUM_USERS="${2:-100}"
DURATION="${3:-60}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# LOAD TEST WITH APACHE BENCH
# ============================================================================

if ! command -&gt; ab &gt; /dev/null; then
  log_error "Apache Bench (ab) is not installed"
  log_info "Install with: sudo apt-get install apache2-utils"
  exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          GULA Platform - Load Test                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info "Base URL: $BASE_URL"
log_info "Number of Users (concurrent): $NUM_USERS"
log_info "Duration: $DURATION seconds"
echo ""

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

echo -e "${YELLOW}--- Load Test: /health ---${NC}"
log_info "Running $NUM_USERS concurrent requests for $DURATION seconds..."
echo ""

ab -n $((NUM_USERS * DURATION / 10)) \
   -c $NUM_USERS \
   -t $DURATION \
   -g /tmp/gula-health-load-test.tsv \
   "$BASE_URL/health"

echo ""

# ============================================================================
# PING ENDPOINT
# ============================================================================

echo -e "${YELLOW}--- Load Test: /api/test/ping ---${NC}"
log_info "Running $NUM_USERS concurrent requests..."
echo ""

ab -n $((NUM_USERS * DURATION / 10)) \
   -c $NUM_USERS \
   -t $DURATION \
   -g /tmp/gula-ping-load-test.tsv \
   "$BASE_URL/api/test/ping"

echo ""

# ============================================================================
# ECHO ENDPOINT (POST)
# ============================================================================

echo -e "${YELLOW}--- Load Test: /api/test/echo (POST) ---${NC}"
log_info "Running $NUM_USERS concurrent POST requests..."
echo ""

ab -n $((NUM_USERS * DURATION / 10)) \
   -c $NUM_USERS \
   -t $DURATION \
   -p /tmp/echo-payload.json \
   -T application/json \
   -g /tmp/gula-echo-load-test.tsv \
   "$BASE_URL/api/test/echo"

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Load Test Summary                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_success "Load test completed!"
log_info "Results saved to /tmp/gula-*-load-test.tsv"
log_info "View results with: gnuplot /tmp/gula-health-load-test.tsv"
echo ""

# ============================================================================
# STRESS TEST WITH WRK (if available)
# ============================================================================

if command -v wrk &gt; /dev/null; then
  echo -e "${YELLOW}--- Stress Test with wrk ---${NC}"
  log_info "Running stress test with wrk..."
  echo ""
  
  wrk -t4 -c$NUM_USERS -d${DURATION}s "$BASE_URL/health"
  
  echo ""
fi

# ============================================================================
# PERFORMANCE ANALYSIS
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                Performance Recommendations                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. Monitor response times (p50, p95, p99)"
echo "2. Check for any errors or timeouts"
echo "3. Monitor server CPU and memory usage"
echo "4. Check database connection pool"
echo "5. Verify Redis cache hit rates"
echo ""
