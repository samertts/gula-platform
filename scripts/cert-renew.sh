#!/usr/bin/env bash
# =============================================================================
# Certificate Renewal Hook — GULA Platform
# =============================================================================
# Path: scripts/cert-renew.sh
# Managed by: Security Operations
# Schedule: Runs daily via cron (crontab -e)
#   # Daily certificate check at 02:00 Baghdad time (UTC+3)
#   0 2 * * * /opt/gula/scripts/cert-renew.sh >> /var/log/cert-renew.log 2>&1
#
# Description:
#   Checks TLS certificate expiry and triggers renewal if needed.
#   Supports both Kubernetes cert-manager and standalone Docker deployments.
# =============================================================================

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"

# Certificate paths and settings
readonly CERT_PATH="${CERT_PATH:-/etc/nginx/certs/gula.health.pem}"
readonly KEY_PATH="${KEY_PATH:-/etc/nginx/certs/gula.health.key}"
readonly CHAIN_PATH="${CHAIN_PATH:-/etc/nginx/certs/chain.pem}"
readonly FULLCHAIN_PATH="${FULLCHAIN_PATH:-/etc/nginx/certs/fullchain.pem}"

# Renewal thresholds (in days)
readonly RENEW_DAYS="${RENEW_DAYS:-30}"
readonly CRITICAL_DAYS="${CRITICAL_DAYS:-7}"

# Deployment mode: docker or kubernetes
readonly DEPLOY_MODE="${DEPLOY_MODE:-docker}"

# Notifications
readonly ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
readonly NOTIFY_EMAIL="${NOTIFY_EMAIL:-security@gula.health}"

# cert-manager namespace
readonly CERT_MANAGER_NS="${CERT_MANAGER_NS:-cert-manager}"

# Kubernetes certificate resources
readonly K8S_CERT_NAME="${K8S_CERT_NAME:-gula-wildcard-tls}"
readonly K8S_CERT_NAMESPACE="${K8S_CERT_NAMESPACE:-default}"

# Nginx reload command
readonly NGINX_RELOAD_CMD="${NGINX_RELOAD_CMD:-docker exec api-gateway nginx -s reload}"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

log_info() {
  echo "[${TIMESTAMP}] [INFO] ${SCRIPT_NAME}: $*"
}

log_warn() {
  echo "[${TIMESTAMP}] [WARN] ${SCRIPT_NAME}: $*" >&2
}

log_error() {
  echo "[${TIMESTAMP}] [ERROR] ${SCRIPT_NAME}: $*" >&2
}

send_notification() {
  local subject="$1"
  local message="$2"
  local severity="${3:-WARNING}"

  log_info "Sending notification: ${subject}"

  # Send to webhook if configured
  if [[ -n "${ALERT_WEBHOOK_URL}" ]]; then
    local payload
    payload=$(cat <<EOF
{
  "message": "${subject}",
  "description": "${message}",
  "severity": "${severity}",
  "service": "cert-renew",
  "timestamp": "${TIMESTAMP}",
  "host": "$(hostname)"
}
EOF
)
    curl -s -f -X POST -H "Content-Type: application/json" \
      -d "${payload}" "${ALERT_WEBHOOK_URL}" || log_warn "Failed to send webhook notification"
  fi

  # Send email if mail command available
  if command -v mail &>/dev/null; then
    echo "${message}" | mail -s "[GULA] ${subject}" "${NOTIFY_EMAIL}" || log_warn "Failed to send email notification"
  fi
}

get_cert_expiry_days() {
  local cert_file="$1"

  if [[ ! -f "${cert_file}" ]]; then
    echo "0"
    return
  fi

  local expiry_date
  local now_epoch
  local expiry_epoch

  expiry_date=$(openssl x509 -enddate -noout -in "${cert_file}" 2>/dev/null | cut -d= -f2)
  if [[ -z "${expiry_date}" ]]; then
    echo "0"
    return
  fi

  now_epoch=$(date +%s)
  expiry_epoch=$(date -d "${expiry_date}" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "${expiry_date}" +%s 2>/dev/null)

  if [[ -z "${expiry_epoch}" ]]; then
    echo "0"
    return
  fi

  echo "$(( (expiry_epoch - now_epoch) / 86400 ))"
}

check_prerequisites() {
  local missing=0

  if ! command -v openssl &>/dev/null; then
    log_error "openssl is required but not installed"
    missing=1
  fi

  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    if ! command -v kubectl &>/dev/null; then
      log_error "kubectl is required for kubernetes mode but not installed"
      missing=1
    fi
  fi

  if [[ "${DEPLOY_MODE}" == "docker" ]]; then
    if ! command -v docker &>/dev/null; then
      log_error "docker is required for docker mode but not installed"
      missing=1
    fi
  fi

  return "${missing}"
}

verify_certificate() {
  local cert_file="$1"
  local key_file="${2:-}"

  if [[ ! -f "${cert_file}" ]]; then
    log_error "Certificate file not found: ${cert_file}"
    return 1
  fi

  # Check certificate validity dates
  if ! openssl x509 -checkend 0 -in "${cert_file}" &>/dev/null; then
    log_error "Certificate has expired: ${cert_file}"
    return 1
  fi

  # Verify certificate matches key if both provided
  if [[ -n "${key_file}" && -f "${key_file}" ]]; then
    local cert_hash
    local key_hash
    cert_hash=$(openssl x509 -noout -modulus -in "${cert_file}" | openssl md5)
    key_hash=$(openssl rsa -noout -modulus -in "${key_file}" | openssl md5)

    if [[ "${cert_hash}" != "${key_hash}" ]]; then
      log_error "Certificate and key do not match!"
      return 1
    fi
  fi

  log_info "Certificate verification passed for: ${cert_file}"
  return 0
}

reload_nginx() {
  log_info "Reloading nginx configuration..."

  if eval "${NGINX_RELOAD_CMD}"; then
    log_info "nginx reloaded successfully"
    return 0
  else
    log_error "Failed to reload nginx"
    return 1
  fi
}

# ==============================================================================
# RENEWAL STRATEGIES
# ==============================================================================

renew_docker() {
  log_info "Executing Docker renewal strategy"

  # For standalone Docker deployments using Let's Encrypt certbot
  if command -v certbot &>/dev/null; then
    log_info "Running certbot renewal..."

    if certbot renew --non-interactive --quiet; then
      log_info "certbot renewal completed"

      # Copy renewed certs to nginx location
      if [[ -f /etc/letsencrypt/live/gula.health/fullchain.pem ]]; then
        cp /etc/letsencrypt/live/gula.health/fullchain.pem "${FULLCHAIN_PATH}"
        cp /etc/letsencrypt/live/gula.health/privkey.pem "${KEY_PATH}"
        cp /etc/letsencrypt/live/gula.health/chain.pem "${CHAIN_PATH}"
        cp /etc/letsencrypt/live/gula.health/cert.pem "${CERT_PATH}"

        chmod 644 "${FULLCHAIN_PATH}" "${CHAIN_PATH}" "${CERT_PATH}"
        chmod 600 "${KEY_PATH}"

        verify_certificate "${CERT_PATH}" "${KEY_PATH}" && reload_nginx
        return 0
      fi
    else
      log_error "certbot renewal failed"
      return 1
    fi
  else
    log_warn "certbot not found — cannot renew certificates in Docker mode"
    log_warn "Consider switching to Kubernetes cert-manager or install certbot"
    return 1
  fi
}

renew_kubernetes() {
  log_info "Executing Kubernetes cert-manager renewal strategy"

  # Trigger renewal by annotating the certificate
  log_info "Triggering cert-manager renewal for ${K8S_CERT_NAME}..."

  if kubectl annotate certificate "${K8S_CERT_NAME}" \
    --namespace "${K8S_CERT_NAMESPACE}" \
    cert-manager.io/issue-temporary-certificate="true" \
    --overwrite &>/dev/null; then
    log_info "Renewal annotation applied"
  else
    log_warn "Could not annotate certificate (may not exist yet)"
  fi

  # Delete the secret to force re-issuance (alternative approach)
  if kubectl get secret gula-tls-cert --namespace "${K8S_CERT_NAMESPACE}" &>/dev/null; then
    log_info "Deleting existing secret to force re-issuance..."
    kubectl delete secret gula-tls-cert --namespace "${K8S_CERT_NAMESPACE}" --wait=false &>/dev/null
  fi

  # Wait for the new certificate to be ready
  log_info "Waiting for certificate to be issued..."
  local wait_count=0
  local max_wait=120  # 2 minutes max

  while [[ ${wait_count} -lt ${max_wait} ]]; do
    if kubectl get certificate "${K8S_CERT_NAME}" \
      --namespace "${K8S_CERT_NAMESPACE}" \
      -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -q "True"; then
        log_info "Certificate is ready!"
        break
    fi
    sleep 5
    wait_count=$((wait_count + 1))
  done

  if [[ ${wait_count} -ge ${max_wait} ]]; then
    log_error "Timed out waiting for certificate to be issued"
    return 1
  fi

  # Verify the new certificate
  local new_cert
  new_cert=$(kubectl get secret gula-tls-cert \
    --namespace "${K8S_CERT_NAMESPACE}" \
    -o jsonpath='{.data.tls\.crt}' 2>/dev/null | base64 -d)

  if [[ -n "${new_cert}" ]]; then
    local tmp_cert
    tmp_cert=$(mktemp)
    echo "${new_cert}" > "${tmp_cert}"
    verify_certificate "${tmp_cert}"
    rm -f "${tmp_cert}"
  fi

  # Ingress will automatically pick up the new secret
  log_info "Kubernetes ingress will auto-detect the renewed certificate"
  return 0
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
  log_info "=== Certificate Renewal Check ==="

  # Check prerequisites
  if ! check_prerequisites; then
    log_error "Prerequisites check failed"
    send_notification \
      "Certificate Renewal Failed — Missing Prerequisites" \
      "The certificate renewal script could not run because required tools are missing." \
      "CRITICAL"
    exit 1
  fi

  # Determine renewal strategy based on deployment mode
  case "${DEPLOY_MODE}" in
    docker)
      if [[ -f "${CERT_PATH}" ]]; then
        local days_left
        days_left=$(get_cert_expiry_days "${CERT_PATH}")
        log_info "Current certificate expires in ${days_left} days"

        if [[ ${days_left} -le 0 ]]; then
          log_error "Certificate has ALREADY EXPIRED!"
          send_notification \
            "CRITICAL: TLS Certificate Expired" \
            "The TLS certificate has expired. Immediate action required." \
            "CRITICAL"
          renew_docker || exit 1
        elif [[ ${days_left} -le ${CRITICAL_DAYS} ]]; then
          log_warn "Certificate expires in ${days_left} days (CRITICAL)"
          send_notification \
            "CRITICAL: TLS Certificate Expiring Soon" \
            "The TLS certificate expires in ${days_left} days. Triggering renewal." \
            "CRITICAL"
          renew_docker || exit 1
        elif [[ ${days_left} -le ${RENEW_DAYS} ]]; then
          log_info "Certificate expires in ${days_left} days — renewing"
          renew_docker || exit 1
        else
          log_info "Certificate is valid for ${days_left} days — no action needed"
          exit 0
        fi
      else
        log_warn "Certificate not found at ${CERT_PATH} — attempting initial issuance"
        renew_docker || exit 1
      fi
      ;;

    kubernetes)
      # Check if cert-manager certificate exists
      if kubectl get certificate "${K8S_CERT_NAME}" \
        --namespace "${K8S_CERT_NAMESPACE}" &>/dev/null; then
        log_info "Found cert-manager Certificate resource: ${K8S_CERT_NAME}"

        # Get certificate expiry from Kubernetes
        local k8s_expiry
        k8s_expiry=$(kubectl get certificate "${K8S_CERT_NAME}" \
          --namespace "${K8S_CERT_NAMESPACE}" \
          -o jsonpath='{.status.notAfter}' 2>/dev/null || echo "")

        if [[ -n "${k8s_expiry}" ]]; then
          local expiry_epoch
          local now_epoch
          now_epoch=$(date +%s)
          expiry_epoch=$(date -d "${k8s_expiry}" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "${k8s_expiry}" +%s 2>/dev/null)

          if [[ -n "${expiry_epoch}" ]]; then
            local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
            log_info "Certificate expires in ${days_left} days (until ${k8s_expiry})"

            if [[ ${days_left} -le ${RENEW_DAYS} ]]; then
              log_info "Certificate expires in ${days_left} days — triggering renewal"
              renew_kubernetes || exit 1
            else
              log_info "Certificate is valid for ${days_left} days — no action needed"
              exit 0
            fi
          fi
        else
          log_warn "Could not determine certificate expiry — forcing renewal"
          renew_kubernetes || exit 1
        fi
      else
        log_warn "Certificate resource not found — attempting to create"
        # If we have a template, apply it
        if [[ -f "${SCRIPT_DIR}/../config/cert-manager/certificate-template.yaml" ]]; then
          kubectl apply -f "${SCRIPT_DIR}/../config/cert-manager/certificate-template.yaml" || exit 1
        fi
        exit 0
      fi
      ;;

    *)
      log_error "Unknown deployment mode: ${DEPLOY_MODE}"
      log_error "Supported modes: docker, kubernetes"
      exit 1
      ;;
  esac

  # Final verification
  log_info "=== Certificate Renewal Verification ==="

  if [[ "${DEPLOY_MODE}" == "docker" ]] && [[ -f "${CERT_PATH}" ]]; then
    local new_days_left
    new_days_left=$(get_cert_expiry_days "${CERT_PATH}")
    log_info "New certificate expires in ${new_days_left} days"

    if [[ ${new_days_left} -gt ${RENEW_DAYS} ]]; then
      log_info "Renewal successful!"
      send_notification \
        "TLS Certificate Renewed Successfully" \
        "The TLS certificate was renewed. New expiry: ${new_days_left} days." \
        "INFO"
    else
      log_warn "Renewal may not have taken effect — certificate still expiring soon"
      send_notification \
        "TLS Certificate Renewal Warning" \
        "Certificate renewal was attempted but the certificate still shows ${new_days_left} days until expiry." \
        "WARNING"
    fi
  fi

  log_info "=== Certificate Renewal Complete ==="
}

# ==============================================================================
# EXECUTION
# ==============================================================================

main "$@"
