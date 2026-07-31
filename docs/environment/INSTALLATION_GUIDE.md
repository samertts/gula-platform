# GULA Platform — Installation Guide

## Prerequisites

- Ubuntu 22.04 LTS (WSL2 or native)
- sudo access
- Internet connection

## Step 1: System Packages

```bash
sudo apt-get update
sudo apt-get install -y software-properties-common curl wget git
```

## Step 2: Python 3.12

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
```

## Step 3: pipx & uv

```bash
python3.12 -m ensurepip --upgrade
python3.12 -m pip install --user pipx
pipx ensurepath
pipx install uv
```

## Step 4: Backend Virtual Environment

```bash
cd /path/to/gula-platform/backend
python3.12 -m venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install pytest ruff mypy
```

## Step 5: Node.js 24

```bash
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## Step 6: Docker & Compose

```bash
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Re-login for group changes
```

## Step 7: Git LFS

```bash
sudo apt-get install -y git-lfs
git lfs install
```

## Step 8: Pre-commit

```bash
pipx install pre-commit
cd /path/to/gula-platform
pre-commit install
```

## Step 9: Verify

```bash
# Run the bootstrap verification
bash scripts/verify_environment.sh
```

## Step 10: Environment Files

The following files are already in the repository:

- `.python-version` → `3.12`
- `.nvmrc` → `24`
- `.tool-versions` → node 24, python 3.12
- `.editorconfig` → existing

## Step 11: Docker Services

```bash
docker compose up -d
```

## Optional: Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
