#!/usr/bin/env bash
# ===========================================================
# dev_environment_doctor.sh — Development Environment Health Check
# Mission: PROGRAM-ENV-001 Phase 6
# Created: 2026-08-04
# Usage: bash scripts/dev_environment_doctor.sh
# ===========================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
WARN=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo -e "  ${GREEN}PASS${NC}  $1"; }
warn() { WARN=$((WARN + 1)); echo -e "  ${YELLOW}WARN${NC}  $1"; }
fail() { FAIL=$((FAIL + 1)); echo -e "  ${RED}FAIL${NC}  $1"; }
section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# ===========================================================
section "PATH"
# ===========================================================

PATH_COUNT=$(echo "$PATH" | tr ':' '\n' | wc -l)
PATH_DUPES=$(echo "$PATH" | tr ':' '\n' | sort | uniq -d)

if [ "$PATH_COUNT" -le 20 ]; then
    pass "PATH has $PATH_COUNT entries (target: ≤20)"
else
    warn "PATH has $PATH_COUNT entries (target: ≤20)"
fi

if [ -z "$PATH_DUPES" ]; then
    pass "No duplicate PATH entries"
else
    dupes=$(echo "$PATH_DUPES" | tr '\n' ', ' | sed 's/,$//')
    fail "Duplicate PATH entries: $dupes"
fi

# ===========================================================
section "Shell Configuration"
# ===========================================================

if [ -f "$HOME/.bashrc" ]; then
    pass ".bashrc exists"
    if grep -q 'export PATH=.*\.local/bin.*\.opencode/bin.*\.npm-global/bin' "$HOME/.bashrc" 2>/dev/null; then
        pass ".bashrc has clean PATH entries"
    else
        warn ".bashrc PATH may need cleanup"
    fi
else
    fail ".bashrc not found"
fi

if [ -f "$HOME/.profile" ]; then
    pass ".profile exists"
else
    warn ".profile not found"
fi

if [ ! -f "$HOME/.bash_profile" ]; then
    pass "No duplicate .bash_profile"
else
    warn ".bash_profile exists — may cause double-sourcing"
fi

# ===========================================================
section "Node.js (NVM)"
# ===========================================================

if [ -d "$HOME/.nvm" ]; then
    pass "NVM directory exists"
else
    fail "NVM not installed"
fi

if command -v node &>/dev/null; then
    NODE_VER=$(node --version 2>/dev/null)
    NODE_PATH=$(which node 2>/dev/null)
    if echo "$NODE_PATH" | grep -q "\.nvm"; then
        pass "Node.js $NODE_VER via NVM"
    else
        warn "Node.js $NODE_VER NOT via NVM (at $NODE_PATH)"
    fi
else
    fail "Node.js not found"
fi

if command -v npm &>/dev/null; then
    NPM_VER=$(npm --version 2>/dev/null)
    NPM_PREFIX=$(npm config get prefix 2>/dev/null)
    if echo "$NPM_PREFIX" | grep -q "\.nvm"; then
        pass "npm $NPM_VER via NVM (prefix: $NPM_PREFIX)"
    else
        warn "npm prefix not NVM-managed: $NPM_PREFIX"
    fi
else
    fail "npm not found"
fi

if command -v npx &>/dev/null; then
    pass "npx available"
else
    warn "npx not found"
fi

if command -v corepack &>/dev/null; then
    COREPACK_VER=$(corepack --version 2>/dev/null)
    pass "corepack $COREPACK_VER"
else
    warn "corepack not found"
fi

if command -v pnpm &>/dev/null; then
    PNPM_VER=$(pnpm --version 2>/dev/null)
    pass "pnpm $PNPM_VER"
else
    warn "pnpm not found"
fi

# ===========================================================
section "Python"
# ===========================================================

if command -v python3.12 &>/dev/null; then
    PY12_VER=$(python3.12 --version 2>/dev/null)
    pass "Python 3.12 available: $PY12_VER"
else
    fail "Python 3.12 not found"
fi

if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>/dev/null)
    if echo "$PY_VER" | grep -q "3.12"; then
        pass "python3 points to 3.12"
    else
        warn "python3 points to $(echo $PY_VER | awk '{print $2}') (project needs 3.12)"
    fi
fi

if command -v uv &>/dev/null; then
    UV_VER=$(uv --version 2>/dev/null | awk '{print $1}')
    pass "uv $UV_VER"
else
    fail "uv not found"
fi

# ===========================================================
section "Docker"
# ===========================================================

if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version 2>/dev/null | awk '{print $3}' | tr -d ',')
    pass "Docker $DOCKER_VER"

    if docker info &>/dev/null; then
        pass "Docker daemon running"
    else
        warn "Docker daemon not accessible (may need sudo or group add)"
    fi
else
    fail "Docker not found"
fi

if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    COMPOSE_VER=$(docker compose version --short 2>/dev/null)
    pass "Docker Compose v2: $COMPOSE_VER"
else
    warn "Docker Compose v2 not available"
fi

# ===========================================================
section "Rust/Cargo"
# ===========================================================

if command -v cargo &>/dev/null; then
    CARGO_VER=$(cargo --version 2>/dev/null | awk '{print $2}')
    pass "Cargo $CARGO_VER"
else
    warn "Cargo not found"
fi

if command -v rustc &>/dev/null; then
    RUSTC_VER=$(rustc --version 2>/dev/null | awk '{print $2}')
    pass "Rustc $RUSTC_VER"
else
    warn "Rustc not found"
fi

# ===========================================================
section "Git"
# ===========================================================

if command -v git &>/dev/null; then
    GIT_VER=$(git --version 2>/dev/null | awk '{print $3}')
    pass "Git $GIT_VER"
else
    fail "Git not found"
fi

if [ -d "$HOME/.gitconfig" ] || [ -f "$HOME/.gitconfig" ]; then
    pass "Git config exists"
else
    warn "No ~/.gitconfig found"
fi

# ===========================================================
section "AI Tools"
# ===========================================================

if command -v opencode &>/dev/null; then
    OC_VER=$(opencode --version 2>/dev/null)
    pass "OpenCode $OC_VER"
else
    warn "OpenCode not found"
fi

if command -v ollama &>/dev/null; then
    OLLAMA_VER=$(ollama --version 2>/dev/null | awk '{print $NF}')
    pass "Ollama $OLLAMA_VER"
    if ollama list &>/dev/null 2>&1; then
        MODEL_COUNT=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
        pass "Ollama models loaded: $MODEL_COUNT"
    else
        warn "Ollama server not running"
    fi
else
    warn "Ollama not found"
fi

# ===========================================================
section "System Tools"
# ===========================================================

for TOOL in bat fd ruff trivy kubectl gh; do
    if command -v "$TOOL" &>/dev/null; then
        pass "$TOOL available"
    else
        warn "$TOOL not found"
    fi
done

# ===========================================================
section "Permissions"
# ===========================================================

if [ -w "$HOME/.bashrc" ]; then
    pass ".bashrc is writable"
else
    warn ".bashrc is not writable"
fi

if [ -w "$HOME/.profile" ]; then
    pass ".profile is writable"
else
    warn ".profile is not writable"
fi

if [ -d "$HOME/.local/bin" ] && [ -w "$HOME/.local/bin" ]; then
    pass "~/.local/bin is writable"
else
    warn "~/.local/bin missing or not writable"
fi

# ===========================================================
section "Network"
# ===========================================================

if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
    pass "Internet connectivity OK"
else
    warn "No internet connectivity"
fi

if curl -s --max-time 5 https://github.com &>/dev/null; then
    pass "GitHub accessible"
else
    warn "GitHub not accessible"
fi

# ===========================================================
section "Summary"
# ===========================================================

TOTAL=$((PASS + WARN + FAIL))
echo ""
echo -e "  ${GREEN}PASS: $PASS${NC}  ${YELLOW}WARN: $WARN${NC}  ${RED}FAIL: $FAIL${NC}  Total: $TOTAL"
echo ""

if [ "$FAIL" -eq 0 ] && [ "$WARN" -le 3 ]; then
    echo -e "  ${GREEN}ENVIRONMENT HEALTHY${NC}"
    exit 0
elif [ "$FAIL" -eq 0 ]; then
    echo -e "  ${YELLOW}ENVIRONMENT USABLE — $WARN warnings${NC}"
    exit 0
else
    echo -e "  ${RED}ENVIRONMENT NEEDS ATTENTION — $FAIL failures${NC}"
    exit 1
fi
