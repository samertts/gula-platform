#!/usr/bin/env bash
# =============================================================================
# GULA PLATFORM — Emergency One-Shot Fix
#
# Run this ONCE on the server to permanently fix nginx + watchdog:
#   curl -fsSL https://raw.githubusercontent.com/... | sudo bash
#   OR:
#   sudo bash /home/samertts/gula-platform/scripts/emergency-fix.sh
#
# What it does:
#   1. Diagnoses current state (nginx, Docker, ports, disk)
#   2. Fixes nginx immediately (HTTP or HTTPS depending on cert presence)
#   3. Installs systemd drop-in so nginx NEVER stays down after reboot
#   4. Installs cron watchdog every 5 minutes
#   5. Adds sudoers rules so watchdog can restart nginx without password
#   6. Verifies the site responds on port 80
# =============================================================================
set -uo pipefail

REPO_DIR="/home/samertts/gula-platform"
DEPLOY_USER="${DEPLOY_USER:-samertts}"
LOG="/var/log/gula-emergency-fix.log"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}  $*" | tee -a "$LOG"; }
fail() { echo -e "${RED}[FAIL]${NC} $*" | tee -a "$LOG"; }
info() { echo -e "${YELLOW}[INFO]${NC} $*" | tee -a "$LOG"; }
hr()   { echo "─────────────────────────────────────────────────────" | tee -a "$LOG"; }

echo "" | tee -a "$LOG"
hr
echo "$(date '+%Y-%m-%d %H:%M:%S') GULA Emergency Fix Started" | tee -a "$LOG"
hr

# Must run as root
if [ "$(id -u)" -ne 0 ]; then
    fail "Must run as root: sudo bash $0"
    exit 1
fi

# ─── STEP 0: Diagnose current state ──────────────────────────────────────────
info "--- DIAGNOSIS ---"

# nginx
NGINX_STATE=$(systemctl is-active nginx 2>/dev/null || echo "not-found")
NGINX_ENABLED=$(systemctl is-enabled nginx 2>/dev/null || echo "unknown")
info "nginx: state=${NGINX_STATE} enabled=${NGINX_ENABLED}"
systemctl status nginx --no-pager -l 2>&1 | tail -10 | tee -a "$LOG" || true

# Ports
info "Ports listening:"
ss -tlnp | grep -E ':80|:443|:8080' | tee -a "$LOG" || true

# Docker
DOCKER_STATE=$(systemctl is-active docker 2>/dev/null || echo "not-found")
info "Docker daemon: ${DOCKER_STATE}"
if command -v docker &>/dev/null && systemctl is-active --quiet docker; then
    docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | tee -a "$LOG" || true
fi

# Disk
info "Disk usage:"
df -h / /var /home 2>/dev/null | tee -a "$LOG" || df -h / | tee -a "$LOG"

# SSL cert
CERT_PATH="/etc/letsencrypt/live/gula-platform.org/fullchain.pem"
if [ -f "$CERT_PATH" ]; then
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_PATH" 2>/dev/null | cut -d= -f2 || echo "unknown")
    info "SSL cert: EXISTS — expires ${CERT_EXPIRY}"
else
    info "SSL cert: NOT FOUND — will use HTTP-only mode"
fi

hr

# ─── STEP 1: Pull latest code ─────────────────────────────────────────────────
info "--- STEP 1: Pull latest code ---"
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR"
    sudo -u "$DEPLOY_USER" git fetch origin 2>&1 | tee -a "$LOG" || true
    sudo -u "$DEPLOY_USER" git pull origin claude/server-image-branching-iyurJ 2>&1 | tee -a "$LOG" \
        && ok "Code updated" \
        || { info "git pull failed — continuing with existing code"; }
else
    fail "Repo not found at $REPO_DIR — clone it first"
    exit 1
fi

# Make scripts executable
chmod +x "${REPO_DIR}/scripts/"*.sh 2>/dev/null || true

# ─── STEP 2: Install HTTP-only nginx config (needed by nginx-ensure.sh) ───────
info "--- STEP 2: Ensure nginx configs exist ---"
HTTP_CONF="${REPO_DIR}/config/nginx/system/gula-platform-http.conf"
HTTPS_CONF="${REPO_DIR}/config/nginx/system/gula-platform.conf"

if [ ! -f "$HTTP_CONF" ]; then
    info "Creating HTTP-only nginx config..."
    mkdir -p "${REPO_DIR}/config/nginx/system"
    cat > "$HTTP_CONF" << 'NGINX_HTTP'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name gula-platform.org www.gula-platform.org _;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 10s;
        proxy_read_timeout 60s;
        proxy_send_timeout 30s;
    }

    client_max_body_size 50M;
}
NGINX_HTTP
    ok "HTTP-only config created"
fi

[ -f "$HTTP_CONF" ] && ok "HTTP config: $HTTP_CONF" || fail "HTTP config MISSING"
[ -f "$HTTPS_CONF" ] && ok "HTTPS config: $HTTPS_CONF" || info "HTTPS config not present (OK if no cert)"

# ─── STEP 3: Fix nginx RIGHT NOW ─────────────────────────────────────────────
info "--- STEP 3: Fix nginx immediately ---"

# Install nginx if missing
if ! command -v nginx &>/dev/null; then
    info "nginx not installed — installing..."
    apt-get update -qq && apt-get install -y nginx
fi

# Reset any failed state
systemctl reset-failed nginx 2>/dev/null || true

# Pick config
if [ -f "$CERT_PATH" ]; then
    ACTIVE_CONF="$HTTPS_CONF"
    MODE="HTTPS"
else
    ACTIVE_CONF="$HTTP_CONF"
    MODE="HTTP-only"
fi

# Install config
cp "$ACTIVE_CONF" /etc/nginx/sites-available/gula-platform
ln -sf /etc/nginx/sites-available/gula-platform /etc/nginx/sites-enabled/gula-platform
rm -f /etc/nginx/sites-enabled/default

# Test config
if nginx -t 2>>"$LOG"; then
    ok "nginx config valid ($MODE)"
else
    fail "nginx config failed — falling back to HTTP-only"
    cp "$HTTP_CONF" /etc/nginx/sites-available/gula-platform
    nginx -t 2>>"$LOG" || { fail "Even HTTP config fails — check nginx install"; exit 1; }
    MODE="HTTP-only (fallback)"
fi

# Enable and start nginx
systemctl enable nginx 2>/dev/null || true

if systemctl is-active --quiet nginx; then
    systemctl reload nginx && ok "nginx reloaded ($MODE)"
else
    systemctl start nginx && ok "nginx started ($MODE)"
fi

# Wait and verify
sleep 2
if ss -tlnp | grep -q ':80 '; then
    ok "Port 80 is LISTENING"
else
    fail "Port 80 still not listening — forcing restart"
    systemctl restart nginx
    sleep 3
    ss -tlnp | grep -q ':80 ' && ok "Port 80 listening after restart" || fail "PORT 80 STILL DEAD — check 'journalctl -u nginx -n 50'"
fi

# ─── STEP 4: Systemd drop-in (nginx restarts on crash + uses nginx-ensure.sh) ─
info "--- STEP 4: Install systemd drop-in ---"
DROPIN_DIR="/etc/systemd/system/nginx.service.d"
mkdir -p "$DROPIN_DIR"
cat > "${DROPIN_DIR}/gula-restart.conf" << DROPIN
[Service]
Restart=always
RestartSec=5s
ExecStartPre=/bin/bash ${REPO_DIR}/scripts/nginx-ensure.sh
DROPIN

systemctl daemon-reload
ok "systemd drop-in installed: nginx will auto-restart + use nginx-ensure.sh"

# ─── STEP 5: Docker containers ───────────────────────────────────────────────
info "--- STEP 5: Check/start Docker containers ---"
if systemctl is-active --quiet docker; then
    cd "$REPO_DIR"
    DOCKER_COMPOSE_CMD="docker compose"
    $DOCKER_COMPOSE_CMD -f docker-compose.yml up -d 2>&1 | tee -a "$LOG" \
        && ok "Docker containers started" \
        || fail "docker compose failed — check logs with: docker compose logs"
else
    fail "Docker daemon is down — starting..."
    systemctl start docker && sleep 5
    cd "$REPO_DIR"
    docker compose -f docker-compose.yml up -d 2>&1 | tee -a "$LOG" || true
fi

# ─── STEP 6: Cron watchdog ───────────────────────────────────────────────────
info "--- STEP 6: Install cron watchdog ---"
CRON_JOB="*/5 * * * * GULA_DIR=${REPO_DIR} ${REPO_DIR}/scripts/auto_heal.sh >> /var/log/gula-heal.log 2>&1"
( crontab -u "$DEPLOY_USER" -l 2>/dev/null | grep -v "auto_heal" ; echo "$CRON_JOB" ) \
    | crontab -u "$DEPLOY_USER" - \
    && ok "Cron watchdog installed (every 5 min)" \
    || fail "Failed to install cron"

# Verify
crontab -u "$DEPLOY_USER" -l 2>/dev/null | grep -q "auto_heal" \
    && ok "Cron verified: $(crontab -u "$DEPLOY_USER" -l | grep auto_heal)" \
    || fail "Cron NOT installed"

# ─── STEP 7: Sudoers rules ───────────────────────────────────────────────────
info "--- STEP 7: Sudoers rules for watchdog ---"
SUDOERS_FILE="/etc/sudoers.d/gula-nginx"
cat > "$SUDOERS_FILE" << SUDOERS
# GULA Platform: allow deploy user to manage nginx without password
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl start nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl stop nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl reset-failed nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/bash ${REPO_DIR}/scripts/nginx-ensure.sh
SUDOERS
chmod 440 "$SUDOERS_FILE"
visudo -c -f "$SUDOERS_FILE" 2>>"$LOG" \
    && ok "Sudoers rules installed" \
    || { fail "Sudoers syntax error — removing"; rm -f "$SUDOERS_FILE"; }

# ─── STEP 8: Final verification ──────────────────────────────────────────────
hr
info "--- FINAL VERIFICATION ---"
sleep 3

# nginx status
systemctl is-active --quiet nginx \
    && ok "nginx: RUNNING" \
    || fail "nginx: STILL DOWN — run: journalctl -u nginx -n 30"

# Port 80
ss -tlnp | grep -q ':80 ' \
    && ok "Port 80: LISTENING" \
    || fail "Port 80: NOT listening"

# Local HTTP test
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    ok "HTTP response: ${HTTP_CODE} — site is UP"
elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
    fail "HTTP response: ${HTTP_CODE} — nginx OK but Docker containers may be starting (wait 30s)"
else
    fail "HTTP response: ${HTTP_CODE} — unexpected"
fi

# Health endpoint
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/health 2>/dev/null || echo "000")
[ "$HEALTH_CODE" = "200" ] \
    && ok "/health: 200 OK — backend is reachable" \
    || info "/health: ${HEALTH_CODE} (backend may still be starting)"

hr
echo "" | tee -a "$LOG"
echo "Full log: $LOG" | tee -a "$LOG"
echo "" | tee -a "$LOG"

# Summary
if systemctl is-active --quiet nginx && ss -tlnp | grep -q ':80 '; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  SITE IS UP — nginx running, port 80 listening       ${NC}"
    echo -e "${GREEN}  Watchdog active: every 5 min via cron               ${NC}"
    echo -e "${GREEN}  nginx auto-restart: systemd Restart=always          ${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  STILL DOWN — check: journalctl -u nginx -n 50       ${NC}"
    echo -e "${RED}  And: docker compose logs --tail=30                  ${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
