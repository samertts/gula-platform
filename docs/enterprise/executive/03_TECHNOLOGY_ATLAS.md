# GULA Platform — Technology Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18

---

## 1. Backend Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.139.0 |
| ASGI Server | Uvicorn | 0.51.0 |
| WSGI Server | Gunicorn | 21.2+ |
| Language | Python (CPython) | 3.11+ |
| ORM | SQLAlchemy | 2.0.51 |
| Migrations | Alembic | 1.18.5 |
| Validation | Pydantic | 2.13.4 |
| DB Driver | psycopg2-binary | 2.9.9 |
| JWT/Auth | python-jose | 3.4+ |
| Encryption | cryptography (Fernet) | 49.0.0 |
| Password Hashing | passlib[bcrypt] | 1.7.4 |
| Password Hashing | bcrypt | 4.1.3 |
| HTTP Client | httpx | 0.27+ |
| Redis Client | redis-py | 8.0.1 |
| Error Tracking | sentry-sdk | 2.65.0 |
| QR Generation | qrcode | 7.4.2 |
| Image Processing | Pillow | 10.4.0 |
| PDF Generation | reportlab | 4.1.0 |
| Multipart | python-multipart | 0.0.20 |
| Arabic Text | arabic-reshaper, python-bidi | — |

### Production Dependencies: 17 core packages

---

## 2. Frontend Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Primary Frontend | React | 19 |
| Primary Backend-as-a-Service | Firebase (Firestore + Auth) | — |
| Light Client | React + tRPC | 18 |
| Legacy PWA | Static HTML/CSS/JS | — |
| Desktop | hospital_desktop/ | — |
| TypeScript/JS Files | 1,432 | — |

---

## 3. Database & Storage

| System | Technology | Version | Purpose |
|--------|------------|---------|---------|
| Primary DB | PostgreSQL | 16 (MVP) / 14.11 (full.yml) | All transactional data |
| Cache | Redis | 7-alpine | Session, rate limiting, feature flags |
| Analytics | ClickHouse | 23.8 | Analytical queries (full stack only) |
| Object Storage | MinIO | RELEASE.2024-01 | Document/image storage (full stack only) |
| Stream | Kafka | 7.5.0 | Event streaming (full stack only) |

**Database Scale:** 48 Alembic migrations, 100+ tables, 31+ ORM models, ~250 total tables

---

## 4. Infrastructure & Containerization

| Component | Technology | Notes |
|-----------|------------|-------|
| Container Runtime | Docker | Multi-stage builds |
| Orchestration (Primary) | Docker Compose | 7 services (MVP), 25+ (full) |
| Orchestration (K8s) | Kustomize + Helm | 4 overlays: dev, prod, region-eu, region-me |
| Service Mesh | Linkerd | Auto-inject, configured |
| IaC | Terraform | 12 modules, 5 environments (AWS target — mismatched) |
| PaaS Configs | DigitalOcean, Render, Supabase, Cloudflare | — |

---

## 5. CI/CD Pipeline

| Workflow | Jobs | Purpose |
|----------|------|---------|
| ci.yml (644 lines) | 7 | syntax-gate → migration-check → openapi-contract → backend-test → smoke-test → security-scan → build-and-push (8-image matrix + Trivy) |
| quality-gate.yml | 9 gates | Architecture, Performance, Security, Database, API, FHIR, Scalability, Offline, Accessibility |
| deploy.yml | 1 | SSH → git sync → secrets → pull → zero-downtime restart → health check → auto-rollback |
| canary-deploy.yml | 1 | Linkerd TrafficSplit: 10% → 25% → 50% → 100% |
| blue-green-deploy.yml | 1 | K8s slot swap |
| auto-rollback.yml | 1 | Detect failure → kubectl patch svc |

### Security Scanning in CI
- Safety (CVE), Bandit (SAST), Hadolint (Dockerfile), Gitleaks (secrets), Trivy (container), Semgrep (custom rules), OWASP ZAP (DAST)

---

## 6. Monitoring & Observability

| Layer | Tool | Status |
|-------|------|--------|
| Metrics | Prometheus | ✅ Configured (2 scrape configs, 3 rule files) |
| Dashboards | Grafana | ✅ 11 dashboards (platform, hospital, capacity, laboratory) |
| Logs | Loki + Promtail | ✅ Configured |
| Tracing | Tempo + Jaeger + OpenTelemetry | ⚠️ Configured |
| Alerting | Alertmanager | ✅ Slack + PagerDuty |
| Uptime | Cloudflare + Prometheus | ✅ |
| Synthetic | k6 scripts | ✅ Available, no baseline |
| APM | None | ❌ Missing |

---

## 7. Docker Image Matrix (8 images)

| Image | Base |
|-------|------|
| ghcr.io/gula/backend | Python 3.11-slim |
| ghcr.io/gula/svc-lab | Python 3.11-slim |
| ghcr.io/gula/svc-order | Python 3.11-slim |
| ghcr.io/gula/svc-patient | Python 3.11-slim |
| ghcr.io/gula/svc-result | Python 3.11-slim |
| ghcr.io/gula/svc-sample | Python 3.11-slim |
| ghcr.io/gula/svc-notification | Python 3.11-slim |
| ghcr.io/gula/svc-ai | Python 3.11-slim |

---

## 8. Language Distribution

| Language | Percentage |
|----------|------------|
| Python | 60.5% |
| TypeScript/JavaScript | 25% |
| Shell/YAML | 10% |
| Other | 4.5% |
