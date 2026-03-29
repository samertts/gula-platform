#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Development Quick Start
# Usage: bash scripts/start-dev.sh
#
# This script:
#   1. Checks that .env exists and has all required secrets filled in
#   2. Generates missing secrets automatically (safe for dev)
#   3. Starts docker compose in detached mode
#   4. Waits for the backend to become ready (up to 3 minutes)
#   5. Prints the access URL
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'
info()    { echo -e "${GREEN}[GULA]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── 1. Ensure .env exists ─────────────────────────────────────────────────────
if [ ! -f .env ]; then
    warn ".env not found — copying from template"
    cp .env .env.bak 2>/dev/null || true
fi

# ── 2. Auto-generate missing secrets ─────────────────────────────────────────
py3() { python3 -c "$1"; }

fill_if_placeholder() {
    local var="$1"
    local generator="$2"
    local current
    current=$(grep "^${var}=" .env | cut -d= -f2-)
    if [[ "$current" == *"CHANGE_ME"* || -z "$current" ]]; then
        local value
        value=$(py3 "$generator")
        # Use | as sed delimiter to avoid issues with / in base64 values
        sed -i "s|^${var}=.*|${var}=${value}|" .env
        info "Generated ${var}"
    fi
}

fill_if_placeholder "SECRET_KEY"            "import secrets; print(secrets.token_urlsafe(64))"
fill_if_placeholder "REFRESH_TOKEN_SECRET"  "import secrets; print(secrets.token_urlsafe(64))"
fill_if_placeholder "ENCRYPTION_KEY"        "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
fill_if_placeholder "NID_HMAC_KEY"          "import secrets; print(secrets.token_hex(32))"
fill_if_placeholder "DEVICE_HMAC_KEY"       "import secrets; print(secrets.token_hex(32))"
fill_if_placeholder "POSTGRES_PASSWORD"     "import secrets; print(secrets.token_urlsafe(24))"
fill_if_placeholder "REDIS_PASSWORD"        "import secrets; print(secrets.token_urlsafe(24))"
fill_if_placeholder "GULA_ADMIN_PASSWORD"   "import secrets; print('Admin-' + secrets.token_urlsafe(12))"

# Set debug-friendly values for dev
sed -i "s|^ENV=.*|ENV=development|" .env 2>/dev/null || true
sed -i "s|^DEBUG=.*|DEBUG=true|" .env 2>/dev/null || true
sed -i "s|^ENABLE_API_DOCS=.*|ENABLE_API_DOCS=true|" .env 2>/dev/null || true

# ── 3. Start docker compose ───────────────────────────────────────────────────
info "Starting GULA Platform..."
docker compose up -d --build --remove-orphans

# ── 4. Wait for backend ready ─────────────────────────────────────────────────
info "Waiting for backend to become ready..."
MAX_WAIT=180
WAITED=0
INTERVAL=5
until curl -sf http://127.0.0.1:8080/health/ready > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        error "Backend did not become ready after ${MAX_WAIT}s"
        echo ""
        warn "Container logs:"
        docker compose logs --tail=30 gula-backend
        exit 1
    fi
    sleep $INTERVAL
    WAITED=$((WAITED + INTERVAL))
    echo -n "."
done
echo ""

# ── 5. Print summary ──────────────────────────────────────────────────────────
info "GULA Platform is running!"
echo ""
echo "  🌐 Staff Portal:     http://localhost:8080/"
echo "  🔬 Citizen Portal:   http://localhost:8080/citizen/login.html"
echo "  📊 API Docs:         http://localhost:8080/docs"
echo "  💊 Health Check:     http://localhost:8080/health/deep"
echo ""
ADMIN_EMAIL=$(grep "^GULA_ADMIN_EMAIL=" .env | cut -d= -f2-)
ADMIN_PASS=$(grep "^GULA_ADMIN_PASSWORD=" .env | cut -d= -f2-)
echo "  🔑 Master Admin:"
echo "     Email:    ${ADMIN_EMAIL}"
echo "     Password: ${ADMIN_PASS}"
echo ""
echo "  Logs: docker compose logs -f gula-backend"
echo "  Stop: docker compose down"
