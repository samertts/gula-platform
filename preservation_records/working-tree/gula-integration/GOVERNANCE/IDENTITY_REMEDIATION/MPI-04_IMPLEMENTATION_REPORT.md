# MPI-04 Implementation Report — Transaction Boundaries & SAVEPOINT Commit Correctness

**Status:** `PASS` (behaviour + boot evidence; not production readiness)
**Date:** 2026-11-18
**Scope:** Make outer transaction ownership explicit; guarantee SAVEPOINT RELEASE is never treated as a commit; handle commit failures without post-commit lazy reads.

---

## 1. Work done

`backend/app/services/mpi/api.py` now owns the outer transaction for the two write endpoints:

- `POST /mpi/resolve` and `POST /mpi/merge` run their whole transaction body inside `bounded_retry` using fresh `SessionLocal()` sessions. The resolver's SAVEPOINT is nested **inside** that outer transaction; its `RELEASE` is not a commit.
- **Response capture before commit:** `_resolve_response` and `_merge_response` materialise plain scalar values from ORM rows *before* `bounded_retry` commits, so `expire_on_commit=True` cannot turn response building into post-commit SELECTs on a possibly-dead session.
- Review-decision endpoints (`decide_pending_review`, both confirm and reject branches) capture the response dict before `db.commit()`, roll back and translate `SQLAlchemyError` into HTTP 503 on commit failure.
- All `SQLAlchemyError` commit failures map to `503` with a generic detail (no internal error text leaked).

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/api.py` | +207 / -42 | Transaction ownership, bounded retry wiring, pre-commit response capture, commit-error handling |
| `backend/tests/test_mpi_api_reliability.py` | **new** (5 tests) | Verify response survives `expire_on_commit`, idempotent replay, reconcile |

API contract is unchanged: response schemas (`ResolveResponse`, `MergeResponse`, `CitizenResponse`, `PendingReviewPage`) and route paths/methods are byte-identical at the OpenAPI level (see §4).

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `py_compile <changed scope>` | compile OK | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_api_reliability.py` | **5 passed**, 83.97 s | 0 |
| `ENV=test PYTHONPATH=. … pytest -q (6 focused files)` | **84 passed** | 0 |

## 4. Boot / contract stability

```
ENV=test PYTHONPATH=.:.. python -c "from app.factory import create_app; app=create_app(); ..."
routes: 125
openapi paths: 1805
/mpi/resolve ['post']
/mpi/merge ['post']
/mpi/citizens/{citizen_ulid} ['get']
```

No route, method, request model or response model changed.

## 5. Residual risks

- The advisory lock (MPI-01) and row locks (MPI-02) are transaction-scoped; a long outer transaction holds them longer. No statement timeout change was made.
- No distributed/across-service transaction exists; this correctness applies to the MPI service's own database transaction.
- `SessionLocal()` retry is not applied to every read endpoint — only the two write transactions that need commit safety.
- Production readiness is **not** claimed; this is isolated CI-style evidence.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| API owns outer transaction; SAVEPOINT never commits | PASS |
| Response materialised before commit | PASS |
| Commit failure → rollback + structured 503 | PASS |
| OpenAPI/route contract unchanged | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
