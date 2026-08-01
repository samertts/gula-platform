# Changelog

All notable changes to the GULA Platform are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) — the
version scheme follows [Semantic Versioning](https://semver.org/).

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
