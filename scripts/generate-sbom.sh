#!/usr/bin/env bash
# =============================================================================
# SBOM Generation Script — GULA Platform
# =============================================================================
# Path: scripts/generate-sbom.sh
# Managed by: Security Operations
# Usage:
#   ./generate-sbom.sh                    # Generate SBOM for all components
#   ./generate-sbom.sh --python           # Python dependencies only
#   ./generate-sbom.sh --node             # Node.js dependencies only
#   ./generate-sbom.sh --container        # Container image only
#   ./generate-sbom.sh --all --publish    # Generate and publish to artifact store
#   ./generate-sbom.sh --verify           # Verify SBOM completeness
#
# Dependencies: pip-licenses, cyclonedx-npm, syft, jq
# =============================================================================

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly TIMESTAMP="$(date '+%Y-%m-%d_%H%M%S')"
readonly VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo 'unknown')}"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Output directory
readonly SBOM_DIR="${SBOM_DIR:-${REPO_ROOT}/reports/sbom}"
mkdir -p "${SBOM_DIR}"

# Container image
readonly CONTAINER_IMAGE="${CONTAINER_IMAGE:-ghcr.io/samertts/gula-platform/backend:latest}"

# Artifact store configuration
readonly ARTIFACT_STORE_URL="${ARTIFACT_STORE_URL:-}"
readonly ARTIFACT_STORE_TOKEN="${ARTIFACT_STORE_TOKEN:-}"

# ==============================================================================
# LOGGING
# ==============================================================================
log_info()  { echo "[${TIMESTAMP}] [INFO] ${SCRIPT_NAME}: $*"; }
log_warn()  { echo "[${TIMESTAMP}] [WARN] ${SCRIPT_NAME}: $*" >&2; }
log_error() { echo "[${TIMESTAMP}] [ERROR] ${SCRIPT_NAME}: $*" >&2; }

# ==============================================================================
# TOOL CHECKS
# ==============================================================================

check_prerequisites() {
  local missing=0

  for tool in jq pip3 npm syft; do
    if ! command -v "${tool}" &>/dev/null; then
      log_error "Required tool not found: ${tool}"
      missing=1
    fi
  done

  # pip-licenses is optional but recommended
  if ! python3 -m pip_licenses --version &>/dev/null; then
    log_warn "pip-licenses not installed. Python SBOM will use pip list instead."
  fi

  # cyclonedx-npm is optional but recommended
  if ! npx --yes cyclonedx-npm --version &>/dev/null 2>&1; then
    log_warn "cyclonedx-npm not available. Node SBOM will use npm list instead."
  fi

  return "${missing}"
}

# ==============================================================================
# SBOM GENERATION FUNCTIONS
# ==============================================================================

generate_python_sbom() {
  log_info "Generating Python dependency SBOM..."

  local python_sbom="${SBOM_DIR}/sbom-python-${VERSION}.json"

  if python3 -m pip_licenses --format=json &>/dev/null; then
    python3 -m pip_licenses \
      --format=json \
      --with-authors \
      --with-urls \
      --with-description \
      --with-system \
      2>/dev/null > "${python_sbom}" || {
        log_warn "pip-licenses failed, falling back to pip list"
        python3 -c "
import json, subprocess, sys
result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], capture_output=True, text=True)
packages = json.loads(result.stdout)
sbom = {
  'bomFormat': 'CycloneDX',
  'specVersion': '1.4',
  'version': 1,
  'metadata': {
    'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'component': {
      'name': 'gula-platform-backend',
      'version': '${VERSION}',
      'type': 'application'
    }
  },
  'components': [{'name': p['name'], 'version': p['version'], 'type': 'library'} for p in packages]
}
with open('${python_sbom}', 'w') as f:
    json.dump(sbom, f, indent=2)
" 2>/dev/null || log_error "Failed to generate Python SBOM"
      }
  else
    log_error "pip-licenses not installed. Install with: pip install pip-licenses"
    log_info "Falling back to pip list..."
    python3 -m pip list --format=json 2>/dev/null > "${python_sbom}" || true
  fi

  # Add CycloneDX format metadata if missing
  if [[ -f "${python_sbom}" ]]; then
    local pkg_count
    pkg_count=$(jq '.components | length' "${python_sbom}" 2>/dev/null || jq 'length' "${python_sbom}" 2>/dev/null || echo "unknown")
    local sbom_size
    sbom_size=$(wc -c < "${python_sbom}")
    log_info "Python SBOM: ${python_sbom} (${pkg_count} packages, ${sbom_size} bytes)"
  else
    log_error "Python SBOM generation failed"
    return 1
  fi
}

generate_node_sbom() {
  log_info "Generating Node.js dependency SBOM..."

  local node_sbom="${SBOM_DIR}/sbom-node-${VERSION}.json"
  local node_sbom_legacy="${SBOM_DIR}/sbom-node-legacy-${VERSION}.json"

  # Frontend-v2 (main frontend)
  if [[ -f "${REPO_ROOT}/frontend-v2/package.json" ]]; then
    log_info "Scanning frontend-v2 dependencies..."
    if npx --yes cyclonedx-npm --output-file "${node_sbom}" 2>/dev/null; then
      log_info "cyclonedx-npm SBOM generated"
    else
      log_warn "cyclonedx-npm failed, using npm list"
      (cd "${REPO_ROOT}/frontend-v2" && npm list --all --json 2>/dev/null) > "${node_sbom}" || true
    fi
  fi

  # Legacy frontend
  if [[ -f "${REPO_ROOT}/package.json" ]]; then
    log_info "Scanning root (legacy frontend) dependencies..."
    if npx --yes cyclonedx-npm --output-file "${node_sbom_legacy}" 2>/dev/null; then
      log_info "Legacy frontend cyclonedx-npm SBOM generated"
    else
      (cd "${REPO_ROOT}" && npm list --all --json 2>/dev/null) > "${node_sbom_legacy}" || true
    fi
  fi

  # Report sizes
  for f in "${node_sbom}" "${node_sbom_legacy}"; do
    if [[ -f "${f}" ]]; then
      local pkg_count
      pkg_count=$(jq '.components | length' "${f}" 2>/dev/null || jq '.dependencies | length' "${f}" 2>/dev/null || echo "unknown")
      local sbom_size
      sbom_size=$(wc -c < "${f}")
      log_info "Node SBOM: ${f} (${pkg_count} packages, ${sbom_size} bytes)"
    fi
  done
}

generate_container_sbom() {
  log_info "Generating container image SBOM..."

  local container_sbom="${SBOM_DIR}/sbom-container-${VERSION}.json"

  # Try SPDX format first, fall back to CycloneDX
  if syft "${CONTAINER_IMAGE}" -o spdx-json > "${container_sbom}" 2>/dev/null; then
    log_info "Container SBOM generated (SPDX format)"
  elif syft "${CONTAINER_IMAGE}" -o cyclonedx-json > "${container_sbom}" 2>/dev/null; then
    log_info "Container SBOM generated (CycloneDX format)"
  else
    log_error "Failed to generate container SBOM. Is the image available?"
    log_error "Image: ${CONTAINER_IMAGE}"
    return 1
  fi

  local pkg_count
  pkg_count=$(jq '.packages | length' "${container_sbom}" 2>/dev/null || jq '.components | length' "${container_sbom}" 2>/dev/null || echo "unknown")
  local sbom_size
  sbom_size=$(wc -c < "${container_sbom}")
  log_info "Container SBOM: ${container_sbom} (${pkg_count} packages, ${sbom_size} bytes)"
}

generate_summary() {
  log_info "Generating SBOM summary..."

  local summary_file="${SBOM_DIR}/sbom-summary-${VERSION}.json"
  local summary
  summary=$(cat <<EOF
{
  "project": "gula-platform",
  "version": "${VERSION}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "components": {
EOF
)

  # Add Python info
  if [[ -f "${SBOM_DIR}/sbom-python-${VERSION}.json" ]]; then
    local py_count
    py_count=$(jq '.components | length' "${SBOM_DIR}/sbom-python-${VERSION}.json" 2>/dev/null || echo "0")
    summary="${summary}"$'\n'"    \"python\": ${py_count},"
  fi

  # Add Node info
  if [[ -f "${SBOM_DIR}/sbom-node-${VERSION}.json" ]]; then
    local node_count
    node_count=$(jq '.components | length' "${SBOM_DIR}/sbom-node-${VERSION}.json" 2>/dev/null || echo "0")
    summary="${summary}"$'\n'"    \"node\": ${node_count},"
  fi

  # Add Container info
  if [[ -f "${SBOM_DIR}/sbom-container-${VERSION}.json" ]]; then
    local container_count
    container_count=$(jq '.packages | length' "${SBOM_DIR}/sbom-container-${VERSION}.json" 2>/dev/null || jq '.components | length' "${SBOM_DIR}/sbom-container-${VERSION}.json" 2>/dev/null || echo "0")
    summary="${summary}"$'\n'"    \"container\": ${container_count}"
  fi

  summary="${summary}"$'\n'"  },"
  summary="${summary}"$'\n'"  \"files\": ["

  local first=true
  for f in "${SBOM_DIR}/sbom-"*"-${VERSION}.json"; do
    if [[ -f "${f}" ]]; then
      local filename
      filename=$(basename "${f}")
      local filesize
      filesize=$(wc -c < "${f}")
      if [[ "${first}" == true ]]; then
        first=false
      else
        summary="${summary},"","
      fi
      summary="${summary}"$'\n'"    {\"name\": \"${filename}\", \"size\": ${filesize}}"
    fi
  done

  summary="${summary}"$'\n'"  ]"
  summary="${summary}"$'\n'"}"
  echo "${summary}" > "${summary_file}"
  log_info "Summary: ${summary_file}"
}

archive_sbom() {
  log_info "Archiving SBOM files..."

  local archive_name="sbom-gula-platform-${VERSION}"
  local archive_dir="${SBOM_DIR}/${archive_name}"
  mkdir -p "${archive_dir}"

  # Copy all SBOM files
  cp "${SBOM_DIR}/sbom-python-${VERSION}.json" "${archive_dir}/" 2>/dev/null || true
  cp "${SBOM_DIR}/sbom-node-${VERSION}.json" "${archive_dir}/" 2>/dev/null || true
  cp "${SBOM_DIR}/sbom-node-legacy-${VERSION}.json" "${archive_dir}/" 2>/dev/null || true
  cp "${SBOM_DIR}/sbom-container-${VERSION}.json" "${archive_dir}/" 2>/dev/null || true
  cp "${SBOM_DIR}/sbom-summary-${VERSION}.json" "${archive_dir}/" 2>/dev/null || true

  # Create tar.gz archive
  (cd "${SBOM_DIR}" && tar -czf "${archive_name}.tar.gz" "${archive_name}/")

  log_info "Archive: ${SBOM_DIR}/${archive_name}.tar.gz"

  # Generate SHA256 checksum
  (cd "${SBOM_DIR}" && sha256sum "${archive_name}.tar.gz" > "${archive_name}.tar.gz.sha256")
  log_info "Checksum: $(cat "${SBOM_DIR}/${archive_name}.tar.gz.sha256")"
}

publish_to_artifact_store() {
  if [[ -z "${ARTIFACT_STORE_URL}" ]]; then
    log_warn "ARTIFACT_STORE_URL not set. Skipping publish."
    return 0
  fi

  log_info "Publishing SBOM to artifact store..."

  local archive_name="sbom-gula-platform-${VERSION}.tar.gz"
  local archive_path="${SBOM_DIR}/${archive_name}"

  if [[ ! -f "${archive_path}" ]]; then
    log_error "Archive not found: ${archive_path}"
    return 1
  fi

  # Upload to artifact store
  curl -s -f -X POST \
    -H "Authorization: Bearer ${ARTIFACT_STORE_TOKEN}" \
    -F "file=@${archive_path}" \
    "${ARTIFACT_STORE_URL}/api/v1/artifacts/" \
    || log_warn "Failed to publish SBOM to artifact store"

  log_info "SBOM published to artifact store"
}

# ==============================================================================
# VERIFICATION
# ==============================================================================

verify_sbom() {
  log_info "Verifying SBOM completeness..."
  local errors=0

  # Check Python SBOM
  if [[ -f "${SBOM_DIR}/sbom-python-${VERSION}.json" ]]; then
    local py_count
    py_count=$(jq '.components | length' "${SBOM_DIR}/sbom-python-${VERSION}.json" 2>/dev/null || echo "0")
    if [[ "${py_count}" -gt 0 ]]; then
      log_info "Python SBOM: ${py_count} packages"
    else
      log_warn "Python SBOM appears empty"
      errors=$((errors + 1))
    fi
  else
    log_error "Python SBOM not found"
    errors=$((errors + 1))
  fi

  # Check Node SBOM
  if [[ -f "${SBOM_DIR}/sbom-node-${VERSION}.json" ]]; then
    local node_count
    node_count=$(jq '.components | length' "${SBOM_DIR}/sbom-node-${VERSION}.json" 2>/dev/null || echo "0")
    if [[ "${node_count}" -gt 0 ]]; then
      log_info "Node SBOM: ${node_count} packages"
    fi
  fi

  # Check Container SBOM
  if [[ -f "${SBOM_DIR}/sbom-container-${VERSION}.json" ]]; then
    local container_count
    container_count=$(jq '.packages | length' "${SBOM_DIR}/sbom-container-${VERSION}.json" 2>/dev/null || jq '.components | length' "${SBOM_DIR}/sbom-container-${VERSION}.json" 2>/dev/null || echo "0")
    if [[ "${container_count}" -gt 0 ]]; then
      log_info "Container SBOM: ${container_count} packages"
    else
      log_warn "Container SBOM appears empty"
      errors=$((errors + 1))
    fi
  fi

  if [[ ${errors} -eq 0 ]]; then
    log_info "SBOM verification PASSED"
    return 0
  else
    log_warn "SBOM verification completed with ${errors} issue(s)"
    return 1
  fi
}

# ==============================================================================
# MAIN
# ==============================================================================

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS]

Generate Software Bill of Materials for GULA Platform.

Options:
  --python        Generate Python dependency SBOM
  --node          Generate Node.js dependency SBOM
  --container     Generate container image SBOM
  --all           Generate all SBOMs (default)
  --publish       Publish SBOM to artifact store
  --verify        Verify SBOM completeness
  --archive       Create tar.gz archive
  --help          Show this help message

Examples:
  ${SCRIPT_NAME} --all
  ${SCRIPT_NAME} --all --publish --archive
  ${SCRIPT_NAME} --verify
EOF
  exit 0
}

main() {
  local do_python=false
  local do_node=false
  local do_container=false
  local do_all=true
  local do_publish=false
  local do_verify=false
  local do_archive=false

  if [[ $# -eq 0 ]]; then
    do_all=true
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --python) do_python=true; do_all=false ;;
      --node) do_node=true; do_all=false ;;
      --container) do_container=true; do_all=false ;;
      --all) do_all=true ;;
      --publish) do_publish=true ;;
      --verify) do_verify=true ;;
      --archive) do_archive=true ;;
      --help) usage ;;
      *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
  done

  log_info "=== GULA Platform SBOM Generation ==="
  log_info "Version: ${VERSION}"
  log_info "Output: ${SBOM_DIR}"

  check_prerequisites

  if [[ "${do_all}" == true ]]; then
    generate_python_sbom
    generate_node_sbom
    generate_container_sbom
  else
    [[ "${do_python}" == true ]] && generate_python_sbom
    [[ "${do_node}" == true ]] && generate_node_sbom
    [[ "${do_container}" == true ]] && generate_container_sbom
  fi

  generate_summary

  if [[ "${do_archive}" == true ]]; then
    archive_sbom
  fi

  if [[ "${do_verify}" == true ]]; then
    verify_sbom
  fi

  if [[ "${do_publish}" == true ]]; then
    archive_sbom
    publish_to_artifact_store
  fi

  log_info "=== SBOM Generation Complete ==="
  ls -la "${SBOM_DIR}/" 2>/dev/null | grep "${VERSION}"
}

main "$@"
