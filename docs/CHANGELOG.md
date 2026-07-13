# Changelog

## [2.1.1] — 2026-07-13 — MISSION-001A

### Added
- **Notification Service** (`backend/app/notifications/`) — Circuit-broken multi-channel notification
  service with email, SMS, WhatsApp, push, and Telegram support. Graceful degradation when
  channels are unconfigured.
- **Notification Templates** (`shared/notifications/template.py`) — Channel-specific template
  engine with variable interpolation and built-in templates for welcome, password reset,
  test results, and critical alerts.
- **Audit Log Immutability** — Integrated audit log immutability trigger (ISO 27001 A.8.15)
  into the startup guard seeding process.
- **ADR-001** through **ADR-004** — Missing architecture decision records created (Engineering
  Constitution, Monolith First, Multi-Tenant Isolation, Skill Platform).
- **ADR-011** and **ADR-012** — New ADRs for Notification Platform and Engineering Automation
  architectures.
- **Test infrastructure** — Added `__init__.py` to all test subdirectories (identity, booking,
  notifications, kernel, kernel_hardening, integration, skills) to fix import resolution.

### Changed
- **Dead code removal** — Removed 4 unused functions from `main.py` (227 lines of dead code).
  `_migrate_perm_version`, `_seed_test_types`, `_ensure_master_admin` were duplicate
  implementations superseded by `startup_guard.py`. `_ensure_audit_log_immutable` moved
  into `startup_guard.py` as `_run_ensure_audit_log_immutable`.
- **Engineering imports** — Fixed `engineering/__init__.py` to use relative imports instead
  of absolute `backend.app.engineering.*` paths.

### Quality
- All `py_compile` checks pass (syntax gate)
- Flake8 (E9, F821, F822, F823) — clean
- `main.py` reduced from 1635 to 1368 lines (267 lines removed)

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
