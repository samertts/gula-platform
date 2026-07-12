# Changelog

## [2.1.0] — 2026-07-12 — MISSION-000B

### Added
- **`shared/` Library** — 27 canonical modules covering auth, config, events, logging, audit,
  metrics, cache, retry, health, QR, barcode, PDF, security, RBAC, storage, notifications,
  backup/restore, workflow, policies, validation, middleware, schemas, models, utilities,
  observability, device integration, and design system.
- **Canonical Architecture** — Documented unified architecture with component maps and
  migration paths.
- **Unified Entity Catalog** — Complete catalog of all data entities across all repositories.
- **Engineering Knowledge Graph** — Dependency, API, database, security, and test maps.
- **Design System Tokens** — Colors, typography, spacing, shadows, RTL styles.

### Changed
- **`services/shared/`** — Redirected to canonical `shared/` library with deprecation warnings.
- **QR Code** — Consolidated from 3 independent implementations into `shared/qr/`.
- **Barcode** — Consolidated from 2 implementations into `shared/barcode/`.
- **Circuit Breaker** — Unified from 2 implementations into `shared/circuit_breaker.py`.
- **Message Broker** — Consolidated from Platform-Core + Services into `shared/messaging.py`.
- **Retry Logic** — Merged decorator and function-based approaches into `shared/retry/`.

### Removed
- Code duplication across 7 areas (QR, barcode, audit, circuit breaker, messaging, retry,
  device adapters).

### Quality
- All `py_compile` checks pass
- All Ruff checks pass (E9, F821, F822, F823)
- Existing backend code unaffected
