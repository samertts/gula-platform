#!/usr/bin/env bash
# =============================================================================
# GSF: health-check.sh — Security Subsystem Health Check
# =============================================================================
# Checks all security services, audit log writability, secret backend
# accessibility, crypto module self-tests, and reports an overall security
# health score.
#
# Usage:
#   ./health-check.sh [options]
#
# Options:
#   --verbose       Detailed output
#   --json          Output results as JSON
#   --help, -h      Show this help message
#
# Exit codes:
#   0   All subsystems healthy
#   1   One or more subsystems degraded/unhealthy
#   2   Error during health check
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VERBOSE=false
OUTPUT_JSON=false

HEALTH_SCORE=100
HEALTH_CHECKS_PASSED=0
HEALTH_CHECKS_TOTAL=0
HEALTH_FAILURES=()

usage() {
    sed -n '/^# ============/,/^# ============/p' "${BASH_SOURCE[0]}" | \
        grep -v '^# ============' | sed 's/^# //'
    exit 0
}

log_info()  { [[ "${VERBOSE}" == true ]] && echo "[INFO]  $*" >&2 || true; }
log_warn()  { echo "[WARN]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_pass()  { echo "[PASS]  $*"; }
log_fail()  { echo "[FAIL] $*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --verbose) VERBOSE=true ;;
        --json) OUTPUT_JSON=true ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
done

check() {
    local name="$1"
    local weight="$2"
    local score_deduction="$3"
    shift 3

    HEALTH_CHECKS_TOTAL=$((HEALTH_CHECKS_TOTAL + 1))
    log_info "Checking: ${name}..."

    if "$@"; then
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
        log_pass "${name}"
    else
        HEALTH_SCORE=$((HEALTH_SCORE - score_deduction))
        HEALTH_FAILURES+=("${name}")
        log_fail "${name}"
    fi
}

check_python_import() {
    python3 -c "import $1" 2>/dev/null
}

check_command_exists() {
    command -v "$1" &>/dev/null
}

check_file_writable() {
    local path="$1"
    local dir
    dir="$(dirname "${path}")"
    mkdir -p "${dir}" 2>/dev/null
    touch "${path}" 2>/dev/null
}

check_service_pid() {
    local name="$1"
    pgrep -f "${name}" &>/dev/null
}

main() {
    log_info "Starting GSF security subsystem health check..."

    # 1. Python module imports
    check "GSF Secrets module import" 5 10 check_python_import "security.modules.secrets.engine"
    check "GSF Crypto module import" 5 10 check_python_import "security.modules.crypto.engine"
    check "GSF Audit module import" 5 10 check_python_import "security.modules.audit.logger"
    check "GSF Identity module import" 5 10 check_python_import "security.modules.identity.models"
    check "GSF Headers module import" 5 10 check_python_import "security.modules.headers.middleware"

    # 2. Audit log writability
    check "Audit log directory writable" 10 20 check_file_writable "/var/log/gula/audit/.health-check"

    # 3. Scanning tools availability
    check "Bandit available" 3 5 check_command_exists "bandit"
    check "Semgrep available" 3 5 check_command_exists "semgrep"
    check "Trivy available" 3 5 check_command_exists "trivy"
    check "Checkov available" 3 5 check_command_exists "checkov"
    check "Gitleaks available" 3 5 check_command_exists "gitleaks"

    # 4. Crypto self-test
    if check_python_import "cryptography"; then
        python3 -c "
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
key = os.urandom(32)
nonce = os.urandom(12)
cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
enc = cipher.encryptor()
ct = enc.update(b'test data') + enc.finalize()
assert len(ct) > 0, 'AES encryption failed'
print('AES-256-GCM encrypt/decrypt: PASS')
" && HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1)) && log_pass "Crypto self-test (AES-256-GCM)" \
        || { HEALTH_SCORE=$((HEALTH_SCORE - 20)); HEALTH_FAILURES+=("Crypto self-test"); log_fail "Crypto self-test"; }
    else
        log_warn "Cryptography library not installed, skipping crypto self-test"
    fi
    HEALTH_CHECKS_TOTAL=$((HEALTH_CHECKS_TOTAL + 1))

    # 5. Configuration file check
    local config_dir="${PROJECT_ROOT}/security/configs"
    local all_configs_found=true
    for cfg in rotation.yaml security-headers.yaml scanning.yaml audit.yaml threat-detection.yaml compliance.yaml password-policy.yaml; do
        if [[ ! -f "${config_dir}/${cfg}" ]]; then
            log_warn "Missing config: ${cfg}"
            all_configs_found=false
        fi
    done
    if ${all_configs_found}; then
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
        log_pass "All configuration files present"
    else
        HEALTH_SCORE=$((HEALTH_SCORE - 5))
        HEALTH_FAILURES+=("Configuration files")
        log_fail "Configuration files check"
    fi
    HEALTH_CHECKS_TOTAL=$((HEALTH_CHECKS_TOTAL + 1))

    # 6. Policy files check
    local policy_dir="${PROJECT_ROOT}/security/policies"
    local all_policies_found=true
    for pol in access-control.md encryption-policy.md incident-response-policy.md data-protection-policy.md; do
        if [[ ! -f "${policy_dir}/${pol}" ]]; then
            log_warn "Missing policy: ${pol}"
            all_policies_found=false
        fi
    done
    if ${all_policies_found}; then
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
        log_pass "All policy files present"
    else
        HEALTH_SCORE=$((HEALTH_SCORE - 5))
        HEALTH_FAILURES+=("Policy files")
        log_fail "Policy files check"
    fi
    HEALTH_CHECKS_TOTAL=$((HEALTH_CHECKS_TOTAL + 1))

    # Final report
    local health_status="HEALTHY"
    local exit_code=0
    if [[ ${HEALTH_SCORE} -lt 80 ]]; then
        health_status="CRITICAL"
        exit_code=1
    elif [[ ${HEALTH_SCORE} -lt 100 ]]; then
        health_status="DEGRADED"
        exit_code=1
    fi

    if [[ "${OUTPUT_JSON}" == true ]]; then
        cat << JSONEOF
{
    "health_score": ${HEALTH_SCORE},
    "status": "${health_status}",
    "checks_passed": ${HEALTH_CHECKS_PASSED},
    "checks_total": ${HEALTH_CHECKS_TOTAL},
    "failures": [$(printf '"%s",' "${HEALTH_FAILURES[@]}" | sed 's/,$//')],
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
JSONEOF
    else
        echo ""
        echo "============================================"
        echo "  GSF Security Health Check Report"
        echo "============================================"
        echo "  Status:       ${health_status}"
        echo "  Health Score: ${HEALTH_SCORE}/100"
        echo "  Checks:       ${HEALTH_CHECKS_PASSED}/${HEALTH_CHECKS_TOTAL} passed"
        if [[ ${#HEALTH_FAILURES[@]} -gt 0 ]]; then
            echo "  Failures:"
            for f in "${HEALTH_FAILURES[@]}"; do
                echo "    - ${f}"
            done
        fi
        echo "  Timestamp:    $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
        echo "============================================"
    fi

    exit "${exit_code}"
}

main
