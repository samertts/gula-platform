# Changelog

All notable changes to GULA Platform — Engineering Factory.

## [2.1.0] — 2026-07-12

### Engineering Factory Initialization (MISSION-000C)

#### Infrastructure (Phase 1 & 2)
- Unified `pyproject.toml` with comprehensive ruff/mypy/pytest/coverage config
- Standardized `shared/pyproject.toml` with full dependency spec
- Consolidated `services/shared/` → canonical `shared/` library

#### Canonical Shared Library — 25 new modules (Phase 3)
- `shared/ai/` — AIClient + AIProvider (Gemini + stub)
- `shared/architecture/` — Validator + KnowledgeGraph
- `shared/booking.py` — Appointment booking engine
- `shared/cli.py` — Developer CLI (health/patient/order/generate/config)
- `shared/documents.py` — Document store
- `shared/domain/` — 7 canonical domain model modules (healthcare, security, events, notifications, billing, api, booking)
- `shared/feature_flags.py` — FeatureFlag registry
- `shared/generators/` — Module, Migration, Documentation generators
- `shared/licensing.py` — License + Tier management
- `shared/localization.py` — i18n support
- `shared/payments.py` — Payment processing
- `shared/scheduler.py` — Task scheduling
- `shared/search.py` — Full-text search
- `shared/sdk/` — Developer SDK (client, models, exceptions)
- `shared/subscriptions.py` — 4-tier subscription plans

#### Canonical Domain Models (Phase 6)
- Healthcare: Citizen, LabOrder, LabResult, Visit, QualityControl
- Security: User, Role (8), Permission (17), ROLE_PERMISSIONS matrix
- Events: 7 canonical event types (OrderCreated, ResultCritical, etc.)
- Notifications: Notification, NotificationChannel, NotificationTemplate
- Billing: Invoice, PricingTier, BillingCycle
- API: APIResponse, PaginatedResponse, APIError
- Booking: Appointment, AppointmentStatus

#### Developer Platform (Phase 7)
- SDK: GulaClient with full CRUD (patients, orders, results, samples, labs)
- CLI: 10+ commands across 5 subcommands
- Generators: ModuleGenerator, MigrationGenerator, DocGenerator

#### Architecture Validation (Phase 8)
- `ArchitectureValidator` with 3 rules: circular import, service→backend isolation, shared independence

#### Knowledge Graph (Phase 5)
- 38 nodes × 40+ edges across all capabilities
- Mermaid export, path-finding, JSON query

#### Quality Gates (Phase 9)
- Zero F821/E9 errors in backend
- All 35+ new modules compile clean
- ruff lint passes with configured rules

#### Git Operations (Phase 10)
- CHANGELOG generated
- Tagged for release
