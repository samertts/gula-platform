# Release blockers for GULA Stable v1.0.0

A blocker leaves this list only with: a fix, a regression test, that test
passing, and the affected integration passing. No readiness percentage is given
here — the evidence below is the statement.

## Blocking, with evidence

| # | Blocker | Evidence | Owner |
|---|---|---|---|
| RB-1 | **RESOLVED on the integration lineage — see `rb1-migration-head.md`.** A fresh database reaches head on `claude/p0-2-pharmacy-reconciliation`: 112 of 112 migrations, 0 errors, final revision `20260916_0001`, 423 tables, and the `downgrade -1` / `upgrade head` round-trip passes. Two layers, both already repaired by authored commits: `f92d4132` (a `String(26)` foreign key onto an `Integer` primary key at `20260815_0023`) and `efcc4b6e` (`hospital_operation_theaters` created by no migration). **Still unresolved on `claude/autonomous-run-1`**, which lacks both. No new repair written — writing one would have duplicated existing work. | `rb1-migration-head.md`; register NR-003 / NR-043 / NR-073 | integration, not engineering |
| RB-2 | **222 of 564 ORM-mapped tables are created by no migration.** Measured against the richest reachable database with the app assembled; an upper bound with a measured ~4% false-positive rate against a 328/342 control. Four are FK targets of tables that *do* exist, and `national_encounters` and `national_practitioners` appear in no migration at all. | register NR-079 | per-domain decision |
| RB-3 | **AUDITED — see `rb3-ehr-surface-audit.md`.** All 54 served `/ehr` paths (86 operations) executed against the RB-1 proven head DB: **0 return clinical data**, 85 fail `UndefinedTable`, 1 returns a correct `403`. Classification: **53 BROKEN, 1 PARTIAL, 0 REAL, 0 STUB, 0 UNIMPLEMENTED, 0 INTENTIONALLY_EXTERNAL**. Root cause is single and unambiguous: the 18 `ehr_*` tables **and** `national_patients` are created by no migration anywhere in the chain — never authored, not failed or skipped. The router is registered unconditionally, behind no feature flag. A second, independent defect (**IA-005**) keeps 59 of 86 operations failing even once the schema exists. | `rb3-ehr-surface-audit.md`; register IA-005 / IA-006 / NR-082 | schema ownership decision (RB-2) + IA-005 **After IA-005/IA-006 remediation the classification is unchanged — 53 BROKEN, 1 PARTIAL, 0 REAL — and that is correct: IA-005 was never why the surface fails against the head database. IA-005 is RESOLVED (27 code-path recursions → 1); IA-006 stays OPEN with **zero migrations authored**, because ADR-016 (Accepted, not superseded) forbids the very tables a migration would create. See `ia005-ia006-remediation.md`. |
| RB-4 | **The generic FHIR write surface stores no clinical content, and none of its 12 advertised resource types can be inserted.** `_create_fhir_resource` copies only tenancy and audit scaffolding; 9 types have NOT NULL clinical columns it never populates and 3 resolve to no model. | register NR-085 | per-resource FHIR→ORM mapping decision |
| RB-5 | **All 15 nursing tables are unwritable**: 149 ORM columns the tables lack, 176 columns the ORM ignores, 41 type mismatches, 15 of 15 primary keys disagreeing. 66 clinical routes ship on a model that cannot write. | register NR-076 | identity + instrument decision |
| RB-6 | **CI has produced no real signal since 2026-09-24.** Jobs complete in 2-4s with `created_at == started_at`, runner_id 0, empty output and HTTP 404 on log download, across two independent workflows — an account-level Actions block. Every "green" or "red" on these PRs is uninformative. | register NR-136 (sibling lane) | GitHub billing / repo Actions settings |

RB-6 deserves emphasis for a release decision: **no claim of "tests pass in CI"
can currently be supported for this repository.** Local runs are the only
evidence, and local runs were themselves shown to be corruptible by a reclaimed
database (IA-003).

## Not blocking, but should not ship silently

* **IA-001** — `app/reference` would become a live cross-tenant read and write on
  being mounted. Tripwired.
* **IA-002** — 68 served operations taking a tenant id from the client are
  unverified. This is the largest single unmeasured security surface found.
* **NR-089** — the capability subsystem is scaffolding: 0 of 10 registered with
  the kernel, and until `203c85aa` every one reported success without doing
  anything. Now honest, still unimplemented.

## Account 2 findings ledger (not all release blockers)

| id | sev | state | one line |
|---|---|---|---|
| IA-004 | — | **SPLIT** after re-verification; migration untouched | `citizen_id` arm **CLOSED** (ALREADY_FIXED by `20260914_0001`/NR-064 → `niam_persons`, independently verified); `patient_id` arm **BLOCKED on NR-022** |
| IA-005 | P0 | **FIXED**, test + runtime verified | 17 serializers returned the `MetaData` registry for a column named `metadata`; 137 models affected |
| IA-006 | P1 | **NEEDS_DECISION** | ADR-016 forbids new EHR tables while its Phase 2 mandates EHR write support; 0 migrations authored |
| IA-007 | P3 | **FIXED** | the generated invoice number never reached the claim; unreachable today, latent data loss once `ins_*` is migrated |
| IA-008 | P1 | OPEN, methodology | this lane is 176 commits behind the lineage that built the head DB; conformance measurements here produce false positives |
| IA-009 | P1 | OPEN, awaiting owner | on the matched pair, 26 present tables are unwritable through the ORM — radiology 17/17, nhdw 14, fin 3 |
| IA-010 | P2 | **NEEDS_DECISION** | the audit chain resists modification (DB triggers) but a NULL-hash row verifies as intact; legacy rows make NULL legitimate |
| IA-013 | P1 | **CONFIRMED_DEFECT**, decision then Account 2 | the kernel event bus is wholly in-memory: `publish` never uses its own outbox, failed handlers reach no retry or DLQ, `EventStore` is unbounded — and identity lifecycle events ride it |
| IA-012 | P2 | **CONFIRMED_DEFECT**, owner Account 1 | served `GET /pharmacy/dispense/dispense-records/{patient_id}` declares `str` against an `INTEGER` column → `DataError`/500 on a ULID id, in the shipping lineage |
| national_patients | — | **BLOCKED on NR-022** | not a new decision: `20260914_0001`'s docstring already defers the clinical subject to NR-022; evidence package delivered |
| IA-011 | P2 | **NEEDS_DECISION** | two FHIR Observation builders with different contracts; no canonical `lab_results.flag` vocabulary; the unreached builder reports abnormal results as Normal |
| IA-013a | P2 | **FIXED**, test verified + negative proof | the kernel `EventStore` was an unbounded dict on a process-lifetime singleton; bounded at 10 000 with oldest-first eviction. Precondition for IA-015, not an independent tidy-up |
| IA-014 | P2 | **NEEDS_DECISION** (response shape) | `/kernel/events/outbox` and `/kernel/events/dlq` are served under `system:admin` and report the two components `publish` never writes, so both are pinned at zero for the life of the process. Also **withdraws** my earlier claim that the eight bus components are unused: two are read by these endpoints |
| IA-015 | P2 | **FIXED**, runtime + test verified, negative proof both directions | `hasattr(kernel, "event_bus")` is unsatisfiable (`Kernel` uses `_components`), so 6 national route groups — **89 served paths / 115 operations** — built and discarded a throwaway `EventBus` per request. Repaired via a canonical `resolve_event_bus()` |
| IA-016 | P1 as a trap | **NEEDS_DECISION**, deliberately not fixed | 8 further route groups — **138 served paths / 130 operations** — carry the same dead probe with a `None` fallback, and their services call `event_bus.emit(...)`, which the kernel bus does not define. Injecting a bus raises `AttributeError` on blood bank, critical care, EMS and public health. The obvious one-line fix is the regression |
| IA-017 | P2 | **NEEDS_DECISION** (retire vs. wire) | `POST /integration/offline/sync` — the platform's only served offline-sync path — is structurally incapable of a non-zero result: nothing populates the queue it drains, no edge node can be registered, and `ConflictResolver.resolve` is called **0** times in a full cycle. `get_status()` reports `"engine": "active"`. `sync_to_edge` returns `records_synced: N` while discarding the payload (latent fake-green, NR-084 pattern). The real capability is the DB-backed `/edge/*` |
| IA-018 | P2 | **NEEDS_DECISION** (canonical owner) | four classes named `OfflineSyncEngine` with four different meanings; the most sophisticated — vector clocks, LWW/CRDT, signatures, its own test file, in `app/services/` — has **zero** production importers, and carries 5 real defects (unauthenticated default "signature", non-converging conflict resolution, a `CRDT_MERGE` that is order-dependent, device-wall-clock LWW that discards the loser, `EncryptedSyncStore` storing plaintext by default) |