# GULA Platform — Knowledge Integration

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Knowledge Graph](#1-knowledge-graph)
2. [API Catalog](#2-api-catalog)
3. [Service Catalog Index](#3-service-catalog-index)
4. [Data Dictionary](#4-data-dictionary)
5. [FHIR Catalog](#5-fhir-catalog)
6. [Security Catalog Index](#6-security-catalog-index)
7. [Operations Catalog Index](#7-operations-catalog-index)
8. [ADR Catalog](#8-adr-catalog)
9. [Cross-Reference Matrix](#9-cross-reference-matrix)

---

## 1. Knowledge Graph

### 1.1 Purpose

The knowledge graph connects all platform artifacts — code modules, services, APIs, data entities, security controls, operations, and architecture decisions — into a navigable map of the entire platform.

### 1.2 Implementation

| Component | Purpose | Location |
|-----------|---------|----------|
| Knowledge Graph Engine | Graph analysis and querying | `backend/app/knowledge_graph/engine.py` |
| Knowledge Graph Models | Graph data structures | `backend/app/knowledge_graph/models.py` |
| Knowledge Graph Routes | Graph query API | `backend/app/knowledge_graph/routes.py` |
| Architecture Validator | Dependency and layer validation | `shared/architecture/validator.py` |
| Architecture Knowledge Graph | Module relationship analysis | `shared/architecture/knowledge_graph.py` |

### 1.3 Entity Types

| Entity Type | Description | Examples |
|-------------|-------------|----------|
| `module` | Python package | `backend.app.lims`, `backend.app.national` |
| `service` | Business service | `OrderService`, `CitizenService` |
| `route` | API endpoint | `POST /api/orders`, `GET /api/patients/{id}` |
| `model` | Database model | `LabOrder`, `Citizen`, `Patient` |
| `event` | Domain event | `order.created`, `citizen.registered` |
| `security_control` | Security mechanism | `RBAC`, `ABAC`, `JWT` |
| `gateway` | External integration | `NIDGateway`, `InsuranceGateway` |
| `adr` | Architecture decision | ADR-001, ADR-002 |
| `test` | Test module | `test_security.py`, `test_patient_card.py` |
| `metric` | Engineering metric | `line_coverage`, `P95_latency` |

### 1.4 Relationships

| Relationship | Description |
|-------------|-------------|
| `depends_on` | Module dependency |
| `implements` | Service implements interface |
| `exposes` | Route exposes service through API |
| `publishes` | Service publishes event |
| `consumes` | Service consumes event |
| `maps_to` | Model maps to FHIR resource |
| `gateway_to` | Gateway connects to external system |
| `audited_by` | Action audited by audit system |
| `governed_by` | Controlled by security control |
| `documented_in` | Decision documented in ADR |
| `tested_by` | Feature tested by test module |

### 1.5 Code References

- `backend/app/knowledge_graph/` — Knowledge graph implementation
- `shared/architecture/validator.py` — Architecture validation
- `shared/architecture/knowledge_graph.py` — Codebase analysis graph

---

## 2. API Catalog

### 2.1 REST API Endpoints

| Prefix | Route Module | Purpose | Versioned |
|--------|-------------|---------|-----------|
| `/api/labs` | `backend/app/routes/labs.py` | Lab management | ✅ |
| `/api/login` | `backend/app/routes/login.py` | Authentication | ✅ |
| `/api/register` | `backend/app/routes/register.py` | Registration | ✅ |
| `/api/patients` | `backend/app/routes/patients.py` | Patient management | ✅ |
| `/api/orders` | `backend/app/routes/clinical_orders.py` | Lab orders | ✅ |
| `/api/results` | `backend/app/routes/results.py` | Lab results | ✅ |
| `/api/samples` | `backend/app/routes/samples.py` | Sample tracking | ✅ |
| `/api/test-results` | `backend/app/routes/test_results.py` | Individual test results | ✅ |
| `/api/quality-control` | `backend/app/routes/quality_control.py` | QC management | ✅ |
| `/api/critical-alerts` | `backend/app/routes/critical_alerts.py` | Critical alerts | ✅ |
| `/api/patient-card` | `backend/app/routes/patient_card.py` | Patient QR cards | ✅ |
| `/api/ai` | `backend/app/routes/ai.py` | AI services | ✅ |
| `/api/ai/telemetry` | `backend/app/routes/ai_telemetry.py` | AI telemetry | ✅ |
| `/api/stats` | `backend/app/routes/stats.py` | Statistics | ✅ |
| `/api/dashboard` | `backend/app/routes/dashboard.py` | Dashboard data | ✅ |
| `/api/tiers` | `backend/app/routes/tiers.py` | Subscription tiers | ✅ |
| `/api/compliance` | `backend/app/routes/compliance.py` | Compliance reporting | ✅ |
| `/api/identity` | `backend/app/routes/identity.py` | Identity resolution | ✅ |
| `/api/claims` | `backend/app/routes/claims.py` | Insurance claims | ✅ |
| `/api/clinical` | `backend/app/routes/clinical.py` | Clinical services | ✅ |
| `/api/care-continuum` | `backend/app/routes/care_continuum.py` | Care continuity | ✅ |
| `/api/ehr` | `backend/app/routes/ehr.py` | EHR integration | ✅ |
| `/api/ehr/fhir` | `backend/app/routes/ehr_fhir.py` | FHIR API | ✅ |
| `/api/edge` | `backend/app/routes/edge.py` | Edge platform | ✅ |
| `/api/admin` | `backend/app/routes/admin.py` | Admin functions | ✅ |
| `/api/security` | `backend/app/routes/security.py` | Security settings | ✅ |
| `/api/mobile` | `backend/app/routes/mobile.py` | Mobile API | ✅ |
| `/api/notifications` | `backend/app/routes/notifications.py` | Notifications | ✅ |
| `/api/integrations` | `backend/app/routes/integrations.py` | Integrations | ✅ |
| `/api/hospital` | `backend/app/routes/hospital.py` | Hospital integration | ✅ |
| `/api/consent` | `backend/app/routes/consent.py` | Consent management | ✅ |
| `/api/batch` | `backend/app/routes/batch.py` | Batch operations | ✅ |
| `/api/clinical-orders` | `backend/app/routes/clinical_orders.py` | Clinical orders | ✅ |
| `/api/clinical-quality` | `backend/app/routes/clinical_quality.py` | Clinical quality | ✅ |
| `/api/clinical-documentation` | `backend/app/routes/clinical_documentation.py` | Clinical docs | ✅ |
| `/api/national-data` | `backend/app/routes/national_data.py` | National data | ✅ |
| `/api/national-identity` | `backend/app/routes/national_identity.py` | National identity | ✅ |
| `/api/citizen-portal` | `backend/app/routes/citizen_portal.py` | Citizen portal API | ✅ |
| `/api/device-results` | `backend/app/routes/device_results.py` | Device results | ✅ |
| `/api/id-scan` | `backend/app/routes/id_scan.py` | ID scanning | ✅ |
| `/api/insurance` | `backend/app/routes/insurance.py` | Insurance API | ✅ |
| `/api/setup` | `backend/app/routes/setup.py` | Lab setup | ✅ |
| `/api/optimizer` | `backend/app/routes/optimizer.py` | System optimizer | ✅ |
| `/api/qr` | `backend/app/routes/qr.py` | QR code generation | ✅ |
| `/api/mpi` | MPI service API | MPI resolution | ✅ |

### 2.2 Internal / Health Endpoints

| Path | Purpose | Module |
|------|---------|--------|
| `/health` | Liveness | `backend/app/main.py` |
| `/health/live` | Liveness | `backend/app/main.py` |
| `/health/ready` | Readiness (Docker healthcheck) | `backend/app/main.py` |
| `/health/status` | Diagnostic status | `backend/app/main.py` |
| `/health/deep` | Full diagnostic | `backend/app/main.py` |
| `/metrics/prom` | Prometheus metrics | `backend/app/routes/metrics.py` |
| `/kernel/status` | Kernel health | `backend/app/kernel/routes.py` |
| `/kernel/services` | Registered services | `backend/app/kernel/routes.py` |
| `/kernel/capabilities` | Registered capabilities | `backend/app/kernel/routes.py` |
| `/kernel/plugins` | Installed plugins | `backend/app/kernel/routes.py` |

### 2.3 Event API (Outbox / Event Bus)

| Event Channel | Publisher | Consumer(s) | Type |
|---------------|-----------|-------------|------|
| `order.*` | Order Service | Outbox → National, Notifications, EHR | Domain event |
| `result.*` | Result Service | Outbox → AI, Clinical, Notifications | Domain event |
| `patient.*` | Patient Service | Outbox → MPI, National | Domain event |
| `citizen.*` | MPI Service | Outbox → National | Domain event |
| `clinical.*` | Clinical Engine | Outbox → Quality, Analytics | Domain event |

### 2.4 API Documentation Endpoints

| Path | Purpose | Protected |
|------|---------|-----------|
| `/docs` | Swagger UI | ✅ (DocsAuthMiddleware in production) |
| `/redoc` | ReDoc UI | ✅ (DocsAuthMiddleware in production) |
| `/openapi.json` | OpenAPI spec | ✅ (DocsAuthMiddleware in production) |

---

## 3. Service Catalog Index

| Service | Module | Domain | Status |
|---------|--------|--------|--------|
| Order Service | `backend/app/services/order_service.py` | Laboratory | 🟢 PRODUCTION |
| Patient Service | `backend/app/services/patient_service.py` | Laboratory | 🟢 PRODUCTION |
| Outbox Service | `backend/app/services/outbox_service.py` | Platform | 🟢 PRODUCTION |
| Audit Service | `backend/app/services/audit_service.py` | Security | 🟢 PRODUCTION |
| MPI Service | `backend/app/services/mpi/` | National | 🟢 PRODUCTION |
| Citizen Service | `backend/app/national/services/citizen_service.py` | National | 🟢 PRODUCTION |
| Identity Service | `backend/app/services/identity_service.py` | Security | 🟢 PRODUCTION |
| Clinical Engine | `backend/app/services/clinical_engine.py` | Clinical | 🟢 PRODUCTION |
| Clinical Intelligence | `backend/app/services/clinical_intelligence.py` | Clinical | 🟡 BETA |
| Clinical State | `backend/app/services/clinical_state.py` | Clinical | 🟢 PRODUCTION |
| Clinical Service | `backend/app/services/clinical_service.py` | Clinical | 🟢 PRODUCTION |
| Interpretation | `backend/app/services/interpretation.py` | AI | 🟢 PRODUCTION |
| Ali Reza Engine | `backend/app/services/ali_reza_engine.py` | AI | 🟡 BETA |
| SAMIR Engine | `backend/app/services/samir_engine.py` | AI | 🟡 BETA |
| Epidemiology | `backend/app/services/epidemiology.py` | Public Health | 🟡 BETA |
| EHR Service | `backend/app/services/ehr_service.py` | Integration | 🟢 PRODUCTION |
| Patient Card | `backend/app/services/patient_card.py` | Platform | 🟢 PRODUCTION |
| PDF Report | `backend/app/services/pdf_report.py` | Platform | 🟢 PRODUCTION |
| Data Platform | `backend/app/services/data_platform_service.py` | Analytics | 🟡 BETA |
| Claims Service | `backend/app/services/claims_service.py` | Financial | 🟡 BETA |
| Hospital Service | `backend/app/services/hospital_service.py` | Integration | 🟡 BETA |
| Care Continuum | `backend/app/services/care_continuum_service.py` | Clinical | 🟡 BETA |
| Critical Alerts | `backend/app/services/critical_alerts.py` | Clinical | 🟢 PRODUCTION |
| Notification Service | `backend/app/notifications/service.py` | Platform | 🟢 PRODUCTION |
| Identity Matching | `backend/app/services/identity_matching.py` | National | 🟢 PRODUCTION |
| Encounter Service | `backend/app/national/services/encounter_service.py` | National | 🟡 BETA |
| Family Service | `backend/app/national/services/family_service.py` | National | 🟡 BETA |
| Reference Service | `backend/app/national/services/reference_service.py` | National | 🟡 BETA |

---

## 4. Data Dictionary

### 4.1 Domain Data Elements

| Element | Type | Domain | Definition | PII |
|---------|------|--------|------------|-----|
| `lab_id` | Integer | Laboratory | Tenant-scoped identifier | ❌ |
| `patient_id` | Integer | Laboratory | Local patient identifier | ❌ |
| `citizen_ulid` | String | National | Canonical citizen identifier | ❌ |
| `order_id` | Integer | Laboratory | Order identifier | ❌ |
| `result_id` | Integer | Laboratory | Result identifier | ❌ |
| `sample_id` | Integer | Laboratory | Sample identifier | ❌ |
| `national_id_hash` | String | National | HMAC-SHA256 of national ID | ✅ (hashed) |
| `health_number` | String | National | National health number | ✅ |
| `first_name` | String | Demographic | Patient first name (Arabic) | ✅ |
| `father_name` | String | Demographic | Patient father name | ✅ |
| `last_name` | String | Demographic | Patient last name | ✅ |
| `date_of_birth` | Date | Demographic | Patient DOB | ✅ |
| `phone` | String | Contact | Patient phone number | ✅ |
| `email` | String | Contact | Patient email | ✅ |
| `status` | String | State | Order/result status | ❌ |
| `version` | Integer | Concurrency | Optimistic lock version | ❌ |
| `created_at` | DateTime | Audit | Record creation timestamp | ❌ |
| `updated_at` | DateTime | Audit | Record update timestamp | ❌ |
| `deleted_at` | DateTime | Audit | Soft delete timestamp | ❌ |

### 4.2 Value Domains

| Domain | Values | Location |
|--------|--------|----------|
| Order status | `pending`, `completed`, `validated`, `cancelled` | `backend/app/domain/order_state.py` |
| Gender | `male`, `female`, `unknown` | `backend/app/national/enums.py` |
| Identity status | `active`, `merged`, `review`, `deceased` | `backend/app/national/enums.py` |
| Marital status | `single`, `married`, `divorced`, `widowed`, `unknown` | `backend/app/national/enums.py` |
| Circuit state | `closed`, `open`, `half_open` | `backend/app/core/self_healing.py` |
| Degradation level | `none`, `L1_cache_heavy`, `L2_read_only`, `L3_critical_only` | `backend/app/core/self_healing.py` |
| Feature tier | `starter`, `growth`, `enterprise` | `backend/app/core/feature_flags.py` |
| Capability status | `draft`, `active`, `deprecated`, `retired` | `backend/app/kernel/types.py` |
| Outbox status | `pending`, `processing`, `done`, `failed` | `backend/app/models/outbox.py` |
| Data trust level | `enrichment`, `non_critical`, `critical` | `backend/app/gateways/base.py` |
| Break glass reason | `emergency`, `patient_safety`, `public_safety`, `legal`, `consent_obtained` | `backend/app/national/security/break_glass.py` |

---

## 5. FHIR Catalog

### 5.1 FHIR Resources

| Resource | GULA Entity | File | R4 | R5 |
|----------|-------------|------|----|----|
| Patient | `Citizen` / `Patient` | `backend/app/national/fhir/patient.py` | ✅ | ✅ |
| Practitioner | `LabUser` / `Practitioner` | `backend/app/national/fhir/practitioner.py` | ✅ | ✅ |
| Organization | `Lab` / `Organization` | `backend/app/national/fhir/organization.py` | ✅ | ✅ |
| Observation | `LabResult` | `backend/app/national/fhir/observation.py` | ✅ | ✅ |
| Encounter | `Visit` / `Encounter` | `backend/app/national/fhir/encounter.py` | ✅ | ✅ |
| Bundle | Bulk operations | `backend/app/national/fhir/bundle.py` | ✅ | ✅ |
| ValueSet | Terminology | `backend/app/national/fhir/terminology.py` | ✅ | ✅ |
| OperationOutcome | Error responses | `backend/app/national/fhir/validation.py` | ✅ | ✅ |
| DiagnosticReport | Lab reports | `backend/app/lims/fhir_mappers.py` | ⏳ | ⏳ |
| ServiceRequest | Lab orders | `backend/app/lims/fhir_mappers.py` | ⏳ | ⏳ |
| DocumentReference | Clinical docs | Future | ❌ | ❌ |

### 5.2 FHIR Operations

| Operation | Endpoint | Implementation |
|-----------|----------|----------------|
| `read` | `GET /fhir/{resource}/{id}` | Resource-specific handler |
| `search` | `GET /fhir/{resource}?{params}` | `backend/app/national/fhir/search.py` |
| `create` | `POST /fhir/{resource}` | Resource-specific handler |
| `update` | `PUT /fhir/{resource}/{id}` | Resource-specific handler |
| `delete` | `DELETE /fhir/{resource}/{id}` | Resource-specific handler (soft) |
| `$validate` | `POST /fhir/{resource}/$validate` | `backend/app/national/fhir/validation.py` |

### 5.3 FHIR Profiles

| Profile | Target | Status |
|---------|--------|--------|
| US Core Patient | Patient resource | ⏳ Partial |
| US Core Practitioner | Practitioner resource | ⏳ Partial |
| US Core Organization | Organization resource | ⏳ Partial |
| US Core Observation | Observation (lab) | ⏳ Partial |
| IPA Patient | Cross-border patient | ❌ Planned |

### 5.4 FHIR Search Parameters

| Parameter | Supported Resources | Implementation |
|-----------|--------------------|----------------|
| `_id` | All | `backend/app/national/fhir/search.py` |
| `identifier` | Patient, Practitioner, Organization | `backend/app/national/fhir/search.py` |
| `name` | Patient, Practitioner | `backend/app/national/fhir/search.py` |
| `birthdate` | Patient | `backend/app/national/fhir/search.py` |
| `gender` | Patient | `backend/app/national/fhir/search.py` |
| `_lastUpdated` | All | `backend/app/national/fhir/search.py` |
| `_count` | All | `backend/app/national/fhir/search.py` |
| `_page` | All | `backend/app/national/fhir/search.py` |
| `_sort` | All | `backend/app/national/fhir/search.py` |
| `_include` | All | `backend/app/national/fhir/search.py` |

---

## 6. Security Catalog Index

### 6.1 Security Controls by Category

| Category | Control | File |
|----------|---------|------|
| Authentication | JWT creation | `backend/app/security/auth.py` |
| Authentication | JWT validation | `backend/app/security/dependencies.py` |
| Authentication | Password hashing | `shared/auth/passwords.py` |
| Authentication | Token revocation | `backend/app/security/auth.py:43-52` |
| Authorization | RBAC | `backend/app/security/rbac.py` |
| Authorization | ABAC | `backend/app/security/abac.py` |
| Authorization | National ABAC | `backend/app/national/security/abac.py` |
| Authorization | Break glass | `backend/app/national/security/break_glass.py` |
| Authorization | Purpose of use | `backend/app/national/security/purpose_of_use.py` |
| Authorization | Minimum necessary | `backend/app/national/security/minimum_necessary.py` |
| Authorization | Minor protection | `backend/app/national/security/minor_protection.py` |
| Authorization | VIP protection | `backend/app/national/security/vip_protection.py` |
| Authorization | Emergency access | `backend/app/national/security/emergency_access.py` |
| Authorization | Consent enforcement | `backend/app/security/consent_dep.py` |
| Authorization | Tenant isolation | All routes (lab_id filter) |
| Encryption | PII encryption | `shared/security/encryption.py` |
| Encryption | NID hashing | `backend/app/security/encryption.py` |
| Encryption | Patient card tokens | `backend/app/services/patient_card.py` |
| Encryption | Config validation | `backend/app/config.py:_is_weak_secret` |
| Rate Limiting | Rate limiter | `backend/app/security/rate_limit.py` |
| Rate Limiting | Concurrency limit | `backend/app/main.py:ConcurrencyLimitMiddleware` |
| Rate Limiting | API firewall | `backend/app/firewall/api_firewall.py` |
| Audit | Audit logging | `backend/app/audit/audit_log.py` |
| Audit | Hash chain | `backend/app/models/audit_log.py:24` |
| Audit | MPI merge audit | MPI module |
| Resilience | Circuit breaker | `backend/app/core/self_healing.py` |
| Resilience | Retry | `backend/app/core/resilience.py` |
| Resilience | Idempotency | `backend/app/core/idempotency.py` |
| Resilience | Kill switch | `backend/app/core/kill_switch.py` |
| Monitoring | Health endpoints | `backend/app/main.py` |
| Monitoring | Metrics | `backend/app/routes/metrics.py` |
| Monitoring | Telemetry | `shared/observability/tracer.py` |
| Gateway | Gateway base | `backend/app/gateways/base.py` |
| Gateway | NID gateway | `backend/app/gateways/national_identity_gateway.py` |
| Gateway | Insurance gateway | `backend/app/gateways/insurance_gateway.py` |
| Gateway | Residency gateway | `backend/app/gateways/residency_gateway.py` |
| Gateway | Cloudflare gateway | `backend/app/gateways/cloudflare_gateway.py` |

---

## 7. Operations Catalog Index

### 7.1 Operational Procedures

| Procedure | Command | File |
|-----------|---------|------|
| Deploy | `make up` | `Makefile` |
| Stop | `make down` | `Makefile` |
| Restart | `make restart` | `Makefile` |
| Backup | `make backup` | `Makefile` |
| Health check | `make health` | `Makefile` |
| Deep health | `make health-deep` | `Makefile` |
| Scale | `make scale REPLICAS=5` | `Makefile` |
| Secrets gen | `make secrets-gen` | `Makefile` |
| DB shell | `make db-shell` | `Makefile` |
| Redis CLI | `make redis-cli` | `Makefile` |
| Lint | `make lint` | `Makefile` |
| Test | `make test` | `Makefile` |
| CI | `make ci` | `Makefile` |
| Kill switch on | `make kill-switch-on` | `Makefile` |
| Kill switch off | `make kill-switch-off` | `Makefile` |

### 7.2 Monitoring Endpoints

| Endpoint | Purpose | Always Available |
|----------|---------|-----------------|
| `/health` | Liveness | ✅ |
| `/health/live` | Liveness | ✅ |
| `/health/ready` | Readiness | ✅ |
| `/health/status` | Diagnostic | ✅ |
| `/health/deep` | Full diagnostic | ✅ |
| `/metrics/prom` | Prometheus | ✅ (authenticated) |

### 7.3 Alert Destinations

| Alert | Level | Destination | Config |
|-------|-------|-------------|--------|
| System RED | P0 | Telegram, Slack, SMS | `ALERT_WEBHOOK_URL` |
| System YELLOW | P1 | Telegram, Slack | `ALERT_WEBHOOK_URL` |
| Circuit OPEN | P1 | Telegram, Slack | Monitoring |
| High latency | P1 | Telegram, Slack | Monitoring |
| Backup failure | P1 | Slack | CRON |

---

## 8. ADR Catalog

### 8.1 Architecture Decision Records

| ADR | Title | Status | Location |
|-----|-------|--------|----------|
| ADR-001 | Three-Layer Architecture (LIMS/National/Government) | ACCEPTED | `docs/adr/` |
| ADR-002 | Transactional Outbox Pattern | ACCEPTED | `docs/adr/` |
| ADR-003 | Modular Monolith with Service Decomposition | ACCEPTED | `docs/adr/` |
| ADR-004 | JWT Authentication with Redis Blacklist | ACCEPTED | `docs/adr/` |
| ADR-005 | ULID Primary Keys for National Entities | ACCEPTED | `docs/adr/` |
| ADR-006 | FHIR R4/R5 Dual Support | ACCEPTED | `docs/adr/` |
| ADR-007 | Circuit Breaker for External Dependencies | ACCEPTED | `docs/adr/` |
| ADR-008 | Circuit Breaker for External Dependencies | ACCEPTED | `docs/adr/` |
| ADR-009 | CQRS for EHR Module | ACCEPTED | `docs/adr/` |
| ADR-010 | Feature Flags with Tier Matrix | ACCEPTED | `docs/adr/` |

### 8.2 National Layer ADR

| ADR | Title | Status | Location |
|-----|-------|--------|----------|
| N-ADR-001 | National Layer Architecture | ACCEPTED | `backend/app/national/ADR.md` |

### 8.3 ADR Status Legend

| Status | Meaning |
|--------|---------|
| PROPOSED | Under review |
| ACCEPTED | Approved and implemented |
| DEPRECATED | Replaced by newer ADR |
| SUPERSEDED | Superseded by newer ADR |

---

## 9. Cross-Reference Matrix

### 9.1 Domain ↔ Service ↔ Route

| Domain | Primary Service | Primary Route | Database Table |
|--------|----------------|---------------|----------------|
| Laboratory | Order Service | `routes/clinical_orders.py` | `lab_orders` |
| Laboratory | Patient Service | `routes/patients.py` | `patients` |
| Laboratory | Result Service | `routes/results.py` | `lab_results` |
| Laboratory | Sample Service | `routes/samples.py` | `samples` |
| National | Citizen Service | `routes/national_data.py` | `national_citizens` |
| National | MPI Service | `routes/identity.py` | `identity_claims` |
| Clinical | Clinical Engine | `routes/clinical.py` | `clinical_*` |
| Clinical | Clinical Intelligence | `routes/ai.py` | `ai_interactions` |
| EHR | EHR Service | `routes/ehr_fhir.py` | FHIR views |
| Edge | Edge Service | `routes/edge.py` | `edge_*` |
| Financial | Claims Service | `routes/claims.py` | `claims` |
| Platform | Outbox Service | — | `outbox_events` |
| Security | Identity Service | `routes/login.py` | `lab_users` |
| Security | Audit Service | — | `audit_logs` |

### 9.2 Event ↔ Publisher ↔ Consumer

| Event | Publisher | Consumer(s) |
|-------|-----------|-------------|
| `order.created` | Order Service | Notifications, National |
| `order.completed` | Order Service | AI (interpretation) |
| `order.validated` | Order Service | Notifications, Claims |
| `result.finalized` | Result Service | AI, Clinical Engine |
| `result.validated` | Result Service | EHR, National |
| `patient.created` | Patient Service | MPI Service |
| `patient.updated` | Patient Service | MPI Service |
| `patient.merged` | MPI Service | National Service |
| `citizen.registered` | MPI Service | National Service |
| `citizen.merged` | MPI Service | National Service |
| `clinical.interpretation.completed` | Clinical Engine | Notifications |

### 9.3 Security Control ↔ Service ↔ Route

| Security Control | Enforced In | Applied To |
|-----------------|-------------|------------|
| JWT Auth | `security/dependencies.py` | All authenticated routes |
| RBAC | `security/rbac.py:require_role()` | Admin, management routes |
| ABAC | `security/abac.py:ABACEngine` | Sensitive data routes |
| Rate Limit | `security/rate_limit.py` | All API routes |
| Tenant Isolation | lab_id filter in queries | All laboratory routes |
| Feature Gate | `core/feature_flags.py:require_feature()` | Feature-gated routes |
| Idempotency | `core/idempotency.py:idempotency_check()` | POST create routes |
| Audit Log | `audit/audit_log.py` | All mutation routes |

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial knowledge integration |

**Review Cycle**: This document must be reviewed and updated quarterly or when significant architectural changes occur.
