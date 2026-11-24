# GULA SEC-015 — F-01 Remediation Package

**Directive:** `GULA-MASTER-COMPLETION-2026-11-20` §5 / §23(D); owner authorization `GULA-SEC015-F01-REMEDIATION` dated 2026-11-20
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1`
**Baseline HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` (unchanged — no commit)
**Prepared:** 2026-11-20 · **Classification:** R4 — audit behavior change requiring explicit review
**Status:** `IMPLEMENTED` + `TESTED` for the scoped source/test change; **NOT** `INDEPENDENTLY VERIFIED` (fresh review pending); OD-001 remains `BLOCKED`; release stays `HOLD`.
**Authority:** the owner explicitly authorized implementation and testing only. This package does **not** authorize a commit, push, merge, deployment, OD-001 acceptance, or a change to HOLD. The sections below are preserved as the original preparation record; §8 records the authorized implementation and its evidence.

---

## 1. Purpose

Provide an exact, reviewable remedy for Finding **F-01 (MEDIUM)** of `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md`, so the owner can decide OD-001 from concrete evidence rather than an open-ended condition. F-01 is the only unresolved condition that blocks OD-001 acceptance.

This document is additive. No source, test, migration, configuration, or existing report was changed by its creation.

---

## 2. Problem statement (evidence, not hypothesis)

| Item | Evidence |
|---|---|
| Reviewed source | `backend/app/services/audit_service.py` MD5 `40c2598a02319b00c0351ddc689f7ed7` (unchanged by this package) |
| Vulnerable path | `log_action()` PG branch, lines 225–244: `db.execute(SELECT pg_advisory_xact_lock(:key))` → `nextval(...)` → `_get_last_chain_hash()` → `INSERT` |
| Root mechanism | Under `REPEATABLE READ` / `SERIALIZABLE` the transaction snapshot predates the lock waiter's predecessor commit; the advisory lock serializes *execution* but cannot refresh the snapshot, so the waiter reads genesis and forks the chain |
| Empirical result | Review-2 §6: `READ COMMITTED` → `INTACT` (`broken=[]`); `REPEATABLE READ` and `SERIALIZABLE` → `FORKED` (`broken=[2]`), with the advisory lock as the first data statement |
| Enforcement gap | Review-2 §6: no isolation-level setting or check exists anywhere in `backend/app`; the supported level is an **unenforced precondition** |
| Public contract | `log_action()` signature and the 206 call sites are byte-unchanged; no caller found that sets an isolation level |

Impact if unaddressed: legitimate audit events can be reported as tampered, and the tamper-evident control becomes unreliable on any future or external isolation-level change. The current production configuration (READ COMMITTED) is correct but unprotected against drift.

---

## 3. Proposed change (Option B — narrow fail-fast; RECOMMENDED)

### 3.1 Rationale

Enforcing READ COMMITTED globally in `backend/app/database.py` would alter every database session on the platform (broader than the audit defect and outside this package's scope). The fail-fast guard confines the change to the audit write path, preserves behavior for all supported callers, and converts an unsafe silent fork into an explicit, auditable refusal.

### 3.2 Exact code shape (proposed — not applied)

In `backend/app/services/audit_service.py`, add a narrow exception and a guard immediately **before** the advisory-lock statement, inside the `if is_postgres:` branch:

```python
class AuditChainIsolationError(RuntimeError):
    """Raised when DB isolation cannot guarantee audit-chain serialization."""

_AUDIT_SAFE_ISOLATION_LEVELS = frozenset({"READ COMMITTED", "READ-COMMITTED"})

# ... inside log_action(), after bind/is_postgres detection, before the lock:
if is_postgres:
    effective_isolation = str(db.connection().get_isolation_level() or "").upper()
    if effective_isolation not in _AUDIT_SAFE_ISOLATION_LEVELS:
        raise AuditChainIsolationError(
            "audit chain requires READ COMMITTED isolation; "
            f"got {effective_isolation!r}"
        )
    db.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": _AUDIT_CHAIN_ADVISORY_KEY},
    )
    # ... unchanged remainder (nextval -> _get_last_chain_hash -> INSERT)
```

**Invariants of the proposal:**

- The guard runs **before** any data statement in the transaction, so no snapshot is established and no advisory lock is taken on the rejected path.
- No `INSERT`, no `nextval` consumption, and no `_write_anchor()` call occur on rejection (the anchor write is at lines 264–266, after the branch).
- The exception is raised from `log_action()` to the caller; callers that do not catch it roll back the transaction under existing `SessionLocal` / `ReadSessionLocal` handling (`autocommit=False`).
- SQLite branch (lines 245–263) is untouched: its write-reservation proof is dialect-independent of this guard.
- `log_action()` signature, `_compute_chain_hash`, `_canonical_audit_timestamp`, `verify_audit_chain()`, and the append-only triggers are untouched.

**Design choices requiring explicit reviewer confirmation:**

1. Exception class `AuditChainIsolationError(RuntimeError)` vs. reusing an existing domain exception — no suitable audit-specific exception currently exists in this module.
2. `db.connection().get_isolation_level()` (SQLAlchemy `Connection` API, available in the pinned 2.1.9 and in 1.4+) vs. `db.get_isolation_level()` (SQLAlchemy 2.0+ `Session` API). The chosen call must be exercised against the repository-pinned SQLAlchemy version.
3. Accepted string forms: `READ COMMITTED` / `READ-COMMITTED`; both uppercase-normalized. `None`, `AUTOCOMMIT`, `REPEATABLE READ`, `SERIALIZABLE` are all rejected.

### 3.3 Alternative (Option A — engine-level enforcement), recorded but not recommended

Set `isolation_level="READ COMMITTED"` on every engine that can write audit logs. This is broader (all sessions in `backend/app/database.py`), can still be overridden per-connection by a caller, and does not fail fast if an external system opens a transaction at another level. Requires its own review if chosen instead of Option B.

---

## 4. Regression test plan (disposable PostgreSQL 16 only)

A new test module, proposed path `backend/tests/unit/test_audit_chain_isolation_guard.py`, using **synthetic data only** and a disposable PG16 database created and dropped within the test session. No operational `gula` database and no shared Redis/RabbitMQ/MinIO may be contacted.

| Case | Setup | Expected assertion |
|---|---|---|
| RC-1 | Two writers at `READ COMMITTED`; A holds advisory lock uncommitted 1.5 s; B starts at +0.25 s | B waits, reads A's committed hash, both insert; `verify_audit_chain()` → `intact` |
| RR-1 | Same at `REPEATABLE READ` | `AuditChainIsolationError` raised **before** INSERT; zero audit rows added by B; no sequence value consumed by B |
| SER-1 | Same at `SERIALIZABLE` | identical refusal to RR-1 |
| NONE-1 | Isolation level `None` / unset connection default reported as `AUTOCOMMIT` | refusal (fail closed), no INSERT |
| ANCHOR-1 | Rejected writer followed by anchor-directory inspection | no new anchor line for a row that was never persisted |
| SIGN-1 | `log_action()` signature and `_compute_chain_hash` field set | byte-unchanged vs. reviewed MD5 `40c2598a…` |
| SQLITE-1 | SQLite branch with guard present | guard not invoked; chain still serializes; focused 13/13 suite remains green |

**Verification command shape** (exact interpreter/log IDs to be recorded at execution time):

```bash
cd backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=.:.. <disposable-py3.12> -m pytest \
  tests/unit/test_audit_chain_isolation_guard.py \
  tests/unit/test_audit_chain_integrity.py \
  tests/test_compliance_integrity.py -q -p no:cacheprovider
```

Required result: all new cases pass; the original focused 13/13 and related 73/73 suites remain green; **no assertion is weakened or skipped to obtain the result**. Review-2 §12 acceptance wording: *RC INTACT and RR/SERIALIZABLE either rejected before insert or INTACT*.

---

## 5. Security and data-integrity review (pre-implementation)

| Dimension | Assessment |
|---|---|
| Weakens audit integrity? | **No.** It adds a refusal path; all accepted writes keep the reviewed hash/lock ordering unchanged |
| New bypass? | **None.** A rejected write cannot reach INSERT or anchor emission |
| PHI / secrets | None introduced; synthetic rows only |
| Migration impact | **None** — no DDL, no data migration, no Alembic change |
| API contract | `log_action()` signature unchanged; new exception type is additive and internal to the write path |
| Transaction boundary | Guard executes inside the caller's transaction; caller retains commit/rollback ownership |
| Failure recovery | Rejection surfaces as an exception; caller rollback releases any transaction state; no orphan chain row |
| Provenance | Single file (`audit_service.py`) plus one new test file; no mixed-workstream hunks touched |

---

## 6. Owner decision required

**Select one:**

1. **Authorize implementation of Option B** with the §4 regression suite, then obtain a **fresh independent review** of the new MD5 before OD-001 can be accepted. This package's status becomes `IMPLEMENTED`/`TESTED` after execution; OD-001 stays `BLOCKED` until the new review returns PASS.
2. **Explicitly accept a READ-COMMITTED-only scope** with the enforcement guard as a named owner decision, recording approver and date; OD-001 may then be reconsidered on that recorded basis.
3. **Defer / reject** F-01 with a documented rationale; OD-001 remains `BLOCKED` and the audit-chain precondition stays recorded as unresolved.

No option is selected by this package. The owner's exact text, approver and date must be recorded in `GULA_OWNER_DECISION_REGISTER.md` under OD-001.

---

## 7. Rollback and non-claims

- Rollback: revert the single `audit_service.py` hunk and remove the new test file; one `git revert` per future commit; staged `R100` renames and protected MD5s are never touched.
- This package does **not** award `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`, does not accept OD-001, does not authorize a commit/PR/deploy, and does not change release posture (**HOLD**; Stable v1.0.0 **not declared**; `production_ready_items = 0`).
- The full backend suite figure `5151 passed / 28 skipped / 0 failed` remains historical evidence only; it was not re-run by Review-2 or by this package.

---

## 8. Authorized implementation and evidence — 2026-11-20

Owner authorization `GULA-SEC015-F01-REMEDIATION` selected Option B (scope item 2 is satisfied by enforcement through fail-fast: **no audit write is permitted at any isolation level other than READ COMMITTED**; the level is never silently changed).

### 8.1 Exact changed-file list

| File | Change | MD5 (final) |
|---|---|---|
| `backend/app/services/audit_service.py` | added `AuditChainIsolationError`, `_AUDIT_SAFE_ISOLATION_LEVELS`, `_require_audit_safe_isolation()`, and one guard call at the start of the PostgreSQL branch of `log_action()` | `566d64a2f8aa5c898a2511e1bbe304bd` (prior reviewed MD5 `40c2598a02319b00c0351ddc689f7ed7`) |
| `backend/tests/unit/test_audit_chain_isolation_guard.py` | new 401-line regression module: 12 tests (2 structural, 4 isolation-acceptance incl. two parametrized cases, 1 raw-SET bypass, 1 AUTOCOMMIT, 1 fail-closed, 4 transaction-semantics) | `9ccfa3e92fac50c247f0e839ea180cc8` |

No migration, configuration, model, route, call site, or other source file was touched. Protected MD5s, the 20 staged `R100` renames, and sibling worktrees are unchanged.

### 8.2 Implementation explanation

`_require_audit_safe_isolation(db)` reads three pieces of state from the connection that will perform the write, before the advisory lock and before any data statement:

1. **Actual level** — `Connection.get_isolation_level()`. SQLAlchemy 2.0.51 implements this with a live `SHOW transaction isolation level`, so it observes both an engine/connection setting and a per-transaction `SET TRANSACTION ISOLATION LEVEL` (verified empirically against PG16.14). Only `READ COMMITTED` is accepted.
2. **Configured execution option** — `Connection.get_execution_options().get("isolation_level")`, rejected unless empty/default or `READ COMMITTED`.
3. **DBAPI `autocommit` flag** — checked separately because SQLAlchemy intentionally does not report AUTOCOMMIT via `get_isolation_level()`; an autocommit connection releases the transaction-scoped advisory lock after the SELECT and would still fork the chain. `None` (undeterminable) and `True` are both rejected; any exception while reading any of the three values is converted to `AuditChainIsolationError` (fail closed).

The guard runs only in the PostgreSQL branch. SQLite behavior, `log_action()` signature, `_compute_chain_hash`, `_canonical_audit_timestamp`, `verify_audit_chain()`, the advisory lock ordering, `nextval`, and the append-only triggers are unchanged. A rejected writer performs no `SHOW` write, no advisory lock, no sequence consumption, no INSERT and no anchor emission.

**Deviation from the original §3.2 sketch (deliberate, evidence-driven):** the sketch proposed `Connection.get_isolation_level()` alone. Empirical probing showed that API reports `READ COMMITTED` even for `create_engine(..., isolation_level="AUTOCOMMIT")`; the DBAPI autocommit check was added to close that bypass and to satisfy owner scope items 3–4 and the fail-closed requirement.

### 8.3 Verification evidence (raw logs)

Interpreter: `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` = **Python 3.12.13**; SQLAlchemy **2.0.51**; psycopg2 **2.9.12**; pytest **9.1.1**; PostgreSQL **16.14**. Env: `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. REDIS_URL="" DATABASE_URL="sqlite:///:memory:"`.

| Suite | Command (from `backend/`) | Result | Raw log | Exit |
|---|---|---|---|---|
| Focused SEC-015 | `python -m pytest -q --no-header -p no:cacheprovider tests/unit/test_audit_chain_integrity.py` | **13 passed** (68.43 s) | `/tmp/opencode/f01_verify_focused_final.log` | 0 |
| Related audit (six-file set) | `python -m pytest -q --no-header -p no:cacheprovider` + chain, bypass, positional, anchor, compliance, MPI-chain files | **73 passed** (93.75 s) | `/tmp/opencode/f01_verify_related.log` | 0 |
| New PG16 isolation suite | `GULA_AUDIT_PG16_TEST_DSN=<disposable> python -m pytest -q --no-header -p no:cacheprovider tests/unit/test_audit_chain_isolation_guard.py` | **12 passed** (1.59 s) | `/tmp/opencode/f01_verify_pg16_final.log` | 0 |

The earlier pre-format runs are preserved at `/tmp/opencode/f01_verify_focused.log` (13 passed, 71.54 s), `/tmp/opencode/f01_verify_pg16.log` (12 passed, 1.53 s). All three final exits were recorded together as `ALL_EXITS=0,0,0`. No assertion was weakened, skipped, or deleted.

Quality gates: `py_compile` exit 0; `ruff check` clean on the new test file; `ruff format --check` clean on both changed files; `git diff --check` exit 0. One `ruff check` SIM108 finding remains in `audit_service.py::_canonical_audit_timestamp` (lines 131–134) and was confirmed **pre-existing at HEAD** (`git show HEAD:backend/app/services/audit_service.py`); it was not introduced or changed by this work.

### 8.4 PostgreSQL isolation results

| Case | Result |
|---|---|
| `READ COMMITTED` — 3 sequential writes | 3 rows, all hashes valid, `verify_audit_chain()` → `intact` |
| Concurrent RC writers — A holds advisory lock, B starts while A uncommitted | B did **not** finish before A committed (lock proven held); after A commit both rows present, distinct hashes, chain `intact` |
| `REPEATABLE READ` | `AuditChainIsolationError` before write; 0 rows; sequence state unchanged |
| `SERIALIZABLE` | `AuditChainIsolationError` before write; 0 rows; sequence state unchanged |
| Raw `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` (default engine) | active level observed as `SERIALIZABLE`, guard rejected; 0 rows; sequence unchanged |
| `AUTOCOMMIT` engine | `AuditChainIsolationError` naming AUTOCOMMIT; 0 rows; sequence unchanged |
| Isolation probe raising an exception | fail-closed `AuditChainIsolationError`; 0 rows; sequence unchanged |
| Rollback after a successful RC write | only surviving row present; chain `intact` |
| Append-only triggers after guard | UPDATE and DELETE both rejected with `append-only`; chain `intact` |

Disposable container: `gula-f01-pg16-verify`, `postgres:16-alpine` 16.14, isolated host port 127.0.0.1:55432, synthetic credentials, throwaway database `f01test`, created and used only for this verification. The shared `gula-postgres`, `gula-redis`, `posta-*` containers were never touched; the container was removed after verification. No PHI, production data, or secret appears in logs, tests, or this report.

### 8.5 Security and regression findings

| Dimension | Finding |
|---|---|
| New bypass found and closed | SQLAlchemy's `get_isolation_level()` does not expose AUTOCOMMIT; the DBAPI flag check closes it (§8.2) |
| Weakens audit assertions? | No — all 13 focused and 73 related assertions unchanged and passing |
| Silent fallback? | None — verification of the live state is mandatory; unknown state fails closed |
| API compatibility | `log_action()` signature and all 206 call sites unchanged; SQLite branch unchanged |
| Schema / migrations | No DDL, no data migration, no Alembic file changed |
| Pre-existing limitations retained | F-03 pre-commit anchor; F-06 no anchor cross-check; `shared/audit/service.py` schema mismatch — all out of scope |
| Status | `IMPLEMENTED` + `TESTED`; **not** `INDEPENDENTLY VERIFIED` — see `GULA_SEC015_F01_INDEPENDENT_REVIEW_PACKAGE.md` |

### 8.6 Git invariants (final recheck)

Branch `integration/gula-unification-v1`; HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`; 20 staged `R100` renames; staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`; three protected MD5s exact (`effdfeaf…`, `1a02c015…`, `ea3969d0…`); sibling `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91`; `git diff --check` exit 0. No staging, commit, push, merge, PR, rebase or deployment. Release **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.
