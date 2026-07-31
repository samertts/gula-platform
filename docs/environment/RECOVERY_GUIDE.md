# GULA Platform — Recovery Guide

## Python Recovery

### Symptom: `python3.12: command not found`

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
```

### Symptom: `ModuleNotFoundError` in backend

```bash
source backend/.venv/bin/activate
uv pip install -r requirements.txt --quiet
```

### Symptom: `pip` points to wrong Python

```bash
python3.12 -m pip install --upgrade pip
# Always use: source backend/.venv/bin/activate first
```

### Symptom: Broken virtual environment

```bash
rm -rf backend/.venv
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
uv pip install -r requirements.txt
uv pip install pytest ruff mypy
```

## Node Recovery

### Symptom: `node: command not found`

```bash
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Symptom: Wrong node version

```bash
node --version  # should be v24.x
# If not: reinstall from NodeSource
```

### Symptom: npm global packages not found

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
# Add to ~/.bashrc: export PATH="$HOME/.npm-global/bin:$PATH"
```

## Docker Recovery

### Symptom: `docker: command not found`

```bash
sudo apt-get install -y docker.io docker-compose-v2
```

### Symptom: `docker compose: command not found`

```bash
# Install compose plugin
sudo apt-get install -y docker-compose-v2
# Or create symlink in user plugins dir:
mkdir -p ~/.docker/cli-plugins
ln -sf /usr/libexec/docker/cli-plugins/docker-compose ~/.docker/cli-plugins/docker-compose
```

### Symptom: Permission denied (docker socket)

```bash
sudo usermod -aG docker $USER
# Re-login or: newgrp docker
```

### Symptom: Container exit/crash

```bash
docker compose logs gula-backend   # Check backend logs
docker compose logs gula-postgres  # Check database logs
docker compose restart gula-backend
```

## Git Recovery

### Symptom: `git lfs: command not found`

```bash
sudo apt-get install -y git-lfs
git lfs install
```

### Symptom: Pre-commit hooks not running

```bash
pipx install pre-commit
pre-commit install
pre-commit run --all-files
```

## uv Recovery

### Symptom: `uv: command not found`

```bash
pipx install uv
# Or standalone: curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Symptom: uv cache corruption

```bash
uv cache clean
```
