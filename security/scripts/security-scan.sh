#!/usr/bin/env bash
# =============================================================================
# GSF: security-scan.sh — Comprehensive Security Scan
# =============================================================================
# Runs multiple security scanning tools and generates an aggregated report.
# Each tool is optional; missing tools are skipped with a warning.
#
# Usage:
#   ./security-scan.sh [options]
#
# Options:
#   --path PATH          Path to scan (default: repository root)
#   --sarif-dir DIR      Output directory for SARIF reports (default: security/reports/sarif)
#   --skip TOOL          Skip a specific tool (can be repeated)
#   --fail-on SEVERITY   Exit code severity threshold (critical, high, medium, low, never)
#   --help, -h           Show this help message
#
# Tools:
#   bandit, semgrep, trivy, checkov, gitleaks, pip-audit
#
# Exit codes:
#   0   All scans passed quality gate
#   1   Quality gate failed (findings above threshold)
#   2   Error during scanning
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCAN_PATH="${PROJECT_ROOT}"
SARIF_DIR="${PROJECT_ROOT}/security/reports/sarif"
FAIL_ON_SEVERITY="high"
SKIP_TOOLS=()
EXIT_CODE=0
FINDINGS_CRITICAL=0
FINDINGS_HIGH=0
FINDINGS_MEDIUM=0
FINDINGS_LOW=0

usage() {
    sed -n '/^# ============/,/^# ============/p' "${BASH_SOURCE[0]}" | \
        grep -v '^# ============' | sed 's/^# //'
    exit 0
}

log_info()  { echo "[INFO]  $*" >&2; }
log_warn()  { echo "[WARN]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_pass()  { echo "[PASS]  $*" >&2; }
log_fail()  { echo "[FAIL]  $*" >&2; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --path) SCAN_PATH="$2"; shift ;;
        --sarif-dir) SARIF_DIR="$2"; shift ;;
        --skip) SKIP_TOOLS+=("$2"); shift ;;
        --fail-on) FAIL_ON_SEVERITY="$2"; shift ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
done

mkdir -p "${SARIF_DIR}"
SCAN_TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
AGGREGATED_REPORT="${SARIF_DIR}/aggregated-report-${SCAN_TIMESTAMP}.json"

should_skip() {
    local tool="$1"
    for s in "${SKIP_TOOLS[@]}"; do
        [[ "${s}" == "${tool}" ]] && return 0
    done
    return 1
}

check_tool() {
    command -v "$1" &>/dev/null
}

run_bandit() {
    local tool="bandit"
    should_skip "${tool}" && { log_info "Skipping ${tool}"; return 0; }
    check_tool "${tool}" || { log_warn "${tool} not installed, skipping"; SKIP_TOOLS+=("${tool}"); return 0; }
    log_info "Running bandit SAST scan..."
    local report="${SARIF_DIR}/bandit-${SCAN_TIMESTAMP}.sarif"
    bandit --quiet --recursive --format sarif \
        --output "${report}" \
        "${SCAN_PATH}" 2>/dev/null || true
    if [[ -f "${report}" ]]; then
        local count
        count=$(python3 -c "import json; r=json.load(open('${report}')); print(len(r.get('runs',[{}])[0].get('results',[])));" 2>/dev/null || echo "0")
        log_info "bandit: ${count} findings"
    fi
}

run_semgrep() {
    local tool="semgrep"
    should_skip "${tool}" && { log_info "Skipping ${tool}"; return 0; }
    check_tool "${tool}" || { log_warn "${tool} not installed, skipping"; SKIP_TOOLS+=("${tool}"); return 0; }
    log_info "Running semgrep scan..."
    local report="${SARIF_DIR}/semgrep-${SCAN_TIMESTAMP}.sarif"
    semgrep --sarif --output="${report}" \
        --config=auto \
        "${SCAN_PATH}" 2>/dev/null || true
    if [[ -f "${report}" ]]; then
        local count
        count=$(python3 -c "import json; r=json.load(open('${report}')); print(len(r.get('runs',[{}])[0].get('results',[])));" 2>/dev/null || echo "0")
        log_info "semgrep: ${count} findings"
    fi
}

run_trivy() {
    local tool="trivy"
    should_skip "${tool}" && { log_info "Skipping ${tool}"; return 0; }
    check_tool "${tool}" || { log_warn "${tool} not installed, skipping"; SKIP_TOOLS+=("${tool}"); return 0; }
    log_info "Running trivy filesystem scan..."
    local report="${SARIF_DIR}/trivy-${SCAN_TIMESTAMP}.sarif"
    trivy fs --format sarif --output "${report}" \
        --severity CRITICAL,HIGH,MEDIUM \
        --scanners vuln,secret,misconfig \
        "${SCAN_PATH}" 2>/dev/null || true
    if [[ -f "${report}" ]]; then
        local count
        count=$(python3 -c "import json; r=json.load(open('${report}')); print(len(r.get('runs',[{}])[0].get('results',[])));" 2>/dev/null || echo "0")
        log_info "trivy: ${count} findings"
    fi
}

run_checkov() {
    local tool="checkov"
    should_skip "${tool}" && { log_info "Skipping ${tool}"; return 0; }
    check_tool "${tool}" || { log_warn "${tool} not installed, skipping"; SKIP_TOOLS+=("${tool}"); return 0; }
    log_info "Running checkov IaC scan..."
    local report="${SARIF_DIR}/checkov-${SCAN_TIMESTAMP}.sarif"
    checkov --directory "${SCAN_PATH}" \
        --output sarif \
        --output-file-path "${report}" \
        --framework terraform,kubernetes,dockerfile,github_actions 2>/dev/null || true
    if [[ -f "${report}" ]]; then
        local count
        count=$(python3 -c "import json; r=json.load(open('${report}')); print(len(r.get('runs',[{}])[0].get('results',[])));" 2>/dev/null || echo "0")
        log_info "checkov: ${count} findings"
    fi
}

run_gitleaks() {
    local tool="gitleaks"
    should_skip "${tool}" && { log_info "Skipping ${tool}"; return 0; }
    check_tool "${tool}" || { log_warn "${tool} not installed, skipping"; SKIP_TOOLS+=("${tool}"); return 0; }
    log_info "Running gitleaks secret scan..."
    local report="${SARIF_DIR}/gitleaks-${SCAN_TIMESTAMP}.sarif"
    gitleaks detect --source "${SCAN_PATH}" \
        --report-format sarif \
        --report-path "${report}" \
        --no-git --verbose 2>/dev/null || true
    if [[ -f "${report}" ]]; then
        local count
        count=$(python3 -c "import json; r=json.load(open('${report}')); print(len(r.get('runs',[{}])[0].get('results',[])));" 2>/dev/null || echo "0")
        log_info "gitleaks: ${count} findings"
    fi
}

run_pip_audit() {
    local tool="pip-audit"
    should_skip "${tool}" && { log_info "Skipping ${tool}"; return 0; }
    check_tool "${tool}" || { log_warn "${tool} not installed, skipping"; SKIP_TOOLS+=("${tool}"); return 0; }
    log_info "Running pip-audit on Python dependencies..."
    local report="${SARIF_DIR}/pip-audit-${SCAN_TIMESTAMP}.sarif"
    pip-audit --local --format sarif \
        --output "${report}" 2>/dev/null || true
    if [[ -f "${report}" ]]; then
        local count
        count=$(python3 -c "import json; r=json.load(open('${report}')); print(len(r.get('runs',[{}])[0].get('results',[])));" 2>/dev/null || echo "0")
        log_info "pip-audit: ${count} findings"
    fi
}

count_findings() {
    local sarif_file="$1"
    if [[ ! -f "${sarif_file}" ]]; then
        return
    fi
    python3 -c "
import json
with open('${sarif_file}') as f:
    r = json.load(f)
total = 0
crit = 0
high = 0
med = 0
low = 0
for run in r.get('runs', []):
    for result in run.get('results', []):
        total += 1
        level = result.get('level', 'warning')
        if level == 'error':
            crit += 1
        elif level == 'warning':
            high += 1
        elif level == 'note':
            med += 1
        else:
            low += 1
print(f'{total} {crit} {high} {med} {low}')
" 2>/dev/null || echo "0 0 0 0 0"
}

generate_aggregated_report() {
    log_info "Generating aggregated SARIF report..."
    local report_files
    report_files=$(find "${SARIF_DIR}" -name "*-${SCAN_TIMESTAMP}.sarif" 2>/dev/null || true)
    python3 -c "
import json, glob, os
sarif_dir = '${SARIF_DIR}'
timestamp = '${SCAN_TIMESTAMP}'
aggregated = {
    '\$schema': 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/Schemata/sarif-schema-2.1.0.json',
    'version': '2.1.0',
    'runs': [],
}
for f in sorted(glob.glob(os.path.join(sarif_dir, f'*-{timestamp}.sarif'))):
    try:
        with open(f) as fh:
            r = json.load(fh)
            aggregated['runs'].extend(r.get('runs', []))
    except Exception as e:
        print(f'Error reading {f}: {e}', file=__import__(\"sys\").stderr)
with open('${AGGREGATED_REPORT}', 'w') as f:
    json.dump(aggregated, f, indent=2)
print(f'Aggregated report written')
" 2>/dev/null || log_warn "Failed to generate aggregated report"
}

quality_gate() {
    local fail_severity="${FAIL_ON_SEVERITY}"
    local gate_passed=true

    log_info "Evaluating quality gate (fail-on: ${fail_severity})..."

    for f in "${SARIF_DIR}"/*-"${SCAN_TIMESTAMP}".sarif; do
        [[ -f "${f}" ]] || continue
        read -r total crit high med low <<< "$(count_findings "${f}")"
        FINDINGS_CRITICAL=$((FINDINGS_CRITICAL + crit))
        FINDINGS_HIGH=$((FINDINGS_HIGH + high))
        FINDINGS_MEDIUM=$((FINDINGS_MEDIUM + med))
        FINDINGS_LOW=$((FINDINGS_LOW + low))
    done

    log_info "Findings: CRITICAL=${FINDINGS_CRITICAL} HIGH=${FINDINGS_HIGH} MEDIUM=${FINDINGS_MEDIUM} LOW=${FINDINGS_LOW}"

    case "${fail_severity}" in
        critical)
            [[ ${FINDINGS_CRITICAL} -gt 0 ]] && gate_passed=false
            ;;
        high)
            [[ ${FINDINGS_CRITICAL} -gt 0 || ${FINDINGS_HIGH} -gt 0 ]] && gate_passed=false
            ;;
        medium)
            [[ ${FINDINGS_CRITICAL} -gt 0 || ${FINDINGS_HIGH} -gt 0 || ${FINDINGS_MEDIUM} -gt 0 ]] && gate_passed=false
            ;;
        low)
            [[ ${FINDINGS_CRITICAL} -gt 0 || ${FINDINGS_HIGH} -gt 0 || ${FINDINGS_MEDIUM} -gt 0 || ${FINDINGS_LOW} -gt 0 ]] && gate_passed=false
            ;;
        never)
            gate_passed=true
            ;;
    esac

    if ${gate_passed}; then
        log_pass "Quality gate PASSED"
        return 0
    else
        log_fail "Quality gate FAILED (severity threshold: ${fail_severity})"
        return 1
    fi
}

main() {
    log_info "Starting comprehensive security scan of: ${SCAN_PATH}"
    log_info "SARIF output: ${SARIF_DIR}"
    log_info "Fail-on severity: ${FAIL_ON_SEVERITY}"

    run_bandit
    run_semgrep
    run_trivy
    run_checkov
    run_gitleaks
    run_pip_audit

    generate_aggregated_report

    if quality_gate; then
        log_pass "Security scan PASSED all checks"
        EXIT_CODE=0
    else
        log_fail "Security scan FAILED quality gate"
        EXIT_CODE=1
    fi

    log_info "Scan complete. Aggregated report: ${AGGREGATED_REPORT}"
    exit "${EXIT_CODE}"
}

main
