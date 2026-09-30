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
