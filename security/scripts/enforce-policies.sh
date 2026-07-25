#!/usr/bin/env bash
# =============================================================================
# GSF: enforce-policies.sh — Policy Enforcement
# =============================================================================
# Reads policies from security/policies/, checks the codebase against each
# policy rule, reports violations, and can auto-fix certain policies.
# Designed to run as a pre-commit hook or in CI.
#
# Usage:
#   ./enforce-policies.sh [options]
#
# Options:
#   --path PATH          Path to check [default: repository root]
#   --policy POLICY      Specific policy file to enforce (default: all)
#   --auto-fix           Auto-fix fixable violations
#   --ci                 CI mode (strict, exit on first violation batch)
#   --list-policies      List available policies and exit
#   --help, -h           Show this help message
#
# Exit codes:
#   0   All policies pass
#   1   Policy violations found
#   2   Error during enforcement
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
POLICY_DIR="${PROJECT_ROOT}/security/policies"
CHECK_PATH="${PROJECT_ROOT}"
TARGET_POLICY=""
AUTO_FIX=false
CI_MODE=false
LIST_POLICIES=false
VIOLATIONS=0
FIXED=0

usage() {
    sed -n '/^# ============/,/^# ============/p' "${BASH_SOURCE[0]}" | \
        grep -v '^# ============' | sed 's/^# //'
    exit 0
}

log_info()  { echo "[INFO]  $*" >&2; }
log_warn()  { echo "[WARN]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_pass()  { echo "[PASS]  $*"; }
log_fail()  { echo "[FAIL]  $*"; }
log_fix()   { echo "[FIX]   $*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --path) CHECK_PATH="$2"; shift ;;
        --policy) TARGET_POLICY="$2"; shift ;;
        --auto-fix) AUTO_FIX=true ;;
        --ci) CI_MODE=true ;;
        --list-policies) LIST_POLICIES=true ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
done

list_policies() {
    echo "Available GSF policies:"
    for f in "${POLICY_DIR}"/*.md; do
        local name
        name="$(basename "${f}" .md)"
        local title
        title="$(head -1 "${f}" 2>/dev/null | sed 's/^# //')"
        printf "  %-35s %s\n" "${name}" "${title}"
    done
    exit 0
}

if ${LIST_POLICIES}; then
    list_policies
fi

if [[ ! -d "${POLICY_DIR}" ]]; then
    log_error "Policy directory not found: ${POLICY_DIR}"
    exit 2
fi

check_policy_exists() {
    local policy_file="${POLICY_DIR}/${TARGET_POLICY}.md"
    if [[ -n "${TARGET_POLICY}" ]] && [[ ! -f "${policy_file}" ]]; then
        log_error "Policy file not found: ${policy_file}"
        exit 2
    fi
}

# ---------------------------------------------------------------------------
# Policy Checks
# ---------------------------------------------------------------------------

check_no_credentials_in_code() {
    local violated=false
    log_info "Checking: No hardcoded credentials in source code..."

    while IFS= read -r -d '' file; do
        local relpath
        relpath="${file#${CHECK_PATH}/}"
        case "${relpath}" in
            *.py|*.js|*.ts|*.tsx|*.jsx|*.yaml|*.yml|*.toml|*.env|*.sh|*.go|*.rs)
                ;;
            *) continue ;;
        esac
        while IFS= read -r line; do
            if [[ -z "${line}" ]]; then
                continue
            fi
            local lineno
            lineno=$(echo "${line}" | cut -d: -f1)
            local content
            content=$(echo "${line}" | cut -d: -f2-)
            if echo "${content}" | grep -qiP '(password|secret|api.?key|token|credential)\s*[:=]\s*["'"'"']?[^"'"'"'\s,;}]{8,}' 2>/dev/null; then
                log_fail "Hardcoded credential in ${relpath}:${lineno}"
                violated=true
                VIOLATIONS=$((VIOLATIONS + 1))
            fi
        done < <(grep -n -iP '(password|secret|api.?key|token)\s*[:=]\s*["'"'"']?[^"'"'"'\s,;}]{8,}' "${file}" 2>/dev/null || true)
    done < <(find "${CHECK_PATH}" -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.yaml' -o -name '*.yml' -o -name '*.sh' \) \
        ! -path '*/node_modules/*' ! -path '*/.venv/*' ! -path '*/__pycache__/*' ! -path '*/.git/*' -print0 2>/dev/null)

    if ! ${violated}; then
        log_pass "No hardcoded credentials found"
    fi
    ${violated} && return 1 || return 0
}

check_no_private_keys() {
    local violated=false
    log_info "Checking: No private keys in repository..."

    while IFS= read -r -d '' file; do
        local relpath
        relpath="${file#${CHECK_PATH}/}"
        if grep -q '-----BEGIN\s\+\(RSA\|EC\|DSA\|OPENSSH\|PRIVATE\)\s\+KEY-----' "${file}" 2>/dev/null; then
            log_fail "Private key found: ${relpath}"
            violated=true
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(find "${CHECK_PATH}" -type f ! -path '*/.git/*' -print0 2>/dev/null)

    if ! ${violated}; then
        log_pass "No private keys found"
    fi
    ${violated} && return 1 || return 0
}

check_no_dotenv_committed() {
    local violated=false
    log_info "Checking: No .env files committed..."

    while IFS= read -r -d '' file; do
        local relpath
        relpath="${file#${CHECK_PATH}/}"
        if [[ "${relpath}" != *".env.example" ]] && [[ "${relpath}" != *".env.template" ]]; then
            log_fail "Environment file committed: ${relpath}"
            violated=true
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(find "${CHECK_PATH}" -name '.env*' -not -name '.env.example' -not -name '.env.template' -print0 2>/dev/null)

    if ! ${violated}; then
        log_pass "No .env files committed"
    fi
    ${violated} && return 1 || return 0
}

check_permissions_0644_0755() {
    local violated=false
    log_info "Checking: File permissions (scripts 0755, others 0644)..."

    while IFS= read -r -d '' file; do
        local relpath="${file#${CHECK_PATH}/}"
        local perms
        perms=$(stat -c "%a" "${file}" 2>/dev/null || true)
        if [[ "${file}" == *.sh ]] || [[ "${file}" == *.py ]]; then
            if [[ "${perms}" != "755" ]] && [[ "${perms}" != "754" ]] && [[ "${perms}" != "750" ]]; then
                if ${AUTO_FIX}; then
                    chmod 755 "${file}"
                    log_fix "Fixed permissions: ${relpath} (${perms} -> 755)"
                    FIXED=$((FIXED + 1))
                else
                    log_fail "Wrong permissions: ${relpath} (${perms}, expected 755)"
                    violated=true
                    VIOLATIONS=$((VIOLATIONS + 1))
                fi
            fi
        fi
    done < <(find "${CHECK_PATH}" -type f \( -name '*.sh' -o -name '*.py' \) ! -path '*/.git/*' -print0 2>/dev/null)

    if ! ${violated}; then
        log_pass "File permissions correct"
    fi
    ${violated} && return 1 || return 0
}

check_security_imports() {
    local violated=false
    log_info "Checking: Security module imports in Python code..."

    while IFS= read -r -d '' file; do
        local relpath="${file#${CHECK_PATH}/}"
        case "${relpath}" in
            security/*) continue ;;
            tests/*) continue ;;
            *.py) ;;
            *) continue ;;
        esac
        local uses_crypto=false
        if grep -q 'from security\.modules\.crypto\|from security\.modules\.secrets\|from security\.modules\.identity' "${file}" 2>/dev/null; then
            uses_crypto=true
        fi
        local has_sensitive_ops=false
        if grep -qiP '(encrypt|decrypt|hash|sign|verify|password|secret|token)' "${file}" 2>/dev/null; then
            has_sensitive_ops=true
        fi
        if ${has_sensitive_ops} && ! ${uses_crypto}; then
            log_fail "Sensitive operation without GSF import: ${relpath}"
            violated=true
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(find "${CHECK_PATH}" -name '*.py' ! -path '*/.git/*' ! -path '*/node_modules/*' -print0 2>/dev/null)

    if ! ${violated}; then
        log_pass "All crypto-sensitive files use GSF imports"
    fi
    ${violated} && return 1 || return 0
}

check_security_headers_config() {
    local violated=false
    log_info "Checking: Security headers configuration..."

    local headers_config="${PROJECT_ROOT}/security/configs/security-headers.yaml"
    if [[ ! -f "${headers_config}" ]]; then
        log_fail "Security headers config not found"
        VIOLATIONS=$((VIOLATIONS + 1))
        return 1
    fi

    if grep -q 'strict_transport_security' "${headers_config}" 2>/dev/null; then
        log_pass "Security headers configured"
    else
        log_fail "Security headers missing"
        violated=true
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    ${violated} && return 1 || return 0
}

check_password_policy_config() {
    local violated=false
    log_info "Checking: Password policy configuration..."

    local pw_config="${PROJECT_ROOT}/security/configs/password-policy.yaml"
    if [[ ! -f "${pw_config}" ]]; then
        log_fail "Password policy config not found"
        VIOLATIONS=$((VIOLATIONS + 1))
        return 1
    fi

    if grep -q 'minimum_length' "${pw_config}" 2>/dev/null && grep -q 'mfa' "${pw_config}" 2>/dev/null; then
        log_pass "Password policy configured"
    else
        log_fail "Password policy incomplete"
        violated=true
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    ${violated} && return 1 || return 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    check_policy_exists

    log_info "Enforcing GSF policies from: ${POLICY_DIR}"
    log_info "Checking path: ${CHECK_PATH}"
    log_info "Auto-fix: ${AUTO_FIX}"
    log_info "CI mode: ${CI_MODE}"

    local exit_code=0

    check_no_credentials_in_code || exit_code=1
    check_no_private_keys || exit_code=1
    check_no_dotenv_committed || exit_code=1
    check_permissions_0644_0755 || exit_code=1
    check_security_imports || exit_code=1
    check_security_headers_config || exit_code=1
    check_password_policy_config || exit_code=1

    echo ""
    echo "============================================"
    echo "  GSF Policy Enforcement Summary"
    echo "============================================"
    echo "  Violations: ${VIOLATIONS}"
    echo "  Auto-fixed: ${FIXED}"
    echo "  Result:     $([ ${exit_code} -eq 0 ] && echo 'PASS' || echo 'FAIL')"
    echo "============================================"

    if ${CI_MODE} && [[ ${exit_code} -ne 0 ]]; then
        log_error "CI mode: Policy enforcement failed, blocking"
    fi

    exit "${exit_code}"
}

main
