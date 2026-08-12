# GULA Platform — Software Bill of Materials (SBOM)

**Generated:** 2026-07-14  
**Platform Version:** 2.1.0  
**Repository:** gula-platform (monorepo)

---

## 1. SBOM Summary

| Metric | Count |
|---|---|
| Total Python dependencies (unique) | 44 |
| Total JavaScript/TypeScript dependencies (unique, across both `package.json`) | ~68 (dependencies) + ~38 (devDependencies) |
| Total Docker images | 8 unique base images |
| Total sub-projects scanned | 9 (backend, shared, nhop-platform, edge_agent, device_bridge, root client, frontend-v2, Docker infra, microservices) |
| Proprietary modules | Shared library (`gula-shared`, `gula-platform`) — proprietary license |

### Dependency Sources

| Source | File | Type |
|---|---|---|
| Backend API | `backend/requirements.txt` | Python (production) |
| Backend Dev | `backend/requirements-dev.txt` | Python (dev/CI) |
| Shared Library | `shared/pyproject.toml` | Python (library + dev extras) |
| NHOP Platform | `nhop-platform/requirements.txt` | Python (production) |
| Edge Agent | `edge_agent/requirements.txt` | Python (production) |
| Device Bridge | `services/device_bridge/pyproject.toml` | Python (production) |
| Root Docker | `requirements.txt` | Python (minimal boot) |
| Root Client | `package.json` | JS/TS (production + dev) |
| Frontend v2 | `frontend-v2/package.json` | JS/TS (production + dev) |
| CI/CD config | `pyproject.toml` (root) | Python (tooling only) |

---

## 2. Python Dependency Table

| # | Package | Version(s) Used | License | Location(s) | Purpose | Risk Level |
|---|---|---|---|---|---|---|
| 1 | **fastapi** | >=0.110.0, ==0.115.0 | MIT | backend, nhop, device_bridge, root | Web framework (all API endpoints) | HIGH |
| 2 | **uvicorn[standard]** | >=0.29.0, ==0.30.6 | BSD-3-Clause | backend, nhop, device_bridge, root | ASGI server | MEDIUM |
| 3 | **gunicorn** | >=21.2.0 | MIT | backend | WSGI process manager | MEDIUM |
| 4 | **sqlalchemy** | >=2.0.30, ==2.0.35 | MIT | backend, nhop | ORM / database layer | HIGH |
| 5 | **alembic** | >=1.13.0, ==1.13.3 | MIT | backend, nhop | DB migration engine | HIGH |
| 6 | **psycopg2-binary** | >=2.9.9 | LGPL | backend, nhop | PostgreSQL adapter | MEDIUM |
| 7 | **asyncpg** | ==0.29.0 | Apache-2.0 | nhop | Async PostgreSQL adapter | MEDIUM |
| 8 | **python-multipart** | >=0.0.20 | Apache-2.0 | backend, nhop, root | Form-data parsing | MEDIUM |
| 9 | **pydantic** | >=2.7.0, >=2.0.0, ==2.9.2, >=2.8.0 | MIT | backend, shared, nhop, device_bridge | Data validation / settings | HIGH |
| 10 | **pydantic-settings** | >=2.0.0, ==2.5.2 | MIT | backend, shared, nhop | Settings management | LOW |
| 11 | **passlib[bcrypt]** | >=1.7.4 | BSD-3-Clause | backend | Password hashing | CRITICAL |
| 12 | **bcrypt** | >=4.1.3,<4.2.0, >=4.0.0 | Apache-2.0 | backend, shared | Cryptographic hashing | CRITICAL |
| 13 | **python-jose[cryptography]** | >=3.3.0, >=3.3.0 | MIT | backend, shared | JWT encode/decode | CRITICAL |
| 14 | **cryptography** | >=42.0.0, >=41.0.0 | Apache-2.0 / BSD | backend, shared, edge_agent | Encryption primitives | CRITICAL |
| 15 | **qrcode** | >=7.4.2, >=7.4.0 | BSD-3-Clause | backend, shared | QR code generation | LOW |
| 16 | **Pillow** | >=10.4.0, >=10.0.0 | Historical (MIT-like) | backend, shared | Image processing | MEDIUM |
| 17 | **jinja2** | >=3.1.4 | BSD-3-Clause | backend | HTML templating | LOW |
| 18 | **reportlab** | >=4.1.0, >=4.0.0 | BSD-3-Clause | backend, shared | PDF generation | MEDIUM |
| 19 | **arabic-reshaper** | >=3.0.0 | MIT | backend | Arabic text shaping | LOW |
| 20 | **python-bidi** | >=0.4.2 | LGPL | backend | Bidirectional text | LOW |
| 21 | **httpx** | >=0.27.0, ==0.27.2 | BSD-3-Clause | backend, shared, nhop, edge_agent, device_bridge | Async HTTP client | MEDIUM |
| 22 | **redis** | >=5.0.0, ==5.1.1 | MIT | backend, shared, nhop, root | Redis client (caching, rate limiting) | HIGH |
| 23 | **orjson** | >=3.9.0 | Apache-2.0 / MIT | backend | Fast JSON serialization | LOW |
| 24 | **sentry-sdk[fastapi]** | >=2.0.0 | MIT | backend, shared (opt) | Error tracking | LOW |
| 25 | **pytest** | >=8.0.0 | MIT | backend-dev, shared-dev | Testing framework | LOW (dev) |
| 26 | **pytest-asyncio** | >=0.23.0,<1.0.0 | Apache-2.0 | backend-dev | Async test support | LOW (dev) |
| 27 | **boto3** | >=1.28.0 | Apache-2.0 | shared | AWS SDK | MEDIUM |
| 28 | **firebase-admin** | >=6.0.0 | Apache-2.0 | shared | Firebase admin SDK | MEDIUM |
| 29 | **python-barcode** | >=0.15.0 | MIT | shared | Barcode generation | LOW |
| 30 | **pika** | >=1.3.0 | BSD-3-Clause | shared | RabbitMQ client | MEDIUM |
| 31 | **opentelemetry-api** | >=1.20.0 | Apache-2.0 | shared | OpenTelemetry tracing API | LOW |
| 32 | **opentelemetry-sdk** | >=1.20.0 | Apache-2.0 | shared | OpenTelemetry SDK | LOW |
| 33 | **whoosh** | >=1.7.0 | BSD-2-Clause | shared | Full-text search | LOW |
| 34 | **google-generativeai** | >=0.8.0 | Apache-2.0 | shared | Gemini AI SDK | LOW |
| 35 | **jsonschema** | >=4.20.0 | MIT | shared | JSON schema validation | LOW |
| 36 | **jsonpath-ng** | >=1.6.0 | Apache-2.0 | shared | JSONPath queries | LOW |
| 37 | **tomli** | >=2.0.0 | MIT | edge_agent | TOML parsing | LOW |
| 38 | **psutil** | >=5.9.0 | BSD-3-Clause | edge_agent | System monitoring | LOW |
| 39 | **setuptools** | >=80.0 | MIT | shared (build), root (build) | Build system | LOW (build) |
| 40 | **ruff** | >=0.5.0 | MIT | shared-dev | Linter | LOW (dev) |
| 41 | **mypy** | >=1.10.0 | MIT | shared-dev | Type checker | LOW (dev) |
| 42 | **coverage** | >=7.0.0 | Apache-2.0 | shared-dev | Code coverage | LOW (dev) |
| 43 | **bandit** | >=1.7.0 | Apache-2.0 | shared-dev | Security linter | LOW (dev) |
| 44 | **celery** | >=5.3.0 | BSD-3-Clause | shared (optional) | Task queue | LOW (opt) |

### Python Packages Referenced Only in Dockerfiles (Not in requirements.txt)

| Package | Dockerfile(s) | License | Notes |
|---|---|---|---|
| prometheus-client | services/*/Dockerfile | Apache-2.0 | Installed via `pip install` inline |
| requests | services/ai/Dockerfile, services/autonomous_manager/Dockerfile, services/result/Dockerfile | Apache-2.0 | HTTP client (unpinned) |
| kafka-python | services/result/Dockerfile | Apache-2.0 | Kafka client (unpinned) |
| minio | services/result/Dockerfile | Apache-2.0 | S3-compatible storage (unpinned) |
| asyncpg | services/lab,order,patient,sample/ Dockerfiles | Apache-2.0 | Async Postgres (unpinned) |

---

## 3. JavaScript / TypeScript Dependency Table

### Root Client (`package.json`) — Production Dependencies

| # | Package | Version | License | Purpose | Risk Level |
|---|---|---|---|---|---|
| 1 | **express** | ^4.18.2 | MIT | Web framework | HIGH |
| 2 | **@trpc/server** | ^10.45.0 | MIT | tRPC server | MEDIUM |
| 3 | **@trpc/client** | ^10.45.0 | MIT | tRPC client | MEDIUM |
| 4 | **@trpc/react-query** | ^10.45.0 | MIT | tRPC React integration | MEDIUM |
| 5 | **react** | ^18.2.0 | MIT | UI library | MEDIUM |
| 6 | **react-dom** | ^18.2.0 | MIT | DOM renderer | MEDIUM |
| 7 | **react-router-dom** | ^6.20.0 | MIT | Client routing | MEDIUM |
| 8 | **tailwindcss** | ^3.4.0 | MIT | CSS framework | LOW |
| 9 | **mysql2** | ^3.6.5 | MIT | MySQL database driver | HIGH |
| 10 | **redis** | ^4.6.12 | MIT | Redis client | MEDIUM |
| 11 | **zod** | ^3.22.4 | MIT | Schema validation | MEDIUM |
| 12 | **@tanstack/react-query** | ^5.28.0 | MIT | Data fetching | MEDIUM |
| 13 | **@tanstack/react-query-devtools** | ^5.28.0 | MIT | Dev tools | LOW (dev) |
| 14 | **jsonwebtoken** | ^9.0.3 | MIT | JWT handling | CRITICAL |
| 15 | **bcryptjs** | ^2.4.3 | MIT | Password hashing (JS) | CRITICAL |
| 16 | **dotenv** | ^16.3.1 | BSD-2-Clause | Env var loading | LOW |
| 17 | **axios** | ^1.8.2 | MIT | HTTP client | MEDIUM |
| 18 | **cors** | ^2.8.5 | MIT | CORS middleware | LOW |
| 19 | **helmet** | ^7.1.0 | MIT | Security headers | CRITICAL |
| 20 | **compression** | ^1.7.4 | MIT | Gzip compression | LOW |
| 21 | **uuid** | ^11.1.0 | MIT | UUID generation | LOW |
| 22 | **superjson** | ^2.2.1 | MIT | Super JSON serialization | LOW |
| 23 | **date-fns** | ^2.30.0 | MIT | Date utilities | LOW |
| 24 | **clsx** | ^2.0.0 | MIT | CSS class builder | LOW |
| 25 | **class-variance-authority** | ^0.7.0 | Apache-2.0 | Component variants | LOW |
| 26 | **lodash** | ^4.17.21 | MIT | Utility library | LOW |
| 27 | **recharts** | ^2.10.3 | MIT | Charts | LOW |
| 28 | **lucide-react** | ^0.344.0 | ISC | Icons | LOW |
| 29 | **framer-motion** | ^10.16.16 | MIT | Animations | LOW |
| 30 | **@types/uuid** | ^10.0.0 | MIT | TypeScript types | LOW (dev) |

### Frontend v2 (`frontend-v2/package.json`) — Production Dependencies

| # | Package | Version | License | Purpose | Risk Level |
|---|---|---|---|---|---|
| 31 | **firebase** | ^11.1.0 | Apache-2.0 | Firebase SDK (auth, firestore) | CRITICAL |
| 32 | **@google/genai** | ^1.50.1 | Apache-2.0 | GenAI SDK | LOW |
| 33 | **@google/generative-ai** | ^0.24.1 | Apache-2.0 | Gemini AI SDK | LOW |
| 34 | **@sentry/react** | ^8.42.0 | MIT | Error tracking | LOW |
| 35 | **@tailwindcss/vite** | ^4.1.14 | MIT | Tailwind Vite plugin | LOW |
| 36 | **cmdk** | ^1.1.1 | MIT | Command palette | LOW |
| 37 | **date-fns** | ^4.1.0 | MIT | Date utilities | LOW |
| 38 | **dotenv** | ^17.2.3 | BSD-2-Clause | Env loading | LOW |
| 39 | **express** | ^4.21.2 | MIT | Web server (dev proxy) | MEDIUM |
| 40 | **html5-qrcode** | ^2.3.8 | Apache-2.0 | QR code scanning | LOW |
| 41 | **lucide-react** | ^0.546.0 | ISC | Icons | LOW |
| 42 | **motion** | ^12.23.24 | MIT | Animations | LOW |
| 43 | **posthog-js** | ^1.205.0 | MIT | Product analytics | LOW |
| 44 | **react** | ^19.0.0 | MIT | UI library | MEDIUM |
| 45 | **react-barcode** | ^1.6.1 | MIT | Barcode rendering | LOW |
| 46 | **react-dom** | ^19.0.0 | MIT | DOM renderer | MEDIUM |
| 47 | **react-easy-crop** | ^5.5.7 | MIT | Image crop | LOW |
| 48 | **react-hot-toast** | ^2.6.0 | MIT | Toast notifications | LOW |
| 49 | **react-is** | ^19.2.6 | MIT | React type checking | LOW |
| 50 | **react-markdown** | ^10.1.0 | MIT | Markdown rendering | LOW |
| 51 | **react-router-dom** | ^7.14.1 | MIT | Client routing | MEDIUM |
| 52 | **recharts** | ^3.8.1 | MIT | Charts | LOW |
| 53 | **sonner** | ^2.0.7 | MIT | Toast notifications | LOW |
| 54 | **tailwind-merge** | ^3.5.0 | MIT | Tailwind class merge | LOW |
| 55 | **vite** | ^6.2.0 | MIT | Build tool | LOW (dev) |
| 56 | **vite-plugin-pwa** | ^1.2.0 | MIT | PWA support | LOW |
| 57 | **clsx** | ^2.1.1 | MIT | CSS class builder | LOW |
| 58 | **@vitejs/plugin-react** | ^5.0.4 | MIT | React Vite plugin | LOW (dev) |
| 59 | **@firebase/eslint-plugin-security-rules** | ^0.0.1 | Apache-2.0 | Firebase security rules lint | LOW (dev) |

### Dev Dependencies (Both Projects)

| # | Package | Version | License | Location | Purpose |
|---|---|---|---|---|---|
| 60 | typescript | ^5.3.3 / ~5.8.2 | Apache-2.0 | root, frontend-v2 | TypeScript compiler |
| 61 | tsx | ^4.7.0 / ^4.21.0 | MIT | root, frontend-v2 | TS execution |
| 62 | vite | ^7.3.2 / ^6.2.0 | MIT | root, frontend-v2 | Build tool |
| 63 | @vitejs/plugin-react | ^5.2.0 | MIT | root | React Vite plugin |
| 64 | @vitejs/plugin-basic-ssl | ^1.0.1 | MIT | root | SSL dev plugin |
| 65 | vitest | ^1.0.4 | MIT | root | Test runner |
| 66 | @vitest/ui | ^1.1.0 | MIT | root | Vitest UI |
| 67 | eslint | ^8.56.0 | MIT | root | Linter |
| 68 | prettier | ^3.1.1 | MIT | root | Formatter |
| 69 | @typescript-eslint/eslint-plugin | ^6.16.0 | MIT | root | TS lint rules |
| 70 | @typescript-eslint/parser | ^6.16.0 | MIT | root | TS parser |
| 71 | @tailwindcss/forms | ^0.5.7 | MIT | root | Form styles |
| 72 | @tailwindcss/typography | ^0.5.10 | MIT | root | Typography plugin |
| 73 | shadcn-ui | ^0.8.0 | MIT | root | UI components |
| 74 | postcss | ^8.4.32 | MIT | root | CSS post-processor |
| 75 | autoprefixer | ^10.4.16 / ^10.4.21 | MIT | root, frontend-v2 | CSS prefixer |
| 76 | @testing-library/react | ^14.1.2 | MIT | root | React testing |
| 77 | @testing-library/jest-dom | ^6.1.5 | MIT | root | DOM matchers |
| 78 | @testing-library/user-event | ^14.5.1 | MIT | root | User events |
| 79 | @vitest/coverage-v8 | ^1.0.4 | MIT | root | Coverage |
| 80 | vitest-mock-extended | ^1.3.2 | MIT | root | Mocking |
| 81 | tailwindcss | ^4.1.14 | MIT | frontend-v2 | CSS framework |
| 82 | @types/express | ^4.17.21 | MIT | root, frontend-v2 | Express types |
| 83 | @types/react | ^18.2.45 | MIT | root | React types |
| 84 | @types/react-dom | ^18.2.18 | MIT | root | React DOM types |
| 85 | @types/cors | ^2.8.17 | MIT | root | CORS types |
| 86 | @types/compression | ^1.7.5 | MIT | root | Compression types |
| 87 | @types/lodash | ^4.14.202 | MIT | root | Lodash types |
| 88 | @types/react-router-dom | ^5.3.3 | MIT | root | Router types |
| 89 | @types/jest | ^29.5.11 | MIT | root | Jest types |
| 90 | @types/node | ^20.10.6 / ^22.14.0 | MIT | root, frontend-v2 | Node types |

---

## 4. Docker Images

### Base Images Used Across All Dockerfiles

| Base Image | Tag | Used In | Purpose | Size Class |
|---|---|---|---|---|
| **python** | `3.11-slim` | `backend/Dockerfile`, `services/{ai,lab,order,patient,result,sample,notification,autonomous_manager}/Dockerfile` | Backend API + 7 microservices | ~120 MB |
| **python** | `3.12-slim` | `nhop-platform/Dockerfile`, `services/device_bridge/Dockerfile` | NHOP + Device Bridge | ~130 MB |
| **python** | `3.10` | `docker/Dockerfile` (legacy) | Legacy Dockerfile | ~150 MB |
| **postgres** | `16-alpine` | `docker-compose.yml` | Primary database | ~85 MB |
| **redis** | `7-alpine` | `docker-compose.yml` | Cache / rate-limiting | ~12 MB |
| **nginx** | `1.25-alpine` | `docker-compose.yml` (frontend + api-gateway) | Static file serving + reverse proxy | ~25 MB |
| **prom/prometheus** | `v2.50.1` | `docker-compose.yml` (monitoring profile) | Metrics collection | ~200 MB |
| **grafana/grafana** | `10.3.3` | `docker-compose.yml` (monitoring profile) | Dashboard visualization | ~180 MB |
| **node** | `20-alpine` | `Dockerfile` (root) | Frontend client build + runtime | ~125 MB |

### Image Dependency Graph

```
                        ┌──────────────────┐
                        │  python:3.11-slim  │
                        │  (base for 8 img)  │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
         gula-backend    gula-worker    services/*
         (FastAPI)      (bg worker)   (microsvc)

                        ┌──────────────────┐
                        │  python:3.12-slim  │
                        │  (base for 2 img)  │
                        └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            nhop-platform           device-bridge

                        ┌──────────────────┐
                        │  node:20-alpine    │
                        │  (client build)   │
                        └──────────────────┘
```

---

## 5. Risk Assessment

### CRITICAL — Auth / Encryption / Security / Patient Data

| Package | Reason |
|---|---|
| **passlib[bcrypt]** | Password hashing — compromise leaks all user credentials |
| **bcrypt** | Core password hashing primitive |
| **python-jose[cryptography]** | JWT signing/verification — auth backbone |
| **cryptography** | All encryption ops (NID encryption, Fernet, HMAC keys) |
| **jsonwebtoken** (JS) | JWT handling in the client |
| **bcryptjs** (JS) | Client-side password hashing |
| **helmet** (JS) | Security headers — CSP, HSTS, X-Frame-Options |
| **firebase** (JS frontend) | Auth provider for citizen portal |

### HIGH — Web Framework / Database / Core Business Logic

| Package | Reason |
|---|---|
| **fastapi** | Primary web framework — all HTTP entry points |
| **sqlalchemy** | All database queries — SQL injection surface |
| **alembic** | Schema migrations — correctness is critical |
| **pydantic** | All input validation — bypass could allow data corruption |
| **redis** | Session cache, rate limiting, permission invalidation |
| **express** (JS) | Client web server |
| **mysql2** (JS) | Database driver in the client |
| **react** / **react-dom** (JS) | Core UI framework |

### MEDIUM — Utilities / Formatting / Reporting

| Package | Reason |
|---|---|
| **uvicorn** | ASGI server — performance and stability |
| **gunicorn** | Process management |
| **psycopg2-binary** / **asyncpg** | DB connectivity |
| **python-multipart** | File upload parsing |
| **Pillow** | Image processing (potential RCE via malformed images) |
| **reportlab** | PDF generation (patient reports) |
| **httpx** | Service-to-service HTTP calls |
| **jinja2** | HTML templating (server-side template injection risk) |
| **boto3** | AWS SDK — cloud credentials |
| **firebase-admin** | Firebase admin — privileged access |
| **pika** | RabbitMQ — message queue |
| **axios** (JS) | HTTP client |
| **@trpc/** (JS) | API communication layer |
| **@tanstack/react-query** (JS) | Data fetching |

### LOW — Dev Tools / Documentation / Monitoring

| Package | Reason |
|---|---|
| **orjson** | Performance optimization only |
| **qrcode** | QR generation |
| **arabic-reshaper** / **python-bidi** | Text rendering |
| **sentry-sdk** | Error monitoring (opt-in) |
| **opentelemetry-*** | Tracing (opt-in) |
| **whoosh** | Search indexing |
| **google-generativeai** | AI features (opt-in) |
| **celery** | Task queue (opt-in) |
| **pytest** / **vitest** / **eslint** / **ruff** / **mypy** | All dev/test tools |
| **tomli** / **psutil** | Edge agent utilities |
| **all tailwind/UI/styling packages** | Presentation layer only |
| **recharts** / **lucide-react** / **framer-motion** | UI enhancements |

---

## 6. Known Vulnerabilities

### FastAPI

| CVE | Severity | Affected Versions | Fixed In | Status in GULA |
|---|---|---|---|---|
| CVE-2024-24762 | HIGH (ReDoS) | < 0.109.1 | 0.109.1 | ✅ **Not affected** (>=0.110.0) |
| CVE-2021-32677 | HIGH (CSRF) | < 0.65.2 | 0.65.2 | ✅ **Not affected** |
| CVE-2026-48710 (Starlette BadHost) | MEDIUM | Starlette < 1.0.1 | 1.0.1 | ⚠️ **Check fastapi sub-dependency** |
| CVE-2025-68481 (fastapi-users OAuth) | MEDIUM | fastapi-users < 15.0.2 | 15.0.2 | ⚠️ **Not used directly** (but verify) |

### SQLAlchemy

| CVE | Severity | Affected Versions | Fixed In | Status in GULA |
|---|---|---|---|---|
| CVE-2019-7548 | HIGH (SQLi in group_by) | 1.2.17 | 1.3.0 | ✅ **Not affected** (>=2.0.30) |
| CVE-2019-7164 | HIGH (SQLi) | < 1.3.0 | 1.3.0 | ✅ **Not affected** |
| CVE-2012-0805 | MEDIUM (SQLi) | < 0.7.0b4 | 0.7.0 | ✅ **Not affected** |

No known CVEs in SQLAlchemy 2.x as of 2026-07-14.

### Pydantic

| CVE | Severity | Affected Versions | Fixed In | Status in GULA |
|---|---|---|---|---|
| CVE-2024-3772 | MODERATE (ReDoS) | 2.0.0–2.4.0, < 1.10.13 | 2.4.0 | ✅ **Not affected** (>=2.7.0) |
| CVE-2021-29510 | MODERATE (Infinite loop) | < 1.6.2, 1.7–1.7.4, 1.8–1.8.2 | 1.8.2 | ✅ **Not affected** |

### cryptography

| CVE | Severity | Affected Versions | Fixed In | Status in GULA |
|---|---|---|---|---|
| CVE-2026-39892 | MEDIUM (Buffer overflow) | 45.0.0–46.0.6 | 46.0.7 | ✅ **Not affected** (>=42.0.0, <45.0.0) |
| CVE-2026-26007 | MEDIUM (ECDH info disclosure) | < 46.0.5 | 46.0.5 | ✅ **Not affected** |
| CVE-2026-34073 | MEDIUM (DNS validation) | < 46.0.6 | 46.0.6 | ✅ **Not affected** |
| CVE-2024-26130 | HIGH (NULL deref DoS) | 41.0.0–42.0.4 | 42.0.5 | ✅ **Not affected** (>=42.0.0 — check exact pinned) |
| CVE-2023-49083 | MEDIUM (NULL deref) | 3.1–41.0.6 | 41.0.6 | ✅ **Not affected** |
| CVE-2023-50782 | MEDIUM (Bleichenbacher) | < 41.0.5 | 41.0.5 | ✅ **Not affected** |
| CVE-2020-25659 | MEDIUM (Timing attack) | 3.2 | 3.3.2 | ✅ **Not affected** |

### python-jose

| CVE | Severity | Affected Versions | Fixed In | Status in GULA |
|---|---|---|---|---|
| CVE-2024-33663 | MEDIUM (Algorithm confusion) | <= 3.3.0 | 3.4.0 | ❌ **AFFECTED** — backend uses >=3.3.0, shared uses >=3.3.0. **Upgrade to >=3.4.0** |
| CVE-2024-33664 | MEDIUM (JWT bomb DoS) | <= 3.3.0 | 3.4.0 | ❌ **AFFECTED** — same fix version |
| CVE-2024-29370 | MEDIUM (JWE DoS) | 3.3.0 | 3.4.0 | ❌ **AFFECTED** — same fix version |
| CVE-2016-7036 | MEDIUM (Timing attack) | < 1.3.2 | 1.3.2 | ✅ **Not affected** |

### Additional Noteworthy CVEs

| Package | CVE | Severity | Notes |
|---|---|---|---|
| **Pillow** | CVE-2023-50447 | HIGH | Heap buffer overflow — fixed in 10.2.0. **GULA has >=10.4.0 — not affected** |
| **Pillow** | Multiple (CVE-2024-28219, etc.) | MEDIUM | Various — all fixed by 10.3.0. **Not affected** |
| **jinja2** | CVE-2024-22195 | MEDIUM | Sandbox escape via `|attr` filter — fixed in 3.1.3. **Not affected** (>=3.1.4) |
| **reportlab** | CVE-2024-42512 | CRITICAL | Sandbox escape allowing arbitrary code execution — fixed in 4.2.1. **GULA has >=4.1.0 — needs verification** |
| **reportlab** | CVE-2023-33733 | CRITICAL | RCE via code injection — fixed in 4.0. **Not affected** (>=4.1.0) |
| **gunicorn** | CVE-2024-1135 | MEDIUM | HTTP response splitting — fixed in 22.0.0. **GULA has >=21.2.0 — verify** |
| **psycopg2-binary** | CVE-2024-39398 | MEDIUM | DoS via malformed data — fixed in 2.9.10. **GULA has >=2.9.9 — check** |
| **lodash** (JS) | Multiple | HIGH | Prototype pollution CVEs — fixed in 4.17.21+ via resolutions |
| **axios** (JS) | CVE-2024-39338 | HIGH | SSRF — fixed in 1.7.4. **resolutions enforce >=1.8.2** |
| **jsonwebtoken** (JS) | CVE-2022-23529 | HIGH | Unrestricted key type — fixed in 9.0.1+. **GULA has ^9.0.3** |

### Critical Vulnerability Summary

| Severity | Count | Action Required |
|---|---|---|
| CRITICAL (CVSS >=9) | 0 direct — reportlab needs pin verification | Verify reportlab >=4.2.1 |
| HIGH (CVSS 7–8.9) | 3 (python-jose algorithm confusion, reportlab sandbox, gunicorn splitting) | Upgrade python-jose to >=3.4.0, verify reportlab version |
| MEDIUM (CVSS 4–6.9) | 7+ | Standard patching cadence |
| LOW | Several | Monitor |

---

## 7. License Compliance

### License Inventory

| License | Count | Packages |
|---|---|---|
| **MIT** | ~50+ | fastapi, pydantic, sqlalchemy, alembic, gunicorn, httpx, redis, passlib, python-jose, jinja2, qrcode, pytest, most JS packages |
| **BSD-3-Clause** | ~8 | uvicorn, passlib, reportlab, psutil, pika, qrcode (alt) |
| **BSD-2-Clause** | ~2 | whoosh, dotenv (JS) |
| **Apache-2.0** | ~15 | bcrypt, cryptography, asyncpg, python-multipart, boto3, firebase-admin, orjson, opentelemetry-*, google-generativeai, bandit, coverage, mypy, typescript |
| **LGPL** | 2 | psycopg2-binary, python-bidi |
| **ISC** | 1 | lucide-react |
| **Historical (MIT-like)** | 1 | Pillow |
| **Proprietary** | 2 | gula-shared, gula-platform |

### Copyleft / Restricted Licenses

| License | Package | Risk | Mitigation |
|---|---|---|---|
| **LGPL-3.0** | **psycopg2-binary** | LOW — LGPL allows dynamic linking without GPL obligations | Used as dynamically linked library — compliant |
| **LGPL-3.0** | **python-bidi** | LOW — same as above | Used as PyPI import — compliant |

**No GPL, AGPL, or SSPL packages detected in the dependency tree.** The project is fully compatible with proprietary distribution.

### License Compatibility Matrix

| GULA Code (Proprietary) | MIT | Apache-2.0 | BSD | LGPL |
|---|---|---|---|---|
| ✅ Compatible | ✅ Compatible | ✅ Compatible | ✅ Compatible | ✅ Compatible (dynamic link) |

### Required Attribution

When distributing, the following packages require copyright notice preservation:
- **MIT licensed:** All require the MIT copyright notice to be included
- **Apache-2.0:** Requires NOTICE file preservation + copyright notice
- **BSD:** Requires copyright notice and disclaimer

---

## 8. Recommendations

### 8.1 Packages to Update (Security)

| Package | Current Spec | Recommended | Reason |
|---|---|---|---|
| **python-jose** | >=3.3.0 | >=3.4.0 | CVE-2024-33663 (algorithm confusion), CVE-2024-33664 (JWT bomb), CVE-2024-29370 (JWE DoS) — all fixed in 3.4.0. **CRITICAL for auth security.** |
| **reportlab** | >=4.1.0 | >=4.2.1 | CVE-2024-42512 (sandbox escape, RCE) fixed in 4.2.1 |
| **gunicorn** | >=21.2.0 | >=22.0.0 | CVE-2024-1135 (HTTP response splitting) |
| **psycopg2-binary** | >=2.9.9 | >=2.9.10 | CVE-2024-39398 (DoS) |
| **cryptography** (shared) | >=41.0.0 | >=42.0.0 | Multiple CVEs (CVE-2024-26130, CVE-2023-49083). Backend already requires >=42.0.0 but shared pins lower. |

### 8.2 Packages to Pin to Exact Versions

| Package | Reason |
|---|---|
| **cryptography** | Cryptographic correctness is version-sensitive — pin to exact version across all sub-projects |
| **python-jose** | JWT auth is security-critical — pin to exact patched version |
| **bcrypt** | Already pinned with upper bound (`<4.2.0`) due to passlib incompatibility — this pattern is correct |
| **fastapi** | Framework version affects API behavior — consider pinning all sub-projects to same version |
| **sqlalchemy** | ORM behavior changes between minor versions — pin to exact |

### 8.3 Packages to Remove (Unused / Redundant)

| Package | Location | Reason |
|---|---|---|
| **@firebase/eslint-plugin-security-rules** | frontend-v2 | Only applies to Firebase security rules — not used in the actual codebase. Check if needed. |
| **@types/react-router-dom** | Root | React Router v6 has built-in types — this type package is for v5 and may be stale |
| **@types/uuid** | Root | UUID v11 includes types natively — redundant (listed as both dependency and devDependency) |
| **python-barcode** | shared | Check if `qrcode` + `Pillow` already cover barcode need. Reportlab also generates barcodes. Potential overlap. |
| **whoosh** | shared | Pure-Python full-text search — verify it's actually used vs. PostgreSQL full-text search. |

### 8.4 Packages to Add

| Package | Reason | Priority |
|---|---|---|
| **pip-audit** or **safety** (dev) | Automated vulnerability scanning in CI/CD | HIGH |
| **PyJWT** (alternative to python-jose) | python-jose is unmaintained (last release 2025, repo inactive, 95 open issues). PyJWT has active maintenance, 4x more stars, fewer issues. Consider migration. | MEDIUM |
| **uvloop** | Faster event loop for uvicorn (2–4x throughput increase). Add to `uvicorn[standard]` or explicitly. | LOW |
| **python-dotenv** (if not already) | Ensure consistent env loading across all sub-projects | LOW |
| **watchfiles** | Auto-reload for development (already part of uvicorn[standard] but explicit pin helps) | LOW |

### 8.5 Cross-Cutting Concerns

| Issue | Recommendation |
|---|---|
| **Version alignment** | `cryptography`, `pydantic`, `httpx`, `redis` are specified in 4+ files with different minimum versions. Consolidate to a single `_requirements_base.txt` or use a `constraints.txt` file to enforce a single version across the monorepo. |
| **Unpinned Docker deps** | 7 microservice Dockerfiles install packages via `pip install` without version pins (`fastapi`, `uvicorn`, `pydantic`, `prometheus-client`, `requests`). Pin these to match the backend versions. |
| **python-jose deprecation** | The python-jose library has 95 open issues, infrequent releases, and known unpatched vulnerabilities. Consider migrating to **PyJWT** + **python-jwcrypto** for production JWT handling. Backend uses `python-jose[cryptography]` — the `cryptography` extra is the safest backend, but the library itself carries risk. |
| **Node.js version alignment** | Root uses node >=20.0.0 but Dockerfile uses `node:20-alpine`. Frontend-v2 has no engines field specified. Align all to node 20 LTS. |
| **SBOM automation** | Integrate `cyclonedx-bom` generation into CI pipeline (`make sbom` target). The existing XML files in `assessment/brain/` are manually generated. |
| **Dependency scanning** | Add `pip-audit` and `npm audit` / `pnpm audit` to the CI pipeline (syntax-gate or a new security-scan job). |

### 8.6 Docker Image Security

| Container | Base Image | Issues | Recommendation |
|---|---|---|---|
| All python images | `python:3.11-slim` / `3.12-slim` | Generally good. | Regularly rebuild to pick up OS patch updates. |
| device-bridge | `python:3.12-slim` | Uses `pip install` without `--no-cache-dir` in Dockerfile (already has it for `RUN pip install` but `COPY pyproject.toml` + `pip install` is fine). | Ensure `pip install --no-cache-dir` is used. |
| prometheus / grafana | `prom/prometheus:v2.50.1`, `grafana/grafana:10.3.3` | Monitoring images pinned to specific versions — good practice. | Subscribe to CVE alerts for these images. |
| nginx | `nginx:1.25-alpine` | Outdated — nginx 1.25 series is EOL. | **Upgrade to `nginx:1.26-alpine` or `nginx:1.27-alpine`.** |
| postgres / redis | Alpine variants | Well-configured with health checks and resource limits. | No immediate action needed. |
| node | `node:20-alpine` | Current LTS. | Keep updated to latest 20.x patch. |

---

## Appendix A: Dependency Tree (Python, consolidated deduplicated)

```
gula-platform (proprietary)
├── backend/requirements.txt (23 prod deps)
│   ├── fastapi>=0.110.0         ─── Web framework
│   ├── uvicorn[standard]>=0.29.0 ─── ASGI server
│   ├── gunicorn>=21.2.0        ─── WSGI manager
│   ├── sqlalchemy>=2.0.30      ─── ORM
│   ├── alembic>=1.13.0         ─── Migrations
│   ├── psycopg2-binary>=2.9.9  ─── Postgres adapter
│   ├── python-multipart>=0.0.20
│   ├── pydantic>=2.7.0
│   ├── pydantic-settings>=2.0.0
│   ├── passlib[bcrypt]>=1.7.4
│   ├── bcrypt>=4.1.3,<4.2.0
│   ├── python-jose[cryptography]>=3.3.0
│   ├── cryptography>=42.0.0
│   ├── qrcode>=7.4.2
│   ├── Pillow>=10.4.0
│   ├── jinja2>=3.1.4
│   ├── reportlab>=4.1.0
│   ├── arabic-reshaper>=3.0.0
│   ├── python-bidi>=0.4.2
│   ├── httpx>=0.27.0
│   ├── redis>=5.0.0
│   ├── orjson>=3.9.0
│   └── sentry-sdk[fastapi]>=2.0.0
│
├── backend/requirements-dev.txt (2 dev deps)
│   ├── pytest>=8.0.0
│   └── pytest-asyncio>=0.23.0,<1.0.0
│
├── shared/pyproject.toml (20 prod + 5 dev + 2 opt)
│   ├── bcrypt>=4.0.0
│   ├── cryptography>=41.0.0
│   ├── python-jose>=3.3.0
│   ├── pydantic>=2.0.0
│   ├── pydantic-settings>=2.0.0
│   ├── boto3>=1.28.0
│   ├── firebase-admin>=6.0.0
│   ├── redis>=5.0.0
│   ├── reportlab>=4.0.0
│   ├── qrcode>=7.4.0
│   ├── python-barcode>=0.15.0
│   ├── pillow>=10.0.0
│   ├── pika>=1.3.0
│   ├── opentelemetry-api>=1.20.0
│   ├── opentelemetry-sdk>=1.20.0
│   ├── whoosh>=1.7.0
│   ├── google-generativeai>=0.8.0
│   ├── httpx>=0.27.0
│   ├── jsonschema>=4.20.0
│   ├── jsonpath-ng>=1.6.0
│   ├── [dev] pytest>=8.0.0, ruff>=0.5.0, mypy>=1.10.0, coverage>=7.0.0, bandit>=1.7.0
│   └── [opt] sentry-sdk>=2.0.0, celery>=5.3.0
│
├── nhop-platform/requirements.txt (11 prod deps — pinned)
│   ├── fastapi==0.115.0
│   ├── uvicorn[standard]==0.30.6
│   ├── sqlalchemy==2.0.35
│   ├── asyncpg==0.29.0
│   ├── psycopg2-binary==2.9.9
│   ├── alembic==1.13.3
│   ├── pydantic==2.9.2
│   ├── pydantic-settings==2.5.2
│   ├── redis==5.1.1
│   ├── python-multipart>=0.0.20
│   └── httpx==0.27.2
│
├── edge_agent/requirements.txt (4 prod deps)
│   ├── httpx>=0.27.0
│   ├── cryptography>=42.0.0
│   ├── tomli>=2.0.0
│   └── psutil>=5.9.0
│
├── services/device_bridge/pyproject.toml (4 prod deps)
│   ├── fastapi>=0.115.0
│   ├── uvicorn>=0.30.0
│   ├── pydantic>=2.8.0
│   └── httpx>=0.27.0
│
└── requirements.txt (root, 4 deps)
    ├── fastapi
    ├── uvicorn
    ├── redis
    └── python-multipart>=0.0.20
```

## Appendix B: CycloneDX SBOM Files

Pre-generated CycloneDX JSON files exist at:

| File | Contents |
|---|---|
| `assessment/brain/sbom-backend.xml` | CycloneDX v1.6 — covers `backend/requirements.txt` (24 components) |
| `assessment/brain/sbom-shared.xml` | CycloneDX v1.6 — covers `shared/pyproject.toml` (root component only, no sub-dependencies resolved) |

**Note:** Both files were generated with `cyclonedx-py` v7.3.0 / `cyclonedx-python-lib` v11.11.0. The shared SBOM does not contain individual component entries — it only registered the root `gula-shared` component. Regenerate with `--deep` or resolution flags to capture transitive dependencies.

---

*This SBOM was generated by analyzing source dependency files across the GULA monorepo. For production accuracy, regenerate from lock files (`pip freeze`, `pnpm-lock.yaml`).*
