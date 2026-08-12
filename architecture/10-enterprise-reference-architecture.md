# GULA Platform — Enterprise Reference Architecture

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Presentation Layer](#1-presentation-layer)
2. [Application Layer](#2-application-layer)
3. [Domain Layer](#3-domain-layer)
4. [Infrastructure Layer](#4-infrastructure-layer)
5. [Integration Layer](#5-integration-layer)
6. [Data Layer](#6-data-layer)
7. [Security Layer](#7-security-layer)
8. [AI Layer](#8-ai-layer)
9. [Analytics Layer](#9-analytics-layer)
10. [Operations Layer](#10-operations-layer)
11. [Platform Layer](#11-platform-layer)
12. [Offline Layer](#12-offline-layer)

---

## 1. Presentation Layer

### 1.1 Purpose

The Presentation Layer provides all user-facing interfaces for the GULA platform, supporting diverse client types, offline operation, RTL Arabic-first UX, and accessibility compliance.

### 1.2 Components

| Component | Location | Technology | Purpose |
|-----------|----------|------------|---------|
| Frontend-v2 (SPA) | `frontend-v2/` | React + Firebase | Citizen portal, Ministry Command Centre, predictive analytics, doctor/lab dashboards |
| Client (tRPC) | `client/` | tRPC + React | Lightweight SPA connected to gula-backend |
| Frontend (PWA) | `frontend/` | Static HTML PWA | Offline-capable progressive web app |
| Mobile (React Native) | `frontend-v2/` | React Native | Mobile lab and citizen access |
| Edge Agent | `edge_agent/` | Python | Off-site/offline edge computing for remote lab sites |

### 1.3 Interactions

```
[Browser/Mobile] → [Cloudflare (CDN/WAF)] → [api-gateway:8080] → [gula-backend:8000]
                                                                  → [PostgreSQL / Redis]
```

- Web apps communicate via HTTPS/JWT through the api-gateway nginx proxy
- Mobile apps use same REST endpoints with offline-first local storage
- Edge agent syncs bidirectionally using delta-sync protocol
- Static assets served through Cloudflare CDN

### 1.4 Data Flow

1. User authenticates via login form → JWT issued (`backend/app/security/auth.py:76-80`)
2. SPA loads feature flags per lab tier (`backend/app/core/feature_flags.py:176-220`)
3. RTL layout loads from shared design system tokens (`shared/design_system/rtl.py`)
4. API calls routed through `api-gateway` nginx → FastAPI middleware stack (`backend/app/main.py:19-23`)
5. Offline mutations queued in IndexedDB (PWA) or local SQLite (edge agent)

### 1.5 Security Considerations

- JWT tokens with short expiry (default 15min) + refresh tokens (`backend/app/config.py:94-99`)
- All presentation-layer inputs validated server-side (never trust client)
- CORS restricted to known origins (`backend/app/main.py`)
- CSP headers enforced via `SecurityHeadersMiddleware`
- Session fingerprinting for high-security deployments

### 1.6 Code References

- `backend/app/routes/login.py` - Authentication endpoint
- `backend/app/security/auth.py` - JWT creation and verification
- `backend/app/security/dependencies.py` - FastAPI dependency injection for auth
- `shared/design_system/tokens.py` - Design tokens
- `shared/design_system/components.py` - Shared UI components
- `frontend-v2/src/` - Main React SPA source
- `edge_agent/` - Offline edge agent

---

## 2. Application Layer

### 2.1 Purpose

The Application Layer orchestrates business operations, coordinates domain objects, handles transactions, and exposes application services to the presentation layer. It is the thin, stateless coordination layer above the domain.

### 2.2 Components

| Module | Location | Responsibility |
|--------|----------|----------------|
| Routes (API) | `backend/app/routes/` | 47 route modules exposing REST endpoints |
| Services | `backend/app/services/` | Business logic orchestration (31 services) |
| Tasks | `backend/app/tasks/` | Background task processing (outbox pattern) |
| Worker | `backend/app/worker.py` | Background worker entry point |
| Services/MPI | `backend/app/services/mpi/` | Master Patient Index resolution |
| Notifications | `backend/app/notifications/` | Push, SMS, Telegram, email |
| Audit | `backend/app/audit/` | Audit logging service |
| Integration | `backend/app/integration/` | External system integration (DDD layers) |
| EHR | `backend/app/ehr/` | Electronic Health Record commands/queries/events |

### 2.3 Capabilities

Per-tent feature matrix (`backend/app/core/feature_flags.py:47-114`):

| Capability | Starter | Growth | Enterprise |
|------------|---------|--------|------------|
| patient_management | ✓ | ✓ | ✓ |
| basic_results | ✓ | ✓ | ✓ |
| sample_tracking | ✓ | ✓ | ✓ |
| quality_control | | ✓ | ✓ |
| batch_import | | ✓ | ✓ |
| ai_interpretation | | | ✓ |
| ai_anomaly_detection | | | ✓ |
| multi_branch | | | ✓ |
| government_reporting | | | ✓ |

### 2.4 Service Design Standards

- All services are **stateless** — no instance state, all state in DB/Redis
- Services are **idempotent** where possible (`backend/app/core/idempotency.py`)
- Services emit **typed events** via the outbox pattern
- Every service is **observable** (OpenTelemetry traced, structured logged)
- Service dependencies injected via constructor (`shared/di_container/`)
- Services return domain objects or DTOs — never raw ORM models

### 2.5 Code References

- `backend/app/routes/` - All REST route modules
- `backend/app/services/` - Business logic services
- `backend/app/worker.py` - Background worker loop
- `backend/app/tasks/` - Task definitions
- `backend/app/services/outbox_service.py` - Outbox pattern implementation
- `backend/app/lims/services.py` - LIMS-specific services
- `backend/app/ehr/services/` - EHR services
- `backend/app/national/services/` - National layer services

---

## 3. Domain Layer

### 3.1 Purpose

The Domain Layer implements the core business logic, domain entities, value objects, aggregate roots, domain events, and domain services. It has zero dependencies on infrastructure or framework concerns.

### 3.2 Bounded Contexts

| Bounded Context | Location | Core Responsibility |
|-----------------|----------|---------------------|
| LIMS | `backend/app/lims/` | Laboratory Information Management System |
| National | `backend/app/national/` | National citizen registry and identity |
| Clinical | `backend/app/clinical/` | Clinical decision support, terminology, quality |
| EHR | `backend/app/ehr/` | Electronic Health Record aggregates |
| Financial | `backend/app/financial/` | Financial engine (Phase A — schema only) |
| Integration | `backend/app/integration/` | External system integration domain |
| Hospital | `backend/app/hospital/` | Hospital information domain |
| Edge | `backend/app/edge/` | Edge platform governance and policy |
| Platform | `backend/app/platform/` | Cross-cutting platform capabilities |
| Kernel | `backend/app/kernel/` | Core kernel — plugin, module, event bus |

### 3.3 Domain Entities

Key domain entities with file locations:

- `Lab` — `backend/app/models/lab.py`
- `Patient` — `backend/app/models/patient.py`
- `LabOrder` — `backend/app/models/lab_order.py`
- `LabResult` — `backend/app/models/lab_result.py`
- `Sample` — `backend/app/models/sample.py`
- `Citizen` — `backend/app/national/domain/citizen.py`
- `LabUser` — `backend/app/models/lab_user.py`
- `Organization` — `backend/app/models/organization.py`
- `Consent` — `backend/app/models/consent.py`

### 3.4 Value Objects

- `OrderState` — `backend/app/domain/order_state.py` — state machine
- `Address` — `backend/app/national/domain/address.py`
- `Gender`, `IdentityStatus`, `MaritalStatus` — `backend/app/national/enums.py`
- `ClinicalEnums` — `backend/app/clinical/enums.py`
- `FinancialRanking` — `backend/app/financial/ranking.py`

### 3.5 Domain Events

Events are defined per bounded context:

- `backend/app/lims/events.py` — LIMS domain events
- `backend/app/national/events/` — National domain events (citizen, encounter, family, identity, security)
- `backend/app/ehr/events/` — EHR events
- `backend/app/integration/domain/` — Integration domain events
- `backend/app/kernel/event_bus/events.py` — Kernel-level events
- `shared/events/constants.py` — Shared event type constants

### 3.6 State Machines

Order state machine (`backend/app/domain/order_state.py:18-23`):

```
pending → completed → validated (terminal)
       ↘ cancelled  ↗         (terminal)
```

Validated orders are immutable — `assert_not_locked()` enforces this.

### 3.7 Security Considerations

- Domain entities enforce tenant isolation via `lab_id` column
- Optimistic locking via `version` column on `LabResult`
- Citizens never DELETEd — only merged/deactivated
- Audit invariants enforced at domain level

### 3.8 Code References

- `backend/app/domain/order_state.py` — Lab order state machine
- `backend/app/national/domain/` — 44 domain entities
- `backend/app/clinical/` — Clinical domain (CDS, knowledge, terminology, quality)
- `backend/app/models/base.py` — Shared model mixins
- `backend/app/models/` — 21 SQLAlchemy models
- `backend/app/lims/state_machine.py` — LIMS-specific state machines
- `backend/app/kernel/types.py` — Kernel domain types (ServiceDescriptor, CapabilityStatus)

---

## 4. Infrastructure Layer

### 4.1 Purpose

The Infrastructure Layer provides the technical foundation for the platform — containers, networking, storage, compute, and deployment orchestration.

### 4.2 Components

#### 4.2.1 Containerization

| Component | Configuration | Purpose |
|-----------|---------------|---------|
| Docker Compose | `docker-compose.yml` | Primary MVP deployment |
| Full Stack | `docker-compose.full.yml` | + Prometheus, Grafana, Loki, RabbitMQ, HAProxy |
| Scale Stack | `docker-compose.scale.yml` | Horizontal scaling with HAProxy |
| PostgreSQL 16 | `docker-compose.yml` | Primary database |
| Redis 7 | `docker-compose.yml` | Caching, rate limiting, session store |

#### 4.2.2 Networking

```
Internet → host nginx (TLS) → api-gateway (Docker nginx :8080) → gula-backend (:8000)
                                                                    → PostgreSQL :5432
                                                                    → Redis :6379
```

- Backend never exposes a public port — all traffic through api-gateway
- Internal Docker network for inter-service communication
- Cloudflare for DNS, WAF, CDN, edge compute
- HAProxy for horizontal scaling (config/haproxy/haproxy.cfg)

#### 4.2.3 Monitoring Infrastructure

| Component | Config | Purpose |
|-----------|--------|---------|
| Prometheus | `config/prometheus/` | Metrics collection |
| Grafana | `config/grafana/` | Dashboards and alerting |
| Loki | `docker-compose.full.yml` | Log aggregation |
| RabbitMQ | `docker-compose.full.yml` | Message broker (future) |

#### 4.2.4 Compute Profiles

- **Standard**: Single endpoint on Render/DigitalOcean
- **High-Availability**: Multi-replica with HAProxy load balancer
- **Edge**: Device bridge running on-premise at lab sites
- **Air-Gapped**: Fully isolated deployment without external dependencies

### 4.3 Scalability Architecture

```
            ┌──────────┐
            │  HAProxy  │  (port 8404 stats)
            │  :8080    │
            └────┬─────┘
         ┌───────┼───────┐
         │       │       │
    ┌────┴──┐ ┌──┴───┐ ┌──┴────┐
    │gula-  │ │gula-  │ │gula-  │  ... N replicas
    │backend│ │backend│ │backend│
    └───────┘ └───────┘ └───────┘
         │         │         │
         └─────────┼─────────┘
             ┌─────┴─────┐
             │ PostgreSQL │
             │ + Redis    │
             └───────────┘
```

### 4.4 Database Connection Pool

Formula: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`

Defaults: 3 × (6 + 12) = 54 (within Postgres default of 100)

Configuration in `backend/app/database.py` — per-request contextvars for correlation.

### 4.5 Code References

- `docker-compose.yml` — Primary deployment configuration
- `docker-compose.full.yml` — Full observability stack
- `docker-compose.scale.yml` — Horizontal scaling
- `config/haproxy/haproxy.cfg` — Load balancer configuration
- `config/prometheus/` — Scrape configs and alerting rules
- `config/grafana/` — Provisioned dashboards
- `backend/app/database.py` — Connection pool and engine configuration

---

## 5. Integration Layer

### 5.1 Purpose

The Integration Layer manages all external system communication — government APIs, lab devices, EHR systems, insurance providers, and third-party services — through a consistent gateway architecture.

### 5.2 Gateway Architecture

Every external integration uses `ExternalGateway` base class (`backend/app/gateways/base.py`):

```
Business Code → Gateway Adapter → External API
                  ├─ Rate Limiter (sliding window)
                  ├─ Circuit Breaker (3-state)
                  ├─ Retry + Backoff
                  ├─ Timeout
                  ├─ Data Trust Classification
                  ├─ Response Validation
                  └─ Audit Log
```

### 5.3 Gateway Catalog

| Gateway | File | Mode | Trust Level | External System |
|---------|------|------|-------------|-----------------|
| National ID | `gateways/national_identity_gateway.py` | stub/live | NON_CRITICAL | البطاقة الوطنية |
| Insurance | `gateways/insurance_gateway.py` | stub/live | NON_CRITICAL | الضمان الصحي |
| Residency | `gateways/residency_gateway.py` | stub/live | NON_CRITICAL | الإقامة للأجانب |
| Cloudflare | `gateways/cloudflare_gateway.py` | stub/live | ENRICHMENT | DNS/WAF/Workers |
| Lab Device | `gateways/lab_device_gateway.py` | stub/live | CRITICAL | Sysmex, Roche, Mindray |
| Google AI | `gateways/google_ai.py` | stub/live | ENRICHMENT | Gemini AI |

### 5.4 Data Trust Classification

From `backend/app/gateways/base.py:56-72`:

- **ENRICHMENT** — UI decoration only (city names, icons). Never drives logic.
- **NON_CRITICAL** — Operational data (insurance status, SMS delivery). Used with verified fallback.
- **CRITICAL** — Clinical decision data. **ALWAYS BLOCKED** from external sources.

### 5.5 Device Integration

Lab instrument integration via ASTM/HL7 protocol:

- `services/device_bridge/` — LabLink-Core: reads from physical devices
- `services/device_bridge/app/integration/gula_client.py` — Forwards results to gula-backend
- `shared/device/astm.py` — ASTM protocol parser
- `shared/device/adapters.py` — Device adapters for specific instruments

### 5.6 HL7/FHIR Integration

- `backend/app/interoperability/` — HL7/FHIR interoperability layer
- `backend/app/interoperability/adapter_base.py` — Base adapter contract
- `backend/app/interoperability/trust_domain.py` — Trust domain verification
- `backend/app/national/fhir/` — FHIR resource mapping (R4/R5)
- `backend/app/lims/fhir_mappers.py` — LIMS-to-FHIR mapping

### 5.7 Event-Driven Integration

- Outbox pattern for reliable event publishing (`backend/app/models/outbox.py`)
- Event bus for in-process communication (`backend/app/kernel/event_bus/`)
- Dead letter queue for failed events (`backend/app/kernel/event_bus/dead_letter_queue.py`)
- Event replay capability (`backend/app/kernel/event_bus/replay.py`)

### 5.8 Security Considerations

- Every gateway call audited to `audit_logs` table
- Circuit breaker prevents cascade failures
- Response validation rejects malformed external data
- Trust classification prevents external data from driving clinical decisions
- Shadow mode for safe comparison without risk

### 5.9 Code References

- `backend/app/gateways/base.py` — Base gateway with all resilience patterns
- `backend/app/gateways/mode.py` — Stub/live mode management
- `backend/app/gateways/gov_*.py` — Government integration adapters
- `backend/app/interoperability/` — HL7/FHIR interoperability
- `backend/app/integration/` — DDD-structured integration module
- `services/device_bridge/` — Lab instrument integration
- `shared/device/` — Device protocol definitions

---

## 6. Data Layer

### 6.1 Purpose

The Data Layer manages all persistent storage — relational (PostgreSQL), caching (Redis), object storage, and analytical stores — with strict governance over data integrity, tenant isolation, audit, and retention.

### 6.2 Storage Components

| Store | Technology | Purpose | Location/Config |
|-------|-----------|---------|-----------------|
| Primary OLTP | PostgreSQL 16 | All transactional data | `DATABASE_URL` env var |
| Cache/Session | Redis 7 | Cache, rate limiting, session, pub/sub | `REDIS_URL` env var |
| Object Storage | Cloudflare R2 / S3 | Documents, PDFs, images | `gateways/cloudflare_gateway.py` |
| Analytics | PostgreSQL (same DB) | Reporting queries, OLAP | Separate read replica |
| Data Lake | (future) ClickHouse | Long-term analytics, time-series | Future component |

### 6.3 Database Schema Architecture

```
public schema (LIMS):
  labs, lab_users, patients, lab_orders, lab_results, samples, ...
  audit_logs, outbox_events, feature_flags, subscriptions, ...

national schema:
  national_citizens, identity_claims, mpi_merge_audit, ...

edge schema:
  edge_devices, edge_sync_log, edge_policy, ...
```

### 6.4 Model Patterns

All models follow consistent patterns from `shared/models/base.py`:

- `TimestampMixin` — created_at, updated_at
- `SoftDeleteMixin` — deleted_at (soft delete)
- `AuditMixin` — created_by, updated_by
- `TenantMixin` — lab_id (tenant isolation)
- `OptimisticLockMixin` — version (concurrency control)

### 6.5 Migration Policy

From `CLAUDE.md` Migration Policy:

1. Never modify existing migrations
2. All schema changes = new Alembic revision
3. `20250322_0000_create_base_schema.py` is immutable
4. Every migration must be idempotent (use `_has_column()`, `_table_exists()` guards)
5. New columns must be nullable or have `server_default`
6. Test on clean DB: `docker compose down -v && docker compose up -d postgres`

### 6.6 Redis Data Model

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `blacklist:jti:{jti}` | JWT revocation | Until token expiry |
| `rate_limit:{lab_id}:{endpoint}` | Rate limiting | Sliding window |
| `cache:{key}` | General cache | Per-key (configurable) |
| `session:{session_id}` | User sessions | 24h |
| `idempotency:{lab_id}:{key}` | Idempotency keys | 24h |
| `circuit:{name}` | Circuit breaker state | Persistent |

### 6.7 Audit Data

- `audit_logs` table — all CRUD operations, immutable hash chain
- `mpi_merge_audit` — identity decisions, hash-chained
- Outbox events (`outbox_events`) — guaranteed delivery trail

### 6.8 Security Considerations

- PII encrypted at rest (national_id via `shared/security/encryption.py`)
- Patients.national_id HMAC-hashed, never plaintext
- All queries filtered by `lab_id` for tenant isolation
- Audit logs append-only with hash chain for tamper detection

### 6.9 Code References

- `backend/app/models/base.py` — Model mixins
- `backend/app/models/` — 21 SQLAlchemy models
- `backend/app/national/domain/citizen.py` — Citizen entity
- `backend/app/national/repositories/` — Repository pattern implementations
- `backend/app/audit/audit_log.py` — Audit service
- `backend/app/core/cache_manager.py` — Cache management
- `backend/app/security/redis_client.py` — Redis client
- `backend/app/database.py` — Database engine and pool
- `shared/models/base.py` — Shared model base classes
- `shared/security/encryption.py` — Encryption utilities

---

## 7. Security Layer

### 7.1 Purpose

The Security Layer provides defense-in-depth for the entire platform — authentication, authorization, encryption, audit, rate limiting, and threat detection.

### 7.2 Authentication

| Mechanism | Implementation | Location |
|-----------|---------------|----------|
| JWT Access Token | RS256/HMAC-signed, 15min TTL | `backend/app/security/auth.py:76-80` |
| JWT Refresh Token | Longer-lived, rotation | `backend/app/security/auth.py` |
| JWT Blacklist | Redis-backed revocation | `backend/app/security/auth.py:43-52` |
| Password Auth | bcrypt via shared.auth | `shared/auth/passwords.py` |
| OAuth2 (future) | OIDC-compatible | Planned |

### 7.3 Authorization

Three-layer model:

| Model | Component | Location |
|-------|-----------|----------|
| RBAC | 9 roles × 13 permissions | `backend/app/security/rbac.py` |
| ABAC | Attribute-based with conditions | `backend/app/security/abac.py` |
| National ABAC | Enhanced for citizen data | `backend/app/national/security/abac.py` |
| Break Glass | Emergency access | `backend/app/national/security/break_glass.py` |
| Purpose of Use | Context-based access | `backend/app/national/security/purpose_of_use.py` |

### 7.4 RBAC Roles

From `shared/rbac/permissions.py`:

| Role | Level | Typical User |
|------|-------|-------------|
| admin | 100 | Platform administrator |
| province_admin | 80 | Provincial health authority |
| lab_admin | 60 | Lab director |
| doctor | 50 | Referring physician |
| manager | 40 | Lab manager |
| technician | 30 | Lab technician |
| receptionist | 20 | Front desk |
| viewer | 10 | Read-only access |
| api_client | 5 | Machine-to-machine |

### 7.5 Encryption

| Scope | Algorithm | Key Management | Location |
|-------|-----------|---------------|----------|
| At rest (PII) | AES-256-GCM | `ENCRYPTION_KEY` env var | `shared/security/encryption.py` |
| Transit (API) | TLS 1.3 | nginx termination | Host config |
| National ID | HMAC-SHA256 | `NID_HMAC_KEY` env var | `backend/app/security/encryption.py` |
| Patient Card | HMAC-SHA256 | `PATIENT_CARD_SECRET` | `backend/app/services/patient_card.py` |

### 7.6 Security Middleware Stack

From `backend/app/main.py`, middleware ordering:

1. `MaxBodySizeMiddleware` — 413 above MAX_REQUEST_BODY_MB
2. `RequestIDMiddleware` — X-Request-ID correlation
3. `DocsAuthMiddleware` — Production API doc protection
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — Access log + X-Response-Time
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options
7. `GZipMiddleware`
8. `ReadinessMiddleware` — 503 until system_ready
9. `DegradedModeMiddleware` — Circuit breaker degradation
10. `ConcurrencyLimitMiddleware` — In-flight request cap

### 7.7 Rate Limiting

- `backend/app/security/rate_limit.py` — Sliding window rate limiter
- `backend/app/security/intrusion_detection.py` — Anomaly-based detection
- `backend/app/firewall/api_firewall.py` — Application firewall
- Per-endpoint limits, per-lab quotas, burst protection

### 7.8 Audit Security

- All mutations logged to `audit_logs`
- Hash chain prevents tampering (SHA-256 chain_hash)
- Identity audit via `mpi_merge_audit`
- Gateway call audit with fingerprint and latency

### 7.9 Code References

- `backend/app/security/auth.py` — Authentication core
- `backend/app/security/jwt_guard.py` — JWT validation guard
- `backend/app/security/rbac.py` — Role-based access control
- `backend/app/security/abac.py` — Attribute-based access control
- `backend/app/security/encryption.py` — Encryption utilities
- `backend/app/security/rate_limit.py` — Rate limiting
- `backend/app/security/intrusion_detection.py` — Intrusion detection
- `backend/app/security/dependencies.py` — FastAPI auth dependencies
- `backend/app/security/consent_dep.py` — Consent enforcement
- `backend/app/security/session.py` — Session management
- `backend/app/national/security/` — National layer security (15 modules)
- `backend/app/firewall/api_firewall.py` — API firewall
- `backend/app/core/kill_switch.py` — Emergency kill switch
- `shared/security/encryption.py` — Shared encryption
- `shared/security/hmac.py` — HMAC utilities

---

## 8. AI Layer

### 8.1 Purpose

The AI Layer provides clinical intelligence, natural language processing, anomaly detection, and decision support while maintaining strict clinical safety guardrails.

### 8.2 Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Clinical AI | `backend/app/ai/` | AI sandbox, guardrails, approval, system optimizer |
| Clinical Intelligence | `backend/app/clinical/ai/` | Clinical decision support AI |
| AI Routes | `backend/app/routes/ai.py` | AI API endpoints |
| AI Telemetry | `backend/app/routes/ai_telemetry.py` | AI usage monitoring |
| AI Services | `backend/app/services/ali_reza_engine.py` | Ali Reza AI engine |
| AI Services | `backend/app/services/samir_engine.py` | SAMIR AI engine |
| AI Provider | `shared/ai/provider.py` | AI provider abstraction |
| AI Client | `shared/ai/client.py` | AI API client |

### 8.3 AI Guardrails

From `backend/app/ai/guardrails.py`:

- Clinical safety checks before any AI output reaches a patient
- Human-in-the-loop approval for critical decisions (`backend/app/ai/approval.py`)
- Sandboxed execution for untrusted AI code (`backend/app/ai/sandbox.py`)
- System optimizer for resource management (`backend/app/ai/system_optimizer.py`)

### 8.4 Clinical Decision Support

From `backend/app/clinical/cds/`:

- CDS rules engine
- Knowledge base integration
- Clinical quality measures
- Evidence-based recommendations

### 8.5 AI Interpretation Services

- `backend/app/services/interpretation.py` — Clinical interpretation engine
- `backend/app/services/clinical_intelligence.py` — Clinical intelligence
- `backend/app/services/ali_reza_engine.py` — Ali Reza diagnostic support
- `backend/app/services/samir_engine.py` — SAMIR predictive analytics

### 8.6 Feature Gating

AI features are gated per-tier (`backend/app/core/feature_flags.py:102-106`):

- `ai_interpretation` — Enterprise tier only
- `ai_anomaly_detection` — Enterprise tier only
- `ai_epidemiology` — Enterprise tier only

### 8.7 Security Considerations

- AI outputs never directly reach patients without human review
- All AI calls logged for audit
- Rate-limited API access per lab
- Sandboxed AI module execution
- Data trust classification prevents external AI from clinical decisions

### 8.8 Code References

- `backend/app/ai/guardrails.py` — Clinical safety guardrails
- `backend/app/ai/approval.py` — Human-in-the-loop approval
- `backend/app/ai/sandbox.py` — AI sandbox
- `backend/app/ai/system_optimizer.py` — AI resource optimizer
- `backend/app/clinical/ai/` — Clinical AI integration
- `backend/app/services/interpretation.py` — Interpretation engine
- `backend/app/services/ali_reza_engine.py` — Ali Reza engine
- `backend/app/services/samir_engine.py` — SAMIR engine
- `backend/app/routes/ai.py` — AI API routes
- `shared/ai/provider.py` — AI provider abstraction
- `shared/ai/client.py` — AI client

---

## 9. Analytics Layer

### 9.1 Purpose

The Analytics Layer provides business intelligence, statistical analysis, epidemiological surveillance, and operational reporting across all platform data.

### 9.2 Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Statistics | `backend/app/routes/stats.py` | Statistics and trends API |
| Advanced Analytics | `backend/app/services/data_platform_service.py` | Data platform analytics |
| Epidemiology | `backend/app/services/epidemiology.py` | Disease surveillance |
| Clinical Quality | `backend/app/clinical/quality/` | Quality measures |
| Clinical Research | `backend/app/clinical/research/` | Research analytics |
| Financial Ranking | `backend/app/financial/ranking.py` | Financial analytics |
| Analytics Dashboard | `backend/app/routes/dashboard.py` | Operational dashboards |

### 9.3 Reporting Capabilities

- PDF report generation (`shared/pdf/generator.py`)
- Batch export of results
- Government compliance reporting
- Ministry-level aggregate dashboards

### 9.4 Data Flow for Analytics

```
Transactional DB (PostgreSQL) → Application-level aggregation → API Response
                                                                    ↓
                                                              Cache (Redis)
                                                                    ↓
                                                              Dashboard UI
```

Future state: ClickHouse data lake for long-term OLAP queries.

### 9.5 Feature Gating

- `advanced_analytics` — Growth tier and above
- `government_reporting` — Enterprise tier (or government deployment mode)

### 9.6 Code References

- `backend/app/routes/stats.py` — Statistics API
- `backend/app/services/data_platform_service.py` — Data platform
- `backend/app/services/epidemiology.py` — Epidemiology
- `backend/app/clinical/quality/` — Clinical quality
- `backend/app/clinical/research/` — Clinical research
- `backend/app/routes/dashboard.py` — Dashboard endpoints
- `shared/pdf/generator.py` — PDF report generation

---

## 10. Operations Layer

### 10.1 Purpose

The Operations Layer provides observability, self-healing, incident response, and SRE capabilities to keep the platform running reliably.

### 10.2 Observability

| Component | Technology | Location |
|-----------|-----------|----------|
| Structured Logging | JSON format | `backend/app/core/logging_config.py` |
| Request Tracing | OpenTelemetry | `backend/app/main.py` |
| Metrics | Prometheus | `config/prometheus/` |
| Dashboards | Grafana | `config/grafana/` |
| Health Endpoints | FastAPI | `backend/app/main.py` |
| Error Tracking | Sentry (optional) | `backend/app/main.py:48-71` |

### 10.3 Health Endpoints

| Path | Purpose | Always Allowed |
|------|---------|----------------|
| `/health` | Liveness | Yes |
| `/health/live` | Same as above | Yes |
| `/health/ready` | Readiness (Docker healthcheck) | Yes |
| `/health/status` | Diagnostic (always visible) | Yes |
| `/health/deep` | Grade + latency + memory | Yes |

### 10.4 Self-Healing System

3-layer self-healing from `backend/app/core/self_healing.py`:

1. **Circuit Breaker** — CLOSED → OPEN → HALF_OPEN for each service dependency
2. **Degraded Mode** — NONE → L1 (cache heavy) → L2 (read-only) → L3 (critical only)
3. **Recovery Worker** — Background probing of failed services

### 10.5 Auto-Repair Engine

From `backend/app/core/auto_repair.py`:

- GC pressure detection and mitigation
- Database connection pool recycle
- Connection leak detection
- Stuck query termination

### 10.6 Adaptive Concurrency

From `backend/app/main.py::_adaptive_concurrency_loop`:

- Halves `_MAX_CONCURRENT` on 2 slow DB reads (>300ms)
- Restores after 3 fast reads (<150ms)
- Clinical writes exempt from shedding

### 10.7 Monitoring Metrics

RED metrics (Rate, Errors, Duration) for every service:

| Metric | Source | Collection |
|--------|--------|-----------|
| Request Rate | `RequestTimingMiddleware` | Per-endpoint |
| Error Rate | App logs + Sentry | Real-time |
| Latency (P50/P95/P99) | `RequestTimingMiddleware` | Histogram |
| DB Connection Pool | `database.py` | Gauge |
| Circuit Breaker State | `self_healing.py` | Gauge |
| Active Requests | `ConcurrencyLimitMiddleware` | Gauge |

### 10.8 Alerting

- Health alert loop scores GREEN/YELLOW/RED every 60s
- Webhook notifications on state transitions (Telegram/Discord/Slack)
- RED state persists → reminder every 5 minutes
- Alert webhook URL configured via `ALERT_WEBHOOK_URL` env var

### 10.9 Code References

- `backend/app/core/self_healing.py` — Circuit breaker and degraded mode
- `backend/app/core/auto_repair.py` — Auto-repair engine
- `backend/app/core/logging_config.py` — JSON structured logging
- `backend/app/main.py` — Middleware stack, health endpoints, background loops
- `backend/app/core/startup_guard.py` — Startup validation
- `backend/app/routes/metrics.py` — Prometheus metrics endpoint
- `config/prometheus/` — Prometheus configuration
- `config/grafana/` — Grafana dashboards
- `shared/health/checker.py` — Health check utilities
- `shared/observability/tracer.py` — OpenTelemetry tracing
- `shared/metrics/collector.py` — Metrics collection

---

## 11. Platform Layer

### 11.1 Purpose

The Platform Layer provides the kernel, module system, plugin framework, tenant management, capability registry, and lifecycle management that all other layers build upon.

### 11.2 Kernel

The kernel (`backend/app/kernel/`) is the foundation module with zero dependencies on business modules:

| Subsystem | Location | Purpose |
|-----------|----------|---------|
| Module registry | `backend/app/kernel/module/` | Module discovery, loading, metadata, versioning |
| Plugin system | `backend/app/kernel/plugin/` | Hot-reload, sandbox, permissions, marketplace |
| Event bus | `backend/app/kernel/event_bus/` | In-process eventing, outbox, DLQ, replay, snapshots |
| Feature flags | `backend/app/kernel/features/` | Capabilities, experimental, regional, kill switch |
| Tenant | `backend/app/kernel/tenant/` | Configuration, isolation, quotas, registry, resolver |
| Background | `backend/app/kernel/background/` | Cron, scheduler, task queue, worker pool, locks |
| Validation | `backend/app/kernel/validation/` | Schema and business rule validation |
| Runtime | `backend/app/kernel/runtime/` | Service lifecycle, health probes |
| Config | `backend/app/kernel/config/` | Kernel configuration |
| Gateway | `backend/app/kernel/gateway/` | Kernel-level service gateway |

### 11.3 Module System

```python
# From backend/app/kernel/module/metadata.py
@dataclass
class ModuleMetadata:
    name: str
    version: str
    description: str
    dependencies: list[str]
    capabilities: list[str]
    status: ModuleStatus  # DRAFT | ACTIVE | DEPRECATED | RETIRED
```

Modules are discovered by `backend/app/kernel/module/discovery.py` and loaded by `backend/app/kernel/module/loader.py`, with dependency resolution in `backend/app/kernel/module/resolver.py` and compatibility checking in `backend/app/kernel/module/compatibility.py`.

### 11.4 Capability Registry

From `backend/app/kernel/types.py`:

```python
class CapabilityStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
```

Capabilities are registered via `backend/app/kernel/capabilities_registry_populator.py` and served via `backend/app/kernel/routes.py`.

### 11.5 Plugin System

From `backend/app/kernel/plugin/`:

- **Loader** (`plugin/loader.py`) — Dynamic module loading
- **Sandbox** (`plugin/sandbox.py`) — Isolated execution
- **Permissions** (`plugin/permissions.py`) — Plugin capabilities
- **Manager** (`plugin/manager.py`) — Lifecycle management
- **Registry** (`plugin/registry.py`) — Plugin catalog
- **Hot-reload** (`plugin/hot_reload.py`) — Watch for changes
- **Version Manager** (`plugin/version_manager.py`) — Compatibility
- **Marketplace** (`plugin/marketplace.py`) — Plugin distribution

### 11.6 Tenant Management

From `backend/app/kernel/tenant/`:

- **Registry** (`tenant/registry.py`) — Tenant catalog
- **Resolver** (`tenant/resolver.py`) — Tenant identification from request
- **Isolation** (`tenant/isolation.py`) — Data and compute isolation
- **Quotas** (`tenant/quotas.py`) — Resource limits
- **Config** (`tenant/config.py`) — Per-tenant configuration

### 11.7 Service Container

From `shared/di_container/`:

- **Engine** (`shared/di_container/engine.py`) — DI container
- **Service Descriptor** — Service metadata
- **Lifetime** — Singleton/scoped/transient
- **Interfaces** — Interface definitions

### 11.8 Capabilities Registry API

From `backend/app/kernel/routes.py`:

- `GET /kernel/status` — Kernel health
- `GET /kernel/services` — Registered services
- `GET /kernel/capabilities` — Registered capabilities
- `GET /kernel/plugins` — Installed plugins

### 11.9 Code References

- `backend/app/kernel/module/` — Module system
- `backend/app/kernel/plugin/` — Plugin framework
- `backend/app/kernel/event_bus/` — Event bus system
- `backend/app/kernel/features/` — Feature flags
- `backend/app/kernel/tenant/` — Tenant management
- `backend/app/kernel/background/` — Background task infrastructure
- `backend/app/kernel/types.py` — Core type definitions
- `backend/app/kernel/routes.py` — Kernel management API
- `backend/app/kernel/integration.py` — Kernel integration helpers
- `shared/di_container/` — Dependency injection container
- `shared/cache/backends.py` — Cache backend abstractions

---

## 12. Offline Layer

### 12.1 Purpose

The Offline Layer enables the platform to operate in environments with intermittent connectivity — remote labs, disaster zones, and mobile phlebotomy units — through delta sync, conflict resolution, and local-first data management.

### 12.2 Edge Agent

From `edge_agent/`:

- Local SQLite database for offline operation
- Delta sync protocol for bidirectional data transfer
- Conflict resolution based on last-writer-wins with audit trail
- Scheduled sync when connectivity is restored
- WAL mode for safe concurrent access

### 12.3 Offline-First Web Application

From `frontend/` (static HTML PWA):

- Service worker for offline caching
- IndexedDB for local mutation queue
- Background sync when online
- Cache-first strategy for static assets
- Network-first for data with offline fallback

### 12.4 Sync Architecture

```
Edge Agent (local SQLite) ──sync──→ gula-backend ──→ PostgreSQL
     ↑                                ↑
     │                                │
  Lab Devices (ASTM/HL7)          Other Labs

Sync Protocol:
  1. Client requests delta (last_sync_timestamp)
  2. Server returns changes since timestamp
  3. Client applies changes locally
  4. Client sends local mutations
  5. Server resolves conflicts (LWW with audit)
  6. Response confirms or flags conflicts
```

### 12.5 Conflict Resolution Strategy

- **Last-Writer-Wins** for most data (with full audit trail)
- **Manual review** for clinical data conflicts (flagged in UI)
- **Transactional integrity** — sync is atomic per patient/order
- **Conflict audit** — every conflict logged with both versions

### 12.6 Edge Device Integration

From `services/device_bridge/`:

- ASTM/HL7 protocol parsing
- Device authentication and trust
- Offline result buffering
- Batched upload on reconnect

### 12.7 Edge Platform Management

From `backend/app/edge/`:

- **Config** (`edge/config.py`) — Edge device configuration
- **Governance** (`edge/governance.py`) — Policy enforcement
- **Identity** (`edge/identity.py`) — Device identity
- **Maintenance** (`edge/maintenance.py`) — Remote maintenance
- **Policy** (`edge/policy.py`) — Edge deployment policies
- **Registry** (`edge/registry.py`) — Edge device catalog
- **Scheduler** (`edge/scheduler.py`) — Sync scheduling
- **Telemetry** (`edge/telemetry.py`) — Edge device monitoring
- **Trust** (`edge/trust.py`) — Device trust verification

### 12.8 National Layer Offline

The National layer is designed to work independently — LIMS continues to function if National is offline:

- LIMS publishes outbox events → National consumes when available
- Identity resolution uses local cache (citizen_ulid denormalized on patients)
- No synchronous dependency on National for lab operations

### 12.9 Code References

- `edge_agent/` — Offline edge agent
- `frontend/` — Offline-capable PWA
- `backend/app/edge/` — Edge platform management
- `services/device_bridge/` — Device bridge with offline buffering
- `backend/app/services/mpi/` — MPI with offline-friendly design
- `backend/app/models/outbox.py` — Outbox for async replication
- `backend/app/kernel/event_bus/recovery.py` — Event recovery after disconnect

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial enterprise reference architecture |

**Review Cycle**: This document must be reviewed and updated quarterly or when significant architectural changes occur.
