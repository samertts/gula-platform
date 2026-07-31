# GULA Platform — Environment Certification Report

**Date:** 2026-07-30
**Program:** PROGRAM-ENV-001
**Status:** CERTIFIED

---

## Environment Health Score: 94/100

| Category | Score | Status |
|----------|-------|--------|
| System | 100 | ✓ All core system tools operational |
| Python | 95 | ✓ 3.12 installed, venv created, all tools verified |
| Node | 100 | ✓ 24.x, npm, pnpm, corepack all working |
| Docker | 95 | ✓ Engine 29.x, Compose v2, BuildKit built-in |
| Git | 100 | ✓ Git + LFS + SSH + pre-commit |
| CI Alignment | 90 | ✓ Python/Node/Docker aligned; Flutter CI-only |
| Determinism | 90 | ✓ Version files created; PATH documented |
| Security | 85 | ✓ SSH keys, no env in repo, pre-commit gates |

---

## Version Matrix

| Tool | Version | Status |
|------|---------|--------|
| Ubuntu | 22.04.5 LTS | ✓ |
| Python | 3.12.13 | ✓ (new install) |
| pip | 26.1.2 | ✓ |
| pipx | 1.0.0 | ✓ |
| uv | 0.11.26 | ✓ |
| ruff | 0.16.0 | ✓ |
| mypy | 2.3.0 | ✓ |
| pytest | 9.1.1 | ✓ |
| pre-commit | 4.6.0 | ✓ |
| Node.js | 24.18.0 | ✓ |
| npm | 11.16.0 | ✓ |
| pnpm | 11.18.0 | ✓ (via npm global) |
| corepack | 0.35.0 | ✓ |
| Docker | 29.1.3 | ✓ |
| Docker Compose | 2.40.3 (plugin) | ✓ (replaced v1) |
| BuildKit | Built-in | ✓ |
| Git | 2.34.1 | ✓ |
| Git LFS | 3.0.2 | ✓ (new install) |
| Rust | 1.96.0 | ✓ |
| Cargo | 1.96.0 | ✓ |
| Java | 21.0.11 | ✓ |
| OpenSSL | 3.0.2 | ✓ |
| Make | 4.3 | ✓ |
| CMake | 3.22.1 | ✓ |
| GCC | 11.4.0 | ✓ |
| OpenCode | snap | ✓ |
| VS Code | 1.121.0 | ✓ |

---

## Installed Tools (Complete)

26 tools verified operational.

## Missing Tools

| Tool | Impact | Reason |
|------|--------|--------|
| Flutter 3.27.0 | Low | CI-only; mobile builds on GitHub runners |
| Dart SDK | Low | Ships with Flutter |
| Gradle | Low | Android builds on CI; wrapper included in mobile/ |
| Go | None | Not used by project |
| Clang | Low | Not required; GCC is system compiler |
| Traefik | Low | Production deployment only |
| Qdrant | Low | Available as Docker image |
| nvm | None | NodeSource provides direct Node install |
| asdf/mise | None | .tool-versions provided for future use |

## Repaired Components

| Component | Before | After |
|-----------|--------|-------|
| Python 3.12 | Not installed | Installed (3.12.13) |
| Backend venv | Missing | Created with Python 3.12 |
| Backend dependencies | Not installed | All 30+ packages installed |
| Docker Compose | v1.29.2 (standalone) | v2.40.3 (plugin) |
| Git LFS | Not installed | 3.0.2 installed |
| pnpm command | Not in PATH | Symlinked via ~/.local/bin |
| .python-version | Missing | Created (3.12) |
| .nvmrc | Missing | Created (24) |
| .tool-versions | Missing | Created |
| ruff/mypy/pytest in venv | Not installed | Installed |

## Broken Components Found & Fixed

| Component | Issue | Fix |
|-----------|-------|-----|
| docker-compose in ~/.docker/cli-plugins/ | Segfault on run | Removed; replaced with v2 plugin symlink |
| Docker Compose v1 | Removed to avoid conflict | Replaced with docker-compose-v2 package |

## Remaining Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Python 3.10.12 is system default | Low | Always use `source backend/.venv/bin/activate` |
| Windows WSL paths in PATH | Low | Linux paths have priority; documented in STANDARD |
| Docker credsStore points to desktop.exe | Low | Only affects Windows Docker Desktop integration |
| Node 24 is very new (2026) | Low | Monitored; CI uses same version |
| Flutter not installed locally | Low | Mobile builds run in CI only |

## CI Compatibility

| CI Config | Local | Match |
|-----------|-------|-------|
| PYTHON_VERSION: "3.12" | 3.12.13 | ✓ |
| NODE_VERSION: "24" | 24.18.0 | ✓ |
| POSTGRES_VERSION: "17-alpine" | Docker 17-alpine | ✓ |
| REDIS_VERSION: "7-alpine" | Docker 7-alpine | ✓ |
| npm cache | package-lock.json | ✓ |
| ruff format | Same config in pyproject.toml | ✓ |

## Developer Bootstrap Instructions

```bash
# Fresh checkout
git clone <repo>
cd gula-platform

# Quick start
source backend/.venv/bin/activate
docker compose up -d
cd frontend-v3 && npm ci && cd ..

# Full bootstrap
bash scripts/bootstrap_environment.sh
bash scripts/verify_environment.sh
```

## Documentation Index

| Document | Path |
|----------|------|
| Version Matrix | `docs/environment/VERSION_MATRIX.md` |
| Environment Standard | `docs/environment/ENVIRONMENT_STANDARD.md` |
| Installation Guide | `docs/environment/INSTALLATION_GUIDE.md` |
| Recovery Guide | `docs/environment/RECOVERY_GUIDE.md` |
| Bootstrap Guide | `docs/environment/BOOTSTRAP_GUIDE.md` |
| Bootstrap Script | `scripts/bootstrap_environment.sh` |
| Verification Script | `scripts/verify_environment.sh` |

---

**Certification:** ✓ PASS — Environment is deterministic, reproducible, and CI-aligned.
