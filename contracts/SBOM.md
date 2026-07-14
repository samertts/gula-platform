# Software Bill of Materials — GULA Platform

**Contract Tag:** `integration-contracts-v1.0` | **Date:** 2026-07-14
**SPDX Identifier:** GULA-2.1.0

---

## 1. Python Backend (`backend/`)

### Core Runtime

| Package | Version | License | Purpose |
|---|---|---|---|
| fastapi | >=0.110.0 | MIT | Web framework |
| uvicorn[standard] | >=0.29.0 | BSD-3-Clause | ASGI server |
| gunicorn | >=21.2.0 | MIT | WSGI process manager |
| sqlalchemy | >=2.0.30 | MIT | ORM / database toolkit |
| alembic | >=1.13.0 | MIT | Database migrations |
| psycopg2-binary | >=2.9.9 | LGPL-3.0 | PostgreSQL adapter |
| pydantic | >=2.7.0 | MIT | Data validation / settings |
| pydantic-settings | >=2.0.0 | MIT | Settings management |
| python-multipart | >=0.0.20 | Apache-2.0 | Multipart form parsing |

### Security

| Package | Version | License | Purpose |
|---|---|---|---|
| passlib[bcrypt] | >=1.7.4 | BSD-3-Clause | Password hashing |
| bcrypt | >=4.1.3,<4.2.0 | Apache-2.0 | bcrypt algorithm |
| python-jose[cryptography] | >=3.4.0 | MIT | JWT encode/decode |
| cryptography | >=42.0.0 | Apache-2.0 / BSD | Cryptographic operations |
| python-multipart | >=0.0.20 | Apache-2.0 | Form parsing |

### PDF & Reporting

| Package | Version | License | Purpose |
|---|---|---|---|
| reportlab | >=4.1.0 | BSD-3-Clause | PDF generation |
| arabic-reshaper | >=3.0.0 | MIT | Arabic text reshaping |
| python-bidi | >=0.4.2 | LGPL-3.0 | Bi-directional text |
| Pillow | >=10.4.0 | Historical | Image processing |
| qrcode | >=7.4.2 | BSD-3-Clause | QR code generation |

### Infrastructure

| Package | Version | License | Purpose |
|---|---|---|---|
| redis | >=5.0.0 | MIT | Redis client |
| httpx | >=0.27.0 | BSD-3-Clause | HTTP client |

### Observability

| Package | Version | License | Purpose |
|---|---|---|---|
| sentry-sdk[fastapi] | >=2.0.0 | MIT | Error tracking |

### Environment

| Package | Version | License | Purpose |
|---|---|---|---|
| python-dotenv | * | BSD-3-Clause | Env file loading |

### Development & Test

| Package | Version | License |
|---|---|---|
| pytest | * | MIT |
| pytest-asyncio | <1.0.0 | Apache-2.0 |
| pytest-cov | * | MIT |
| httpx | * | BSD-3-Clause |
| ruff | * | MIT |
| pyflakes | * | MIT |
| flake8 | * | MIT |
| bandit | * | Apache-2.0 |
| mypy | * | MIT |
| hypothesis | * | MPL-2.0 |

---

## 2. Node.js Frontend (`frontend-v2/`)

### Core

| Package | Version | License | Purpose |
|---|---|---|---|
| react | ^19.0.0 | MIT | UI framework |
| react-dom | ^19.0.0 | MIT | React DOM renderer |
| react-router-dom | ^7.14.1 | MIT | Client-side routing |
| vite | ^6.2.0 | MIT | Build tool |
| @vitejs/plugin-react | ^5.0.4 | MIT | Vite React plugin |

### UI & Styling

| Package | Version | License | Purpose |
|---|---|---|---|
| tailwindcss | ^4.1.14 | MIT | CSS framework |
| @tailwindcss/vite | ^4.1.14 | MIT | Tailwind Vite plugin |
| tailwind-merge | ^3.5.0 | MIT | Class merging |
| clsx | ^2.1.1 | MIT | Conditional classes |
| lucide-react | ^0.546.0 | ISC | Icons |
| motion | ^12.23.24 | MIT | Animations |
| sonner | ^2.0.7 | MIT | Toast notifications |
| react-hot-toast | ^2.6.0 | MIT | Toast notifications |
| cmdk | ^1.1.1 | MIT | Command palette |
| react-markdown | ^10.1.0 | MIT | Markdown rendering |
| recharts | ^3.8.1 | MIT | Charts |
| react-easy-crop | ^5.5.7 | MIT | Image crop |

### Firebase / Backend

| Package | Version | License | Purpose |
|---|---|---|---|
| firebase | ^11.1.0 | Apache-2.0 | Firebase SDK |
| dotenv | ^17.2.3 | BSD-2-Clause | Env vars |

### AI

| Package | Version | License | Purpose |
|---|---|---|---|
| @google/genai | ^1.50.1 | Apache-2.0 | Google AI SDK |
| @google/generative-ai | ^0.24.1 | Apache-2.0 | Gemini SDK |

### Utilities

| Package | Version | License | Purpose |
|---|---|---|---|
| date-fns | ^4.1.0 | MIT | Date utilities |
| react-barcode | ^1.6.1 | MIT | Barcode rendering |
| html5-qrcode | ^2.3.8 | Apache-2.0 | QR scanning |
| posthog-js | ^1.205.0 | MIT | Analytics |
| @sentry/react | ^8.42.0 | MIT | Error tracking |

### QR / Barcode

| Package | Version | License |
|---|---|---|
| react-barcode | ^1.6.1 | MIT |
| html5-qrcode | ^2.3.8 | Apache-2.0 |

---

## 3. TypeScript SDK (`contracts/sdk/typescript/`)

| Package | Version | License | Purpose |
|---|---|---|---|
| axios | ^1.7.0 | MIT | HTTP client |
| typescript | ^5.5.0 | Apache-2.0 | Language |
| @types/node | ^20.14.0 | MIT | Node types |

---

## 4. Service Dependencies

### Infrastructure Services (Docker Compose)

| Service | Image | Version | License | Purpose |
|---|---|---|---|---|
| PostgreSQL | postgres | 16-alpine | PostgreSQL License | Primary database |
| Redis | redis | 7-alpine | BSD-3-Clause | Cache, rate-limiter, blacklist |
| nginx | nginx | 1.25-alpine | BSD-2-Clause | API gateway |
| Prometheus | prom/prometheus | latest | Apache-2.0 | Metrics (opt-in) |
| Grafana | grafana/grafana | latest | AGPL-3.0 | Dashboards (opt-in) |
| HAProxy | haproxy | latest | GPL-2.0 | Load balancer (scale mode) |

### Cloud Services

| Service | Purpose | Dependency |
|---|---|---|
| Firebase Auth | Citizen portal authentication | Optional (frontend-v2) |
| Firebase Firestore | Citizen portal data | Optional (frontend-v2) |
| Google AI Studio | Gemini AI API | Optional (API key) |
| Sentry | Error tracking | Optional (SENTRY_DSN) |
| PostHog | Product analytics | Optional (frontend-v2) |

---

## 5. Licenses Summary

| License | Packages | Usage |
|---|---|---|
| MIT | 30+ | Majority of dependencies |
| Apache-2.0 | 15+ | Firebase, Google SDKs, cryptography, python-multipart |
| BSD-3-Clause | 8+ | uvicorn, passlib, reportlab, redis-py, httpx, Pillow |
| BSD-2-Clause | 2+ | dotenv, nginx |
| LGPL-3.0 | 2 | psycopg2, python-bidi |
| PostgreSQL License | 1 | PostgreSQL |
| MPL-2.0 | 1 | hypothesis |
| ISC | 1 | lucide-react |
| AGPL-3.0 | 1 | Grafana |
| GPL-2.0 | 1 | HAProxy |
| Historical | 1 | Pillow (historical permission) |
| Proprietary | — | GULA Platform itself |

---

## 6. Generated by

This SBOM was generated from:
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/requirements-lock.txt`
- `frontend-v2/package.json`
- `contracts/sdk/typescript/package.json`
- `contracts/sdk/python/setup.py`
- `docker-compose.yml`
- `docker-compose.full.yml`

**Date:** 2026-07-14
