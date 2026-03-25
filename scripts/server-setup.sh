#!/usr/bin/env bash
# =============================================================================
# GULA PLATFORM - DigitalOcean Server Setup Script
# Run this ONCE on a fresh Ubuntu 22.04 / 24.04 droplet as root
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/samertts/gula-platform/main/scripts/server-setup.sh | sudo bash
#   OR:
#   sudo bash scripts/server-setup.sh
#
# What this does:
#   1. Installs Docker, Nginx, Git, Certbot
#   2. Creates deploy user 'samertts'
#   3. Generates SSH deploy key (for GitHub)
#   4. Clones the repository
#   5. Configures system nginx
#   6. Sets up firewall (UFW)
#   7. Prints all GitHub Secrets you need to add
# =============================================================================
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[1;31m'; GREEN='\033[1;32m'; CYAN='\033[1;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { printf "${CYAN}[setup]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[✓]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[✗]${NC} %s\n" "$*" >&2; exit 1; }

# ── Require root ─────────────────────────────────────────────────────────────
[ "$(id -u)" -eq 0 ] || err "Run as root: sudo bash $0"

DEPLOY_USER="samertts"
REPO_URL="https://github.com/samertts/gula-platform.git"
REPO_DIR="/home/${DEPLOY_USER}/gula-platform"
DOMAIN="gula-platform.org"

log "======================================================="
log " GULA PLATFORM - Server Setup"
log " Server: $(hostname -I | awk '{print $1}')"
log " Date: $(date)"
log "======================================================="

# ── 1. System update ─────────────────────────────────────────────────────────
log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
  curl wget git vim htop ufw fail2ban \
  ca-certificates gnupg lsb-release \
  python3 python3-pip \
  nginx certbot python3-certbot-nginx \
  jq unzip
ok "System packages installed"

# ── 2. Install Docker ─────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Installing Docker..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
  ok "Docker installed"
else
  ok "Docker already installed: $(docker --version)"
fi

# ── 3. Create deploy user ─────────────────────────────────────────────────────
if ! id "$DEPLOY_USER" &>/dev/null; then
  log "Creating user: $DEPLOY_USER..."
  useradd -m -s /bin/bash "$DEPLOY_USER"
  usermod -aG docker "$DEPLOY_USER"
  usermod -aG sudo "$DEPLOY_USER"
  # Allow sudo without password only for the exact nginx/certbot commands needed
  # Note: /bin/cp, /bin/ln, /bin/rm intentionally excluded — too broad
  echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx, /bin/systemctl status nginx, /usr/sbin/nginx -t, /usr/bin/certbot renew, /usr/bin/certbot certonly" \
    > /etc/sudoers.d/gula-deploy
  chmod 440 /etc/sudoers.d/gula-deploy
  ok "User $DEPLOY_USER created"
else
  usermod -aG docker "$DEPLOY_USER" 2>/dev/null || true
  ok "User $DEPLOY_USER already exists"
fi

# ── 4. Generate SSH deploy key ────────────────────────────────────────────────
SSH_DIR="/home/${DEPLOY_USER}/.ssh"
DEPLOY_KEY="${SSH_DIR}/id_ed25519_deploy"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ ! -f "$DEPLOY_KEY" ]; then
  log "Generating SSH deploy key..."
  ssh-keygen -t ed25519 -C "gula-platform-deploy@${DOMAIN}" -f "$DEPLOY_KEY" -N ""
  ok "SSH key generated: $DEPLOY_KEY"
else
  ok "SSH deploy key already exists"
fi

# Set up authorized_keys for GitHub Actions SSH
touch "${SSH_DIR}/authorized_keys"
chmod 600 "${SSH_DIR}/authorized_keys"

# Allow the deploy key to login (for GitHub Actions)
DEPLOY_PUBKEY=$(cat "${DEPLOY_KEY}.pub")
if ! grep -qF "$DEPLOY_PUBKEY" "${SSH_DIR}/authorized_keys" 2>/dev/null; then
  echo "$DEPLOY_PUBKEY" >> "${SSH_DIR}/authorized_keys"
  ok "Deploy public key added to authorized_keys"
fi

chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "$SSH_DIR"

# ── 5. Clone repository ───────────────────────────────────────────────────────
if [ ! -d "$REPO_DIR/.git" ]; then
  log "Cloning repository..."
  sudo -u "$DEPLOY_USER" git clone "$REPO_URL" "$REPO_DIR"
  ok "Repository cloned to $REPO_DIR"
else
  log "Repository already exists, pulling latest..."
  sudo -u "$DEPLOY_USER" git -C "$REPO_DIR" pull origin main || true
  ok "Repository updated"
fi

# Set correct ownership
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "$REPO_DIR"

# ── 6. Configure system Nginx ─────────────────────────────────────────────────
log "Configuring system nginx..."

# Create certbot webroot
mkdir -p /var/www/certbot

# Copy HTTP-only config (works immediately, before SSL)
cp "${REPO_DIR}/config/nginx/system/gula-platform-http.conf" \
   /etc/nginx/sites-available/gula-platform

ln -sf /etc/nginx/sites-available/gula-platform \
       /etc/nginx/sites-enabled/gula-platform

# Remove default nginx site
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
nginx -t && systemctl reload nginx
ok "System nginx configured (HTTP mode)"

# ── 7. Firewall (UFW) ─────────────────────────────────────────────────────────
log "Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment "SSH"
ufw allow 80/tcp   comment "HTTP"
ufw allow 443/tcp  comment "HTTPS"
ufw --force enable
ok "Firewall configured (22, 80, 443 open)"

# ── 8. Fail2ban ───────────────────────────────────────────────────────────────
log "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF
systemctl enable --now fail2ban
ok "Fail2ban configured"

# ── 9. Create .env file template ─────────────────────────────────────────────
if [ ! -f "${REPO_DIR}/.env" ]; then
  log "Creating .env template..."
  gen_secret() { python3 -c 'import secrets; print(secrets.token_urlsafe(32))'; }
  PG_PASS=$(gen_secret)
  REDIS_PASS=$(gen_secret)

  cat > "${REPO_DIR}/.env" << ENVEOF
# ===== GULA PLATFORM - Production Environment =====
# Generated: $(date)
# Server: $(hostname -I | awk '{print $1}')

# Database
POSTGRES_PASSWORD=${PG_PASS}
DATABASE_URL=postgresql://postgres:${PG_PASS}@postgres:5432/labdb

# Cache
REDIS_PASSWORD=${REDIS_PASS}
REDIS_URL=redis://:${REDIS_PASS}@redis:6379

# Security
SECRET_KEY=$(gen_secret)
ENCRYPTION_KEY=$(gen_secret)
NID_HMAC_KEY=$(gen_secret)

# App
ENVIRONMENT=production
DOMAIN=${DOMAIN}
ENVEOF

  chown "${DEPLOY_USER}:${DEPLOY_USER}" "${REPO_DIR}/.env"
  chmod 600 "${REPO_DIR}/.env"
  ok ".env created"
else
  ok ".env already exists"
fi

# ── 10. Swap space (important for small droplets) ─────────────────────────────
if [ ! -f /swapfile ]; then
  log "Creating 2GB swap space..."
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  ok "Swap created (2GB)"
else
  ok "Swap already configured"
fi

# ── 10b. Kernel / OS performance tuning ───────────────────────────────────────
# Apply GULA-specific sysctl and ulimit overrides for high-throughput operation.
# These settings raise fd limits, tune TCP buffers and TIME_WAIT recycling,
# reduce swappiness, and generally match nginx + Docker + PostgreSQL workloads.
log "Applying kernel tuning (sysctl + limits)..."

# sysctl — takes effect immediately and persists across reboots via /etc/sysctl.d/
cp "${REPO_DIR}/config/system/99-gula-sysctl.conf" /etc/sysctl.d/99-gula.conf
sysctl --system --pattern "fs.file-max|net.core|net.ipv4.tcp|vm.swappiness|vm.dirty" > /dev/null 2>&1 || \
  sysctl -p /etc/sysctl.d/99-gula.conf > /dev/null 2>&1 || true
ok "sysctl applied (/etc/sysctl.d/99-gula.conf)"

# ulimits — take effect for new sessions / service restarts
cp "${REPO_DIR}/config/system/gula-limits.conf" /etc/security/limits.d/99-gula.conf
ok "ulimits applied (/etc/security/limits.d/99-gula.conf)"

# ── 11. Nginx systemd override: Restart=always ───────────────────────────────
# By default systemd stops retrying nginx after consecutive failures.
# This drop-in ensures nginx is ALWAYS restarted, with nginx-ensure.sh
# running first to pick the right config (HTTP vs HTTPS).
log "Configuring nginx systemd override..."
mkdir -p /etc/systemd/system/nginx.service.d
cat > /etc/systemd/system/nginx.service.d/gula-restart.conf << 'NGINXEOF'
[Service]
Restart=always
RestartSec=5s
# Run nginx-ensure.sh before each start: picks HTTP or HTTPS config
# based on whether SSL certs exist. Prevents startup failures.
ExecStartPre=/bin/bash /home/samertts/gula-platform/scripts/nginx-ensure.sh
NGINXEOF
systemctl daemon-reload
systemctl enable nginx
ok "nginx systemd override installed (Restart=always + smart config)"

# ── 12. Docker system service (auto-start on reboot) ─────────────────────────
cat > /etc/systemd/system/gula-platform.service << SERVICEEOF
[Unit]
Description=GULA Platform Docker Compose
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=${DEPLOY_USER}
WorkingDirectory=${REPO_DIR}
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable gula-platform.service
ok "Auto-start service configured"

# ── 13. Cron: auto_heal.sh every 5 minutes ───────────────────────────────────
log "Installing watchdog cron..."
chmod +x "${REPO_DIR}/scripts/auto_heal.sh"
chmod +x "${REPO_DIR}/scripts/nginx-ensure.sh"

# Allow deploy user to call nginx commands without password
SUDOERS_FILE="/etc/sudoers.d/gula-deploy"
cat > "$SUDOERS_FILE" << SUDOEOF
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl start nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl reset-failed nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /usr/sbin/nginx
${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/bash ${REPO_DIR}/scripts/nginx-ensure.sh
SUDOEOF
chmod 440 "$SUDOERS_FILE"

# Install cron for deploy user
CRON_JOB="*/5 * * * * GULA_DIR=${REPO_DIR} ${REPO_DIR}/scripts/auto_heal.sh >> /var/log/gula-heal.log 2>&1"
( crontab -u "$DEPLOY_USER" -l 2>/dev/null | grep -v "auto_heal" ; echo "$CRON_JOB" ) \
    | crontab -u "$DEPLOY_USER" -

touch /var/log/gula-heal.log
chown "${DEPLOY_USER}:${DEPLOY_USER}" /var/log/gula-heal.log
ok "Watchdog cron installed (every 5 minutes)"

# ── 14. Run nginx-ensure.sh now to start nginx correctly ─────────────────────
log "Starting nginx with correct config..."
bash "${REPO_DIR}/scripts/nginx-ensure.sh" && ok "nginx started" \
    || warn "nginx-ensure.sh failed (may need SSL setup first)"

# ── Summary ────────────────────────────────────────────────────────────────────
SERVER_IP=$(hostname -I | awk '{print $1}')
PRIVATE_KEY=$(cat "${DEPLOY_KEY}")
PUBLIC_KEY=$(cat "${DEPLOY_KEY}.pub")

echo ""
echo "============================================================"
echo -e "${GREEN} SETUP COMPLETE! ${NC}"
echo "============================================================"
echo ""
echo -e "${YELLOW}=== ADD THESE TO GITHUB SECRETS ===${NC}"
echo -e "${CYAN}(Settings → Secrets → Actions → New repository secret)${NC}"
echo ""
echo -e "${YELLOW}Secret 1: SERVER_HOST${NC}"
echo "$SERVER_IP"
echo ""
echo -e "${YELLOW}Secret 2: SERVER_USER${NC}"
echo "$DEPLOY_USER"
echo ""
echo -e "${YELLOW}Secret 3: SERVER_SSH_KEY${NC}"
echo "Copy the ENTIRE block below (including BEGIN and END lines):"
echo "------------------------------------------------------------"
echo "$PRIVATE_KEY"
echo "------------------------------------------------------------"
echo ""
echo -e "${YELLOW}=== NEXT STEPS ===${NC}"
echo "1. Add the 3 secrets above to GitHub"
echo "2. Push to 'main' branch to trigger auto-deploy"
echo "3. (Optional) Run SSL setup after first deploy:"
echo "   sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
echo ""
echo -e "${YELLOW}=== SERVER INFO ===${NC}"
echo "IP Address:   $SERVER_IP"
echo "Deploy User:  $DEPLOY_USER"
echo "Project Dir:  $REPO_DIR"
echo "Nginx Config: /etc/nginx/sites-enabled/gula-platform"
echo ""
echo -e "${GREEN}Platform will be available at: http://${SERVER_IP}${NC}"
echo "============================================================"
