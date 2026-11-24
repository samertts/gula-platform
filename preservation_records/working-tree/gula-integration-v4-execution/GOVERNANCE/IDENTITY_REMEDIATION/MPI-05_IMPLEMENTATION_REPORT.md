# MPI-05 Implementation Report — Idempotency & Replay Safety

**Status:** `PASS` (synthetic + isolated PostgreSQL evidence; not production readiness)
**Date:** 2026-11-18
**Scope:** Make resolve and manual-merge re-invocation safe, including ambiguous commit and reversed-ULID replay.

---

## 1. Work done

- **Resolve idempotency:** relies on the **existing** `uq_identity_claims_lab_patient` unique constraint. `_resolve_reconcile(lab_id, local_patient_id)` resolves an in-doubt commit with a fresh session by looking up the persisted `IdentityClaim` and returning the original outcome; `created=False` on replay. No new DB constraint was added.
- **Merge idempotency:** `_find_merge_replay(db, primary_ulid, secondary_ulid, reason)` matches the **unordered** citizen-id pair on the `MergeAudit` ledger via `and_`/`or_` predicates, so a reconnecting client that swaps primary/secondary still receives the original audited result with no new mutation. A replay carrying a **different reason** raises HTTP 409 rather than being silently accepted.
- Both write endpoints call replay detection/reconciliation before mutating and inside `bounded_retry`'s reconcile hook.

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/api.py` | replay helpers + wiring | Idempotent resolve/merge under retry and reconnect |
| `backend/tests/test_mpi_api_reliability.py` | **new** (5 tests) | Reversed-ULID replay, conflicting-reason 409, pre-commit capture, reconcile hit/miss |
| `backend/app/services/mpi/models.py` | **unchanged** | Existing unique constraint is sufficient; no schema change authorized |
| `backend/app/services/mpi/schemas.py` | **unchanged** | API contract unchanged |

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_api_reliability.py` | **5 passed**, 83.97 s | 0 |
| `ENV=test PYTHONPATH=. … pytest -q (6 focused files)` | **84 passed** | 0 |

## 4. PostgreSQL evidence (isolated `mpi_test`, synthetic only)

| Scenario | Result |
|---|---|
| Same citizen pair, 10 concurrent merges | `audits=1`, `worker_errors=0` |
| Sequential replay of applied merge | Original result returned, **0 new audit rows** |
| Concurrent replay | Original result returned, no duplicate mutation |
| Conflicting replay reason | `409` / conflict recorded, no write |
| In-doubt resolve commit | Reconciled by claim key to original result (`created=False`) |
| Naive client retry (no idempotency) | Duplicate writes reproduced in baseline strategy |
| Idempotent client retry | No duplicates |

Full harness: `73 passed in 74.40s`, `EXIT=0`.

## 5. Residual risks

- No new DB unique constraint or idempotency-key header was added; replay detection relies on the **existing** claim constraint and the audit ledger.
- Replay is matched on the unordered ULID pair plus exact reason string; a caller that changes both ULIDs and reason is treated as a new merge (by design).
- The "which caller wins" policy for concurrent first resolve is D-MPI-5 and remains an owner decision. This implementation prevents duplicates but does not formally define winner semantics.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| Resolve replay returns original outcome, no duplicate claim | PASS |
| Merge replay (incl. reversed ULIDs) returns original audit result | PASS |
| Conflicting replay rejected (409) | PASS |
| No new schema / API contract change | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
