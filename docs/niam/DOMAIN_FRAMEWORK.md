# DOMAIN_FRAMEWORK.md

> **PROGRAM-STABLE-004** — the permanent Domain Platform Framework.
> Generated: 2026-08-06T04:28:40+00:00

## Purpose

The Domain Platform Framework is the single reusable foundation that every current and future GULA healthcare module inherits. Every healthcare specialty is an independent Domain (GULA Laboratory, GULA Pharmacy, GULA Radiology, GULA Hospital, Blood Bank, Public Health, Insurance, Emergency, Research, and any future specialty).

## Non-Negotiable Invariants (Domain Sovereignty)

1. **Domain Sovereignty** — every Domain owns only itself.
2. **Shared Core** — every Domain consumes ONLY the official Shared Core.
3. **Zero Cross-Domain Administration** — no Domain manages another Domain.
4. **Zero Cross-Domain Database Access** — no Domain reads another Domain's database.
5. **Zero Business Logic Duplication** — shared logic lives only in Shared Core.

## Framework Layering

- **Shared Core** (platform) — Identity, Authentication, Authorization, Organizations, Audit, Notifications, Workflow Engine, Rule Engine, Barcode Engine, QR Engine, Search Engine, Reporting Framework, Document Engine, Files, Media, Scheduler, Localization, Monitoring, Logging, API Gateway, FHIR Engine, Event Bus, Settings.
- **Domain Layer** — each healthcare specialty declares its Domain Blueprint.
- **Cross-Domain Contract Layer** — versioned REST / FHIR / HL7 / events. Direct access is forbidden.
- **Workspace Layer** — each Domain binds to exactly ONE workspace type.

## Shared Core Catalog (Phase 2)

| Service | Provider | Description |
|---|---|---|
| identity | `backend/app/identity` | NIAM identity registry (person, enterprise, machine, guest). |
| authentication | `backend/app/identity/api/auth.py` | Authentication (password, passkeys, OTP, OAuth2, OIDC, smart cards). |
| authorization | `backend/app/identity/services/authorization_service.py` | RBAC + ABAC + workspace-scoped permission checks. |
| organizations | `backend/app/identity/models/niam_organization.py` | Ministry/Directorate/Hospital/Laboratory hierarchy + org guard. |
| audit | `backend/app/identity/models/audit.py` | Immutable, hash-chained audit log for every platform event. |
| notifications | `backend/app/notifications` | Push, email, SMS, in-app notification delivery. |
| workflow_engine | `backend/app/workflows` | Workflow engine for multi-step clinical and operational flows. |
| rule_engine | `shared/rules_engine` | Deterministic business/clinical rule engine. |
| barcode_engine | `shared/barcode` | Barcode generation and decoding. |
| qr_engine | `shared/qr` | QR generation and decoding. |
| search_engine | `backend/app/capabilities/search_service` | Unified search engine over platform records. |
| reporting_framework | `backend/app/capabilities/reporting_service` | Report generation framework (domain reports build on it). |
| document_engine | `backend/app/capabilities/document_management` | Clinical and administrative document management. |
| files | `shared/storage` | File storage and retrieval (MinIO / object storage). |
| media | `shared/storage` | Image and media asset handling. |
| scheduler | `shared/scheduler.py` | Recurring job scheduling (domain workflows consume it). |
| localization | `shared/localization.py` | Arabic-first localization and i18n. |
| monitoring | `backend/app/services/metrics_service.py` | Metrics, health checks, Prometheus endpoints. |
| logging | `shared/logging` | Structured logging and tracing. |
| api_gateway | `backend/app/routes` | Gateway routing, versioning, rate limiting. |
| fhir_engine | `backend/app/fhir` | FHIR R4 engine (resources, profiles, mappers, validation). |
| event_bus | `shared/events` | Event bus for async cross-domain events. |
| settings | `backend/app/config.py` | Platform configuration and settings. |

## Principles

- Every healthcare specialty is an independent Domain.
- No Domain owns another Domain.
- No Domain manages another Domain.
- No Domain reads another Domain's database.
- Everything shared lives only inside Shared Core.
- Every Domain is independently deployable, testable, certifiable, and maintainable.
- Backward compatibility is never broken.
- Infrastructure is never duplicated.
- Domain Sovereignty is never violated.

## Runtime Framework

The framework is implemented in `backend/app/domain_platform` with a DB-backed runtime (`niam_domain_*` tables), a REST API under `/niam/domains`, and lifecycle + certification engines. The governance engine (`scripts/domains`) shares the same implementation and publishes these documents.

## Documents

| Document | Purpose |
|---|---|
| DOMAIN_FRAMEWORK.md | Domain Platform Framework — architecture, sovereignty, and governance |
| DOMAIN_BLUEPRINT.md | Domain Blueprint — the official structure every Domain must follow |
| DOMAIN_CONTRACTS.md | Cross-Domain Contracts — the only legal communication channels |
| DOMAIN_ISOLATION_CERTIFICATION.md | Domain Isolation Certification — Phase 3 + Phase 7 validation |
| DOMAIN_LIFECYCLE.md | Domain Lifecycle — install, activate, suspend, upgrade, rollback, backup, restore |
| DOMAIN_VERSIONING.md | Domain Versioning — independent SemVer releases with backward compatibility |
| DOMAIN_REGISTRY.md | Domain Registry — the canonical catalog of every GULA Domain |
