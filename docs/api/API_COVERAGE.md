# GULA Platform — API Coverage Report

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Route Module Coverage](#2-route-module-coverage)
3. [Coverage Summary](#3-coverage-summary)
4. [FHIR Coverage](#4-fhir-coverage)
5. [Authentication Coverage](#5-authentication-coverage)
6. [OpenAPI Specification](#6-openapi-specification)
7. [API Version Matrix](#7-api-version-matrix)
8. [Endpoint Ownership](#8-endpoint-ownership)
9. [Security Classification](#9-security-classification)
10. [Performance Classification](#10-performance-classification)
11. [Test Coverage Matrix](#11-test-coverage-matrix)
12. [Deprecation Status](#12-deprecation-status)
13. [Cross References](#13-cross-references)
14. [Related Documents](#14-related-documents)

## 1. API Overview

| Metric | Value |
|--------|-------|
| Total Route Modules | 54 |
| Total Endpoints (counted) | ~610 |
| Authentication | JWT (HS256) + RBAC |
| API Gateway | nginx (rate limiting, TLS) |
| OpenAPI | Auto-generated at /docs and /redoc |
| FHIR R4 | Available at /fhir/* |
| Rate Limiting | Auth: 10/min, Public: 30/min |
| Max Body Size | 10 MB (configurable) |

**Prefix conventions:**

- `/ehr/*` — Clinical document architecture
- `/hospital/*` — Hospital information system
- `/care-continuum/*` — Continuity of care
- `/clinical/*` — Medical knowledge & decision support
- `/national-data/*` — Analytics, MDM, governance
- `/national-data/streaming/*` — Real-time data feeds
- `/fhir/*` — HL7 FHIR R4 API

## 2. Route Module Coverage

| # | Module | File | Endpoints | Description | Auth | Status |
|---|--------|------|-----------|-------------|------|--------|
| 1 | admin | admin.py | 22 | System administration operations | JWT+Admin | Active |
| 2 | admin_log_level | admin_log_level.py | 2 | Dynamic log level management | JWT+Admin | Active |
| 3 | ai | ai.py | 11 | Clinical AI inference endpoints | JWT | Active |
| 4 | ai_platform | ai_platform.py | 23 | AI platform orchestration & model management | JWT | Active |
| 5 | ai_telemetry | ai_telemetry.py | 6 | AI model telemetry & monitoring | JWT | Active |
| 6 | authorization | authorization.py | 27 | RBAC/ABAC role & permission management | JWT+Admin | Active |
| 7 | batch | batch.py | 1 | Batch operations for lab workflows | JWT | Active |
| 8 | canonical_patient | canonical_patient.py | 8 | Master Patient Index golden records | JWT | Active |
| 9 | care_continuum | care_continuum.py | 74 | Continuity of care records across episodes | JWT | Active |
| 10 | citizen_portal | citizen_portal.py | 6 | Citizen self-service portal API | JWT/Public | Active |
| 11 | claims | claims.py | 4 | Insurance claims processing | JWT | Feature-gated |
| 12 | clinical | clinical.py | 65 | Clinical knowledge & decision support | JWT | Active |
| 13 | clinical_documentation | clinical_documentation.py | 12 | Clinical notes & documentation | JWT | Active |
| 14 | clinical_orders | clinical_orders.py | 10 | Computerized Provider Order Entry (CPOE) | JWT | Active |
| 15 | clinical_quality | clinical_quality.py | 4 | Clinical quality metrics & reporting | JWT | Active |
| 16 | compliance | compliance.py | 11 | Regulatory compliance reporting | JWT | Active |
| 17 | consent | consent.py | 3 | Patient consent management | JWT | Active |
| 18 | critical_alerts | critical_alerts.py | 2 | Critical lab result alerting | JWT | Active |
| 19 | dashboard | dashboard.py | 2 | Dashboard data aggregation | JWT | Active |
| 20 | device_results | device_results.py | 1 | Lab instrument device bridge results | JWT | Active |
| 21 | edge | edge.py | 22 | Edge platform site management & sync | JWT | Active |
| 22 | ehr | ehr.py | 85 | Electronic Health Record management | JWT | Active |
| 23 | ehr_fhir | ehr_fhir.py | 25 | HL7 FHIR R4 API surface | JWT | Active |
| 24 | hospital | hospital.py | 39 | Hospital Information System (HIS) | JWT | Active |
| 25 | id_scan | id_scan.py | 1 | National ID/document scanning | JWT | Active |
| 26 | identity | identity.py | 2 | Identity provider management | JWT+Admin | Active |
| 27 | insurance | insurance.py | 1 | Insurance provider integration | JWT | Active |
| 28 | integrations | integrations.py | 2 | Third-party system integration management | JWT | Active |
| 29 | labs | labs.py | 5 | Laboratory management & configuration | JWT | Active |
| 30 | login | login.py | 2 | Authentication (JWT token issuance) | Public | Active |
| 31 | metrics | metrics.py | 2 | Prometheus metrics export | Bearer Token | Active |
| 32 | mfa | mfa.py | 9 | Multi-factor authentication management | JWT | Active |
| 33 | mobile | mobile.py | 2 | Mobile-specific API endpoints | JWT | Active |
| 34 | national_data | national_data.py | 34 | National health data analytics & MDM | JWT | Active |
| 35 | national_identity | national_identity.py | 1 | National ID/health ID lookup | JWT | SNDHS-gated |
| 36 | national_streaming | national_streaming.py | 5 | Real-time national data streaming | JWT | Active |
| 37 | notifications | notifications.py | 2 | Push notification delivery | JWT | Active |
| 38 | oauth2 | oauth2.py | 7 | OAuth 2.0 provider (authorization code flow) | JWT/Public | Active |
| 39 | optimizer | optimizer.py | 2 | Platform performance optimization | JWT+Admin | Active |
| 40 | password_reset | password_reset.py | 3 | Password reset flow | Public | Active |
| 41 | patient_card | patient_card.py | 5 | QR-backed digital patient cards | JWT/Public | Active |
| 42 | patients | patients.py | 6 | Patient demographic management | JWT | Active |
| 43 | qr | qr.py | 2 | QR code generation utilities | JWT | Active |
| 44 | quality_control | quality_control.py | 4 | Lab quality control management | JWT | Active |
| 45 | register | register.py | 4 | User self-registration | Public | Active |
| 46 | results | results.py | 12 | Lab result entry & retrieval | JWT | Active |
| 47 | saml | saml.py | 2 | SAML 2.0 SSO authentication | Public | Active |
| 48 | samples | samples.py | 4 | Specimen/sample tracking | JWT | Active |
| 49 | security | security.py | 1 | Security policy configuration | JWT+Admin | Active |
| 50 | service_accounts | service_accounts.py | 4 | Machine-to-machine service accounts | JWT+Admin | Active |
| 51 | setup | setup.py | 1 | Initial platform setup wizard | Public | Active |
| 52 | stats | stats.py | 6 | Statistics & trends API | JWT | Active |
| 53 | test_results | test_results.py | 6 | Individual test result management | JWT | Active |
| 54 | tiers | tiers.py | 8 | Subscription tier management | JWT+Admin | Active |

## 3. Coverage Summary

| Category | Endpoints |
|----------|-----------|
| Core LIMS (labs, patients, results, samples, test_results, batch) | ~34 |
| Admin & Security (admin, authorization, identity, service_accounts, security, optimizer, tiers, setup, metrics, admin_log_level) | ~71 |
| EHR/Clinical (ehr, ehr_fhir, clinical, clinical_documentation, clinical_orders, clinical_quality, care_continuum) | ~275 |
| Hospital (hospital) | ~39 |
| National Data (national_data, national_identity, national_streaming, citizen_portal) | ~46 |
| Authentication (login, register, password_reset, mfa, oauth2, saml) | ~27 |
| AI (ai, ai_platform, ai_telemetry) | ~40 |
| Device & Edge (device_results, edge) | ~23 |
| Other (claims, compliance, consent, critical_alerts, dashboard, id_scan, insurance, integrations, mobile, notifications, patient_card, qr, quality_control, stats, canonical_patient) | ~55 |
| **Total (counted)** | **~610** |

## 4. FHIR Coverage

FHIR R4 resources implemented via `ehr_fhir.py` (25 endpoints):

| Resource | Operations |
|----------|-----------|
| Patient | Read, Search, Create |
| Encounter | Read, Search, Create |
| Condition | Read, Search |
| Observation | Read, Search, Create |
| MedicationRequest | Read, Search |
| MedicationStatement | Read, Search |
| CarePlan | Read, Search |
| Procedure | Read, Search |
| AllergyIntolerance | Read, Search |
| Immunization | Read, Search |
| DocumentReference | Read, Search |
| ConceptMap, ValueSet, CodeSystem | Terminology services |

## 5. Authentication Coverage

- **All production endpoints** require JWT authentication (HS256-signed tokens)
- **Public endpoints:** `/health*`, `/docs` (if enabled), login, register, password_reset, patient card scan (limited), SAML SSO
- **Metrics endpoint** (`/metrics/prom`) requires `Bearer METRICS_BEARER_TOKEN`
- **RBAC roles:** 10 roles × 16 permissions (admin, lab_manager, lab_technician, doctor, nurse, receptionist, phlebotomist, viewer, compliance_officer, ministry_officer)

## 6. OpenAPI Specification

- **Live spec:** `/openapi.json`
- **Documentation UI:** `/docs` (Swagger UI), `/redoc` (ReDoc)
- **Export:** `/contracts/export/openapi.json`
- **Production:** Disabled by default (`ENABLE_API_DOCS` toggle)
- **Auth header:** All operations accept `Authorization: Bearer <token>`

## 7. API Version Matrix

| Version | Prefix | Routes | Status | Notes |
|---------|--------|--------|--------|-------|
| v1 | `/api/v1/*` | Majority of routes (login, admin, labs, patients, results, ehr, clinical, etc.) | **Active** | Primary API version |
| v2 | `/api/v2/*` | citizen_portal, select AI/edge endpoints | **Partial rollout** | New and migrated endpoints |
| unversioned | `/*` | health, docs, openapi.json, metrics | **Active** | Infrastructure & utility endpoints |
| FHIR R4 | `/fhir/*` | 12 FHIR resources via `ehr_fhir.py` | **Active** | HL7 FHIR R4 standard |

**Implementation:**
- Version prefix defined in each route module via `APIRouter(prefix=...)`
- `X-API-Version` response header set by middleware (based on request path)
- OpenAPI spec at `/openapi.json` documents both versions
- ADR-003 governs API versioning strategy (URL-path based, no Accept-header negotiation)

**Migration policy:**
- New development targets **v2** prefix
- **v1** routes maintain backward compatibility
- v1 → v2 migration tracked in `contracts/CHANGELOG.md`

## 8. Endpoint Ownership

The platform uses a **shared monolith ownership model** — all route modules are maintained by the core platform team. No `CODEOWNERS` file exists. Ownership is organized by domain area:

| Domain | Route Modules | Primary Steward |
|--------|---------------|-----------------|
| Core LIMS | labs, patients, results, samples, test_results, batch, device_results, quality_control | LIMS Team |
| EHR / Clinical | ehr, ehr_fhir, clinical, clinical_documentation, clinical_orders, clinical_quality, care_continuum | Clinical Informatics Team |
| Hospital | hospital | Hospital Systems Team |
| National Data | national_data, national_identity, national_streaming, citizen_portal | National Data Team |
| Authentication | login, register, password_reset, mfa, oauth2, saml | Identity Team |
| Admin / Security | admin, authorization, identity, security, service_accounts, optimizer, tiers, admin_log_level | Platform Team |
| AI | ai, ai_platform, ai_telemetry | AI/ML Team |
| Device / Edge | edge, device_results | Edge Platform Team |
| Analytics | stats, dashboard | Analytics Team |
| Compliance | compliance, claims, consent | Compliance Team |
| Financial | tiers | Financial Team (Phase A schema-only) |
| Integrations | integrations, insurance, id_scan, mobile, notifications | Cross-functional |
| Patient Identity | canonical_patient, patient_card, qr | Patient Identity Team |

**Note:** This is a logical ownership map. All route code resides in `backend/app/routes/` and is accessible to the entire backend team.

## 9. Security Classification

Every endpoint is classified into one of five security tiers:

| Classification | Auth Requirement | Route Modules | Est. Count |
|---------------|-----------------|---------------|-----------|
| **Admin** | JWT + `is_admin` flag + RBAC `admin` role | admin, admin_log_level, authorization, identity, optimizer, security, service_accounts, tiers | ~46 |
| **Authenticated** | JWT (HS256) + RBAC role check | Majority of routes (ai, clinical, ehr, hospital, labs, patients, results, etc.) | ~500 |
| **Public** | No authentication required | login, register, password_reset, setup, `/health*`, `/docs` | ~12 |
| **Mixed** | Public read / JWT write | citizen_portal, patient_card (QR scan limited), oauth2 | ~18 |
| **Bearer Token** | `Authorization: Bearer <METRICS_BEARER_TOKEN>` | metrics | 2 |

**Security invariants (from CLAUDE.md):**
1. All patient-data queries MUST filter by `lab_id = current_user.lab_id` (tenant isolation)
2. All mutations MUST write to the audit log (SHA-256 hash chain)
3. Phone lookups MUST use exact match — never `LIKE` with user input
4. `/metrics/prom` MUST require `Bearer METRICS_BEARER_TOKEN` in production
5. Optimistic lock (`version` column) MUST be checked on every `LabResult` mutation
6. `patients.national_id` MUST be encrypted at rest — never stored in plaintext

## 10. Performance Classification

Route performance classified into three tiers based on load testing (`tests/test_stress.py`):

| Tier | Latency Target (p95) | Throughput | Example Routes |
|------|---------------------|-----------|----------------|
| **Normal** | < 200ms | 100+ req/s | labs, patients, samples, test_results, stats, qr, notifications |
| **Clinical** | < 500ms | 50+ req/s | ehr, clinical, clinical_documentation, care_continuum, results |
| **Heavy** | < 2000ms | 10+ req/s | analytics, national_data aggregations, AI inference, predictive stats |

**Key constraints:**
- `ConcurrencyLimitMiddleware` caps in-flight requests at 50 per worker (default 3 workers)
  - Clinical writes (`/results`, `/orders`, `/samples`, `/critical-alerts`) are **exempt** from shedding
- Adaptive concurrency loop halves `_MAX_CONCURRENT` on 2 slow DB readings (>300ms); restores after 3 fast (<150ms)
- Max body size 10 MB (configurable via `MAX_REQUEST_BODY_MB`)
- Rate limiting: 10/min (auth), 30/min (public), 100+/min (authenticated)
- DB pool: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` = 3 × (6 + 12) = 54, within Postgres default 100

## 11. Test Coverage Matrix

Test coverage across route modules (85+ test files, 2,148+ tests):

| Route Module | Test File(s) | Coverage Highlights |
|-------------|-------------|---------------------|
| Admin | `test_admin.py` | CRUD operations, permission enforcement |
| AI | `test_ai.py`, `test_ai_platform.py`, `test_system_improvements.py` | Inference, model management, clinical interpretation |
| Authorization | `test_authorization.py`, `test_abac.py` | RBAC/ABAC enforcement, permission matrix |
| Clinical | `test_clinical.py`, `test_clinical_safety.py` | Decision support, clinical safety invariants |
| Compliance | `test_comprehensive.py` | Regulatory reporting |
| Edge | `test_edge_platform.py` | Site synchronization, offline support |
| EHR / FHIR | `test_comprehensive.py` | CRUD, FHIR R4 resource operations |
| Feature Flags | `test_feature_flags.py` | Per-tenant feature matrix |
| Kernel | `test_kernel/` (38 files) | Plugin system, event bus, background tasks |
| Patient Card | `test_patient_card.py` | QR token generation, HMAC verification, scanning |
| Security / Auth | `test_security.py`, `test_stability_assertions.py` | JWT, auth flows, encryption, data integrity |
| Stats | `test_stats.py`, `test_system_improvements.py` | Aggregation queries |
| Stress / Chaos | `test_stress.py`, `test_chaos_survival.py`, `test_migration_resilience.py` | Performance, resilience, migration integrity |
| Tenant Isolation | `test_tenant_isolation_matrix.py` | Multi-tenant isolation for all data routes |

**Multi-route test files:**
- `test_comprehensive.py` — Full integration tests across all major routes
- `test_system_improvements.py` — Clinical interpretation, intelligence APIs, stats
- `test_stability_assertions.py` — Data integrity checks across routes

**CI pipeline testing (`.github/workflows/ci.yml`):**
1. `syntax-gate` — py_compile + flake8 E9/F821 on every push
2. `migration-check` — alembic upgrade head on fresh postgres, verify required tables, downgrade -1 + upgrade head
3. `test` — pytest against postgres:17-alpine + redis:7-alpine
4. `security-scan` — safety (CVE) + bandit -ll -ii

## 12. Deprecation Status

| Status | Count | Notes |
|--------|-------|-------|
| **Active** | ~610 endpoints | All currently deployed endpoints are active |
| **Deprecated** | 0 | No routes marked with `@deprecated` decorator or deprecation headers |
| **Sunset** | 0 | No `Sunset` HTTP headers implemented |

The compliance route (`compliance.py`) explicitly reports no deprecated endpoints. API version migration from v1 → v2 is tracked in `contracts/CHANGELOG.md` and ADR-003.

**Deprecation Policy (planned):**
- Deprecated endpoints will receive a `Sunset` HTTP header with migration timeline
- Endpoints maintained for 6 months after deprecation announcement
- Removal documented in CHANGELOG.md and API migration guides

## 13. Cross References

| Resource | Location | Description |
|----------|----------|-------------|
| OpenAPI (live) | `/openapi.json` | Auto-generated OpenAPI 3.0 specification |
| Swagger UI | `/docs` | Interactive API documentation (production-gated) |
| ReDoc | `/redoc` | Alternative API documentation UI (production-gated) |
| OpenAPI Export | `contracts/export/openapi.json` | Static export of OpenAPI spec |
| API Changelog | `contracts/CHANGELOG.md` | Version history and migration notes |
| ADR-003 | `docs/adr/ADR-003-api-versioning.md` | API versioning strategy decision record |
| ADR-007 | `docs/adr/ADR-007-fhir-integration.md` | FHIR R4 integration decision record |
| Route Architecture | `backend/app/routes/README.md` | Route module architecture overview |
| Security Spec | `docs/security/API_SECURITY.md` | API security requirements and threat model |
| Rate Limiting | `backend/app/firewall/` | Rate limiting configuration |
| Concurrency Model | `backend/app/main.py` | Concurrency limit middleware + adaptive loop |
| API Gateway | `config/nginx/` | nginx gateway configuration (TLS, rate limiting) |
| OpenAPI Config | `backend/app/config.py` | `OPENAPI` env vars for docs toggle |

## 14. Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| API Catalog | `docs/national/API_CATALOG.md` | Full endpoint catalog with method/path/description tables |
| Routes README | `backend/app/routes/README.md` | Routes architecture overview |
| CLAUDE.md | `CLAUDE.md` | Security invariants, middleware stack, key files |
| App Initialization | `backend/app/main.py` | App init, health endpoints, middleware registration, background loops |
| App Factory | `backend/app/factory.py` | Application factory and middleware registration order |
| API Security | `docs/security/API_SECURITY.md` | API security requirements and threat model |
| OpenAPI Config | `backend/app/config.py` | OpenAPI toggle and documentation configuration |
| Test Suite | `backend/tests/` | 85+ test files, 2,148+ tests |
| CI Pipeline | `.github/workflows/ci.yml` | syntax-gate → migration-check → lint → test → security-scan → build-and-push |
| ADR-003 | `docs/adr/` | API versioning strategy decision record |
