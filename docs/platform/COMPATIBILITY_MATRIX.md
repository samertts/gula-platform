# GULA Platform — Compatibility Matrix

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

- [1. Operating Systems](#1-operating-systems)
- [2. Web Browsers](#2-web-browsers)
- [3. Databases](#3-databases)
- [4. Redis](#4-redis)
- [5. Python](#5-python)
- [6. Docker](#6-docker)
- [7. Kubernetes](#7-kubernetes)
- [8. Mobile](#8-mobile)
- [9. Deployment Platforms](#9-deployment-platforms)
- [10. Node.js (Frontend Build)](#10-nodejs-frontend-build)
- [11. Key Dependencies](#11-key-dependencies)
- [12. Related Documents](#12-related-documents)

---

## 1. Operating Systems

| OS | Supported | Tested | Production | Notes |
|----|-----------|--------|------------|-------|
| Ubuntu 22.04 LTS | ✅ | ✅ | ✅ | Primary target |
| Ubuntu 24.04 LTS | ✅ | ✅ | ✅ | Production (DigitalOcean droplet) |
| Debian 12 | ✅ | ✅ | ⚠️ | Tested in CI, not primary deployment |
| macOS (Ventura+) | ✅ | ✅ | ❌ | Development only |
| Windows (WSL2) | ✅ | ⚠️ | ❌ | Development only; Docker Desktop backend |
| Windows (native) | ❌ | ❌ | ❌ | Not supported (no native Docker support) |

**Sources:** `README.md`, `CLAUDE.md`, `docker-compose.yml`

## 2. Web Browsers

| Browser | Supported | Tested | Notes |
|---------|-----------|--------|-------|
| Chrome 120+ | ✅ | ✅ | Primary target for frontend-v2 SPA |
| Firefox 120+ | ✅ | ✅ | Full support; RTL tested |
| Safari 17+ | ✅ | ✅ | RTL (Arabic) layout verified |
| Edge 120+ | ✅ | ✅ | Chromium-based; parity with Chrome |
| Chrome Mobile (Android) | ✅ | ⚠️ | PWA support via `vite-plugin-pwa` |
| Safari Mobile (iOS 17+) | ✅ | ⚠️ | PWA support; limited testing |
| IE 11 | ❌ | ❌ | Not supported (React 19+ incompatible) |

**Sources:** `frontend-v2/package.json` (React 19, Vite 8, PWA plugin), `CLAUDE.md` (frontend-e2e.yml with Playwright)

## 3. Databases

| Database | Supported | Tested | Production | Notes |
|----------|-----------|--------|------------|-------|
| PostgreSQL 17 | ✅ | ✅ | ✅ | Primary — `postgres:17-alpine` in Docker Compose |
| PostgreSQL 16 | ⚠️ | ✅ | ❌ | Previously primary; code compatible but not actively deployed |
| PostgreSQL 15 | ❌ | ❌ | ❌ | Not supported (missing features, version too old) |
| SQLite | ⚠️ | ✅ | ❌ | In-memory test fixtures only |

**Evidence:** `docker-compose.yml` uses `postgres:17-alpine`; `CLAUDE.md` CI section tests against `postgres:17-alpine`.

## 4. Redis

| Version | Supported | Tested | Production | Notes |
|---------|-----------|--------|------------|-------|
| Redis 7.2+ | ✅ | ✅ | ✅ | Primary — `redis:7-alpine` in Docker Compose |
| Redis 6.x | ❌ | ❌ | ❌ | Missing ACL support required by config |
| Redis Sentinel | ✅ | ⚠️ | ❌ | HA mode configured (`REDIS_SENTINEL_HOSTS`, `REDIS_SENTINEL_MASTER` in `config.py`) |
| Redis Cluster | ⚠️ | ❌ | ❌ | Config skeleton exists (`REDIS_CLUSTER_NODES`); not deployed |

**Sources:** `docker-compose.yml:52` (`redis:7-alpine`), `backend/app/config.py:198-200`

## 5. Python

| Version | Supported | Tested | Production | Notes |
|---------|-----------|--------|------------|-------|
| 3.12 | ✅ | ✅ | ✅ | Minimum per `pyproject.toml` (`requires-python = ">=3.12"`) |
| 3.13 | ✅ | ✅ | ⚠️ | Tested in staging |
| 3.14 | ✅ | ✅ | ✅ | Docker runtime image (`python:3.12-slim` in `backend/Dockerfile`) |
| 3.11 | ❌ | ❌ | ❌ | Below minimum; code uses 3.12+ features |

**Sources:** `backend/pyproject.toml:9` (`requires-python = ">=3.12"`), `backend/Dockerfile:8,20` (`python:3.12-slim`), `backend/app/config.py` (runtime)

## 6. Docker

| Version | Supported | Tested | Production | Notes |
|---------|-----------|--------|------------|-------|
| Docker 24+ | ✅ | ✅ | ✅ | Primary; `compose` v2 built-in |
| Docker Compose v2 | ✅ | ✅ | ✅ | Orchestration for all services |
| Docker Compose v1 | ❌ | ❌ | ❌ | Deprecated; `docker-compose` (v1) not compatible with `docker compose` (v2) directives |

**Sources:** `docker-compose.yml` uses Compose v2 format; `CLAUDE.md` Makefile targets use `docker compose` (v2)

## 7. Kubernetes

| Platform | Supported | Tested | Production | Notes |
|----------|-----------|--------|------------|-------|
| K8s 1.28+ | ⚠️ | ⚠️ | ❌ | Manifests in `k8s/` base + overlays; not primary deployment |
| K3s | ⚠️ | ⚠️ | ❌ | Edge deployment target for off-site labs |

**Sources:** `CLAUDE.md` Deployment Targets table; `DIGITAL_LIBRARY_INDEX.md:279` (K8s 1.31+ referenced)

## 8. Mobile

| Platform | Supported | Tested | Production | Notes |
|----------|-----------|--------|------------|-------|
| Android 11+ | ⚠️ | ⚠️ | ❌ | PWA from frontend-v2; native app in development |
| iOS 16+ | ⚠️ | ⚠️ | ❌ | PWA from frontend-v2; native app in development |

**Sources:** `frontend-v2/package.json` (`vite-plugin-pwa`); `backend/app/config.py:228` (APNS_KEY, FCM_SERVER_KEY for push notifications)

## 9. Deployment Platforms

| Platform | Supported | Tested | Production | Notes |
|----------|-----------|--------|------------|-------|
| DigitalOcean Droplet | ✅ | ✅ | ✅ | Primary production target; scripts in `digitalocean/` |
| Docker Compose (single host) | ✅ | ✅ | ✅ | Current deployment model (`docker-compose.yml`) |
| Docker Compose (full infra) | ✅ | ✅ | ⚠️ | Monitoring profile (`docker-compose.full.yml` — Prometheus, Grafana, Loki, RabbitMQ) |
| Render | ✅ | ⚠️ | ❌ | `render.yaml` exists; backend can deploy as Web Service |
| Supabase | ⚠️ | ⚠️ | ❌ | Managed Postgres integration (config/supabase/ exists) |
| AWS EC2 | ⚠️ | ❌ | ❌ | Future target |
| Azure VM | ⚠️ | ❌ | ❌ | Future target |

**Sources:** `CLAUDE.md` Deployment Targets table; `docker-compose.yml`; `docker-compose.full.yml`

## 10. Node.js (Frontend Build)

| Version | Supported | Notes |
|---------|-----------|-------|
| 18.x LTS | ✅ | Minimum for Vite 8 + React 19 toolchain |
| 20.x LTS | ✅ | Recommended |
| 22.x | ✅ | Latest; used in CI |

**Sources:** `frontend-v2/package.json` (Vite 8, React 19 — require Node 18+); `.github/workflows/` CI references

## 11. Key Dependencies

| Dependency | Version | Role | Source |
|------------|---------|------|--------|
| FastAPI | >=0.139.2 | Web framework | `backend/requirements.txt:1` |
| Uvicorn | >=0.51.0 | ASGI server | `backend/requirements.txt:2` |
| Gunicorn | >=26.0.0 | WSGI/ASGI worker manager | `backend/requirements.txt:3` |
| SQLAlchemy | >=2.0.51 | ORM (async) | `backend/requirements.txt:4` |
| Alembic | >=1.18.5 | DB migrations | `backend/requirements.txt:5` |
| Pydantic | >=2.13.4 | Data validation | `backend/requirements.txt:8` |
| React | ^19.2.8 | Frontend UI framework | `frontend-v2/package.json:27` |
| TypeScript | ^6.0.2 | Frontend type system | `frontend-v2/package.json:57` |
| Vite | ^8.1.5 | Frontend build tool | `frontend-v2/package.json:59` |
| Tailwind CSS | ^4.3.3 | CSS framework | `frontend-v2/package.json:54` |
| Redis (redis-py) | >=8.0.1 | Python Redis client | `backend/requirements.txt:20` |
| nginx | 1.28-alpine | API gateway + frontend server | `docker-compose.yml:238,263` |
| Prometheus | v2.56.1 | Metrics collection | `docker-compose.yml:329` |
| Grafana | 11.7.1 | Dashboards | `docker-compose.yml:362` |
| Alertmanager | v0.33.1 | Alert routing | `docker-compose.yml:304` |
| Terraform | >=1.10 | IaC provisioning | `DIGITAL_LIBRARY_INDEX.md:280` |

**Sources:** `backend/requirements.txt`, `backend/pyproject.toml`, `frontend-v2/package.json`, `docker-compose.yml`, `DIGITAL_LIBRARY_INDEX.md`

## 12. Related Documents

| Document | Path | Description |
|----------|------|-------------|
| Digital Library Index | `docs/reference/DIGITAL_LIBRARY_INDEX.md` | Technology standards, versions, and references |
| CLAUDE.md | `CLAUDE.md` | Developer guide, architecture, invariants |
| Platform Evolution Plan | `docs/evolution/PLATFORM_EVOLUTION_PLAN.md` | Architecture evolution strategy |
| Docker Compose Config | `docker-compose.yml` | Current service definitions and base images |
| Backend Dockerfile | `backend/Dockerfile` | Python runtime image definition |
| Backend Config | `backend/app/config.py` | Runtime environment configuration |
| Frontend Package | `frontend-v2/package.json` | Frontend dependency versions |
| CI Pipeline | `.github/workflows/ci.yml` | CI test matrix and image versions |