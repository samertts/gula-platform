# MPI PostgreSQL Concurrency & Audit Serialization Remediation Report

**Tranche:** isolated-database / source-verified / test-driven — **STOPPED AT DATABASE SAFETY GATE**.
**Repository:** `/home/samertts/workspace/projects/gula-integration` @
`integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
**Protected repository:** `/home/samertts/workspace/projects/gula-platform` @
`remediate-security-001` / `f478676b6fc375338648dde46fbf076c015a3f91` — clean, untouched.
**Release:** HOLD (`GOVERNANCE/FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552`, unchanged).
**D-020 / D-021:** `PENDING_APPROVAL`, unchanged.
**No database connection was made. No DDL, migration, schema change, API change or source-code change was made.**

Evidence-class vocabulary used below: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED`, `PARTIAL`,
`SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`.
Decision vocabulary: `OWNER_APPROVED`, `RECOMMENDED`, `NEEDS_OWNER_DECISION`,
`LEGAL_REVIEW_REQUIRED`, `SECURITY_REVIEW_REQUIRED`, `BLOCKED_BY_EXTERNAL_DEPENDENCY`.

---

## 1. Executive Summary

| Item | Result |
|---|---|
| Phase A (environment discovery) | **COMPLETE — discovery only, no connection** |
| Strict DB safety gate (7 conditions) | **FAILED** — 0 of 7 proven; 4 explicitly contradicted by evidence |
| Phases B–I (PG baseline, concurrency, serialization benchmark, performance) | **NOT RUN — `BLOCKED_BY_EXTERNAL_DEPENDENCY`** |
| Phase J (static analysis / regression) | **NOT RUN this tranche** (no source change to regress; prior tranche evidence stands) |
| Phase K (security review) | Source-level review only (`VERIFIED_IN_SOURCE`); no runtime claim |
| Phase L (documentation) | This report + 6 governance docs updated |
| Source files changed | **0** |
| Tests added / removed / weakened | **0 / 0 / 0** |
| Production mechanism selected | **NONE** — D-MPI-1 remains `NEEDS_OWNER_DECISION` |

The only reachable PostgreSQL instance is `gula-postgres`, which Docker metadata proves is
attached to the **`gula-platform_default` network** and the persistent **`pgdata` volume**, with
application superuser env keys (`POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD`). It is the
protected repository's application database, not a dedicated disposable test database. Per the
tranche's §3.2 and §15, connecting to it is forbidden; therefore **all runtime concurrency work
stopped before any connection**. No alternative endpoint was probed and no database was created.

## 2. Initial Repository State

Captured before any action; compared against the prior tranche baseline (all matched):

| Check | Value |
|---|---|
| `git rev-parse --show-toplevel` | `/home/samertts/workspace/projects/gula-integration` |
| `git branch --show-current` | `integration/gula-unification-v1` |
| `git rev-parse HEAD` | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` |
| `git status --short` count | 244 entries: 104 ` M`, 120 `??`, 20 `R ` |
| `git diff --stat` | 104 files, +2619 / −2121 |
| `git diff --cached --stat` | 20 files, +0 / −0 (renames only) |
| `git ls-files --others --exclude-standard` | 302 |
| Protected repo | clean, `remediate-security-001` / `f478676b…` |
| `GOVERNANCE/FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` (unchanged) |
| `backend/migrations/env.py` diff | `+49 / −0` pre-existing, preserved |
| `GOVERNANCE/GECS/*.md` | 11 files, unchanged |

Pre-existing user work was treated as read-only: the modified `backend/app/services/mpi/resolver.py`
(` M`, prior tranche's +81/−20), the untracked `backend/tests/test_mpi_merge_integrity.py`
(reviewer-supplied suite), and the prior new `backend/tests/test_mpi_hash_chain_integrity.py`
(11 synthetic tests) were inspected but **not edited** in this tranche.

## 3. Database Isolation Evidence

### 3.1 Discovery commands (read-only; exit 0 unless noted)

| # | Command (purpose) | Result |
|---|---|---|
| D1 | `env \| grep -iE 'postgres\|database_url\|pg(host\|port\|user)\|test.*db' \| cut -d= -f1` | **no DB-related env var names** in the tranche shell |
| D2 | `command -v docker`; `docker info --format '{{.ServerVersion}}'` | Docker CLI present; daemon 29.1.3 |
| D3 | `command -v psql pg_isready initdb pg_ctl postgres` | `psql` `/usr/bin/psql`, `pg_isready` present; **`initdb`, `pg_ctl`, `postgres` not found** (no local server binaries) |
| D4 | `ss -ltn \| grep -E ':5432\|:5433'` | no local 5432/5433 listener |
| D5 | `docker ps -a --format …` | `gula-postgres` up 30 h; `gula-redis` up; all other PG/DB containers exited |
| D6 | `docker inspect gula-postgres --format …` (no secret values printed) | see §3.2 |
| D7 | `docker volume ls` | `pgdata` (local, persistent), `posta_db_data`, `posta_redis_data`, others |
| D8 | `grep -rInE '(TEST\|test).*(POSTGRES\|DATABASE_URL…)'` across repo, values masked | no `MPI_TEST_POSTGRES_URL`; see §3.3 |
| D9 | `grep -nE 'sqlite\|DATABASE_URL\|create_engine…' backend/tests/conftest.py` | line 28 hard-forces `DATABASE_URL = "sqlite:///:memory:"` |
| D10 | local library versions (isolated interpreter) | Python 3.12.13, SQLAlchemy 2.0.51, psycopg2 2.9.12, pytest 9.1.1 |

### 3.2 `gula-postgres` metadata (secret values never read or printed)

| Attribute | Value | Safety implication |
|---|---|---|
| Image | `postgres:16-alpine` (image tag only; server version **not** queried) | PG 16 family, unverified at runtime |
| Created | `2026-07-30T09:46:14Z`; started `2026-11-16T15:15:07Z` | long-lived, not freshly disposable |
| Network | **`gula-platform_default`**, IP `172.18.0.3` | belongs to the **protected** platform compose project |
| Volume | `pgdata` → `/var/lib/postgresql/data`, rw | persistent operational data volume |
| Env keys | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `PGDATA`, `PG_MAJOR`, `PG_VERSION`, `LANG`, `PATH`, `GOSU_VERSION`, `PG_SHA256`, `DOCKER_PG_LLVM_DEPS` | application superuser account; no restricted test role |
| Labels | `{}` | no "test"/"disposable" declaration |
| Healthcheck | `null` | no test-oriented health gating |
| Published ports | `{"5432/tcp": null}` | internal-network only; reachable from host only via the platform bridge |

### 3.3 Repository-side configuration evidence (`VERIFIED_IN_SOURCE`)

- `backend/tests/conftest.py:28` sets `DATABASE_URL = "sqlite:///:memory:"` before importing the
  app; the shared engine uses `StaticPool` (line 50). The established MPI test backend is SQLite.
- `backend/tests/blood_bank/test_*postgres*.py` (7 files, e.g. `test_postgres_concurrency.py:15`)
  use `pytestmark = pytest.mark.skipif(not POSTGRES_URL, …)` with `BLOOD_BANK_POSTGRES_URL` —
  this is the repo's existing pattern for PG-gated tests, but **no MPI equivalent URL is set**.
- `.github/workflows/ci.yml:129,149` and `iam-hardening.yml:68,77-78` define ephemeral
  `POSTGRES_DB: gula_test` GitHub Actions services. These are **CI-only, not reachable from this
  session**, and provisioning a local equivalent is forbidden without separate authorization.
- `GOVERNANCE/REMEDIATION_STAGE_REPORT.md:88` mentions `172.18.0.3:5432/...` — **stale evidence**,
  explicitly not reused (§3.1 D6 still shows `172.18.0.3`, but the endpoint is the protected
  platform's DB and remains forbidden).
- `NEXT_PHASE_AUTHORIZATION_REQUEST.md:125` already records D-MPI-2
  (`BLOCKED_BY_EXTERNAL_DEPENDENCY`) for exactly this missing resource.

### 3.4 Strict gate decision

| # | Required condition | Evidence | Verdict |
|---|---|---|---|
| 1 | Dedicated to testing | member of `gula-platform_default`, persistent `pgdata` | **FAIL** |
| 2 | Not production | no declaration available; container is the app DB | **UNPROVEN** |
| 3 | Not operational | it is the protected repo's application database | **FAIL** |
| 4 | No real patient data | volume since 2026-07-30; contents not inspected (connection forbidden) | **UNPROVEN** |
| 5 | Restricted account, no other DB privileges | `POSTGRES_*` superuser bootstrap keys only | **FAIL** |
| 6 | Disposable / recreatable with explicit authorization | persistent named volume; no authorization in this tranche | **FAIL** |
| 7 | Not through application production config | it is exactly the platform app config/network | **FAIL** |

**Gate result: FAILED → STOP before any connection.** No candidate DB was tried experimentally.
No server, container, database or volume was created. No software installed.

## 4. PostgreSQL Environment Details

| Field | Value | Evidence class |
|---|---|---|
| Candidate server image | `postgres:16-alpine` | `VERIFIED_IN_SOURCE` (docker metadata only) |
| Runtime `SELECT version()` | **not obtained** | `UNVERIFIABLE` (no connection permitted) |
| SQLAlchemy | 2.0.51 (isolated interpreter) | `VERIFIED_IN_SOURCE` |
| psycopg2 | 2.9.12 (dt dec pq3 ext lo64) | `VERIFIED_IN_SOURCE` |
| Python | 3.12.13 (`/tmp/opencode/gula-py312/bin/python`) | `VERIFIED_IN_SOURCE` |
| pytest | 9.1.1 | `VERIFIED_IN_SOURCE` |
| Transaction isolation actually used | default (READ COMMITTED assumed, **not measured**) | `UNVERIFIABLE` |
| Connection pool size / dataset size | n/a — no test DB | `NOT_IMPLEMENTED` |
| `MPI_TEST_POSTGRES_URL` | absent | `VERIFIED_IN_SOURCE` |

## 5. Baseline Test Results

**No test was executed in this tranche.** The safety gate failed before Phase B; running the
SQLite suite would not constitute a PostgreSQL baseline and could be misread as one. Prior
tranche results remain valid for that tranche only and are **not** re-claimed here:

| Prior tranche evidence (reference only, not re-run) | Value |
|---|---|
| Combined MPI regression | 65 passed / 0 failed / 0 skipped, EXIT 0, 85.53s |
| Backend | SQLite (`sqlite:///:memory:`), Python 3.12.13 |
| PostgreSQL baseline | never run; `BLOCKED_BY_EXTERNAL_DEPENDENCY` |

No numbers are invented for pass rates, lock waits, throughput or deadlock counts.

## 6. Audit Serialization Options

All analysis in this section is `VERIFIED_IN_SOURCE` + design reasoning. **No benchmark was run**,
so no throughput/latency column can be populated with measured data (`TEST_VERIFIED = none`).

Source baseline: `resolver.py:110-115` `_last_audit_hash()` performs
`ORDER BY MergeAudit.id DESC LIMIT 1` with **no row lock**; `resolver.py:130-160` `_write_audit()`
computes `prev_hash` and `entry_hash` from that read and inserts one row; the caller commits.
Two concurrent transactions can therefore read the same predecessor → fork. A source precedent
for row-locking the last entry exists in `backend/app/identity/services/canonical_audit.py:133-141`
(`_last_canonical_hash()` uses `.with_for_update()` on the ordered `LIMIT 1` query).

| Criterion | Sentinel Row (`FOR UPDATE`) | Advisory Lock | SERIALIZABLE + bounded retry | Evidence |
|---|---|---|---|---|
| Correctness | sound for non-genesis chains; genesis has no row to lock | sound if key derivation is stable and lock is xact-scoped | sound with correct retry classification | design / `VERIFIED_IN_SOURCE` |
| Fork Prevention | yes when lock precedes predecessor read | yes | yes (abort + retry) | design |
| Deadlock Risk | low if single fixed row, acquired first | very low (no row lock) | low; serialization failures are aborts, not deadlocks | design |
| Throughput | serialized at one row; unmeasured | serialized on one key; unmeasured | fewer forced waits but retries cost; unmeasured | `BLOCKED` |
| Lock Wait | proportional to append time; unmeasured | bounded by xact; unmeasured | no lock wait, retry delay; unmeasured | `BLOCKED` |
| Recovery | lock released on commit/rollback | xact-scoped auto-release; session-scoped requires disciplined release | engine-driven retry on SQLSTATE 40001 | design |
| Multi-process Safety | yes (DB-enforced) | yes (DB-enforced) | yes | design |
| Operational Complexity | low | medium (key derivation, pool lifecycle) | high (retry policy, idempotency) | design |
| Schema Requirement | **none new** — add `.with_for_update()` to `_last_audit_hash` (last-row sentinel); a dedicated sentinel row would require a new row/table → `STOP` | none | none | `VERIFIED_IN_SOURCE` |
| Test Evidence | **none this tranche**; two-session `threading.Barrier` test required | none; key-collision + crash tests required | none; SQLSTATE 40001 retry tests required | `BLOCKED` |

Notes:
- Sentinel-row on the **last existing row** needs no DDL, matching the source precedent in
  `canonical_audit.py`; it does not cover the genesis (empty-table) case, which needs either a
  fixed sentinel row (**new table/row → STOP, requires owner decision**) or an advisory lock.
- Advisory locks must be **transaction-level** (`pg_advisory_xact_lock`), not session-level, to
  avoid leaks across pooled connections. A poorly derived key can cause uncontrolled collisions.
- SERIALIZABLE must only retry SQLSTATE `40001` / `40P01` with a **bounded, idempotent** policy;
  a failed SQLAlchemy Session/Transaction must not be reused.
- No mechanism was implemented; selecting one is D-MPI-1 (`NEEDS_OWNER_DECISION`).

## 7. Selected Strategy and Justification

**No production strategy selected.** Per §5 of the tranche brief, selection requires source
reading **+ benchmark + concurrent tests + comparison + confirmation that no unapproved schema is
needed**. Three of those five inputs are unavailable (`BLOCKED_BY_EXTERNAL_DEPENDENCY`).
Recommendation only (not approved): start with the **last-row `FOR UPDATE` sentinel** because it
reuses an existing table and an existing in-repo precedent (`canonical_audit.py:139`), with an
explicit owner decision for the genesis case. Classification: `RECOMMENDED`, **not**
`OWNER_APPROVED`. D-MPI-1 stays open.

## 8. Hash Chain Concurrency Results

| Scenario | Result | Class |
|---|---|---|
| Detection of tampering / fork / broken `prev_hash` / timestamp mismatch | prior tranche verifier `verify_merge_audit_chain()` (`resolver.py:175-207`) recomputes hashes and checks links | `TEST_VERIFIED` (prior tranche only) |
| Two concurrent appends to the same chain | **not run** — no isolated PG | `BLOCKED` |
| Multiple independent connections | not run | `BLOCKED` |
| Failure after predecessor allocation → rollback, no orphan | not run | `BLOCKED` |
| Connection drop mid-transaction | not run | `BLOCKED` |
| Idempotent replay of a successful request | source: dedup check exists at `resolver.py:477-483` but concurrency behaviour unproven | `PARTIAL` |
| DBA-privileged full-chain rewrite | out of scope; hash chain is not a defence against DBA rewrite | `NOT_IMPLEMENTED` (per brief) |

No claim of fork prevention is made.

## 9. Lost Update Results

| Item | Source finding | Runtime result |
|---|---|---|
| `secondary.version += 1` (`resolver.py:515`) | plain read-modify-write inside SAVEPOINT; no `WHERE version = :expected` guard or atomic `UPDATE … SET version = version + 1` found in the inspected path | `VERIFIED_IN_SOURCE` |
| `bump_perm_version` | prior tranche corrected signature; concurrency behaviour not tested | `PARTIAL` |
| 2 / 10 / 50 concurrent increments, rollback after increment, failure during commit | not run | `BLOCKED` / `UNVERIFIABLE` |

No claim that lost updates are absent.

## 10. Deadlock Results

| Item | Source finding | Runtime result |
|---|---|---|
| Citizen lock ordering | `resolver.py:458-463` key-ordered `SELECT … FOR UPDATE` (prior tranche P0-E5) | `TEST_VERIFIED` in source/behaviour; **not** PG-runtime-proven |
| A→B vs B→A, A→B vs A→C, A→B vs B→C, nested waits | not run | `BLOCKED` |
| SQLSTATE `40P01` handling | none found in inspected MPI path; must not be hidden or retried without bound | `NOT_IMPLEMENTED` |
| `canonical_service.merge_canonicals()` path | separate path, not inspected for locking in this tranche | `SOURCE_PRESENT` / D-MPI-6 open |

SQLite emits no `FOR UPDATE`; it is not evidence about PostgreSQL deadlocks.

## 11. Atomicity and Recovery Results

| Source finding | Class |
|---|---|
| `merge_citizens()` wraps the merge in `db.begin_nested()` SAVEPOINT with `commit()`/`rollback()` (`resolver.py:502-537`) | `VERIFIED_IN_SOURCE` |
| Post-merge consistency check is inside the SAVEPOINT before commit (docstring `resolver.py:439-440`) | `VERIFIED_IN_SOURCE` |
| Caller owns the outer commit (`_write_audit` docstring `resolver.py:129`) | `VERIFIED_IN_SOURCE` |
| Ten failure-injection points (before/after locks, after each update, during audit, at commit, post-commit) | **not run** — `BLOCKED` |
| External side effects (messages/events) atomic with DB | not inspected; **not assumed atomic** | `UNVERIFIABLE` |
| Outbox / new tables | explicitly not added | `NOT_IMPLEMENTED` |

## 12. Performance Results

**No measurements were taken; no numbers are reported.** Required workloads (2/5/10/25/50
concurrent transactions; merges/s; audit appends/s; mean lock wait; p95/p99 duration; deadlock,
serialization-failure, retry and failed-transaction counts) all remain `BLOCKED`.

Minimal isolated environment required for a future bounded benchmark (no paid services; free /
open-source / self-hosted first per repository constitution):

| Resource | Minimum proposal | Rationale |
|---|---|---|
| PostgreSQL | 16.x, local Docker container, **new dedicated network + named volume**, e.g. `mpi-pg-test` | version parity with project base image |
| Database | dedicated `mpi_test`, created only after written owner authorization | disposable, isolated |
| Account | least-privilege role with `CONNECT` on `mpi_test` only; **no superuser**, no privileges on `gula` or other DBs | gate condition 5 |
| Schema objects | synthetic tables only, created by the test harness inside `mpi_test`; no application migrations, no changes to `backend/migrations/env.py` | tests need tables; **authorization required** — see §15 |
| Sizing | 1 vCPU / 1 GB RAM / 5 GB volume; `max_connections` ≥ 60 for 50-way test; `shared_buffers` 128 MB | bounded, disposable |
| Isolation | dedicated docker network; no link to `gula-platform_default`; no published host port (use exec/sidecar); unique env var `MPI_TEST_POSTGRES_URL` | gate conditions 1/3/7 |
| Disposal | `docker rm -f <container> && docker volume rm <dedicated-volume> && docker network rm <dedicated-network>` — only on explicit authorization; verify no other consumer | gate condition 6 |
| Cost | €0 license / €0 SaaS; only local CPU/RAM/disk; no paid dependency | free-first / zero-paid-dependency policy |

## 13. Security Review

Source-level only (`VERIFIED_IN_SOURCE`); no runtime or production claim.

| Concern | Status |
|---|---|
| Authorization before merge | prior tranche source checks preserved; not re-verified at runtime |
| Tenant / organization isolation, IDOR, privilege escalation | not exercised this tranche; no expansion of privileges |
| Audit tampering / replay | verifier detects tampering; replay under concurrency unproven (`PARTIAL`) |
| Concurrent permission changes / TOCTOU (`_last_audit_hash` read before insert) | `VERIFIED_IN_SOURCE` gap; no mitigation implemented |
| PII in logs | no National ID / patient data logged; discovery commands printed env **keys only** and masked URL credentials |
| Unsafe exception messages | not exercised (no tests run) |
| Connection-pool leakage / transaction leakage | not exercised; advisory-lock lifecycle risk documented in §6 |
| Lock exhaustion / unbounded waits / unbounded retry loops | no unbounded retry implemented; benchmark not run |
| Test accounts | no account used; no production/operational credentials read |

## 14. Implemented Changes

**None in application source.** This tranche produced documentation only:

| File | Change |
|---|---|
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_POSTGRESQL_CONCURRENCY_REMEDIATION_REPORT.md` | **new** — this 18-section report |
| `IMPLEMENTATION_BACKLOG.md`, `IMPLEMENTATION_PROGRESS.md`, `DEPENDENCY_GRAPH.md`, `CHANGE_RISK_REGISTER.md`, `ACCEPTANCE_EVIDENCE.md`, `NEXT_PHASE_AUTHORIZATION_REQUEST.md` | appended tranche-status sections |

No test was added, deleted, skipped or weakened. No dormancy changed, no router/engine activated,
no migration/DDL/schema/API change, no commit/push/merge/PR/deploy.

## 15. Exact Test Evidence

| # | Exact command | Exit | Evidence | DB backend |
|---|---|---|---|---|
| 1 | `git rev-parse --show-toplevel && git branch --show-current && git rev-parse HEAD && git status --short` | 0 | §2 inventory | none |
| 2 | `md5sum GOVERNANCE/FINAL_DECISION.md` | 0 | `effdfeaf…` | none |
| 3 | `env \| grep -iE … \| cut -d= -f1 \| sort -u` | 0 | no DB env names | none |
| 4 | `docker info --format '{{.ServerVersion}}'` | 0 | `29.1.3` | none |
| 5 | `command -v psql pg_isready initdb pg_ctl postgres` | 0 | no local server binaries | none |
| 6 | `ss -ltn \| grep -E ':5432\|:5433'` | 1 (no match) | no local listener | none |
| 7 | `docker ps -a --format …` | 0 | §3.1 D5 inventory | none |
| 8 | `docker inspect gula-postgres --format …` (values for secret keys omitted) | 0 | §3.2 metadata | none |
| 9 | `docker volume ls` / `docker network ls` | 0 | `pgdata`, `gula-platform_default` | none |
| 10 | repo grep for test PG env names (credentials masked) | 0 | §3.3 | none |
| 11 | `grep -nE … backend/tests/conftest.py` | 0 | SQLite fixture | none |
| 12 | `/tmp/opencode/gula-py312/bin/python -c 'import sys,sqlalchemy,psycopg2…'` | 0 | Python 3.12.13 / SQLAlchemy 2.0.51 / psycopg2 2.9.12 | none |

`pytest`, Ruff and MyPy were **not run this tranche**: no source file was modified, so there is no
new code to regress; prior tranche results (§5) are not re-claimed. No `RUNTIME_VERIFIED`,
`E2E_VERIFIED` or `PRODUCTION_VERIFIED` evidence exists. **Open authorization question:** even
after a dedicated DB is approved, creating synthetic tables requires test-only DDL inside that
dedicated DB; the tranche brief forbids DDL, so written authorization must explicitly cover this
or the concurrency proof remains `BLOCKED`.

## 16. Remaining Risks

| ID | Risk | Class | Approval |
|---|---|---|---|
| R-PG-1 | Audit fork under concurrent appends is unproven and unprevented | `BLOCKED` | `NEEDS_OWNER_DECISION` (D-MPI-1) |
| R-PG-2 | No isolated test DB → no deadlock/lock/atomicity proof | `BLOCKED` | `BLOCKED_BY_EXTERNAL_DEPENDENCY` (D-MPI-2) |
| R-PG-3 | Temptation to use `gula-postgres` (protected operational DB) | **MITIGATED by STOP** | never connect — mandatory |
| R-PG-4 | Genesis-chain gap in last-row sentinel option | `PARTIAL` design | `NEEDS_OWNER_DECISION` |
| R-PG-5 | Session-scoped advisory locks leaking across pool | design risk | `SECURITY_REVIEW_REQUIRED` if chosen |
| R-PG-6 | SERIALIZABLE retry must be bounded and idempotent | design risk | `SECURITY_REVIEW_REQUIRED` if chosen |
| R-PG-7 | `version += 1` read-modify-write lost update | `VERIFIED_IN_SOURCE`, unproven runtime | `NEEDS_OWNER_DECISION` |
| R-PG-8 | Synthetic-table DDL inside dedicated test DB needs explicit authorization | `BLOCKED` | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| R-PG-9 | DBA can rewrite an entire hash chain | out of scope | documented non-claim |

## 17. Owner Decisions

| # | Decision requested | Classification |
|---|---|---|
| D-MPI-1 | Select audit-append serialization mechanism (unchanged from prior tranche) | `NEEDS_OWNER_DECISION` |
| D-MPI-2 | Authorize and provision dedicated disposable PG test DB, dedicated network/volume, least-privilege role, and synthetic-table DDL inside that DB | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| D-MPI-2a | Decide genesis-chain handling if last-row sentinel is chosen (dedicated sentinel row ⇒ **schema change, requires new authorization** vs advisory lock) | `NEEDS_OWNER_DECISION` |
| D-MPI-6 | Extend key-ordered locking/verification to `canonical_service.merge_canonicals()` | `NEEDS_OWNER_DECISION` |
| D-MPI-7 | Docstring-only EN-DASH cleanup in pre-modified `resolver.py:13` | `RECOMMENDED` (not granted) |
| — | Confirm HOLD / D-020 / D-021 unchanged; no release decision this tranche | `OWNER_APPROVED` (existing state) |

## 18. Next Phase Recommendation

**STOP now.** Do not start another phase. Recommended next tranche (only after explicit owner
authorization): (1) provision the isolated PG environment in §12 with written authorization
covering synthetic-table DDL; (2) run Phase B baseline with two independent sessions; (3) execute
Phases D–F with `threading.Barrier` determinism and bounded timeouts; (4) benchmark the three
serialization options before selecting one; (5) implement at most one mechanism, with a matching
test, only if it needs no schema/API change. Until then: **0 PRODUCTION_VERIFIED,
0 RUNTIME_VERIFIED, 0 E2E_VERIFIED, RPO/RTO UNMEASURED, F-085 OPEN, OCR/NFC L0, ID Scan
`needs_confirmation`, D-020/D-021 `PENDING_APPROVAL`, Release HOLD.**

**Governing principle:** no single merge may corrupt a patient's identity or mix their medical
record with another patient's. Data safety precedes performance and release speed.

---

**Post-report update — environment provisioned (no runtime work performed):**
`MPI_ISOLATED_POSTGRES_PROVISIONING_REPORT.md` records that the D-MPI-2 infrastructure was
subsequently authorized and created: dedicated `gula-mpi-pg-test` / `gula-mpi-test-network` /
`gula-mpi-test-data`, DB `mpi_test`, non-superuser `mpi_test_user`, PostgreSQL 16.14, loopback-only
`127.0.0.1:55432`, out-of-repo 0600 `MPI_TEST_POSTGRES_URL`. `PROVISIONING_STATUS: PASS`,
`ISOLATION_STATUS: VERIFIED`. **No table, test, benchmark or serialization choice followed.**
All blocked/UNVERIFIED results in §§5–12 of this report still stand; only the infrastructure
precondition changed. HOLD unchanged.

**Post-report update — concurrency evaluation executed (2026-11-18):**
`MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md` records the separately authorized evaluation against
isolated `mpi_test` (schema `mpi_concurrency_test`, synthetic fixtures only): **65 passed / 0 failed /
0 skipped, EXIT 0, 87.61 s**; `DATABASE_IDENTITY: VERIFIED`, PostgreSQL 16.14. The source-level
findings in §§3–6 are now additionally **TEST_VERIFIED**: the unlocked tail read forks under
concurrency (50/20/10/5 fork groups at 2/5/10/20 workers), naive RMW loses 1/4/9/19 increments,
and opposite-order locking deadlocks (`40P01`). Sentinel-row (A) and transaction-advisory (B)
locking were fork-safe including genesis; SERIALIZABLE (C) was **not guaranteed** (rare genesis
fork reproduced despite correct full-transaction retry); atomic SQL (D) prevents lost updates only.
**No strategy was selected, approved or implemented**; `SOURCE_FILES_CHANGED: 0`,
`APPLICATION_MIGRATIONS_CREATED: 0`, `GIT_OPERATIONS: NONE`. HOLD `effdfeaf…`, D-020/D-021
`PENDING_APPROVAL`, D-MPI-1 `NEEDS_OWNER_DECISION`. **STOP.**

**Post-analysis pointer (read-only, 2026-11-18):** this report's source-level options A–E were
carried into four `PROPOSED — NOT APPROVED` decision-preparation artifacts:
`MPI_SERIALIZATION_ARCHITECTURE_DECISION.md` (recommendation E = transaction-advisory B + atomic-SQL
D + existing ascending row locks, no schema change; SERIALIZABLE C comparison-only),
`MPI_IMPLEMENTATION_EXECUTION_PLAN.md`, `MPI_FAILURE_RECOVERY_MATRIX.md`,
`MPI_CROSS_COMPONENT_IMPACT.md`. No decision, source, migration or Git state changed.
