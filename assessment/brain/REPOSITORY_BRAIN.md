# GULA Platform — Repository Brain v2.1.0

> Generated: 2026-07-14
> Mission: 4.1A — Repository Brain

---

## 1. Repository Overview

| Attribute | Value |
|-----------|-------|
| Name | gula-platform |
| Version | 2.1.0 |
| Type | Monorepo (3 consolidated repos) |
| License | Proprietary |
| Python | >=3.11 |
| Primary Stack | FastAPI + PostgreSQL 16 + Redis 7 |
| Total Deployable Units | 10+ (backend, 8 microservices, nhop-platform, edge_agent, 2 frontends) |
| Total Modules | 53 shared + 36 route + 17 model + 24 service + 15 core + 10 security |
| Total Tests | 119 Python + 5 non-Python = 124 |
| Total Migrations | 27 |
| Total Tables | ~46 |
| Git Branches | ~50 (1 local, ~50 remote) |

---

## 2. Repository Knowledge Graph

### 2.1 Directory Structure
```
gula-platform/
├── backend/          # Production monolith (FastAPI + 36 route modules)
├── frontend-v2/      # Rich React + Firebase UI (formerly Front-end-)
├── frontend/         # Static HTML PWA (legacy)
├── client/           # tRPC + React SPA
├── server/           # Express + tRPC backend
├── services/         # 9 microservice stubs + device_bridge
├── nhop-platform/    # National Health Oversight Platform
├── edge_agent/       # Edge computing agent for remote labs
├── ai/               # Clinical AI modules
├── shared/           # Shared Engineering Library (53 modules)
├── docs/             # Documentation (ADRs, SNDHS, architecture)
├── architecture/     # Architecture Decision Records
├── assessment/       # Audit/assessment reports
├── scripts/          # 51 operational scripts
├── tests/            # Cross-project tests (chaos, load, integrity)
├── config/           # Infrastructure config (Prometheus, Grafana, HAProxy, etc.)
├── k8s/              # Kubernetes manifests
├── cloudflare/       # Cloudflare config
├── digitalocean/     # DigitalOcean App Platform
├── supabase/         # Supabase integration
│── docker/           # Auxiliary Docker files
├── data/             # Database data
├── logs/             # Runtime logs
├── sample_tracking/  # Lab sample tracking
├── test_library/     # Test library demo
├── archive/          # Legacy code
├── database/         # Raw SQL schemas
└── k6/               # K6 load testing
```

### 2.2 Architecture Layers
```
Internet → nginx (TLS) → api-gateway (Docker nginx) → gula-backend (FastAPI)
                                                         ├── Middleware (11 layers)
                                                         ├── Routes (36 modules, ~202 endpoints)
                                                         ├── Services (24 modules)
                                                         ├── Models (17 ORM, 29 classes)
                                                         ├── Core (15 modules: self-healing, etc.)
                                                         ├── Security (10 modules)
                                                         ├── Domain (state machines)
                                                         ├── Kernel (DI, event bus, plugins)
                                                         └── Tasks (outbox pattern)
                                                         └── PostgreSQL 16 + Redis 7
```

### 2.3 Component Tree
```
gula-backend (FastAPI monolith)
├── Middleware Stack
│   ├── 1. MaxBodySizeMiddleware
│   ├── 2. RequestIDMiddleware
│   ├── 3. DocsAuthMiddleware (production)
│   ├── 4. CORSMiddleware
│   ├── 5. RequestTimingMiddleware
│   ├── 6. SecurityHeadersMiddleware
│   ├── 7. GZipMiddleware
│   ├── 8. ReadinessMiddleware
│   ├── 9. DegradedModeMiddleware
│   ├── 10. KernelMiddleware
│   └── 11. ConcurrencyLimitMiddleware
├── Security Layer
│   ├── JWT (dual-secret: access + refresh)
│   ├── RBAC (9 roles × 16 permissions)
│   ├── ABAC (tenant isolation via lab_id)
│   ├── Consent-based access
│   ├── Rate limiting (Redis-backed)
│   ├── Encryption (Fernet + HMAC)
│   └── Session invalidation (perm_version)
├── Self-Healing Layer
│   ├── Circuit Breaker (DB + Redis)
│   ├── Auto-Repair Engine (GC, pool recycle)
│   └── Adaptive Concurrency
├── Domain Logic
│   ├── Order State Machine (5 states)
│   ├── Clinical Interpretation Engine
│   ├── Westgard QC Rules
│   └── MPI Patient Matching
├── Background Systems
│   ├── Outbox Pattern (at-least-once delivery)
│   ├── Scheduler + Cron
│   ├── Task Queue + Worker Pool
│   └── Health Alert Watchdog
└── Monitoring
    ├── /health endpoints (5 paths)
    ├── Prometheus metrics
    ├── Sentry error tracking
    └── Structured JSON logging
```

### 2.4 AI Component Map
```
ai/ (top-level)
├── ai_agent.py
├── ai_service.py
├── ali_reza_engine.py
├── anomaly_detection.py
├── clinical/
├── lab_brain.py
├── lab_business_ai/
├── outbreak/
├── performance_analysis.py
├── population_health.py
├── population/
├── preventive_engine.py
└── preventive/

backend/app/ai/
├── guardrails.py
├── optimizer.py
├── sandbox.py
└── system_optimizer.py

backend/app/routes/ai.py
backend/app/routes/ai_telemetry.py
```

---

## 3. Architecture Score

| Dimension | Score | Details |
|-----------|-------|---------|
| Architecture Documentation | 65/100 | Good ADR process; 7 empty stubs in architecture/ |
| DDD Compliance | 35/100 | State machine exists; no aggregates, VOs, domain events |
| Clean Architecture | 30/100 | 32/35 routes violate layer boundaries |
| CQRS Implementation | 20/100 | Tooling exists; zero production CQRS |
| Plugin Architecture | 50/100 | Well-designed subsystem; no real plugins |
| Modularity | 55/100 | Clear structure; 7 empty directories |
| Dependency Injection | 40/100 | DI container exists; zero usage in business code |
| Layer Separation | 45/100 | Excellent middleware; poor route/service separation |
| **Overall Architecture** | **42.5/100** | Strong intent/awareness; weak execution |

## 4. Maintainability Score

| Metric | Score | Details |
|--------|-------|---------|
| Code Organization | 70/100 | Well-structured directories; consistent naming |
| Documentation Coverage | 55/100 | Good ADRs; many empty architecture stubs |
| Test Coverage (estimate) | 50/100 | 119 test files; no coverage enforcement |
| Dead Code | 40/100 | Unused imports (44), dead intrusion_detection, legacy jwt_guard |
| Duplicate Code | 60/100 | Some config duplication across files |
| **Overall Maintainability** | **55/100** | |

## 5. Security Score

| Area | Score | Details |
|------|-------|---------|
| Authentication | 75/100 | JWT dual-secret, bcrypt, blacklist; no MFA |
| Authorization | 70/100 | RBAC (9 roles × 16 perms), ABAC; some gaps |
| Encryption | 70/100 | Fernet + HMAC for NID; no key rotation |
| Input Validation | 60/100 | Pydantic schemas; some missing validation |
| Rate Limiting | 55/100 | Redis-backed; per-worker gaps; opt-in per route |
| CSP/Headers | 50/100 | 'unsafe-inline' weakens CSP |
| Audit Trail | 80/100 | Hash-chained audit logs; immutability trigger |
| Secrets Management | 65/100 | Weak-pattern detection; no vault integration |
| **Overall Security** | **65/100** | Strong foundation; several hardening opportunities |

## 6. Technical Debt Score

| Category | Items | Estimated Effort |
|----------|-------|------------------|
| Unused Imports | 44 in main.py and kernel/__init__.py | 1 hour |
| Dead Code | intrusion_detection.py (unused), jwt_guard.py (redundant) | 1 hour |
| Empty Stub Directories | 7 (approvals/, constraints/, policies/, etc.) | 2 hours |
| Unpinned Dependencies | 8 Dockerfiles with no version constraints | 2 hours |
| Architecture Violations | 32 routes bypassing service layer | 40 hours |
| Missing Tests | Frontend, property-based, fuzz, E2E | 80 hours |
| Version Conflicts | Python (bcrypt, cryptography), JS (react, tailwind) | 4 hours |
| **Total Technical Debt** | **~180 hours** | |

## 7. Coupling Score

| Metric | Score | Details |
|--------|-------|---------|
| Route-to-Service Coupling | 30/100 | 32 of 35 routes bypass services |
| Model Dependency | 45/100 | Imported in routes directly |
| Cross-Project Coupling | 60/100 | Shared library helps decouple |
| **Overall Coupling** | **45/100** | Too tight; needs service layer enforcement |

## 8. Cohesion Score

| Metric | Score | Details |
|--------|-------|---------|
| Route Cohesion | 75/100 | Well-organized by resource |
| Service Cohesion | 65/100 | Some cross-cutting concerns |
| Model Cohesion | 80/100 | Clear table-per-file pattern |
| **Overall Cohesion** | **73/100** | Good; consistent |

## 9. Dependencies

### Python (across all sub-projects)
| File | Deps | Pinned |
|------|------|--------|
| backend/requirements.txt | 23 | 1 upper-bound |
| backend/requirements-dev.txt | 2 | 1 upper-bound |
| shared/pyproject.toml | 28 | 0 |
| nhop-platform/requirements.txt | 11 | 10 exact |
| edge_agent/requirements.txt | 4 | 0 |
| services/device_bridge/ | 5 | 0 |
| 8 microservice Dockerfiles | 54 | 0 (fully unpinned) |
| **Total** | **~127** | **2 pinned** |

### JavaScript/TypeScript
| File | Deps | DevDeps | Issues |
|------|------|---------|--------|
| package.json (root) | 30 | 31 | @types/react-router-dom mismatch, shadcn-ui risk, uncommitted lockfile |
| frontend-v2/package.json | 29 | 7 | vite duplicated, autoprefixer unneeded |

---

## 10. API Graph (~202 Endpoints)

| Router | File | Endpoints | Docstrings |
|--------|------|-----------|------------|
| /health | main.py | 5 | ✅ |
| /test-types | main.py | 1 | ✅ |
| /auth | main.py | 1 | ✅ |
| /login | routes/login.py | 2 | ✅ |
| /register | routes/register.py | 2 | ✅ |
| /patients | routes/patients.py | 4 | Partial (3 missing) |
| /orders | routes/orders.py | 3 | Partial (2 missing) |
| /results | routes/results.py | 4 | ✅ |
| /samples | routes/samples.py | 4 | ✅ |
| /labs | routes/labs.py | 3 | Partial (1 missing) |
| /dashboard | routes/dashboard.py | 1 | ❌ missing |
| /stats | routes/stats.py | 3 | ✅ |
| /ai | routes/ai.py | 4 | ✅ |
| /compliance | routes/compliance.py | 2 | ✅ |
| /citizen-portal | routes/citizen_portal.py | 6 | ✅ |
| /patient-card | routes/patient_card.py | 4 | ✅ |
| /edge | routes/edge.py | 22 | ❌ module-level only |
| /kernel | routes/kernel/routes.py | 11 | ❌ missing |
| /security | routes/security.py | 1 | ✅ |
| + 15 more | | ~120 | Mixed |

---

## 11. Database Graph (~46 Tables)

| Category | Tables | ORM Model |
|----------|--------|-----------|
| Core LIMS | 15 (labs, patients, lab_orders, lab_results, etc.) | ✅ 16 models |
| Subscriptions | 4 (lab_subscriptions, upgrade_requests, etc.) | ✅ subscription.py |
| Audit | 2 (audit_logs, sndhs_audit_logs) | ✅ audit_log.py |
| Outbox | 1 (outbox_events) | ✅ outbox.py |
| Quality Control | 1 (quality_controls) | ✅ quality_control.py |
| Edge Platform | 7 (edge_devices, edge_tasks, etc.) | ✅ edge.py |
| AI Dataset | 5 (ai_interactions, ai_feedback, etc.) | ✅ ai_interaction.py |
| MPI | 3 (citizens, identity_claims, mpi_merge_audit) | 📍 services/mpi/models.py |
| Financial | 9 (fin_providers, fin_transactions, etc.) | ❌ No ORM models |
| SNDHS | 2 (visits, sndhs_audit_logs) | ❌ No ORM models |
| Claims | 2 (claims, claim_items) | ✅ claim.py |
| Consent | 1 (consents) | ✅ consent.py |
| Idempotency | 1 (idempotency_keys) | ❌ No ORM model |

---

## 12. Workflow Graph

```
Lab Order Lifecycle:
  pending → completed → validated (immutable)
  pending → cancelled

Sample Lifecycle:
  collected → received → processing → analyzed (→ rejected)

Result Flag States:
  normal | high | low | critical

Quality Control (Westgard):
  pass → warning → fail (1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10-x)

Outbox Event States:
  pending → processing → done | failed (retry max 5)

Consent States:
  active → revoked | expired

Edge Task States:
  queued → assigned → running → completed | failed
```

---

## 13. Service Graph

| Service | Status | Dependencies |
|---------|--------|--------------|
| gula-backend | ✅ Production | postgres, redis |
| device_bridge | ✅ MVP | gula-backend (via HTTP) |
| nhop-platform | ✅ Active | postgres, redis |
| edge_agent | ✅ Active | gula-backend (via HTTP) |
| services/lab | 📍 Stub | postgres, rabbitmq |
| services/order | 📍 Stub | postgres, rabbitmq |
| services/patient | 📍 Stub | postgres, rabbitmq |
| services/result | 📍 Stub | postgres, rabbitmq, minio, kafka |
| services/sample | 📍 Stub | postgres, rabbitmq |
| services/notification | 📍 Stub | rabbitmq |
| services/ai | 📍 Stub | rabbitmq |
| services/autonomous_manager | 📍 Stub | rabbitmq |

---

## 14. Test Coverage Assessment

| Area | Test Files | Quality |
|------|-----------|---------|
| Unit/Integration | 91 (backend) | ✅ Strong |
| Device Bridge | 12 | 📍 Moderate |
| Security | 5 | ✅ Strong |
| Chaos/Resilience | 10 | ✅ Strong |
| Clinical Safety | 8 | ✅ Strong |
| Kernel | 31 | ✅ Strong |
| Load/Performance | 5 | 📍 Moderate |
| Frontend | 0 | ❌ Missing |
| E2E/Browser | 0 | ❌ Missing |
| Property-based | 0 | ❌ Missing (empty stub) |
| Fuzzing | 0 | ❌ Missing |
| Mutation | 0 | ❌ Missing |

---

## 15. Issues Detected

### Dead Code
- `backend/app/security/intrusion_detection.py` — never imported
- `backend/app/security/jwt_guard.py` — redundant (simpler than dependencies.py)
- 44 unused imports in main.py and kernel/__init__.py

### Duplicate Code
- Config validation in both config.py and startup_guard.py
- Version constraints for same package differ across sub-projects

### Unused Packages
- autoprefixer in frontend-v2/ (Tailwind v4 uses Lightning CSS)
- Several JS types packages (@types/uuid duplicated)

### Architecture Violations
- 32/35 routes access ORM directly instead of going through service layer
- 7 empty stub directories (approvals/, constraints/, policies/, etc.)

### Security Hotspots
- CSP allows 'unsafe-inline' scripts
- No key rotation mechanism
- REFRESH_TOKEN_SECRET strength not validated
- Intrusion detector is dead code (never wired)

### Performance Hotspots
- Fixed-window rate limiting (burst at boundaries)
- No connection pooling for per-worker rate limiting
- In-memory Redis fallback breaks cross-worker consistency

### Database Hotspots
- Missing ORM models for financial (9 tables) and SNDHS (2 tables)
- test_results model not wired into metadata (pending migration)

---

## 16. Scoring Summary

| Score | Value | Grade |
|-------|-------|-------|
| Architecture Score | 42.5/100 | 🟡 |
| Maintainability Score | 55/100 | 🟡 |
| Security Score | 65/100 | 🟢 |
| Technical Debt Score | 180 hours | 🟡 |
| Coupling Score | 45/100 | 🟡 |
| Cohesion Score | 73/100 | 🟢 |
| Complexity Score | 50/100 | 🟡 |
| Reuse Score | 60/100 | 🟢 |
| Test Coverage (estimate) | 50% | 🟡 |
| **Overall Platform Score** | **54/100** | 🟡 |

---

## 17. Recommended Next Actions

### Priority 1 (Fix Before Feature)
1. Remove 44 unused imports from main.py and kernel/__init__.py
2. Fix 2 mypy strict errors in config.py
3. Wire intrusion_detection.py into auth flow or remove dead code
4. Fix 8 Ruff findings (context managers, unicode dashes)

### Priority 2 (Dependency Hardening)
5. Pin version constraints in 8 microservice Dockerfiles
6. Fix JS dependency version conflicts across projects
7. Create proper lockfile(s) for root package.json
8. Remove shadcn-ui impersonation dependency risk

### Priority 3 (Architecture)
9. Continue moving route DB queries into service layer
10. Implement ORM models for financial and SNDHS tables
11. Fill empty architecture stub documents
12. Add coverage enforcement to CI pipeline

### Priority 4 (Testing)
13. Add frontend test infrastructure
14. Implement property-based tests
15. Set up mutation testing
16. Add E2E browser tests
