# GULA Platform — Development Environment Standard

## 1. Purpose

Establish a single deterministic development environment that is reproducible on any developer workstation, CI runner (GitHub Actions), and Docker build container.

## 2. Python Standard

| Property | Value |
|----------|-------|
| Version | 3.12.x |
| Install method | deadsnakes PPA (`python3.12`, `python3.12-venv`, `python3.12-dev`) |
| Virtual environment | `backend/.venv` (Python 3.12) |
| Package manager | `uv` (primary), `pip` (fallback) |
| Linter | `ruff` (0.16.x) |
| Type checker | `mypy` (2.3.x) |
| Test framework | `pytest` (9.x) |

### Activation

```bash
source backend/.venv/bin/activate
```

### Dependencies

- Runtime: `backend/requirements.txt`
- Dev: `backend/pyproject.toml [dev]` extras

## 3. Node.js Standard

| Property | Value |
|----------|-------|
| Version | 24.x |
| Install method | NodeSource (`node_24.x`) |
| Package manager | `npm` (primary, 11.x) |
| Secondary PM | `pnpm` (11.x) via npm global |
| Corepack | 0.35.x |

### Lock Files

- `package-lock.json` (root)
- `frontend-v3/package-lock.json`

## 4. Docker Standard

| Property | Value |
|----------|-------|
| Docker Engine | 29.x |
| Docker Compose | v2 (plugin, 2.x) |
| BuildKit | Built-in (Docker >=23) |

### Services

| Service | Image | Port |
|---------|-------|------|
| PostgreSQL | postgres:17-alpine | 5432 |
| Redis | redis:7-alpine | 6379 |
| Backend | gula-backend:latest | 10000 |
| Qdrant | qdrant/qdrant:latest | 6333 |

### Commands

```bash
# Start all services
docker compose up -d

# Start with full infrastructure
docker compose -f docker-compose.full.yml up -d

# Rebuild backend
docker compose up -d --build gula-backend
```

## 5. Git Standard

| Property | Value |
|----------|-------|
| Git | 2.34.x |
| Git LFS | 3.0.x |
| Pre-commit | 4.6.x |
| Commit style | Conventional Commits |

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## 6. Environment Files

| File | Purpose |
|------|---------|
| `.python-version` | Python version (pyenv/mise) |
| `.nvmrc` | Node version (nvm) |
| `.tool-versions` | Unified version (asdf/mise) |
| `.editorconfig` | Editor settings |

## 7. PATH Order

Priority (highest to lowest):

1. `~/.local/bin` (pipx, uv, user tools)
2. `~/.npm-global/bin` (npm global packages)
3. `~/.cargo/bin` (Rust/Cargo)
4. `~/.opencode/bin` (OpenCode)
5. `/usr/local/bin`
6. `/usr/bin`
7. `/bin`
8. `/snap/bin`
9. WSL interop paths (Windows, lowest priority)
