#!/usr/bin/env bash
# Launch-day secret generator for GULA Platform.
#
# Produces a secrets file suitable for Render/Docker/systemd with every
# CHANGE_ME placeholder replaced by a cryptographically random value.
#
# CRITICAL ENVIRONMENT NOTES
#   - NID_HMAC_KEY and ENCRYPTION_KEY must NEVER change after first data is
#     written to production. Rotating them corrupts hashed NIDs and Fernet
#     ciphertexts.
#   - SECRET_KEY and REFRESH_TOKEN_SECRET may be rotated; sessions will be
#     invalidated and every user forced to re-authenticate.
#
# USAGE
#   bash scripts/generate-launch-secrets.sh > .env.launch
#   chmod 600 .env.launch
#   # Review, then:
#   cp .env.launch .env     # for docker-compose
#   # or feed each key into the Render dashboard (sync: false secrets).

set -euo pipefail

command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }

token_urlsafe() {
    python3 -c "import secrets; print(secrets.token_urlsafe($1))"
}

token_hex() {
    python3 -c "import secrets; print(secrets.token_hex($1))"
}

fernet_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null \
        || python3 -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
}

SECRET_KEY=$(token_urlsafe 64)
REFRESH_TOKEN_SECRET=$(token_urlsafe 64)
# Ensure the two JWT secrets never collide.
while [[ "$REFRESH_TOKEN_SECRET" == "$SECRET_KEY" ]]; do
    REFRESH_TOKEN_SECRET=$(token_urlsafe 64)
done

ENCRYPTION_KEY=$(fernet_key)
NID_HMAC_KEY=$(token_hex 32)
DEVICE_HMAC_KEY=$(token_hex 32)
POSTGRES_PASSWORD=$(token_urlsafe 32)
REDIS_PASSWORD=$(token_urlsafe 32)
GRAFANA_PASSWORD=$(token_urlsafe 16)
GULA_ADMIN_PASSWORD=$(token_urlsafe 20)

cat <<EOF
# GULA Platform — Launch Secrets
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# DO NOT COMMIT. DO NOT SHARE ON SLACK/EMAIL. Store in a password manager
# and/or the cloud provider's secret store.

ENV=production
DEBUG=false
LOG_LEVEL=warning

POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/labdb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=10
DB_POOL_RECYCLE=1800

REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

SECRET_KEY=${SECRET_KEY}
REFRESH_TOKEN_SECRET=${REFRESH_TOKEN_SECRET}
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_EXPIRE_MINUTES=30

ENCRYPTION_KEY=${ENCRYPTION_KEY}
NID_HMAC_KEY=${NID_HMAC_KEY}
DEVICE_HMAC_KEY=${DEVICE_HMAC_KEY}

GULA_ADMIN_EMAIL=admin@gula-platform.org
GULA_ADMIN_NAME=GULA Platform Admin
GULA_ADMIN_PASSWORD=${GULA_ADMIN_PASSWORD}

BASE_URL=https://gula-platform.org
CORS_ORIGINS=https://gula-platform.org
ENABLE_API_DOCS=false

WEB_CONCURRENCY=4
MAX_CONCURRENT_REQUESTS=200
MAX_REQUEST_BODY_MB=10
MAX_UPLOAD_SIZE_MB=2
RATE_LIMIT_AUTH=10
RATE_LIMIT_PUBLIC=60

GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *

MPI_MAX_CANDIDATES=50
EOF

cat >&2 <<WARN

== Generated successfully ==
Review the output, then:
    1. Save to a secret store (1Password, AWS Secrets Manager, Render dashboard).
    2. Store ENCRYPTION_KEY and NID_HMAC_KEY separately in cold storage
       (paper, HSM, or offline vault) — they are immutable after first write.
    3. Rotate GULA_ADMIN_PASSWORD after the first login.

WARN
