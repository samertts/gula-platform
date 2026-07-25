#!/usr/bin/env bash
# =============================================================================
# GSF: generate-sbom.sh — Software Bill of Materials Generator
# =============================================================================
# Generates SBOM for containers (Syft), Python dependencies (pip-audit), and
# the full project. Supports CycloneDX and SPDX formats. Signs SBOM with
# Cosign if available.
#
# Usage:
#   ./generate-sbom.sh [options]
#
# Options:
#   --format FORMAT    Output format: cyclonedx, spdx, both [default: both]
#   --image IMAGE      Container image to scan (optional)
#   --output DIR       Output directory [default: security/reports/sbom]
#   --sign             Sign SBOM with Cosign
#   --help, -h         Show this help message
#
# Dependencies:
#   - syft (optional, for container SBOM)
#   - pip-audit (optional, for Python deps)
#   - cosign (optional, for signing)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/security/reports/sbom"
SBOM_FORMAT="both"
CONTAINER_IMAGE=""
DO_SIGN=false
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")

usage() {
    sed -n '/^# ============/,/^# ============/p' "${BASH_SOURCE[0]}" | \
        grep -v '^# ============' | sed 's/^# //'
    exit 0
}

log_info()  { echo "[INFO]  $*" >&2; }
log_warn()  { echo "[WARN]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_pass()  { echo "[PASS]  $*" >&2; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --format)
            SBOM_FORMAT="$2"
            shift
            ;;
        --image)
            CONTAINER_IMAGE="$2"
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift
            ;;
        --sign) DO_SIGN=true ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
done

mkdir -p "${OUTPUT_DIR}"

generate_python_sbom() {
    log_info "Generating Python dependency SBOM..."
    local format="$1"
    local ext
    case "${format}" in
        cyclonedx) ext="cyclonedx.json" ;;
        spdx) ext="spdx.json" ;;
    esac
    local output="${OUTPUT_DIR}/python-deps-${format}-${TIMESTAMP}.${ext}"

    if command -v pip-audit &>/dev/null; then
        pip-audit --local --format "${format}" --output "${output}" 2>/dev/null && {
            log_pass "Python SBOM (${format}) generated: ${output}"
            return 0
        }
        log_warn "pip-audit failed for ${format}"
    else
        log_warn "pip-audit not installed, generating using pip list..."
        pip list --format=json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
sbom = {
    'bomFormat': 'CycloneDX',
    'specVersion': '1.5',
    'version': 1,
    'metadata': {'timestamp': '${TIMESTAMP}', 'tools': [{'name': 'pip'}]},
    'components': [
        {'name': pkg['name'], 'version': pkg['version'], 'type': 'library', 'purl': f'pkg:pypi/{pkg[\"name\"]}@{pkg[\"version\"]}'}
        for pkg in data
    ]
}
with open('${output}', 'w') as f:
    json.dump(sbom, f, indent=2)
print(f'Generated {len(data)} components')
" && log_pass "Python SBOM generated via pip: ${output}"
    fi
}

generate_container_sbom() {
    [[ -z "${CONTAINER_IMAGE}" ]] && return 0
    log_info "Generating container SBOM for: ${CONTAINER_IMAGE}"

    if ! command -v syft &>/dev/null; then
        log_warn "Syft not installed, skipping container SBOM"
        return 0
    fi

    for format in cyclonedx spdx; do
        local ext
        case "${format}" in
            cyclonedx) ext="cyclonedx.json" ;;
            spdx) ext="spdx.json" ;;
        esac
        local output="${OUTPUT_DIR}/container-${CONTAINER_IMAGE##*/}-${format}-${TIMESTAMP}.${ext}"
        syft "${CONTAINER_IMAGE}" --output "${format}=${output}" 2>/dev/null && {
            log_pass "Container SBOM (${format}) generated: ${output}"
        } || log_warn "Syft failed for ${format}"
    done
}

generate_full_project_sbom() {
    log_info "Generating full project SBOM..."
    if command -v syft &>/dev/null; then
        local output="${OUTPUT_DIR}/project-cyclonedx-${TIMESTAMP}.cyclonedx.json"
        syft dir:"${PROJECT_ROOT}" --output cyclonedx-json="${output}" 2>/dev/null && {
            log_pass "Project SBOM generated: ${output}"
        } || log_warn "Syft project scan failed"
    else
        log_warn "Syft not installed, project-level SBOM skipped"
    fi
}

sign_sbom() {
    ${DO_SIGN} || return 0
    if ! command -v cosign &>/dev/null; then
        log_warn "Cosign not installed, skipping SBOM signing"
        return 0
    fi
    log_info "Signing SBOM files with Cosign..."
    for sbom in "${OUTPUT_DIR}"/*-"${TIMESTAMP}".*; do
        [[ -f "${sbom}" ]] || continue
        cosign sign-blob --key "cosign.key" "${sbom}" 2>/dev/null && {
            log_pass "Signed: ${sbom}"
        } || log_warn "Failed to sign: ${sbom}"
    done
}

main() {
    log_info "Starting SBOM generation"
    log_info "Output directory: ${OUTPUT_DIR}"
    log_info "Format: ${SBOM_FORMAT}"

    case "${SBOM_FORMAT}" in
        both)
            generate_python_sbom "cyclonedx"
            generate_python_sbom "spdx"
            ;;
        cyclonedx)
            generate_python_sbom "cyclonedx"
            ;;
        spdx)
            generate_python_sbom "spdx"
            ;;
    esac

    if [[ -n "${CONTAINER_IMAGE}" ]]; then
        generate_container_sbom
    fi

    generate_full_project_sbom
    sign_sbom

    log_info "SBOM generation complete. Files in: ${OUTPUT_DIR}"
    ls -lh "${OUTPUT_DIR}" | grep "${TIMESTAMP}" || true
}

main
