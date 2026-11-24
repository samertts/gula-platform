# MPI-08 Implementation Report — In-Transaction Audit Verification (Detection-Only)

**Status:** `PASS` (verification implemented and tested; detection-only by design)
**Date:** 2026-11-18
**Scope:** Verify that every freshly appended audit segment links to the tail read under the advisory lock and that each stored `entry_hash` reproduces from persisted columns — inside the SAVEPOINT, before outer commit.

---

## 1. Work done

In `backend/app/services/mpi/resolver.py`:

- Extracted the exact nine-column hash input into `_audit_row_dict(row)` and `_audit_entry_hash(row)`, shared by the full-chain verifier and the new segment verifier so they **cannot drift apart**. Floats are normalised via `float()` to tolerate SQLite/PostgreSQL numeric representation differences.
- Added `_verify_audit_segment(db, first_id, expected_prev)`: inside the merge SAVEPOINT, re-reads rows `id >= first_id`, checks `prev_hash` linkage from the locked tail and recomputes each `entry_hash`; raises `RuntimeError` on any mismatch, which rolls the SAVEPOINT back.
- `verify_merge_audit_chain(db)` refactored to use `_audit_entry_hash`, preserving its public result (`ChainVerificationResult(valid, checked, errors)`) and error messages.
- In `merge_citizens`, the tail is read via `_last_audit_hash(db)` **under the advisory lock**, then the audit is appended, flushed, and the segment verified before the outer commit.

**This is detection-only:** verification raises/rolls back locally; it never auto-repairs a chain and never claims a fork-response policy (D-MPI-3/4 remain owner decisions).

## 2. Modified files and reasons

| File | Change | Reason |
|---|---|---|
| `backend/app/services/mpi/resolver.py` | +232 / -30 | Shared hash helpers, in-SAVEPOINT segment verification, tail read under lock |
| `backend/tests/test_mpi_hash_chain_integrity.py` | **untracked user file — preserved unchanged** | 11 tamper/fork detection tests still pass |
| `backend/tests/test_mpi_merge_integrity.py` | **untracked user file — preserved unchanged** | 6 merge-integrity tests still pass |

## 3. Commands and results (exit codes)

| Command | Result | Exit |
|---|---|---|
| `ruff check --output-format concise <changed scope>` | `All checks passed!` | 0 |
| `ENV=test PYTHONPATH=. … pytest -q tests/test_mpi_hash_chain_integrity.py tests/test_mpi_merge_integrity.py …` | **84 passed** (11 chain-integrity + 6 merge-integrity included) | 0 |
| Broader regression (10 files) | **137 passed** | 0 |

## 4. PostgreSQL evidence (isolated `mpi_test`, synthetic only)

| Scenario | Result |
|---|---|
| Actual `merge_citizens`, 2/5/10/20 workers | `chain_valid=true` in all scenarios; `checked == workers` |
| Actual `resolve_identity` genesis, 20 workers | `chain_valid=true`, `checked=20` |
| Same pair, 10 concurrent merges | `chain_valid=true`, `audits=1` |
| Full-chain verifier after all implementation tests | `valid=true`, 0 errors |

Tamper-detection coverage from the preserved user tests: forged `entry_hash`, forged `prev_hash` pointing at genesis, and full-chain re-walk all detected with `valid=false` (verified in SQLite test run). Tampered rows are never silently accepted.

## 5. Residual risks

- Verification is **detection-only**: a fork discovered by `verify_merge_audit_chain` in already-committed data raises an incident; there is no automatic repair and no agreed owner response policy (D-MPI-3/4).
- The segment verifier proves local linkage/hash correctness; it does not prove that no other process wrote outside the MPI advisory lock.
- Full-chain verification is O(n) over all audit rows; no incremental checkpoint/caching was added.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| Segment verified inside SAVEPOINT before outer commit | PASS |
| Hash input shared with full-chain verifier (no drift) | PASS |
| Tamper/fork detection preserved and passing | PASS |
| Detection-only; no fabricated policy or repair | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
