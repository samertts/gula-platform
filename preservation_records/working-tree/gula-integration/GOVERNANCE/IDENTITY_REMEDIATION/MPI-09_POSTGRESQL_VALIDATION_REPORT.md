# MPI-09 PostgreSQL Validation Report

**Status:** `PASS` (isolated, synthetic-only PostgreSQL validation; **not** production readiness)
**Date:** 2026-11-18
**Scope:** Real PostgreSQL 16.14 concurrency and failure validation of the **actual implemented MPI code**, plus strategy baselines. No production, protected or shared database was touched.

---

## 1. Environment (isolated, disposable)

| Item | Value |
|---|---|
| Container | `gula-mpi-pg-test` (healthy) |
| Network | `gula-mpi-test-network` (separate from protected `gula-platform_default`) |
| Volume | `gula-mpi-test-data` (separate from protected `pgdata`) |
| Database / role | `mpi_test` / `mpi_test_user` — `superuser=false`, `createdb=false`, `createrole=false`, `replication=false`, `bypassrls=false` |
| Server | `PostgreSQL 16.14 on x86_64-pc-linux-musl` |
| Key config | `max_connections=60`, `shared_buffers=128MB`, `wal_level=replica`, `fsync=on`, `synchronous_commit=on`, `deadlock_timeout=1s` |
| Schema | `mpi_concurrency_test` (dedicated, synthetic rows only) |
| Client timeout | `lock_timeout=15s` per connection |
| Test interpreter | isolated Python 3.12.13 venv at `/tmp/opencode/mpi-venv` (repo untouched) |
| Credentials | read from out-of-repo secure file at `/tmp/opencode/gula-mpi-pg-test/`; **never printed or written to any report** |

Security checks: `security_connection_target = mpi_test @ 127.0.0.1:55432`; `security_non_system_other_databases=[]`; no explicit grants to `postgres`/`template1`/`template0`; `security_public_tables=0`; protected PG network/volume untouched; repo secret scan `33,139 files scanned / 0 files with secrets`, no credential directory inside the repo.

---

## 2. Commands and exit codes

| Command | Result | Exit |
|---|---|---|
| `cd /tmp/opencode/gula-mpi-tests && python -m pytest -q test_*.py` | **73 passed in 74.40s** | **0** |
| `python -m pytest -q test_80_implementation.py` | **8 passed in 9.82s** | 0 |
| `python -m pytest -q test_80_implementation.py` (first attempt) | DSN error (`lock_timeout` as connect kwarg) → fixed to `options=-c lock_timeout=15s` | 1 (diagnosed, corrected) |
| `python -m pytest -q test_80_implementation.py` (second attempt) | ORM FK metadata error → registered lightweight stubs for `lab_users/labs/patients` | 1 (diagnosed, corrected) |
| Full log | `/tmp/opencode/mpi-impl/mpi09_full.log` | — |
| Metrics | `/tmp/opencode/gula-mpi-tests/metrics.json` | — |

Earlier isolated runs (`pytest_final2.log`) had one timing-dependent SERIALIZABLE fork assertion failure; the final clean run is the evidence of record, and the flaky run is retained in the harness directory rather than hidden.

---

## 3. Concurrency results — actual implementation

These tests call the **shipped** `resolver.merge_citizens`, `resolver.resolve_identity`, `acquire_audit_chain_lock` and `atomic_increment_version` against PostgreSQL.

| Scenario | Workers | Errors | Audits | Chain valid | Throughput (ops/s) | p95 (ms) | p99 (ms) |
|---|---|---|---|---|---|---|---|
| `merge_citizens` | 2 | 0 | 2 | true | 15.70 | 77.17 | 78.37 |
| `merge_citizens` | 5 | 0 | 5 | true | 10.66 | 146.07 | 151.24 |
| `merge_citizens` | 10 | 0 | 10 | true | 5.97 | 278.62 | 288.55 |
| `merge_citizens` | 20 | 0 | 20 | true | 3.06 | 568.37 | 590.85 |
| `resolve_identity` genesis | 20 | 0 | 20 | true | — | — | — |
| Same-pair concurrent merge | 10 | 0 | 1 | true | — | — | — |
| `atomic_increment_version` | 20 | 0 | — | final_version=21 | — | — | — |

Advisory lock scope test: an observer thread calling `pg_advisory_xact_lock(key)` blocks while the holder keeps the lock across a SAVEPOINT, and proceeds only after the holder's outer rollback — proving transaction scope and correct acquisition order.

---

## 4. Baseline vs implemented (why the controls matter)

| Failure mode | Naive / opposite baseline | Implemented control | Result |
|---|---|---|---|
| Concurrent genesis fork | naive 2 workers → `rows=2`, `fork_groups=1`, `valid=false` | advisory lock | `rows=20`, `forks={}`, `valid=true` |
| Lost version updates | 2/5/10/20 workers lost `1/4/9/19` increments | atomic `UPDATE … RETURNING` | `lost_updates=0` at 10 and 20 workers |
| Opposite lock order | `deadlocks=1`, SQLSTATE `40P01` | ascending-id `FOR UPDATE` | `deadlocks=0`, `stuck=0` |
| Lock wait | `lock_timeout` SQLSTATE `55P03` | classified transient, bounded retry | `timed_out=true`, handled |
| Duplicate client replay | naive retry produced duplicates | claim constraint + audit replay | no duplicates, 409 on conflict |
| SERIALIZABLE comparison | `serialization_failures=27`, retries 27; flaky fork incidence in stress trials (3/20 invalid chains at 10 workers) | advisory lock chosen instead | `0` forks with advisory lock |

SENTINEL-row fallback was validated as a **strategy** (`rows=20, valid=true`) but **not implemented**, because D-MPI-2a schema authorization was not granted.

---

## 5. Performance before/after (isolated benchmark — **no production SLA**)

Strategy-level medians from `metrics.json`:

| Strategy | Throughput (ops/s) | p50 (ms) | p95 (ms) | p99 (ms) | Median retries |
|---|---|---|---|---|---|
| Naive (incorrect — forks) | 358.54 | 8.30 | 35.98 | 48.85 | 0 |
| **Advisory lock (implemented)** | **136.49** | 68.29 | **78.30** | 82.65 | 0 |
| Sentinel row (fallback, not implemented) | 136.62 | 50.75 | 102.67 | 114.07 | 0 |
| Atomic SQL increment | 214.35 | 21.89 | 60.46 | 78.42 | 0 |
| SERIALIZABLE + retry | 119.37 | 10.19 | 203.13 | 243.10 | 227 |

Interpretation: the implemented advisory-lock path gives up throughput versus the *incorrect* naive path (≈358 → ≈136 ops/s; p95 ≈36 ms → ≈78 ms) and is comparable to the sentinel strategy, while eliminating forks. The full-stack `merge_citizens` numbers in §3 are lower because they include ORM mapping, claim repointing, hash computation and in-transaction verification — not just the lock append. These are isolated container numbers on local storage, **not** a capacity statement for national deployment.

---

## 6. Residual risks

- Results are from one disposable PostgreSQL 16.14 container with synthetic rows; no replicated/HA setup, no production-like data volume, no network partition test.
- Advisory locks are PostgreSQL-only; the SQLite test suite is explicitly **not** used as locking proof.
- 50-worker scenario was **not** run; the highest validated merge concurrency is 20 workers (and 20 for genesis/version).
- `55P03` and `40P01` were observed; retry correctness is bounded and classified, but no production timeout/SLA was established.
- Concurrency success in isolation is **not** production readiness.

## 7. Acceptance criteria

| Criterion | Result |
|---|---|
| Real PostgreSQL, not SQLite-only, used for locking proof | PASS |
| Actual implemented code exercised (not only abstract strategies) | PASS |
| No production/protected DB or schema touched | PASS |
| All synthetic data, no credentials printed | PASS |
| Performance before/after recorded honestly | PASS |
| Production readiness claimed | **NO** — explicitly not claimed |
