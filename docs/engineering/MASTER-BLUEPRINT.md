# GULA Platform — Master Blueprint

**Version:** 2.1.0
**Date:** 2026-07-08
**Classification:** Internal — Engineering

---

## 1. Platform Overview

GULA is a medical laboratory SaaS platform serving Iraqi healthcare providers. It provides laboratory information management (LIMS), patient data management, lab instrument integration, and healthcare compliance for the Iraqi market.

### Core Mission
Provide reliable, secure, and compliant laboratory information management for Iraqi medical laboratories, with national health system integration (SNDHS-lite).

### Core Principles
1. **Stability first** — never break working code to add features
2. **Data integrity above all** — no change may risk patient data loss
3. **Fix before feature** — bugs and security issues take priority
4. **Test then commit** — all changes verified before integration

## 2. System Architecture

### 2.1 High-Level Architecture

```
Internet → host nginx (TLS) → api-gateway (Docker nginx, 127.0.0.1:8080)
  → gula-backend (FastAPI, gunicorn + uvicorn, port 8000)
  → PostgreSQL 16 + Redis 7
```

Backend never exposes public port. All traffic enters through gateway. Additional services (device bridge, edge agent) connect via authenticated API calls.

### 2.2 Component Map

| Component | Technology | Purpose | Status |
|-----------|------------|---------|--------|
| API Gateway | Docker nginx | TLS termination, routing, rate limiting | Production |
| Backend | FastAPI + gunicorn + uvicorn | Core business logic, REST API | Production |
| Database | PostgreSQL 16 | Primary data store | Production |
| Cache | Redis 7 | Session, rate limiting, caching | Production |
| Frontend | React + Firebase (v2) | Citizen portal, dashboards | Production |
| Client | tRPC + React | Lightweight SPA | Development |
| Legacy Frontend | Static HTML/PWA | Offline-capable fallback | Maintenance |
| Device Bridge | Python (ASTM/HL7) | Lab instrument integration | Production |
| Edge Agent | Python | Offline site computing | Development |
| Monitoring | Prometheus + Grafana | Observability | Opt-in |
| Load Balancer | HAProxy | Horizontal scaling | Opt-in |

### 2.3 Layered Architecture

```
┌─────────────────────────────────────────────────┐
│                   API Gateway                     │
├─────────────────────────────────────────────────┤
│              Middleware Stack                      │
│  MaxBody → RequestID → DocsAuth → CORS → Timing  │
│  → SecurityHeaders → GZip → Readiness → Degraded │
│  → ConcurrencyLimit                                │
├─────────────────────────────────────────────────┤
│                    Routes                          │
│  auth, labs, orders, results, samples, patients,  │
│  stats, ai, compliance, patient_card, edge, ...   │
├─────────────────────────────────────────────────┤
│                   Services                         │
│  outbox_service, mpi/, integration/, ...           │
├─────────────────────────────────────────────────┤
│                    Models                          │
│  17 SQLAlchemy ORM models                          │
├─────────────────────────────────────────────────┤
│                 Core Infrastructure                │
│  self_healing, auto_repair, startup_guard,         │
│  feature_flags, logging_config, ...                │
├─────────────────────────────────────────────────┤
│              Database + Cache                      │
│  PostgreSQL 16 + Redis 7                           │
└─────────────────────────────────────────────────┘
```

## 3. Data Architecture

### 3.1 Core Entities

- **Lab** — Medical laboratory tenant (multi-tenant isolation via `lab_id`)
- **LabUser** — Platform user with RBAC role
- **Patient** — Patient record with optional national ID (SNDHS)
- **LabOrder** — Test order with state machine
- **LabResult** — Test result with optimistic locking
- **Sample** — Physical specimen tracking
- **Visit** — Clinical episode (SNDHS Phase 1)

### 3.2 Data Flow

```
Device → Device Bridge → API → Result Service → DB → Audit Log
Patient → Registration → MPI → Patient Service → DB
Order → Creation → State Machine → Result → Report
```

### 3.3 Security Layers

- All patient data queries filtered by `lab_id`
- All mutations logged to immutable audit hash chain
- Encryption at rest for sensitive fields (national_id)
- JWT authentication with refresh token rotation
- Rate limiting per user per endpoint

## 4. Integration Architecture

### 4.1 Lab Instrument Integration (Device Bridge)

```
Lab Instrument (ASTM/HL7) → Device Bridge → gula_client → Backend API
```

Device bridge runs as separate container. Supports Sysmex, Roche, Mindray, and generic ASTM/HL7 devices. Normalises results and forwards via authenticated HTTP.

### 4.2 Government Integration (SNDHS-lite)

- Phase 1: National ID, health ID, visits, enhanced audit
- Phase 2+: Full health data exchange (future)
- Feature flags control rollout per deployment

## 5. Deployment Architecture

### 5.1 Production Stack (Docker Compose)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  api-gateway  │────▶│ gula-backend │────▶│  postgres:16  │
│  (nginx)      │     │ (FastAPI)    │     │               │
└──────────────┘     └──────────────┘     └──────────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   redis:7    │     │   volumes    │
                    └──────────────┘     └──────────────┘
```

### 5.2 Scaling

Horizontal scaling via `docker compose --scale gula-backend=N` with HAProxy load balancer. Database connection pool must be re-budgeted when scaling.

### 5.3 CI/CD

GitHub Actions pipeline with 6 jobs: syntax-gate → migration-check → smoke-test → backend-test → security-scan → build-and-push. Blue-green deployment for zero-downtime updates.

## 6. Quality Gates

| Gate | Focus | Status |
|------|-------|--------|
| A — Backend Foundation | Ruff lint/format, py_compile, tests pass | PASS |
| B — Security Hardening | Bandit, security tests | PASS |
| C — Testing Hardening | Coverage, test health | PASS |
| D — Production Readiness | Full certification | PASS |

## 7. Future Roadmap

### Phase A (Complete)
- Schema-only Financial Engine
- SNDHS-lite Phase 1 integration
- Patient card system
- Skill platform

### Phase B (In Progress)
- Financial Engine routes and services
- SNDHS-lite Phase 2 (health data exchange)
- Enhanced reporting and analytics
- AI clinical intelligence expansion

### Phase C (Planned)
- Microservices decomposition
- Multi-region deployment
- Full regulatory compliance certification
- Advanced edge computing

## 8. Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test coverage | 54% | 70% |
| Test pass rate | 82% | 98%+ |
| Ruff lint errors | 0 | 0 |
| Bandit High findings | 0 | 0 |
| mypy errors | 1413 | 0 |
| Response time p95 | TBD | <500ms |
| Uptime | TBD | 99.9% |

## References

- `CLAUDE.md` — Engineering Constitution
- `QUALITY.md` — Quality gate matrix
- `docs/adr/` — Architecture Decision Records
- `docs/engineering/` — Engineering assessment documents
- `Makefile` — Build and development commands
