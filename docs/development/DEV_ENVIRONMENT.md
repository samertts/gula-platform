# Development Environment Guide

**Mission:** PROGRAM-ENV-001
**Created:** 2026-08-04
**Last Updated:** 2026-08-04
**Status:** Active

---

## Overview

This document describes the standardized development environment for the
GULA Platform. All contributors must use this environment to ensure
reproducible builds and consistent behavior.

**Target OS:** Ubuntu 22.04.5 LTS (WSL2 on Windows 11)
**Shell:** bash

---

## Installed Software

### Core Stack

| Tool | Version | Location | Manager |
|---|---|---|---|
| Python | 3.12.13 | `~/.local/bin/python3.12` | uv |
| Node.js | 24.18.0 | `~/.nvm/versions/node/v24.18.0/bin/` | NVM |
| npm | 11.16.0 | NVM-managed | NVM |
| Rust | 1.96.0 | `~/.cargo/bin/` | rustup |
| Docker | 29.1.3 | `/usr/bin/docker` | apt |

### Utilities

| Tool | Version | Location |
|---|---|---|
| Git | 2.34.1 | `/usr/bin/git` |
| uv | 0.11.26 | `~/.local/bin/uv` |
| OpenCode | 1.18.13 | `~/.opencode/bin/opencode` |
| Ollama | 0.24.0 | `/usr/local/bin/ollama` |
| ruff | 0.15.21 | `/snap/bin/ruff` |
| bat | 0.19.0 | `/usr/local/bin/bat` |
| fd | 8.3.1 | `/usr/local/bin/fd` |
| trivy | 0.72.0 | `/usr/local/bin/trivy` |
| kubectl | (latest) | `/usr/local/bin/kubectl` |
| gh | 2.86.0 | `/snap/bin/gh` |

### Node Package Managers

| Tool | Version | Location |
|---|---|---|
| pnpm | 11.18.0 | `~/.local/bin/pnpm` |
| bun | 1.3.14 | `~/.npm-global/bin/bun` |
| corepack | 0.35.0 | NVM-managed |

---

## Installation

### Fresh Ubuntu/WSL2 Setup

```bash
# 1. System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential

# 2. NVM (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 24
nvm use 24
nvm alias default 24

# 3. Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 4. Python via uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12

# 5. Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER
# Log out and back in for group change

# 6. Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text

# 7. OpenCode
curl -fsSL https://opencode.ai/install.sh | sh

# 8. Snap packages
sudo snap install ruff --classic
sudo snap install gh

# 9. Local tools
sudo apt install -y bat fd-find
sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
sudo ln -sf /usr/bin/fdfind /usr/local/bin/fd

# 10. kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 11. Trivy
sudo apt install -y trivy
```

### Project Setup

```bash
# Clone repository
git clone <repo-url> ~/workspace/projects/gula-platform
cd ~/workspace/projects/gula-platform

# Backend setup
cd backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

# Frontend setup
cd ../frontend-v3
npm install

# Verify
python3.12 --version   # Should show 3.12.13
node --version          # Should show v24.18.0
docker --version        # Should show 24.x or later
```

---

## Recovery

### Shell Config Recovery

Backups are stored at `~/.backups/YYYY-MM-DD/`.

```bash
# Restore .bashrc
cp ~/.backups/2026-08-04/.bashrc.bak ~/.bashrc
source ~/.bashrc

# Restore .profile
cp ~/.backups/2026-08-04/.profile.bak ~/.profile
source ~/.profile
```

### NVM Recovery

```bash
# Reinstall NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 24
nvm alias default 24
```

### Python Recovery

```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reinstall Python 3.12
uv python install 3.12

# Recreate project venv
cd backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Docker Recovery

```bash
# Reinstall Docker
sudo apt remove -y docker docker-engine docker.io containerd runc
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker
```

---

## Backup

### What to Back Up

| Item | Location | Frequency |
|---|---|---|
| `.bashrc` | `~/.bashrc` | Before every change |
| `.profile` | `~/.profile` | Before every change |
| NVM | `~/.nvm/` | Monthly |
| uv Python | `~/.local/share/uv/` | Monthly |
| Docker images | `docker save` | Before upgrades |
| Ollama models | `~/.ollama/` | Monthly |
| Git config | `~/.gitconfig` | Before changes |

### Backup Location

```
~/.backups/YYYY-MM-DD/
├── .bashrc.bak
├── .profile.bak
└── manifest.txt
```

---

## Upgrade Procedures

### Node.js Upgrade

```bash
nvm install 24        # Install latest v24
nvm use 24            # Switch to it
nvm alias default 24  # Set as default
nvm ls                # Verify
```

### Python Upgrade

```bash
uv python install 3.13   # Install new version
uv python list            # Verify
# Update pyproject.toml to target new version
```

### Docker Upgrade

```bash
sudo apt update
sudo apt upgrade docker.io
docker --version
```

### Rust Upgrade

```bash
rustup update
cargo --version
rustc --version
```

---

## Maintenance

### Weekly

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update NVM node
nvm install --latest-npm

# Update uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Prune Docker
docker system prune -f

# Update Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### Monthly

```bash
# Update snap packages
sudo snap refresh

# Update Rust
rustup update

# Full system cleanup
sudo apt autoremove -y
docker system prune -af
```

---

## Troubleshooting

### PATH Issues

```bash
# Check for duplicates
echo "$PATH" | tr ':' '\n' | sort | uniq -d

# Check entry count
echo "$PATH" | tr ':' '\n' | wc -l

# Clean PATH: see PLAYBOOK-000001
```

### Node/npm Issues

```bash
# Verify NVM is active
nvm current

# Reset npm
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Python Issues

```bash
# Verify Python version
python3.12 --version

# Recreate venv
rm -rf backend/.venv
cd backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Docker Issues

```bash
# Check Docker daemon
docker info

# Restart Docker
sudo systemctl restart docker

# Check WSL integration
docker context ls
```

---

## Health Check

Run the development environment health check:

```bash
bash scripts/dev_environment_doctor.sh
```

This validates all tools, PATH, permissions, and configurations.

---

## Related Documentation

- `.ai/core/memory/PROJECT_MEMORY.md` — Technology stack
- `.ai/core/skills/SKILL-000001_wsl2_path_deduplication.md` — PATH fix
- `.ai/core/playbooks/PLAYBOOK-000001_fix_duplicate_path_entries.md` — PATH playbook
- `ENVIRONMENT_AUDIT_REPORT.md` — Full environment audit
- `AGENTS.md` — AI agent guidance
- `CLAUDE.md` — AI operating manual
