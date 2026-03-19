#!/bin/bash
# =============================================================================
# GULA Platform — Secure Secrets Setup
#
# Addresses: Key Exposure Runtime Risk (ISO 27001 A.8.24)
#
# This script creates /etc/gula-secrets.env with secure permissions (600/root)
# so even if the application process is compromised, the secrets file itself
# is not readable by the app user.
#
# After setup, load the file in:
#   - Systemd: EnvironmentFile=/etc/gula-secrets.env  (service reads on start)
#   - Docker:  docker run --env-file /etc/gula-secrets.env ...
#   - Docker Compose: env_file: /etc/gula-secrets.env
#
# Usage (run as root):
#   sudo bash scripts/setup-secrets.sh
# =============================================================================

set -euo pipefail

SECRETS_FILE="/etc/gula-secrets.env"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: This script must be run as root: sudo bash $0"
  exit 1
fi

echo "=== GULA Platform — Secrets Setup ==="
echo ""

# ─── Generate cryptographically secure secrets if not already set ─────────────
generate_key() {
  openssl rand -hex 32
}

if [[ -f "${SECRETS_FILE}" ]]; then
  echo "INFO: ${SECRETS_FILE} already exists — updating permissions only."
  chmod 600 "${SECRETS_FILE}"
  chown root:root "${SECRETS_FILE}"
  echo "OK: Permissions set to 600/root:root"
  exit 0
fi

echo "Generating secure secrets..."
SECRET_KEY=$(generate_key)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)
NID_HMAC_KEY=$(generate_key)

cat > "${SECRETS_FILE}" <<ENV
# GULA Platform — Production Secrets
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# IMPORTANT: Never commit this file to version control
# IMPORTANT: Never set these in .env.production (load from this file instead)

# JWT signing key — rotate every 90 days (forces all sessions to re-login)
SECRET_KEY=${SECRET_KEY}

# Fernet encryption key for sensitive data fields
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# HMAC key for national ID hashing + audit anchor signing
NID_HMAC_KEY=${NID_HMAC_KEY}

# Current anchor key version (increment when rotating NID_HMAC_KEY)
ANCHOR_KEY_VERSION=1

# Previous HMAC key (set during rotation window, clear after 30 days)
# NID_HMAC_KEY_PREV=

# Database URL (adjust to your DB)
# DATABASE_URL=postgresql://gula:CHANGE_ME@db:5432/labdb

# Production flag
IS_PRODUCTION=true
ENV

chmod 600 "${SECRETS_FILE}"
chown root:root "${SECRETS_FILE}"

echo ""
echo "=== DONE ==="
echo "Secrets file: ${SECRETS_FILE}"
echo "Permissions:  $(stat -c '%a %U:%G' "${SECRETS_FILE}")"
echo ""
echo "Next steps:"
echo "  1. Edit ${SECRETS_FILE} and fill in DATABASE_URL"
echo "  2. Load in docker-compose:  env_file: /etc/gula-secrets.env"
echo "     OR systemd service:      EnvironmentFile=/etc/gula-secrets.env"
echo "  3. Verify app can read it:  docker exec <container> env | grep SECRET_KEY"
echo ""
echo "Key rotation procedure:"
echo "  1. Generate new key: openssl rand -hex 32"
echo "  2. Set NID_HMAC_KEY_PREV=<old_key> in this file"
echo "  3. Set NID_HMAC_KEY=<new_key>"
echo "  4. Increment ANCHOR_KEY_VERSION"
echo "  5. Restart the app"
echo "  6. After 30 days: clear NID_HMAC_KEY_PREV"
