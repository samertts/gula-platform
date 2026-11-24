# GULA SEC-015 / F-01 — Independent Adversarial Review Package

**Prepared:** 2026-11-20 · **Classification:** R4 security change (audit write path)
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1`
**HEAD (unchanged):** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Requested verdict scope:** engineering correctness only. **No** `PRODUCTION READY`, no OD-001 acceptance, no release decision may be awarded by this review.
**Status:** `IMPLEMENTED` + `TESTED` locally; **NOT** `INDEPENDENTLY VERIFIED` until a fresh reviewer returns PASS against these exact bytes.

---

## 1. Why a new review is required

Review-2 (`GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md`, MD5 `f2b44ae6b23ffbbb3f65344aa2126134`) returned **PASS WITH CONDITIONS** against source MD5 `40c2598a02319b00c0351ddc689f7ed7` and raised unresolved **F-01 (MEDIUM)**. The owner authorized remediation; the source MD5 has changed to `566d64a2f8aa5c898a2511e1bbe304bd`. Review-2 explicitly did not review the new bytes and must not be treated as evidence for them.

Do **not** rely on: Review-1 (`ses_e0a984dadffemm3LClZf6oKOPo`), Review-2, prior `/tmp/opencode/sec015_*` logs (removed), or the historical full-suite result `5151 / 28 / 0`. Review the files below as they exist in the working tree.

## 2. Exact review surface

| File | MD5 | Lines | Role |
|---|---|---|---|
| `backend/app/services/audit_service.py` | `566d64a2f8aa5c898a2511e1bbe304bd` | 375 | Changed source (guard + one call site) |
| `backend/tests/unit/test_audit_chain_isolation_guard.py` | `9ccfa3e92fac50c247f0e839ea180cc8` | 401 | New PG16 regression suite |
| `backend/tests/unit/test_audit_chain_integrity.py` | `501e5fc8eb26f1cbd1824b5cfff61975` | 355 | Focused suite (unchanged) |
| `backend/tests/test_compliance_integrity.py` | `eb07739eefd982faf30ed673d23fd73d` | 480 | Compliance/tamper suite (unchanged) |
| `backend/app/models/audit_log.py` | inspect at review time | 27 | Table contract (unchanged) |
| `backend/migrations/versions/20250322_0002_perf_indexes_audit_protection.py` | inspect at review time | 129 | Append-only triggers (unchanged) |

**Verify these MD5s first.** Any mismatch invalidates the package. No other source, test, migration, config or call site was authored in this change.

## 3. Claimed implementation (to be challenged, not accepted)

`_require_audit_safe_isolation(db)` is invoked as the first statement of the PostgreSQL branch of `log_action()`, before `pg_advisory_xact_lock`, `nextval`, predecessor read, INSERT and anchor write. It reads:

1. `db.connection().get_isolation_level()` — claimed to be a live `SHOW transaction isolation level` in SQLAlchemy 2.0.51 (psycopg2 dialect), therefore observing both engine-level and per-transaction `SET TRANSACTION` settings.
2. `db.connection().get_execution_options().get("isolation_level")` — configured execution option.
3. `db.connection().connection.dbapi_connection.autocommit` — DBAPI autocommit flag, added because SQLAlchemy deliberately excludes AUTOCOMMIT from `get_isolation_level()`.

Accepted state: actual level `READ COMMITTED`, configured option empty or `READ COMMITTED`, autocommit `False`. Anything else — including an exception while reading any value — raises `AuditChainIsolationError` before any write. SQLite branch is claimed unchanged.

## 4. Mandatory adversarial challenge areas

The reviewer must actively try to falsify the following; a simple re-run of the author's tests is not sufficient.

### 4.1 Isolation-level enforcement
- Confirm the level is read from the **connection performing the write**, not from an engine default or a cached value. Try `SET TRANSACTION ISOLATION LEVEL ...`, `SET SESSION CHARACTERISTICS ...`, `SET default_transaction_isolation`, engine `isolation_level=`, and `Connection.execution_options(isolation_level=)`.
- Try a session that begins a transaction at READ COMMITTED and then changes the level mid-transaction. Is the guard still reading the level that governs the INSERT?
- Check normalization: case, hyphens, trailing whitespace, unusual driver strings. Can any accepted string map to a non-RC level?
- Check the order of statements in `log_action()` with AST/source inspection: is there ANY path between the guard and the INSERT where a level change could be issued?

### 4.2 Race conditions and transaction boundaries
- Prove the advisory lock is still held immediately before `nextval` / predecessor read / INSERT under READ COMMITTED across processes (not only threads).
- Determine whether the guard's own `SHOW` query can establish a snapshot that changes behavior at RC or RR/SER.
- Explore a competitor that takes the same advisory lock outside `log_action()`; check key derivation and whether a second lock guards the same chain.
- Check what happens if the caller commits or rolls back concurrently with the guard.

### 4.3 Connection-pool behavior
- Check `QueuePool`/`StaticPool`/`NullPool`, connection invalidation, `db.connection()` checkout semantics, and whether `db.connection()` can hand out a different connection from the one used by `db.execute()` later.
- Verify `get_execution_options()` cannot be stale after `execution_options()` changes or pool recycle.
- Verify the DBAPI `autocommit` flag is read from the same physical connection that performs the write.

### 4.4 Concurrent writers
- Reproduce two writers at RC where B starts while A holds the lock uncommitted; confirm B cannot read a stale predecessor. Try more than two writers and a mix of RC and RR/SER clients.
- Confirm rejected writers contribute no row, no sequence consumption and no anchor line. Check `pg_locks` / `pg_stat_activity` if useful.

### 4.5 Failure and rollback behavior
- Verify no INSERT, no `nextval`, no anchor emission on the rejection path.
- Verify caller rollback after a successful write leaves an intact chain and acceptable sequence gaps.
- Verify exceptions from the isolation probes fail closed (not open), including a driver that lacks `autocommit` (attribute absent → `None` → reject).
- Check exception type/message stability and whether any caller in the 206 call sites catches `RuntimeError` broadly and would swallow the refusal. Search for `except RuntimeError`, `except Exception`, and retry loops around `log_action()`.

### 4.6 Bypass paths
- Search for direct `AuditLog(...)` construction or direct INSERT into `audit_logs` in app code that bypasses `log_action()`.
- Search for `log_action` wrappers that set isolation, autocommit, or swap the session.
- Check `shared/audit/service.py`, `backend/app/kernel`, background tasks, and any SQL text that writes audit rows.
- Confirm append-only UPDATE/DELETE triggers still reject mutation after the guard.
- Check whether `verify_audit_chain()` or anchor files are modified (they must not be).

### 4.7 Regression/public contract
- Confirm `log_action()` parameter names/order/defaults are unchanged and all 206 call sites still compile.
- Confirm `_compute_chain_hash` field set, `verify_audit_chain()` ordering, timestamp canonicalization and SQLite branch are byte-equivalent to the reviewed version outside the new guard.
- Run the focused and related suites independently; do not accept a combined count alone.

## 5. Required verification commands

From `backend/`, using a Python 3.12 environment with the repo dependencies:

```bash
export ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. REDIS_URL="" DATABASE_URL="sqlite:///:memory:"
PY=/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python

$PY -m pytest -q --no-header -p no:cacheprovider tests/unit/test_audit_chain_integrity.py
$PY -m pytest -q --no-header -p no:cacheprovider \
  tests/unit/test_audit_chain_integrity.py \
  tests/unit/test_audit_bypass_regression.py \
  tests/unit/test_audit_positional_regression.py \
  tests/unit/test_audit_anchor.py \
  tests/test_compliance_integrity.py \
  tests/test_mpi_hash_chain_integrity.py

export GULA_AUDIT_PG16_TEST_DSN='postgresql://<synthetic-creds>@127.0.0.1:<disposable-port>/f01test'
$PY -m pytest -q --no-header -p no:cacheprovider tests/unit/test_audit_chain_isolation_guard.py
```

Author's recorded results: 13 passed (`/tmp/opencode/f01_verify_focused_final.log`), 73 passed (`/tmp/opencode/f01_verify_related.log`), 12 passed (`/tmp/opencode/f01_verify_pg16_final.log`), all exit 0 on Python 3.12.13 / SQLAlchemy 2.0.51 / psycopg2 2.9.12 / pytest 9.1.1 / PostgreSQL 16.14. **Treat these as claims; generate your own logs.** Use only a disposable PG16 database and synthetic data.

## 6. Findings format and verdict

Report each finding with: ID, severity (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`/`INFORMATIONAL`), exact file:line, reproduction command, observed output, impact, and required correction. Then give one verdict:

- `PASS` — F-01 is closed for the engineering scope; may be used as OD-001 evidence **only after the owner records acceptance**.
- `PASS WITH CONDITIONS` — list unresolved conditions; OD-001 stays `BLOCKED`.
- `FAIL` — F-01 remains open or a new HIGH/CRITICAL issue was introduced; OD-001 stays `BLOCKED`.

The reviewer must state explicitly that no `PRODUCTION READY` or `INDEPENDENTLY VERIFIED` is self-awarded by the implementation agent.

## 7. Repository safety constraints for the reviewer

Work read-only where possible. Preserve the 20 staged `R100` renames, all staged/unstaged/untracked work, the three protected MD5s, branch and HEAD. Never use `git reset`, `clean`, `checkout --`, `restore`, `stash`, force-push, `git add .`/`-A`, or destructive DB operations. Do not commit, push, merge, open a PR or deploy. Do not contact production services or use PHI/secrets.

## 8. Current posture

**HOLD** · Stable v1.0.0 **NOT declared** · `production_ready_items = 0` · OD-001 `BLOCKED` pending this review + owner acceptance · no commit/push/PR/deploy performed.
