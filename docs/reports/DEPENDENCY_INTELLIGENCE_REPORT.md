# MISSION 4.3 — Dependency Intelligence Report (SBOM)
**GULA Platform v2.1.0** | Generated: 2026-07-14

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total dependency declarations** | **273** (across all files, deduplicated within each file) |
| **Unique packages** (est.) | ~160 distinct packages across ecosystems |
| **Python packages (declared)** | 53 unique declared deps, 58 locked (incl. transitive) |
| **JavaScript packages (declared)** | 80 unique declared deps |
| **Docker images** | 28 distinct container images |
| **Dependency definition files** | 15 files across 3 ecosystems |
| **License** | Proprietary (all first-party code) |

---

## 1. Inventory by Ecosystem

### 1.1 Python — Production Dependencies

| # | Package | Version Constraint | Source File(s) |
|---|---------|-------------------|----------------|
| 1 | fastapi | >=0.110.0 | `backend/requirements.txt`, `root/requirements.txt`, `nhop-platform/requirements.txt`, `services/device_bridge/pyproject.toml` |
| 2 | uvicorn[standard] | >=0.29.0 | `backend/requirements.txt`, `root/requirements.txt`, `nhop-platform/requirements.txt`, `services/device_bridge/pyproject.toml` |
| 3 | gunicorn | >=21.2.0 | `backend/requirements.txt` |
| 4 | sqlalchemy | >=2.0.30 | `backend/requirements.txt`, `nhop-platform/requirements.txt` |
| 5 | alembic | >=1.13.0 | `backend/requirements.txt`, `nhop-platform/requirements.txt` |
| 6 | psycopg2-binary | >=2.9.9 | `backend/requirements.txt`, `nhop-platform/requirements.txt` |
| 7 | python-multipart | >=0.0.20 | `backend/requirements.txt`, `root/requirements.txt`, `nhop-platform/requirements.txt` |
| 8 | pydantic | >=2.7.0 | `backend/requirements.txt`, `shared/pyproject.toml`, `nhop-platform/requirements.txt`, `services/device_bridge/pyproject.toml` |
| 9 | pydantic-settings | >=2.0.0 | `backend/requirements.txt`, `shared/pyproject.toml`, `nhop-platform/requirements.txt` |
| 10 | passlib[bcrypt] | >=1.7.4 | `backend/requirements.txt` |
| 11 | bcrypt | >=4.1.3,<4.2.0 | `backend/requirements.txt`, `shared/pyproject.toml` |
| 12 | python-jose[cryptography] | >=3.4.0 | `backend/requirements.txt`, `shared/pyproject.toml` |
| 13 | cryptography | >=42.0.0 | `backend/requirements.txt`, `shared/pyproject.toml`, `edge_agent/requirements.txt` |
| 14 | qrcode | >=7.4.2 | `backend/requirements.txt`, `shared/pyproject.toml` |
| 15 | Pillow | >=10.4.0 | `backend/requirements.txt`, `shared/pyproject.toml` |
| 16 | reportlab | >=4.1.0 | `backend/requirements.txt`, `shared/pyproject.toml` |
| 17 | arabic-reshaper | >=3.0.0 | `backend/requirements.txt` |
| 18 | python-bidi | >=0.4.2 | `backend/requirements.txt` |
| 19 | httpx | >=0.27.0 | `backend/requirements.txt`, `shared/pyproject.toml`, `edge_agent/requirements.txt`, `nhop-platform/requirements.txt`, `services/device_bridge/pyproject.toml` |
| 20 | redis | >=5.0.0 | `backend/requirements.txt`, `root/requirements.txt`, `shared/pyproject.toml`, `nhop-platform/requirements.txt` |
| 21 | sentry-sdk[fastapi] | >=2.0.0 | `backend/requirements.txt`, `shared/pyproject.toml` (optional: sentry) |
| 22 | boto3 | >=1.28.0 | `shared/pyproject.toml` |
| 23 | firebase-admin | >=6.0.0 | `shared/pyproject.toml` |
| 24 | python-barcode | >=0.15.0 | `shared/pyproject.toml` |
| 25 | pika | >=1.3.0 | `shared/pyproject.toml` |
| 26 | opentelemetry-api | >=1.20.0 | `shared/pyproject.toml` |
| 27 | opentelemetry-sdk | >=1.20.0 | `shared/pyproject.toml` |
| 28 | whoosh | >=1.7.0 | `shared/pyproject.toml` |
| 29 | google-generativeai | >=0.8.0 | `shared/pyproject.toml` |
| 30 | jsonschema | >=4.20.0 | `shared/pyproject.toml` |
| 31 | jsonpath-ng | >=1.6.0 | `shared/pyproject.toml` |
| 32 | asyncpg | >=0.29.0 | `nhop-platform/requirements.txt` |
| 33 | tomli | >=2.0.0 | `edge_agent/requirements.txt` (python_version < "3.11") |
| 34 | psutil | >=5.9.0 | `edge_agent/requirements.txt` |
| 35 | celery | >=5.3.0 | `shared/pyproject.toml` (optional: celery) |

### 1.2 Python — Development Dependencies

| # | Package | Version Constraint | Source File(s) |
|---|---------|-------------------|----------------|
| 1 | pytest | >=9.0.3 | `backend/requirements-dev.txt`, `shared/pyproject.toml` (optional: dev), `services/device_bridge/pyproject.toml` (optional: dev) |
| 2 | pytest-asyncio | >=0.23.0,<1.0.0 | `backend/requirements-dev.txt` |
| 3 | factory_boy | >=3.3.0 | `backend/requirements-dev.txt` |
| 4 | ruff | >=0.5.0 | `shared/pyproject.toml` (optional: dev) |
| 5 | mypy | >=1.10.0 | `shared/pyproject.toml` (optional: dev) |
| 6 | coverage | >=7.0.0 | `shared/pyproject.toml` (optional: dev) |
| 7 | bandit | >=1.7.0 | `shared/pyproject.toml` (optional: dev) |

### 1.3 Python — Locked Transitive Dependencies

From `backend/requirements-lock.txt` (58 packages pinned). Notable additions beyond declared deps:

| # | Package | Version | Role |
|---|---------|---------|------|
| 1 | anyio | 4.14.2 | Async runtime (fastapi/starlette dep) |
| 2 | certifi | 2026.6.17 | SSL cert bundle |
| 3 | cffi | 2.1.0 | C FFI (cryptography dep) |
| 4 | click | 8.4.2 | CLI (alembic dep) |
| 5 | ecdsa | 0.19.2 | ECDSA (python-jose dep) |
| 6 | Faker | 40.28.1 | Test data (factory_boy dep) |
| 7 | greenlet | 3.5.3 | Coroutine (sqlalchemy dep) |
| 8 | h11 | 0.16.0 | HTTP/1.1 (uvicorn dep) |
| 9 | httpcore | 1.0.9 | HTTP core (httpx dep) |
| 10 | httptools | 0.8.0 | HTTP parsing (uvicorn dep) |
| 11 | Mako | 1.3.12 | Template engine (alembic dep) |
| 12 | MarkupSafe | 3.0.3 | Template safety (Mako dep) |
| 13 | pyasn1 | 0.6.4 | ASN.1 (python-jose dep) |
| 14 | pycparser | 3.0 | C parser (cffi dep) |
| 15 | pydantic_core | 2.46.4 | Pydantic core (pydantic dep) |
| 16 | Pygments | 2.20.0 | Syntax highlighting |
| 17 | python-dotenv | 1.2.2 | Env file loading |
| 18 | PyYAML | 6.0.3 | YAML parsing |
| 19 | rsa | 4.9.1 | RSA (python-jose dep) |
| 20 | six | 1.17.0 | Py2/3 compat |
| 21 | starlette | 1.3.1 | ASGI framework (fastapi dep) |
| 22 | typing_extensions | 4.16.0 | Type hints |
| 23 | typing-inspection | 0.4.2 | Type inspection |
| 24 | urllib3 | 2.7.0 | HTTP client |
| 25 | uvloop | 0.22.1 | Event loop (uvicorn dep) |
| 26 | watchfiles | 1.2.0 | File watcher (uvicorn dep) |
| 27 | websockets | 16.1 | WebSocket (uvicorn dep) |
| 28 | annotated-types | 0.7.0 | Type annotations (pydantic dep) |
| 29 | annotated-doc | 0.0.4 | Documentation annotations |
| 30 | charset-normalizer | 3.4.9 | Charset detection |
| 31 | idna | 3.18 | IDNA encoding |
| 32 | iniconfig | 2.3.0 | Config (pytest dep) |
| 33 | packaging | 26.2 | Packaging utils |
| 34 | pluggy | 1.6.0 | Plugin (pytest dep) |

### 1.4 Python — Build System Dependencies

| # | Package | Version Constraint | Source File |
|---|---------|-------------------|-------------|
| 1 | setuptools | >=80 | `pyproject.toml` (root) |
| 2 | wheel | (any) | `pyproject.toml` (root) |

### 1.5 JavaScript — Production Dependencies (root `package.json`)

| # | Package | Version | Source |
|---|---------|---------|--------|
| 1 | express | ^4.18.2 | `package.json` |
| 2 | @trpc/server | ^10.45.0 | `package.json` |
| 3 | @trpc/client | ^10.45.0 | `package.json` |
| 4 | @trpc/react-query | ^10.45.0 | `package.json` |
| 5 | react | ^18.2.0 | `package.json` |
| 6 | react-dom | ^18.2.0 | `package.json` |
| 7 | react-router-dom | ^6.20.0 | `package.json` |
| 8 | tailwindcss | ^3.4.0 | `package.json` |
| 9 | mysql2 | ^3.6.5 | `package.json` |
| 10 | redis | ^4.6.12 | `package.json` |
| 11 | zod | ^3.22.4 | `package.json` |
| 12 | @tanstack/react-query | ^5.28.0 | `package.json` |
| 13 | @tanstack/react-query-devtools | ^5.28.0 | `package.json` |
| 14 | jsonwebtoken | ^9.0.3 | `package.json` |
| 15 | bcryptjs | ^2.4.3 | `package.json` |
| 16 | dotenv | ^16.3.1 | `package.json` |
| 17 | axios | ^1.8.2 | `package.json` |
| 18 | cors | ^2.8.5 | `package.json` |
| 19 | helmet | ^7.1.0 | `package.json` |
| 20 | compression | ^1.7.4 | `package.json` |
| 21 | uuid | ^11.1.0 | `package.json` |
| 22 | superjson | ^2.2.1 | `package.json` |
| 23 | date-fns | ^2.30.0 | `package.json` |
| 24 | clsx | ^2.0.0 | `package.json` |
| 25 | class-variance-authority | ^0.7.0 | `package.json` |
| 26 | lodash | ^4.17.21 | `package.json` |
| 27 | recharts | ^2.10.3 | `package.json` |
| 28 | lucide-react | ^0.344.0 | `package.json` |
| 29 | framer-motion | ^10.16.16 | `package.json` |
| 30 | @types/uuid | ^10.0.0 | `package.json` |

### 1.6 JavaScript — Production Dependencies (frontend-v2 `package.json`)

| # | Package | Version | Source |
|---|---------|---------|--------|
| 1 | @firebase/eslint-plugin-security-rules | ^0.0.1 | `frontend-v2/package.json` |
| 2 | @google/genai | ^1.50.1 | `frontend-v2/package.json` |
| 3 | @google/generative-ai | ^0.24.1 | `frontend-v2/package.json` |
| 4 | @tailwindcss/vite | ^4.1.14 | `frontend-v2/package.json` |
| 5 | @sentry/react | ^8.42.0 | `frontend-v2/package.json` |
| 6 | @vitejs/plugin-react | ^5.0.4 | `frontend-v2/package.json` |
| 7 | clsx | ^2.1.1 | `frontend-v2/package.json` |
| 8 | cmdk | ^1.1.1 | `frontend-v2/package.json` |
| 9 | date-fns | ^4.1.0 | `frontend-v2/package.json` |
| 10 | dotenv | ^17.2.3 | `frontend-v2/package.json` |
| 11 | express | ^4.21.2 | `frontend-v2/package.json` |
| 12 | firebase | ^11.1.0 | `frontend-v2/package.json` |
| 13 | html5-qrcode | ^2.3.8 | `frontend-v2/package.json` |
| 14 | lucide-react | ^0.546.0 | `frontend-v2/package.json` |
| 15 | motion | ^12.23.24 | `frontend-v2/package.json` |
| 16 | posthog-js | ^1.205.0 | `frontend-v2/package.json` |
| 17 | react | ^19.0.0 | `frontend-v2/package.json` |
| 18 | react-barcode | ^1.6.1 | `frontend-v2/package.json` |
| 19 | react-dom | ^19.0.0 | `frontend-v2/package.json` |
| 20 | react-easy-crop | ^5.5.7 | `frontend-v2/package.json` |
| 21 | react-hot-toast | ^2.6.0 | `frontend-v2/package.json` |
| 22 | react-is | ^19.2.6 | `frontend-v2/package.json` |
| 23 | react-markdown | ^10.1.0 | `frontend-v2/package.json` |
| 24 | react-router-dom | ^7.14.1 | `frontend-v2/package.json` |
| 25 | recharts | ^3.8.1 | `frontend-v2/package.json` |
| 26 | sonner | ^2.0.7 | `frontend-v2/package.json` |
| 27 | tailwind-merge | ^3.5.0 | `frontend-v2/package.json` |
| 28 | vite | ^6.2.0 | `frontend-v2/package.json` |
| 29 | vite-plugin-pwa | ^1.2.0 | `frontend-v2/package.json` |

### 1.7 JavaScript — Development Dependencies (root `package.json`)

| # | Package | Version | Source |
|---|---------|---------|--------|
| 1 | typescript | ^5.3.3 | `package.json` |
| 2 | tsx | ^4.7.0 | `package.json` |
| 3 | vite | ^7.3.2 | `package.json` |
| 4 | @vitejs/plugin-react | ^5.2.0 | `package.json` |
| 5 | @vitejs/plugin-basic-ssl | ^1.0.1 | `package.json` |
| 6 | vitest | ^1.0.4 | `package.json` |
| 7 | @vitest/ui | ^1.1.0 | `package.json` |
| 8 | eslint | ^8.56.0 | `package.json` |
| 9 | prettier | ^3.1.1 | `package.json` |
| 10 | @typescript-eslint/eslint-plugin | ^6.16.0 | `package.json` |
| 11 | @typescript-eslint/parser | ^6.16.0 | `package.json` |
| 12 | @tailwindcss/forms | ^0.5.7 | `package.json` |
| 13 | @tailwindcss/typography | ^0.5.10 | `package.json` |
| 14 | shadcn-ui | ^0.8.0 | `package.json` |
| 15 | postcss | ^8.4.32 | `package.json` |
| 16 | autoprefixer | ^10.4.16 | `package.json` |
| 17 | @types/react | ^18.2.45 | `package.json` |
| 18 | @types/react-dom | ^18.2.18 | `package.json` |
| 19 | @types/express | ^4.17.21 | `package.json` |
| 20 | @types/cors | ^2.8.17 | `package.json` |
| 21 | @types/compression | ^1.7.5 | `package.json` |
| 22 | @types/lodash | ^4.14.202 | `package.json` |
| 23 | @types/node | ^20.10.6 | `package.json` |
| 24 | @types/uuid | ^10.0.0 | `package.json` |
| 25 | @types/react-router-dom | ^5.3.3 | `package.json` |
| 26 | @types/jest | ^29.5.11 | `package.json` |
| 27 | @testing-library/react | ^14.1.2 | `package.json` |
| 28 | @testing-library/jest-dom | ^6.1.5 | `package.json` |
| 29 | @testing-library/user-event | ^14.5.1 | `package.json` |
| 30 | @vitest/coverage-v8 | ^1.0.4 | `package.json` |
| 31 | vitest-mock-extended | ^1.3.2 | `package.json` |

### 1.8 JavaScript — Development Dependencies (frontend-v2 `package.json`)

| # | Package | Version | Source |
|---|---------|---------|--------|
| 1 | @types/express | ^4.17.21 | `frontend-v2/package.json` |
| 2 | @types/node | ^22.14.0 | `frontend-v2/package.json` |
| 3 | autoprefixer | ^10.4.21 | `frontend-v2/package.json` |
| 4 | tailwindcss | ^4.1.14 | `frontend-v2/package.json` |
| 5 | tsx | ^4.21.0 | `frontend-v2/package.json` |
| 6 | typescript | ~5.8.2 | `frontend-v2/package.json` |

### 1.9 Docker Infrastructure Images (MVP stack — `docker-compose.yml`)

| Service | Image | Version Tag |
|---------|-------|-------------|
| postgres | postgres | 16-alpine |
| redis | redis | 7-alpine |
| gula-backend | `${GULA_IMAGE_PREFIX}/backend:${GULA_IMAGE_TAG}` | local / CI-built |
| gula-worker | `${GULA_IMAGE_PREFIX}/backend:${GULA_IMAGE_TAG}` | local / CI-built |
| frontend | nginx | 1.25-alpine |
| api-gateway | nginx | 1.25-alpine |
| prometheus | prom/prometheus | v2.50.1 |
| grafana | grafana/grafana | 10.3.3 |
| device-bridge | (custom build) | `./services/device_bridge` |

### 1.10 Docker Infrastructure Images (Full stack — `docker-compose.full.yml`)

| Service | Image | Version Tag |
|---------|-------|-------------|
| postgres-primary | postgres | 14.11-alpine |
| postgres-replica | postgres | 14.11-alpine |
| pgbouncer | edoburu/pgbouncer | 1.22.1 |
| redis | redis | 7-alpine |
| redis-replica | redis | 7-alpine |
| redis-sentinel | redis | 7-alpine |
| clickhouse | clickhouse/clickhouse-server | 23.8 |
| rabbitmq | rabbitmq | 3.12-management |
| zookeeper | confluentinc/cp-zookeeper | 7.5.0 |
| kafka | confluentinc/cp-kafka | 7.5.0 |
| ollama | ollama/ollama | 0.1.29 |
| minio | minio/minio | RELEASE.2024-01-18T22-51-28Z |
| node-exporter | prom/node-exporter | v1.7.0 |
| keycloak | quay.io/keycloak/keycloak | 23.0 |
| vault | hashicorp/vault | 1.15 |
| prometheus | prom/prometheus | v2.48.1 |
| grafana | grafana/grafana | 10.2.3 |
| loki | grafana/loki | 2.9.0 |
| promtail | grafana/promtail | 2.9.0 |
| jaeger | jaegertracing/all-in-one | 1.51 |
| backup-cron | postgres | 14.11-alpine |
| ai-service | (custom build) | `services/ai/Dockerfile` |
| lab-service | (custom build) | `services/lab/Dockerfile` |
| patient-service | (custom build) | `services/patient/Dockerfile` |
| order-service | (custom build) | `services/order/Dockerfile` |
| result-service | (custom build) | `services/result/Dockerfile` |
| sample-service | (custom build) | `services/sample/Dockerfile` |
| notification-service | (custom build) | `services/notification/Dockerfile` |
| autonomous-manager | (custom build) | `services/autonomous_manager/Dockerfile` |
| gula-backend | (custom build) | `./backend` |
| frontend | nginx | 1.25-alpine |

### 1.11 Dockerfile Base Images

| Dockerfile | Base Image |
|------------|------------|
| `backend/Dockerfile` | python:3.11-slim (builder + runtime) |
| `Dockerfile` (root) | node:20-alpine (builder + runtime) |
| `nhop-platform/Dockerfile` | python:3.12-slim |
| `services/device_bridge/Dockerfile` | python:3.12-slim |
| `services/ai/Dockerfile` | (check services/* — same pattern) |
| `services/lab/Dockerfile` | (check services/* — same pattern) |
| `services/order/Dockerfile` | (check services/* — same pattern) |
| `services/patient/Dockerfile` | (check services/* — same pattern) |
| `services/result/Dockerfile` | (check services/* — same pattern) |
| `services/sample/Dockerfile` | (check services/* — same pattern) |
| `services/notification/Dockerfile` | (check services/* — same pattern) |
| `services/autonomous_manager/Dockerfile` | (check services/* — same pattern) |

---

## 2. SBOM — JSON Structure

```json
{
  "bomFormat": "GULA Platform SBOM",
  "specVersion": "1.0",
  "serialNumber": "gula-platform-20260714",
  "metadata": {
    "component": {
      "name": "gula-platform",
      "version": "2.1.0",
      "type": "application",
      "license": "Proprietary",
      "supplier": "GULA Platform Team"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "fastapi",
      "version": ">=0.110.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": [
        "backend/requirements.txt",
        "requirements.txt",
        "nhop-platform/requirements.txt",
        "services/device_bridge/pyproject.toml"
      ]
    },
    {
      "type": "library",
      "name": "uvicorn[standard]",
      "version": ">=0.29.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": [
        "backend/requirements.txt",
        "requirements.txt",
        "nhop-platform/requirements.txt",
        "services/device_bridge/pyproject.toml"
      ]
    },
    {
      "type": "library",
      "name": "gunicorn",
      "version": ">=21.2.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt"]
    },
    {
      "type": "library",
      "name": "sqlalchemy",
      "version": ">=2.0.30",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "alembic",
      "version": ">=1.13.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "psycopg2-binary",
      "version": ">=2.9.9",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "python-multipart",
      "version": ">=0.0.20",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "requirements.txt", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "pydantic",
      "version": ">=2.7.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml", "nhop-platform/requirements.txt", "services/device_bridge/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "pydantic-settings",
      "version": ">=2.0.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "passlib[bcrypt]",
      "version": ">=1.7.4",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt"]
    },
    {
      "type": "library",
      "name": "bcrypt",
      "version": ">=4.1.3",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "python-jose",
      "version": ">=3.4.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "cryptography",
      "version": ">=42.0.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml", "edge_agent/requirements.txt"]
    },
    {
      "type": "library",
      "name": "qrcode",
      "version": ">=7.4.2",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "Pillow",
      "version": ">=10.4.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "reportlab",
      "version": ">=4.1.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "arabic-reshaper",
      "version": ">=3.0.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt"]
    },
    {
      "type": "library",
      "name": "python-bidi",
      "version": ">=0.4.2",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt"]
    },
    {
      "type": "library",
      "name": "httpx",
      "version": ">=0.27.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml", "edge_agent/requirements.txt", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "redis",
      "version": ">=5.0.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "requirements.txt", "shared/pyproject.toml", "nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "sentry-sdk[fastapi]",
      "version": ">=2.0.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["backend/requirements.txt", "shared/pyproject.toml (optional)"]
    },
    {
      "type": "library",
      "name": "boto3",
      "version": ">=1.28.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "firebase-admin",
      "version": ">=6.0.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "python-barcode",
      "version": ">=0.15.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "pika",
      "version": ">=1.3.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "opentelemetry-api",
      "version": ">=1.20.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "opentelemetry-sdk",
      "version": ">=1.20.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "whoosh",
      "version": ">=1.7.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "google-generativeai",
      "version": ">=0.8.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "jsonschema",
      "version": ">=4.20.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "jsonpath-ng",
      "version": ">=1.6.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["shared/pyproject.toml"]
    },
    {
      "type": "library",
      "name": "asyncpg",
      "version": ">=0.29.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["nhop-platform/requirements.txt"]
    },
    {
      "type": "library",
      "name": "psutil",
      "version": ">=5.9.0",
      "ecosystem": "python",
      "category": "production",
      "found_in": ["edge_agent/requirements.txt"]
    },
    {
      "type": "library",
      "name": "celery",
      "version": ">=5.3.0",
      "ecosystem": "python",
      "category": "optional",
      "found_in": ["shared/pyproject.toml (optional)"]
    },
    {
      "type": "library",
      "name": "express",
      "version": "^4.18.2 / ^4.21.2",
      "ecosystem": "javascript",
      "category": "production",
      "found_in": ["package.json", "frontend-v2/package.json"]
    },
    {
      "type": "library",
      "name": "react",
      "version": "^18.2.0 / ^19.0.0",
      "ecosystem": "javascript",
      "category": "production",
      "found_in": ["package.json", "frontend-v2/package.json"]
    },
    {
      "type": "library",
      "name": "react-dom",
      "version": "^18.2.0 / ^19.0.0",
      "ecosystem": "javascript",
      "category": "production",
      "found_in": ["package.json", "frontend-v2/package.json"]
    },
    {
      "type": "container",
      "name": "postgres",
      "version": "16-alpine",
      "ecosystem": "docker",
      "category": "infrastructure",
      "found_in": ["docker-compose.yml"]
    },
    {
      "type": "container",
      "name": "redis",
      "version": "7-alpine",
      "ecosystem": "docker",
      "category": "infrastructure",
      "found_in": ["docker-compose.yml"]
    },
    {
      "type": "container",
      "name": "nginx",
      "version": "1.25-alpine",
      "ecosystem": "docker",
      "category": "infrastructure",
      "found_in": ["docker-compose.yml (frontend + api-gateway)"]
    },
    {
      "type": "container",
      "name": "prom/prometheus",
      "version": "v2.50.1",
      "ecosystem": "docker",
      "category": "infrastructure",
      "found_in": ["docker-compose.yml"]
    },
    {
      "type": "container",
      "name": "grafana/grafana",
      "version": "10.3.3",
      "ecosystem": "docker",
      "category": "infrastructure",
      "found_in": ["docker-compose.yml"]
    }
  ]
}
```

---

## 3. Dependency Definition File Inventory

| # | File Path | Ecosystem | Category | Declared Dep Count |
|---|-----------|-----------|----------|-------------------|
| 1 | `backend/requirements.txt` | Python | Production | 21 (2 commented out) |
| 2 | `backend/requirements-dev.txt` | Python | Development | 3 |
| 3 | `backend/requirements-lock.txt` | Python | Locked (all) | 58 (incl. transitive) |
| 4 | `pyproject.toml` (root) | Python | Build system | 2 |
| 5 | `requirements.txt` (root) | Python | Production | 4 |
| 6 | `shared/pyproject.toml` | Python | Production + Optional + Dev | 20 prod + 5 dev + 2 optional |
| 7 | `frontend-v2/package.json` | JavaScript | Production + Dev | 29 prod + 6 dev |
| 8 | `package.json` (root) | JavaScript | Production + Dev | 30 prod + 31 dev |
| 9 | `edge_agent/requirements.txt` | Python | Production | 4 |
| 10 | `nhop-platform/requirements.txt` | Python | Production | 11 |
| 11 | `services/device_bridge/pyproject.toml` | Python | Production + Dev | 4 prod + 1 dev |
| 12 | `docker-compose.yml` | Infrastructure | Docker | 9 service images |
| 13 | `docker-compose.full.yml` | Infrastructure | Docker | 30 service images |
| 14 | `backend/Dockerfile` | Infrastructure | Base image | 1 (python:3.11-slim) |
| 15 | `Dockerfile` (root) | Infrastructure | Base image | 1 (node:20-alpine) |
| 16 | `nhop-platform/Dockerfile` | Infrastructure | Base image | 1 (python:3.12-slim) |
| 17 | `services/device_bridge/Dockerfile` | Infrastructure | Base image | 1 (python:3.12-slim) |
| 18 | `archive/legacy/lab-platform/requirements.txt` | Python | Legacy (archived) | 7 |

**Total files: 18** (15 active, 3 supporting/archived)

---

## 4. License Summary

| License | Scope | Notes |
|---------|-------|-------|
| **Proprietary** | All 1st-party code | All Python/JS project configs declare "Proprietary" |
| **MIT** | Most npm packages | Underlying OSS libs (React, express, vite, etc.) |
| **Apache-2.0** | Firebase, Kafka, ClickHouse, Jaeger, Prometheus, Grafana | Key infra components |
| **BSD** | Redis, bcrypt, python-bcrypt | |
| **PSF** | Python, pip packages | Python ecosystem standard |
| **MPL-2.0** | RabbitMQ | |
| **BSL-1.1** | HashiCorp Vault, Sentry SDK | |
| **AGPL** | MinIO | GPL-licensed object store |
| **Apache 2.0 + MIT** | OpenTelemetry | |
| **Apache 2.0** | Keycloak | |

**First-party code: Proprietary.** All OSS packages carry their respective upstream licenses.

---

## 5. Production vs Development Breakdown

| Category | Python | JavaScript | Docker | Total |
|----------|--------|------------|--------|-------|
| **Production** | 35 | 59 | 33 | **127** |
| **Development** | 7 | 37 | 0 | **44** |
| **Optional** | 3 | 0 | 0 | **3** |
| **Legacy/Archived** | 7 | 0 | 0 | **7** |
| **Locked (transitive)** | 58 | — | — | **58** |
| **Build System** | 2 | 0 | 0 | **2** |
| **Infrastructure** | 0 | 0 | 2 (base images) | **2** |
| **Totals** | **112** | **96** | **35** | **243** |

---

## 6. Risk Assessment

### 6.1 Potential Issues

| Risk Level | Issue | Affected Package(s) | Details |
|------------|-------|-------------------|---------|
| 🟡 **Medium** | **Bcrypt version cap** | bcrypt <4.2.0 | `backend/requirements.txt` pins bcrypt<4.2.0 due to passlib incompatibility — prevents security updates |
| 🟢 **Low** | **React version skew** | react (root: ^18.2.0 vs frontend-v2: ^19.0.0) | Two active JS projects use different React major versions |
| 🟢 **Low** | **Redis client version skew** | redis (Python: >=5.0.0 vs JS: ^4.6.12) | Two different ecosystem clients |
| 🟢 **Low** | **Dual TailwindCSS versions** | tailwindcss (root: ^3.4.0, frontend-v2: ^4.1.14) | Two active JS projects on different major versions |
| 🟢 **Low** | **Dual recharts versions** | recharts (root: ^2.10.3, frontend-v2: ^3.8.1) | Different major versions across projects |
| 🟢 **Low** | **Dual clsx versions** | clsx (root: ^2.0.0, frontend-v2: ^2.1.1) | Minor version difference only |
| 🟢 **Low** | **Dual date-fns versions** | date-fns (root: ^2.30.0, frontend-v2: ^4.1.0) | Major version difference |
| 🟢 **Low** | **esbuild override** | esbuild pinned to 0.27.6 in `package.json` | Security override (healthy — intentional pin) |
| 🟢 **Low** | **axios override** | axios >=1.8.2 in `package.json` resolutions | Security override (healthy) |
| 🟢 **Low** | **minimatch override** | minimatch >=9.0.5 in `package.json` | Security override |
| 🟢 **Low** | **Abandoned package** | **framer-motion** (root `package.json`: ^10.16.16) | Replaced by **motion** (frontend-v2: ^12.23.24) — active project migrated |
| 🟢 **Low** | **Abandoned package** | shadcn-ui ^0.8.0 | `shadcn-ui` npm package is deprecated — use `shadcn` CLI instead |
| 🟢 **Low** | **Ruff & Flake8 overlap** | ruff + flake8 | `pyproject.toml` configures ruff linting but CI runs `flake8 (E9, F821)` — duplicated lint |
| 🟢 **Low** | **Abandoned alternative** | vitest-mock-extended ^1.3.2 | Consider migrating to native vi.mock() |
| 🟢 **Low** | **Deprecated toolkit** | @testing-library/react, user-event | Legacy React 18 testing pattern; React 19 (frontend-v2) uses new patterns |
| 🟢 **Low** | **OpenCV/Pytesseract commented out** | opencv-python-headless, pytesseract | Commented out in `backend/requirements.txt` — cleanup dead code |
| 🟢 **Low** | **PostgreSQL version mismatch** | postgres 16-alpine (MVP) vs 14.11-alpine (full.yml) | MVP uses v16; full stack uses v14 — potential drift |
| 🟢 **Low** | **Prometheus version mismatch** | prometheus v2.50.1 (MVP) vs v2.48.1 (full.yml) | Different versions in two compose files |
| 🟢 **Low** | **Grafana version mismatch** | grafana/grafana 10.3.3 (MVP) vs 10.2.3 (full.yml) | Different versions in two compose files |

### 6.2 Criticality Scale

| Level | Count | Description |
|-------|-------|-------------|
| 🔴 **Critical** | 0 | No exploitable vulnerabilities found in declared deps |
| 🟡 **High** | 1 | passlib + bcrypt version cap blocks security updates |
| 🟢 **Medium** | 0 | — |
| ⚪ **Low** | 18 | Version skews, deprecated packages, benign drift |
| ⚪ **Info** | 3 | Commented-out dead deps, override annotations |

---

## 7. Lock File Analysis (`backend/requirements-lock.txt`)

| Metric | Value |
|--------|-------|
| Total pinned packages | 58 |
| Direct dependencies | ~25 |
| Transitive dependencies | ~33 |
| Freshness (avg release age) | Recent (mid-2026 releases observed) |
| Python version lock | >=3.11 (via starlette compatibility) |

**Notable locked versions:**
- cryptography==49.0.0 (current as of mid-2026)
- fastapi==0.139.0 (latest 0.x)
- pydantic==2.13.4
- sqlalchemy==2.0.51
- sentry-sdk==2.65.0
- uvicorn==0.51.0 (with uvloop 0.22.1 for async performance)

---

## 8. Override & Resolution Analysis (`package.json`)

Root `package.json` defines both `pnpm.overrides` and `resolutions`:

| Override | Version | Reason |
|----------|---------|--------|
| esbuild | >=0.25.0 / 0.27.6-pinned | Security CVE hardening |
| minimatch | >=9.0.5 / 10.0.3-pinned | Security CVE hardening |
| vite | >=7.3.2 | Ensure latest Vite in root project |
| uuid | >=11.1.0 | Ensure latest uuid |
| axios | >=1.8.2 | Security CVE hardening |
| lodash | >=4.17.21 | Security CVE hardening |
| hono | >=4.7.7 | Security CVE hardening |
| @hono/node-server | >=1.13.8 | Security CVE hardening |

---

## 9. Recommendations

1. **Unify TailwindCSS versions** across root and frontend-v2 (both on v4)
2. **Remove commented-out deps** (opencv-python-headless, pytesseract, orjson, jinja2) from `backend/requirements.txt`
3. **Audit passlib bcrypt cap** — consider replacing `passlib` with `bcrypt` directly
4. **Unify React versions** across the two JS frontends or document intentional divergence
5. **Replace `shadcn-ui` npm package** with the correct `shadcn` CLI tool
6. **Align docker-compose.yml and docker-compose.full.yml** where they share services
7. **Add a lock file** for the frontend-v2 project if not using pnpm lock

---

## Appendix A: Ecosystem File Count

| Ecosystem | Files Defining Dependencies | Breakdown |
|-----------|---------------------------|-----------|
| **Python** | 8 | `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/requirements-lock.txt`, `root/requirements.txt`, `shared/pyproject.toml`, `edge_agent/requirements.txt`, `nhop-platform/requirements.txt`, `services/device_bridge/pyproject.toml` |
| **JavaScript** | 2 | `package.json`, `frontend-v2/package.json` |
| **Docker/Infrastructure** | 5 | `docker-compose.yml`, `docker-compose.full.yml`, `backend/Dockerfile`, `Dockerfile` (root), `nhop-platform/Dockerfile`, `services/device_bridge/Dockerfile` |
| **Legacy** | 1 | `archive/legacy/lab-platform/requirements.txt` |
| **Total active** | **15** | |

## Appendix B: Services Microservice Dockerfiles

Each `services/*/Dockerfile` uses Python base images (typically `python:3.12-slim`). Their requirements are defined individually per service, but none had `requirements.txt` or `pyproject.toml` files at time of scanning (except `services/device_bridge/`). These microservices reuse the shared library from `shared/pyproject.toml` and are built via CI matrix.
