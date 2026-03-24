#!/usr/bin/env bash
# =============================================================================
# GULA PLATFORM — One-Command Production Setup
# منصة غولا الصحية — إعداد الإنتاج بأمر واحد
#
# Usage:
#   chmod +x setup-production.sh
#   sudo ./setup-production.sh
#
# What this script does:
#   1. Validates prerequisites (Docker, compose, .env)
#   2. Generates missing secrets automatically
#   3. Creates required directories and log files
#   4. Sets correct file permissions
#   5. Builds and starts all containers
#   6. Runs database migrations
#   7. Verifies health checks pass
#   8. Prints access instructions
# =============================================================================
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()   { echo -e "${GREEN}[✓] $*${NC}"; }
warn() { echo -e "${YELLOW}[!] $*${NC}"; }
err()  { echo -e "${RED}[✗] $*${NC}" >&2; }
die()  { err "$*"; exit 1; }
hr()   { echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

hr
echo -e "${BOLD}  GULA Platform — Production Setup${NC}"
echo -e "${BOLD}  منصة غولا الصحية — إعداد الإنتاج${NC}"
hr

# ── Step 1: Prerequisites ────────────────────────────────────────────────────
log "Checking prerequisites..."

command -v docker >/dev/null 2>&1  || die "Docker not installed. Install from https://docs.docker.com/get-docker/"
command -v python3 >/dev/null 2>&1 || die "python3 required for key generation"

# Detect compose command (v2: 'docker compose', v1: 'docker-compose')
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    die "Docker Compose not found. Install with: sudo apt-get install docker-compose-plugin"
fi

DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+' | head -1)
ok "Docker $DOCKER_VERSION found"
ok "$COMPOSE found"

# ── Step 2: .env File ────────────────────────────────────────────────────────
log "Checking .env configuration..."

if [ ! -f .env ]; then
    warn ".env not found — creating from .env.example"
    cp .env.example .env
    warn "IMPORTANT: .env was just created with placeholder values."
    warn "You MUST review and fill in the CHANGE_ME values before using in production."
    warn "Opening .env for editing in 5 seconds... (Ctrl+C to skip)"
    sleep 5
    ${EDITOR:-nano} .env || true
fi

# ── Step 3: Auto-generate missing secrets ────────────────────────────────────
log "Checking and generating secrets..."

_gen_secret()   { python3 -c "import secrets; print(secrets.token_urlsafe(64))"; }
_gen_hex()      { python3 -c "import secrets; print(secrets.token_hex(32))"; }
_gen_fernet()   { python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"; }
_gen_password() { python3 -c "import secrets,string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(32)))"; }

_ensure_env() {
    local key="$1"
    local generator="$2"
    local current
    current=$(grep -E "^${key}=" .env | cut -d= -f2- | tr -d '"' || true)
    if [ -z "$current" ] || echo "$current" | grep -q "CHANGE_ME"; then
        local val
        val=$(eval "$generator")
        # Replace or append
        if grep -q "^${key}=" .env; then
            sed -i "s|^${key}=.*|${key}=${val}|" .env
        else
            echo "${key}=${val}" >> .env
        fi
        warn "Auto-generated ${key}"
    fi
}

_ensure_env "SECRET_KEY"           "_gen_secret"
_ensure_env "REFRESH_TOKEN_SECRET" "_gen_secret"
_ensure_env "ENCRYPTION_KEY"       "_gen_fernet"
_ensure_env "NID_HMAC_KEY"         "_gen_hex"
_ensure_env "DEVICE_HMAC_KEY"      "_gen_hex"
_ensure_env "POSTGRES_PASSWORD"    "_gen_password"
_ensure_env "REDIS_PASSWORD"       "_gen_password"

ok "All secrets present"

# Warn if admin password is still a placeholder
_admin_pw=$(grep "^GULA_ADMIN_PASSWORD=" .env | cut -d= -f2- || true)
if echo "$_admin_pw" | grep -q "CHANGE_ME"; then
    warn "GULA_ADMIN_PASSWORD is still a placeholder — set a strong password in .env!"
fi

# ── Step 4: Directories and Permissions ──────────────────────────────────────
log "Creating required directories..."

mkdir -p logs/nginx data config/ssl
chmod 755 logs logs/nginx data
# nginx log files must be writable
touch logs/nginx/access.log logs/nginx/error.log logs/nginx/access.json
chmod 644 logs/nginx/access.log logs/nginx/error.log logs/nginx/access.json

# config/ssl: store TLS certificates here
chmod 700 config/ssl 2>/dev/null || true

ok "Directories created"

# ── Step 5: Kernel Tuning (optional, requires root) ──────────────────────────
if [ "$(id -u)" = "0" ]; then
    log "Applying kernel tuning for high concurrency..."

    # Increase connection backlog and TIME_WAIT recycling
    sysctl -w net.core.somaxconn=65535              >/dev/null 2>&1 || true
    sysctl -w net.ipv4.tcp_max_syn_backlog=65535     >/dev/null 2>&1 || true
    sysctl -w net.ipv4.tcp_fin_timeout=15            >/dev/null 2>&1 || true
    sysctl -w net.ipv4.tcp_tw_reuse=1               >/dev/null 2>&1 || true
    sysctl -w net.core.netdev_max_backlog=65535      >/dev/null 2>&1 || true
    # Increase file descriptor limits
    sysctl -w fs.file-max=2097152                    >/dev/null 2>&1 || true

    # Persist across reboots
    cat > /etc/sysctl.d/99-gula.conf << 'EOF'
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.core.netdev_max_backlog = 65535
fs.file-max = 2097152
EOF
    ok "Kernel tuning applied"
else
    warn "Not running as root — skipping kernel tuning (run with sudo for optimal performance)"
fi

# ── Step 6: Build and Start ───────────────────────────────────────────────────
log "Building and starting GULA Platform..."
hr

# Load .env for docker compose
export $(grep -v '^#' .env | grep -v '^$' | xargs) 2>/dev/null || true

# Pull base images first (speeds up build)
log "Pulling base images..."
$COMPOSE pull --ignore-pull-failures postgres redis 2>/dev/null || true

# Build backend
log "Building backend..."
$COMPOSE build --no-cache gula-backend || die "Backend build failed"

# Start database and cache first
log "Starting database and cache..."
$COMPOSE up -d postgres redis

# Wait for postgres to be healthy
log "Waiting for PostgreSQL to be ready..."
_max=60; _i=0
while ! $COMPOSE exec -T postgres pg_isready -U postgres -d labdb >/dev/null 2>&1; do
    sleep 2; _i=$((_i+2))
    [ $_i -ge $_max ] && die "PostgreSQL did not become ready in ${_max}s"
    echo -n "."
done
echo ""
ok "PostgreSQL is ready"

# Start remaining services
log "Starting all services..."
$COMPOSE up -d --remove-orphans

# ── Step 7: Health Check ─────────────────────────────────────────────────────
log "Waiting for backend to pass health check..."
_max=120; _i=0
while true; do
    sleep 3; _i=$((_i+3))
    status=$($COMPOSE exec -T gula-backend python3 -c \
        "import urllib.request,sys; r=urllib.request.urlopen('http://localhost:8000/health/ready',timeout=5); sys.exit(0 if r.status==200 else 1)" \
        2>/dev/null && echo "ok" || echo "wait")
    if [ "$status" = "ok" ]; then
        ok "Backend is healthy and ready"
        break
    fi
    echo -n "."
    [ $_i -ge $_max ] && {
        warn "Backend not ready after ${_max}s — showing logs:"
        $COMPOSE logs --tail=50 gula-backend
        die "Backend health check failed"
    }
done

# Check nginx gateway
_gw_code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080/health" 2>/dev/null || echo "000")
if [ "$_gw_code" = "200" ]; then
    ok "API Gateway is responding (HTTP $_gw_code)"
else
    warn "API Gateway returned HTTP $_gw_code — check nginx logs"
fi

# ── Step 8: Final Status ─────────────────────────────────────────────────────
hr
echo -e "${GREEN}${BOLD}"
echo "  ✓ GULA Platform is running!"
echo "  ✓ منصة غولا الصحية تعمل بنجاح!"
echo -e "${NC}"

echo -e "${CYAN}Services:${NC}"
$COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

hr
echo -e "${CYAN}Access Points:${NC}"
BASE_URL_VAL=$(grep "^BASE_URL=" .env | cut -d= -f2- || echo "http://localhost")
echo -e "  🌐 Platform:    ${BOLD}http://127.0.0.1:8080/${NC}"
echo -e "  🔧 Health:      ${BOLD}http://127.0.0.1:8080/health/ready${NC}"
if grep "^ENABLE_API_DOCS=true" .env >/dev/null 2>&1; then
    echo -e "  📖 API Docs:    ${BOLD}http://127.0.0.1:8080/docs${NC}"
fi

hr
echo -e "${YELLOW}${BOLD}Next Steps:${NC}"
echo "  1. Configure your domain in .env (BASE_URL, CORS_ORIGINS)"
echo "  2. Set up HTTPS: bash scripts/setup-https.sh"
echo "  3. Change the admin password: bash scripts/change-master-password.sh"
echo "  4. Monitor logs: docker compose logs -f gula-backend"
echo "  5. View status:  docker compose ps"
hr
