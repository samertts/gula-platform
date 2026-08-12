#!/usr/bin/env bash
# =============================================================================
# SBOM Validation Script — GULA Platform
# =============================================================================
# Path: scripts/validate-sbom.sh
# Managed by: Security Operations
# Usage:
#   ./validate-sbom.sh --sbom sbom-python-v2.1.0.json
#   ./validate-sbom.sh --all
#   ./validate-sbom.sh --license sbom-python-v2.1.0.json
#   ./validate-sbom.sh --completeness
#
# This script validates SBOM files for:
#   - License compliance (check against allowlist/blocklist)
#   - Completeness (vs installed packages)
#   - Package integrity
# =============================================================================

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly TIMESTAMP="$(date '+%Y-%m-%d_%H%M%S')"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly SBOM_DIR="${SBOM_DIR:-${REPO_ROOT}/reports/sbom}"
readonly REPORT_DIR="${REPORT_DIR:-${REPO_ROOT}/reports/sbom-validation}"
mkdir -p "${REPORT_DIR}"

# License configuration
readonly LICENSE_CONFIG="${LICENSE_CONFIG:-${REPO_ROOT}/config/security/license-config.yml}"

# ==============================================================================
# LICENSE ALLOWLIST / BLOCKLIST
# ==============================================================================
# These are parsed from license-config.yml. For direct use without parsing:
ALLOWED_LICENSES=(
  "MIT" "Apache-2.0" "Apache 2.0" "BSD" "BSD-2-Clause" "BSD-3-Clause"
  "ISC" "Python-2.0" "MPL-2.0" "LGPL-2.1" "LGPL-3.0" "LGPL-2.1-only"
  "LGPL-2.1+" "LGPL-3.0-only" "LGPL-3.0+" "Unlicense" "CC0-1.0"
  "Zlib" "PSF" "Curl" "MIT License" "The MIT License"
  "Apache Software License" "Apache License 2.0" "Apache-2.0"
)

CONDITIONAL_LICENSES=(
  "LGPL-2.1" "LGPL-2.1-only" "LGPL-2.1+"
  "CC-BY-4.0" "CC-BY-3.0" "CC-BY-2.0"
)

BLOCKED_LICENSES=(
  "GPL" "GPL-2.0" "GPL-2.0-only" "GPL-2.0+" "GPL-2.0-or-later"
  "GPL-3.0" "GPL-3.0-only" "GPL-3.0+" "GPL-3.0-or-later"
  "AGPL" "AGPL-3.0" "AGPL-3.0-only" "AGPL-3.0-or-later"
  "BUSL-1.1" "SSPL-1.0" "BSL-1.0"
  "GNU General Public License" "GNU Affero General Public License"
)

# ==============================================================================
# LOGGING
# ==============================================================================
log_info()   { echo "[${TIMESTAMP}] [INFO] ${SCRIPT_NAME}: $*"; }
log_warn()   { echo "[${TIMESTAMP}] [WARN] ${SCRIPT_NAME}: $*" >&2; }
log_error()  { echo "[${TIMESTAMP}] [ERROR] ${SCRIPT_NAME}: $*" >&2; }
log_pass()   { echo "[${TIMESTAMP}] [PASS] ${SCRIPT_NAME}: $*"; }
log_fail()   { echo "[${TIMESTAMP}] [FAIL] ${SCRIPT_NAME}: $*"; }

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

check_prerequisites() {
  local missing=0
  for tool in jq python3; do
    if ! command -v "${tool}" &>/dev/null; then
      log_error "Required tool not found: ${tool}"
      missing=1
    fi
  done
  return "${missing}"
}

normalize_license() {
  local license="$1"
  # Normalize common license name variants
  case "${license}" in
    *"MIT"*) echo "MIT" ;;
    *"Apache"*"2"*) echo "Apache-2.0" ;;
    *"Apache"*) echo "Apache-2.0" ;;
    *"BSD"*) echo "BSD-3-Clause" ;;
    *"Python"*) echo "Python-2.0" ;;
    *"LGPL"*"2.1"*) echo "LGPL-2.1" ;;
    *"LGPL"*"3"*) echo "LGPL-3.0" ;;
    *"GPL"*"2"*) echo "GPL-2.0" ;;
    *"GPL"*"3"*) echo "GPL-3.0" ;;
    *"GPL"*) echo "GPL" ;;
    *"AGPL"*) echo "AGPL-3.0" ;;
    *"MPL"*) echo "MPL-2.0" ;;
    *"ISC"*) echo "ISC" ;;
    *"Unlicense"*) echo "Unlicense" ;;
    *"CC0"*) echo "CC0-1.0" ;;
    *"Zlib"*) echo "Zlib" ;;
    *"PSF"*) echo "PSF" ;;
    *"Curl"*) echo "Curl" ;;
    *"BUSL"*) echo "BUSL-1.1" ;;
    *"SSPL"*) echo "SSPL-1.0" ;;
    *"BSL"*) echo "BSL-1.0" ;;
    *) echo "${license}" ;;
  esac
}

# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

validate_licenses() {
  local sbom_file="$1"

  log_info "Validating licenses in: ${sbom_file}"
  local report_file="${REPORT_DIR}/license-validation-$(basename "${sbom_file}" .json).txt"

  local blocked_found=0
  local conditional_found=0
  local unknown_found=0
  local allowed_found=0
  local total=0

  {
    echo "License Validation Report"
    echo "=========================="
    echo "SBOM: ${sbom_file}"
    echo "Date: ${TIMESTAMP}"
    echo ""
    echo "Package License Validation Results:"
    echo "-----------------------------------"
  } > "${report_file}"

  # Process each component in the SBOM
  while read -r component; do
    local name version license
    name=$(echo "${component}" | jq -r '.name // "unknown"')
    version=$(echo "${component}" | jq -r '.version // "unknown"')

    # Try different SBOM formats
    license=$(echo "${component}" | jq -r '.license // .licenses[0].license.name // .licenses[0].license.id // "Unknown"')

    local normalized_license
    normalized_license=$(normalize_license "${license}")
    total=$((total + 1))

    # Check against blocklist
    local blocked=false
    for bl in "${BLOCKED_LICENSES[@]}"; do
      if [[ "${normalized_license}" == "${bl}"* ]]; then
        blocked=true
        break
      fi
    done

    if [[ "${blocked}" == true ]]; then
      blocked_found=$((blocked_found + 1))
      echo "  BLOCKED: ${name}@${version} (${license})" >> "${report_file}"
      log_fail "BLOCKED LICENSE: ${name}@${version} — ${license}"
      continue
    fi

    # Check against conditional list
    local conditional=false
    for cl in "${CONDITIONAL_LICENSES[@]}"; do
      if [[ "${normalized_license}" == "${cl}"* ]]; then
        conditional=true
        break
      fi
    done

    if [[ "${conditional}" == true ]]; then
      conditional_found=$((conditional_found + 1))
      echo "  CONDITIONAL: ${name}@${version} (${license})" >> "${report_file}"
      log_warn "CONDITIONAL LICENSE: ${name}@${version} — ${license}"
      continue
    fi

    # Check against allowlist
    local allowed=false
    for al in "${ALLOWED_LICENSES[@]}"; do
      if [[ "${normalized_license}" == "${al}"* ]]; then
        allowed=true
        break
      fi
    done

    if [[ "${allowed}" == true ]]; then
      allowed_found=$((allowed_found + 1))
      echo "  ALLOWED: ${name}@${version} (${license})" >> "${report_file}"
    else
      unknown_found=$((unknown_found + 1))
      echo "  UNKNOWN: ${name}@${version} (${license})" >> "${report_file}"
      log_warn "UNKNOWN LICENSE: ${name}@${version} — ${license}"
    fi
  done < <(jq -c '.components[]?' "${sbom_file}" 2>/dev/null || jq -c '.packages[]?' "${sbom_file}" 2>/dev/null || echo "[]")

  {
    echo ""
    echo "Summary:"
    echo "--------"
    echo "Total packages: ${total}"
    echo "  Allowed:     ${allowed_found}"
    echo "  Conditional: ${conditional_found}"
    echo "  Unknown:     ${unknown_found}"
    echo "  Blocked:     ${blocked_found}"
    echo ""
    if [[ ${blocked_found} -gt 0 ]]; then
      echo "RESULT: FAILED — ${blocked_found} blocked license(s) found"
    elif [[ ${conditional_found} -gt 0 ]]; then
      echo "RESULT: WARNING — ${conditional_found} conditional license(s) found"
    else
      echo "RESULT: PASSED — All licenses are allowed"
    fi
  } >> "${report_file}"

  cat "${report_file}"
  log_info "License validation report: ${report_file}"

  # Return 1 if blocked licenses found
  [[ ${blocked_found} -eq 0 ]]
}

validate_completeness() {
  log_info "Validating SBOM completeness..."
  local errors=0

  # For Python SBOM: compare SBOM packages with installed packages
  if [[ -f "${SBOM_DIR}/sbom-python-"*".json" ]]; then
    local sbom_file
    sbom_file=$(ls "${SBOM_DIR}/sbom-python-"*".json" 2>/dev/null | head -1)
    if [[ -n "${sbom_file}" ]]; then
      log_info "Comparing Python SBOM with installed packages..."

      python3 -c "
import json, subprocess, sys

# Load SBOM
with open('${sbom_file}') as f:
    sbom = json.load(f)

# Get installed packages
result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                       capture_output=True, text=True)
installed = json.loads(result.stdout)
installed_map = {p['name'].lower(): p['version'] for p in installed}

# Get SBOM packages
if 'components' in sbom:
    sbom_packages = {p['name'].lower(): p.get('version', '') for p in sbom['components']}
elif 'packages' in sbom:
    sbom_packages = {p['name'].lower(): p.get('versionInfo', '') for p in sbom['packages']}
else:
    sbom_packages = {}

# Find missing packages
missing_in_sbom = []
for name, version in installed_map.items():
    if name not in sbom_packages and name != 'pip' and name != 'setuptools':
        missing_in_sbom.append(f'{name}=={version}')

extra_in_sbom = []
for name, version in sbom_packages.items():
    if name not in installed_map and name != 'pip' and name != 'setuptools':
        extra_in_sbom.append(f'{name}=={version}')

if missing_in_sbom:
    print(f'WARNING: {len(missing_in_sbom)} packages installed but not in SBOM:')
    for p in missing_in_sbom[:10]:
        print(f'  {p}')
    if len(missing_in_sbom) > 10:
        print(f'  ... and {len(missing_in_sbom) - 10} more')

if extra_in_sbom:
    print(f'INFO: {len(extra_in_sbom)} packages in SBOM but not installed:')
    for p in extra_in_sbom[:5]:
        print(f'  {p}')

if not missing_in_sbom:
    print('PASS: All installed packages are in SBOM')
else:
    print(f'FAIL: {len(missing_in_sbom)} package(s) missing from SBOM')
    sys.exit(1)
" 2>&1 || errors=$((errors + 1))
    fi
  fi

  if [[ ${errors} -eq 0 ]]; then
    log_pass "Completeness validation PASSED"
    return 0
  else
    log_fail "Completeness validation found ${errors} issue(s)"
    return 1
  fi
}

validate_all() {
  log_info "=== Full SBOM Validation ==="
  local exit_code=0

  # Find all SBOM files
  local sbom_files=()
  while IFS= read -r f; do
    sbom_files+=("${f}")
  done < <(find "${SBOM_DIR}" -name "sbom-*.json" ! -name "sbom-summary*" 2>/dev/null || true)

  if [[ ${#sbom_files[@]} -eq 0 ]]; then
    log_error "No SBOM files found in ${SBOM_DIR}"
    log_error "Run scripts/generate-sbom.sh first"
    return 1
  fi

  # Validate each SBOM
  for sbom in "${sbom_files[@]}"; do
    if [[ ! -f "${sbom}" ]]; then
      log_warn "SBOM file not found: ${sbom}"
      exit_code=1
      continue
    fi

    log_info "Validating: ${sbom}"

    # License validation
    if ! validate_licenses "${sbom}"; then
      log_fail "License validation FAILED for ${sbom}"
      exit_code=1
    else
      log_pass "License validation PASSED for ${sbom}"
    fi
  done

  # Completeness validation (Python only)
  if ! validate_completeness; then
    exit_code=1
  fi

  # Generate compliance report
  generate_compliance_report

  return "${exit_code}"
}

generate_compliance_report() {
  local report_file="${REPORT_DIR}/sbom-compliance-report-${TIMESTAMP}.md"

  log_info "Generating compliance report: ${report_file}"

  {
    echo "# GULA Platform SBOM Compliance Report"
    echo ""
    echo "**Generated:** ${TIMESTAMP}"
    echo "**Project:** GULA Platform (gula-platform)"
    echo ""
    echo "## Validation Summary"
    echo ""
    echo "| SBOM File | Packages | Status |"
    echo "|-----------|----------|--------|"

    for f in "${SBOM_DIR}/sbom-"*".json"; do
      if [[ -f "${f}" && "${f}" != *"summary"* ]]; then
        local name
        name=$(basename "${f}")
        local count
        count=$(jq '.components | length // .packages | length // 0' "${f}" 2>/dev/null || echo "?")
        local status
        if grep -q "FAILED" "${REPORT_DIR}/license-validation-${name}.txt" 2>/dev/null; then
          status="❌ FAILED"
        elif grep -q "WARNING" "${REPORT_DIR}/license-validation-${name}.txt" 2>/dev/null; then
          status="⚠️ WARNING"
        else
          status="✅ PASSED"
        fi
        echo "| ${name} | ${count} | ${status} |"
      fi
    done

    echo ""
    echo "## License Summary"
    echo ""
    echo "| Category | Count |"
    echo "|----------|-------|"

    local allowed=0
    local conditional=0
    local unknown=0
    local blocked=0

    for f in "${REPORT_DIR}/license-validation-"*".txt"; do
      [[ -f "${f}" ]] || continue
      local a c u b
      a=$(grep "Allowed:" "${f}" | awk '{print $2}' | tr -d ' ')
      c=$(grep "Conditional:" "${f}" | awk '{print $2}' | tr -d ' ')
      u=$(grep "Unknown:" "${f}" | awk '{print $2}' | tr -d ' ')
      b=$(grep "Blocked:" "${f}" | awk '{print $2}' | tr -d ' ')
      allowed=$((allowed + (a == "" ? 0 : a)))
      conditional=$((conditional + (c == "" ? 0 : c)))
      unknown=$((unknown + (u == "" ? 0 : u)))
      blocked=$((blocked + (b == "" ? 0 : b)))
    done

    echo "| Allowed | ${allowed} |"
    echo "| Conditional | ${conditional} |"
    echo "| Unknown | ${unknown} |"
    echo "| Blocked | ${blocked} |"
    echo ""

    if [[ ${blocked} -gt 0 ]]; then
      echo "## ❌ Blocked Licenses Found"
      echo ""
      echo "The following blocked licenses were detected. These packages must be removed or replaced:"
      echo ""
      for f in "${REPORT_DIR}/license-validation-"*".txt"; do
        [[ -f "${f}" ]] || continue
        grep "BLOCKED:" "${f}" || true
      done | while IFS= read -r line; do
        echo "- ${line##*BLOCKED: }"
      done
      echo ""
    fi

    if [[ ${unknown} -gt 0 ]]; then
      echo "## ⚠️ Unknown Licenses"
      echo ""
      echo "The following packages have unknown licenses and need manual review:"
      echo ""
      for f in "${REPORT_DIR}/license-validation-"*".txt"; do
        [[ -f "${f}" ]] || continue
        grep "UNKNOWN:" "${f}" || true
      done | while IFS= read -r line; do
        echo "- ${line##*UNKNOWN: }"
      done
      echo ""
    fi

    echo "## Overall Result"
    echo ""
    if [[ ${blocked} -gt 0 ]]; then
      echo "**FAILED** — Blocked licenses found. Resolve before proceeding."
    elif [[ ${unknown} -gt 0 ]] || [[ ${conditional} -gt 0 ]]; then
      echo "**WARNING** — Review required for conditional/unknown licenses."
    else
      echo "**PASSED** — All licenses comply with GULA policy."
    fi
  } > "${report_file}"

  log_info "Compliance report generated: ${report_file}"
}

# ==============================================================================
# MAIN
# ==============================================================================

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS]

Validate SBOM files for license compliance and completeness.

Options:
  --license <file>    Validate licenses in a specific SBOM file
  --completeness      Validate SBOM completeness vs installed packages
  --all               Run all validations
  --help              Show this help message

Examples:
  ${SCRIPT_NAME} --all
  ${SCRIPT_NAME} --license reports/sbom/sbom-python-v2.1.0.json
  ${SCRIPT_NAME} --license sbom.json --completeness
EOF
  exit 0
}

main() {
  local do_all=false
  local do_license=""
  local do_completeness=false

  if [[ $# -eq 0 ]]; then
    do_all=true
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --license)
        shift
        do_license="$1"
        ;;
      --completeness) do_completeness=true ;;
      --all) do_all=true ;;
      --help) usage ;;
      *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
  done

  log_info "=== GULA Platform SBOM Validation ==="

  check_prerequisites || exit 1

  local exit_code=0

  if [[ "${do_all}" == true ]]; then
    validate_all || exit_code=$?
  else
    if [[ -n "${do_license}" ]]; then
      if [[ -f "${do_license}" ]]; then
        validate_licenses "${do_license}" || exit_code=$?
      else
        log_error "SBOM file not found: ${do_license}"
        exit_code=1
      fi
    fi

    if [[ "${do_completeness}" == true ]]; then
      validate_completeness || exit_code=$?
    fi

    generate_compliance_report
  fi

  if [[ ${exit_code} -eq 0 ]]; then
    log_pass "SBOM validation PASSED"
  else
    log_fail "SBOM validation FAILED — review reports in ${REPORT_DIR}"
  fi

  exit "${exit_code}"
}

main "$@"
