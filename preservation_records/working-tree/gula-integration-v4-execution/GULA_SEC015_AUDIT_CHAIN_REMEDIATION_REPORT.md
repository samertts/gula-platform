# GULA SEC-015 — Audit Chain Regression Remediation Report

**Finding:** SEC-015 — SQLite multi-row audit-chain linkage regression  
**Directive:** GULA-PBR-2026-11-19, §3 (Priority P0)  
**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`  
**Baseline HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`  
**Date:** 2026-11-19  
**Independent review:** fresh-context reviewer, session `ses_e0a984dadffemm3LClZf6oKOPo` — **VERDICT: PASS** (engineering scope)  
**Status:** `INDEPENDENTLY VERIFIED` (engineering scope; awarded by the fresh-context reviewer, not self-awarded)

---

## 1. Executive summary

The SQLite audit-chain writer read its predecessor hash **after** flushing the new row, so the just-inserted NULL-hash row became its own predecessor and every row chained to the genesis hash. The defect was a regression of an earlier correct fix. The minimal correction restores pre-insert predecessor resolution on both supported dialects and adds transaction-scoped serialization so concurrent writers cannot fork the chain. The PostgreSQL path, append-only trigger, timestamp canonicalization, tamper detection and public `log_action()` contract are unchanged.

**Release posture:** `HOLD`. Stable v1.0.0 **NOT declared**. No `PRODUCTION READY`. No commit authorized.

---

## 2. Root cause and historical regression

| Commit | Date | Effect |
|---|---|---|
| `2cdc5479` | 2026-08-01 | Corrected SQLite chain linkage: predecessor hash computed **before** the insert; added dialect-independent timestamp normalization. Removed the old hash re-stitching workaround from `test_compliance_integrity.py`. |
| `2fb4fd11` | 2026-08-11 | Refactored timestamp normalization into `_canonical_audit_timestamp()`; behavior preserved. This is the canonicalization present at HEAD — it was **not** dropped. |
| `f0b021bd3` | 2026-09-08 | Regressed the non-PostgreSQL branch to `db.add(entry); db.flush(); prev_hash = _get_last_chain_hash(db)`. |

**Exact mechanism:** `_get_last_chain_hash()` (`audit_service.py:117-123`) executes `SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1`. After `db.flush()` the newly inserted row is the max-id row and its `chain_hash` is still `NULL`; the helper therefore returns `_GENESIS_HASH` (64 zeros) for every row. `verify_audit_chain()` then recomputes each hash from the real predecessor and reports `tampered` on any multi-row SQLite chain, even though no data was modified.

**Contributing factors ruled out:**
- **Timestamp normalization** — already correct at HEAD via `_canonical_audit_timestamp()`; the old `test_compliance_integrity.py` docstring blaming tz stripping was an imprecise description of the real defect.
- **Query ordering** — `ORDER BY id DESC LIMIT 1` is correct; the problem was *when* it was called, not its SQL.
- **NULL hashes** — a symptom of the write ordering, not an independent cause; legacy NULL rows are still deliberately skipped by verification.
- **PostgreSQL** — unaffected: it pre-assigns the id with `nextval(...)` and computes the hash before INSERT; the append-only trigger rejects UPDATE, so no re-flush path exists.

**Historical workaround:** `test_compliance_integrity.py::_seed_chain_persisted` rewrote every `chain_hash` after commit to hide the divergence. This masked the regression: tests passed while the persisted chain was invalid.

---

## 3. Code changes (exact, minimal)

### 3.1 `backend/app/services/audit_service.py`

| Change | Purpose |
|---|---|
| Added `_AUDIT_CHAIN_ADVISORY_KEY = 0x47554C4155444954` (`"GULAUDIT"`, fits signed BIGINT) | Single shared advisory-lock key for the canonical chain. |
| PostgreSQL branch: `SELECT pg_advisory_xact_lock(:key)` **before** predecessor read | Serializes writers across processes/pool workers for the transaction lifetime; released on commit or rollback. Prevents two writers reading the same predecessor and forking the chain. |
| SQLite branch: `UPDATE audit_logs SET id = id WHERE 1 = 0` **before** predecessor read | Acquires SQLite's transaction-scoped RESERVED write lock, held until caller commit/rollback. A zero-row `UPDATE` still starts a write transaction; the optimizer does not skip the write opcode. No column values change, so hash verification is unaffected. |
| SQLite branch: moved `prev_hash = _get_last_chain_hash(db)` to **before** `db.add(entry)` | Restores the `2cdc5479` ordering. The row is still flushed once to obtain its auto-assigned id (the hash includes `id`), hashed, then flushed again. |
| No other change | `log_action()` signature unchanged; `_compute_chain_hash`, `_canonical_audit_timestamp`, `_get_last_chain_hash`, `_write_anchor`, `verify_audit_chain` byte-unchanged. |

**Dialect-serialization decision:** correctness of a single ordered hash chain requires that the predecessor read and the caller's commit be atomic with respect to other writers. `log_action()` does not own the transaction boundary, so a process-local lock would be released before commit and is insufficient (demonstrated empirically: the earlier RLock attempt still forked the chain). A transaction-scoped DB-level lock is the only safe approach that preserves the public API. SQLite is a dev/test single-file dialect; production runs on PostgreSQL.

**Precondition (documented per reviewer MEDIUM finding):** the PG advisory lock guarantees correctness under the default `READ COMMITTED` isolation, which is what the application uses (no isolation-level override exists in app code). Under `REPEATABLE READ`/`SERIALIZABLE` a snapshot taken before the predecessor commits could still be stale despite the lock. Callers must not change the isolation level without revisiting this design. `nextval()` is non-transactional, so rollback creates benign id **gaps**, not chain breaks.

### 3.2 `backend/tests/unit/test_audit_chain_integrity.py` (new, 13 tests)

Covers: first event from genesis; two sequential events; multiple events in one transaction; multiple committed transactions; persisted-hash verification without repair; canonical UTC timestamp; tampered payload; tampered predecessor hash; missing predecessor; NULL legacy hash; structural AST guard (predecessor read before insert and lock before read in **both** dialect branches); 4-thread/12-row concurrent writers; rolled-back writer. All payloads are synthetic; no production data, no secrets, no manual hash re-stitching.

### 3.3 `backend/tests/test_compliance_integrity.py`

`_seed_chain_persisted()` no longer rewrites `chain_hash` after commit. It returns rows exactly as `log_action` persisted them, so the 21 compliance tests now validate the real chain. Imports `_GENESIS_HASH` and `_compute_chain_hash` remain in use by other tests in the file.

---

## 4. Test evidence

| Stage | Command / artifact | Result |
|---|---|---|
| Red baseline (unfixed code) | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. python -m pytest tests/unit/test_audit_chain_integrity.py -q` → `/tmp/opencode/sec015_red_baseline.log` | **7 failed / 6 passed** — defect reproduced |
| Green (after fix) | same command → `/tmp/opencode/sec015_green_final.log` | **13 passed** (97.06s), exit 0 |
| Related audit suites (single sequential pytest) | `pytest -q tests/unit/test_audit_chain_integrity.py tests/unit/test_audit_bypass_regression.py tests/unit/test_audit_positional_regression.py tests/unit/test_audit_anchor.py tests/test_compliance_integrity.py tests/test_mpi_hash_chain_integrity.py` → `/tmp/opencode/sec015_related_audit.log` | **73 passed**, exit 0 — includes compliance tests validating real persisted hashes |
| Disposable PostgreSQL 16 verification | `PYTHONPATH=... python /tmp/opencode/sec015_pg_verify.py` → `/tmp/opencode/sec015_pg_verify.log` | **PG_VERIFY_RESULT=PASS** — serial sequence `public.audit_logs_id_seq`; sequential chain + persisted verification; tz-aware timestamps; append-only trigger rejects UPDATE; 4 concurrent writers / 12 rows / single unbroken chain |
| Lint / compile | `ruff check tests/unit/test_audit_chain_integrity.py` → exit 0; `py_compile` both files → OK | Clean. `ruff check app/services/audit_service.py` reports one **pre-existing** SIM108 at `_canonical_audit_timestamp()` (commit `2fb4fd11`), not introduced by this change; deliberately left untouched to keep the diff minimal. |
| Full backend suite (once, after stabilization, no concurrent pytest) | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. python -m pytest tests/ -q` → `/tmp/opencode/sec015_full_suite.log` (PID 859100) | **5151 passed / 28 skipped / 0 failed, EXIT=0, 203 warnings in 636.19s (10m36s)** — exactly +13 vs the historical 5138 (the new SEC-015 test file); no concurrent pytest. Run against the final production code; the only later change was the test-only LOW assertion fix (§5), re-verified by the 13/13 focused rerun — production code is byte-identical, so no full-suite rerun was performed per the directive (full suite once; no rerun after minor test/doc edits). |

PostgreSQL verification used a **new disposable container** (`gula-sec015-pg-verify`, PG16) on an isolated port; it was removed afterward. The shared `gula-postgres` container was never touched. No production DB/Redis, real PHI, or secrets were used.

---

## 5. Independent review (fresh context)

Reviewer session `ses_e0a984dadffemm3LClZf6oKOPo` inspected the exact changed files, both historical commits, counterexamples, negative tests, call sites and regression risks. **VERDICT: PASS** — safe to mark `INDEPENDENTLY VERIFIED (engineering scope)`; no CRITICAL/HIGH finding.

| Reviewer finding | Severity | Resolution |
|---|---|---|
| PG advisory lock correctness implicitly assumes `READ COMMITTED` | MEDIUM | **Documented** in §3.1 above. No application caller changes isolation level; PG harness PASS. Non-blocking latent precondition, not introduced by this fix. |
| `assert third_id >= second_id` in `test_missing_predecessor_is_detected` is tautological | LOW | **Fixed** after the full suite finished (no test-file edits mid-run). The reviewer's *suggested* replacement — asserting `third_id` also appears in `broken_entries` — was tried first and **empirically failed** (`assert 3 in [2]`): `verify_audit_chain` feeds each row's **stored** hash forward as the next predecessor, so a deleted row is detected only at the first surviving boundary row (row 2), while row 3 stays internally consistent and is correctly NOT flagged. Replaced with the stronger, correct assertion `broken_ids == [second_id]`, which pins the exact boundary-detection behaviour. Rerun: **13/13 passed** (`/tmp/opencode/sec015_green_lowfix.log`, 78.83s, EXIT=0). The substantive original assertion (`second_id in broken_entries`) failed on the red baseline and is preserved within the stricter form. |

Explicit reviewer confirmations: root cause real; SQLite zero-row UPDATE acquires and holds the write lock; no autocommit caller exists; PG key fits BIGINT; `nextval` gaps are benign; no new deadlock cycle (the only other advisory lock guards a different chain); no-op UPDATE is SQLite-only and trigger-safe; tamper tests meaningful; `_seed_chain_persisted` change sound; ~200 call sites unaffected; no weakening, DDL, contract change, secrets or PHI.

One **pre-existing, not introduced** behavior noted by the reviewer: `_write_anchor()` writes before commit, so a rollback can leave an anchor line for a non-existent row. Recorded here as a known limitation; not changed in this minimal fix.

---

## 6. Residual risks and limitations

1. **SQLite multi-process writers** are serialized through the file-level RESERVED lock only for a single database file; production is PostgreSQL and multi-process SQLite is not a supported deployment.
2. **READ COMMITTED** isolation is a precondition for the PG advisory-lock design (§3.1).
3. **Anchor checkpoint timing** is pre-commit (pre-existing); a rollback can leave an anchor entry for a row that was never persisted.
4. **`shared/audit/service.py` schema mismatch** remains a separately documented `BLOCKED` finding (see `GULA_AUDIT_ARCHITECTURE_COMPLETENESS_REPORT.md`); it was deliberately not repaired.
5. **No runtime/production verification** beyond the disposable PG16 harness; no operational, clinical, legal or regulatory claim is made.

---

## 7. Strict status classification

| Item | Status |
|---|---|
| SEC-015 root cause established | `INDEPENDENTLY VERIFIED` (engineering scope — fresh-context reviewer) |
| SEC-015 code correction | `INDEPENDENTLY VERIFIED` (engineering scope — fresh-context reviewer) |
| Focused regression suite (13) | `TESTED` |
| Related audit suites (73) | `TESTED` |
| PostgreSQL path (disposable PG16) | `TESTED` |
| Full backend suite | `TESTED` — 5151 passed / 28 skipped / 0 failed, EXIT=0 (636.19s) |
| Exact-path commit | `BLOCKED` (no-commit authority; mixed provenance in other files) |
| Production deployment / operational verification | `BLOCKED` (no environment or authorization) |

---

## 8. Non-claims

No `PRODUCTION READY`. No clinical, legal, regulatory, ministerial or release approval. No commit, push, merge, PR or deployment. No production DB/Redis access, no real PHI, no secrets. Historical result `5138 passed / 28 skipped / 0 failed (12m13s)` from `/tmp/opencode/auditfix_full_suite_clean.log` is preserved as evidence of the pre-SEC-015 tree and is not overwritten by this report. Standing release decision remains **HOLD**; Stable v1.0.0 is **NOT declared**; `production_ready_items = 0`.

---

## 9. Evidence index

- `/tmp/opencode/sec015_red_baseline.log` — red baseline (7 failed / 6 passed)
- `/tmp/opencode/sec015_green_final.log` — green focused suite (13 passed)
- `/tmp/opencode/sec015_green_lowfix.log` — focused suite after LOW assertion correction (13 passed, 78.83s)
- `/tmp/opencode/sec015_related_audit.log` — related audit suites (73 passed)
- `/tmp/opencode/sec015_pg_verify.log` — disposable PG16 verification (PASS)
- `/tmp/opencode/sec015_full_suite.log` — post-stabilization full suite (5151 passed / 28 skipped / 0 failed, EXIT=0, 636.19s, 203 warnings)
- `/tmp/opencode/auditfix_full_suite_clean.log` — preserved pre-change full suite (5138/28/0, EXIT=0)
- `git show 2cdc5479`, `git show f0b021bd3`, `git show 2fb4fd11` — historical evidence

---

## 10. Additive F-01 remediation — owner authorization 2026-11-20 (NOT independently reviewed)

Sections 1–9 and all historical results above are preserved verbatim. The owner explicitly authorized `GULA-SEC015-F01-REMEDIATION`; Review-2's unresolved MEDIUM finding F-01 has been addressed in a separate, narrowly scoped change.

| Item | Record |
|---|---|
| Finding | F-01 — PG advisory-lock chain fork at `REPEATABLE READ` / `SERIALIZABLE`; no application enforcement |
| Source before / after | `backend/app/services/audit_service.py` MD5 `40c2598a02319b00c0351ddc689f7ed7` → `566d64a2f8aa5c898a2511e1bbe304bd` |
| New test file | `backend/tests/unit/test_audit_chain_isolation_guard.py`, MD5 `9ccfa3e92fac50c247f0e839ea180cc8`, 12 tests |
| Fix | Fail-fast guard on the actual active transaction isolation level plus DBAPI autocommit state, before the advisory lock and before any audit data statement; unknown state fails closed; only `READ COMMITTED` accepted |
| Additional bypass closed | SQLAlchemy `get_isolation_level()` reports `READ COMMITTED` even under `AUTOCOMMIT`; the DBAPI `autocommit` flag is now checked as well |
| Fresh evidence | focused 13/13 (`/tmp/opencode/f01_verify_focused_final.log`); related 73/73 (`/tmp/opencode/f01_verify_related.log`); PG16 three-isolation + concurrency + rollback + sequence + trigger suite 12/12 (`/tmp/opencode/f01_verify_pg16_final.log`); all exits 0 |
| Disposable environment | `gula-f01-pg16-verify` (`postgres:16-alpine`, PG 16.14), isolated port, synthetic credentials, throwaway DB, removed after use; no production service touched |
| Status | `IMPLEMENTED` + `TESTED` for the scoped change. **Not** `INDEPENDENTLY VERIFIED` — a fresh adversarial reviewer must inspect the new MD5s before OD-001 can be reconsidered |
| Unchanged | §5 Review-1 award remains historical context; Review-2 verdict `PASS WITH CONDITIONS` remains recorded; F-03/F-06 and `shared/audit/service.py` schema mismatch remain out of scope; HOLD stands; Stable v1.0.0 not declared |

Full implementation evidence: `GULA_SEC015_F01_REMEDIATION_PACKAGE.md` §8. Review handoff: `GULA_SEC015_F01_INDEPENDENT_REVIEW_PACKAGE.md`.
