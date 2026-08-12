# GULA Platform — Master Dependency Map

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Module Dependency Structure](#1-module-dependency-structure)
2. [External Dependencies](#2-external-dependencies)
3. [Dependency Direction](#3-dependency-direction)
4. [Shared Kernel](#4-shared-kernel)
5. [Circular Dependency Analysis](#5-circular-dependency-analysis)
6. [Dependency Health Scores](#6-dependency-health-scores)
7. [Replaceability Index](#7-replaceability-index)

---

## 1. Module Dependency Structure

### 1.1 Kernel Layer (Foundation — Zero Dependencies on Business)

| Module | Location | Depends On | Depended By |
|--------|----------|------------|-------------|
| Kernel Core | `backend/app/kernel/` | shared/* | ALL business modules |
| Kernel Module | `backend/app/kernel/module/` | kernel.types, kernel.config | kernel |
| Kernel Plugin | `backend/app/kernel/plugin/` | kernel.module, kernel.types | kernel.routes |
| Kernel Event Bus | `backend/app/kernel/event_bus/` | kernel.types | All modules |
| Kernel Features | `backend/app/kernel/features/` | kernel.types | All modules |
| Kernel Tenant | `backend/app/kernel/tenant/` | kernel.types | All modules |
| Kernel Background | `backend/app/kernel/background/` | kernel.types | kernel.routes |
| Kernel Gateway | `backend/app/kernel/gateway/` | kernel.types | kernel |
| Kernel Runtime | `backend/app/kernel/runtime/` | kernel.types | main.py |

### 1.2 Shared Kernel (Cross-Cutting — No Internal Dependencies)

| Module | Location | Depends On |
|--------|----------|------------|
| Shared Core | `shared/__init__.py` | — |
| Shared Auth | `shared/auth/` | shared.security |
| Shared Models | `shared/models/` | sqlalchemy |
| Shared RBAC | `shared/rbac/` | — |
| Shared Events | `shared/events/` | — |
| Shared Logging | `shared/logging/` | python-json-logger |
| Shared Security | `shared/security/` | cryptography |
| Shared AI | `shared/ai/` | httpx |
| Shared Cache | `shared/cache/` | redis |
| Shared DI | `shared/di_container/` | — |
| Shared Config | `shared/config/` | python-dotenv |
| Shared Observability | `shared/observability/` | opentelemetry |
| Shared Domain | `shared/domain/` | — |
| Shared Circuit Breaker | `shared/circuit_breaker.py` | — |
| Shared Scheduler | `shared/scheduler.py` | — |
| Shared Messaging | `shared/messaging.py` | — |
| Shared PDF | `shared/pdf/` | reportlab |
| Shared Design System | `shared/design_system/` | — |
| Shared Architecture | `shared/architecture/` | — |

### 1.3 Core Infrastructure Layer

| Module | Location | Depends On |
|--------|----------|------------|
| Config | `backend/app/config.py` | shared.config, os |
| Database | `backend/app/database.py` | config, sqlalchemy |
| Main | `backend/app/main.py` | ALL modules (router registration) |
| Self-Healing | `backend/app/core/self_healing.py` | database, shared.circuit_breaker |
| Auto-Repair | `backend/app/core/auto_repair.py` | database, self_healing |
| Feature Flags | `backend/app/core/feature_flags.py` | database, models.subscription |
| Idempotency | `backend/app/core/idempotency.py` | database |
| Resilience | `backend/app/core/resilience.py` | — |
| Cache Manager | `backend/app/core/cache_manager.py` | shared.cache |
| Logging Config | `backend/app/core/logging_config.py` | shared.logging |
| Startup Guard | `backend/app/core/startup_guard.py` | database, config |

### 1.4 Security Layer

| Module | Location | Depends On |
|--------|----------|------------|
| Auth | `backend/app/security/auth.py` | shared.auth, config, redis_client |
| RBAC | `backend/app/security/rbac.py` | shared.rbac |
| ABAC | `backend/app/security/abac.py` | — |
| Encryption | `backend/app/security/encryption.py` | shared.security |
| Rate Limit | `backend/app/security/rate_limit.py` | redis_client |
| Session | `backend/app/security/session.py` | redis_client |
| Redis Client | `backend/app/security/redis_client.py` | redis, config |
| Dependencies | `backend/app/security/dependencies.py` | auth, database |
| JWT Guard | `backend/app/security/jwt_guard.py` | auth, database |
| Intrusion | `backend/app/security/intrusion_detection.py` | — |

### 1.5 Domain Modules

| Module | Location | Depends On |
|--------|----------|------------|
| LIMS | `backend/app/lims/` | kernel, shared.* |
| National | `backend/app/national/` | kernel, shared.*, national.domain |
| Clinical | `backend/app/clinical/` | kernel, shared.* |
| EHR | `backend/app/ehr/` | kernel, shared.* |
| Edge | `backend/app/edge/` | kernel, shared.* |
| Financial | `backend/app/financial/` | kernel (Phase A: schema only) |
| Integration | `backend/app/integration/` | kernel, shared.* |
| Interoperability | `backend/app/interoperability/` | kernel, shared.* |
| Notifications | `backend/app/notifications/` | shared.notifications, gateways |

### 1.6 Service Layer

| Module | Location | Depends On |
|--------|----------|------------|
| MPI | `backend/app/services/mpi/` | kernel, database, models |
| Outbox | `backend/app/services/outbox_service.py` | kernel.event_bus, models.outbox |
| Orders | `backend/app/services/order_service.py` | database, models, domain.order_state |
| Patients | `backend/app/services/patient_service.py` | database, models |
| Clinical Engine | `backend/app/services/clinical_engine.py` | clinical.*, models |
| Interpretation | `backend/app/services/interpretation.py` | shared.ai |
| Ali Reza Engine | `backend/app/services/ali_reza_engine.py` | shared.ai |
| SAMIR Engine | `backend/app/services/samir_engine.py` | shared.ai |
| Audit | `backend/app/services/audit_service.py` | models.audit_log |
| Patient Card | `backend/app/services/patient_card.py` | models, security.encryption |
| Identity | `backend/app/services/identity_service.py` | models, mpi |
| EHR Service | `backend/app/services/ehr_service.py` | ehr.* |
| Hospital Service | `backend/app/services/hospital_service.py` | models |

### 1.7 API Routes Layer

| Route Module | Location | Depends On |
|--------------|----------|------------|
| Labs | `backend/app/routes/labs.py` | models, security.dependencies |
| Patients | `backend/app/routes/patients.py` | services.patient_service |
| Orders | `backend/app/routes/clinical_orders.py` | services.order_service |
| Results | `backend/app/routes/results.py` | services, domain.order_state |
| Samples | `backend/app/routes/samples.py` | services |
| AI | `backend/app/routes/ai.py` | services, ai.* |
| Stats | `backend/app/routes/stats.py` | services |
| Edge | `backend/app/routes/edge.py` | edge.* |
| National | `backend/app/routes/national_data.py` | national.* |
| FHIR | `backend/app/routes/ehr_fhir.py` | national.fhir |
| Identity | `backend/app/routes/identity.py` | services.mpi |
| Patient Card | `backend/app/routes/patient_card.py` | services.patient_card |
| Labs | `backend/app/routes/labs.py` | models, security |
| Login | `backend/app/routes/login.py` | security.auth |
| Mobile | `backend/app/routes/mobile.py` | kernel, services |
| Admin | `backend/app/routes/admin.py` | security, kernel |
| Metrics | `backend/app/routes/metrics.py` | prometheus_client |

### 1.8 Gateway Layer

| Module | Location | Depends On |
|--------|----------|------------|
| Base Gateway | `backend/app/gateways/base.py` | httpx, shared.circuit_breaker |
| NID Gateway | `backend/app/gateways/national_identity_gateway.py` | base |
| Insurance Gateway | `backend/app/gateways/insurance_gateway.py` | base |
| Residency Gateway | `backend/app/gateways/residency_gateway.py` | base |
| Cloudflare Gateway | `backend/app/gateways/cloudflare_gateway.py` | base |
| Device Gateway | `backend/app/gateways/lab_device_gateway.py` | base |
| Google AI | `backend/app/gateways/google_ai.py` | base |

---

## 2. External Dependencies

### 2.1 Python Packages (Production)

| Package | Version | Purpose | License | Health |
|---------|---------|---------|---------|--------|
| fastapi | ≥ 0.110 | Web framework | MIT | 🟢 Active |
| uvicorn[standard] | ≥ 0.27 | ASGI server | BSD | 🟢 Active |
| gunicorn | ≥ 22.0 | WSGI server | MIT | 🟢 Active |
| sqlalchemy | ≥ 2.0 | ORM | MIT | 🟢 Active |
| psycopg2-binary | ≥ 2.9 | PostgreSQL adapter | LGPL | 🟢 Active |
| alembic | ≥ 1.13 | Migrations | MIT | 🟢 Active |
| redis | ≥ 5.0 | Redis client | MIT | 🟢 Active |
| pydantic | ≥ 2.5 | Validation | MIT | 🟢 Active |
| python-jose[cryptography] | ≥ 3.3 | JWT | MIT | 🟢 Active |
| passlib[bcrypt] | ≥ 1.7 | Password hashing | BSD | 🟢 Maintenance |
| httpx | ≥ 0.27 | HTTP client | BSD | 🟢 Active |
| prometheus-client | ≥ 0.19 | Metrics | Apache 2.0 | 🟢 Active |
| opentelemetry-* | ≥ 1.22 | Tracing | Apache 2.0 | 🟢 Active |
| sentry-sdk | ≥ 1.40 | Error tracking | MIT | 🟢 Active |
| python-multipart | ≥ 0.0.6 | File upload | Apache 2.0 | 🟢 Active |
| reportlab | ≥ 4.0 | PDF generation | BSD | 🟢 Active |
| pydantic-settings | ≥ 2.1 | Settings mgmt | MIT | 🟢 Active |

### 2.2 Infrastructure Services

| Service | Provider | Purpose | SLA |
|---------|----------|---------|-----|
| PostgreSQL 16 | Self-hosted / Supabase / Render | Primary database | 99.95% |
| Redis 7 | Self-hosted / Upstash / Render | Cache, session, rate limit | 99.95% |
| Cloudflare | Cloudflare | DNS, WAF, CDN, Workers | 100% (SLA) |
| Render | Render | Application hosting | 99.95% |
| DigitalOcean | DigitalOcean | Droplet hosting | 99.99% |
| Supabase | Supabase | Managed PostgreSQL | 99.95% |

### 2.3 External APIs

| API | Purpose | Dependency Health | Replaceability |
|-----|---------|-------------------|----------------|
| البطاقة الوطنية (NID) | National ID verification | Government (stable) | Medium (adapter pattern) |
| الضمان الصحي (Insurance) | Health insurance eligibility | Government (stable) | Medium (adapter pattern) |
| Google AI (Gemini) | AI clinical interpretation | Vendor (stable) | Low (vendor-specific) |
| Telegram API | Notifications | Vendor (stable) | High (multiple channels) |
| Cloudflare API | DNS, Workers, R2 | Vendor (stable) | Medium (adapter pattern) |

---

## 3. Dependency Direction

### 3.1 Layered Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    API ROUTES LAYER                          │
│  routes/* — depends on: services, security, kernel           │
├──────────────────────────────────────────────────────────────┤
│                     SERVICE LAYER                            │
│  services/* — depends on: models, domain, kernel, shared     │
├──────────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                             │
│  lims/, national/, clinical/, ehr/ — depends on: kernel      │
├──────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                       │
│  core/, security/, gateways/ — depends on: shared, kernel    │
├──────────────────────────────────────────────────────────────┤
│               PLATFORM / KERNEL LAYER                        │
│  kernel/ — depends on: shared/* (NEVER on business modules)  │
├──────────────────────────────────────────────────────────────┤
│                    SHARED LAYER                               │
│  shared/ — depends on: external libs only, framework-indep   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Strict Rules

1. **Kernel** → depends on `shared/*` only (never business modules)
2. **Business modules** → depend on `kernel/*` and `shared/*` only (not each other)
3. **Shared** → depends on external libraries and Python stdlib only
4. **Routes** → depend on services, security, kernel
5. **Services** → depend on models, domain, kernel, shared
6. **No cross-business-module dependencies** allowed

---

## 4. Shared Kernel

### 4.1 What Every Module Depends On

The following are depended upon by all (or most) business modules:

| Module | Used By | Reason |
|--------|---------|--------|
| `shared.models.base` | All ORM models | Base mixins (Timestamp, SoftDelete, Tenant, Audit) |
| `shared.rbac.permissions` | All security checks | Role and permission definitions |
| `shared.events.constants` | Event publishers/consumers | Event type constants |
| `shared.auth` | Authentication | JWT, password hashing |
| `shared.security.encryption` | PII handling | Encryption utilities |
| `shared.logging` | All modules | Structured logging |
| `shared.circuit_breaker` | External gateway calls | Resilience pattern |
| `shared.cache.backends` | Caching | Cache abstraction |
| `backend/app/kernel/types` | Module definitions | Core type definitions |
| `backend/app/config.py` | All modules | Configuration |
| `backend/app/database.py` | All DB operations | Engine, session, context |

---

## 5. Circular Dependency Analysis

### 5.1 Current Status

No circular dependencies detected in the architecture (verified by module dependency graph analysis). The layered architecture and strict dependency direction rules prevent cycles.

### 5.2 Potential Risk Areas

| Area | Risk | Mitigation |
|------|------|-------------|
| Event bus ↔ Service | Service publishes → Event bus dispatches → Handler calls service | Event handlers call services, services publish events → no cycle |
| Feature flags ↔ Subscription | Feature flags read subscription → Subscription model | One-way: Feature flag reads Subscription, not vice versa |
| Auth ↔ User model | Auth reads user → User model | One-way: Auth dependency on User model, clean separation |

### 5.3 Monitoring

```
make ci  → includes import-walk validation to detect any introduced cycles
shared/architecture/validator.py → automated cycle detection
```

---

## 6. Dependency Health Scores

### 6.1 Scoring Criteria

| Factor | Weight | Measurement |
|--------|--------|-------------|
| Freshness | 30% | Last release < 1 year |
| Maintenance | 25% | Regular commits, responsive maintainers |
| Security | 25% | No critical CVEs |
| Popularity | 10% | GitHub stars, PyPI downloads |
| License | 10% | Compatible with project license |

### 6.2 Current Scores

| Package | Freshness | Maintenance | Security | Popularity | License | Overall |
|---------|-----------|-------------|----------|------------|---------|---------|
| fastapi | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 95% |
| sqlalchemy | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 95% |
| pydantic | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 95% |
| httpx | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 90% |
| passlib | 🟡 (maintenance) | 🟡 | 🟢 | 🟢 | 🟢 | 75% |
| psycopg2-binary | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 95% |
| reportlab | 🟢 | 🟡 | 🟢 | 🟢 | 🟢 | 85% |

---

## 7. Replaceability Index

### 7.1 Scoring Criteria

| Rating | Meaning | Effort |
|--------|---------|--------|
| 🟢 High | Easily swappable (adapter pattern) | Days |
| 🟡 Medium | Moderate effort (interface extraction) | Weeks |
| 🔴 Low | Deeply integrated | Months |

### 7.2 Replaceability by Module

| Dependency | Replaceability | Adapter | Alternative |
|------------|---------------|---------|-------------|
| PostgreSQL | 🟡 Medium | SQLAlchemy ORM | MySQL, CockroachDB |
| Redis | 🟡 Medium | `shared/cache/backends.py` | Memcached, Dragonfly |
| passlib | 🟢 High | `shared/auth/passwords.py` | argon2-cffi |
| reportlab | 🟡 Medium | `shared/pdf/` | WeasyPrint, pdfkit |
| prometheus | 🟢 High | `shared/metrics/` | OpenTelemetry metrics |
| sentry-sdk | 🟢 High | `backend/app/main.py:48-71` | Rollbar, Datadog |
| Cloudflare | 🟡 Medium | `backend/app/gateways/cloudflare_gateway.py` | AWS CloudFront, Fastly |
| Render | 🟡 Medium | PaaS abstraction | DigitalOcean App, Railway |
| NID Gateway | 🟡 Medium | `backend/app/gateways/base.py` | Alternative gov ID system |
| AI Provider | 🟡 Medium | `shared/ai/provider.py` | OpenAI, Anthropic, local |

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial master dependency map |

**Review Cycle**: This document must be updated with every significant dependency change.
