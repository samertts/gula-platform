# MPI-03 Implementation Report — Atomic Version Control

**Status:** `PASS` (isolated PostgreSQL evidence; not production readiness)
**Date:** 2026-11-18
**Scope:** Replace blind read-modify-write version bumps with a database-side atomic increment, with an optional optimistic guard.

---

## 1. Work done

Added `atomic_increment_version(db, instance, model, expected=None)` in `backend/app/services/mpi/reliability.py`:

- Single `UPDATE … SET version = version + 1 … RETURNING version`, so the database evaluates the increment and two concurrent transactions cannot lose an update.
- Optional optimistic guard `WHERE version = :expected`; a stale writer raises `VersionConflictError` and mutates nothing.
- The ORM attribute is expired after the statement so no redundant write is emitted on the next flush.

Integrated at both mutation sites:

- `resolver.py` — secondary citizen version bump inside the merge SAVEPOINT.
- `canonical_service.py` — both source and target canonical version bumps.

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/reliability.py` | **new** — `atomic_increment_version`, `VersionConflictError` | DB-side increment + optional stale detection |
| `backend/app/services/mpi/resolver.py` | secondary version bump → atomic | Lost-update prevention on merged citizen |
| `backend/app/services/mpi/canonical_service.py` | source + target version bumps → atomic | Lost-update prevention on canonical path |
| `backend/tests/test_mpi_reliability.py` | 2 dedicated tests | Single increment + stale-version rejection with no mutation |

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_reliability.py` | **19 passed**, 78.87 s | 0 |
| `ENV=test PYTHONPATH=. … pytest -q (6 focused files)` | **84 passed** | 0 |

## 4. PostgreSQL evidence (isolated `mpi_test`, synthetic only)

Naive blind increment vs database-side increment (10/20 workers):

| Strategy | Workers | Expected | Actual | Lost updates |
|---|---|---|---|---|
| Naive read-modify-write | 2 | 2 | 1 | 1 |
| Naive read-modify-write | 5 | 5 | 1 | 4 |
| Naive read-modify-write | 10 | 10 | 1 | 9 |
| Naive read-modify-write | 20 | 20 | 1 | 19 |
| `SELECT … FOR UPDATE` | 10 | 10 | 10 | 0 |
| **Atomic SQL increment** | 10 | 10 | 10 | **0** |
| **Atomic SQL increment** | 20 | 20 | 20 | **0** |
| Optimistic guard | 10 | 10 | 10 | 0 (45 retries) |

Actual implementation, 20 concurrent `atomic_increment_version` calls: `final_version=21`, `lost_updates=0`, `errors=0`.

## 5. Residual risks

- The optimistic `expected=` guard is available but **not wired at every call site**; only the always-correct atomic increment is applied at the two known mutation sites.
- No new DB `version` constraint/check was added (no schema change authorized).
- Version monotonicity proves no lost updates in the tested paths; it is not a general optimistic-concurrency policy for the whole platform.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| One atomic DB-side increment statement | PASS |
| No lost updates at 2/5/10/20 concurrency | PASS |
| Stale writer rejected without mutation | PASS |
| No schema change | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
