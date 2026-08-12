#!/usr/bin/env bash
# =============================================================================
# Secret Rotation Script — GULA Platform
# =============================================================================
# Path: scripts/rotate-secrets.sh
# Managed by: Security Operations
# Usage:
#   ./rotate-secrets.sh --all                    Rotate all secrets
#   ./rotate-secrets.sh --postgres               Rotate PostgreSQL password only
#   ./rotate-secrets.sh --redis                  Rotate Redis password only
#   ./rotate-secrets.sh --rabbitmq               Rotate RabbitMQ password only
#   ./rotate-secrets.sh --secret-key             Rotate SECRET_KEY only
#   ./rotate-secrets.sh --encryption-key         Rotate ENCRYPTION_KEY only
#   ./rotate-secrets.sh --status                 Check rotation status
#   ./rotate-secrets.sh --help                   Show help
#
# Requirements:
#   - psql client, redis-cli, rabbitmqadmin, docker compose
#   - Access to production .env file
#   - kubectl (for Kubernetes deployments)
# =============================================================================

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
readonly LOG_FILE="/var/log/gula/secret-rotation.log"
readonly ENV_FILE="${ENV_FILE:-${SCRIPT_DIR}/../.env}"
readonly ENV_BACKUP_DIR="${ENV_BACKUP_DIR:-/opt/gula/env-backups}"
readonly ROTATION_LOCK_FILE="/tmp/gula-secret-rotation.lock"
readonly DEPLOY_MODE="${DEPLOY_MODE:-docker}"

# Source environment
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ENV_FILE}"
  set +a
fi

# Docker compose project
readonly COMPOSE_PROJECT="${COMPOSE_PROJECT:-gula-platform}"

# ==============================================================================
# LOGGING
# ==============================================================================
mkdir -p "$(dirname "${LOG_FILE}")"

log_info() {
  echo "[${TIMESTAMP}] [INFO] ${SCRIPT_NAME}: $*" | tee -a "${LOG_FILE}"
}

log_warn() {
  echo "[${TIMESTAMP}] [WARN] ${SCRIPT_NAME}: $*" | tee -a "${LOG_FILE}" >&2
}

log_error() {
  echo "[${TIMESTAMP}] [ERROR] ${SCRIPT_NAME}: $*" | tee -a "${LOG_FILE}" >&2
}

log_audit() {
  local action="$1"
  local target="$2"
  local status="$3"
  local detail="${4:-}"
  echo "[${TIMESTAMP}] [AUDIT] action=${action} target=${target} status=${status} detail=${detail}" | tee -a "${LOG_FILE}"
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

cleanup() {
  rm -f "${ROTATION_LOCK_FILE}"
}

acquire_lock() {
  if [[ -f "${ROTATION_LOCK_FILE}" ]]; then
    local lock_pid
    lock_pid=$(cat "${ROTATION_LOCK_FILE}" 2>/dev/null || echo "")
    if [[ -n "${lock_pid}" ]] && kill -0 "${lock_pid}" 2>/dev/null; then
      log_error "Rotation already in progress (PID: ${lock_pid})"
      exit 1
    fi
    log_warn "Removing stale lock file"
  fi
  echo "$$" > "${ROTATION_LOCK_FILE}"
  trap cleanup EXIT INT TERM
}

generate_password() {
  local length="${1:-32}"
  openssl rand -base64 "${length}" | tr -d '\n' | tr -d '=' | tr '+/' '-_'
}

generate_secret_key() {
  openssl rand -hex 32
}

generate_encryption_key() {
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

backup_env() {
  local backup_name="env-backup-$(date '+%Y%m%d-%H%M%S')"
  mkdir -p "${ENV_BACKUP_DIR}"
  if [[ -f "${ENV_FILE}" ]]; then
    cp "${ENV_FILE}" "${ENV_BACKUP_DIR}/${backup_name}"
    log_info "Environment backed up to ${ENV_BACKUP_DIR}/${backup_name}"
  fi
}

update_env() {
  local key="$1"
  local value="$2"

  if [[ ! -f "${ENV_FILE}" ]]; then
    log_error "Environment file not found: ${ENV_FILE}"
    return 1
  fi

  # Escape special characters for sed
  local escaped_value
  escaped_value=$(printf '%s\n' "${value}" | sed 's/[&/\]/\\&/g')

  if grep -q "^${key}=" "${ENV_FILE}"; then
    sed -i "s|^${key}=.*|${key}=${escaped_value}|" "${ENV_FILE}"
  elif grep -q "^#${key}=" "${ENV_FILE}"; then
    sed -i "s|^#${key}=.*|${key}=${escaped_value}|" "${ENV_FILE}"
  else
    echo "${key}=${value}" >> "${ENV_FILE}"
  fi

  log_info "Updated ${key} in ${ENV_FILE}"
}

read_env() {
  local key="$1"
  grep -E "^${key}=" "${ENV_FILE}" 2>/dev/null | cut -d= -f2- || echo ""
}

wait_for_service() {
  local service="$1"
  local timeout="${2:-60}"
  local interval="${3:-5}"
  local count=0

  log_info "Waiting for ${service} to be ready..."
  while [[ ${count} -lt ${timeout} ]]; do
    if docker compose -p "${COMPOSE_PROJECT}" ps "${service}" 2>/dev/null | grep -q "Up"; then
      log_info "${service} is ready"
      return 0
    fi
    sleep "${interval}"
    count=$((count + interval))
  done

  log_error "${service} did not become ready within ${timeout}s"
  return 1
}

rolling_restart() {
  local service="$1"
  log_info "Performing rolling restart of ${service}..."

  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    kubectl rollout restart "deployment/${service}" --namespace=default
    kubectl rollout status "deployment/${service}" --namespace=default --timeout=120s
  else
    docker compose -p "${COMPOSE_PROJECT}" up -d --force-recreate --no-deps "${service}"
    wait_for_service "${service}"
  fi

  log_info "Rolling restart of ${service} completed"
}

# ==============================================================================
# ROTATION FUNCTIONS
# ==============================================================================

rotate_postgres() {
  log_info "=== Rotating PostgreSQL Password ==="
  local old_password
  local new_password

  old_password=$(read_env "POSTGRES_PASSWORD")
  new_password=$(generate_password 32)

  log_info "Step 1: Updating password in PostgreSQL..."

  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    # Get current superuser password from secret
    local pg_superuser
    pg_superuser=$(kubectl get secret gula-postgres-secret -o jsonpath='{.data.POSTGRES_USER}' | base64 -d 2>/dev/null || echo "gula")
    local pg_host
    pg_host=$(kubectl get service gula-postgres -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-postgres")

    PGPASSWORD="${old_password}" psql -h "${pg_host}" -U "${pg_superuser}" -d postgres \
      -c "ALTER USER ${pg_superuser} WITH PASSWORD '${new_password}';"
  else
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-postgres \
      psql -U "${POSTGRES_USER:-gula}" -d postgres \
      -c "ALTER USER ${POSTGRES_USER:-gula} WITH PASSWORD '${new_password}';"
  fi

  log_info "Step 2: Updating .env file..."
  backup_env
  update_env "POSTGRES_PASSWORD" "${new_password}"

  log_info "Step 3: Rolling restart of backend and worker..."
  rolling_restart "gula-backend"
  rolling_restart "gula-worker"

  log_info "Step 4: Verifying new password..."
  sleep 5

  local verify_result=1
  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local pg_host
    pg_host=$(kubectl get service gula-postgres -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-postgres")
    local pg_user
    pg_user=$(kubectl get secret gula-postgres-secret -o jsonpath='{.data.POSTGRES_USER}' | base64 -d 2>/dev/null || echo "gula")
    PGPASSWORD="${new_password}" psql -h "${pg_host}" -U "${pg_user}" -d postgres -c "SELECT 1;" && verify_result=0
  else
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-postgres \
      psql -U "${POSTGRES_USER:-gula}" -d postgres -c "SELECT 1;" && verify_result=0
  fi

  if [[ ${verify_result} -eq 0 ]]; then
    log_info "Step 5: Revoking old password connections..."
    if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
      local pg_host
      pg_host=$(kubectl get service gula-postgres -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-postgres")
      local pg_user
      pg_user=$(kubectl get secret gula-postgres-secret -o jsonpath='{.data.POSTGRES_USER}' | base64 -d 2>/dev/null || echo "gula")
      PGPASSWORD="${new_password}" psql -h "${pg_host}" -U "${pg_user}" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='${pg_user}' AND pid <> pg_backend_pid();"
    else
      docker compose -p "${COMPOSE_PROJECT}" exec -T gula-postgres \
        psql -U "${POSTGRES_USER:-gula}" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='${POSTGRES_USER:-gula}' AND pid <> pg_backend_pid();"
    fi
    log_info "PostgreSQL password rotation completed successfully"
    log_audit "rotate" "postgres_password" "success" "Password rotated and verified"
  else
    log_error "Password verification failed — rolling back"
    update_env "POSTGRES_PASSWORD" "${old_password}"
    rolling_restart "gula-backend"
    rolling_restart "gula-worker"
    log_audit "rotate" "postgres_password" "failed" "Verification failed, rolled back"
    return 1
  fi
}

rotate_redis() {
  log_info "=== Rotating Redis Password ==="
  local old_password
  local new_password

  old_password=$(read_env "REDIS_PASSWORD")
  new_password=$(generate_password 32)

  log_info "Step 1: Updating Redis password..."
  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local redis_host
    redis_host=$(kubectl get service gula-redis -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-redis")
    redis-cli -h "${redis_host}" -a "${old_password}" \
      CONFIG SET requirepass "${new_password}" 2>/dev/null || true
    # For Redis with ACL
    redis-cli -h "${redis_host}" -a "${new_password}" \
      ACL SETUSER default on ">${new_password}" 2>/dev/null || true
  else
    # Connect with old password, set new password
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-redis \
      redis-cli -a "${old_password}" CONFIG SET requirepass "${new_password}" 2>/dev/null || true
    # For Redis 6+ with ACL
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-redis \
      redis-cli -a "${new_password}" ACL SETUSER default on ">${new_password}" 2>/dev/null || true
  fi

  log_info "Step 2: Updating .env file..."
  backup_env
  update_env "REDIS_PASSWORD" "${new_password}"

  log_info "Step 3: Rolling restart of backend and worker..."
  rolling_restart "gula-backend"
  rolling_restart "gula-worker"

  log_info "Step 4: Verifying new password..."
  sleep 3

  local verify_result=1
  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local redis_host
    redis_host=$(kubectl get service gula-redis -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-redis")
    redis-cli -h "${redis_host}" -a "${new_password}" PING && verify_result=0
  else
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-redis \
      redis-cli -a "${new_password}" PING && verify_result=0
  fi

  if [[ ${verify_result} -eq 0 ]]; then
    log_info "Redis password rotation completed successfully"
    log_audit "rotate" "redis_password" "success" "Password rotated and verified"
  else
    log_error "Redis password verification failed — rolling back"
    update_env "REDIS_PASSWORD" "${old_password}"
    rolling_restart "gula-backend"
    rolling_restart "gula-worker"
    log_audit "rotate" "redis_password" "failed" "Verification failed, rolled back"
    return 1
  fi
}

rotate_rabbitmq() {
  log_info "=== Rotating RabbitMQ Password ==="
  local old_password
  local new_password

  old_password=$(read_env "RABBITMQ_PASS")
  new_password=$(generate_password 32)

  log_info "Step 1: Updating RabbitMQ password..."
  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local rabbitmq_host
    rabbitmq_host=$(kubectl get service gula-rabbitmq -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-rabbitmq")
    local rabbitmq_user
    rabbitmq_user=$(kubectl get secret gula-rabbitmq-secret -o jsonpath='{.data.RABBITMQ_USER}' | base64 -d 2>/dev/null || echo "gula")
    rabbitmqadmin -H "${rabbitmq_host}" -u "${rabbitmq_user}" -p "${old_password}" \
      change_password "${rabbitmq_user}" "${new_password}" 2>/dev/null || true
  else
    local rabbitmq_user="${RABBITMQ_USER:-gula}"
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-rabbitmq \
      rabbitmqctl change_password "${rabbitmq_user}" "${new_password}" 2>/dev/null || true
  fi

  log_info "Step 2: Updating .env file..."
  backup_env
  update_env "RABBITMQ_PASS" "${new_password}"

  log_info "Step 3: Rolling restart of backend and worker..."
  rolling_restart "gula-backend"
  rolling_restart "gula-worker"

  log_info "Step 4: Verifying new password..."
  sleep 5

  local verify_result=1
  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local rabbitmq_host
    rabbitmq_host=$(kubectl get service gula-rabbitmq -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-rabbitmq")
    curl -s -u "${rabbitmq_user}:${new_password}" "http://${rabbitmq_host}:15672/api/whoami" && verify_result=0
  else
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-rabbitmq \
      rabbitmqctl authenticate_user "${rabbitmq_user}" "${new_password}" && verify_result=0
  fi

  if [[ ${verify_result} -eq 0 ]]; then
    log_info "RabbitMQ password rotation completed successfully"
    log_audit "rotate" "rabbitmq_password" "success" "Password rotated and verified"
  else
    log_error "RabbitMQ password verification failed — rolling back"
    update_env "RABBITMQ_PASS" "${old_password}"
    rolling_restart "gula-backend"
    rolling_restart "gula-worker"
    log_audit "rotate" "rabbitmq_password" "failed" "Verification failed, rolled back"
    return 1
  fi
}

rotate_secret_key() {
  log_info "=== Rotating SECRET_KEY ==="
  local old_key
  local new_key

  old_key=$(read_env "SECRET_KEY")
  new_key=$(generate_secret_key)

  backup_env
  update_env "SECRET_KEY" "${new_key}"

  log_info "Rolling restart of backend..."
  rolling_restart "gula-backend"

  log_info "Note: SECRET_KEY rotation invalidates all existing JWT tokens."
  log_info "All users will need to re-authenticate."
  log_audit "rotate" "secret_key" "success" "JWT signing key rotated"
}

rotate_encryption_key() {
  log_info "=== Rotating ENCRYPTION_KEY ==="
  local old_key
  local new_key

  old_key=$(read_env "ENCRYPTION_KEY")
  new_key=$(generate_encryption_key)

  backup_env

  log_info "Step 1: Generated new Fernet key"

  log_info "Step 2: Re-encrypting sensitive fields in database..."
  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local pg_host
    pg_host=$(kubectl get service gula-postgres -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "gula-postgres")
    local pg_user
    pg_user=$(kubectl get secret gula-postgres-secret -o jsonpath='{.data.POSTGRES_USER}' | base64 -d 2>/dev/null || echo "gula")
    local pg_password
    pg_password=$(kubectl get secret gula-postgres-secret -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d 2>/dev/null || echo "")
    PGPASSWORD="${pg_password}" psql -h "${pg_host}" -U "${pg_user}" -d gula -c "
      -- Re-encryption will be handled by the application on read
      -- Mark all encrypted fields as needing re-encryption
      UPDATE patients SET encryption_key_version = encryption_key_version + 1;
      UPDATE lab_results SET encryption_key_version = encryption_key_version + 1;
    " 2>/dev/null || log_warn "Could not mark fields for re-encryption (may not exist)"
  else
    docker compose -p "${COMPOSE_PROJECT}" exec -T gula-postgres \
      psql -U "${POSTGRES_USER:-gula}" -d gula -c "
      UPDATE patients SET encryption_key_version = encryption_key_version + 1;
      UPDATE lab_results SET encryption_key_version = encryption_key_version + 1;
    " 2>/dev/null || log_warn "Could not mark fields for re-encryption (may not exist)"
  fi

  log_info "Step 3: Updating ENCRYPTION_KEY in environment..."
  update_env "ENCRYPTION_KEY" "${new_key}"

  log_info "Step 4: Rolling restart of backend and worker..."
  rolling_restart "gula-backend"
  rolling_restart "gula-worker"

  log_info "Step 5: Verifying decryption works..."
  sleep 5

  if [[ "${DEPLOY_MODE}" == "kubernetes" ]]; then
    local backend_pod
    backend_pod=$(kubectl get pods -l app=gula-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "${backend_pod}" ]]; then
      kubectl exec "${backend_pod}" -- python3 -c "
from cryptography.fernet import Fernet
import os
key = os.environ.get('ENCRYPTION_KEY', '')
try:
    f = Fernet(key)
    test = f.encrypt(b'test')
    f.decrypt(test)
    print('Encryption/decryption verified with new key')
except Exception as e:
    print(f'Encryption verification failed: {e}')
" 2>/dev/null || log_warn "Could not verify encryption in backend pod"
    fi
  fi

  log_info "Step 6: Keeping old key for existing records..."
  update_env "ENCRYPTION_KEY_PREVIOUS" "${old_key}"
  log_info "Old key saved as ENCRYPTION_KEY_PREVIOUS for rotation period"

  log_audit "rotate" "encryption_key" "success" "Encryption key rotated, old key preserved"
}

# ==============================================================================
# STATUS FUNCTIONS
# ==============================================================================

show_status() {
  echo "=== GULA Secret Rotation Status ==="
  echo "Timestamp: ${TIMESTAMP}"
  echo ""

  local secrets
  secrets=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "RABBITMQ_PASS" "SECRET_KEY" "ENCRYPTION_KEY")

  for secret in "${secrets[@]}"; do
    local value
    value=$(read_env "${secret}" 2>/dev/null || echo "<not set>")
    if [[ -n "${value}" ]] && [[ "${value}" != "<not set>" ]]; then
      echo "  ${secret}: [SET] (${#value} chars)"
    else
      echo "  ${secret}: [NOT SET]"
    fi
  done

  echo ""
  echo "Last rotation log entries:"
  if [[ -f "${LOG_FILE}" ]]; then
    grep "\[AUDIT\]" "${LOG_FILE}" | tail -10
  else
    echo "  No rotation log found"
  fi
}

# ==============================================================================
# MAIN
# ==============================================================================

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS]

Options:
  --all               Rotate all secrets (sequential)
  --postgres          Rotate PostgreSQL password
  --redis             Rotate Redis password
  --rabbitmq          Rotate RabbitMQ password
  --secret-key        Rotate SECRET_KEY (JWT signing key)
  --encryption-key    Rotate ENCRYPTION_KEY (Fernet key)
  --status            Show rotation status and last audit entries
  --help              Show this help message

Examples:
  ${SCRIPT_NAME} --all
  ${SCRIPT_NAME} --postgres --redis
  ${SCRIPT_NAME} --status
EOF
  exit 0
}

main() {
  if [[ $# -eq 0 ]]; then
    usage
  fi

  local do_all=false
  local do_postgres=false
  local do_redis=false
  local do_rabbitmq=false
  local do_secret_key=false
  local do_encryption_key=false
  local do_status=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --all) do_all=true ;;
      --postgres) do_postgres=true ;;
      --redis) do_redis=true ;;
      --rabbitmq) do_rabbitmq=true ;;
      --secret-key) do_secret_key=true ;;
      --encryption-key) do_encryption_key=true ;;
      --status) do_status=true ;;
      --help) usage ;;
      *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
  fi

  if [[ "${do_status}" == true ]]; then
    show_status
    exit 0
  fi

  # Acquire lock for rotation operations
  acquire_lock

  local exit_code=0

  if [[ "${do_all}" == true ]]; then
    log_info "=== Starting full secret rotation ==="
    log_audit "rotate_start" "all" "started" "Full secret rotation initiated"

    rotate_postgres || exit_code=$?
    rotate_redis || exit_code=$?
    rotate_rabbitmq || exit_code=$?
    rotate_secret_key || exit_code=$?
    rotate_encryption_key || exit_code=$?

    if [[ ${exit_code} -eq 0 ]]; then
      log_info "=== Full secret rotation completed successfully ==="
      log_audit "rotate_complete" "all" "success" "Full secret rotation completed"
    else
      log_error "=== Full secret rotation completed with errors ==="
      log_audit "rotate_complete" "all" "partial" "Some rotations failed"
    fi
  else
    if [[ "${do_postgres}" == true ]]; then
      rotate_postgres || exit_code=$?
    fi
    if [[ "${do_redis}" == true ]]; then
      rotate_redis || exit_code=$?
    fi
    if [[ "${do_rabbitmq}" == true ]]; then
      rotate_rabbitmq || exit_code=$?
    fi
    if [[ "${do_secret_key}" == true ]]; then
      rotate_secret_key || exit_code=$?
    fi
    if [[ "${do_encryption_key}" == true ]]; then
      rotate_encryption_key || exit_code=$?
    fi
  fi

  exit "${exit_code}"
}

main "$@"
