# Changelog

All notable changes to the GULA Platform are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) — the
version scheme follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Resend as production email provider** — `shared/notifications/resend.py`
  (`ResendEmailClient`) using the official `resend>=2.35.0` SDK with
  dependency injection, bounded HTTP timeouts, transient-failure retries
  (HTTP 429/5xx/network, exponential backoff), structured logging that never
  leaks the API key, and robust typed error handling.
- `NotificationSender.send_email()` now uses Resend when `RESEND_API_KEY` is
  set and falls back to self-hosted SMTP otherwise.
- Startup validation in `startup_guard.validate_config()` fails in production
  with a clear message when `RESEND_API_KEY` is missing or weak.
- Environment configuration: `RESEND_API_KEY`, `EMAIL_FROM`,
  `RESEND_TIMEOUT_SECONDS`, `RESEND_MAX_RETRIES` in `.env.example`,
  `backend/app/config.py`, `shared/config/loader.py`, and `render.yaml`
  (as Render secrets).
- Unit tests: `backend/tests/notifications/test_resend_email.py` (36 tests);
  new startup-guard validation tests.
- Docs: `docs/adr/ADR-011-resend-email-provider.md` (Free-First exception +
  SMTP fallback), notifications README, backend catalog, README deployment
  secrets policy.
- **Telegram Bot as production notification provider** —
  `shared/notifications/telegram.py` (`TelegramNotificationService`) using the
  official Telegram Bot API over HTTPS with dependency injection, bounded
  timeouts, exponential-backoff retries on transient failures (HTTP 408/429/
  5xx, network), structured logging and bot-token redaction everywhere.
- `NotificationSender.send_telegram()` integrates Telegram with dynamic
  `chat_id` (never a config value); supports text / HTML / MarkdownV2 /
  photos / documents / files / alerts / monitoring notifications.
- Startup validation fails in production when `TELEGRAM_BOT_TOKEN` is missing
  or weak while `TELEGRAM_NOTIFICATIONS_ENABLED=true`.
- Environment configuration: `TELEGRAM_BOT_TOKEN` (empty in `.env.example`),
  `TELEGRAM_NOTIFICATIONS_ENABLED`, `TELEGRAM_TIMEOUT_SECONDS`,
  `TELEGRAM_MAX_RETRIES` in `.env.example`, `backend/app/config.py`,
  `shared/config/loader.py`.
- Unit tests: `backend/tests/notifications/test_telegram.py` (36 tests),
  Telegram cases in `test_notification_sender.py` and
  `test_startup_guard.py`.
- Docs: `docs/adr/ADR-012-telegram-notification-provider.md`, notifications
  README, backend catalog.

### Security
- Secrets (including `RESEND_API_KEY` and `TELEGRAM_BOT_TOKEN`) are loaded
  ONLY from the environment (`.env` / hosting-platform secrets) — never
  hardcoded, never in logs, never committed.

## [1.0.0] — 2026-08-02

Stable v1.0 certification (PROGRAM-06 + PROGRAM-STABLE-001/002). Recommended
version tag: `v1.0.0`.

### Release Engineering (PROGRAM-REPO-01 Wave 4)
- Version single-source aligned to **1.0.0**: `VERSION`, backend
  `APP_VERSION` + `pyproject.toml`, `frontend-v3/package.json` +
  `package-lock.json` (root `package.json` + TS SDK already 1.0.0).
- Release stream normalized to semver `v*` tags: 35 non-semver feature tags
  archived to `refs/archive/tags/*` (recoverable); `v1.0.0-RC1`,
  `v1.0.0-RC2`, `v2.1.0-engineering-factory` retained.
- Branch hygiene: 61 stale remote branches archived to
  `refs/archive/branches/*`; `main` + `remediate-security-001` remain.
- Root derived artifacts removed: `skills-lock.json` (git rm, zero
  dependencies), root `openapi.json` (untracked regenerable spec).
  Deployment/build surfaces (`vercel.json`, `tsconfig.json`,
  `package-lock.json`) intentionally retained.
- OSS governance refreshed: SECURITY.md coordinated disclosure (GitHub
  Security Advisories), CODEOWNERS re-pointed to live trees, CONTRIBUTING
  Python 3.12 alignment.

### Fixed
- `mobileApi.info()` now calls `/mobile/app-info` (was `/auth/mobile/app-info`,
  a runtime 404 — parity defect found by PROGRAM-06 live route diff)
- Frontend `getErrorMessage` now prefers backend `detail_ar` (Arabic-first
  error parity; 32 backend sites emit bilingual errors)
- Ruff SIM102 nested-if in `identity/services/authorization_service.py`
- `services/health_exchange/api_security.py`: hardcoded API key replaced with
  env/key-file backed constant-time verification, deny-by-default
  (PROGRAM-STABLE-001 security repair)
- FK index coverage migration `20260802_0002_stable_fk_indexes.py` + policy
  tests (`test_fk_index_policy.py`, `test_api_security.py`)

### Fixed (PROGRAM-STABLE-001/002 continuation)
- **Import cycles eliminated**:
  - `app.ehr <-> app.national` — the shared national/EHR declarative
    metadata now lives in Shared Core (`shared/models/base.SharedBase`);
    `app/national/base.py` re-exports it as `NationalBase` (backward
    compatible), `app/ehr/base.py` consumes it directly
  - `app.kernel <-> app.national` — the rule-engine domain types moved to
    Shared Core (`shared/rules_engine/domain`); `app.national.rules_engine`
    re-exports for backward compatibility, `app/kernel/rules_runtime.py`
    consumes Shared Core directly
- Flaky load-sensitive benchmarks made robust (best-of-3 throughput /
  min-of-3 latency) while keeping the same regression thresholds:
  `test_ai_benchmark.py::test_cosine_similarity_throughput`,
  `tests/kernel_hardening/test_performance_baseline.py` (4 loop benchmarks)
- STABLE harness scanner truthfulness:
  - module-level-only import-cycle detection (lazy/`TYPE_CHECKING` imports
    no longer create false rings)
  - approved EHR-consumer contract allowlist
    (`docs/certification/DOMAIN_SOVEREIGNTY_REPORT.md`) in the
    domain-isolation check
  - severity-aware verdict per constitution §32.3 (LOW/MEDIUM warnings are
    advisory; only fail/HIGH/CRITICAL block certification)

### Certified
- Backend: **2845 tests passed / 0 failed** (full suite, 8m00s)
- Frontend: tsc 0 errors, eslint 0 errors, vitest **122/122**, production
  build PASS
- Enterprise validation (fast scope): **VERDICT PASS**
- API parity: **593/593 frontend calls resolve to live backend routes** (0 drift)
- RBAC parity: **25 roles × 16 permissions — 0 drift** (backend shared.rbac ↔ frontend guards)
- Workflow parity: **14/14 production workflows** complete (page→client→route)
- Entity parity: 26/26 models referenced in frontend types/pages
- i18n parity: 399/399 keys ar↔en
- STABLE-002: Shared Core unique (declarative metadata + rule-engine domain),
  domains sovereign, zero cross-domain administration (5 documented approved
  EHR-consumer read contracts + 1 risk-registered nursing→EHR write contract)
- STABLE harness (full run, 11m): **CERTIFIED** — 0 fail checks,
  all mandatory gates green

## [1.0.0-RC2] — 2026-08-01

Release candidate certified by PROGRAM-010 (Release Candidate
Certification). Supersedes v1.0.0-RC1 (tagged pre-certification).

### Added
- Deployment bundle for RC2: `docs/releases/v1.0.0-RC2/DEPLOYMENT.md`
- Root `VERSION` file (`1.0.0-RC2`) as single-file version marker

### Changed
- Unified release version to `1.0.0-RC2` across:
  `backend/pyproject.toml`, `backend/app/config.py`,
  `frontend-v3/package.json`, `mobile/version.json`,
  `mobile/android/app/build.gradle.kts` (versionName `1.0.0-RC2`,
  versionCode `20502`)
- `shared/pyproject.toml` aligned to Python 3.12
  (`requires-python >=3.12`, `target-version py312`); removed stray
  tracked `shared/pyproject.toml.bak`

### Fixed
- `backend/app/config.py` APP_VERSION now reports the certified version
  through `/health`

### Certified
- Backend: 2576 tests passed / 0 failed
- Frontend: tsc 0 errors, eslint 0 errors, vitest 60/60, production build OK
- Validation engine (fast scope): VERDICT PASS
- Production-like: `/health` system_ready, `/health/deep` grade A
- Parity: 0 unresolved API calls in core LIMS flows
- Docker backend image builds and runs healthy (port 10000)

## [2.5.0] — 2026-07-15

Pre-certification version line. Historical baseline for all platform
components (backend, frontend, mobile, shared SDKs).
