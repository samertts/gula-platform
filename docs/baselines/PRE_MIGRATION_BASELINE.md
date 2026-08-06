# PRE-MIGRATION BASELINE — GULA Platform

> Permanent, immutable baseline captured for the **Phases 0–2 migration** of the GULA
> Platform monorepo. Every subsequent migration commit must be compared against this
> document (Before-vs-After). Metrics below were **verified end-to-end in a clean
> environment** on the verification cycle that produced Commit 0.0's report, AFTER the
> SQLite test-infrastructure root-cause fix (see §Root Cause & §Permanent Fix).

---

## 1. Baseline Identity

| Field | Value |
|---|---|
| Baseline commit | `d6574f8e` — `chore(repository): establish pre-migration baseline` |
| Branch | `remediate-security-001` |
| Baseline date | 2026-08-06 |
| Baseline kind | Pre-migration (immutable starting point for Phases 0–2) |
| Working-tree delta at capture | `backend/tests/conftest.py` (+19/−1, test-infra fix, see §8) + the two baseline docs |

## 2. Repository Statistics

| Metric | Value |
|---|---|
| Tracked files | 6,311 (+1 gitlink `gula-platform` → `5e158e8a`) |
| Tracked directories | 1,352 |
| Git objects / history | Conventional commits, `remediate-security-001` branch |

### 2.1 LOC per language (verified at Commit 0.0)

| Language | LOC | Files |
|---|---|---|
| Python | 478,082 | 3,111 |
| TypeScript | 53,175 | — |
| TSX | 80,305 | — |
| TS + TSX total | 133,480 | — |
| JavaScript | 5,680 | — |
| Shell | 22,156 | — |
| JSON | 420,634 | — |
| YAML | 11,451 | — |
| Markdown | 217,052 | — |
| SQL | 1,114 | — |

## 3. Build Status (verified)

| Component | Command | Result |
|---|---|---|
| Backend byte-compile | `python -m compileall -q app` | **PASS** (exit 0) |
| Frontend TypeScript | `npx tsc --noEmit` (frontend-v3) | **0 errors** (exit 0) |
| Frontend ESLint | `npx eslint "src/**/*.{ts,tsx}"` | **0 errors** (exit 0) |
| Frontend production build | `npx vite build` | **PASS** in 5.12 s |
| Python environment | `pip check` | **No broken requirements** |

## 4. Test Summary (verified, clean environment)

| Suite | Result | Duration |
|---|---|---|
| **Complete backend suite** `pytest tests/` | **4865 passed / 0 failed / 148 warnings** | 1253.46 s (20:53) |
| Parity file `test_integration_parity.py` (previously hung) | 36 passed | 102.46 s |
| Service subset `test_lab_service` + `test_admin_service` + `test_metrics_service` + `test_sample_service` | 95 passed | 70.5–80.3 s |

> The complete suite **completes** — the historical "pytest hang" is resolved, not
> reduced (see §8).

## 5. Static Analysis / Quality Gates (verified)

| Gate | Baseline | Status |
|---|---|---|
| Ruff (backend/app) | **379 errors**: E402 167, N801 141, N999 71 | matches `reports/validation/baseline.json` |
| MyPy | times out on full backend codebase (capabilities/-heavy) | **Known limitation** (documented, not green) |
| Architecture Constitution gate | `architecture.py check` → **PASS** | 57 findings (57 acknowledged, **0 new**); domain 11/11 (isolation PASS); country-agnostic PASS |
| Domain Platform gate | `domains.py check` → **PASS** | 11/11 certification, isolation PASS |
| Brain freshness | `make brain-check` | maintained (see §CI) |

## 6. API & OpenAPI (verified)

| Metric | Value |
|---|---|
| Served OpenAPI paths (`app.openapi()` → `paths`) | **1,699 unique** (0 duplicates) |
| Top-level FastAPI routes (`app.routes`) | 126 |
| Contracts export OpenAPI | 0 paths (empty placeholder — no contract diff expected at baseline) |
| Pre-existing OpenAPI warning | duplicate Operation ID `configure_connector_integration_connectors__name__configure_post` (benign) |

> Note: an earlier figure of 1,329 paths was measured with a different method/state;
> **1,699** is the verified, reproducible baseline.

## 7. Migrations & Database

| Metric | Value |
|---|---|
| Alembic migration files | **56** (`backend/migrations/versions/`) |
| Config | `backend/alembic.ini` (`script_location=migrations`, empty `sqlalchemy.url`, env-driven); root `alembic.ini` has **no** `script_location` and shadows it under `cd backend` |
| DB driver state | `gula-postgres` (postgres:16-alpine) + `gula-redis` running via docker; PG has **no host port mapping** (`localhost:5432` refused) |
| Known defect | `migrations/env.py` does not bootstrap repo root into `sys.path` → `ModuleNotFoundError: No module named 'shared'` when running from `backend` without `PYTHONPATH=..` (documented limitation, remediation is a follow-up task, not a baseline fix) |

## 8. Root Cause & Permanent Fix (pytest hang)

**Symptom:** full backend suite stalled indefinitely; every run blocked at the first test
using the DB fixture (`test_integration_parity.py::TestHealthEndpoints::test_health_liveness_public_and_shape`).

**Root cause (proven):** the session-scoped test engine in `tests/conftest.py`
(`_session_engine`) creates a **file-backed SQLite** database and runs `create_all` over
**457 tables / ~1,300 DDL statements**. Under the WSL2 virtual disk, the default
rollback journal forces an **fsync per DDL statement**, turning `create_all` into a
multi-minute I/O stall. The stall manifests as `D`-state (uninterruptible disk I/O) with
a live `.db-journal` file; faulthandler SIGABRT dumps confirmed the block at
`sqlalchemy → visit_index → do_execute` inside `_session_engine` (conftest.py:161).

**Permanent fix:** register a `connect` event listener on the session engine that sets
`PRAGMA journal_mode=MEMORY` and `PRAGMA synchronous=OFF`. SQLite locking/transaction
semantics are **unchanged** (journal location does not alter lock behavior; savepoint
isolation is preserved). The disk-journal write path — the observed stall — is removed.

**Semantics verification (objective A/B):** identical 95-pass results for
`test_lab_service` + `test_admin_service` + `test_metrics_service` + `test_sample_service`
under (A) old conftest (journal=delete), (B) new conftest, (C) new conftest re-run
(determinism). Transaction, isolation, and determinism behavior is byte-for-byte
equivalent in outcome.

## 9. Performance & Memory (verified)

| Metric | Value |
|---|---|
| App import / boot (once per process) | ~33–35 s (module cache; dominates wall-clock) |
| `create_all` (457 tables) | ~40 s after fix (was ~112 s; WSL2 load-dependent) |
| Full-suite wall clock | 20:53 on WSL2 (documented ~10 min on faster hardware) |
| Process peak RSS (parity-file run) | ~448 MB |
| Swap pressure | observed ~321 MB (WSL2) — occasional D-state spikes possible, mitigated |

## 10. Dependency Baseline

| Category | Status |
|---|---|
| `pip check` | clean (backend venv) |
| `npm audit` | 0 vulnerabilities (frontend-v3, after react-router 8.3.0 migration) |
| Runtime services | PostgreSQL 16 + Redis (docker), self-hosted per constitution |

## 11. Known Limitations / Debt (accepted at baseline)

1. **Alembic environment**: repo-root `sys.path` bootstrap missing in `migrations/env.py`;
   root `alembic.ini` lacks `script_location`; PG not reachable at `localhost:5432`
   (no host port mapping). → Remediation planned as a dedicated follow-up commit.
2. **Startup guard DB retry**: with `DATABASE_URL` unset (non-test mode), the app retries
   15× against `unknown:5432`. Only affects out-of-pytest boots; documented.
3. **WSL2 disk I/O**: remains the dominant cost (suite 20:53); the fix removes the
   pathological journal-fsync path but not virtual-disk latency.
4. **MyPy**: times out on the full backend codebase (accepted; not a gate).
5. **Ruff 379 baseline** (E402 cond-imports, N801 capabilities naming, N999 dormant
   modules): acknowledged, gated by `baseline.json` (higher-is-worse; no growth allowed).
6. **Architecture debt**: 57 acknowledged Shared Core reimplementation findings +
   2 country findings at `.ai/core/architecture/constitution_baseline.json` — gated
   (any NEW finding fails CI). 32 L1 layer violations etc. tracked (advisory).
7. **148 test warnings** (incl. SAWarning unresolvable FK cycle
   `national_encounters ↔ national_referrals` on `drop_all`, OpenAPI duplicate op id):
   pre-existing, cosmetic.
8. **Dormant contexts** (per Commit 0.1 plan): `ai/`, `nhop-platform/`, `edge_agent/`
   to be archived; `platform/` deferred (`active_development`).
9. **Tooling**: `docker compose v2` unavailable (raw docker used); `gitleaks` pre-commit
   hook active.

## 12. Risks (top)

1. Migration (Phases 0–2) touches ~6.3k files; any semantics drift is caught by the
   4,865-test gate + architecture gate (0-new-findings).
2. Archiving `backend/services/`, `ai/`, `frontend-v2/`, etc. removes code paths; each
   commit must re-verify endpoint counts (1,699 baseline) and importer graphs.
3. WSL2 environment variability can produce false "slowness" signals; the fixed A/B +
   determinism protocol guards against attributing perf noise to regressions.

## 13. Rollback Readiness

| Change | Rollback |
|---|---|
| `tests/conftest.py` pragma fix | `git checkout d6574f8e -- backend/tests/conftest.py` restores exact pre-fix behavior (A/B-verified via stash) |
| Baseline docs | Additive (`docs/baselines/`); removal is lossless |
| Whole baseline commit | `git revert` of the baseline commit (no schema/data/API changes) |

## 14. Baseline Sign-off

Verified end-to-end in a clean environment on 2026-08-06. All hard gates PASS; complete
suite green. Commit 0.1 (dormancy registry + ADR-014 + certification check + tests) is
the first planned deviation from this baseline.
