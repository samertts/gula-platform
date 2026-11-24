# MPI Serialization Architecture Decision — PROPOSED, NOT APPROVED

**Status:** `PROPOSED — NOT APPROVED`. This document is a decision *preparation* artifact. It does
not select, authorize, activate or implement a production mechanism. **D-MPI-1 remains
`NEEDS_OWNER_DECISION`.**
**Repository:** `/home/samertts/workspace/projects/gula-integration` @
`integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
**Protected repository:** `/home/samertts/workspace/projects/gula-platform` @
`f478676b6fc375338648dde46fbf076c015a3f91` — clean, untouched.
**Release:** HOLD — `GOVERNANCE/FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552`, unchanged.
**D-020 / D-021:** `PENDING_APPROVAL`, unchanged.
**Primary evidence:** `MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md` (65 passed / 0 failed / 0 skipped,
EXIT 0, 87.61 s, PostgreSQL 16.14, schema `mpi_concurrency_test`, synthetic data only).

Evidence classes used throughout: `TEST_VERIFIED` (measured in the isolated evaluation),
`VERIFIED_IN_SOURCE` (read from current code), `INFERRED` (design reasoning, not measured),
`NOT_MEASURED`, `OWNER_DECISION`.

---

## 1. Problem statement

Concurrent MPI operations can violate identity and audit integrity in five distinct ways:

1. **Audit-chain fork.** `_last_audit_hash()` reads the tail with an unlocked
   `ORDER BY MergeAudit.id DESC LIMIT 1` (`resolver.py:110-115`); two transactions can read the same
   predecessor and both commit a valid-looking row (`resolver.py:118-163`).
2. **Genesis fork.** With an empty audit table there is no last row to lock; two simultaneous first
   appends can both commit with the all-zero predecessor.
3. **Lost version updates.** `secondary.version += 1` (`resolver.py:515`) and
   `source.version = source.version + 1` / `target.version = target.version + 1`
   (`canonical_service.py:128,130`) are unprotected read-modify-write operations.
4. **Lock-order deadlocks.** Opposite acquisition order produces SQLSTATE `40P01`; the current
   ascending-`id` citizen lock (`resolver.py:459-465`) is correct for the pairs it covers, but no
   global ordering exists across the audit tail, canonical records and citizen rows.
5. **Ambiguous commit / replay.** The service owns only a SAVEPOINT; the caller owns the outer
   commit (`resolver.py:432-442`, `resolver.py:502-538`). A connection loss after commit but before
   response must not produce a second merge or audit event.

**Governing principle:** no single merge may corrupt a patient's identity or mix their medical
record with another patient's. Correctness and recoverability precede throughput.

---

## 2. Empirical evidence and its limits

All numbers below are `TEST_VERIFIED` in the isolated, single-node, 1 vCPU / 1 GiB PostgreSQL 16.14
environment and are **not** production capacity figures. Full raw data is in the primary report.

| Finding | Measurement | Class | Limit on interpretation |
|---|---|---|---|
| Naive audit-tail fork | 50 / 20 / 10 / 5 fork groups at 2 / 5 / 10 / 20 workers (100 ops each) | `TEST_VERIFIED` | forced-coincidence barrier; real timing may differ, but the race is real |
| Simultaneous genesis fork | two committed rows share the 64-zero predecessor | `TEST_VERIFIED` | reproduced deterministically |
| Sentinel row lock (A) | 20 workers → 20 rows, 0 forks, valid chain | `TEST_VERIFIED` | required a sentinel row fixture (schema impact) |
| Transaction advisory lock (B) | 20 workers → 20 rows, 0 forks, valid chain | `TEST_VERIFIED` | single stable key, **transaction-scoped only**; session-scoped locks untested |
| SERIALIZABLE (C) | full-txn retry on `40001`; fork reproduced in diagnostics (ids 2 and 7, both `prev=0…0`) despite 33 retries and 0 worker errors; in-suite 20-trial incidence 0/20 invalid | `TEST_VERIFIED` + `MEASURED_OBSERVATION` | **not guaranteed**, not "always fails"; rare and nondeterministic |
| Lost version updates | naive RMW lost 1 / 4 / 9 / 19 at 2 / 5 / 10 / 20 workers | `TEST_VERIFIED` | isolated counter model, not full merge |
| Safe version mechanisms | `FOR UPDATE`, atomic `SET v=v+1`, optimistic `WHERE v=:expected` → 0 lost | `TEST_VERIFIED` | optimistic path needed 40 retries at 10 workers |
| Lock ordering | opposite order → 1 × `40P01`; ascending order → 0 deadlocks at 10 workers | `TEST_VERIFIED` | tested shapes only; 50 workers untested |
| Lock timeout / failure injection | `55P03` at 1.008 s; `40P01`; rollback / interruption / worker termination → no partial row | `TEST_VERIFIED` | synthetic fixtures only |
| Idempotency | duplicate replay, unique violation `23505`, conflicting payload rejected, retry after interruption → 1 operation / 1 audit row | `TEST_VERIFIED` | in-suite idempotency-key model |
| Median throughput (ops/s) | naive 123.88 / sentinel 75.53 / advisory 84.47 / serializable 82.17 / atomic 105.54 | `TEST_VERIFIED` | 10 workers × 6 ops × 3 reps; high variance; not a target |
| Median p95 / p99 (ms) | naive 101.5/119.2 / sentinel 137.1/164.1 / advisory 142.3/180.6 / serializable 366.9/397.4 / atomic 130.6/149.3 | `TEST_VERIFIED` | same caveat |
| Full merge transaction under candidate lock | — | `NOT_MEASURED` | claims + SAVEPOINT + caller commit were not exercised in the harness |
| Multi-node advisory-lock behaviour, pooled-connection edge cases, production load | — | `NOT_MEASURED` | must be covered in the implementation tranche |

Do not convert a limited result into a universal guarantee: A and B are **proven fork-safe in the
tested model**; C is **not guaranteed**; D is **proven only for version counters**; 50-worker and
full-merge behaviour remain unmeasured.

### Source baseline (`VERIFIED_IN_SOURCE`)

| Path | Fact |
|---|---|
| `resolver.py:110-115` | unlocked audit-tail read |
| `resolver.py:129`, `resolver.py:162` | `_write_audit` flushes; **caller commits** |
| `resolver.py:175-208` | `verify_merge_audit_chain()` is detection only (docstring says so explicitly) — and is **never called in production** (only by `test_mpi_hash_chain_integrity.py`) |
| `resolver.py:231-268` | `resolve_identity` idempotency lookup is an unlocked `first()` |
| `resolver.py:252-254`, `models.py:124` | unique constraint `uq_identity_claims_lab_patient` exists — replay is DB-enforced |
| `resolver.py:380-389` | `create` audit append in `resolve_identity` also uses the unlocked tail |
| `resolver.py:454-465` | citizen locks: one statement, `ORDER BY Citizen.id.asc()`, `with_for_update()`, acquired **before** `begin_nested()` so they live on the outer transaction |
| `resolver.py:472-488` | merge retry returns the original audit row; no DB unique constraint on the merge pair and swapped ULID arguments are not deduplicated |
| `resolver.py:501-538` | claims repointed, `secondary.version += 1`, audit appended, state/claim/canonical checks, `SAVEPOINT` commit; **no hash verification and no post-commit verification** |
| `api.py:168` / `:87` | outer `db.commit()` is owned by the HTTP endpoint; `SAVEPOINT RELEASE` is not commit (`VERIFIED_IN_SOURCE`) |
| `api.py:166-167` | only `ValueError` is translated to 400; any DB error is an unhandled 500 — no `IntegrityError`/`OperationalError`, SQLSTATE, deadlock or serialization handling exists |
| `database.py:242`, `api.py:171-175` | `expire_on_commit=True` → response attribute reads after commit can issue fresh SELECTs and fail **after** a successful commit |
| `models.py:105-112` | `canonical()` chain walk silently returns the current node beyond 10 hops |
| `canonical_service.py:94-133` | `merge_canonicals` loads two rows unlocked, increments two versions unprotected, no audit/SAVEPOINT; caller `routes/canonical_patient.py:185` commits |
| `canonical_audit.py:133-180` | precedent: `_last_canonical_hash()` uses `.with_for_update()` on ordered `LIMIT 1`; genesis returns `None` with **no lock** |
| `backend/tests/conftest.py` | repository tests use SQLite, which emits no `FOR UPDATE`; key-ordered locking is source-level in-repo and runtime-verified only by the out-of-repo PostgreSQL harness |

---

## 3. Alternatives evaluated

| Option | Fork-safe incl. genesis | Lost updates | Schema change | Coupling | Retry burden | Verdict |
|---|---|---|---|---|---|---|
| **A — sentinel row lock** | PASS (20/20) | no (separate control needed) | **YES** — fixed sentinel row/table | low (portable row lock) | low | viable **fallback only**; requires D-MPI-2a schema authorization |
| **B — transaction advisory lock** | PASS (20/20) | no (separate control needed) | **NO** | PostgreSQL-specific | low | **recommended primary** |
| **C — SERIALIZABLE alone** | **NOT GUARANTEED** | theoretically via SSI, not isolated here | NO | low | high (`40001` ~190/60 ops) | comparison only; must not be sole protection |
| **D — atomic SQL** | NO | PASS (0 lost at 10/20 workers) | NO | low | low | recommended as **complementary** version control only |
| **E — hybrid B + D + ascending locks + idempotency + verification** | PASS (B) | PASS (D) | **NO** | PostgreSQL-specific | low | **recommended architecture** |

A last-row `FOR UPDATE` added to `_last_audit_hash()` (no new schema) is explicitly **not** a
complete solution: it does not cover genesis. It may be retained as a defence-in-depth measure once
a chain exists, but it cannot be the primary serialization mechanism.

---

## 4. Recommended architecture (E = B + D + existing ordered locking)

`PROPOSED — NOT APPROVED`. Selection requires explicit owner approval of D-MPI-1.

### 4.1 Audit serialization mechanism
Use a **single, fixed-key, transaction-scoped PostgreSQL advisory lock**
(`pg_advisory_xact_lock(<stable int64 key>)`) around the audit-tail read and append. The key must be
a process-independent constant derived from a versioned namespace, e.g.
`hashtext('gula:mpi:audit_chain:tail:v1')::bigint`; the one-argument `bigint` overload is preferred
to avoid accidental collision with unrelated two-key namespaces. The key is public configuration,
not a secret. Acquire it **before** any row lock and **before** `db.begin_nested()`, at the outermost
transaction level, so it survives SAVEPOINT rollback and is released only by the outer commit or
rollback. `pg_advisory_xact_lock` is mandatory; session-scoped locks are prohibited without a
separate documented justification (they leak across pooled connections).

### 4.2 Genesis handling
The advisory lock does not depend on the existence of a chain row, so the empty-table case is
protected by the same critical section. Evidence: 20 workers / 20 rows / 0 forks / valid chain.
No sentinel row and no schema change are required. Fallback A would require a sentinel row and is
therefore a separately authorized D-MPI-2a decision, not part of this recommendation.

### 4.3 Version update mechanism
Use **atomic SQL** (`UPDATE … SET version = version + 1 … RETURNING version`) for counter
increments where only the new value matters (`resolver.py:515`, `canonical_service.py:128,130`).
Use an **optimistic guard** (`WHERE version = :expected`) only where validation genuinely depends
on the prior value; bound its retries. Retain the existing `FOR UPDATE` citizen lock as the
deterministic ordering mechanism, not as the sole version protection. Evidence: 0 lost updates for
atomic and optimistic mechanisms; 40 retries at 10 workers for optimistic.

### 4.4 MPI row-lock ordering
Total order: **(1)** transaction-scoped advisory lock (global, single key) → **(2)** citizen rows by
ascending immutable `Citizen.id` in one statement (`resolver.py:459-465`) → **(3)** all reads and
writes inside the existing SAVEPOINT. Do not acquire new row locks inside the SAVEPOINT and do not
introduce a second audit-tail row lock while the advisory lock is held. This preserves the tested
ascending-order property and extends it across the audit critical section. (`INFERRED`: the combined
full-merge lock sequence was not benchmarked.)

### 4.5 Idempotency behaviour
- **Merge:** keep the existing post-lock lookup by `(primary.id, secondary.id, event_type)` and
  return the original `MergeAudit` on replay (`resolver.py:475-488`).
- **Resolve:** keep the DB-enforced `uq_identity_claims_lab_patient` constraint
  (`models.py:124`); on SQLSTATE `23505` inside a SAVEPOINT, re-read and return the winning claim
  instead of propagating an error (D-MPI-5). No schema change needed.
- **Conflicting payload for the same key:** reject without mutating audit or identity state;
  define payload comparison explicitly in implementation (no API contract change).
- Never create a second audit row during recovery.

### 4.6 Audit-chain verification
Keep `verify_merge_audit_chain()` (`resolver.py:175-208`) strictly as **detection**. It currently has
**no production caller** (`VERIFIED_IN_SOURCE`), so MPI-08 must (a) invoke a segment check inside the
existing SAVEPOINT before `savepoint.commit()`, and (b) expose the full-chain check through an
authorized operational path with an agreed fork-response policy (D-MPI-3/4). Never represent
verification as fork prevention. Note that the existing checks at `resolver.py:529-534` validate
claims/state/canonical-chain consistency, **not** the hash chain.

### 4.7 Transaction ownership
Unchanged: the service owns the SAVEPOINT; the API/caller owns the outer transaction and commit
(`resolver.py:432-442`, `resolver.py:502-538`). The advisory lock must be acquired by the outer
transaction owner before calling the service, or by the service at entry before `begin_nested()`
with a documented requirement that the session is not already inside a different lock order.
`SAVEPOINT RELEASE` is not `COMMIT`; no post-commit verification is claimed by the service.

### 4.8 Commit boundary
Response is returned only after the caller's outer commit. Post-commit work is limited to
idempotency-based reconciliation. External side effects are out of scope and not claimed atomic.

### 4.9–4.13 Retry, recovery, pooling, observability (summary; full matrix in the recovery document)
- Retry **only transient** SQLSTATEs: `40001` (serialization_failure — requires complete transaction
  restart), `40P01` (deadlock_detected — full rollback + restart), `55P03` (lock_not_available —
  bounded wait/retry).
- Do **not** retry `23505` as an error (handle as idempotent replay at the claim key), `23503`
  (foreign_key_violation), `23514` (check_violation), `22xxx` data exceptions, or validation errors.
- Bounded attempts: **3 total** (initial + 2 restarts), controlled backoff 25 ms / 50 ms with small
  production jitter; deterministic barriers in tests, never random sleeps to force race outcomes.
- Transaction-scoped advisory locks are automatically released on commit/rollback and are safe with
  connection pooling; always roll back the session on exception before returning it to the pool.
- Use existing Prometheus/metrics infrastructure; no Redis, distributed lock service or new
  external dependency. Instrument lock wait, retry count by SQLSTATE, chain-verification result and
  fork count, merge duration, and idempotent replay rate.

### 4.14 API compatibility
No endpoint, request/response schema, status code or client contract change. All keys are existing
keys; all service signatures remain valid. No new required request field is introduced.

### 4.15 Fallback strategy
If advisory locks are unavailable or rejected for a deployment: use **A (single sentinel row locked
`FOR UPDATE` first)** as the primary chain serializer, **with D-MPI-2a schema authorization
required before implementation**. A last-row-only lock remains insufficient for genesis and must
not be substituted silently. If D-MPI-2a is not granted, there is no approved fallback that is both
genesis-safe and schema-free; stop and return to the owner.

---

## 5. Trade-offs

- **PostgreSQL coupling:** advisory locks are PostgreSQL-specific. The platform is PostgreSQL 16.14
  (`TEST_VERIFIED`), so this is acceptable, but portability is reduced versus a portable row lock.
- **Repository test limitation:** in-repo tests run on SQLite, which emits no `FOR UPDATE`; PostgreSQL
  runtime proof exists only in the out-of-repo harness. Implementation tests must therefore include
  PostgreSQL-backed concurrency cases, not only SQLite assertions.
- **Single-key contention:** one global key serializes all MPI audit appends; this is intentional for
  chain integrity and is the cost of correctness. Measured isolated median throughput was 84.47
  ops/s with p95 142.3 ms versus unsafe naive 123.88 ops/s with p95 101.5 ms — not a production
  target, only an observed cost.
- **Unmeasured combined behaviour:** full merge + claims + SAVEPOINT + advisory lock, 50 workers,
  multi-node behaviour and pooled-connection edge cases are `NOT_MEASURED`.
- **Operational simplicity:** no new infrastructure, no migration for the recommended path, no new
  privileges, no new secrets. Fallback A adds a sentinel-row lifecycle and a migration.
- **Retry discipline:** a single-key advisory lock should make `40001`/`40P01` rare; retries are a
  safety net, not the primary mechanism.

---

## 6. Failure scenarios (summary)

| Scenario | Detection | Outcome | Retry | Recovery |
|---|---|---|---|---|
| Lock timeout (`55P03`) | SQLSTATE | victim rolled back | bounded | re-acquire from clean transaction |
| Deadlock (`40P01`) | SQLSTATE | victim rolled back | bounded, full restart | fresh transaction; ordering already enforced |
| Serialization failure (`40001`) | SQLSTATE | full rollback | bounded, full restart | never reuse failed session/transaction |
| Connection lost before commit | connection error | outer rollback | yes | client retry with existing key |
| Connection lost after commit | idempotency lookup | committed | no blind replay | return original audit row |
| Audit insert failure | exception | SAVEPOINT rollback | transient only | no orphan audit |
| Hash verification failure | verifier result | SAVEPOINT rollback / incident | no | preserve evidence; owner response policy |
| Version conflict | guard/rowcount | SAVEPOINT rollback | bounded | re-read then retry |

Full detection/outcome/retry/recovery detail: `MPI_FAILURE_RECOVERY_MATRIX.md`.

---

## 7. Security implications

- No new credentials, privileges, secrets or network exposure. Advisory lock key is a public
  constant and carries no sensitive data.
- Single global key serializes across tenants; this is a correctness choice, not a cross-tenant data
  leak. Tenant isolation remains enforced by existing authorization, not by the lock key.
- Existing audit redaction (`canonical_audit._redact`) and raw-identifier hashing
  (`resolver.py:242-243,273-274`) are preserved; no patient data is introduced into the harness or
  documentation.
- No protected repository, protected database, migration or production configuration is touched.

## 8. Migration implications

**Recommended architecture: no schema change, no application migration.** All required unique
constraints and indexes already exist (`models.py:124-126`). Fallback A requires a sentinel row and
a separately authorized migration (D-MPI-2a); that authorization is **not** granted here.

## 9. Acceptance criteria for the implementation tranche

1. Zero audit-chain forks at 2 / 5 / 10 / 20 workers with independent sessions and deterministic
   barriers, including genesis.
2. Zero lost version updates at 2 / 5 / 10 / 20 workers for both resolver and canonical paths.
3. Zero partial merges under rollback, connection interruption and worker termination.
4. Zero duplicate successful merge operations for the same idempotency key.
5. Deterministic lock order verified by a locking-order test; zero `40P01` under the approved order.
6. Bounded retries: every transient failure classified correctly; no permanent violation retried.
7. Complete `verify_merge_audit_chain()` success after concurrent operations.
8. No API contract, migration, HOLD, D-020/D-021 or protected-repository change.
9. Full backend suite and architecture/domain gates pass in the implementation tranche, including
   PostgreSQL-backed concurrency tests (SQLite alone cannot prove row locking).
10. Transient SQLSTATEs are classified and bounded; permanent integrity violations are never
    retried; the post-commit attribute-read failure window is eliminated or reconciled.
11. No performance target is asserted from the isolated benchmark; a separate benchmark plan is in
    `MPI_IMPLEMENTATION_EXECUTION_PLAN.md` §11.

## 10. Unresolved owner decisions

| ID | Decision | Current status |
|---|---|---|
| D-MPI-1 | Approve/reject the recommended advisory-lock architecture | `NEEDS_OWNER_DECISION` |
| D-MPI-2a | Sentinel-row schema authorization (fallback A only) | `NEEDS_OWNER_DECISION` |
| D-MPI-3 | Cross-domain reference ownership / unmerge policy | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` |
| D-MPI-4 | Audit event taxonomy for review decisions | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` |
| D-MPI-5 | Concurrent first-resolve policy (now implementable with existing constraint) | `NEEDS_OWNER_DECISION` |
| D-MPI-6 | Canonical-service hardening scope | `NEEDS_OWNER_DECISION` |
| D-020 / D-021 | Release decisions | `PENDING_APPROVAL` |
| Release | FINAL_DECISION | HOLD |

Honesty baseline preserved: **0 PRODUCTION_VERIFIED, 0 RUNTIME_VERIFIED, 0 E2E_VERIFIED**,
RPO/RTO UNMEASURED, F-085 OPEN, OCR/NFC L0, ID Scan `needs_confirmation`.

**STOP — PROPOSED — NOT APPROVED. No production code, migration, API, configuration or governance
decision was changed. Await explicit owner approval of D-MPI-1.**
