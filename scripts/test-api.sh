#!/bin/bash

# GULA Platform - API Test Script
# Usage: ./scripts/test-api.sh [base_url]

BASE_URL="${1:-http://localhost:3000}"
TIMESTAMP=$(date +%s%N)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log_test() {
  echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
  echo -e "${GREEN}[PASS]${NC} $1"
  ((TESTS_PASSED++))
}

log_fail() {
  echo -e "${RED}[FAIL]${NC} $1"
  ((TESTS_FAILED++))
}

log_info() {
  echo -e "${YELLOW}[INFO]${NC} $1"
}

test_endpoint() {
  local name=$1
  local method=$2
  local endpoint=$3
  local data=$4
  local expected_status=$5

  ((TESTS_RUN++))
  log_test "$name"

  if [ -z "$data" ]; then
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
      -H "Content-Type: application/json")
  else
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
      -H "Content-Type: application/json" \
      -d "$data")
  fi

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | head -n-1)

  if [ "$http_code" = "$expected_status" ]; then
    log_pass "$name - HTTP $http_code"
    echo "Response: $body" | head -c 100
    echo ""
  else
    log_fail "$name - Expected HTTP $expected_status, got $http_code"
    echo "Response: $body" | head -c 200
    echo ""
  fi
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          GULA Platform - API Test Suite                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
log_info "Base URL: $BASE_URL"
echo ""

echo -e "${YELLOW}--- Health Checks ---${NC}"
test_endpoint "Liveness Check" "GET" "/health/live" "" "200"
test_endpoint "Readiness Check" "GET" "/health/ready" "" "200"
test_endpoint "Full Health Check" "GET" "/health" "" "200"

# ============================================================================
# TEST ENDPOINTS
# ============================================================================

echo ""
echo -e "${YELLOW}--- Test Endpoints ---${NC}"
test_endpoint "Ping Test" "GET" "/api/test/ping" "" "200"
test_endpoint "Echo Test" "POST" "/api/test/echo" '{"message":"Hello GULA"}' "200"
test_endpoint "Echo Test - Invalid" "POST" "/api/test/echo" '{"invalid":"data"}' "400"

# ============================================================================
# PATIENT MANAGEMENT (Mock)
# ============================================================================

echo ""
echo -e "${YELLOW}--- Patient Management (Mock) ---${NC}"

PATIENT_DATA='{
  "name": "أحمد محمد",
  "email": "ahmed@example.com",
  "phone": "+964771234567",
  "nationalId": "12345678901234",
  "dateOfBirth": "1990-01-15",
  "gender": "M",
  "address": "بغداد، العراق"
}'

test_endpoint "Create Patient" "POST" "/api/patients" "$PATIENT_DATA" "201"

# ============================================================================
# SAMPLE MANAGEMENT (Mock)
# ============================================================================

echo ""
echo -e "${YELLOW}--- Sample Management (Mock) ---${NC}"

SAMPLE_DATA='{
  "patientId": "patient-123",
  "sampleType": "blood",
  "collectionDate": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "volume": "5ml",
  "notes": "Routine blood test"
}'

test_endpoint "Create Sample" "POST" "/api/samples" "$SAMPLE_DATA" "201"

# ============================================================================
# RESULTS MANAGEMENT (Mock)
# ============================================================================

echo ""
echo -e "${YELLOW}--- Results Management (Mock) ---${NC}"

RESULT_DATA='{
  "sampleId": "sample-123",
  "testType": "blood_count",
  "values": {
    "wbc": 7.5,
    "rbc": 4.8,
    "hemoglobin": 14.2,
    "hematocrit": 42.5
  },
  "referenceRange": {
    "wbc": "4.5-11.0",
    "rbc": "4.5-5.5",
    "hemoglobin": "13.5-17.5",
    "hematocrit": "41-53"
  },
  "status": "normal"
}'

test_endpoint "Create Result" "POST" "/api/results" "$RESULT_DATA" "201"

# ============================================================================
# REPORT GENERATION (Mock)
# ============================================================================

echo ""
echo -e "${YELLOW}--- Report Generation (Mock) ---${NC}"

REPORT_DATA='{
  "patientId": "patient-123",
  "resultIds": ["result-123"],
  "format": "pdf"
}'

test_endpoint "Generate Report" "POST" "/api/reports/generate" "$REPORT_DATA" "200"

# ============================================================================
# ERROR HANDLING
# ============================================================================

echo ""
echo -e "${YELLOW}--- Error Handling ---${NC}"
test_endpoint "404 Not Found" "GET" "/api/nonexistent" "" "404"
test_endpoint "Invalid Method" "DELETE" "/api/test/ping" "" "405"

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Test Summary                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Total Tests: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some tests failed!${NC}"
  exit 1
fi
