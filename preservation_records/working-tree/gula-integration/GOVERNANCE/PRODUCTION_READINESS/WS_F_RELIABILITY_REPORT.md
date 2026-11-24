# Workstream F — Reliability & Operations Readiness Report

**Program:** GULA Production Readiness Acceleration Program
**Workstream:** WS-F (Reliability & Operations)
**Date:** 2026-11-18
**Repository:** `/home/samertts/workspace/projects/gula-integration` (branch `integration/gula-unification-v1`)
**Toolchain:** `/tmp/opencode/mpi-venv/bin/python` (CPython 3.12.13, pytest 9.1.1, ruff 0.16.10, mypy 2.4.1)

---

## 1. Scope and compliance statement

This workstream prepared and tested **isolated, in-memory reliability designs** — real working
code with executable tests, not documentation. No production activation of any kind was performed.

| Constraint | Status |
|---|---|
| `GOVERNANCE/FINAL_DECISION.md` remains **HOLD**; MPI remains **REJECT** | Confirmed unchanged (read-only) |
| Did not modify MPI files, `FINAL_DECISION.md`, `integration/`, other workstream packages, or other governance reports | Confirmed — write operations only to the three exclusive paths in §2 |
| No DDL, migrations, schema changes, production DB access, real patient data or secrets | Confirmed — stdlib + existing `app.health_core.common` only; no DB/network/filesystem calls in the new package |
| No `factory.py`, `main.py`, routers, routes or feature flags touched | Confirmed |
| No new third-party dependency | Confirmed — `json`, `hashlib`, `dataclasses`, `enum`, `time`, `math`, `re`, `typing`, `collections.abc` only |
| No commit, push, merge, rebase, PR, deploy, `git add`, `git reset`, `git clean` | Confirmed — none executed |
| No skipped/xfail tests, placeholders, empty dataclasses, fake success returns or weakened assertions | Confirmed |
| All identifiers synthetic `SYN-` values | Confirmed — keys, events, subjects, nodes, artifacts, effects, letters and ledgers use `SYN-` prefixes; `require_synthetic_id` fails closed |
| `/home/samertts/workspace/projects/gula-platform` byte-untouched | Confirmed — `git status --porcelain` count **0** at start and at end of this workstream |

Context read: `GOVERNANCE/ACCELERATION/ACCELERATED_EXECUTION_REPORT.md` §10 (all blockers owner-gated;
persistence requires a separate owner-approved Migration Proposal; HOLD and REJECT stand) and
`GOVERNANCE/ACCELERATION/WS_D_APP_INTEGRATION_REPORT.md` §6 (in-memory outbox has no durability;
conflict resolution records decisions and audit but does not merge clinical content).

---

## 2. Exact files created

All files are new and inside the exclusive write ownership set (no other path was written).

**Production source — `backend/app/health_core/reliability/` (11 files, 1 630 LOC):**

| File | LOC | Purpose |
|---|---:|---|
| `__init__.py` | 145 | Public export surface |
| `errors.py` | 57 | Structured `ReliabilityError` hierarchy (`code`, `status_code`, `retryable`, `details`) |
| `hashing.py` | 86 | Canonical JSON, SHA-256, checksummed envelope decode, synthetic/text validators |
| `durable.py` | 296 | `DurableStore` Protocol, `InMemoryWALStore`, WAL records, atomic snapshots, restart recovery |
| `audit.py` | 198 | SHA-256 hash-chained append-only `AuditLog`, `verify_chain`, reason-coded verification |
| `backup.py` | 125 | Checksummed backup artifact + metadata, verified restore into a fresh store |
| `idempotency.py` | 113 | `IdempotentProcessor` keyed by synthetic idempotency key, structured 409 conflict |
| `retry.py` | 147 | Jitter-free bounded exponential backoff, dead-letter queue, deterministic outcomes |
| `metrics.py` | 100 | Numeric-only counters/gauges/timers with snapshot + JSON export |
| `sync_conflicts.py` | 225 | Isolated offline-sync conflict dispositions with one chained audit record per candidate |
| `performance.py` | 138 | Honest measured in-memory enqueue/replay harness, percentiles, injectable clock for statistics tests |

**Tests — `backend/tests/health_core/` (6 new files, 762 LOC, 50 tests):**

| File | Tests | Area |
|---|---:|---|
| `test_reliability_durable.py` | 9 | WAL, snapshots, restart, corruption rejection |
| `test_reliability_audit.py` | 9 | Mutation, deletion, reordering, digest/PII, synthetic IDs |
| `test_reliability_backup_idempotency.py` | 9 | Backup checksum/equality, negative cases, idempotent replay/conflict |
| `test_reliability_conflicts.py` | 9 | Four conflict policies, full accounting, tamper detection, determinism |
| `test_reliability_performance.py` | 4 | Measured harness, statistics derivation, injected clock, invalid inputs |
| `test_reliability_retry_metrics.py` | 10 | Backoff, success-after-N, DLQ, metrics correctness/PII |
| **Total** | **50** | All passing |

**Report:** `GOVERNANCE/PRODUCTION_READINESS/WS_F_RELIABILITY_REPORT.md` (this file).

---

## 3. Area-by-area verification

| # | Requirement | Status | Evidence (module → tests) |
|---|---|---|---|
| 1 | Durable persistence: `DurableStore` Protocol + in-memory WAL, atomic snapshot, load/restore, restart survival | **VERIFIED (isolated scope)** | `durable.py` → `test_wal_writes_visible_before_commit_and_recovered_by_simulated_restart`, `test_commit_is_atomic_snapshot_and_clears_wal`, `test_restore_from_snapshot_and_wal_replays_uncommitted_tail`, `test_delete_is_logged_and_recovered_after_restart`, `test_sequence_advances_across_restarts`, `test_corrupted_snapshot_is_rejected`, `test_corrupted_wal_bytes_are_rejected` |
| 2 | Audit integrity: SHA-256 hash-chained append-only records; detect mutation, deletion, reordering | **VERIFIED (isolated scope)** | `audit.py` → field mutation → `HASH_MISMATCH`; middle deletion → `SEQUENCE_GAP`/`BROKEN_LINK`; tail deletion → `COUNT_MISMATCH`/`HEAD_MISMATCH` with trusted head; head swap → `GENESIS_MISMATCH`; tail swap → `SEQUENCE_GAP`; genuine rewired link → `BROKEN_LINK`; payload stored only as digest (9 tests) |
| 3 | Backup/restore: bytes + checksum + metadata, restore into fresh store, checksum and data equality, corrupted backup negative test | **VERIFIED (isolated scope)** | `backup.py` → `test_backup_artifact_has_bytes_checksum_and_metadata`, `test_backup_restores_into_fresh_store_with_data_equality` (`snapshot_bytes` equality, `record_count`, `data_digest`, `assert_data_equal`), `test_corrupt_backup_payload_is_rejected`, `test_corrupt_backup_checksum_is_rejected_without_decoding_payload`, `test_backup_count_and_digest_tampering_is_detected` |
| 4 | Idempotent processing: synthetic key dedup, replay has no second effect, conflicting reuse raises structured error | **VERIFIED (isolated scope)** | `idempotency.py` → `test_identical_replay_creates_no_second_effect` (effect count stays 1), `test_conflicting_key_reuse_raises_structured_error` (code `IDEMPOTENCY_KEY_CONFLICT`, status 409, fingerprints in details), `test_distinct_keys_and_invalid_key_shapes` |
| 5 | Retry/recovery: bounded exponential backoff, jitter-free determinism, max attempts, dead-letter queue | **VERIFIED (isolated scope)** | `retry.py` → `test_backoff_is_bounded_exponential_and_jitter_free` ((2,4,8,8,0)), `test_success_after_two_retries_reports_attempts_and_delays`, `test_terminal_failure_is_dead_lettered_with_deterministic_entry` (two executors produce identical outcomes), `test_single_attempt_policy_applies_no_delay`; delays are **computed, not slept** (see §6) |
| 6 | Observability: in-memory counters/gauges/timers, snapshot/export, no PII, no external backend | **VERIFIED (isolated scope)** | `metrics.py` → `test_counters_gauges_and_timers_snapshot`, `test_metrics_reject_free_text_and_non_numeric_values`, `test_metric_export_contains_no_pii_or_free_text`; names restricted by `^[a-z][a-z0-9_]{2,63}$` and values numeric-only |
| 7 | Performance/load: honest measured harness, 1 000 synthetic events, actual numbers, loose bounds only | **VERIFIED** | `performance.py` → `test_measured_pipeline_load_1000_events` asserts 2 000 measured operations, throughput recomputed from measured `elapsed_ms`, `p50 <= p95 <= max`, finiteness and only `throughput > 1 op/s`; `test_injected_deterministic_clock_produces_exact_durations` proves the statistics are derived from duration inputs; actual numbers in §5 |
| 8 | Offline sync conflict resolution: explicit disposition for every candidate + full audit accounting | **VERIFIED (isolated scope)** | `sync_conflicts.py` → four policies (`QUARANTINE_ALL`, `FIRST_WRITER_WINS`, `HIGHEST_VERSION_WINS`, `LATEST_ARRIVAL_WINS`), one chained audit record per candidate including the winner, `assert_full_accounting`; tests cover missing disposition/audit, tampered chain, input-order determinism, invalid candidate sets. Independent design — no code copied from `integration/conflicts.py`; no clinical merge |

**Overall WS-F verdict:** all eight isolated designs implemented and verified by executable tests.
No production readiness claim is made — see §6.

---

## 4. Exact commands and results

All commands were executed from the paths shown. No flags were relaxed and no test was skipped.

### 4.1 Focused WS-F suite

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_reliability*.py -q --tb=short
```
**Result:** `collected 50 items` → **50 passed, 1 warning in 0.61 s** (exit 0).
The single warning is a pre-existing `StarletteDeprecationWarning` from `fastapi/testclient.py` on
import, unrelated to WS-F.

### 4.2 Full Health Core suite

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core -q --tb=short
```

- First run (before concurrent workstream files were added): **553 passed, 1 warning in 6.79 s** (exit 0).
- Final run (after concurrent additions by other workstreams): **4 failed, 637 passed, 1 warning in 10.90 s**.

The 4 final failures are **all in `tests/health_core/test_terminology_validators.py`**, a file owned
by another workstream (created/modified concurrently at 14:57, while WS-F files were last written
at 14:56). WS-F has no import of, or reference to, `health_core/terminology`; the focused WS-F
suite remains 50/50 green in the same working tree. Precise failing cases, reproduced with
`pytest tests/health_core/test_terminology_validators.py -q --tb=line` → **4 failed, 84 passed**:

1. `test_loinc_curated_codes_are_accepted_with_declared_version[718-7]`
2. `test_loinc_curated_codes_are_accepted_with_declared_version[777-3]`
3. `test_ucum_curated_units_are_accepted_exactly[/min]`
4. `test_ucum_format_negatives_are_invalid[mmol//L]`

Observed causes (read-only diagnosis): curated LOINC codes return `UNVERIFIED` instead of `VALID`,
`/min` returns `INVALID` instead of `VALID`, and `mmol//L` returns `UNVERIFIED` instead of `INVALID`.
These are terminology/registry expectations in another workstream's files; **WS-F did not modify
them and does not claim them as fixed**. Handoff request in §7.

### 4.3 Lint

```bash
cd /home/samertts/workspace/projects/gula-integration
/tmp/opencode/mpi-venv/bin/python -m ruff check \
  backend/app/health_core/reliability backend/tests/health_core/test_reliability*.py --no-cache
```
**Result:** `All checks passed!` (exit 0).

### 4.4 Types

```bash
cd /home/samertts/workspace/projects/gula-integration
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core/reliability
```
**Result:** `Found 2 errors in 1 file (checked 11 source files)` — both are the documented
pre-existing baseline in `backend/app/domain/order_state.py:63` and `:81`
(`no-untyped-def` on `assert_not_locked` / `assert_not_cancelled`). **Zero errors attributable to
any WS-F file.** (Initial runs also surfaced two WS-F issues — an `Any` return in backoff and an
implicit re-export in `__init__.py` — both were fixed in code, not suppressed.)

### 4.5 Isolation checks

- `git status --porcelain` in `/home/samertts/workspace/projects/gula-platform`: **0 entries** at start and end.
- No route/router/registry file modified: WS-F touched only the paths in §2.
- `test_sandbox_guards.py` (part of the full Health Core run) passed.

---

## 5. Measured performance (actual numbers, not fabricated)

**Harness:** `app.health_core.reliability.performance.run_pipeline_load(event_count)`.
For each of 1 000 synthetic events it measures one **enqueue** (idempotency record + WAL `put` +
hash-chained audit append) and one **replay** (duplicate-key resolution + store read) using
`time.perf_counter()` around each operation, giving 2 000 measured operations per run. After the
timed loop it measures `finalize_ms` for `commit` + audit verification + simulated restart and
**raises** if effect count, stored state, audit verification or restart state is wrong — a returned
measurement therefore always represents a functionally correct run. Percentiles are nearest-rank
(`ceil(fraction * n) - 1`, clamped); throughput is `operations / (elapsed_ms / 1000)`. No sleeping,
no threads, no I/O, no external broker.

**Invocation:** five independent runs in one process:

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -c \
  "from app.health_core.reliability import run_pipeline_load; ...  # 5 calls with event_count=1000"
```

Environment: CPython 3.12.13, `x86_64`, shared developer host.

| Run | Operations | Elapsed (ms) | Throughput (ops/s) | p50 (ms) | p95 (ms) | Max (ms) | Finalize (ms) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 000 | 119.401498 | 16 750.209 | 0.049400 | 0.145801 | 2.418520 | 21.399379 |
| 2 | 2 000 | 77.584248 | 25 778.429 | 0.049100 | 0.090201 | 0.452304 | 19.775166 |
| 3 | 2 000 | 71.275096 | 28 060.292 | 0.050400 | 0.069500 | 0.470304 | 19.568863 |
| 4 | 2 000 | 93.793683 | 21 323.398 | 0.055201 | 0.089801 | 1.106109 | 32.041768 |
| 5 | 2 000 | 116.436873 | 17 176.689 | 0.049200 | 0.141601 | 3.451829 | 25.198911 |
| **Median** | **2 000** | **93.793683** | **21 323.398** | **0.049400** | **0.090201** | **1.106109** | **21.399379** |

The spread between runs (≈71–119 ms elapsed; max-latency outliers to 3.45 ms) is reported rather
than smoothed away: this is a shared, noisy developer host. Tests assert only `throughput > 1 op/s`
plus ordering/finiteness invariants — **no SLA, no tight or flaky threshold, no fabricated number**.

---

## 6. Limitations — what an isolated in-memory design does NOT prove

1. **No production durability.** The WAL and snapshot exist only as Python objects/bytes in one
   process. A simulated restart proves deterministic recovery logic, not power-loss safety,
   `fsync`, disk failure, replication quorum, backup rotation or cross-process crash consistency.
2. **Audit trust is local.** Tampering detection assumes the trusted head/count kept in the
   `AuditLog` instance is intact. An attacker able to rewrite both the records and that head can
   forge a consistent chain. There is no signing, external anchoring, WORM storage or key management.
3. **No real backup/DR.** Artifacts are in-memory bytes with no encryption at rest, off-site copy,
   retention policy or restore drill against real infrastructure. No RPO/RTO is established.
4. **Process-local idempotency.** Dedup state is not shared across nodes or restarts unless the
   store itself is restored; no distributed exactly-once guarantee is implied.
5. **Retry delays are computed, not executed.** There is no sleeping, timeout, circuit breaker,
   concurrency control or real downstream call. Ordering under threads/processes is untested.
6. **Metrics are numeric-only process-local values.** No histogram buckets, cross-process
   aggregation, exposure endpoint, alerting or telemetry backend. PII exclusion relies on the
   enforced name regex and numeric-only values, not on a live DLP scanner.
7. **Conflict handling is disposition, not clinical resolution.** No three-way merge, clinical
   adjudication, terminology awareness or FHIR content handling — consistent with WS-D §6. A
   quarantined event must never be treated as clinically usable.
8. **Performance numbers are not a production benchmark.** They cover synthetic in-memory
   operations only, on a noisy shared host, with no real I/O, serialization to disk, network,
   concurrency or representative data volume.
9. **No activation.** `factory.py`, `main.py`, routes, CI gates and feature flags are untouched.
   `FINAL_DECISION` HOLD and MPI REJECT remain in force; this package must not be represented as a
   deployable capability.
10. **Owner-gated persistence.** ACCELERATED_EXECUTION_REPORT §10 item 7 requires a separate
    owner-approved Migration Proposal for any persistence work; none was created here.

---

## 7. Handoff requests

1. **Program Director / architecture owner:** decide whether any of these isolated designs should
   enter an owner-authorized hardening workstream. Until then, keep them unactivated and uncommitted.
2. **Migration/data owner:** no persistence design may advance without an approved Migration
   Proposal (ACCELERATED_EXECUTION_REPORT §10.7).
3. **Security owner:** review the audit trust model (head anchoring, signing, external append-only
   anchoring) before any audit design is considered for regulated use.
4. **SRE owner:** define RPO/RTO, backup encryption/retention and a real restore drill before any
   backup design is used outside the sandbox.
5. **Platform owner:** decide distributed idempotency (shared store vs broker-level dedup) and
   whether quarantine-only conflict dispositions are acceptable policy.
6. **Terminology workstream owner (read-only handoff):** the four `test_terminology_validators.py`
   failures in §4.2 are outside WS-F scope and were left untouched; please triage in your workstream.
7. **CI owner:** no CI wiring was added. Any future gate must be approved and must not mask the
   unrelated terminology failures above.

---

**End of WS-F report — no production activation, no commit, no other path modified.**
