# MPI-01 Implementation Report — Audit-Chain Fork Prevention

**Status:** `PASS` (isolated-test evidence; not production readiness)
**Date:** 2026-11-18
**Scope:** Serialize `MergeAudit` tail read + append with a transaction-scoped PostgreSQL advisory lock.

---

## 1. Work done

Added MPI-only reliability primitives in `backend/app/services/mpi/reliability.py`:

- `AUDIT_LOCK_NAMESPACE = "gula:mpi:audit_chain:tail:v1"` and a deterministically derived, positive-bigint `AUDIT_LOCK_KEY` (single-argument `pg_advisory_xact_lock` overload, avoiding two-int namespace collisions). The key is public configuration, never a secret.
- `acquire_audit_chain_lock(db)` → `bool`. Uses `pg_advisory_xact_lock` (transaction-scoped) and returns `False` on non-PostgreSQL dialects (SQLite fixture) as a documented no-op.
- Integrated in `backend/app/services/mpi/resolver.py`:
  - **Genesis/create path** (before minting a new `Citizen` and before `_write_audit` reads the tail) so two concurrent creates cannot both observe genesis (`"0"*64`) and fork the chain.
  - **Merge path** (before the ordered `Citizen` row-lock `SELECT` and before `begin_nested()`), so no SAVEPOINT is ever opened while waiting for the chain lock.

Lock order is now: **advisory chain lock → Citizen rows by `id ASC` (`FOR UPDATE`) → SAVEPOINT work**. The lock is released only by the caller's outer COMMIT/ROLLBACK, never by SAVEPOINT RELEASE.

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/reliability.py` | **new** | MPI-only, DB-native serialization/version/retry primitives; no schema, Redis or new dependency |
| `backend/app/services/mpi/resolver.py` | +232 / -30 | Acquire advisory lock at genesis and merge entry; share hash helpers; in-SAVEPOINT segment verification; atomic version bump |
| `backend/tests/test_mpi_reliability.py` | **new** (19 tests) | Pin stable/versioned key, SQLite no-op, atomic increment, SQLSTATE classification, bounded retry |
| `backend/tests/test_mpi_api_reliability.py` | **new** (5 tests) | Pin idempotent replay, reconcile, pre-commit response capture |

No schema, migration, `env.py`, API contract or governance approval file was changed.

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `/tmp/opencode/mpi-venv/bin/python -m py_compile …` | compile OK | 0 |
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_reliability.py … (6 files)` | **84 passed**, 1 warning, 91.11 s | 0 |
| Broader regression (10 files, includes identity/MDM/security) | **137 passed**, 79.17 s | 0 |

## 4. PostgreSQL evidence (isolated `mpi_test`, synthetic only)

| Scenario | Result |
|---|---|
| Naive concurrent genesis (no lock) | `rows=2`, `fork_groups=1`, `valid=false` — fork reproduced |
| Advisory-locked genesis, 20 workers | `rows=20`, `forks={}`, `valid=true` |
| Advisory lock held across SAVEPOINT, observer thread | Observer **blocks** while holder holds; proceeds only after outer rollback — proves transaction (not session/SAVEPOINT) scope |
| Actual `resolve_identity` genesis, 20 workers | `errors=0`, `chain_valid=true`, `audits=20` |
| Actual `merge_citizens`, 2/5/10/20 workers | `errors=0`, `chain_valid=true` in every scenario |

Full harness: `73 passed in 74.40s`, `EXIT=0` (`/tmp/opencode/mpi-impl/mpi09_full.log`).

## 5. Residual risks

- Advisory locks are **PostgreSQL-specific**; on SQLite the primitive is a no-op by design, so SQLite tests do **not** prove locking. PostgreSQL evidence above is isolated-test evidence only.
- The lock serializes all MPI chain appends on one key; at very high append rates this is a throughput ceiling (see MPI-09 performance table).
- D-MPI-2a sentinel fallback is **not implemented** (no schema authorization). D-MPI-1 execution authorization is recorded in `MPI_EXECUTION_AUTHORIZATION_REQUEST.md`; it is not a production decision.
- Verification remains detection-only (see MPI-08); owner fork-response policy D-MPI-3/4 is unresolved.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| Single stable versioned lock namespace/key | PASS |
| Transaction-scoped, acquired before tail read and before SAVEPOINT | PASS |
| Session-scoped locks never used | PASS |
| No new schema/Redis/distributed lock/dependency | PASS |
| Fork prevention demonstrated on real PostgreSQL with actual code | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
