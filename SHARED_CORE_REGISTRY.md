# SHARED_CORE_REGISTRY — The ONE authoritative Shared Core

> PROGRAM-ALPHA Phase 2 | regenerated 2026-08-07
> **50 services, each with EXACTLY ONE authoritative provider.**
> Domains consume these; they never rebuild them.

## 1. Principles

1. **Everything reusable exists once.** A service appears in this registry only
   if exactly one authoritative provider exists.
2. **Domains own business logic; Shared Core owns infrastructure.** A Domain
   that instantiates `Fernet`, a task queue, an engine, or an event bus instead
   of consuming the registry fails certification.
3. **Replacement is swappable.** Every entry is a replaceable module — no
   vendor coupling, self-hosted first, open source first.
4. **Legacy duplicates are tracked, never grown.** The Architecture
   Constitution scan fails PRs that introduce a new implementation of any
   registry service outside its provider.

## 2. The registry

| Service | Authoritative provider | Responsibility |
|---|---|---|
| `identity` | `backend/app/identity` | NIAM identity registry (person, enterprise, machine, guest). |
| `authentication` | `backend/app/identity/api/auth.py` | Authentication (password, passkeys, OTP, OAuth2, OIDC, smart cards). |
| `authorization` | `backend/app/identity/services/authorization_service.py` | RBAC + ABAC + workspace-scoped permission checks. |
| `organizations` | `backend/app/identity/models/niam_organization.py` | Ministry/Directorate/Hospital/Laboratory hierarchy + org guard. |
| `users` | `backend/app/identity/api/accounts.py` | User/account registry and lifecycle. |
| `sessions` | `backend/app/identity/api/sessions.py` | Session registry, workspace binding, max concurrent enforcement. |
| `audit` | `backend/app/identity/models/audit.py` | Immutable, hash-chained audit log for every platform event. |
| `rbac` | `shared/rbac/permissions.py` | Role-based access control primitives. |
| `abac` | `backend/app/security/abac.py` | Attribute-based access control (subject/resource/context attributes). |
| `encryption` | `shared/security/encryption.py` | Symmetric/asymmetric encryption and at-rest protection. |
| `digital_signature` | `shared/security/hmac.py` | HMAC signatures, integrity and signing primitives. |
| `mfa` | `shared/auth/mfa.py` | Multi-factor authentication primitives (TOTP/OTP). |
| `auth_primitives` | `shared/auth` | JWT, password hashing and passkey/WebAuthn primitives. |
| `service_accounts` | `backend/app/security/service_accounts.py` | Machine/service identity and credentials. |
| `notifications` | `backend/app/notifications` | Push, email, SMS, in-app notification delivery. |
| `workflow_engine` | `backend/app/workflows` | Workflow engine for multi-step clinical and operational flows. |
| `rule_engine` | `shared/rules_engine` | Deterministic business/clinical rule engine. |
| `barcode_engine` | `shared/barcode` | Barcode generation and decoding. |
| `qr_engine` | `shared/qr` | QR generation and decoding. |
| `search_engine` | `backend/app/capabilities/search_service` | Unified search engine over platform records. |
| `reporting_framework` | `backend/app/capabilities/reporting_service` | Report generation framework (domain reports build on it). |
| `document_engine` | `backend/app/capabilities/document_management` | Clinical and administrative document management. |
| `files` | `shared/storage` | File storage and retrieval (MinIO / object storage). |
| `media` | `shared/storage` | Image and media asset handling. |
| `pdf_engine` | `shared/pdf/generator.py` | PDF generation for reports, labels and documents. |
| `printing` | `shared/printing/printer.py` | Label/report printing primitives. |
| `payments` | `shared/payments.py` | Payment processing primitives (country-agnostic gateways). |
| `scheduler` | `shared/scheduler.py` | Recurring job scheduling (domain workflows consume it). |
| `event_bus` | `shared/events` | Event bus for async cross-domain events. |
| `api_gateway` | `backend/app/routes` | Gateway routing, versioning, rate limiting. |
| `api_schemas` | `shared/schemas` | Shared pagination/response schemas for stable API contracts. |
| `validators` | `shared/validators/common.py` | Cross-cutting input and value validators. |
| `localization` | `shared/localization.py` | Arabic-first localization and i18n. |
| `design_system` | `shared/design_system` | RTL-first design tokens and components. |
| `config_loader` | `shared/config/loader.py` | Environment-aware configuration loading. |
| `settings` | `backend/app/config.py` | Platform configuration and settings. |
| `dependency_injection` | `shared/di_container` | DI container for modular composition. |
| `device_integration` | `shared/device` | Analyzer/modality integration (ASTM, HL7 adapters). |
| `communication` | `shared/communication` | Provider-neutral communication platform (channels, queue, policy). |
| `ai_gateway` | `shared/ai` | Self-hosted AI inference gateway (Ollama-first, provider-swappable). |
| `feature_flags` | `shared/feature_flags.py` | Feature flag evaluation and rollout controls. |
| `health_checks` | `shared/health/checker.py` | Liveness/readiness health check primitives. |
| `monitoring` | `backend/app/services/metrics_service.py` | Metrics, health checks, Prometheus endpoints. |
| `logging` | `shared/logging` | Structured logging and tracing. |
| `telemetry` | `shared/observability/tracer.py` | Distributed tracing (OTLP) and metrics collection. |
| `cache` | `shared/cache/backends.py` | Multi-backend caching (Redis, in-memory). |
| `retry` | `shared/retry/decorators.py` | Retry decorators with backoff for resilience. |
| `circuit_breaker` | `shared/circuit_breaker.py` | Circuit breaker for failing dependencies. |
| `backup_recovery` | `shared/backup/manager.py` | Backup and recovery orchestration. |
| `fhir_engine` | `backend/app/fhir` | FHIR R4 engine (resources, profiles, mappers, validation). |

## 3. Consumption rules

- A Domain may import Shared Core providers freely.
- A Domain may NOT import another Domain's modules, tables, or services.
- Cross-domain needs are met via the Cross-Domain Gateway and versioned
  contracts, or events on the Event Bus.
- A Domain may NOT reimplement any registry service (enforced by the 9-check
  `DomainCertificationEngine` and the Architecture Constitution scan).

## 4. Maturity

- Authoritative registry: **50 services declared**.
- Real providers verified on disk: **50** (100%).
- Backed by `shared/` (59 top-level
  components) + `backend/app/identity`, `backend/app/security`,
  `backend/app/notifications`, `backend/app/workflows`, `backend/app/fhir`,
  `backend/app/capabilities/*`.
- Known consolidation debt: **43 finding(s)** — see
  `MASTER_REMAINING_WORK.md`.

_Generated by scripts/architecture/docs.py._
