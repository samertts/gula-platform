#!/usr/bin/env bash
# GULA Platform — Environment Verification Script
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local cmd="$2"
    local expected="$3"
    local output
    output=$(timeout 10 bash -c "$cmd" 2>/dev/null || true)
    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $name (expected: '$expected', got: '$output')"
        FAIL=$((FAIL + 1))
    fi
}

warn_check() {
    local name="$1"
    local cmd="$2"
    local expected="$3"
    local output
    output=$(timeout 10 bash -c "$cmd" 2>/dev/null || true)
    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${YELLOW}⚠${NC} $name (expected: '$expected', got: '$output')"
        WARN=$((WARN + 1))
    fi
}

echo "========================================"
echo "  GULA ENVIRONMENT VERIFICATION"
echo "========================================"
echo ""

# System
check "Ubuntu 22.04" "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME" "22.04"

# Python
check "Python 3.12" "python3.12 --version 2>&1" "3.12"
check "Backend venv" "backend/.venv/bin/python --version 2>&1" "3.12"
check "pip available" "backend/.venv/bin/pip --version 2>&1" "pip"
check "uv installed" "uv --version 2>&1" "uv"
check "ruff in venv" "backend/.venv/bin/ruff --version 2>&1" "ruff"
check "mypy in venv" "backend/.venv/bin/mypy --version 2>&1" "mypy"
check "pytest in venv" "backend/.venv/bin/pytest --version 2>&1" "9."

# Node
check "Node.js 24" "node --version 2>&1" "v24"
check "npm" "npm --version 2>&1" "11."
warn_check "pnpm" "pnpm --version 2>&1" "11."

# Git
check "Git" "git --version 2>&1" "2."
warn_check "Git LFS" "git lfs version 2>&1" "git-lfs"

# Docker
check "Docker" "docker --version 2>&1" "29."
check "Docker daemon" "docker info --format '{{.ServerVersion}}' 2>/dev/null" "29."
check "Compose plugin" "docker compose version 2>&1" "2."

# Environment files
check ".python-version" "cat .python-version 2>/dev/null" "3.12"
check ".nvmrc" "cat .nvmrc 2>/dev/null" "24"
check ".tool-versions" "cat .tool-versions 2>/dev/null" "python 3.12"

# Docker services
warn_check "PostgreSQL running" "docker ps --format '{{.Names}}' 2>/dev/null | grep postgres" "postgres"
warn_check "Redis running" "docker ps --format '{{.Names}}' 2>/dev/null | grep redis" "redis"

echo ""
echo "========================================"
echo "  RESULTS"
echo "========================================"
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo -e "${YELLOW}Warnings:${NC} $WARN"

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}Some checks failed.${NC}"
    exit 1
else
    echo -e "${GREEN}All critical checks passed.${NC}"
    exit 0
fi
