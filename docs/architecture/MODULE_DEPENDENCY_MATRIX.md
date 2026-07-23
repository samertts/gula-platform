# GULA Platform — Module Dependency Matrix

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [Module Architecture Overview](#1-module-architecture-overview)
2. [Module Dependency Matrix](#2-module-dependency-matrix)
3. [Directory Structure](#3-directory-structure)
4. [Circular Dependency Analysis](#4-circular-dependency-analysis)
5. [Coupling Analysis](#5-coupling-analysis)
6. [Module Boundaries](#6-module-boundaries)
7. [Shared Library Dependencies](#7-shared-library-dependencies)
8. [Related Documents](#8-related-documents)

---

## 1. Module Architecture Overview

The backend follows a layered architecture with strict dependency direction:

```
config / _compat        — leaf modules (zero internal deps)
    ↓
database.py             — SQLAlchemy engine, session, connection pool
    ↓
models/                 — ORM entity definitions (inherit Base from database)
core/                   — infrastructure: startup guard, circuit breaker, logging, features, policy
security/               — auth, JWT, RBAC, ABAC, encryption, rate limiting, session
domain/                 — pure domain logic: exceptions, order state machine
    ↓
services/               — business logic layer (use models, database, core, security)
    ↓
routes/                 — HTTP handlers (use services, security, database)
    ↓
factory.py / main.py    — app creation, middleware stack, route registration
```

**Key invariants:**
- Routes never import other routes (no route-to-route imports)
- Services never import routes
- Models never import services
- Core never imports routes or services
- Config is read by every module but depends on nothing internally
- `_compat.py` provides Python version compatibility (UTC, StrEnum); imported across the codebase

**Domain vertical slices** (`lims/`, `ehr/`, `hospital/`, `nursing/`, `pharmacy/`, `radiology/`, `clinical/`, `care_continuum/`, etc.) each contain their own `routes.py`, `services.py`, and `models.py` and follow the same layering.

---

## 2. Module Dependency Matrix

### 2.1 Core Infrastructure Modules

| Module | File(s) | Depends On | Used By | Circular Deps | Coupling |
|--------|---------|-----------|---------|---------------|----------|
| `config.py` | `config.py` | `shared.config.loader` (optional) | **ALL modules** | None | **Tight** — every module reads config globals |
| `_compat.py` | `_compat.py` | `sys`, `datetime`, `enum` (stdlib) | `main.py`, `services/outbox_service.py`, `services/audit_service.py`, `lims/routes.py`, `lims/services.py`, `core/feature_flags.py`, `core/startup.py` | None | Loose |
| `database.py` | `database.py` | `config.py`, `core/self_healing.py`, `core/runtime_guard.py`, `security/redis_client.py` | **ALL modules** (via `get_db`, `Base`, `SessionLocal`) | None | **Tight** — shared engine/session/Base |
| `factory.py` | `factory.py` | `config.py`, `domain/exceptions.py`, `middleware.py`, `core/*`, `kernel/*`, `routes/*`, `financial/*`, `services/mpi/*`, `integration/*`, `lims/*`, `national/*`, `platform/*`, `contracts/*`, `nhdw/*`, `nursing/*`, `pharmacy/*`, `radiology/*`, `simulation/*`, `command_intelligence/*`, `knowledge_graph/*`, `roadmap/*`, `health_data/*`, `control_plane/*`, `citizen_platform/*`, `ai_fabric/*`, `research_platform/*`, `certification/*`, `ems/*`, `document_intelligence/*`, `blood_bank/*`, `critical_care/*`, `biomedical/*`, `public_health/*`, `command_center/*`, `pilot_platform/*`, `lifecycle_platform/*`, `document_intelligence/infrastructure/models/*`, `hospital/models/*`, `lims/models/*`, `national_data/models/*`, `nhdw/models/*`, `nursing/models/*`, `pharmacy/models/*`, `radiology/models/*` | `main.py` | **Potential circular** — factory imports everything; mitigated by lazy imports inside `_register_routes()` and late-binding via `app.include_router()` | **Tight** — central composition root |
| `middleware.py` | `middleware.py` | `config.py`, `core/logging_config.py`, `core/startup_guard.py`, `security/auth.py`, `kernel/integration.py`, `database.py` | `factory.py` (registered via `app.add_middleware`) | None | Medium |
| `main.py` | `main.py` | `factory.py`, `config.py`, `core/logging_config.py`, `core/startup_guard.py`, `database.py`, `core/self_healing.py`, `security/redis_client.py`, `models/outbox.py`, `routes/metrics.py`, `middleware.py`, `kernel/integration.py`, `_compat.py` | Entry point (gunicorn/uvicorn) | None | Loose |

### 2.2 Core Infrastructure Sub-Packages

| Module | Location | Depends On | Used By | Circular Deps | Coupling |
|--------|----------|-----------|---------|---------------|----------|
| `core/` | `core/__init__.py` | `config.py`, `database.py`, `_compat.py`, `shared.logging` | `services/`, `routes/`, `security/`, `factory.py`, `main.py`, `worker.py`, `middleware.py` | None | Medium |
| `core/logging_config.py` | `core/logging_config.py` | `shared.logging` | `main.py`, `factory.py`, `worker.py`, `middleware.py` | None | Loose |
| `core/self_healing.py` | `core/self_healing.py` | `database.py` (lazy) | `main.py`, `database.py`, `middleware.py`, `worker.py` | **Circular detected** — `database.py` imports `core/self_healing.py` for circuit breaker, and `core/self_healing.py` imports `database.py` lazily | **Managed** — lazy imports break cycle |
| `core/startup_guard.py` | `core/startup_guard.py` | `database.py` (lazy), `config.py` | `factory.py`, `main.py`, `middleware.py` | None | Medium |
| `core/startup.py` | `core/startup.py` | `config.py`, `core/self_healing.py`, `database.py`, `_compat.py` | `factory.py`, `worker.py` | None | Medium |
| `core/feature_flags.py` | `core/feature_flags.py` | `_compat.py`, `models/subscription.py` | `routes/`, `services/` | None | Medium |
| `core/auto_repair.py` | `core/auto_repair.py` | `database.py`, `core/self_healing.py` | `worker.py` | None | Medium |
| `core/cache_manager.py` | `core/cache_manager.py` | `config.py`, `security/redis_client.py` | `services/`, `routes/` | None | Loose |
| `core/events.py` | `core/events.py` | (event bus only) | `services/outbox_service.py` | None | Loose |
| `core/sndhs_flags.py` | `core/sndhs_flags.py` | `config.py` | `services/`, `routes/` | None | Loose |
| `core/startup.py` | `core/startup.py` | `config.py`, `database.py`, `core/self_healing.py`, `_compat.py` | `factory.py`, `worker.py` | None | Medium |

### 2.3 Security Sub-Package

| Module | Location | Depends On | Used By | Circular Deps | Coupling |
|--------|----------|-----------|---------|---------------|----------|
| `security/` | `security/*` | `config.py`, `database.py`, `models/*` | `routes/`, `services/`, `middleware.py`, `factory.py` | None | **Tight** — every route uses `get_current_user` |
| `security/auth.py` | `security/auth.py` | `config.py` | `routes/`, `middleware.py`, `services/` | None | Medium |
| `security/dependencies.py` | `security/dependencies.py` | `security/auth.py`, `database.py`, `config.py`, `models/*` | **ALL routes** (via `Depends(get_current_user)`) | None | **Tight** — universal dependency |
| `security/rbac.py` | `security/rbac.py` | (pure permission matrix) | `security/dependencies.py`, `services/authorization_service.py` | None | Loose |
| `security/abac.py` | `security/abac.py` | `models/*` | `security/dependencies.py` | None | Loose |
| `security/encryption.py` | `security/encryption.py` | `config.py` | `services/`, `routes/` | None | Loose |
| `security/rate_limit.py` | `security/rate_limit.py` | `security/redis_client.py`, `config.py` | `middleware.py`, `routes/` | None | Loose |
| `security/redis_client.py` | `security/redis_client.py` | `config.py` | `database.py`, `main.py`, `core/cache_manager.py` | None | Medium |
| `security/session.py` | `security/session.py` | `config.py`, `security/redis_client.py` | `routes/`, `services/` | None | Loose |
| `security/mfa_service.py` | `security/mfa_service.py` | `database.py`, `models/mfa_device.py` | `routes/mfa.py` | None | Loose |
| `security/oauth2_provider.py` | `security/oauth2_provider.py` | `database.py`, `models/*`, `security/auth.py` | `routes/oauth2.py` | None | Medium |
| `security/saml_service.py` | `security/saml_service.py` | `config.py` | `routes/saml.py` | None | Loose |
| `security/service_accounts.py` | `security/service_accounts.py` | `database.py`, `models/service_account.py` | `routes/service_accounts.py` | None | Loose |

### 2.4 Domain Sub-Package

| Module | Location | Depends On | Used By | Circular Deps | Coupling |
|--------|----------|-----------|---------|---------------|----------|
| `domain/exceptions.py` | `domain/exceptions.py` | none | `factory.py`, `services/*`, `routes/*` | None | Loose |
| `domain/order_state.py` | `domain/order_state.py` | (pure state machine) | `lims/services.py`, `lims/state_machine.py` | None | Loose |

### 2.5 ORM Models

| Module | Location | Depends On | Used By | Circular Deps | Coupling |
|--------|----------|-----------|---------|---------------|----------|
| `models/` | `models/*.py` | `database.py` (Base) | `services/`, `routes/`, `core/feature_flags.py`, `financial/*`, `lims/*`, `national/*`, `factory.py` | None | **Tight** — services query models directly |
| `models/__init__.py` | `models/__init__.py` | `database.py`, `models/*.py` | `factory.py` (via `import_all_models()`), other model imports | None | Medium |
| `models/outbox.py` | `models/outbox.py` | `database.py` (Base) | `services/outbox_service.py`, `main.py` | None | Loose |
| `models/subscription.py` | `models/subscription.py` | `database.py` (Base) | `core/feature_flags.py`, `routes/*` | None | Medium |
| `models/ai_interaction.py` | `models/ai_interaction.py` | `database.py` (Base) | `services/clinical_intelligence.py`, `routes/ai.py` | None | Loose |
| `models/edge.py` | `models/edge.py` | `database.py` (Base) | `routes/edge.py`, `services/offline_sync_service.py` | None | Loose |

### 2.6 Business Services

| Module | Location | Depends On | Used By | Circular Deps | Coupling |
|--------|----------|-----------|---------|---------------|----------|
| `services/` | `services/*.py` | `models/`, `database.py`, `core/`, `security/`, `_compat.py` | `routes/`, `financial/`, `lims/`, `ehr/`, `hospital/`, `national/*`, `worker.py` | None | Medium |
| `services/audit_service.py` | `services/audit_service.py` | `models/audit_log.py`, `config.py`, `database.py`, `_compat.py` | **ALL services & routes** (via `log_action()`) | None | **Tight** — every mutation calls it |
| `services/outbox_service.py` | `services/outbox_service.py` | `models/outbox.py`, `core/events.py`, `database.py`, `_compat.py` | `routes/*`, `worker.py`, `lims/services.py`, `financial/services.py` | None | Medium |
| `services/mpi/` | `services/mpi/*.py` | `models/patient.py`, `database.py`, `core/` | `routes/` (via `mpi_router`), `services/patient_service.py` | None | Medium |
| `services/authorization_service.py` | `services/authorization_service.py` | `models/*`, `database.py`, `security/rbac.py` | `routes/authorization.py`, `routes/admin.py` | None | Medium |
| `services/patient_service.py` | `services/patient_service.py` | `models/patient.py`, `database.py`, `services/audit_service.py` | `routes/patients.py` | None | Medium |
| `services/order_service.py` | `services/order_service.py` | `models/*`, `database.py`, `services/audit_service.py` | `routes/labs.py` | None | Medium |
| `services/clinical_intelligence.py` | `services/clinical_intelligence.py` | `models/*`, `database.py`, `gateways/google_ai.py` | `routes/ai.py` | None | Loose |
| `services/policy_engine.py` → `core/policy_engine.py` | `core/policy_engine.py` | `models/*`, `database.py` | `routes/labs.py`, `services/order_service.py` | None | Medium |

### 2.7 Route Modules

| Module | Location | Depends On | Used By | Circular Deps | Coupling |
|--------|----------|-----------|---------|---------------|----------|
| `routes/` (55 modules) | `routes/*.py` | `services/`, `security/dependencies.py`, `database.py`, `models/`, `core/feature_flags.py` | HTTP (registered in `factory.py:_register_routes()`) | None | **Loose** — routes are independent of each other |
| `routes/login.py` | `routes/login.py` | `security/auth.py`, `security/dependencies.py`, `models/*`, `database.py` | — | None | Medium |
| `routes/patients.py` | `routes/patients.py` | `services/patient_service.py`, `security/dependencies.py`, `database.py` | — | None | Medium |
| `routes/labs.py` | `routes/labs.py` | `services/order_service.py`, `security/dependencies.py`, `database.py`, `core/feature_flags.py` | — | None | Medium |
| `routes/metrics.py` | `routes/metrics.py` | `security/dependencies.py` | `main.py` (reads `_START`) | None | Loose |
| `routes/patient_card.py` | `routes/patient_card.py` | `services/patient_card.py`, `security/dependencies.py` | — | None | Loose |
| `routes/ai.py` | `routes/ai.py` | `services/clinical_intelligence.py`, `security/dependencies.py` | — | None | Loose |

### 2.8 Domain Vertical Slices

Each vertical slice follows the pattern: `routes.py` → `services.py` → `models.py` → `database.py`.

| Module | Depends On | Used By | Circular Deps | Coupling |
|--------|-----------|---------|---------------|----------|
| `lims/` | `database.py`, `models/*`, `services/audit_service.py`, `security/dependencies.py`, `_compat.py` | `factory.py` (via `lims/routes.py`) | None | Medium |
| `ehr/` | `database.py`, `models/*`, `services/audit_service.py`, `security/dependencies.py` | `factory.py` (via `ehr/routes.py`) | None | Medium |
| `hospital/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `nursing/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `pharmacy/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `radiology/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `clinical/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `care_continuum/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `nhdw/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `ems/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `blood_bank/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `critical_care/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `biomedical/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |
| `public_health/` | `database.py`, `models/*`, `services/`, `security/dependencies.py` | `factory.py` | None | Medium |

### 2.9 Platform & Infrastructure Sub-Packages

| Module | Depends On | Used By | Circular Deps | Coupling |
|--------|-----------|---------|---------------|----------|
| `kernel/` | `config.py`, `core/`, `database.py` (optional) | `factory.py`, `middleware.py` (via `KernelMiddleware`), `main.py` (`/health/kernel`) | None | Loose |
| `integration/` | `database.py`, `models/*`, `services/`, `security/` | `factory.py` (via `IntegrationPlatform.initialize()`) | None | Medium |
| `financial/` | `config.py`, `database.py`, `models/*`, `services/audit_service.py` | `factory.py` (feature-gated) | None | **Loose (feature-gated)** |
| `notifications/` | `models/*`, `shared.circuit_breaker`, `shared.notifications` | `routes/notifications.py` | None | Loose |
| `tasks/` | `models/*`, `database.py`, `shared.*` | `worker.py` | None | Loose |
| `audit/` | `services/audit_service.py` (re-export) | Backward compat imports | None | Loose (thin wrapper) |
| `edge/` | `database.py`, `models/edge.py`, `security/` | `routes/edge.py` | None | Loose |
| `gateways/` | `config.py`, `database.py` | `services/clinical_intelligence.py`, `routes/national_identity.py` | None | Loose |
| `firewall/` | (standalone) | `routes/login.py`, `middleware.py` | None | Loose |
| `platform/` | `database.py`, `models/*`, `security/dependencies.py` | `factory.py` | None | Medium |
| `control_plane/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `contracts/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |

### 2.10 National Sub-Packages

| Module | Depends On | Used By | Circular Deps | Coupling |
|--------|-----------|---------|---------------|----------|
| `national/rules_engine/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/workflow_runtime/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/scheduling_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/search_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/observability/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/notification_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/document_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/background_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/task_engine/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Medium |
| `national/ecosystem/` | `database.py`, `models/*`, `security/`, `national/*` | `factory.py` | None | Medium |
| `national/intelligence/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `national_data/` | `database.py`, `models/*`, `services/` | `factory.py`, `routes/national_data.py` | None | Medium |

### 2.11 Citizen & AI Platform Modules

| Module | Depends On | Used By | Circular Deps | Coupling |
|--------|-----------|---------|---------------|----------|
| `citizen_platform/` | `database.py`, `models/*`, `services/`, `security/` | `factory.py` | None | Medium |
| `ai_fabric/` | `database.py`, `models/*`, `security/`, `ai/` | `factory.py` | None | Loose |
| `ai/` | `database.py`, `models/*`, `gateways/google_ai.py` | `ai_fabric/`, `services/clinical_intelligence.py` | None | Loose |
| `document_intelligence/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `knowledge_graph/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |

### 2.12 Other Sub-Packages

| Module | Depends On | Used By | Circular Deps | Coupling |
|--------|-----------|---------|---------------|----------|
| `interoperability/` | (standalone adapters) | `services/*`, `integration/*` | None | Loose |
| `fhir/` | (pure utilities) | `integration/standards/fhir.py`, `routes/ehr_fhir.py` | None | Loose |
| `simulation/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `command_center/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `command_intelligence/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `trust/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `research_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `certification/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `pilot_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `lifecycle_platform/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `roadmap/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `health_data/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |
| `optimizer/` | `database.py`, `models/*`, `security/` | `factory.py` | None | Loose |

---

## 3. Directory Structure

```
backend/app/
├── _compat.py                   — Python <3.11 compatibility (UTC, StrEnum)
├── config.py                    — Env var loading, secrets validation, feature flags
├── database.py                  — SQLAlchemy engine, pool, session, contextvars
├── factory.py                   — Application factory (create_app, lifespan, middleware, routes)
├── main.py                      — Entry point, health endpoints, public endpoints
├── middleware.py                 — All middleware classes
├── worker.py                    — Background worker entry point (separate process)
│
├── core/                        — Infrastructure layer (21 files)
│   ├── auto_repair.py           — Auto-repair engine (GC, pool recycle)
│   ├── cache_manager.py         — L1 (in-memory) + L2 (Redis) cache coordinator
│   ├── decision_guard.py        — Clinical decision guard
│   ├── events.py                — Event bus
│   ├── feature_flags.py         — Per-tenant feature matrix + tier enforcement
│   ├── idempotency.py           — Idempotency key support
│   ├── kill_switch.py           — Emergency kill switch
│   ├── logging_config.py        — Structured JSON logging (wraps shared.logging)
│   ├── policy_engine.py         — Policy enforcement engine
│   ├── resilience.py            — Resilience patterns
│   ├── risk_engine.py           — Risk assessment engine
│   ├── runtime_guard.py         — Edge table access guard
│   ├── seeds.py                 — Critical data seeder
│   ├── self_healing.py          — Circuit breaker, degradation levels, recovery worker
│   ├── sndhs_flags.py           — SNDHS-lite deployment flags
│   ├── startup_guard.py         — Startup validation chain, system_ready flag
│   ├── startup.py               — Background task management, health watchdog
│   └── ai_dataset_flags.py      — AI dataset feature flags
│
├── security/                    — Auth, RBAC, ABAC, encryption (17 files)
│   ├── auth.py                  — JWT encode/decode
│   ├── dependencies.py          — get_current_user, RBAC dependencies
│   ├── rbac.py                  — Role-permission matrix
│   ├── abac.py                  — Attribute-based access control
│   ├── encryption.py            — Field-level encryption
│   ├── rate_limit.py            — Rate limiting
│   ├── redis_client.py          — Redis client (optional, in-memory fallback)
│   ├── session.py               — Session management
│   ├── mfa_service.py           — Multi-factor authentication
│   ├── oauth2_provider.py       — OAuth2 provider
│   ├── saml_service.py          — SAML SSO
│   ├── service_accounts.py      — Service account management
│   ├── consent_dep.py           — Consent dependency
│   └── intrusion_detection.py   — Intrusion detection
│
├── domain/                      — Pure domain logic
│   ├── exceptions.py            — DomainError, OrderStateError, ServiceError
│   └── order_state.py           — Lab order state machine
│
├── models/                      — SQLAlchemy ORM models (30 files)
│   ├── __init__.py              — Re-exports all core models
│   ├── base.py                  — Declarative base extensions
│   ├── patient.py, lab.py, user.py, lab_user.py, lab_order.py,
│   │   lab_result.py, sample.py, test_type.py, test_result.py,
│   │   audit_log.py, outbox.py, subscription.py, tenant.py,
│   │   organization.py, quality_control.py, edge.py, ai_interaction.py,
│   │   authorization.py, consent.py, canonical_patient.py, claim.py,
│   │   mfa_device.py, oauth2_client.py, oauth2_token.py,
│   │   service_account.py
│   └── ...
│
├── services/                    — Business logic layer (36 files)
│   ├── audit_service.py         — Hash-chained audit logging
│   ├── outbox_service.py        — Transactional outbox pattern
│   ├── patient_service.py       — Patient management
│   ├── order_service.py         — Lab order processing
│   ├── clinical_intelligence.py — Clinical AI interpretation
│   ├── clinical_engine.py       — Clinical decision engine
│   ├── clinical_service.py      — Clinical workflow service
│   ├── clinical_state.py        — Clinical state management
│   ├── identity.py              — Identity management
│   ├── identity_matching.py     — Patient identity matching
│   ├── authorization_service.py — Authorization delegation
│   ├── consent_service.py       — Patient consent management
│   ├── claims_service.py        — Insurance claims
│   ├── ehr_service.py           — EHR integration
│   ├── hospital_service.py      — Hospital management
│   ├── care_continuum_service.py— Care continuum
│   ├── critical_alerts.py       — Critical alert management
│   ├── patient_card.py          — QR patient card generation
│   ├── pdf_report.py            — PDF report generation
│   ├── offline_sync_service.py  — Edge/offline sync
│   ├── national_id.py           — National ID lookup
│   ├── device_trust_service.py  — Device trust verification
│   ├── interpretation.py        — Result interpretation
│   ├── epidemiology.py          — Epidemiological tracking
│   ├── data_platform_service.py — Data platform integration
│   ├── risk_based_auth_service.py — Risk-based auth
│   ├── samir.py / samir_engine.py — SAMIR engine
│   ├── ali_reza.py / ali_reza_engine.py — Ali Reza engine
│   └── mpi/                     — Master Patient Index
│       ├── api.py, matcher.py, blocking.py, resolver.py,
│       │   canonical_service.py, models.py, schemas.py
│   ├── reference/               — Reference data services
│   │   ├── master_reference_data.py, national_lab_catalog.py,
│   │   └── universal_identifier.py
│   └── governance/              — Identity governance services
│       ├── family_registry.py, identity_governance.py, merge_engine.py
│
├── routes/                      — HTTP route handlers (55 files)
│   ├── login.py, register.py, setup.py
│   ├── patients.py, results.py, test_results.py, samples.py
│   ├── labs.py, dashboard.py, metrics.py
│   ├── admin.py, admin_log_level.py
│   ├── ai.py, ai_platform.py, ai_telemetry.py
│   ├── batch.py, compliance.py, critical_alerts.py
│   ├── qr.py, id_scan.py, identity.py, national_identity.py
│   ├── notifications.py, ehr.py, ehr_fhir.py
│   ├── security.py, device_results.py, mobile.py
│   ├── patient_card.py, edge.py
│   ├── stats.py, optimizer.py, tiers.py
│   ├── mfa.py, oauth2.py, saml.py, password_reset.py
│   ├── service_accounts.py, integrations.py
│   ├── consent.py, canonical_patient.py
│   ├── claims.py, insurance.py
│   ├── clinical.py, clinical_orders.py, clinical_documentation.py,
│   │   clinical_quality.py
│   ├── care_continuum.py, hospital.py
│   ├── national_data.py, national_streaming.py
│   ├── citizen_portal.py
│   └── authorization.py
│
├── lims/                        — National LIMS
│   ├── models.py, routes.py, services.py
│   ├── state_machine.py, workflows.py, quality.py
│   ├── fhir_mappers.py, events.py, exceptions.py
│   └── integration/astm.py, integration/hl7.py
│
├── ehr/                         — EHR platform
│   ├── models/, routes/, services/
│   └── commands/, queries/, events/
│
├── hospital/                    — Hospital management
│   ├── models/, routes/, services/
│   └── commands/, queries/, events/
│
├── nursing/                     — Nursing platform
│   ├── models.py, routes.py, services.py
│   ├── base.py, enums.py, coordination.py, medication.py
│
├── pharmacy/                    — Pharmacy platform
│   ├── models.py, routes.py, services.py
│   ├── base.py, enums.py, clinical.py, dispensing.py, inventory.py
│
├── radiology/                   — Radiology platform
│   ├── models.py, routes.py, services.py
│   ├── base.py, enums.py, ai.py, device.py, pacs.py
│
├── clinical/                    — Clinical platform
│   ├── base.py, enums.py
│   └── ai/, cds/, knowledge/, quality/, research/, terminology/
│
├── care_continuum/              — Care continuum
│   ├── models/, routes/, services/
│   └── commands/, queries/, events/
│
├── nhdw/                        — National Health Data Warehouse
│   ├── models.py, routes.py, services.py
│   ├── base.py, enums.py, kpi.py, offline.py
│
├── ems/                         — Emergency Medical Services
│   └── api/routes.py
│
├── blood_bank/                  — Blood bank & transfusion
│   └── api/routes.py
│
├── critical_care/               — Critical care platform
│   └── api/routes.py
│
├── biomedical/                  — Biomedical engineering
│   └── api/routes.py
│
├── public_health/               — Public health & surveillance
│   └── api/routes.py
│
├── command_center/              — National command center
│   └── api/routes.py
│
├── pilot_platform/              — Pilot platform
│   └── api/routes.py
│
├── lifecycle_platform/          — Lifecycle platform
│   └── api/routes.py
│
├── national/                    — National Health Platform (31 sub-packages)
│   ├── rules_engine/api/routes.py
│   ├── workflow_runtime/api/routes.py
│   ├── scheduling_platform/api/routes.py
│   ├── search_platform/api/routes.py
│   ├── observability/api/routes.py
│   ├── notification_platform/api/routes.py
│   ├── document_platform/api/routes.py
│   ├── background_platform/api/routes.py
│   ├── task_engine/api/routes.py
│   ├── ecosystem/gateway/routes.py, ecosystem/routes.py
│   ├── intelligence/routes.py
│   ├── domain/, services/, events/, workflows/
│   └── ...
│
├── national_data/               — National data warehouse
│   ├── models/, routes/
│   └── ... (Governmental data models)
│
├── kernel/                      — Kernel runtime (32 files)
│   ├── integration.py           — Kernel integration API
│   ├── routes.py, runtime_routes.py
│   ├── exceptions.py, types.py
│   ├── ai_runtime.py, policy_runtime.py, rules_runtime.py
│   ├── resource_manager.py, capabilities_registry_populator.py
│   ├── background/, config/, event_bus/, features/, gateway/,
│   │   module/, plugin/, runtime/, tenant/, validation/
│   └── ... (runtime observability, security, digital twin, SDK)
│
├── integration/                 — Integration platform (22 sub-packages)
│   ├── integration.py           — IntegrationPlatform class
│   ├── routes.py, monitoring.py, offline.py, testing.py
│   ├── base.py, transformation/
│   ├── esb/                     — Enterprise Service Bus
│   │   ├── message_bus.py, router.py, dead_letter.py
│   │   ├── idempotency.py, priority.py, types.py
│   ├── standards/               — Healthcare standards
│   │   ├── fhir.py, hl7.py, dicom.py, ihe.py
│   │   ├── terminology.py, validation.py
│   ├── connectors/routes.py
│   ├── domain/                  — Integration domain logic
│   │   ├── entities/, events/, exceptions/, value_objects/
│   │   ├── repositories/, services/
│   ├── gateway/, connector/
│   ├── api_management/, application/, healthcare/,
│   │   identity/, infrastructure/, presentation/
│   └── government/
│
├── financial/                   — Financial Engine (Phase A+B)
│   ├── models.py, routes.py, services.py
│   ├── pricing.py, ranking.py, schemas.py
│
├── kernel/                      — Kernel runtime
├── notifications/               — Notification service
│   ├── service.py, telegram.py
│
├── audit/                       — Audit log (thin re-export)
│   └── audit_log.py
│
├── tasks/                       — Background task queue
│   ├── queue.py, worker.py, registry.py, schema.py
│
├── edge/                        — Edge platform
│   ├── config.py, governance.py, identity.py, trust.py
│   ├── maintenance.py, policy.py, registry.py, scheduler.py, telemetry.py
│
├── ai/                          — Clinical AI modules (17 files)
│   ├── orchestrator.py, agent_runtime.py, rag_pipeline.py
│   ├── guardrails.py, sandbox.py, security.py
│   ├── healthcare_cds.py, knowledge_graph.py, embeddings.py
│   ├── vector_store.py, memory.py, governance.py
│   ├── observability.py, system_optimizer.py, approval.py
│
├── ai_fabric/                   — AI fabric
│   ├── routes.py
│
├── gateways/                    — External service adapters
│   ├── base.py, mode.py
│   ├── google_ai.py, cloudflare_gateway.py
│   ├── insurance_gateway.py, national_identity_gateway.py
│   ├── residency_gateway.py, lab_device_gateway.py
│
├── citizen_platform/            — Citizen portal
│   ├── routes.py, phr.py, portal.py, sdk.py
│   ├── accessibility.py, appointments.py, certificates.py
│   ├── emergency.py, family.py, identity.py, integration.py
│   ├── laboratory.py, medications.py, notifications.py
│   ├── offline.py, preventive.py, privacy.py, radiology.py
│   └── telemedicine.py
│
├── platform/                    — Platform services
│   ├── routes.py, audit.py, authorization.py, caching.py
│   ├── config.py, documents.py, export.py, i18n.py
│   ├── identity.py, notifications.py, organization.py
│   ├── search.py, sync.py, validation.py, workflow.py
│
├── contracts/                   — Contract management
│   ├── routes.py, models.py, events.py, fhir.py, generator.py
│
├── interoperability/            — Interoperability models
│   ├── adapter_base.py, trust_domain.py, principal.py
│   ├── audit_event.py, failure_isolation.py, manifest.py
│
├── fhir/                        — FHIR utilities
│   ├── _capabilities.py, _reference.py, _scorecard.py, _validation_report.py
│
├── control_plane/               — Control plane
│   ├── routes.py
│
├── firewall/                    — API firewall
│   └── api_firewall.py
│
├── simulation/                  — Simulation
│   ├── routes.py
│
├── command_intelligence/        — Command intelligence
│   ├── routes.py
│
├── trust/                       — Trust platform
│   ├── routes.py
│
├── research_platform/           — Research platform
│   ├── routes.py
│
├── certification/               — Certification platform
│   ├── routes.py
│
├── document_intelligence/       — Document intelligence
│   ├── api/routes.py
│   └── infrastructure/models.py
│
├── knowledge_graph/             — Knowledge graph
│   ├── routes.py
│
├── roadmap/                     — Roadmap module
│   ├── routes.py
│
├── health_data/                 — Health data platform
│   ├── routes.py
│
├── optimizer/                   — Optimizer
│   ├── routes.py
│
└── empty stubs:
    ├── dependencies/            — Empty
    ├── validation/              — Empty
    └── policies/                — Empty
```

---

## 4. Circular Dependency Analysis

### 4.1 Detected Circular Dependencies

| Cycle | Modules Involved | Mechanism | Mitigation |
|-------|-----------------|-----------|------------|
| **C1** | `database.py` ↔ `core/self_healing.py` | `database.py` imports `core/self_healing.py` (circuit escalation). `core/self_healing.py` imports `database.py` (health checks). | **Lazy imports** — both use `from .core.self_healing import health` inside functions, not at module level. |
| **C2** | `factory.py` ↔ `middleware.py` ↔ `main.py` | `factory.py` imports `middleware.py`. `main.py` imports `factory.py`. `middleware.py` imports `core/startup_guard.py`. `factory.py` imports `core/startup.py`. | **Broken** — startup logic extracted to `core/startup.py`, middleware classes extracted to `middleware.py`. Both are imported lazily or via `_build_middleware_stack()`. |
| **C3** | `kernel/integration.py` ↔ `factory.py` | `kernel/integration.py` imports `factory.py` for kernel warmup. `factory.py` imports `kernel/integration.py` for warmup and routes. | **Lazy imports** — `from .kernel.integration import warmup_kernel` inside `_build_lifespan()`. |

### 4.2 Mitigation Strategy

The codebase consistently uses **lazy imports** (imports inside functions) to break circular dependencies. This is the recommended pattern per PEP 8. Key locations:

```python
# In database.py — lazy import to break C1
def _trigger_system_degradation(refused_count):
    from .core.self_healing import DegradationLevel, health
    ...

# In factory.py — lazy import to break C2
def _build_lifespan():
    @asynccontextmanager
    async def _lifespan(_app):
        from .core.startup import start_background_workers, warmup
        ...
```

### 4.3 Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| C1: database ↔ self_healing | **Medium** | Low (lazy-imported) | Runtime import error if import path changes; covered by CI `py_compile` + `pytest` |
| C3: kernel ↔ factory | **Low** | Low (inside lifespan) | Only triggered during startup/shutdown |
| Future: any vertical slice imports factory | **High** | Low (explicitly prevented by CLAUDE.md) | Monitored via `pyflakes E9` + code review |

---

## 5. Coupling Analysis

### 5.1 Tight Coupling

| Module | Reason |
|--------|--------|
| `config.py` | Every module reads config globals. Changing a config key name or default requires updating all consumers. |
| `database.py` | Shared `Base`, `SessionLocal`, `engine` used by every module that touches the DB. Connection pool config affects the entire app. |
| `services/audit_service.py` | Called by every mutation in every service and route. Signature change cascades everywhere. |
| `security/dependencies.py` | `get_current_user` is a dependency in virtually every route. |
| `models/` (shared) | Core models (`Patient`, `LabOrder`, `LabResult`, `User`, `LabUser`) are referenced by ~30+ services and routes. |
| `factory.py` | Central composition root that imports every module and registers every route. |

### 5.2 Medium Coupling

| Module | Reason |
|--------|--------|
| `services/` | Business services depend on models and core. Service API changes affect dependent routes. |
| `core/` | Core infrastructure is consumed by most modules but the interface is stable (circuit breaker, startup guard). |
| `kernel/` | Imports from factory for warmup; middleware depends on kernel middleware. |
| `integration/` | Depends on database, models, services. Changes to integration patterns affect multiple adapters. |
| `routes/` | Each route depends on specific services. Route API (response shape) changes break mobile clients. |

### 5.3 Loose Coupling

| Module | Reason |
|--------|--------|
| `domain/exceptions.py` | Pure exception classes, no internal deps. |
| `domain/order_state.py` | Pure state machine, no internal deps. |
| `notifications/` | Standalone notification service with its own circuit breaker. |
| `tasks/` | Background task queue, isolated from routes/services. |
| `audit/` | Thin re-export wrapper. |
| `financial/` | Feature-gated — routes only registered when `ENABLE_FINANCIAL_ENGINE=true`. |
| `fhir/` | Pure utility functions. |
| `interoperability/` | Standalone adapter interfaces. |
| `simulation/`, `command_center/`, `trust/`, `research_platform/`, etc. | Independent feature modules registered via factory but not imported by other modules. |

### 5.4 Fan-in / Fan-out Analysis

| Module | Fan-in (used by) | Fan-out (uses) | Assessment |
|--------|-----------------|----------------|------------|
| `config.py` | 50+ modules | 1 (`shared.config`) | **High fan-in** — stable interface required |
| `database.py` | 50+ modules | 3 | **High fan-in** — stable interface required |
| `services/audit_service.py` | 30+ modules | 3 | **High fan-in** — signature stability critical |
| `security/dependencies.py` | 50+ routes | 3 | **High fan-in** — signature stability critical |
| `services/outbox_service.py` | 15+ modules | 3 | Medium fan-in |
| `factory.py` | 1 (`main.py`) | 70+ modules | **Extreme fan-out** — composition root |
| `routes/*` | 0 (HTTP only) | 2-5 each | Low fan-in, low fan-out |
| `core/self_healing.py` | 8 modules | 1 | Medium fan-in |

---

## 6. Module Boundaries

### 6.1 Import Rules (from CLAUDE.md and constitution)

| Rule | Enforced By | Violation Risk |
|------|-----------|---------------|
| Routes **must not** import other routes | Code review | Low |
| Services **must not** import routes | Code review | Low |
| Models **must not** import services | Code review | Low |
| Core **must not** import routes or services | Code review | Low |
| All patient-data queries **must** filter by `lab_id` | Code review + tests | **High** — tenant isolation |
| All mutations **must** write to audit log | Code review + stability tests | **High** — compliance |
| Every migration **must** be idempotent | CI migration-gate | None (automated) |
| New columns **must** be nullable or have `server_default` | Code review | None (enforced) |
| `financial/` **must not** contain business logic in Phase A | Code review | Low |

### 6.2 Layer Isolation

```
┌──────────────────────────────────────────────────────┐
│                    HTTP / Entry                       │
│  main.py → factory.py → lifespan + middleware stack  │
├──────────────────────────────────────────────────────┤
│                    Routes Layer                       │
│  routes/*.py — HTTP handlers, validation, response   │
├──────────────────────────────────────────────────────┤
│                 Service Layer                         │
│  services/*.py — business logic, orchestration        │
├──────────────────────────────────────────────────────┤
│                  Model Layer                          │
│  models/*.py — ORM entities, relationships            │
├──────────────────────────────────────────────────────┤
│                  Database Layer                       │
│  database.py — engine, session, pool, contextvars     │
├──────────────────────────────────────────────────────┤
│        Infrastructure / Security / Config             │
│  core/*, security/*, config.py                        │
└──────────────────────────────────────────────────────┘
```

### 6.3 Vertical Slice Pattern

Domain vertical slices (`lims/`, `ehr/`, `hospital/`, etc.) contain their own three layers but must:

- Import `Base` from `database.py`, not define their own
- Use `get_db()` / `get_read_db()` from `database.py` for sessions
- Use `get_current_user` from `security/dependencies.py` for auth
- Use `log_action` from `services/audit_service.py` for audit
- Register routes via `factory.py:_register_routes()`

### 6.4 Feature-Gated Modules

| Module | Gate | Default |
|--------|------|---------|
| `financial/` | `ENABLE_FINANCIAL_ENGINE` | `false` |
| `financial/` (ads) | `ENABLE_ADS` | `false` |
| SNDHS visit tracking | `SNDHS_ENABLE_VISITS` | `false` |
| SNDHS national ID | `SNDHS_ENABLE_NATIONAL_ID` | `false` |

---

## 7. Shared Library Dependencies

The codebase depends on a `shared/` library (not in the `backend/app/` tree) providing:

| Shared Package | Used By | Purpose |
|---------------|---------|---------|
| `shared.logging` | `core/logging_config.py` | Structured JSON formatter, context binding |
| `shared.config.loader` | `config.py` | Canonical AppConfig dataclass |
| `shared.circuit_breaker` | `notifications/service.py` | Notification circuit breaker |
| `shared.notifications.sender` | `notifications/service.py` | Multi-channel notification sending |
| `shared.notifications.template` | `notifications/service.py` | Notification template rendering |

No other modules depend on `shared/`. The backend is self-contained for all business logic, models, services, and routes.

---

## 8. Related Documents

| Document | Location | Relevance |
|----------|----------|-----------|
| CLAUDE.md | `/CLAUDE.md` | Architecture overview, module boundaries, conventions |
| Factory Pattern | `backend/app/factory.py` | Composition root, middleware stack, route registration |
| Startup Guard | `backend/app/core/startup_guard.py` | Startup validation chain |
| Self-Healing | `backend/app/core/self_healing.py` | Circuit breaker, degradation levels |
| Feature Flags | `backend/app/core/feature_flags.py` | Per-tenant feature matrix |
| SNDHS Flags | `backend/app/core/sndhs_flags.py` | Deployment-wide feature toggles |
| ADRs | `backend/docs/architecture/adr/` | Architecture Decision Records |
| SNDHS Architecture | `docs/sndhs/` | National health data system design |
| Order State Machine | `backend/app/domain/order_state.py` | Lab order lifecycle |
| Kernel Architecture | `backend/app/kernel/` | Kernel runtime architecture |
| Integration Platform | `backend/app/integration/` | ESB, connectors, HL7/FHIR |
