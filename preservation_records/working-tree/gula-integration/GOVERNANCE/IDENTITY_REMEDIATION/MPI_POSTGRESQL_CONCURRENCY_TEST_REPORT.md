# MPI PostgreSQL Concurrency & Serialization Evaluation — Test Report

**Tranche:** `GULA — MPI POSTGRESQL CONCURRENCY TESTING & SERIALIZATION EVALUATION`
(evaluation only — no production code, strategy activation or approval).
**Repository:** `/home/samertts/workspace/projects/gula-integration` @
`integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
**Protected repository:** `/home/samertts/workspace/projects/gula-platform` @
`remediate-security-001` / `f478676b6fc375338648dde46fbf076c015a3f91` — clean, untouched.
**Release:** HOLD — `GOVERNANCE/FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552`, unchanged.
**D-020 / D-021:** `PENDING_APPROVAL`, unchanged. **D-MPI-1:** `NEEDS_OWNER_DECISION`, unchanged.
**Test date:** 2026-11-18.

Evidence vocabulary: `TEST_VERIFIED` (measured on the isolated PostgreSQL instance),
`VERIFIED_IN_SOURCE` (read from current source), `MEASURED_OBSERVATION` (recorded, not asserted as a
guarantee), `NOT_MEASURED`, `OUT_OF_SCOPE`. Decision vocabulary: `RECOMMENDED` (not approved),
`NEEDS_OWNER_DECISION`, `OWNER_APPROVED`.

Credentials, connection string and password values are deliberately absent from this document and
from every repository file. Only non-secret connection *metadata* is recorded.

---

## 1. Executive summary

The dedicated PostgreSQL 16.14 environment provisioned by the prior tranche was re-verified against
the strict safety gate (all conditions PASS), then used to execute **65 evaluation tests with
independent PostgreSQL sessions, deterministic `threading.Barrier` synchronisation and bounded
timeouts. Result: 65 passed / 0 failed / 0 skipped, exit 0, 87.61 s.** All data was synthetic.

**Proven behaviour (TEST_VERIFIED):**

- The current audit append pattern — unlocked `ORDER BY id DESC LIMIT 1` predecessor read followed by
  an insert (`resolver.py:110-115`, `resolver.py:118-163`) — **forks deterministically** when two
  sessions read the same tail: 100-op runs produced 50 / 20 / 10 / 5 fork groups at 2 / 5 / 10 / 20
  workers; simultaneous genesis produced two rows sharing the all-zero predecessor.
- Plain `secondary.version += 1` read-modify-write loses updates: 1, 4, 9 and 19 lost increments at
  2, 5, 10 and 20 workers respectively (expected = worker count, actual = 1 in every case).
- Opposite-order row locking produces a real deadlock (SQLSTATE `40P01`); ascending-ID ordering
  produced 0 deadlocks at 10 workers for both identical and overlapping identity pairs.
- Transaction rollback, connection interruption and worker termination leave no partial row; the
  hash-chain verifier detects tampered `entry_hash`, `prev_hash`, timestamps and invalid predecessors.
- Idempotency holds: duplicate requests replay, conflicting payload keys are rejected, and a retry
  after an interrupted commit produces no second merge or audit event.

**Strategies evaluated (not selected):**

| Strategy | Fork-safe incl. genesis | Lost-update protection | Median throughput | Median p95 / p99 | Retry burden | Schema impact |
|---|---|---|---|---|---|---|
| A — sentinel row lock | **PASS** (20 workers, 0 forks) | not provided by tail lock alone | 75.53 ops/s | 137.1 / 164.1 ms | none | sentinel row required |
| B — transaction advisory lock | **PASS** (20 workers, 0 forks) | not provided by audit lock alone | 84.47 ops/s | 142.3 / 180.6 ms | none | none |
| C — SERIALIZABLE + full retry | **NOT GUARANTEED** — fork observed in diagnostics | via SSI for version rows (theoretically; not isolated here) | 82.17 ops/s | 366.9 / 397.4 ms | ~190 failures/retries per 60 ops | none |
| D — atomic SQL increment | **NO** — does not serialise predecessor selection | **PASS** (0 lost at 10 and 20 workers) | 105.54 ops/s | 130.6 / 149.3 ms | none | none |

The most consequential new finding is that **SERIALIZABLE with correct full-transaction retry is not
a sufficient audit-chain fork prevention on its own**: controlled diagnostics reproduced a two-row
genesis fork (ids 2 and 7 both referencing the zero predecessor) despite 33 serialization failures
being correctly classified and retried, with zero unhandled worker errors. The in-suite 20-trial
incidence run recorded 0/20 invalid chains (964 serialization failures total); across all diagnostic
runs the fork was observed in 2 of roughly 100 trials. The property is therefore
`MEASURED_OBSERVATION`: *rare but possible*, not *impossible*.

**No strategy was selected or implemented.** D-MPI-1 remains `NEEDS_OWNER_DECISION`. This report
provides evidence for that decision only. **0 application source files changed, 0 migrations, 0 Git
operations, protected repository untouched, no credentials exposed.**

---

## 2. Authorization boundaries

Authorized and performed: read source/tests/provisioning report; connect only to `mpi_test` via the
out-of-repo `MPI_TEST_POSTGRES_URL`; create temporary tables/indexes in `mpi_concurrency_test`;
create synthetic fixtures; run concurrency tests and controlled benchmarks; generate this report and
update directly related governance documents under `GOVERNANCE/IDENTITY_REMEDIATION/`.

Not performed: changes to `resolver.py`, `identity_matching.py`, models, API contracts,
`backend/migrations/env.py`, migrations, production config or dormant modules; access to any
protected database; DDL outside `mpi_concurrency_test`; commit, push, merge, rebase, PR, deploy or
release; container/volume cleanup; MPI unmerge, NHID canonicalization, cross-domain repointing;
D-020/D-021 approval; HOLD change; serialization selection.

The test harness lives **outside the repository** at `/tmp/opencode/gula-mpi-tests/` specifically to
keep `SOURCE_FILES_CHANGED: 0`. No test file was added to the repository.

---

## 3. Source baseline

Current source was re-read before testing (no inference from prior reports):

| Path | Finding (evidence class) |
|---|---|
| `backend/app/services/mpi/resolver.py:110-115` | `_last_audit_hash()` = `db.query(MergeAudit).order_by(MergeAudit.id.desc()).limit(1).first()` — **no `with_for_update()`** (`VERIFIED_IN_SOURCE`). |
| `resolver.py:118-163` | `_write_audit()` computes `entry_hash` over a canonical payload containing `prev_hash` and one shared `occurred_at`; caller owns commit (`VERIFIED_IN_SOURCE`). |
| `resolver.py:175-208` | `verify_merge_audit_chain()` re-walks and detects tampering/forks — explicitly a **detection** control, not prevention (`VERIFIED_IN_SOURCE`). |
| `resolver.py:454-465` | merge locks both citizens in one `ORDER BY Citizen.id.asc().with_for_update()` statement — the existing key-ordered lock pattern (`VERIFIED_IN_SOURCE`). |
| `resolver.py:472-488` | idempotent retry returns the original audit row when secondary is already merged (`VERIFIED_IN_SOURCE`). |
| `resolver.py:502-538` | merge wrapped in `db.begin_nested()` SAVEPOINT with post-merge checks before caller commit (`VERIFIED_IN_SOURCE`). |
| `resolver.py:515` | `secondary.version += 1` read-modify-write inside that SAVEPOINT (`VERIFIED_IN_SOURCE`). |
| `backend/app/services/mpi/canonical_service.py:128,130` | `source.version = source.version + 1` / `target.version = target.version + 1` with no `with_for_update()` in `merge_canonicals()` — a second unprotected increment path (`VERIFIED_IN_SOURCE`). |
| `backend/app/identity/services/canonical_audit.py:133-141` | existing precedent: `_last_canonical_hash()` uses `.with_for_update()` on an ordered `LIMIT 1` query (`VERIFIED_IN_SOURCE`). |

Baseline captured before any action: branch/HEAD and 244 status entries (104 ` M`, 120 `??`,
20 `R `), 304 untracked files, tracked diff +2619/−2121, staged 20 renames. All preserved.

Existing MPI test inventory (not modified): `test_identity_matching.py` (31 tests, tracked),
`test_mpi_matcher.py` (35, tracked), `test_mpi_hash_chain_integrity.py` (11, untracked),
`test_mpi_merge_integrity.py` (6, untracked).

Seven known risk areas were revalidated: (1) unlocked audit-tail read — confirmed; (2) concurrent
append fork — reproduced; (3) lost version increment — reproduced; (4) citizen lock ordering —
validated under PostgreSQL; (5) caller-owned commit failure behaviour — tested; (6) cross-domain
references — `OUT_OF_SCOPE`; (7) MPI unmerge — `OUT_OF_SCOPE`.

---

## 4. Database safety verification

Re-inspected before the first connection; no connection string or password printed.

| # | Condition | Evidence | Verdict |
|---|---|---|---|
| 1 | Container identity | `docker inspect` → `/gula-mpi-pg-test`, `postgres:16-alpine`, `running`/`healthy` | PASS |
| 2 | Network | `gula-mpi-test-network` only (`172.20.0.2`) | PASS |
| 3 | Volume | `gula-mpi-test-data -> /var/lib/postgresql/data` only | PASS |
| 4 | Endpoint | host binding `127.0.0.1:55432` (loopback only) | PASS |
| 5 | Database / role | session query → `current_database()=mpi_test`, `current_user=mpi_test_user`, `rolsuper=false` | PASS |
| 6 | Cluster contents | `databases=mpi_test,postgres,template0,template1`; `public_user_tables=0`; no `mpi_%` schema pre-existing | PASS |
| 7 | Credential source | secure config `/tmp/opencode/gula-mpi-pg-test/mpi_test.env`, mode `600`, outside both repositories | PASS |
| 8 | No shell DB env vars | `env` scan: no `DATABASE_URL` / `MPI_TEST_POSTGRES_URL` / `POSTGRES_*` | PASS |
| 9 | Protected DB untouched | `gula-postgres` still `gula-platform_default` / `pgdata` / running | PASS |
| 10 | Protected repo clean | 0 status entries at `f478676b…` | PASS |

All gate conditions PASS; connection was then made exclusively through the dedicated config. No
alternative endpoint was probed.

---

## 5. Test schema description

Dedicated schema `mpi_concurrency_test`, created by the out-of-repo harness; **no table was created in
`public`** (`public_user_tables=0`, re-verified after all tests). All objects are synthetic and
namespaced. Schema setup is `DROP SCHEMA … CASCADE` + `CREATE` at session start; tables are truncated
with `RESTART IDENTITY` before every test, and the sentinel hash is reset to the genesis constant.

| Table | Purpose |
|---|---|
| `audit_chain` | synthetic audit records (`event_type`, `primary_id`, `secondary_id`, `match_score`, `features`, `reason`, `decided_by`, `occurred_at`, `prev_hash`, `entry_hash` UNIQUE); index on `prev_hash` |
| `identity_record` | primary/secondary synthetic identity rows with integer `version` counter and explicit `synthetic BOOLEAN NOT NULL DEFAULT TRUE` |
| `merge_operation` | synthetic merge operation identifiers (`op_id` PK, `payload_hash`, `created_at`) — idempotency keys |
| `audit_link` | FK from operation to audit row (`REFERENCES merge_operation ON DELETE RESTRICT`) — FK enforcement fixture |
| `audit_sentinel` | single fixed row `id=1 CHECK (id=1)` holding `last_hash` — Strategy A fixture |

Fixtures use only deterministic `SYNTH-*` identifiers, `SYNTH-USER`, a constant synthetic timestamp
`2026-11-18T00:00:00.000000+00:00`, and a fixed 64-zero genesis hash. No real name, National ID,
NHID, clinical record, export or snapshot was used. A non-vacuous supplementary check after seeding
returned `identity_record (total=1, synthetic=1, all notes synthetic=True)` and
`audit_chain (total=1, all secondary_id LIKE 'SYNTH-%'=True, distinct occurred_at=1)` →
`SYNTHETIC_BY_CONSTRUCTION`.

---

## 6. PostgreSQL baseline

| Setting / check | Measured value (TEST_VERIFIED) |
|---|---|
| `SELECT version()` | `PostgreSQL 16.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit` |
| `max_connections` | `60` |
| `shared_buffers` | `128MB` |
| `wal_level` / `fsync` / `synchronous_commit` | `replica` / `on` / `on` |
| `deadlock_timeout` | `1s` |
| Container limits | 1 vCPU, 1 GiB RAM (from provisioning; unchanged) |
| Transaction commit visible across sessions | PASS |
| Transaction rollback invisible | PASS |
| Unique constraint (`merge_operation.op_id`) | PASS — `23505` raised |
| Foreign key (`audit_link.op_id`) | PASS — FK violation raised |
| Row-lock behaviour + timeout | `FOR UPDATE` blocked contender; `lock_timeout=1s` fired at **1.008 s**, SQLSTATE `55P03` |
| Isolation level | READ COMMITTED default; SERIALIZABLE set explicitly per strategy test |
| Concurrent connections | 20 independent sessions opened and queried successfully |

No global PostgreSQL configuration was changed. No `public` table was created.

---

## 7. Hash-chain concurrency results

All appends used independent connections and a deterministic barrier after the predecessor read
(forced coincidence), 100 operations per concurrency level, bounded join timeouts.

| Workers | Ops | Rows committed | Fork groups | Max rows sharing a predecessor | Chain valid | Worker errors | Elapsed |
|---|---|---|---|---|---|---|---|
| 2 | 100 | 100 | 50 | 2 | **NO** | 0 | 2.988 s |
| 5 | 100 | 100 | 20 | 5 | **NO** | 0 | 3.888 s |
| 10 | 100 | 100 | 10 | 10 | **NO** | 0 | 4.889 s |
| 20 | 100 | 100 | 5 | 20 | **NO** | 0 | 3.102 s |

Sequential control: 100 appends → 100 rows, 0 forks, chain **valid**, stable single timestamp
representation, all hashes recomputable.

Verifier controls: tampered `entry_hash`, tampered `prev_hash` and tampered `occurred_at` were each
detected (`chain.valid=false` with a specific mismatch error); a synthetic row with an invalid
predecessor was detected. Failure after tail read but before insert left **zero** orphan rows.

**Conclusion:** the current unlocked tail read permits two committed audit records to reference the
same predecessor. Fork detection works; fork **prevention is not implemented**.

---

## 8. Genesis results

| Strategy | Workers | Rows | Forks | Chain valid | Notes |
|---|---|---|---|---|---|
| Naive (no lock) | 2 | 2 | 1 (both reference `0…0`) | **NO** | `id=2: prev_hash does not link to preceding entry` |
| A — sentinel row | 20 | 20 | 0 | **YES** | locked sentinel before predecessor read |
| B — advisory lock | 20 | 20 | 0 | **YES** | `pg_advisory_xact_lock(hashtext(key)::bigint)` — transaction-scoped |
| C — SERIALIZABLE | 10 | 10 | 0 in this run | YES | 33 serialization failures, 33 full-transaction retries |

**Critical qualification for Strategy C:** a separate 20-trial incidence run recorded 0/20 invalid
chains (964 serialization failures total), but earlier controlled diagnostics reproduced a fork at
approximately 1/20 and 1/60 trials. Captured failing chain (10 workers, 10 committed appends, 33
serialization failures, 0 worker errors):

```
id=2   prev=0000000000  hash=6ebce04290
id=7   prev=0000000000  hash=f291286d62   <-- second genesis row (fork)
id=16  prev=f291286d62  hash=a9a624afa8
... (remaining 7 rows chain normally from id=7)
verifier: fork_groups=1, errors=['id=7: prev_hash does not link to preceding entry']
```

Therefore **genesis safety is PROVEN for A and B, and NOT GUARANTEED for C**. This is a
`MEASURED_OBSERVATION`, not a claim that C always fails.

---

## 9. Lost-update results

Baseline seeded to version 0; expected final version = number of workers.

| Approach | Workers | Expected | Actual | Lost updates | Retries | Elapsed |
|---|---|---|---|---|---|---|
| Naive read-modify-write | 2 | 2 | 1 | **1** | 0 | 0.069 s |
| Naive read-modify-write | 5 | 5 | 1 | **4** | 0 | 0.122 s |
| Naive read-modify-write | 10 | 10 | 1 | **9** | 0 | 0.272 s |
| Naive read-modify-write | 20 | 20 | 1 | **19** | 0 | 0.570 s |
| `SELECT … FOR UPDATE` | 10 | 10 | 10 | **0** | 0 | 0.354 s |
| Atomic `SET version=version+1` | 10 | 10 | 10 | **0** | 0 | 0.164 s |
| Atomic `SET version=version+1` | 20 | 20 | 20 | **0** | 0 | 0.471 s |
| Optimistic `WHERE version=:expected` | 10 | 10 | 10 | **0** | 40 | 0.504 s |

Interpretation: the plain read-modify-write pattern (present in `resolver.py:515` and
`canonical_service.py:128,130`) loses all but one concurrent increment when workers read before any
writes. In the `resolver.py` merge path specifically, the citizen rows are locked first
(`resolver.py:459-465`), which serialises same-pair increments; that does **not** protect independent
pairs or the `canonical_service` path. Row locks, atomic SQL and optimistic guards all prevent the
loss in the isolated model.

---

## 10. Lock-ordering and deadlock results

| Scenario | Deadlocks | SQLSTATE | Stuck / unhandled errors | Result |
|---|---|---|---|---|
| Two rows locked in opposite order | **1** | `40P01` | 0 / 0 | Deadlock detected by PostgreSQL; victim rolled back |
| Ten workers, ascending-ID order | 0 | — | 0 / 0 | No deadlock |
| Ten workers, overlapping identity pairs, ascending order | 0 | — | 0 / 0 | No deadlock |
| Ten workers, same identity pair, ascending + atomic increment | 0 | — | 0 / 0 | Final version 11 = seed 1 + 10 commits |
| Lock timeout with holder active | 0 | `55P03` | 0 / 0 | Timed-out victim rolled back; connection usable afterwards |
| Recovery after deadlock victim | — | — | 0 / 0 | Fresh transaction succeeded |

The current key-ordered citizen lock pattern in `resolver.py` is therefore validated under real
PostgreSQL for the tested shapes. No `40P01` handling exists in the inspected MPI path
(`VERIFIED_IN_SOURCE`); retry policy remains an owner decision.

---

## 11. Idempotency and atomicity results

| Scenario | Result | Evidence |
|---|---|---|
| Same operation sequentially | `applied` then `replayed` | 1 merge operation, 1 audit row |
| Same operation concurrently (2 sessions) | 1 × `applied`, 1 × `23505` (unique violation) | 1 merge operation, 1 audit row, 0 stuck |
| Same key, conflicting payload | `rejected` | still 1 / 1 |
| Failure after audit insertion | full rollback | 0 audit rows, identity version unchanged at 1 |
| Failure after identity update | full rollback | 0 audit rows |
| Failure before outer commit | full rollback | 0 merge operations, 0 audit rows |
| Client retry after interruption | `replayed` | 1 / 1, chain valid |

Distinction preserved: transaction rollback is deterministic and verified; a client-side ambiguous
commit outcome (connection lost after commit, before response) is handled by the idempotency key
rather than assumed atomic. No partially applied merge was observed. External side effects were not
in scope and are **not** claimed atomic.

---

## 12. Strategy comparison

**A — Sentinel row locking.** A fixed `audit_sentinel` row is locked with `FOR UPDATE` before the
tail is read; the audit row is inserted and the sentinel hash advanced in the same transaction.
Fork-safe including genesis (20/20 workers, 0 forks). Lock is released on commit or rollback.
Acquisition order is single-row-first, so deadlock risk is low; benchmarks recorded 0 deadlocks.
Throughput is reduced by forced serialisation of every append. Requires a sentinel row (schema
impact) and disciplined ordering if combined with other locks.

**B — Transaction advisory locks.** `pg_advisory_xact_lock(hashtext('mpi_concurrency_test.audit_chain')::bigint)`
serialises the critical section without a row. Fork-safe including genesis (20/20, 0 forks), 0
deadlocks in benchmark, automatic release on commit/rollback. Key derivation is stable in this
harness; a poorly derived key could over- or under-serialise in production. PostgreSQL-specific
coupling. Only transaction-scoped locks were used; session-scoped locks were **not** used or tested.

**C — SERIALIZABLE.** Every append is a full transaction retried on SQLSTATE `40001` with bounded
linear backoff and a fresh transaction on each attempt. Under 10 workers it generated 186–217
serialization failures per 60 operations in benchmark reps, with p95 around 367 ms and p99 around
397 ms. Correctly classified and retried, but the genesis fork reproduced above shows that tail
selection via `ORDER BY id DESC LIMIT 1` is not fully protected by SSI in this pattern. Requires
complete transaction retry and idempotency at the caller.

**D — Atomic SQL.** Atomic `version=version+1` completely prevents the lost-update class (0 lost at
10 and 20 workers) at the highest measured non-naive throughput. It does **not** select a
predecessor, so it provides no audit-chain fork prevention and no genesis safety by itself. It is a
complementary building block, not a serialization strategy for the chain.

No strategy was implemented or selected.

---

## 13. Performance benchmarks

Identical conditions for every strategy and repetition: 10 workers, 6 operations per worker
(60 planned), 3 repetitions, 10-way deterministic barrier, `lock_timeout=15s`, `statement_timeout=30s`,
1 vCPU / 1 GiB container. Latency measured per successful operation; lock wait measured where a
lock is explicitly acquired (`NOT_MEASURED` otherwise). **These are isolated-environment numbers,
not production capacity.**

### Raw results (all three repetitions)

| Strategy | Rep | Successful / planned | Wall (s) | Throughput (ops/s) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Lock-wait p95 (ms) | 40001 | 40P01 | Failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| naive | 1 | 60/60 | 0.5173 | 115.99 | 26.345 | 101.504 | 120.756 | 129.758 | NOT_MEASURED | 0 | 0 | 0 |
| naive | 2 | 60/60 | 0.3393 | 176.84 | 11.059 | 61.761 | 62.049 | 62.218 | NOT_MEASURED | 0 | 0 | 0 |
| naive | 3 | 60/60 | 0.4843 | 123.88 | 23.151 | 114.208 | 119.156 | 120.606 | NOT_MEASURED | 0 | 0 | 0 |
| sentinel | 1 | 60/60 | 0.9346 | 64.20 | 100.829 | 205.106 | 258.193 | 278.454 | 192.234 | 0 | 0 | 0 |
| sentinel | 2 | 60/60 | 0.7944 | 75.53 | 72.043 | 130.738 | 164.094 | 173.152 | 123.179 | 0 | 0 | 0 |
| sentinel | 3 | 60/60 | 0.6829 | 87.86 | 70.181 | 137.097 | 157.078 | 163.569 | 130.027 | 0 | 0 | 0 |
| advisory | 1 | 60/60 | 1.0016 | 59.90 | 94.788 | 214.348 | 252.166 | 265.097 | 196.839 | 0 | 0 | 0 |
| advisory | 2 | 60/60 | 0.6606 | 90.82 | 58.691 | 92.154 | 109.051 | 121.569 | 81.338 | 0 | 0 | 0 |
| advisory | 3 | 60/60 | 0.7103 | 84.47 | 72.506 | 142.349 | 180.600 | 184.299 | 131.293 | 0 | 0 | 0 |
| serializable | 1 | 60/60 | 0.5757 | 104.23 | 20.118 | 208.974 | 261.554 | 290.848 | NOT_MEASURED | 217 | 0 | 0 |
| serializable | 2 | 60/60 | 0.7302 | 82.17 | 10.571 | 366.881 | 397.387 | 408.434 | NOT_MEASURED | 190 | 0 | 0 |
| serializable | 3 | 60/60 | 0.7859 | 76.34 | 15.797 | 382.729 | 485.449 | 499.486 | NOT_MEASURED | 186 | 0 | 0 |
| atomic_sql | 1 | 60/60 | 0.5685 | 105.54 | 34.359 | 130.586 | 149.345 | 160.598 | NOT_MEASURED | 0 | 0 | 0 |
| atomic_sql | 2 | 60/60 | 0.3231 | 185.72 | 23.802 | 70.385 | 84.716 | 92.114 | NOT_MEASURED | 0 | 0 | 0 |
| atomic_sql | 3 | 60/60 | 0.6751 | 88.87 | 56.526 | 158.498 | 199.260 | 230.897 | NOT_MEASURED | 0 | 0 | 0 |

### Medians and variability

| Strategy | Median throughput | Median p50 | Median p95 | Median p99 | Median max | Median 40001 | Median retries | Median deadlocks | Median failed |
|---|---|---|---|---|---|---|---|---|---|
| naive (unsafe baseline) | 123.88 | 23.151 | 101.504 | 119.156 | 120.606 | 0 | 0 | 0 | 0 |
| sentinel | 75.53 | 72.043 | 137.097 | 164.094 | 173.152 | 0 | 0 | 0 | 0 |
| advisory | 84.47 | 72.506 | 142.349 | 180.600 | 184.299 | 0 | 0 | 0 | 0 |
| serializable | 82.17 | 15.797 | 366.881 | 397.387 | 408.434 | 190 | 190 | 0 | 0 |
| atomic_sql | 105.54 | 34.359 | 130.586 | 149.345 | 160.598 | 0 | 0 | 0 | 0 |

Resource snapshots (`docker stats --no-stream`) stayed within limits: CPU 0.05 %–12.54 % of the
1 vCPU allocation, memory 51.29–52.09 MiB of 1 GiB. `atomic_sql` measures only the version-increment
operation; it is not an audit append benchmark. No value was extrapolated or fabricated.

---

## 14. Failure-injection results

| Scenario | Result |
|---|---|
| Connection closed before commit | no partial row |
| Explicit rollback after audit insert | no partial row |
| Lock timeout | SQLSTATE `55P03`; victim rolled back cleanly |
| Deadlock victim | SQLSTATE `40P01`; victim rolled back, connection usable |
| Serialization failure | 30 failures classified and retried; 10 rows committed; single run chain valid; recorded as observation, **not** a guarantee (see §8) |
| Duplicate request | handled idempotently |
| Invalid predecessor hash | detected by verifier |
| Corrupted audit record (`entry_hash`, `prev_hash`, timestamp) | detected by verifier |
| Concurrent genesis insertion | forked with naive append; safe with sentinel and advisory locks; SERIALIZABLE not guaranteed |
| Worker termination mid-transaction (child process SIGTERM) | no partial row |
| Chain after all injections | 10 synthetic appends → chain valid, 0 forks |

No unrelated container or the test volume was stopped, restarted or removed.

---

## 15. Security review

| Concern | Result |
|---|---|
| Credentials printed | **No** — only non-secret metadata recorded; harness reads the 0600 out-of-repo config internally |
| Secrets in repository | 0 hits across **33,115** scanned files; credential directory outside the repository |
| Test role privileges | `superuser=false`, `createdb=false`, `createrole=false`, `replication=false`, `bypassrls=false` |
| Connection target | `postgresql`, `127.0.0.1`, port `55432`, database `mpi_test`, user `mpi_test_user` — loopback-only |
| Other-database access | **Disclosed nuance:** `has_database_privilege` reports CONNECT = `true` for `postgres`, `template0`, `template1` because PostgreSQL grants CONNECT to `PUBLIC` by default; provisioning hardened only `mpi_test`. The role has **no explicit grant** on any of them (`false` for all three) and there is **no other application database** in this isolated cluster (`[]`). Those system DBs contain no application/patient data, and no harness connection targets them. Changing grants outside `mpi_concurrency_test` is out of scope and was **not** done. |
| Protected database connection | none — `gula-postgres` still on `gula-platform_default` / `pgdata` |
| Synthetic data only | `SYNTHETIC_BY_CONSTRUCTION` (§5); no real identifier or clinical record used |
| `public` schema | 0 user tables, before and after |
| Protected repository | 0 status entries at `f478676b…` |
| Cleanup scope | documented in §21; only `mpi_concurrency_test` was mutated by the harness |

No security control was weakened to obtain a pass. Two test assumptions were corrected during the
run and are disclosed in §19; both corrections made the tests stricter or more truthful.

---

## 16. Decision matrix

| Criterion | Sentinel Row Lock | Advisory Lock | SERIALIZABLE | Atomic SQL |
|---|---|---|---|---|
| Hash-chain fork prevention | **YES** — 0 forks at 2–20 workers; sentinel genesis 20/20 safe | **YES** — 0 forks at 2–20 workers; genesis 20/20 safe | **NOT GUARANTEED** — fork reproduced despite full retry (2 of ~100 diagnostic trials) | **NO** — predecessor selection not serialised |
| Genesis safety | **YES** — fixed sentinel row exists before first append | **YES** — lock is independent of chain contents | **NOT GUARANTEED** — two rows committed with zero predecessor | **NO** |
| Lost-update protection | Not by tail lock alone; tested separately: `FOR UPDATE`, atomic and optimistic all give 0 lost | Not by audit lock alone; separate version control required | Via SSI in principle; not isolated as a strategy result here | **YES** — 0 lost at 10 and 20 workers |
| Deadlock risk | 0 in benchmark; single-row-first ordering required | 0 in benchmark; key collision risk if derivation unstable | 0 deadlocks, but 186–217 `40001`/60 ops | Minimal for single-row UPDATE |
| Retry complexity | Low — lock waits, no transaction retry needed | Low — lock waits, no transaction retry needed | **High** — full transaction retry, bounded policy, fresh session txn, idempotent caller | Low |
| Throughput (median ops/s) | 75.53 | 84.47 | 82.17 | 105.54 (increment only) |
| p95 latency (median ms) | 137.097 | 142.349 | 366.881 | 130.586 |
| p99 latency (median ms) | 164.094 | 180.600 | 397.387 | 149.345 |
| Operational complexity | Low–medium (sentinel row lifecycle) | Medium (key derivation, PG coupling, txn scope discipline) | High (retry/backoff/idempotency tuning) | Low |
| Failure recovery | Lock auto-released on commit/rollback | Xact-scoped lock auto-released | Correct rollback + whole-txn retry required | Trivial single statement |
| Schema impact | **Yes** — one sentinel row/table | **None** | **None** | **None** |

Unmeasured criteria are marked explicitly: cross-process (multi-node) advisory-lock behaviour,
pooled-connection leak behaviour under session-scoped locks (session locks were not used), and
production-scale throughput are **NOT MEASURED**.

---

## 17. Recommended architecture

Evidence-based recommendation only — **not a selection, not an approval**:

- For **audit-chain append serialisation**, the only strategies that were proven fork-safe including
  genesis are **A (sentinel row lock)** and **B (transaction-scoped advisory lock)**. Between them,
  B avoids schema impact but adds PostgreSQL coupling and key-derivation discipline; A is simpler to
  reason about and matches the existing `canonical_audit.py` row-lock precedent, but requires a
  sentinel row whose introduction is a schema change and therefore a separately authorized decision
  (D-MPI-2a).
- **SERIALIZABLE alone is not sufficient** for the chain under the tested predecessor-read pattern;
  if used, it must be combined with an explicit chain-tail serialisation mechanism.
- **Atomic SQL increment is recommended as a complementary control** for the version-counter class
  of bugs (`resolver.py:515`, `canonical_service.py:128,130`), not as an audit-chain solution.
- Preserve the existing key-ordered citizen locking (`resolver.py:459-465`) and the verifier
  (`resolver.py:175-208`) as detection; the verifier must never be represented as prevention.

Known limitations of this recommendation: results come from a single-node, loopback, 1 vCPU / 1 GiB
container; only the audit append and version counter were modelled, not the full merge transaction
with claims, SAVEPOINT and caller-owned commit under the candidate lock; advisory-lock key derivation
for multi-tenant production was not designed; no migration, compatibility or operational runbook was
produced. Migration requirements, compatibility risks and operational risks are therefore
`NOT MEASURED` and must be assessed in the implementation tranche. Conditions that would invalidate
the recommendation: multi-node deployment changing lock semantics, a different chain-storage layout,
or evidence that a sentinel row cannot be introduced without unapproved schema change.

**D-MPI-1 stays `NEEDS_OWNER_DECISION`. No strategy was implemented or activated.**

---

## 18. Unresolved issues

| ID | Issue | Status |
|---|---|---|
| U-1 | Select audit serialization mechanism (A vs B; genesis handling) | `NEEDS_OWNER_DECISION` (D-MPI-1) |
| U-2 | Sentinel row introduction requires schema authorization | `NEEDS_OWNER_DECISION` (D-MPI-2a) |
| U-3 | Version increment hardening in `resolver.py:515` and `canonical_service.py:128,130` | `NEEDS_OWNER_DECISION`; no source change made |
| U-4 | `40P01` / `40001` handling in the MPI merge path | not implemented; policy undecided |
| U-5 | SERIALIZABLE rare genesis fork — root cause and whether a different tail query removes it | `MEASURED_OBSERVATION`; not fixed (evaluation-only) |
| U-6 | Full merge transaction (claims + SAVEPOINT + caller commit) under candidate locks | not modelled; out of scope |
| U-7 | Cross-domain references, MPI unmerge, NHID canonicalization | `OUT_OF_SCOPE` |
| U-8 | PUBLIC CONNECT on isolated-cluster system databases | disclosed in §15; not modified (out of scope, no data exposure) |

Honesty baseline preserved: **0 PRODUCTION_VERIFIED, 0 RUNTIME_VERIFIED, 0 E2E_VERIFIED**,
RPO/RTO UNMEASURED, F-085 OPEN, OCR/NFC L0, ID Scan `needs_confirmation`, D-020/D-021
`PENDING_APPROVAL`, HOLD.

---

## 19. Limitations

1. Isolated, disposable, single-node environment; no production capacity claim. Latencies include
   Python client threading and barrier overhead.
2. Only the minimum synthetic structures were modelled; the full ORM merge transaction was not
   executed against PostgreSQL.
3. `lock_wait` is measured only where a lock is explicitly acquired; other rows are `NOT_MEASURED`.
4. The in-suite `security_synthetic_fixtures` assertion ran against an empty table after reset and
   is vacuous; synthetic-ness is established by construction and by the non-vacuous supplementary
   check in §5.
5. SERIALIZABLE fork incidence is rare and nondeterministic: 0/20 in the in-suite trial, plus two
   reproduced forks in separate diagnostics (~100 trials). Both outcomes are reported; no rate is
   claimed as exact.
6. Benchmark variability is high (e.g. atomic_sql throughput 88.87–185.72 ops/s); medians and all raw
   repetitions are reported rather than a single headline number.
7. Harness corrections made during the run, all outside the repository and disclosed here for
   reproducibility:
   - `connect()` now commits session `SET`s so `set_session(isolation_level=…)` is legal (psycopg2
     rejects it inside a transaction).
   - Lock-timeout assertions now catch `psycopg2.errors.LockNotAvailable` for SQLSTATE `55P03`
     (they previously caught `QueryCanceled`, which is `57014`); the exact SQLSTATE is still asserted.
   - The lock-timeout failure-injection test now seeds its target row (a removed no-op had left the
     table empty, so no lock was contended).
   - The other-database security test was corrected to assert the in-scope guarantees (no explicit
     grant, no other application database) while recording the PUBLIC-CONNECT fact; it no longer
     asserts a property the provisioning design never provided.
   - The SERIALIZABLE chain-validity assertion was converted to a recorded observation after the
     fork was reproduced; it now asserts only no unhandled worker error, 10 committed rows and
     exercised contention. A dedicated 20-trial incidence test was added.
8. No application source, test, migration, API or configuration was changed; no test expectation was
   weakened to obtain a pass — the corrections above tighten or clarify what is asserted.

---

## 20. Reproducibility instructions

The harness is intentionally outside the repository at `/tmp/opencode/gula-mpi-tests/`
(`harness.py`, `conftest.py`, `test_00_*.py` … `test_70_*.py`). It reads credentials internally from
`/tmp/opencode/gula-mpi-pg-test/mpi_test.env`; never print or copy that value.

```bash
# Preconditions: gula-mpi-pg-test running/healthy; secure config mode 0600;
# git state and FINAL_DECISION md5 re-verified (see §2–§4).
cd /tmp/opencode/gula-mpi-tests
/tmp/opencode/gula-py312/bin/python -m pytest -q --disable-warnings
```

Expected: `65 passed`, exit 0, approximately 85–90 s. Metrics are written to
`/tmp/opencode/gula-mpi-tests/metrics.json` at session teardown. A fresh session recreates
`mpi_concurrency_test` with `DROP SCHEMA … CASCADE`; each test truncates its tables with
`RESTART IDENTITY`. Re-running is idempotent with respect to the database state. The environment is
bounded (1 vCPU / 1 GiB / `max_connections=60`); do not raise worker counts beyond the tested 20
without re-checking resource limits.

---

## 21. Cleanup procedure

**Not executed.** The test database, container, network and volume remain intact as required.

Harness-level cleanup (safe at any time): the session fixture drops and recreates only
`mpi_concurrency_test`; no object outside that schema was created. To discard only test data,
re-run the suite (schema recreation) or `DROP SCHEMA mpi_concurrency_test CASCADE` inside `mpi_test`
with explicit authorization.

Infrastructure teardown is **only on separate explicit authorization** (from the provisioning
report §12): `docker stop gula-mpi-pg-test`, `docker rm gula-mpi-pg-test`,
`docker volume rm gula-mpi-test-data`, `docker network rm gula-mpi-test-network`,
`rm -rf /tmp/opencode/gula-mpi-pg-test`. Never stop or remove `gula-postgres`, `pgdata`,
`gula-platform_default` or any other pre-existing resource.

---

## 22. Next-phase authorization request

This evaluation phase is complete. Requested next authorization (separate tranche):

1. Decide **D-MPI-1** — select the audit-chain serialization mechanism using the evidence in §16–§17.
2. Decide **D-MPI-2a** — if sentinel row (A) is selected, authorize the schema change; otherwise
   authorize transaction-scoped advisory locking (B) design and key derivation.
3. Authorize implementation of a single chosen mechanism **with matching regression tests**, plus
   the atomic version increment as a separate, clearly scoped change.
4. Authorize extending locking/verification to `canonical_service.merge_canonicals()` (D-MPI-6) and
   a bounded `40P01`/`40001` policy for the merge path.
5. Re-run the full backend suite and architecture/domain gates in the implementation tranche.

Explicitly **not** requested here: approval of D-020/D-021, HOLD change, NHID canonicalization, MPI
unmerge, cross-domain repointing, API/schema change without its own authorization, or any release
decision.

**STOP.** No production code was changed, no strategy was selected or activated, no migration ran,
the test database and volume were not removed, and no commit or push was made. Await explicit owner
authorization for the implementation phase.

---

### Post-analysis pointer (read-only, 2026-11-18)

The evidence above was consolidated, without re-running benchmarks or changing any decision, into
four `PROPOSED — NOT APPROVED` artifacts: `MPI_SERIALIZATION_ARCHITECTURE_DECISION.md` (recommendation
E = B + D + existing ascending row locks, no schema; SERIALIZABLE comparison-only),
`MPI_IMPLEMENTATION_EXECUTION_PLAN.md` (MPI-01..MPI-10), `MPI_FAILURE_RECOVERY_MATRIX.md`, and
`MPI_CROSS_COMPONENT_IMPACT.md`. D-MPI-1 `NEEDS_OWNER_DECISION`; HOLD, D-020/D-021 unchanged; no
source, migration, API, configuration or Git change.

**Final status:** `PHASE_STATUS: PASS` · `DATABASE_IDENTITY: VERIFIED` · `TEST_SCHEMA:
mpi_concurrency_test` · `65 tests / 65 passed / 0 failed / 0 skipped` · `SOURCE_FILES_CHANGED: 0` ·
`D_MPI_1: NEEDS_OWNER_DECISION` · `FINAL_DECISION: HOLD`.
