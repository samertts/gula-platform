#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Dedicated AI Server Setup
# Run ONCE on a fresh Ubuntu 24.04 droplet (≥8 GB RAM recommended).
#
# Usage:
#   sudo bash scripts/setup-ai-server.sh
#
# What this does:
#   1. Installs Docker + docker-compose-plugin
#   2. Installs Ollama
#   3. Pulls AI models (RAM-aware selection)
#   4. Configures firewall (only port 22 + 11435 open)
#   5. Generates OLLAMA_ACCESS_TOKEN
#   6. Starts the AI gateway (nginx + Ollama via docker compose)
#   7. Prints the config to paste into core server .env
#
# After setup, add to CORE SERVER .env:
#   OLLAMA_BASE_URL=http://AI_SERVER_IP:11435
#   OLLAMA_ACCESS_TOKEN=<printed below>
#   OLLAMA_MAX_CONCURRENT=2
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }
info() { echo -e "${CYAN}[→]${NC} $*"; }

[ "$(id -u)" -eq 0 ] || err "Run as root: sudo bash $0"

SERVER_IP=$(hostname -I | awk '{print $1}')
TOTAL_RAM_GB=$(awk '/MemTotal/ {print int($2/1024/1024)}' /proc/meminfo)
REPO_DIR="${1:-/home/$(logname 2>/dev/null || echo ubuntu)/gula-platform}"

echo ""
echo -e "${BOLD}=== GULA AI Server Setup ===${NC}"
echo "  IP:  $SERVER_IP"
echo "  RAM: ${TOTAL_RAM_GB} GB"
echo ""

# ── 1. System update ──────────────────────────────────────────────────────────
info "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl wget git ufw ca-certificates gnupg python3
ok "System packages ready"

# ── 2. Install Docker ─────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
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

# ── 3. Install Ollama ─────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    info "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    ok "Ollama installed"
else
    ok "Ollama already installed: $(ollama --version 2>/dev/null || echo 'ok')"
fi

# Start Ollama service
systemctl enable --now ollama 2>/dev/null || ollama serve &>/tmp/ollama.log &
sleep 3

until curl -sf http://localhost:11434/api/tags &>/dev/null; do
    sleep 2
done
ok "Ollama service running"

# ── 4. Pull models (RAM-aware) ────────────────────────────────────────────────
info "Pulling system optimizer model (llama3.2:1b — 700 MB)..."
ollama pull llama3.2:1b

if [[ $TOTAL_RAM_GB -ge 16 ]]; then
    info "RAM ≥16 GB — pulling aya:8b (best Arabic quality, 4.8 GB)..."
    ollama pull aya:8b
    CLINICAL_MODEL="aya:8b"
elif [[ $TOTAL_RAM_GB -ge 8 ]]; then
    info "RAM ${TOTAL_RAM_GB} GB — pulling llama3.2:3b (good Arabic, 2 GB)..."
    ollama pull llama3.2:3b
    CLINICAL_MODEL="llama3.2:3b"
else
    warn "RAM only ${TOTAL_RAM_GB} GB — using llama3.2:3b (minimum viable)"
    ollama pull llama3.2:3b
    CLINICAL_MODEL="llama3.2:3b"
fi
ok "Models installed"

# ── 5. Generate access token ──────────────────────────────────────────────────
ACCESS_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
ok "Generated OLLAMA_ACCESS_TOKEN"

# ── 6. Create .env.ai for docker-compose.ai.yml ───────────────────────────────
if [[ -d "$REPO_DIR" ]]; then
    cat > "${REPO_DIR}/.env.ai" << ENVEOF
# GULA AI Node — environment file
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
OLLAMA_ACCESS_TOKEN=${ACCESS_TOKEN}
OLLAMA_MEM_LIMIT=$((TOTAL_RAM_GB * 1024 * 6 / 10))m
OLLAMA_CPUS=3.5
ENVEOF
    chmod 600 "${REPO_DIR}/.env.ai"
    ok ".env.ai created"
fi

# ── 7. Firewall ───────────────────────────────────────────────────────────────
info "Configuring firewall..."
ufw --force reset &>/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH"
ufw allow 11435/tcp comment "GULA AI Gateway (nginx → Ollama)"
ufw --force enable
ok "Firewall: ports 22 + 11435 open"

# ── 8. Start AI docker-compose stack ─────────────────────────────────────────
if [[ -d "$REPO_DIR" ]]; then
    info "Starting AI gateway stack..."
    cd "$REPO_DIR"
    OLLAMA_ACCESS_TOKEN="$ACCESS_TOKEN" \
    OLLAMA_MEM_LIMIT="${TOTAL_RAM_GB}g" \
        docker compose -f docker-compose.ai.yml \
        --env-file .env.ai \
        up -d --build
    ok "AI gateway running on port 11435"
else
    warn "Repo not found at $REPO_DIR — start manually:"
    warn "  docker compose -f docker-compose.ai.yml up -d"
fi

# ── 9. Smoke test ─────────────────────────────────────────────────────────────
sleep 5
if curl -sf \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "http://localhost:11435/health" &>/dev/null; then
    ok "AI gateway smoke test passed"
else
    warn "AI gateway not responding yet — wait 30s and check: docker compose -f docker-compose.ai.yml logs"
fi

# ── 10. Print config for core server ─────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW} ADD THESE TO CORE SERVER .env${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "# AI Node (dedicated server — ${TOTAL_RAM_GB} GB RAM)"
echo "OLLAMA_BASE_URL=http://${SERVER_IP}:11435"
echo "OLLAMA_ACCESS_TOKEN=${ACCESS_TOKEN}"
echo "OLLAMA_CLINICAL_MODEL=${CLINICAL_MODEL}"
echo "OLLAMA_MODEL=llama3.2:1b"
echo "OLLAMA_MAX_CONCURRENT=2"
echo "OLLAMA_TIMEOUT=30"
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "After updating core server .env, restart backend:"
echo "  docker compose up -d --force-recreate gula-backend"
echo ""
echo "Verify connection from core server:"
echo "  curl http://localhost/api/ai/providers | python3 -m json.tool"
echo ""
