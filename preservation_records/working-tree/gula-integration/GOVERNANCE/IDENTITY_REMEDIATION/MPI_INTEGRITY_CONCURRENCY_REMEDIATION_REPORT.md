# MPI Integrity & Concurrency Remediation Report

> **Tranche:** bounded, uncommitted, source-verified / test-driven. Release decision remains
> **HOLD** (`GOVERNANCE/FINAL_DECISION.md`, md5 `effdfeaf10234678d83b2668c4489552`, unchanged).
> D-020 and D-021 remain `PENDING_APPROVAL`. No NHID model, no MPI Unmerge, no cross-domain
> reference change, no API contract change, no migration/DDL, no commit, no deployment.
> Paths are inside `gula-integration` @ `integration/gula-unification-v1`, HEAD
> `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`. All fixtures are synthetic.

---

## 1. Executive Summary

| Question | Answer | Status |
|---|---|---|
| Can MPI lose a patient record? | No loss path found in the merge flow; `IdentityClaim` rows are re-pointed with provenance and verified inside a SAVEPOINT. Cross-domain records are a **separate, unresolved** inventory. | `PARTIAL` |
| Can MPI merge mismatched records? | Self, cycle, already-merged and ineligible sources are rejected in source and now tested. Probabilistic false-match policy is unchanged. | `TEST_VERIFIED` (bounded) |
| Can MPI corrupt the audit hash chain? | **Yes, pre-fix**: the hashed `occurred_at` was not the persisted value, so no stored row could reproduce its own hash. Fixed; chain verifier added. Fork-under-concurrency remains open. | `PARTIAL` |
| Can a retried request double-merge? | No — original audit row is returned. Tested. | `TEST_VERIFIED` |
| Can concurrent merges deadlock? | A→B / B→A opposite-order lock window existed between the two citizen locks. Fixed by one key-ordered `SELECT … FOR UPDATE`. **Not runtime-proven on PostgreSQL here.** | `SOURCE_PRESENT` (fix), `BLOCKED` (runtime proof) |
| Can concurrent audit appends fork the chain? | **Yes** — unlocked tail read. Detection added; serialization is an open design decision. | `BLOCKED` |
| Can a partial failure be committed? | No within the tested paths: SAVEPOINT rollback verified for audit failure; pre-commit verification checks claims, secondary state and canonical chain. | `TEST_VERIFIED` (SQLite scope) |
| Are clinical references preserved? | Only `IdentityClaim` is re-pointed. ~90 other FK/soft references are untouched by design; inventory revalidated, no repointing performed. | `VERIFIED_IN_SOURCE` |

**Implemented:** 4 source corrections in `backend/app/services/mpi/resolver.py` (pre-modified file,
isolated edits only) + 11 new synthetic tests in a new file. **No file outside MPI service + new
tests was touched by code changes.** Governance docs updated separately.

**STOP conditions triggered (parts stopped, not bypassed):**
1. No dedicated disposable PostgreSQL test database is provisioned → runtime concurrency proof
   `BLOCKED_BY_EXTERNAL_DEPENDENCY`. The only reachable PG (`172.18.0.3:5432`, shared, tables
   already present) was probed **read-only** and was not written to.
2. Closing the audit-append fork requires choosing a serialization mechanism (stable sentinel row
   lock vs `pg_advisory_xact_lock` vs SERIALIZABLE + bounded retry) → `NEEDS_OWNER_DECISION`;
   only the proposed design is documented, nothing implemented.
3. Cross-domain reference ownership/jurisdiction policy is absent → `NEEDS_OWNER_DECISION`;
   inventory only.

---

## 2. Initial State

Recorded before any edit (exact commands executed from the target repo root):

| Item | Value |
|---|---|
| `pwd` | `/home/samertts/workspace/projects/gula-integration` |
| `git rev-parse --show-toplevel` | `/home/samertts/workspace/projects/gula-integration` |
| `git branch --show-current` | `integration/gula-unification-v1` |
| `git rev-parse HEAD` | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` |
| `git status --short` count | **243** entries (104 ` M`, 119 `??`, 20 `R ` staged renames, 0 deleted) |
| `git diff --stat` | 104 files changed, 2533 insertions(+), 2114 deletions(-) |
| `git diff --cached --stat` | 20 files, 0 insertions / 0 deletions (renames) |
| Protected repo | `gula-platform`, branch `remediate-security-001`, HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, **0** status entries |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` |
| D-020 / D-021 | `PENDING_APPROVAL` |
| GECS historical files | 11 `.md` files present, unchanged |
| `backend/migrations/env.py` | pre-existing user diff `+49 / -0`, unchanged |
| Interpreter | `/tmp/opencode/gula-py312/bin/python` = Python **3.12.13**, pytest 9.1.1, SQLAlchemy 2.0.51, FastAPI 0.139.2, webauthn 3.0.0 |
| Ruff | 0.15.21 |

MPI file status at start (important for isolation):

| File | Status | Interpretation |
|---|---|---|
| `backend/app/services/mpi/resolver.py` | ` M` (unstaged, +81/−20 vs HEAD) | **pre-existing user work** (P0-E merge integrity) — minimal targeted edits only |
| `backend/tests/test_mpi_merge_integrity.py` | `??` (untracked, 168 lines, 6 tests) | pre-existing user work — not modified |
| other 7 MPI `.py` modules | clean | read-only |
| new test file (this tranche) | `??` | `backend/tests/test_mpi_hash_chain_integrity.py` |

**Baseline test run before edits:** `test_mpi_merge_integrity.py` + `test_mpi_matcher.py` →
**41 passed / 0 failed / 0 skipped, EXIT 0, 81.16s**, 1 warning (Starlette/httpx deprecation).

---

## 3. Source Findings

Full execution trace (manual merge), verified in source:

```
POST /mpi/merge (api.py:142-176, require_role master/ministry admin)
 → MergeRequest validation (schemas.py:56-59, ULID length 26, reason 10-500)
 → service validation (resolver.py:446-451 in the edited file)
 → ONE key-ordered SELECT … FOR UPDATE of both citizens (resolver.py:459-469)
 → idempotency / cycle / status eligibility (resolver.py:472-497)
 → IdentityClaim query (resolver.py:499)
 → SAVEPOINT (resolver.py:501)
 → claim repoint + provenance, secondary state, version bump (resolver.py:503-512)
 → _write_audit: prev_hash read, canonical JSON, SHA-256, db.add + flush (resolver.py:514-525)
 → db.flush + 3 post-merge assertions (resolver.py:527-534)
 → savepoint.commit / rollback+raise (resolver.py:535-537)
 → caller db.commit() in the route (api.py:168)
 → response built from audit fields (api.py:170-176) — NO post-commit verification
```

| ID | Finding | Source location | Severity | Disposition |
|---|---|---|---|---|
| F1 | Hashed `occurred_at` was `datetime.now(UTC).isoformat()` while the persisted column used the ORM default (a second `datetime.now(UTC)` call). Stored rows could not reproduce their own `entry_hash`. | `resolver.py:122`/`:127-137` (pre-edit), `models.py:183` | **CRITICAL** | `TEST_VERIFIED` — fixed |
| F2 | No `MergeAudit` chain verifier existed despite `models.py:155` claiming tamper detection. The only "chain" test was an algorithm replica in `test_mpi_matcher.py:251-306` that omits `default=str` and never reads a stored row. | full-tree grep; `models.py:151-156` | **HIGH** | `TEST_VERIFIED` — fixed (detection only) |
| F3 | `_last_audit_hash()` reads the tail with an unlocked `SELECT … ORDER BY id DESC LIMIT 1`; concurrent appenders can share a `prev_hash`. `entry_hash UNIQUE` does not stop it because the payloads differ. | `resolver.py:93-98`, `:113` (pre-edit) | **HIGH** | `BLOCKED` — design decision required |
| F4 | Docstring claimed post-merge verification rolls back the *whole* operation; verification is pre-commit inside a SAVEPOINT, and the caller owns the outer commit. No post-commit verification exists. | `resolver.py:371-372` (pre-edit), `api.py:168-176` | **HIGH** | `VERIFIED_IN_SOURCE` — docstring corrected; no new behaviour claimed |
| F5 | Tests use SQLite; `with_for_update()` is emitted as no SQL by the SQLite dialect, so row locking/deadlocks are untestable in this harness. | `conftest.py:28,92-98,154-180` | **HIGH** | `BLOCKED` — see §14 |
| F6 | Review confirm/reject docstrings claim hash-chained audit rows; only `create` and `manual_merge` event types are written. | `api.py:241-244,254-258,275-295`; `models.py:167` | MEDIUM | `NEEDS_OWNER_DECISION` — new event taxonomy is a policy decision; not changed |
| F7 | Claim query, post-check and `secondary.version += 1` are unlocked; no optimistic CAS. | `resolver.py:422,436,450` (pre-edit) | MEDIUM | `PARTIAL` — covered by the two-row ordered lock, residual documented |
| F8 | Two separate locks in argument order (primary then secondary) → A→B / B→A opposite acquisition order. | `resolver.py:385,388` (pre-edit) | MEDIUM | `TEST_VERIFIED` (source + behaviour) — fixed |
| F9 | `resolve_identity` idempotency pre-check is unlocked; concurrent first-time calls can both pass and one fails with uncaught `IntegrityError`. | `resolver.py:183-188,339`; `models.py:124` | MEDIUM | `NEEDS_OWNER_DECISION` — not changed (out of bounded scope) |
| F10 | `RuntimeError` from post-merge verification is not translated by the route; no MPI-local commit-failure handling. | `api.py:166-168`; `database.py:284-298` | MEDIUM | `NEEDS_OWNER_DECISION` — adding status codes changes API contract; not changed |
| F11 | Matcher chain replica omits `default=str`. | `test_mpi_matcher.py:259` | MEDIUM | `PARTIAL` — new independent verifier covers persisted rows; old replica left untouched (user/test file not modified) |
| F12 | `canonical_service.merge_canonicals()` has no locks, audit, or verification; blind `version += 1`. | `canonical_service.py:104-133` | MEDIUM | `NEEDS_OWNER_DECISION` — separate merge path, not changed |
| F13 | Module docstring omits the sub-threshold-candidate branch. | `resolver.py:12-14` | INFORMATIONAL | not changed (pre-existing user file) |

---

## 4. Hash Chain Findings

| Check | Before | After | Status |
|---|---|---|---|
| `prev_hash` source | unlocked tail `SELECT` | unchanged | `BLOCKED` (F3) |
| `entry_hash` formula | `sha256(prev_hash + canonical_json(row_dict))` | unchanged (contract preserved) | `VERIFIED_IN_SOURCE` |
| Canonical serialization | `json.dumps(sort_keys=True, separators=(",", ":"), default=str)` | unchanged; shared by writer and verifier | `TEST_VERIFIED` |
| `occurred_at` hashed vs persisted | two different `datetime.now(UTC)` calls → mismatch | **one** `datetime` instance used for both; `_occurred_at_iso()` normalises naive/PG-aware values | `TEST_VERIFIED` |
| Field order | lexicographic (`sort_keys=True`) | unchanged | `VERIFIED_IN_SOURCE` |
| Timestamp round-trip | never verified | verifier normalises naive→UTC (SQLite drops tzinfo; PG preserves it) | `TEST_VERIFIED` (SQLite), `PARTIAL` (PG untested) |
| Concurrent appends | can fork | fork is now **detectable**, not prevented | `PARTIAL` |
| Verification after save | none | `verify_merge_audit_chain()` re-walks every row by `id` and checks both linkage and recomputed hash | `TEST_VERIFIED` |
| Tamper detection | claimed but absent | detects field rewrite and forked `prev_hash` | `TEST_VERIFIED` |
| Privileged full-chain rewrite | — | **explicitly not detected**; no such claim is made | `UNVERIFIABLE` by design |

**Limits of the protection:** the chain is an append-only tamper-*evident* log against ordinary
field edits and accidental forks. It does **not** resist a DBA or any actor with write access to
the whole table rewriting the chain consistently, and it does not serialise writers. No endpoint
was added for verification (that would change the API surface).

---

## 5. Lock Ordering Findings

| Aspect | Finding | Status |
|---|---|---|
| Locks used | `SELECT … FOR UPDATE` on `Citizen` only; no locks on `IdentityClaim`, `MergeAudit`, or audit tail | `VERIFIED_IN_SOURCE` |
| Order before fix | primary ULID first, secondary second → opposite order for A→B vs B→A | `VERIFIED_IN_SOURCE` |
| Order after fix | **single** `filter(citizen_ulid.in_(…)).order_by(Citizen.id.asc()).with_for_update().all()`; locks acquired by immutable PK in every path | `TEST_VERIFIED` (source + behaviour) |
| Validation after lock | idempotency, cycle and status re-checked after both rows are locked | `VERIFIED_IN_SOURCE` |
| Transaction isolation | DB default (no explicit level in MPI) — assumed READ COMMITTED on PostgreSQL | `VERIFIED_IN_SOURCE` |
| Transaction boundary | locks on outer transaction; mutation/audit in SAVEPOINT; commit in route | `VERIFIED_IN_SOURCE` |
| In-memory locks | none in MPI (`threading.Lock` elsewhere guards error counters only) | `VERIFIED_IN_SOURCE` |
| Sleep/random retries | none | `VERIFIED_IN_SOURCE` |
| Deadlock runtime proof | not possible on SQLite; no dedicated PG test DB | `BLOCKED` |

---

## 6. Concurrency Findings

| Scenario | Result | Status |
|---|---|---|
| Concurrent same pair, A→B and B→A | Opposite-order lock window removed in source; not executed with two real transactions | `SOURCE_PRESENT`; runtime `BLOCKED` |
| Concurrent overlapping pairs (A→B, B→C) | Deterministic key order covers the two locked rows; deeper `canonical()` chain reads are unlocked and may be stale under READ COMMITTED | `PARTIAL` |
| Concurrent audit appends | Fork window **remains**; now detectable by the verifier | `BLOCKED` |
| Lost updates on `version` | Blind increment remains (`secondary.version += 1`; `canonical_service` likewise) | `PARTIAL` |
| Multi-process safety | No process-local lock is used as a substitute for DB locking | `VERIFIED_IN_SOURCE` |
| PG availability | `172.18.0.3:5432` reachable, PostgreSQL 16.14, tables present — **read-only catalog probes only**; no synthetic writes performed | `BLOCKED_BY_EXTERNAL_DEPENDENCY` (no disposable test DB) |

---

## 7. Atomicity Findings

| Scenario | Evidence | Status |
|---|---|---|
| Failure before claim repoint | validation errors raised before SAVEPOINT; no mutation | `TEST_VERIFIED` |
| Failure after repoint, before audit | existing test monkeypatches `_write_audit` → SAVEPOINT rollback restores claims and secondary state | `TEST_VERIFIED` |
| Failure during hash update | same path (`_write_audit` raises before `db.add`) | `TEST_VERIFIED` |
| Failure before outer commit | verification failure raises inside SAVEPOINT → rollback; route never reaches `db.commit()` | `TEST_VERIFIED` (source + SQLite) |
| Rollback after partial failure | existing 6-test suite + new retry-after-failure test | `TEST_VERIFIED` |
| Commit failure in route | dependency `get_db()` rolls back; no MPI-local handling; not exercised | `PARTIAL` |
| Post-commit verification | none exists | `NOT_IMPLEMENTED` |

---

## 8. Idempotency Findings

| Scenario | Evidence | Status |
|---|---|---|
| Retry of same pair | returns the original `MergeAudit` row; one audit row only | `TEST_VERIFIED` |
| Retry after success | covered by the above | `TEST_VERIFIED` |
| Retry after failure | new test: failed audit → zero audit rows; restored call → exactly one audit, chain valid | `TEST_VERIFIED` |
| Self merge | `ValueError("cannot merge a citizen with itself")` | `TEST_VERIFIED` |
| Circular merge | `ValueError("citizens already resolve to the same canonical identity")` | `TEST_VERIFIED` |
| Missing citizen | new test → `ValueError("citizen not found")` | `TEST_VERIFIED` |
| Ineligible primary / linked secondary | new tests → explicit `ValueError` | `TEST_VERIFIED` |
| Resolve-claim idempotency | unique constraint exists, pre-check unlocked | `PARTIAL` (F9) |
| HTTP-level idempotency key / rate limit on merge | none; not required given state-based idempotency | `NOT_IMPLEMENTED` |

---

## 9. Cross-Domain Reference Inventory

Revalidated against `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md` §3 and live source greps. **Inventory
only — no repointing, unmerge, FK change, deletion or migration performed.**

| Domain | Table / file | Reference type | Owner | Merge behavior today | Evidence | Risk |
|---|---|---|---|---|---|---|
| MPI | `identity_claims.citizen_id` | BigInteger FK | MPI | **Repointed** in SAVEPOINT with provenance | `mpi/models.py:131`, `resolver.py:503-512` | mitigated |
| MPI | `mpi_merge_audit.primary/secondary_citizen_id` | BigInteger FK | MPI | ledger, not repointed | `mpi/models.py:169-174` | informational |
| LIMS | `test_results.citizen_id` | BigInteger FK (RESTRICT) | LIMS | not repointed | `models/test_result.py:52-57` | `NEEDS_OWNER_DECISION` |
| Canonical | `citizen_links.citizen_id` | BigInteger FK (RESTRICT) | canonical service | not repointed; `merge_canonicals` repoints a different column only | `models/canonical_patient.py:93-95`, `canonical_service.py:116-121` | `NEEDS_OWNER_DECISION` |
| National | `national_citizens` / `national_patients` | String(26) ULID, separate store | national | not repointed | `national/domain/{citizen,patient}.py` | `NEEDS_OWNER_DECISION` |
| National (9+ classes) | encounter, visit, observation, referral, consent, coverage, … | paired `patient_id`+`citizen_id` FKs | national | not repointed | `national/domain/*` | `NEEDS_OWNER_DECISION` |
| EHR | `ehr/models/*.py` (11 files) | patient/citizen FKs | EHR | not repointed | `ehr/models/*` | `NEEDS_OWNER_DECISION` |
| Pharmacy | `pharmacy/models.py` prescriptions/dispenses + plain columns | FK + soft | pharmacy | not repointed | `pharmacy/models.py:154,255,540,794-798,927-928` | `NEEDS_OWNER_DECISION` |
| Care continuum | `care_continuum/models/*` (~40 classes) | paired FKs | care continuum | not repointed | `care_continuum/models/*` | `NEEDS_OWNER_DECISION` |
| Consent | `consent.gpid`, national soft ULIDs | soft reference | consent/national | not repointed | `models/consent.py:42`, `national/.../national_id.py:9` | `NEEDS_OWNER_DECISION` |
| LIMS patients | `lab_order`, `billing`, `nursing`, `insurance`, `devices`, `trust` | Integer FKs to `patients.id` | LIMS | not repointed | see report §3c | `NEEDS_OWNER_DECISION` |
| Identity | `niam_identities.id` references | auth identity | NIAM | **must not** be repointed | `identity/models/{account,workspace,…}.py` | informational |
| Other merge stores | MDM index, `gov_merged_identities` | own merge chains | MDM/governance | not wired to MPI | `health_data/mdm/*`, `governance/models/health_number.py` | `NEEDS_OWNER_DECISION` |

Three unreconciled identity stores remain (MPI BigInteger, national ULID, health-data MDM) plus
`CanonicalPatient`. Ownership could not be proven for any reference above; each is therefore
`NEEDS_OWNER_DECISION`. No assumption was made that "has patient_id ⇒ must be repointed".

---

## 10. Implemented Changes

All code changes are uncommitted. `resolver.py` was already user-modified; each change below is a
minimal targeted edit, with no full-file rewrite and no auto-format.

| # | File | Change | Lines (post-edit) | Test |
|---|---|---|---|---|
| C1 | `backend/app/services/mpi/resolver.py` | Added `_occurred_at_iso()`; normalises naive/aware datetimes to one UTC ISO string | 93-110 | `test_hashed_timestamp_equals_persisted_timestamp` |
| C2 | same | `_write_audit()` uses one `occurred_at` instance for both hash payload and persisted column | 128-160 | above + `test_chain_verifier_accepts_a_clean_chain` |
| C3 | same | Added `ChainVerificationResult` + `verify_merge_audit_chain()`; re-walks all rows, checks `prev_hash` linkage and recomputed `entry_hash` | 166-208 | 4 verifier/tamper/fork/linearity tests |
| C4 | same | Replaced two argument-ordered `with_for_update()` reads with one key-ordered lock statement | 459-469 | `test_merge_succeeds_with_either_lock_argument_order`, `test_citizen_locks_are_taken_in_one_key_ordered_statement` |
| C5 | same | Corrected the over-claiming `merge_citizens` docstring (verification is pre-commit; caller owns commit) | 434-445 | documentation assertion via source review |
| C6 | `backend/tests/test_mpi_hash_chain_integrity.py` (new) | 11 synthetic tests: hash reproducibility, clean chain, linear chain, tamper, fork, reversed order, retry-after-failure, missing, ineligible, linked source, lock source invariant | whole file | this file |

**Not changed:** `api.py`, `models.py`, `schemas.py`, `matcher.py`, `blocking.py`,
`canonical_service.py`, `conftest.py`, `test_mpi_merge_integrity.py`, `test_mpi_matcher.py`,
`backend/migrations/*`, protected repository, any GECS or release document.

---

## 11. Test Evidence

Interpreter for all pytest runs:
`/tmp/opencode/gula-py312/bin/python` (Python 3.12.13). Workdir:
`/home/samertts/workspace/projects/gula-integration`.
Env: `ENV=test PYTHONPATH=backend:. DATABASE_URL=sqlite:///:memory:`.
DB backend: **SQLite temp-file engine from `backend/tests/conftest.py`** — not PostgreSQL.

| # | Exact command | Exit | Collected / Passed / Failed / Skipped | Warnings | Duration |
|---|---|---|---|---|---|
| 0 (baseline, pre-edit) | `… -m pytest backend/tests/test_mpi_merge_integrity.py backend/tests/test_mpi_matcher.py -q --disable-warnings` | 0 | 41 / 41 / 0 / 0 | 1 | 81.16s |
| 1 (new file, first pass) | `… -m pytest backend/tests/test_mpi_hash_chain_integrity.py -q --no-header --tb=short` | 0 | 7 / 7 / 0 / 0 | 1 | 81.74s |
| 2 (new file, final) | same command after extending to 11 tests | 0 | 11 / 11 / 0 / 0 | 1 | 82.79s |
| 3 (MPI combined) | `… -m pytest backend/tests/test_mpi_merge_integrity.py backend/tests/test_mpi_matcher.py backend/tests/test_mpi_hash_chain_integrity.py -q --no-header --tb=short` | 0 | 52 / 52 / 0 / 0 | 1 | 80.12s |
| 4 (broader regressions) | `… -m pytest backend/tests/test_citizen_relationship_workflow.py backend/tests/test_security_merge_regression_synthetic.py -q --no-header --tb=short` | 0 | 13 / 13 / 0 / 0 | 1 | 0.75s |
| **5 (final combined)** | `… -m pytest backend/tests/test_mpi_merge_integrity.py backend/tests/test_mpi_matcher.py backend/tests/test_mpi_hash_chain_integrity.py backend/tests/test_citizen_relationship_workflow.py backend/tests/test_security_merge_regression_synthetic.py -q --no-header --tb=short` | **0** | **65 / 65 / 0 / 0** | 1 | **85.53s** |

The single warning in every run is
`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`
from FastAPI's own `testclient.py` import — unrelated to MPI and present before this tranche.

Static analysis:

| Tool | Command | Exit | Result |
|---|---|---|---|
| Ruff | `ruff check backend/app/services/mpi/resolver.py backend/tests/test_mpi_hash_chain_integrity.py --output-format=concise` | 1 | 1 finding: `resolver.py:13:21 RUF002` EN DASH in the **pre-existing** module docstring (`0.70–0.90`), confirmed present at HEAD. 0 new findings. Not auto-fixed (pre-modified user file). |
| MyPy | `mypy --config-file backend/pyproject.toml --follow-imports=skip --no-pretty --no-error-summary backend/app/services/mpi/resolver.py` | 0 | clean. System `mypy` used; the isolated venv has no mypy installed. |

No test was deleted, weakened, skipped, or had its expectations changed to obtain a pass.

---

## 12. Failed / Blocked Tests

| Item | Reason | Classification | Required decision |
|---|---|---|---|
| Concurrent same-pair deadlock test (two real transactions) | SQLite drops `FOR UPDATE`; only reachable PG is shared/non-disposable and was not written to | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | provision a dedicated disposable MPI PostgreSQL test DB |
| Concurrent overlapping-pairMerge / lost-update test | same | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | same |
| Concurrent audit-fork reproduction | same | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | same |
| Full-chain-rewrite resistance test | not a property of an application-level append-only log | `UNVERIFIABLE` | accept the documented limit |
| PostgreSQL-backed chain verification after commit | no PG test run in this tranche | `PARTIAL` | same as above |
| Ruff exit 0 on `resolver.py` | pre-existing `RUF002` at HEAD | `SOURCE_PRESENT` | owner may separately approve a docstring-only cleanup |
| Review confirm/reject audit tests | event taxonomy change needs policy | `NEEDS_OWNER_DECISION` | approve new event types |

No test failed. Every fail/exit-1 above is an explicitly documented environment or pre-existing
baseline item, never a hidden test failure.

---

## 13. Security Review

| Check | Result | Status |
|---|---|---|
| Authorization before merge | `POST /mpi/merge` requires `master_admin` or `ministry_admin`; role derived from authenticated principal | `VERIFIED_IN_SOURCE` |
| Actor provenance | `decided_by_user_id=current_user.id`; no S-05-style actor forgery | `VERIFIED_IN_SOURCE` |
| Tenant / lab isolation | MPI is national by design (`models.py:11-16`); unscoped national merge is policy-level, not an exploitable gap for low-privilege callers | `NEEDS_OWNER_DECISION` |
| Resolve IDOR | `require_own_lab` + patient-in-lab check on `POST /mpi/resolve` | `VERIFIED_IN_SOURCE` |
| Review endpoints lab scoping | unscoped; province admins may adjudicate cross-province claims | `NEEDS_OWNER_DECISION` |
| PII in logs / exceptions | no logger/print in MPI; exception details sanitised (`"Invalid request"`) since prior commit `b9cc75e5` | `VERIFIED_IN_SOURCE` |
| PII in new tests/reports | synthetic fixtures only; no national ID, name or phone of a real person recorded | `TEST_VERIFIED` |
| Replay | state-based idempotency; no idempotency key or merge rate limit | `PARTIAL` |
| Privilege escalation | no request-controlled role/identity fields; demoted admins rejected via `perm_version` | `VERIFIED_IN_SOURCE` |
| Transaction leakage / incomplete rollback | SAVEPOINT rollback verified; no process-local locks; no unbounded retry | `TEST_VERIFIED` (SQLite scope) |
| Confirm/reject not hash-chained | real gap; fixing needs event-taxonomy policy decision | `NEEDS_OWNER_DECISION` |

No security permission was widened to make a test pass.

---

## 14. Database Limitations

1. **SQLite only in tests.** `conftest.py:92-98` creates a temp-file SQLite engine;
   `with_for_update()` compiles to nothing on the SQLite dialect. SAVEPOINTs work, but there is
   no row contention, blocking, or deadlock detection. All atomicity evidence is therefore
   **SQLite-scoped**, not a PostgreSQL concurrency proof.
2. **Timestamp precision.** Verifier normalises naive datetimes to UTC so SQLite and PostgreSQL
   can reproduce the same hash string. A backend that truncates microseconds would break
   verification; no such backend is in scope. PostgreSQL was not used, so this remains
   `PARTIAL`.
3. **PG probe was read-only.** `172.18.0.3:5432` answered `SELECT 1` (PostgreSQL 16.14) and the
   six relevant tables exist in database `gula`; only catalog/`SELECT 1` statements were run.
   No DDL, no migration, no synthetic insert, no `alembic` command, no production/operational
   connection was used.
4. **No dedicated disposable MPI PG test DB** is configured (no `MPI_TEST_POSTGRES_URL` or
   equivalent). Provisioning one requires an owner decision; creating databases/schemas is DDL
   and is forbidden in this tranche.

---

## 15. Remaining Risks

| Risk | Impact | Status / classification |
|---|---|---|
| Concurrent audit fork still possible | non-linear ledger; now detectable by `verify_merge_audit_chain()` but not prevented | `BLOCKED`, `NEEDS_OWNER_DECISION` |
| No PG concurrency proof | deadlock and row-lock behaviour inferred from source only | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| `resolve_identity` concurrent first-resolve | uncaught `IntegrityError` on one caller | `PARTIAL`, `NEEDS_OWNER_DECISION` |
| Blind `version` increments | lost update under concurrent writers | `PARTIAL` |
| Unlocked deeper `canonical()` chain reads | stale cycle decision under READ COMMITTED | `PARTIAL` |
| Cross-domain references (~90 sites) | clinical records keep old identity after a merge | `NEEDS_OWNER_DECISION` / `BLOCKED` |
| Review decisions not hash-chained | unattributable adjudication | `NEEDS_OWNER_DECISION` |
| `canonical_service.merge_canonicals()` unguarded | separate unguarded merge path | `NEEDS_OWNER_DECISION` |
| Pre-existing RUF002 in `resolver.py` | lint gate not green on that file | `SOURCE_PRESENT` |
| No post-commit verification / commit-failure handling | a failure after `db.commit()` is not re-checked | `NOT_IMPLEMENTED` |
| Honesty baseline | 0 PRODUCTION_VERIFIED · 0 RUNTIME_VERIFIED · 0 E2E_VERIFIED · RPO/RTO UNMEASURED · F-085 OPEN · OCR/NFC L0 · ID Scan `needs_confirmation` · D-020/D-021 pending · HOLD | preserved |

---

## 16. Owner Decisions

| # | Decision | Proposed options | Classification |
|---|---|---|---|
| D-MPI-1 | Serialize MPI audit appends | (a) stable sentinel row `SELECT … FOR UPDATE` on the first `mpi_merge_audit` row, then read the tail in a **new statement** (portable, works at READ COMMITTED once ≥1 row exists); (b) `pg_advisory_xact_lock` with a fixed key (closes genesis too, but PostgreSQL-coupled); (c) SERIALIZABLE + bounded idempotent retry on 40001 (largest behaviour change). Combine with a detected-fork handling policy. | `NEEDS_OWNER_DECISION` |
| D-MPI-2 | Dedicated disposable MPI PostgreSQL test DB | provision an isolated database + explicit `MPI_TEST_POSTGRES_URL`; then add two-session `threading.Barrier` tests for A→B/B→A and audit forks. | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| D-MPI-3 | Cross-domain reference ownership / repointing policy | per-domain owner sign-off; unmerge and historical reference-change log require schema/ADR. No repointing performed. | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` |
| D-MPI-4 | Review confirm/reject audit event taxonomy | approve new `MergeAudit.event_type` values and actor fields; then make `api.py` docstrings true. | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` |
| D-MPI-5 | `resolve_identity` concurrent-first-resolve handling | catch `IntegrityError` in a savepoint and return the winning claim; or rely on DB upsert. Needs bounded retry policy. | `NEEDS_OWNER_DECISION` |
| D-MPI-6 | `canonical_service.merge_canonicals()` hardening | apply the same key-ordered locking/audit/verification pattern; separate tranche. | `NEEDS_OWNER_DECISION` |
| D-MPI-7 | Pre-existing `RUF002` docstring cleanup | allow a one-character docstring edit on the pre-modified `resolver.py`. | `RECOMMENDED` (not granted here) |

None of these decisions is treated as approved by this report. Release decision **HOLD**,
D-020 and D-021 `PENDING_APPROVAL` remain untouched.

---

## 17. Recommended Next Phase

**Recommended next tranche (only after explicit owner authorization):**
provision D-MPI-2's disposable PG test DB; implement D-MPI-1 option (a) or (b) as selected;
add two-session concurrency tests that reproduce and then prove the A→B/B→A deadlock fix and
the audit-fork fix; extend the verifier into an operational check with an agreed fork-response
policy; then treat D-MPI-3/4/5/6 as separate owner-gated tranches.

**Not started and explicitly excluded:** NHID canonicalization, MPI Unmerge, cross-domain
reference edits, API contract changes, migrations/DDL, dormant component activation, commit,
merge, push, PR, deploy, or any release-status change.

**The session stops here.**

---

**Post-analysis pointer (read-only, 2026-11-18):** the source findings and §17 next-phase gates above
were consolidated into four `PROPOSED — NOT APPROVED` artifacts without changing any decision:
`MPI_SERIALIZATION_ARCHITECTURE_DECISION.md`, `MPI_IMPLEMENTATION_EXECUTION_PLAN.md`
(MPI-01..MPI-10, each owner-gated), `MPI_FAILURE_RECOVERY_MATRIX.md`, and
`MPI_CROSS_COMPONENT_IMPACT.md` (dominant impact: ~90 reference sites remain `NEEDS_OWNER_DECISION`,
no repointing proposed). D-MPI-1 `NEEDS_OWNER_DECISION`; HOLD, D-020/D-021 unchanged. No source,
migration, API or Git change.
