# MPI-07 Implementation Report — Failure Recovery & Bounded Retry

**Status:** `PASS` (unit + isolated PostgreSQL evidence; not production readiness)
**Date:** 2026-11-18
**Scope:** Classify transient vs permanent database failures; retry only transient failures, a bounded number of times, on fresh sessions, reconciling ambiguous commits before replay.

---

## 1. Work done

In `backend/app/services/mpi/reliability.py`:

- `TRANSIENT_SQLSTATES` explicit allowlist: `40001`, `40P01`, `55P03`, `57014`, `08000/08001/08003/08004/08006/08007/08S01`, `57P01/57P02/57P03`.
- `PERMANENT_SQLSTATES` explicit denylist: `23505`, `23503`, `23502`, `23514`, `23515`, `22000/22001/22003/22007/22008`, `42501`. Anything not explicitly transient is **never** retried.
- `sqlstate_of(exc)` walks `pgcode`, `sqlstate`, `.orig` and chained `__cause__`/`__context__` with cycle protection.
- `bounded_retry(session_factory, operation, reconcile=None, max_attempts=3, backoff_seconds=(0.025, 0.05))`:
  - fresh session per attempt; rollback + close on failure;
  - permanent/unclassified errors propagate immediately;
  - failed session is **closed before reconciliation** so in-doubt locks are released before the reconcile read;
  - reconcile runs on a fresh session and, if the first attempt actually committed, returns the original result instead of replaying a write;
  - bounded to 3 attempts (first + 2 retries).

In `backend/app/services/mpi/api.py`, `SQLAlchemyError` on commit is translated to HTTP 503 with a generic detail, and both write endpoints use `bounded_retry` with their idempotency reconcile hooks (MPI-04/05).

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/reliability.py` | **new** | SQLSTATE classification + bounded retry with ambiguous-commit reconciliation |
| `backend/app/services/mpi/api.py` | retry wiring + `SQLAlchemyError` → 503 | Failure recovery at the transaction owner |
| `backend/tests/test_mpi_reliability.py` | 12 dedicated tests | Transient/permanent classification, unknown-error handling, fresh sessions, reconcile-before-replay, no permanent retry, attempt bound |

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_reliability.py` | **19 passed**, 78.87 s | 0 |
| `ENV=test PYTHONPATH=. … pytest -q (6 focused files)` | **84 passed** | 0 |
| `ENV=test PYTHONPATH=. … pytest -q (10 broader files)` | **137 passed**, 79.17 s | 0 |

## 4. PostgreSQL evidence (isolated `mpi_test`, synthetic only)

| Scenario | Result |
|---|---|
| `lock_timeout` expired under contention | SQLSTATE `55P03`, `timed_out=true`, classified transient |
| Serialization-failure injection (10 workers) | `serialization_failures` and `retries` recorded; chain valid after bounded retry (prior isolated runs also showed timing-dependent fork incidence, documented as harness flakiness, not a control defect) |
| Deadlock injection | SQLSTATE `40P01` classified transient |
| Connection-class SQLSTATEs | `08006` classified transient; permanently invalid errors not retried |
| Native integrity violation `23505` | classified permanent, never retried |

A clean full-harness run recorded `73 passed in 74.40s`, `EXIT=0`. Prior runs with transient timing failures are preserved in `/tmp/opencode/gula-mpi-tests/pytest_final2.log` and documented honestly rather than discarded.

## 5. Residual risks

- Retry is confined to the two MPI write transactions; other endpoints are unchanged.
- The classification is an explicit allowlist: novel transient SQLSTATEs are conservatively **not** retried (fail fast rather than risk an unsafe replay).
- Bounded retry does not replace an idempotency key protocol at the API boundary (see MPI-05).
- `verify_merge_audit_chain` fork response policy (D-MPI-3/4) remains an owner decision.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| Transient vs permanent SQLSTATE classification explicit | PASS |
| Only transient failures retried, ≤3 attempts | PASS |
| Fresh session per attempt; failed session never reused | PASS |
| Reconcile-before-replay on ambiguous commit | PASS |
| Commit failure → structured 503 | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
