# P-03-CONCURRENCY — independent design document

Generated 2026-11-24 UTC. **Design only. NOT APPROVED. NO CODE IMPLEMENTED.**

This is a standalone design package for the hash-chain concurrency defect. It is
**separate from P-03 / AUD-F03**: T9 was explicitly deferred by
`P-03_DECISION_PACKET_REV3.md` §2, §6 and §7, and the 2026-11-24
`test_p03_concurrency_diagnostic_postgres.py` result is **defect evidence only** —
it is not P-03 GREEN evidence, not a multi-worker fix proof, and not an acceptance
gate for either package.

## 1. Problem statement (HEAD evidence)

At HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`:

- `_get_last_chain_hash(db)` (`backend/app/services/audit_service.py:106-112`) reads
  the chain tail with an unlocked `SELECT chain_hash FROM audit_logs ORDER BY id
  DESC LIMIT 1`.
- `log_action` PG branch (`:218-225`) reserves the serial id with `nextval`, reads
  that tail, computes `chain_hash` from the predecessor and flushes the row.
- Two concurrent writers can therefore read the same predecessor and produce a
  fork that `verify_audit_chain()` (`:238-268`) rejects. Append-only triggers
  (`20250322_0002_perf_indexes_audit_protection.py:76-104`) prevent in-place repair.
- Reproduced 2026-11-24 on disposable PostgreSQL 16.14 from an untouched
  `git archive HEAD` tree: desired-behavior assertion failed with row `id=2`
  `stored_hash=571f43b6…` vs `expected_hash=5bb1ab4d…`; the companion
  characterization test passed. Log: `/tmp/opencode/gula-int-p03-red.log`.

Additional failure modes recorded in prior evidence:

| Mode | Evidence |
|---|---|
| Snapshot isolation drift | `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md` F-01: advisory lock serialized execution but `REPEATABLE READ`/`SERIALIZABLE` snapshots predated the predecessor commit → `broken=[2]` |
| AUTOCOMMIT | `GULA_SEC015_F01_REMEDIATION_PACKAGE.md` §8.2: SQLAlchemy `get_isolation_level()` does not expose DBAPI autocommit; a transaction-scoped lock would be released immediately |
| Pre-commit anchor | `log_action` writes anchor checkpoints before caller commit; rollback can leave an orphan anchor line (pre-existing residual F-03) |
| No enforcement at HEAD | Review-2 §6: no isolation-level check anywhere in `backend/app`; READ COMMITTED was an unenforced precondition |

## 2. Requirements and invariants for the future implementation tranche

1. No hash-chain fork under any number of concurrent writers or processes.
2. No NULL `chain_hash` row; every committed audit row chains to the immediately
   preceding committed row by ascending id.
3. Serialization must cover the empty-chain (genesis) case.
4. Lock acquisition and release must follow the caller's transaction boundary;
   no session-scoped lock may outlive a request or pool checkout.
5. Isolation must be enforced, not assumed: reject any level that cannot guarantee
   a fresh predecessor read, before any data statement.
6. Rollback must leave no row, no consumed identity that is treated as a row, and
   no anchor line for an uncommitted row.
7. No schema change, new dependency, new service or vendor-specific infrastructure
   unless separately authorized by owner decision.
8. Behavior outside the audit write path unchanged; no API contract change.
9. All proof on disposable PostgreSQL 16 with synthetic data only; no SQLite
   substitution, no PHI, no production access.
10. Verification is detection only; it must never be presented as fork prevention.

## 3. Alternatives compared

| Option | Mechanism | Fork-safe incl. genesis | Schema change | Coupling | Retry burden | Verdict |
|---|---|---|---|---|---|---|
| A | Last-chain-row `SELECT … FOR UPDATE` | **NO** — no row exists at genesis; tail can move | No | low | low | defence-in-depth only, never primary |
| B | Single fixed-key `pg_advisory_xact_lock` | **YES** | No | PostgreSQL-specific | low | **recommended primary** |
| C | `SERIALIZABLE` alone | **NOT GUARANTEED** without enforcement; high abort rate | No | low | high | comparison only; not a sole control |
| D | Sentinel row locked `FOR UPDATE` first | YES | **YES** — sentinel row/table lifecycle | low | low | fallback only; needs separate schema decision |
| E | B + bounded SQLSTATE retries + idempotency + chain verification | YES | No (unless D4-style dedupe keys are added) | PostgreSQL-specific | low | **recommended architecture** |
| F | Redis / external distributed lock | YES if correct | No | **new dependency**, network failure mode | medium | rejected: vendor/dependency coupling and lock leaks |
| G | Single-writer queue / service | YES | large | architectural | medium | rejected: new component, availability bottleneck; separate program |

Precedents: `GOVERNANCE/IDENTITY_REMEDIATION/MPI_SERIALIZATION_ARCHITECTURE_DECISION.md`
§3–§5 evaluated A–E and recommended E; its measured isolated figures (advisory
84.47 ops/s, p95 142.3 ms vs naive 123.88 ops/s, p95 101.5 ms) are **indicative
only**, from the MPI workload, not a canonical-audit benchmark.

## 4. Recommended architecture — Option E (B as primary)

`PROPOSED — NOT APPROVED`. Requires its own owner decision and implementation
packet; nothing in this document authorizes code.

### 4.1 Lock acquisition

- Use one fixed `bigint` key derived from a versioned namespace, e.g.
  `hashtext('gula:audit:chain:tail:v1')::bigint`; the one-argument overload avoids
  collision with unrelated two-key namespaces. The key is public configuration,
  not a secret.
- Acquire `pg_advisory_xact_lock(:key)` at the **outermost transaction level**,
  before `_get_last_chain_hash`, before `nextval`, before any row lock, and before
  any `SAVEPOINT`. It covers genesis because it does not depend on a chain row.
- Use **transaction-scoped** locks only. Session-scoped `pg_advisory_lock` is
  prohibited: it leaks across pooled connections and cannot be guaranteed to be
  released on request failure.
- The key serializes the **canonical audit chain globally**. Per-tenant or
  per-resource keys would allow independent total orders and therefore forks.

### 4.2 Concurrent write ordering

Total order inside the critical section:

1. isolation guard (read live state, before any data statement);
2. transaction-scoped advisory lock;
3. `nextval(pg_get_serial_sequence('audit_logs','id'))`;
4. unlocked tail read — now safe because all writers are serialized;
5. `chain_hash = H(prev_hash, row_image)`;
6. `INSERT` and `flush`;
7. commit by the caller.

No new row lock may be acquired inside the critical section. If other locks are
already held by the caller, they must be acquired in a documented ascending order
before the advisory lock, never after; this is the deadlock-ordering rule.

### 4.3 Isolation enforcement

Adopt the fail-fast pattern from `GULA_SEC015_F01_REMEDIATION_PACKAGE.md` §8.2:

- inspect the live connection's isolation level, configured execution option and
  DBAPI `autocommit` flag **before** the advisory lock;
- accept only `READ COMMITTED`; reject `REPEATABLE READ`, `SERIALIZABLE`,
  `AUTOCOMMIT`, unknown state and probe exceptions by raising an audit-specific
  error before any data statement;
- no fallback to a weaker level, no silent coercion.

Rationale: the advisory lock cannot refresh a transaction snapshot taken before
the predecessor committed. Enforcement makes an unsafe configuration explicit
and auditable rather than silently producing a fork.

### 4.4 Rollback behavior

- `pg_advisory_xact_lock` is released automatically on COMMIT or ROLLBACK; no
  explicit unlock is needed and none may be attempted on a broken session.
- On any failure inside the critical section, the caller rolls back the whole
  transaction. Sequence values consumed by `nextval` are not reclaimed; gaps are
  acceptable and must be documented (they do not break the chain).
- Anchor emission must move to **after commit** in the implementation tranche, or
  a compensating rule must be approved, so a rolled-back row cannot leave an
  orphan anchor line. This is a change to shared canonical code and needs its own
  review; it is not part of P-03.
- Append-only triggers remain in force; no UPDATE/DELETE repair path is allowed.

### 4.5 Deadlocks and lock timeouts

- A single global key cannot deadlock against itself; ordering conflicts can only
  arise from locks acquired by the caller before the advisory lock.
- Configure a bounded `lock_timeout` and `statement_timeout` for the audit write
  path and verify empirically on PG16 whether `lock_timeout` governs
  `pg_advisory_xact_lock` waits in the pinned driver. Do not assume; the
  implementation tranche must measure it.
- Never hold the advisory lock while performing network I/O, provider calls,
  file anchoring or long application work.
- On `55P03` (lock_not_available) treat as a bounded retryable condition; on
  `40P01` (deadlock_detected) roll back the full transaction and restart; do not
  resume a partially executed critical section.

### 4.6 Retries and idempotency

- Retry **only** transient SQLSTATEs: `40001` serialization_failure, `40P01`
  deadlock_detected, `55P03` lock_not_available. Full transaction restart only.
- Never retry `23505` as an error: handle it as an idempotent replay at the
  correlation key. Do not retry `23503`, `23514`, `22xxx` or validation errors.
- Bounded attempts: 3 total (initial + 2 restarts), backoff 25 ms / 50 ms with
  small jitter; deterministic barriers in tests, never random sleeps to force an
  outcome.
- Idempotency requires a correlation key and unique constraint; HEAD has neither.
  Adding one is a **separate schema decision** (parallel to P-03 D4). Until then,
  at-most-once under test with disclosed duplicate risk is the only available
  acceptance basis; retry must not silently create a second audit row during
  recovery.

### 4.7 Multi-worker deployment

- The advisory lock lives in PostgreSQL, so it is effective across processes,
  pods and hosts sharing the database — unlike an in-process mutex.
- The key must be process-independent and versioned; all workers must use the
  same key version. A key change is a deployment-wide migration decision.
- Pooled connections are safe with transaction-scoped locks provided every
  exception path rolls back before the connection returns to the pool.
- No Redis, lock service or new external dependency is introduced.

### 4.8 Performance under pressure

- One global key intentionally serializes all canonical audit appends; this is
  the cost of a single total chain order. Sharding the key is rejected.
- Benchmark separately for the canonical audit path: writes/s, p50/p95/p99 lock
  wait, abort/retry rate by SQLSTATE, and behavior at 10/20/50 workers and
  multi-node. Existing MPI figures are indicative only.
- Before implementation thresholds are set, record that no production load
  target has been approved; do not claim capacity from a single-process test.
- Monitor lock wait time, retries by SQLSTATE, chain verification result and
  fork count using existing Prometheus instrumentation; no new vendor tooling.

### 4.9 Chain recovery and verification

- `verify_audit_chain()` remains **detection**, not prevention. Add a segment
  check inside the write transaction before commit and expose a full-chain check
  through an authorized operational path with a documented fork-response policy.
- On a detected fork: stop audit appends, export a forensic snapshot, and return
  to the owner. Append-only triggers preclude in-place repair. A "new chain
  generation" marker with an explicit trust boundary is the only reversible
  recovery shape; it requires a separate decision (key version + anchor format).
- Never rewrite, delete, or re-hash historical rows. Never represent a post-fork
  append as having repaired the chain.

## 5. Acceptance test matrix for a future implementation packet

All tests on disposable PG16, synthetic data, `--noconftest`, no SQLite:

| Area | Required cases |
|---|---|
| Fork prevention | 2/10/20/50 concurrent writers, distinct and identical keys, genesis and non-empty chain → `verified is True`, no NULL hashes |
| Isolation | RC accepted; RR/SER/AUTOCOMMIT/raw `SET TRANSACTION`/undeterminable state rejected before INSERT and before sequence consumption |
| Locking | transaction-scoped lock proven held until commit; no retention after pool checkout; no session lock leakage |
| Ordering | lock before tail read and before row locks; ascending lock order with caller-held locks |
| Rollback | no row, no anchor for uncommitted row, chain intact after rollback, sequence gaps documented |
| Deadlock/timeout | injected `40P01`/`55P03` → bounded retry, full restart, no partial write |
| Idempotency | replay of the same correlation key → no second row once schema decision exists; duplicate risk disclosed until then |
| Recovery | verification detects an injected fork; no in-place repair attempted; new-generation policy followed only when authorized |
| Performance | throughput and p95/p99 lock wait at 10/20/50 workers; thresholds owner-approved |
| Regression | focused/related audit suites unchanged; `git diff --check` 0; Ruff/strict MyPy clean |

## 6. Separation and status

| Item | Status |
|---|---|
| P-03-CONCURRENCY design | `PREPARED ONLY` — not approved, not implemented |
| P-03 / AUD-F03 | separate packet; D1–D5 still required; NOT implemented |
| 2026-11-24 concurrency RED | defect reproduction only, not P-03 GREEN, not multi-worker proof |
| Working-tree `audit_service.py` | has uncommitted mixed-provenance advisory lock + isolation guard; not reviewed/accepted as P-03-CONCURRENCY evidence |
| Code, schema, migration, config changes by this document | none |
| Release posture | **HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED** |
