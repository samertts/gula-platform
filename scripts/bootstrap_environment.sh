#!/usr/bin/env bash
# GULA Platform — Automated Environment Bootstrap
# Run: bash scripts/bootstrap_environment.sh
set -euo pipefail

echo "=== GULA Platform Environment Bootstrap ==="

# 1. Install Python 3.12
if ! command -v python3.12 &>/dev/null; then
    echo "Installing Python 3.12..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3.12 python3.12-venv python3.12-dev
fi

# 2. Ensure pipx and uv
if ! command -v pipx &>/dev/null; then
    python3.12 -m ensurepip --upgrade
    python3.12 -m pip install --user pipx
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv &>/dev/null; then
    pipx install uv
fi

# 3. Create backend virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "Creating backend virtual environment..."
    python3.12 -m venv backend/.venv
fi
source backend/.venv/bin/activate

# 4. Install Python dependencies
echo "Installing Python dependencies..."
uv pip install -r backend/requirements.txt --quiet
uv pip install pytest ruff mypy --quiet

# 5. Install Git LFS
if ! git lfs version &>/dev/null; then
    echo "Installing Git LFS..."
    sudo apt-get install -y -qq git-lfs
    git lfs install
fi

# 6. Install pre-commit hooks
pipx install pre-commit 2>/dev/null || true
pre-commit install 2>/dev/null || echo "pre-commit hooks skipped (git not initialized)"

# 7. Check Docker compose plugin
if ! docker compose version &>/dev/null; then
    echo "Installing Docker Compose plugin..."
    sudo apt-get install -y -qq docker-compose-v2
    mkdir -p ~/.docker/cli-plugins
    ln -sf /usr/libexec/docker/cli-plugins/docker-compose ~/.docker/cli-plugins/docker-compose
fi

echo ""
echo "=== Bootstrap Complete ==="
echo "Run 'bash scripts/verify_environment.sh' to verify."
