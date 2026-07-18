# GULA Platform — Master Discovery Report
**Date:** 2026-07-17
**Classification:** Confidential — Technical Review Board

---

## 1. Platform Identity

| Attribute | Value |
|-----------|-------|
| **Product Name** | GULA Platform (منصة غولا الصحية) |
| **Type** | Medical Laboratory Information System (LIS/LIMS) + National Health Platform |
| **Deployment** | SaaS Multi-Tenant + On-Premise Edge |
| **Primary Market** | Iraq (Ministry of Health, private labs) |
| **Language** | Arabic-first, English bilingual |
| **Version** | app.config.py: 2.1.0; CHANGELOG.md: 2.3.2 (divergence) |
| **Git** | 467+ commits, 3709+ files, 1421+ directories |
| **Code Distribution** | Python 60.5%, TypeScript/JavaScript 25%, Shell/YAML 10%, Other 4.5% |
| **Repository Type** | Monorepo (3 formerly independent repos consolidated) |
| **Total LOC (Python backend only)** | ~120,000+ lines across app/ |

---

## 2. Consolidated Repositories

| Former Repo | Current Location | Maturity |
|-------------|-----------------|----------|
| `samertts/gula-platform` | `backend/`, `services/`, `nhop-platform/`, `ai/` | Production |
| `samertts/LabLink-Core` | `services/device_bridge/` | Mature (36 files, 12 tests) |
| `samertts/Front-end-` | `frontend-v2/` | High complexity (React + Firebase) |

---

## 3. Deployment Targets (5 distinct targets)

| Type | Config | Status |
|------|--------|--------|
| Docker Compose (MVP) | `docker-compose.yml` | **Primary production** |
| Docker Compose (Full) | `docker-compose.full.yml` | Ready (+17 additional services) |
| Kubernetes (Kustomize) | `k8s/base/` + `k8s/overlays/` | Staging/Ready |
| Kubernetes (Helm) | `helm/gula-platform/` | Ready (1326-line values.yaml) |
| DigitalOcean App Platform | `digitalocean/app.yaml` | Ready |
| Render PaaS | `render.yaml` | Documented |
| Supabase | `supabase/` | Partial |

---

## 4. Component Inventory Summary

### Backend Monolith (`backend/app/`)

| Layer | Count | Description |
|-------|-------|-------------|
| **Routes** | 53+ | FastAPI route modules (core + national + clinical) |
| **Models** | 60+ files, ~250 tables | SQLAlchemy ORM models across all domains |
| **Services** | 34+ files | Business logic layer (largest: interpretation.py 1100+, clinical_service.py 1336, ehr_service.py 1324, care_continuum_service.py 1084) |
| **Migrations** | 48 files | Alembic migrations (20250322_0000 → 20260716_0016) |
| **Middleware** | 11 layers | Ordered stack with self-healing, concurrency, security |
| **Security** | 15 files | Auth, RBAC, ABAC, MFA, OAuth2, SAML, rate limiting, encryption |
| **Core** | 15 files | Startup guard, circuit breaker, auto-repair, feature flags |
| **AI** | 2+ files | AI sandbox, guardrails, approval store |
| **Edge** | 10+ files | Edge AI platform control plane |
| **Tests** | 124 files | Unit, integration, security, stress, kernel, hardening |

### Frontends (4 distinct)

| Project | Location | Tech Stack | Purpose |
|---------|----------|------------|---------|
| **frontend-v2** | `frontend-v2/` | React + Firebase (Firestore + Auth) | Citizen portal, Ministry CC, doctor/lab dashboards |
| **client** | `client/` | tRPC + React SPA | Weight tRPC-connected SPA |
| **frontend** | `frontend/` | Static HTML + PWA | Offline-capable PWA |
| **hospital_desktop** | `hospital_desktop/` | Unknown | Hospital desktop application |

### Microservices (`services/`)

| Service | Location | Status |
|---------|----------|--------|
| **device_bridge** | `services/device_bridge/` | **Mature** — 36 files, 12 tests, ASTM/HL7 |
| **ai** | `services/ai/` | Functional — Ollama, 3 tiers |
| **autonomous_manager** | `services/autonomous_manager/` | Functional — self-healing loop |
| **lab** | `services/lab/` | Stub — basic CRUD |
| **order** | `services/order/` | Stub — CRUD + RabbitMQ events |
| **patient** | `services/patient/` | Stub — CRUD + RabbitMQ events |
| **result** | `services/result/` | Feature-rich stub — ClickHouse, Kafka, MinIO |
| **sample** | `services/sample/` | Stub — CRUD + status tracking |
| **notification** | `services/notification/` | Stub — RabbitMQ consumer only |

### Shared Library (`shared/`)

Centralized cross-cutting library: auth (JWT, passwords, MFA, WebAuthn), RBAC permissions, security (encryption, HMAC), circuit breaker, audit, messaging. Used by both monolith and services.

---

## 5. Key Metrics

| Metric | Value |
|--------|-------|
| Total Python files | ~600+ |
| Total JavaScript/TS files | ~1200+ |
| Total Dockerfiles | ~15 |
| Total CI/CD workflows | 6 |
| Total Infrastructure-as-Code files | ~150 (Terraform + K8s + Helm) |
| Total Documentation files | ~200+ |
| Total Routes/Endpoints | 250+ |
| Total Database Tables | ~250+ |
| Total Test Files | ~135+ |
| Total Test Count | 1505+ collected |
| Test Coverage | ~54% |

---

## 6. Architectural Pattern Summary

- **Primary**: FastAPI monolith + PostgreSQL + Redis
- **Secondary**: Microservices (9 services, mostly stubs)
- **Tertiary**: Edge agents, national platform companion
- **Deployment**: Docker Compose (MVP), Docker Compose Full (~25 services), Kubernetes
- **CI/CD**: GitHub Actions (6 workflows) — syntax gate, migrations, smoke, tests, security scan, build/push
- **Progressive delivery**: Canary, blue-green, auto-rollback workflows

---

## 7. Known Critical Issues

1. **Version inconsistency**: app.config says 2.1.0, CHANGELOG says 2.3.2
2. **Microservice maturity gap**: 6 of 9 services are stubs with 0 tests
3. **Frontend-v2 complexity**: Firestore-based with unclear alignment to backend
4. **Test coverage at 54%**: Routes at 35%, Services at 30% — below enterprise thresholds
5. **Edge/interop test coverage**: 0%
6. **Frontend test gaps**: No evidence of comprehensive frontend test suites
7. **Duplicate clinical engines**: `services/ai/main.py` (Ollama-only) vs `backend/app/services/interpretation.py` vs `backend/app/routes/ai.py` (Ollama/Gemini/Groq)
8. **Documentation-code divergence**: Multiple docs reference old architecture (MySQL in INFRASTRUCTURE_GUIDE.md)

---

## 8. Healthcare Standards Support

| Standard | Implementation Status |
|----------|----------------------|
| **FHIR R4/R5** | `routes/ehr_fhir.py` — Patient, Encounter, Observation, Condition, MedicationRequest, Immunization |
| **HL7 v2** | `gateways/lab_device_gateway.py` — ASTM/HL7 device integration |
| **LOINC** | Full model in `clinical/terminology/models.py` — searchable |
| **SNOMED CT** | Full model — searchable via TerminologyService |
| **ICD-10/ICD-11** | Both modeled with hierarchy, billable flags |
| **UCUM, ATC, RxNorm, CPT** | All modeled |
| **Westgard Rules** | Lab QC with 1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10-x |

---

## 9. Infrastructure Maturity

| Capability | Status |
|------------|--------|
| Container Orchestration | Docker Compose (prod) + K8s (ready) |
| Service Mesh | Linkerd (configured in K8s manifests) |
| Database HA | Patroni + PgBouncer + read replicas (full.yml) |
| Redis HA | Sentinel (3 nodes, quorum 2) |
| Message Broker | RabbitMQ (3-node cluster) + Kafka |
| Object Storage | MinIO (distributed, 4 replicas) |
| Monitoring | Prometheus + Grafana + Loki + Tempo |
| Alerting | Alertmanager (Slack, PagerDuty, Email) |
| Tracing | OpenTelemetry + Jaeger/Tempo |
| CI/CD | 6 GitHub Actions workflows |
| IaC | Terraform (AWS) + Helm + Kustomize |
| Security Scanning | Gitleaks, Bandit, Hadolint, Trivy, Safety, Checkov |
| Chaos Engineering | chaos-mesh experiments defined |
| Load Testing | k6 + Locust scripts available |
| DR | Cross-region replication (RPO=5s, RTO=5m) |
| WAF | ModSecurity (configured in nginx) |
| IDS | Snort rules + Fail2ban configured |

---

## 10. Business Context

- **Target**: Iraqi medical laboratories (~1200 total)
- **Pricing**: SaaS tiers ($100–$10,000+/mo)
- **Market**: Iraq (48M pop), MENA digital health $23.4B (2025)
- **Competitive position**: Only Arabic-first LIS with national Iraqi health system integration
- **Regulatory**: SNDHS-lite (Iraqi National Health Data System), MoI NID verification, National Health Insurance (Law No.22)
- **Maturity**: Production-ready for core LIMS; National platform domains are schema-only
