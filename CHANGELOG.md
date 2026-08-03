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

### Security
- Secrets (including `RESEND_API_KEY`) are loaded ONLY from the environment
  (`.env` / hosting-platform secrets) — never hardcoded, never in logs, never
  committed.

## [1.0.0] — 2026-08-02

Stable v1.0 certification (PROGRAM-06 + PROGRAM-STABLE-001/002). Recommended
version tag: `v1.0.0`.

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

### Certified
- Backend: **2820 tests passed / 0 failed** (full suite, 11m16s)
- Frontend: tsc 0 errors, eslint 0 errors, vitest **122/122**, production
  build PASS
- Enterprise validation (fast scope): **VERDICT PASS**
- API parity: **593/593 frontend calls resolve to live backend routes** (0 drift)
- RBAC parity: **25 roles × 16 permissions — 0 drift** (backend shared.rbac ↔ frontend guards)
- Workflow parity: **14/14 production workflows** complete (page→client→route)
- Entity parity: 26/26 models referenced in frontend types/pages
- i18n parity: 399/399 keys ar↔en
- STABLE-002: Shared Core unique, domains sovereign, zero cross-domain
  administration (1 documented approved nursing→EHR contract)

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
