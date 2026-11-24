# MPI-02 Implementation Report — Deterministic Lock Ordering

**Status:** `PASS` (isolated-test + source-invariant evidence; not production readiness)
**Date:** 2026-11-18
**Scope:** Eliminate opposing-order deadlocks on all MPI merge paths by locking rows in ascending immutable-key order in one statement.

---

## 1. Work done

- **MPI resolver path** (`backend/app/services/mpi/resolver.py`): the existing single `with_for_update()` statement, already ordered by the immutable primary key `.order_by(Citizen.id.asc())`, was **preserved exactly**. It runs after the advisory chain lock and before the SAVEPOINT. This preserves the user's pre-existing source-invariant test.
- **Canonical service path** (`backend/app/services/mpi/canonical_service.py`): replaced two independent unordered `.first()` lookups with **one** `SELECT … WHERE id IN (target, source) ORDER BY id ASC FOR UPDATE`, then resolved the target/source from a by-id map. This removes the opposite-acquisition-order deadlock on the canonical merge path.
- Also fixed the latent `NotFoundError` `NameError` in `merge_canonicals` by importing `ConflictError`/`NotFoundError` at module level.

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/resolver.py` | lock-order comment added; source invariant untouched | Document global lock order; keep user's exact `with_for_update()` block |
| `backend/app/services/mpi/canonical_service.py` | +19 / -6 | One ascending-key `FOR UPDATE` statement; atomic version bumps; fix import-time NameError |
| `backend/tests/test_mpi_api_reliability.py` | **new** (5 tests) | Verify reversed-ULID replay returns original merge result without new audit |
| `backend/tests/test_mpi_hash_chain_integrity.py` | **untracked user file — preserved unchanged** | Its source-invariant assertions (`source.count("with_for_update()") == 1`, `.order_by(Citizen.id.asc())` in the locked block) still pass |

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_hash_chain_integrity.py tests/test_mpi_merge_integrity.py …` | **84 passed** (incl. source-invariant test) | 0 |
| Broader regression (10 files) | **137 passed**, 79.17 s | 0 |

## 4. PostgreSQL evidence (isolated `mpi_test`, synthetic only)

| Scenario | Result |
|---|---|
| Opposite lock order (two overlapping row sets, reversed acquisition) | `deadlocks=1`, SQLSTATE `40P01` — deadlock reproduced |
| Ascending lock order, 10 workers | `deadlocks=0`, `stuck=0`, `worker_errors=0` |
| Actual `merge_citizens`, 2/5/10/20 workers | `errors=0`, `chain_valid=true`, audits = worker count |
| Same citizen pair, 10 concurrent merges | `audits=1`, `worker_errors=0` — no duplicate merge append |

Full harness: `73 passed in 74.40s`, `EXIT=0`.

## 5. Residual risks

- Deadlock-free proof is for the **MPI merge paths only**. Other services that touch the same tables through different code are outside this scope (MPI-06 inventory).
- `SELECT … FOR UPDATE` blocks on the primary/secondary rows; a long-running merge can delay unrelated merges of the same citizens — by design, not a defect.
- Row locks are database-transaction-scoped; outer transaction ownership is covered in MPI-04.
- Cross-domain reference repointing and unmerge remain unresolved (D-MPI-3).

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| One ascending-order `FOR UPDATE` statement per merge path | PASS |
| Both call orders complete without deadlock | PASS |
| User source-invariant test preserved and passing | PASS |
| No schema/API change | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
