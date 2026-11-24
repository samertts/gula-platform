# MPI Implementation Execution Plan — PROPOSED, NOT APPROVED

**Status:** `PROPOSED — NOT APPROVED`. Sequencing/planning artifact only. No work package in this
document is authorized to begin. **D-MPI-1 remains `NEEDS_OWNER_DECISION`** and gates the entire
plan; individual packages carry additional owner-decision gates noted below.
**Repository:** `/home/samertts/workspace/projects/gula-integration` @
`integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
**Release:** HOLD. D-020 / D-021 `PENDING_APPROVAL`. Protected repository `gula-platform` untouched.
**Architecture basis:** `MPI_SERIALIZATION_ARCHITECTURE_DECISION.md` (recommended E = B + D +
existing ordered locking). **Failure semantics:** `MPI_FAILURE_RECOVERY_MATRIX.md`.
**Empirical evidence:** `MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md` (65 passed, 87.61 s).

Effort figures are rough engineer-day estimates for planning only, not commitments. “Schema” column
refers to application data-model/migration changes; the recommended path requires **none** for every
package. Fallback A (sentinel row) is explicitly excluded from this plan and would require a
separately authorized D-MPI-2a migration.

---

## 1. Dependency graph and sequencing

```
D-MPI-1 (owner approves architecture)   ← hard gate for ALL packages
        │
        ├── MPI-01 (advisory serialization) ──┬── MPI-02 (genesis)
        │                                     ├── MPI-04 (lock ordering)
        │                                     ├── MPI-08 (integrity verification)*
        │                                     └── MPI-10 (observability)*
        │
        ├── MPI-03 (version concurrency) ─────┐
        │                                      ├── MPI-06 (txn boundary & commit recovery)
        ├── MPI-05 (idempotency)* ─────────────┤        │
        │                                      │        └── MPI-07 (failure/retry)
        └── MPI-09 (regression & concurrency)* ─┘
                                                        │
                                            MPI-08, MPI-09, MPI-10 close the tranche

* Additional owner gate: MPI-05 → D-MPI-5; MPI-08 → D-MPI-3/4; MPI-03 canonical scope → D-MPI-6.
```

- **Foundation (sequence first, no parallelism):** MPI-01 → MPI-02 / MPI-04. These define the global
  lock discipline every other package relies on.
- **Independent of each other, parallelizable after the foundation:** MPI-03, MPI-05, MPI-08, MPI-10.
- **Sequenced after foundation + idempotency:** MPI-06 → MPI-07 (commit recovery must precede retry
  policy wiring, because retry needs the reconciliation path MPI-06 establishes).
- **Cross-cutting, continuous:** MPI-09 (tests) and MPI-10 (observability) run alongside every
  package but are certified last.
- **File-overlap warning:** MPI-01/02/04/05/06/07/08 all touch `resolver.py`, and MPI-05/06/07 touch
  `api.py`. To minimize merge conflicts, implement them as a **single coordinated sequence on one
  branch**, one package per commit, each commit independently testable — not as parallel branches
  editing the same files. MPI-03 (`canonical_service.py`) and MPI-10 (metrics) are the only packages
  with low file overlap.

---

## 2. Work package definitions

### MPI-01 — Audit-chain serialization
- **Problem:** `_last_audit_hash()` (`resolver.py:110-115`) reads the tail unlocked; concurrent
  appends fork the chain (50/20/10/5 fork groups at 2/5/10/20 workers).
- **Files expected to change:** `backend/app/services/mpi/resolver.py` (new lock helper + call in
  `_write_audit` and the resolve-path `create` audit at `:380-389`).
- **Dependencies:** D-MPI-1 approval. None technical.
- **Implementation strategy:** introduce one transaction-scoped advisory lock
  (`pg_advisory_xact_lock(hashtext('gula:mpi:audit_chain:tail:v1')::bigint)`) acquired at the
  outermost transaction level **before** `begin_nested()` and before the tail read; guard both audit
  append call sites. Keep detection-only last-row `FOR UPDATE` as defence in depth (not primary,
  not genesis coverage). Session-scoped locks prohibited.
- **Tests required:** PostgreSQL-backed 2/5/10/20-worker append test with deterministic barriers
  asserting a single chain, zero forks, unique predecessor; genesis case (empty table).
- **Acceptance criteria:** zero fork groups at all four worker counts including genesis; lock
  released on both commit and rollback; no session-scoped lock in code.
- **Rollback:** revert the single commit; the helper is additive and no data migration exists.
- **Risk:** Medium — changes the hottest serialization point; correctness-critical.
- **Effort:** ~2 d. **Schema:** NO.

### MPI-02 — Genesis protection
- **Problem:** empty audit table has no last row to lock; two simultaneous first appends can both
  commit `prev = 000…0`.
- **Files expected to change:** `resolver.py` (genesis branch in the MPI-01 lock helper) + tests.
- **Dependencies:** MPI-01. No owner decision beyond D-MPI-1.
- **Implementation strategy:** rely on the MPI-01 advisory lock — it does not depend on chain
  existence, so the empty-table case is inside the same critical section. Do **not** add a sentinel
  row (that is fallback A / D-MPI-2a).
- **Tests required:** forced-simultaneous genesis (barrier before first insert), assert exactly one
  genesis row and a contiguous chain.
- **Acceptance criteria:** exactly one `prev=000…0` row under concurrency; verifier reports valid.
- **Rollback:** revert with MPI-01 (they share the helper region).
- **Risk:** Low once MPI-01 lands. **Effort:** ~0.5 d. **Schema:** NO.

### MPI-03 — Version update concurrency
- **Problem:** unprotected read-modify-write at `resolver.py:515` (`secondary.version += 1`) and
  `canonical_service.py:128,130` loses updates (1/4/9/19 lost at 2/5/10/20 workers).
- **Files expected to change:** `backend/app/services/mpi/resolver.py`,
  `backend/app/services/mpi/canonical_service.py`.
- **Dependencies:** D-MPI-1; canonical-scope changes gated by **D-MPI-6**.
- **Implementation strategy:** atomic `UPDATE … SET version = version + 1 … RETURNING version` where
  only the new value matters; optimistic `WHERE version = :expected` only where prior-value
  validation is required, with bounded retries. Retain existing citizen `FOR UPDATE` as ordering,
  not as sole version protection. `primary.version` remains unchanged (existing behaviour).
- **Tests required:** version counter concurrency at 2/5/10/20 workers for both resolver and
  canonical paths; assert zero lost updates.
- **Acceptance criteria:** zero lost updates in both paths; no behavioural change to which rows are
  incremented.
- **Rollback:** revert per-file commits independently (each path is self-contained).
- **Risk:** Medium — must preserve existing version semantics. **Effort:** ~1.5 d. **Schema:** NO.

### MPI-04 — Deterministic lock ordering
- **Problem:** no global order across audit tail, canonical records and citizen rows; opposite order
  produced `40P01`.
- **Files expected to change:** `resolver.py` (document + assert the total order; keep the ascending
  `Citizen.id` statement at `:459-465` unchanged).
- **Dependencies:** MPI-01.
- **Implementation strategy:** formalize order as (1) advisory lock → (2) citizen rows `ORDER BY
  Citizen.id ASC` in one `FOR UPDATE` statement → (3) SAVEPOINT reads/writes. No new row locks inside
  the SAVEPOINT; no second audit-tail row lock while the advisory lock is held.
- **Tests required:** lock-order source invariant test (extend `test_mpi_hash_chain_integrity.py`);
  PostgreSQL two-worker opposing-input test asserting zero `40P01`.
- **Acceptance criteria:** zero observed deadlocks at 10 workers under the approved order; order
  documented and asserted.
- **Rollback:** revert; ordering statement is unchanged from baseline.
- **Risk:** Low. **Effort:** ~1 d. **Schema:** NO.

### MPI-05 — Idempotency and request replay
- **Problem:** merge replay key `(primary, secondary, event)` exists (`resolver.py:475-488`) but has
  no DB unique constraint and does not deduplicate swapped ULIDs; resolve path has a claim
  constraint (`models.py:124`) but no `IntegrityError` handling → concurrent resolves can 500.
- **Files expected to change:** `resolver.py`, `api.py`; test files.
- **Dependencies:** MPI-01/04 (locks); conflicting-payload policy gated by **D-MPI-5**.
- **Implementation strategy:** on `23505` at the claim key, re-read and return the winning claim;
  normalize the merge pair for replay lookup (both ULID orders); reject conflicting payloads without
  mutation per D-MPI-5. No schema change — reuse `uq_identity_claims_lab_patient`.
- **Tests required:** sequential duplicate, concurrent duplicate, conflicting payload, swapped-ULID
  replay; assert one operation / one audit row in each.
- **Acceptance criteria:** zero duplicate successful merges per key; conflicting payload mutates
  nothing; no unhandled `IntegrityError`.
- **Rollback:** revert; no constraint added or removed.
- **Risk:** Medium — touches replay semantics. **Effort:** ~2 d. **Schema:** NO.

### MPI-06 — Transaction boundary and commit recovery
- **Problem:** SAVEPOINT release is not commit; caller owns outer commit (`api.py:168`);
  `expire_on_commit=True` (`database.py:242`) allows post-commit attribute reads (`api.py:171-175`)
  to fail after a successful commit; in-doubt COMMIT has no reconciliation.
- **Files expected to change:** `api.py`, `resolver.py`, possibly `database.py:242` (or capture result
  values before commit rather than changing the global session setting).
- **Dependencies:** MPI-01/04/05.
- **Implementation strategy:** capture response fields before commit (avoid post-commit SELECTs); add
  the reconciliation algorithm from `MPI_FAILURE_RECOVERY_MATRIX.md` §3 for connection-loss paths;
  document and assert that audit append and identity changes share one outer transaction.
- **Tests required:** failure injection before/during/after commit; assert no partial merge, no
  duplicate audit, and correct replay result.
- **Acceptance criteria:** no partial merge in any injection point; commit-succeeded/response-lost
  window eliminated or reconciled; audit + merge atomicity proven by test.
- **Rollback:** revert; additive reconciliation helpers.
- **Risk:** High — most sensitive correctness package. **Effort:** ~3 d. **Schema:** NO.

### MPI-07 — Failure handling and retry policy
- **Problem:** no SQLSTATE handling anywhere; `api.py:166-167` catches only `ValueError`; DB errors
  become unhandled 500s.
- **Files expected to change:** `api.py`, `resolver.py` (shared retry helper); test files.
- **Dependencies:** MPI-06 (needs reconciliation path).
- **Implementation strategy:** classify SQLSTATEs per the recovery matrix; retry only `40001`,
  `40P01`, `55P03` and clearly-transient connection errors with ≤3 attempts and 25/50 ms backoff;
  full transaction restart on serialization/deadlock; never retry `23505`/`23503`/`23514`/`22xxx`.
- **Tests required:** forced `40P01`, `55P03`, `40001`, `23505` paths; assert retry classification,
  attempt caps, and zero permanent-violation retries.
- **Acceptance criteria:** every transient failure bounded; no permanent violation retried; no
  duplicate audit from retry.
- **Rollback:** revert the retry helper and call sites.
- **Risk:** Medium. **Effort:** ~2 d. **Schema:** NO.

### MPI-08 — Integrity verification
- **Problem:** `verify_merge_audit_chain()` (`resolver.py:175-208`) exists but has **no production
  caller**; the in-path check validates state, not the hash chain.
- **Files expected to change:** `resolver.py` (segment check before `savepoint.commit()`); an
  operational verification path (endpoint or scheduled job) — location gated by **D-MPI-3/4**.
- **Dependencies:** MPI-01; D-MPI-3/4 for full-chain exposure.
- **Implementation strategy:** in-transaction verification of the newly appended segment; provide
  full-chain verification through an authorized operational path; emit fork-count/valid metrics
  (feeds MPI-10). Verification remains detection only.
- **Tests required:** verify success after concurrent operations; seeded-fork detection; assert
  verification never prevents a commit incorrectly.
- **Acceptance criteria:** complete chain verification passes after concurrency; seeded forks
  detected; no claim of fork prevention.
- **Rollback:** revert; additive verification calls.
- **Risk:** Low–Medium. **Effort:** ~1.5 d. **Schema:** NO.

### MPI-09 — Regression and concurrency tests
- **Problem:** in-repo tests use SQLite (no `FOR UPDATE`), so row locking is only source-asserted;
  gaps in concurrency/genesis/lock-timeout/deadlock/retry/idempotency coverage.
- **Files expected to change:** test files under `backend/tests/`; a PostgreSQL-backed concurrency
  harness (reuse `/tmp/opencode/gula-mpi-tests` patterns; keep outside production).
- **Dependencies:** runs continuously; certified last. Consumes the finalized test inventory from the
  audit/cross-component analysis.
- **Implementation strategy:** separate correctness tests (deterministic barriers) from performance
  tests (median throughput/latency); cover all acceptance criteria in §5 of the architecture doc.
- **Tests required:** the full matrix in §11 below.
- **Acceptance criteria:** zero forks / lost updates / partial merges / duplicates; deterministic
  lock order; bounded retries; full-chain verification.
- **Rollback:** test-only changes; remove added files.
- **Risk:** Low. **Effort:** ~3 d. **Schema:** NO.

### MPI-10 — Observability and operational controls
- **Problem:** no metrics for lock wait, retry, chain validity or replay rate.
- **Files expected to change:** `resolver.py`/`api.py` instrumentation points; existing metrics module
  (no new service).
- **Dependencies:** MPI-01 (lock hooks), MPI-08 (verification hooks). Independent file overlap.
- **Implementation strategy:** use existing Prometheus/metrics infrastructure; instrument lock-wait
  duration, retry count by SQLSTATE, chain-verification result and fork count, merge duration,
  idempotent replay rate. No Redis, distributed lock or external service.
- **Tests required:** metric emission tests; alert/dashboard definition review.
- **Acceptance criteria:** all listed signals observable; no new infrastructure dependency.
- **Rollback:** revert instrumentation.
- **Risk:** Low. **Effort:** ~1.5 d. **Schema:** NO.

---

## 3. Package summary table

| Package | Depends on | Owner gate | Files (expected) | Schema | Risk | Effort |
|---|---|---|---|---|---|---|
| MPI-01 | — | D-MPI-1 | resolver.py | NO | Medium | 2 d |
| MPI-02 | MPI-01 | D-MPI-1 | resolver.py | NO | Low | 0.5 d |
| MPI-03 | — | D-MPI-1, D-MPI-6 (canonical) | resolver.py, canonical_service.py | NO | Medium | 1.5 d |
| MPI-04 | MPI-01 | D-MPI-1 | resolver.py | NO | Low | 1 d |
| MPI-05 | MPI-01/04 | D-MPI-1, D-MPI-5 | resolver.py, api.py | NO | Medium | 2 d |
| MPI-06 | MPI-01/04/05 | D-MPI-1 | api.py, resolver.py, database.py | NO | High | 3 d |
| MPI-07 | MPI-06 | D-MPI-1 | api.py, resolver.py | NO | Medium | 2 d |
| MPI-08 | MPI-01 | D-MPI-1, D-MPI-3/4 | resolver.py, ops path | NO | Low–Med | 1.5 d |
| MPI-09 | continuous | — | tests/ + harness | NO | Low | 3 d |
| MPI-10 | MPI-01/08 | D-MPI-1 | metrics module, resolver.py/api.py | NO | Low | 1.5 d |

Total indicative effort ≈ 18 engineer-days across 10 packages. **No package requires an application
schema change** under the recommended architecture.

---

## 4. File-overlap matrix (to plan commits, not branches)

| File | Packages touching it |
|---|---|
| `services/mpi/resolver.py` | 01, 02, 03, 04, 05, 06, 07, 08, 10 |
| `services/mpi/api.py` | 05, 06, 07, 10 |
| `services/mpi/canonical_service.py` | 03 |
| `database.py` | 06 (optional — prefer capturing values pre-commit) |
| metrics module | 10 |
| `backend/tests/` + harness | 01–10 (MPI-09 owns) |

`resolver.py` is the contention point: implement all its packages as sequential commits on one
branch. MPI-03 and MPI-10 are safe to develop in parallel because their primary files do not
overlap with the resolver sequence (MPI-03 also edits resolver.py for the `version += 1` line — so
sequence MPI-03's resolver edit with the others; its canonical_service.py edit is independent).

---

## 5. Per-commit verification gate (implementation tranche)

Each work-package commit must: (1) pass focused PostgreSQL + SQLite tests for its package;
(2) leave the full backend suite green; (3) pass ruff on changed files; (4) keep tsc/eslint clean;
(5) preserve OpenAPI byte-stability (no contract change); (6) keep branch/HEAD/decision-state
invariants (HOLD, D-020/D-021, D-MPI-1 until owner approval); (7) produce a short verification note.
No commit may introduce a migration, a source change outside the package's declared files, or a
cross-domain FK repoint.

---

## 6. Rollback strategy (tranche-wide)

- Each package is one atomic, independently `git revert`-able commit.
- No data migration exists in the recommended path, so rollback is code-only and behaviour returns
  to the pre-package state.
- Rollback ordering: reverse dependency order (e.g. revert MPI-07 before MPI-06; revert MPI-02/04
  before MPI-01).
- If a fork or partial merge is discovered after rollback, preserve audit rows and verifier output as
  evidence; do not delete audit data (detection-only verification remains intact).

---

## 7. Owner decisions that gate packages

| Package | Required decision | Current status |
|---|---|---|
| All | D-MPI-1 architecture approval | `NEEDS_OWNER_DECISION` |
| MPI-03 (canonical portion) | D-MPI-6 canonical-service hardening scope | `NEEDS_OWNER_DECISION` |
| MPI-05 | D-MPI-5 concurrent first-resolve / conflicting-payload policy | `NEEDS_OWNER_DECISION` |
| MPI-08 | D-MPI-3/4 fork-response policy + event taxonomy | `NEEDS_OWNER_DECISION` |
| Fallback A (excluded) | D-MPI-2a sentinel-row schema authorization | `NEEDS_OWNER_DECISION` |

No package may proceed on an unresolved owner gate. D-020 / D-021 and HOLD are unchanged throughout.

---

## 8. Out of scope for this plan (explicitly excluded)

- Repointing any cross-domain FK or soft reference (~90 sites — inventory in
  `MPI_CROSS_COMPONENT_IMPACT.md`).
- Implementing MPI unmerge.
- NHID canonicalization / cross-domain identity merge.
- Sentinel-row schema change (fallback A) absent D-MPI-2a.
- SERIALIZABLE as sole chain protection.
- Redis, distributed locks, new external services, API contract changes, application migrations.

---

## 9. Correctness targets (gate the implementation)

- Zero audit-chain forks (2/5/10/20 workers, incl. genesis).
- Zero lost version updates (both paths).
- Zero partial merges (rollback / interruption / termination).
- Zero duplicate successful merges per idempotency key.
- Deterministic lock order; zero `40P01` under the approved order.
- Bounded retries; zero permanent-violation retries.
- Complete audit-chain verification after concurrent operations.

---

## 10. Performance/scaling evaluation

Use the existing PostgreSQL measurements as the **baseline only** — not as targets. Isolated medians:
naive 123.88 ops/s (p95 101.5 ms), advisory 84.47 ops/s (p95 142.3 ms), sentinel 75.53,
serializable 82.17 (p95 366.9 ms), atomic 105.54. The advisory lock's cost is the intentional price
of chain integrity; no throughput target is asserted from a 1 vCPU / 1 GiB single-node harness.

Expected contention points: (1) single advisory-lock key — every MPI audit append serializes here;
(2) citizen row locks on merge pairs; (3) canonical version rows in MPI-03. These are correctness
serialization points, not defects.

---

## 11. Benchmark plan (separate from correctness tests)

- **Worker counts:** 2, 5, 10, 20; **50 if resources permit** (mark `NOT_MEASURED` otherwise).
- **Repetitions:** ≥3 per configuration; report median + p95/p99, not single runs.
- **Scenarios:** audit append (fork/validity), genesis, version counter, full merge transaction
  (currently `NOT_MEASURED` — must be added), idempotent replay.
- **Correctness vs performance:** correctness assertions (forks, lost updates, partial merges,
  duplicates, lock order, bounded retries) are hard gates; throughput/latency are observational only.
- **Environment:** reuse the isolated PostgreSQL 16.14 harness pattern outside production; synthetic
  data only; no patient data; never touch `gula-postgres`/production resources.
- **Full-merge gap:** the existing harness exercised candidate locks on simplified operations, not
  the real `merge_citizens` + claims + SAVEPOINT + caller-commit path. MPI-09 must close this gap.

---

**STOP — PROPOSED — NOT APPROVED. No work package is authorized to start. Await explicit owner
approval of D-MPI-1 (and per-package gates) plus a separate implementation authorization before any
production source, test-in-repo, configuration or migration change.**
