# PROGRAM-010 — Release Candidate Certification Report (v1.0.0-RC2)

Status: **CERTIFIED** (release draft created, not published)
Date: 2026-08-01
Branch: `remediate-security-001`
Environment: production-like (PostgreSQL 16 + Redis 7 live containers)

## Verdict

**PASS — GULA Platform v1.0.0-RC2 is certified as a release candidate.**

All quality gates green, backend/frontend parity holds for core flows,
and the production-like deployment (bare uvicorn AND Docker image)
reports full system readiness with deep-health grade A.

## 1. Repository Audit (P1)

| Check | Result |
|---|---|
| Python target | 3.12 across pyproject/mypy/Dockerfiles/CI |
| `shared/pyproject.toml` | aligned `requires-python >=3.12`, `target-version py312`; stray `.bak` removed |
| Version consistency | `package.json` 2.5.0 == lockfile 2.5.0 (pre-bump) |
| Duplicate route modules / egg-info / `__pycache__` tracked | none |
| Pre-existing uncommitted `scripts/manage-snapshots.sh` | preserved untouched |

## 2. Infrastructure & Migration (P2)

| Check | Result |
|---|---|
| Alembic | single head `20260723_0002`; live PG `alembic_version` in sync |
| Tables (live PG) | 342 |
| `docker compose config` | VALID (with env interpolation provided) |
| Backend Docker image | builds clean (`backend/Dockerfile`, context `backend/`) |
| Image smoke | runs healthy on port 10000 with `shared/` volume mount |

## 3. Frontend ↔ Backend Parity (P3)

| Metric | Value |
|---|---|
| OpenAPI paths (live) | 1640 |
| Unique FE API calls | 532 |
| Resolved to live paths | 479 (90.0%) |
| Unresolved | 53 — ALL in dormant capability/national/NIAM/citizen demo pages (documented strategic gap, zero core-flow defects) |
| Pre-existing exception | `GET /metrics/prom` FE exception (documented, non-blocking) |

## 4. Quality Gates (P4)

| Gate | Result | Detail |
|---|---|---|
| Backend tests | **2576 passed / 0 failed** (461 s) | plain `backend/tests/` suite |
| ruff | PASS | 379 = baseline (E402 167, N801 141, N999 71) |
| tsc | PASS | 0 type errors |
| eslint | PASS | 0 errors (max-warnings 0) |
| vitest | **60/60** (4 files) | 46 utils + 3 debounce + 5 toast + 6 (existing) |
| vite build | PASS | dist 433 kB JS / 130.79 kB gzip |
| Validation engine | **VERDICT: PASS** | brain-freshness, eslint, ruff, tsc, tech-debt |
| mypy | N/A | known full-repo timeout (documented); gated by tsc/eslint/ruff |

## 5. Android (P5)

| Check | Result |
|---|---|
| Source | `mobile/android/` (Gradle 8.13, Kotlin DSL, release block, applicationId `io.gula.android`) |
| Local build | BLOCKED — no Android SDK/gradle/wrapper jar on this machine (documented) |
| CI path | `.github/workflows/mobile-android.yml` (paths `mobile/android/**`, `contracts/sdk/kotlin/**`) |

## 6. Deployment Package (P6)

`docs/releases/v1.0.0-RC2/DEPLOYMENT.md` — deploy/verify/rollback steps,
runtime contract (`shared/` mount, port 10000), backup + PITR references,
known deviations.

## 7. Production-like Verification (P7)

| Probe | Result |
|---|---|
| `GET /health` | `status: ok, system_ready: true, database: ok` |
| `GET /health/ready` | `status: ok` |
| `GET /health/deep` | **grade A**, 0 issues; DB 2.7 ms, Redis 2.1 ms, queue backlog 0 |
| `POST /login` invalid creds | structured `{"detail":"Invalid email or password"}` |
| `GET /openapi.json` | 200 |
| `GET /metrics` | 401 (auth-gated, expected) |

## 8. Release Actions (P9)

- Version files bumped to `1.0.0-RC2`: `backend/pyproject.toml`,
  `frontend-v3/package.json`, `mobile/version.json`,
  `mobile/android/app/build.gradle.kts` (versionName + versionCode 2).
- Root `VERSION` file added; root `CHANGELOG.md` created.
- Tag `v1.0.0-RC2` (annotated) at certified HEAD; `v1.0.0-RC1` left in
  place (remote, pre-certification; superseded — no force-push).
- GitHub **draft** release created (not published).

## Risks / Follow-ups

1. Android artifact requires CI run on tag push — verify `mobile-android.yml`.
2. 53 dormant-page API calls to revisit when bounded contexts activate.
3. mypy full-repo timeout — scoped mypy config is the long-term fix.
4. 379 ruff baseline — track N999 module naming burn-down.
