#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Unified deployment bootstrapper
# منصة غولا الصحية — مُهيِّئ النشر الموحَّد
# =============================================================================
#
# One-shot helper that prepares everything needed to deploy GULA to:
#   • Render             (managed PaaS, Docker)
#   • Supabase           (managed Postgres)
#   • DigitalOcean       (App Platform OR Droplet)
#
# It does NOT push to any platform automatically. It produces:
#   1. .env.deploy   — fully populated, gitignored, shared across platforms
#   2. .deploy/secrets.txt — copy/paste blob for Render & DO dashboards
#   3. A printable summary of next steps per platform
#
# Re-runnable: re-running keeps existing keys (so encrypted patient data stays
# decryptable). Pass --rotate to force-regenerate JWT/HMAC keys (NEVER
# regenerate ENCRYPTION_KEY or NID_HMAC_KEY once data exists).
# =============================================================================
set -euo pipefail

GREEN='\033[1;32m'; RED='\033[1;31m'; CYAN='\033[1;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'
log()  { printf "${CYAN}[deploy]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[\xe2\x9c\x93]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[\xe2\x9c\x97]${NC} %s\n" "$*" >&2; exit 1; }
hdr()  { printf "\n${BOLD}── %s ──${NC}\n" "$*"; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ROTATE=false
SUPABASE_BOOTSTRAP=false
PLATFORM=""

while [ $# -gt 0 ]; do
  case "$1" in
    --rotate)              ROTATE=true; shift ;;
    --supabase-bootstrap)  SUPABASE_BOOTSTRAP=true; shift ;;
    --platform)            PLATFORM="${2:-}"; shift 2 ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--platform render|supabase|do-app|do-droplet|all]
          [--rotate]               force-rotate JWT/HMAC keys
          [--supabase-bootstrap]   also run scripts/supabase_bootstrap.sh
EOF
      exit 0 ;;
    *) err "Unknown flag: $1" ;;
  esac
done

# ── 0. Pre-flight ───────────────────────────────────────────────────────────
hdr "Pre-flight"
command -v python3 >/dev/null 2>&1 || err "python3 is required"
python3 -c "import secrets, sys; sys.exit(0)" 2>/dev/null || err "python3 stdlib broken?"

# Optional: Fernet (for ENCRYPTION_KEY). Install on demand.
if ! python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then
    log "Installing 'cryptography' for Fernet key generation..."
    python3 -m pip install --quiet --user cryptography \
        || err "Failed to install cryptography. Activate your venv and re-run."
fi
ok "All prerequisites available."

# ── 1. Generate / preserve secrets ──────────────────────────────────────────
hdr "Secrets"
ENV_FILE="$ROOT_DIR/.env.deploy"
SECRETS_DIR="$ROOT_DIR/.deploy"
mkdir -p "$SECRETS_DIR"

# Helper: reuse existing value, otherwise generate
keep_or_gen() {
    local key="$1" generator="$2"
    local existing=""
    if [ -f "$ENV_FILE" ]; then
        existing="$(grep -E "^${key}=" "$ENV_FILE" | head -1 | cut -d= -f2- || true)"
    fi
    if [ -n "$existing" ] && [ "$ROTATE" = false ]; then
        printf "%s" "$existing"
    else
        eval "$generator"
    fi
}

# DATA-ENCRYPTION KEYS — never rotate these silently. We refuse to overwrite.
ENCRYPTION_KEY="$(keep_or_gen ENCRYPTION_KEY \
    'python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"')"
NID_HMAC_KEY="$(keep_or_gen NID_HMAC_KEY \
    'python3 -c "import secrets; print(secrets.token_hex(32))"')"
DEVICE_HMAC_KEY="$(keep_or_gen DEVICE_HMAC_KEY \
    'python3 -c "import secrets; print(secrets.token_hex(32))"')"

# JWT keys — safe to rotate (forces re-login but no data loss)
if [ "$ROTATE" = true ]; then
    SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
    REFRESH_TOKEN_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
    METRICS_BEARER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    GULA_ADMIN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
else
    SECRET_KEY="$(keep_or_gen SECRET_KEY \
        'python3 -c "import secrets; print(secrets.token_urlsafe(64))"')"
    REFRESH_TOKEN_SECRET="$(keep_or_gen REFRESH_TOKEN_SECRET \
        'python3 -c "import secrets; print(secrets.token_urlsafe(64))"')"
    METRICS_BEARER_TOKEN="$(keep_or_gen METRICS_BEARER_TOKEN \
        'python3 -c "import secrets; print(secrets.token_urlsafe(32))"')"
    GULA_ADMIN_PASSWORD="$(keep_or_gen GULA_ADMIN_PASSWORD \
        'python3 -c "import secrets; print(secrets.token_urlsafe(24))"')"
fi

# Pull through any existing values for non-secret config
existing_get() {
    local key="$1" default_val="$2"
    if [ -f "$ENV_FILE" ]; then
        local v
        v="$(grep -E "^${key}=" "$ENV_FILE" | head -1 | cut -d= -f2- || true)"
        [ -n "$v" ] && { printf "%s" "$v"; return; }
    fi
    printf "%s" "$default_val"
}
DATABASE_URL="$(existing_get DATABASE_URL '')"
GULA_ADMIN_EMAIL="$(existing_get GULA_ADMIN_EMAIL admin@gula-platform.org)"
BASE_URL="$(existing_get BASE_URL https://gula-platform.org)"
CORS_ORIGINS="$(existing_get CORS_ORIGINS https://gula-platform.org,https://www.gula-platform.org)"

if [ -z "$DATABASE_URL" ]; then
    warn "DATABASE_URL is empty. Get it from Supabase → Settings → Database → Connection pooler"
fi

# ── 2. Write .env.deploy (consumed by docker-compose / scripts) ─────────────
hdr "Writing $ENV_FILE"
cat > "$ENV_FILE" <<EOF
# Generated by scripts/setup-deployment.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
# DO NOT COMMIT — this file is in .gitignore.
ENV=production
ENVIRONMENT=production
DEBUG=false

# ── Database (Supabase pooled URI recommended) ─────────────────────────────
DATABASE_URL=$DATABASE_URL

# ── Redis (leave blank to use in-memory fallback) ──────────────────────────
REDIS_URL=

# ── JWT / encryption secrets ───────────────────────────────────────────────
SECRET_KEY=$SECRET_KEY
REFRESH_TOKEN_SECRET=$REFRESH_TOKEN_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY
NID_HMAC_KEY=$NID_HMAC_KEY
DEVICE_HMAC_KEY=$DEVICE_HMAC_KEY
METRICS_BEARER_TOKEN=$METRICS_BEARER_TOKEN

# ── Bootstrap admin ────────────────────────────────────────────────────────
GULA_ADMIN_EMAIL=$GULA_ADMIN_EMAIL
GULA_ADMIN_NAME=GULA Platform Admin
GULA_ADMIN_PASSWORD=$GULA_ADMIN_PASSWORD

# ── Public URL & CORS ──────────────────────────────────────────────────────
BASE_URL=$BASE_URL
CORS_ORIGINS=$CORS_ORIGINS

# ── Server tuning ──────────────────────────────────────────────────────────
WEB_CONCURRENCY=2
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=10
DB_STMT_TIMEOUT=25s
MAX_CONCURRENT_REQUESTS=50
MAX_REQUEST_BODY_MB=2
AI_BUDGET_SECONDS=6

# ── Feature flags ──────────────────────────────────────────────────────────
ENABLE_API_DOCS=false
CONTROL_LAYER_ENABLED=true
KILL_SWITCH=false
GULA_AUTO_FIX=false
EOF
chmod 600 "$ENV_FILE"
ok "Wrote $ENV_FILE (chmod 600)."

# ── 3. Write copy/paste secrets blob for Render & DO dashboards ─────────────
SECRETS_FILE="$SECRETS_DIR/secrets.txt"
cat > "$SECRETS_FILE" <<EOF
# Paste these into:
#   • Render dashboard → gula-backend → Environment → "Edit"
#   • DO App Platform → Settings → App-Level Environment Variables (Encrypted)
DATABASE_URL=$DATABASE_URL
ENCRYPTION_KEY=$ENCRYPTION_KEY
NID_HMAC_KEY=$NID_HMAC_KEY
DEVICE_HMAC_KEY=$DEVICE_HMAC_KEY
SECRET_KEY=$SECRET_KEY
REFRESH_TOKEN_SECRET=$REFRESH_TOKEN_SECRET
METRICS_BEARER_TOKEN=$METRICS_BEARER_TOKEN
GULA_ADMIN_PASSWORD=$GULA_ADMIN_PASSWORD
GULA_ADMIN_EMAIL=$GULA_ADMIN_EMAIL
EOF
chmod 600 "$SECRETS_FILE"
ok "Wrote $SECRETS_FILE."

# ── 4. Optionally bootstrap Supabase ────────────────────────────────────────
if [ "$SUPABASE_BOOTSTRAP" = true ]; then
    hdr "Supabase bootstrap"
    [ -n "$DATABASE_URL" ] || err "DATABASE_URL is empty — fill it in $ENV_FILE first."
    DATABASE_URL="$DATABASE_URL" bash "$ROOT_DIR/scripts/supabase_bootstrap.sh"
fi

# ── 5. Per-platform next-step summary ───────────────────────────────────────
hdr "Next steps"

case "$PLATFORM" in
    render)
        cat <<EOF

  ${BOLD}Render${NC}
    1. Push this branch to GitHub.
    2. Render dashboard → New → Blueprint → connect this repo → pick render.yaml
    3. When prompted for *Sync: false* secrets, paste from $SECRETS_FILE.
    4. Wait for the first build (~3 min). preDeployCommand runs alembic upgrade head.
    5. Visit https://gula-backend.onrender.com/health ─ expect HTTP 200.

EOF
        ;;
    supabase)
        cat <<EOF

  ${BOLD}Supabase${NC}
    1. Create project at https://supabase.com (Frankfurt region recommended).
    2. Copy the Connection pooler URI (port 6543, sslmode=require) into:
         $ENV_FILE   →   DATABASE_URL=
    3. Re-run with --supabase-bootstrap to apply schema + extensions:
         ./scripts/setup-deployment.sh --platform supabase --supabase-bootstrap

EOF
        ;;
    do-app)
        cat <<EOF

  ${BOLD}DigitalOcean App Platform${NC}
    1. doctl auth init
    2. doctl apps create --spec digitalocean/app.yaml
    3. APP_ID=\$(doctl apps list --format ID,Spec.Name --no-header | grep gula-platform | awk '{print \$1}')
    4. Open the dashboard, replace REPLACE_VIA_DASHBOARD secrets with values
       from $SECRETS_FILE.
    5. doctl apps create-deployment \$APP_ID --force-rebuild

EOF
        ;;
    do-droplet)
        cat <<EOF

  ${BOLD}DigitalOcean Droplet${NC}
    1. doctl compute droplet create gula-prod --image ubuntu-22-04-x64 \\
         --size s-2vcpu-4gb --region fra1 --enable-backups
    2. ssh root@<IP> 'curl -fsSL https://raw.githubusercontent.com/samertts/gula-platform/main/scripts/server-setup.sh | sudo bash'
    3. scp $ENV_FILE samertts@<IP>:~/gula-platform/.env
    4. ssh samertts@<IP> 'cd ~/gula-platform && docker compose up -d'
    5. ./scripts/digitalocean-manage.sh status

EOF
        ;;
    all|"")
        cat <<EOF

  Files generated:
    • $ENV_FILE         — full .env (use locally / docker compose)
    • $SECRETS_FILE     — copy/paste secrets for Render & DO dashboards

  ${BOLD}Choose a target and re-run:${NC}
    ./scripts/setup-deployment.sh --platform render
    ./scripts/setup-deployment.sh --platform supabase --supabase-bootstrap
    ./scripts/setup-deployment.sh --platform do-app
    ./scripts/setup-deployment.sh --platform do-droplet

  All three platforms can run side-by-side: Render hosts the public app,
  Supabase the Postgres, DigitalOcean acts as the geo-failover.

EOF
        ;;
    *)
        err "Unknown --platform '$PLATFORM' (use render|supabase|do-app|do-droplet|all)"
        ;;
esac

ok "Done."
