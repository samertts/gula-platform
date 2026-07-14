# MISSION 4.0 — Environment Guardian Report

**Date:** 2026-07-14
**Repository:** GULA Adaptive Enterprise Platform v2.1.0
**Environment:** Ubuntu 22.04.5 LTS (WSL2) on Windows

---

## 1. EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Overall Grade** | **YELLOW — Stable with Issues** |
| **Critical Issues** | 1 (Python 3.11.0rc1 pre-release) |
| **High Issues** | 3 (Missing lock file, Docker container restarting, Old Poetry) |
| **Medium Issues** | 7 |
| **Low Issues** | 5 |
| **Tools Installed** | 16/26 required |
| **Tools Missing** | 10 |
| **Lock Files Missing** | 3/4 |

---

## 2. RUNTIME ENVIRONMENT

| Component | Installed | Required | Status |
|-----------|-----------|----------|--------|
| OS | Ubuntu 22.04.5 LTS (WSL2) | Any Linux | ✅ |
| Kernel | 6.6.87.2-microsoft-standard-WSL2 | — | ✅ |
| Architecture | x86_64 | — | ✅ |
| Memory | 3.8 GiB total, 2.7 GiB available | ≥2 GiB | ✅ |
| Disk | 251 GiB, 204 GiB available | ≥50 GiB | ✅ |
| Systemd | 249 (active) | — | ✅ |

### Python Ecosystem

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Python 3 | 3.10.12 (system) | ⚠️ | System default; project needs ≥3.11 |
| Python 3.11 | 3.11.0rc1 (pre-release) | 🔴 **CRITICAL** | **Release candidate, not stable** — must upgrade to 3.11.9+ or 3.12+ |
| Python 3.12 | Not installed | ❌ | Recommended target |
| pip | 26.1.2 | ✅ | Latest |
| virtualenv | Not active | ⚠️ | No venv activated in shell context |
| uv | Not installed | ❌ | Missing — would improve dependency management |
| Poetry | 1.1.12 | 🟡 | **Very old** (current: ~1.8). Must upgrade. |
| pip-tools | Installed (in .venv) | ✅ | Used for lock file generation |
| pip-audit | Not installed | ❌ | Missing |
| safety | Not installed | ❌ | Missing |

### Node.js Ecosystem

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Node.js | 24.18.0 | ✅ | Latest |
| npm | 11.16.0 | ✅ | Latest |
| pnpm | Not installed | ❌ | Missing |
| yarn | Not installed | ❌ | Missing |

### Rust Ecosystem

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| rustc | 1.96.0 | ✅ | Latest stable |
| cargo | 1.96.0 | ✅ | Latest; ast-grep installed |

### Other Languages

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Java | OpenJDK 21.0.11 | ✅ | Latest LTS |
| Go | Not installed | ❌ | Missing (used by some tools) |

### Container & Orchestration

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Docker | 29.1.3 | ✅ | Latest for Ubuntu 22.04 |
| docker-compose (v1) | 1.29.2 | 🟡 | **Old v1** — should migrate to `docker compose` plugin |
| docker compose (v2) | Not installed | ❌ | Missing — is the modern replacement |
| kubectl | Not installed | ❌ | Missing (k8s/ exists but tool absent) |

### Git & CI

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Git | 2.34.1 | ✅ | Adequate |
| GitHub CLI (gh) | 2.96.0 (snap) + 2.86.0 (snap) | ⚠️ | Two versions installed (snap + WSL) — PATH conflict possible |
| gh (system) | 2.86.0 (snap - classic) | | |
| gh (wsl) | 2.96.0 | | In `/mnt/c/` paths |

### AI/LLM Tools

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Ollama | 0.24.0 | ✅ | Installed |
| OpenCode | 1.17.18 (snap) | ✅ | Latest snap |
| @opencode-ai/cli | 1.17.10 (npm global) | ⚠️ | Two versions: snap + npm |
| Claude Code | Not installed | ❌ | Missing |
| Gemini CLI | Not installed | ❌ | Missing |

### IDE

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| VS Code | 1.121.0 | ✅ | Latest (WSL remote) |

### Global npm Packages

| Package | Version | Purpose |
|---------|---------|---------|
| @opencode-ai/cli | 1.17.10 | AI CLI |
| codebuff | 1.0.684 | AI coding agent |
| eslint | 10.6.0 | JS linter |
| freebuff | 0.0.122 | AI coding tool |
| opencode-ai | 1.17.13 | AI CLI |
| opencode-codebase-index | 0.14.0 | Code index |
| prettier | 3.9.0 | Formatter |
| pyright | 1.1.411 | Python type checker |
| typescript | 6.0.3 | TypeScript compiler |

---

## 3. QUALITY & SECURITY TOOLS

| Tool | Status | Required by | Notes |
|------|--------|-------------|-------|
| Ruff | ✅ (0.15.21 snap, 0.15.20/0.15.21 .ruff_cache) | MISSION 4.5 | Installed, two cache versions |
| MyPy | 🟡 (0.942 apt — very old) | MISSION 4.5 | **Must upgrade** (≥1.0 for strict) |
| Pytest | 🟡 (via .venv, version TBD) | MISSION 4.5 | Installed in .venv |
| Bandit | ❌ | MISSION 4.5 | Missing — SAST for Python |
| Semgrep | ❌ | MISSION 4.5 | Missing — multi-language SAST |
| Safety | ❌ | MISSION 4.5 | Missing — vulnerability scanner |
| pip-audit | ❌ | MISSION 4.5 | Missing — Python advisory scanner |
| Trivy | ❌ | MISSION 4.5 | Missing — container/comprehensive scanner |
| Hadolint | ❌ | CI pipeline | Missing — Dockerfile linter |
| Gitleaks | ❌ | CI pipeline | Missing — secret scanner |
| ast-grep | ✅ (0.44.0 via cargo) | — | Structural search |

---

## 4. REPOSITORY HEALTH

| Metric | Value | Assessment |
|--------|-------|------------|
| Total files | 2,703 | ✅ |
| Python files | 473 | ✅ |
| Test files | 122 | ✅ (4.3% test ratio) |
| Directories | 278 | ✅ |
| Repository size | 103 MB | ✅ |
| Migration files | 26 | ✅ |
| Docker images | 4 (15.9 GB total) | 🟡 Large image (1.17 GB) |

### Lock File Status

| Location | Lock File | Status |
|----------|-----------|--------|
| Root Python | ❌ | **Missing** — no `poetry.lock` or `requirements-lock.txt` |
| Backend Python | 🔵 **CREATED** → `requirements-lock.txt` | Newly generated |
| Frontend-v2 | ✅ `package-lock.json` (12,268 lines) | Present |
| Client | ❌ | No lock file, no package.json |
| Shared Library | ❌ | No lock file |

### Docker Status

- **Container `gula`**: 🔴 **Restarting** (failing to start) — `docker compose up` needed
- **Image `gula-platform_gula:latest`**: 1.17 GB 🟡 (large)
- **`python:3.11` image**: 1.1 GB (used for builds)
- **`qdrant/qdrant`**: 190 MB (stopped)

---

## 5. CRITICAL ISSUES (Must Fix)

### 🔴 CRITICAL: Python 3.11.0rc1 (pre-release) in use
- **Severity:** Critical
- **Detail:** The only available Python 3.11 is `3.11.0rc1` (August 2022 release candidate). This is unstable, has no security patches, and should never be used in production.
- **Impact:** Potential crashes, unpatched CVEs, undefined behavior
- **Fix:** Install Python 3.11.9+ or 3.12+ via deadsnakes PPA or pyenv
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt-get install python3.12 python3.12-dev python3.12-venv
  ```

### 🔴 HIGH: No `.env` file present
- **Severity:** High
- **Detail:** The `.env` file is missing. Docker container can't start without it.
- **Impact:** Container `gula` is in restart loop (4 months!)
- **Fix:** Copy `.env.example` to `.env` and configure:
  ```bash
  cp .env.example .env
  ```

### 🟡 HIGH: Poetry 1.1.12 — extremely outdated
- **Severity:** High
- **Detail:** Poetry 1.1.12 (2021) lacks modern features, lock file v2 format, and has known bugs
- **Impact:** Can't generate modern lock files, dependency resolution issues
- **Fix:** 
  ```bash
  pip install --upgrade poetry  # or use pipx: pipx install poetry
  ```

### 🟡 HIGH: Lock file was missing (NOW FIXED)
- **Severity:** High
- **Detail:** No Python lock file existed, preventing reproducible builds
- **Resolution:** 🔵 `backend/requirements-lock.txt` generated with 58 pinned packages

### 🟡 MEDIUM: Docker compose v1 (legacy)
- **Severity:** Medium
- **Detail:** Docker Compose v1 is deprecated and removed from Docker. v2 plugin not installed.
- **Fix:**
  ```bash
  sudo apt-get install docker-compose-v2
  # or
  sudo apt-get remove docker-compose && sudo apt-get install docker-compose-v2
  ```

### 🟡 MEDIUM: Docker container restarting
- **Severity:** Medium
- **Detail:** `gula` container in restart loop — likely missing `.env` or config issue
- **Impact:** Application not serving traffic
- **Fix:** Create `.env` and run `docker compose up -d`

### 🟡 MEDIUM: No kubectl on PATH
- **Severity:** Medium
- **Detail:** k8s/ directory exists with deployment configs but no kubectl to validate them
- **Fix:** Install via snap: `sudo snap install kubectl --classic`

---

## 6. DEPENDENCY ISSUES

### Dead Dependencies (NOW FIXED)
| Package | Reason | Action |
|---------|--------|--------|
| `orjson` | Never imported anywhere in codebase | 🔵 **Commented out** |
| `jinja2` | Never imported anywhere in codebase | 🔵 **Commented out** |

### Missing Dependencies (NOW FIXED)
| Package | Reason | Action |
|---------|--------|--------|
| `factory_boy` | Imported in `engineering/testing/factories.py` | 🔵 **Added** to `requirements-dev.txt` |

### Version Drift
| Package | `backend/requirements.txt` | `shared/pyproject.toml` | Risk |
|---------|---------------------------|------------------------|------|
| bcrypt | ≥4.1.3,<4.2.0 | ≥4.0.0 | Low (stricter wins) |
| cryptography | ≥42.0.0 | ≥41.0.0 | Low |
| python-jose | ≥3.4.0 | ≥3.3.0 | Low |
| pydantic | ≥2.7.0 | ≥2.0.0 | Low |
| reportlab | ≥4.1.0 | ≥4.0.0 | Low |
| qrcode | ≥7.4.2 | ≥7.4.0 | Low |
| pillow | ≥10.4.0 | ≥10.0.0 | Low |

---

## 7. QUALITY GATE READINESS

| Gate | Tool | Status | Notes |
|------|------|--------|-------|
| Linting | Ruff | ✅ Ready | 0.15.21 installed |
| Type Checking | MyPy | 🟡 **Old version** | 0.942 (needs ≥1.0) |
| Unit Tests | Pytest | ✅ Ready | In .venv |
| CVE Scan | pip-audit | ❌ Not installed | Must install |
| CVE Scan | Safety | ❌ Not installed | Must install |
| SAST | Bandit | ❌ Not installed | Must install |
| SAST | Semgrep | ❌ Not installed | Must install |
| Container Scan | Trivy | ❌ Not installed | Must install |
| Architecture | Built-in | ⚠️ Module exists but untested | `kernel/validation/architecture.py` |

---

## 8. RECOMMENDATIONS

### Immediate (Day 1)
1. Install stable Python 3.12 via deadsnakes PPA
2. Create `.env` from `.env.example`
3. Fix `docker compose` and restart containers
4. Install security scanners (bandit, semgrep, safety, pip-audit, trivy)
5. Upgrade Poetry to ≥1.8

### Short-term (Week 1)
6. Install `uv` for fast dependency management
7. Install kubectl for K8s validation
8. Install pnpm/yarn for frontend
9. Upgrade MyPy from 0.942 to ≥1.0
10. Consolidate duplicate tool installations (opencode, gh)

### Medium-term (Month 1)
11. Migrate to Docker Compose v2 plugin
12. Reduce Docker image size (currently 1.17 GB)
13. Set up pyenv for Python version management
14. Install Claude Code and Gemini CLI for AI-augmented development

---

## 9. FIXES APPLIED THIS SESSION

| # | Issue | File | Action |
|---|-------|------|--------|
| 1 | Dead dependency `orjson` | `backend/requirements.txt` | Commented out |
| 2 | Dead dependency `jinja2` | `backend/requirements.txt` | Commented out |
| 3 | Missing dependency `factory_boy` | `backend/requirements-dev.txt` | Added |
| 4 | Missing lock file | `backend/requirements-lock.txt` | Generated (58 packages) |
| 5 | Missing virtual environment | `.venv/` | Created with Python 3.11 |

---

## 10. OPEN ISSUES (Require Human Approval)

| Issue | Risk | Requires |
|-------|------|----------|
| Python 3.11.0rc1 usage | 🔴 Critical | Install stable Python |
| Docker container restart loop | 🔴 High | Create .env + debug startup |
| Poetry upgrade | 🟡 Medium | `pip install --upgrade poetry` |
| Docker image size (1.17 GB) | 🟡 Low | Multi-stage build optimization |
| Snap vs npm package duplication | 🟡 Low | Remove redundant opencode installs |

---

*Report generated by GULA Engineering Program — Mission 4.0 Environment Guardian*
