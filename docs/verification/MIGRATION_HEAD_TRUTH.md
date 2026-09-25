# Migration Head — PostgreSQL Truth Closure

**Generated:** 2026-09-25 · **Analysed from:** `6f711725` · **production_ready:** `false`

Companions: [`VERIFICATION_INTELLIGENCE_MAP.md`](./VERIFICATION_INTELLIGENCE_MAP.md) ·
[`EVIDENCE_ICU_INFUSION_VERIFY.md`](./EVIDENCE_ICU_INFUSION_VERIFY.md)

Every number here came from Alembic's own API or from PostgreSQL introspection on
a disposable database. Nothing is inferred from reading a migration.

## 1. The headline

The ICU high-alert infusion verification (NR-023) is blocked by **two** distinct
defects in series, not one.

| #   | Blocker                                                                                                  | Status                                                                                                             |
| --- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| 1   | `20260815_0023` declares foreign keys `String(26)` to an `Integer` primary key                           | **Repair exists, owner-authorised, verified working** — on `claude/nr-003-canonical-drug-identity`, not yet landed |
| 2   | `20260820_0004` references a hospital domain that **no migration creates** — 13 ORM tables, 0 migrations | **NEW — NR-028. Unrecorded before this pass.**                                                                     |

With both satisfied, `alembic upgrade head` completes and
`critical_care_infusions.verified_by` exists. **Proven, not predicted** — §6.

## 2. Migration graph reconciliation

Read through `ScriptDirectory`, not by grep.

| Property        | Value                                                                                   |
| --------------- | --------------------------------------------------------------------------------------- |
| Revisions       | **101** (`6f711725`) · **102** on the NR-003 branch                                     |
| Roots           | **1** — `20250322_0000`                                                                 |
| Heads           | **1** — `20260908_0001` (`20260909_0001` on the NR-003 branch)                          |
| Merge revisions | 4 — `20260815_0003`, `20260815_0015`, `20260819_0001`, `20260908_0001`                  |
| Branch points   | 5 — `20260814_0006`, `20260814_0011`, `20260815_0002`, `20260815_0022`, `20260819_0003` |

**There is no head divergence.** The graph is well-formed: one root, one head, no
orphans. That matters because it rules out the first candidate classification
before any repair is discussed.

### The chain from the blocker to the ICU columns

```
20260716_0003  creates pharmacy_drug_catalog.id = Integer
      │
      ▼
20260815_0022  creates pharmacy_sales, pharmacy_sale_lines
               (drug_catalog_id String(26) — but NO ForeignKey, so it succeeds)
      │
      ▼
20260815_0023  creates pharmacy_drug_substitution_rules
               original_drug_catalog_id String(26) FK -> pharmacy_drug_catalog.id (Integer)
               *** DatatypeMismatch — BLOCKER 1 ***
      │
      ▼
20260819_0001  (merge)  →  20260819_0002  →  20260819_0003
      │
      ▼
20260820_0004  creates hospital_surgical_safety_checklists
               FK -> hospital_operation_theaters, hospitals, hospital_departments
               *** UndefinedTable — BLOCKER 2 (NR-028) ***
      │
      ▼
20260820_0005  add_column verified_by, verified_at   ← what NR-023 needs
      │
      ▼
20260908_0001  (head)
```

Ancestry, computed:

- `20260716_0003` ∈ ancestors(`20260815_0023`) — **True**. So the catalog is always
  `Integer` before the FK is declared. The migration is unconditionally impossible.
- `20260815_0023` ∈ ancestors(`20260820_0005`) — **True**. This corrects an earlier
  statement of mine that the ICU columns were merely "on a branch only head
  reaches". They are **strictly downstream of blocker 1**: no ordering reaches
  `20260820_0005` without applying `20260815_0023` first.
- `20260820_0005` ∈ ancestors(`20260908_0002`) — **False**, which is why the
  391-table build used for earlier verification lacks the columns.

### The partial-commit boundary

A failed `upgrade head` does not leave a clean database. Measured: 94 of 101
revisions logged `Running upgrade`, yet `alembic_version` reads `20260505_0005`
and only **32 tables** exist.

The cause is `20260505_0006_sndhs_phase1_constraints.py`, which enters
`op.get_context().autocommit_block()` to run `CREATE UNIQUE INDEX CONCURRENTLY`.
Entering that block commits the open transaction. Everything up to and including
`20260505_0005` is therefore durable; everything after it rolls back together.
Any rollback plan has to account for this boundary — a failed upgrade is
_partially committed_, not aborted.

## 3. NR-003 classification

Ruled out by evidence, in order:

| Candidate                         | Verdict                                                           |
| --------------------------------- | ----------------------------------------------------------------- |
| Migration dependency divergence   | **NO** — one root, one head, 4 clean merges                       |
| Multiple heads                    | **NO** — `alembic heads` returns exactly one                      |
| Duplicate ownership               | **NO** for this defect (that is NR-006, a different table)        |
| FK / schema divergence            | **Proximate cause** — `DatatypeMismatch`, varchar against integer |
| Incompatible historical migration | **Root cause**                                                    |

**Classification: canonical identity divergence, surfacing as an unsatisfiable
foreign-key datatype, in a historical migration that no database can ever have
applied.**

Three sources, measured independently, disagree about one column:

| Source                                                      | `pharmacy_drug_catalog.id` |
| ----------------------------------------------------------- | -------------------------- |
| `20260716_0003` — the only migration that creates the table | **Integer**                |
| Physical database, every build checked                      | **integer**                |
| ORM `app.pharmacy.models.DrugCatalog`                       | **String(26)**             |

The whole ULID-era pharmacy branch was authored against the ORM's belief.
`20260815_0022` survived because it declared `drug_catalog_id String(26)` with
**no** foreign key — a dangling reference by type that PostgreSQL never checks.
`20260815_0023` declared the constraint and hit the wall. The near-miss is the
tell: this was written and validated against a schema built from the ORM, where
neither statement fails.

## 4. The authorised repair already exists

**No repair was invented here, and none was needed.** `claude/nr-003-canonical-drug-identity`
carries it, with the decision recorded:

| Artefact                                                     | Content                                                                                                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `f92d4132`                                                   | `fix(pharmacy): establish canonical drug identity and unblock upgrade head (NR-003)`                                                        |
| `20260909_0001_pharmacy_canonical_drug_identity.py`          | Adds `drug_id`, a server-generated immutable UUID4, as the public identity. `Integer` PK stays, internal. Guarded, fail-closed, reversible. |
| `20260815_0023`                                              | In-place correction of exactly two column types, `String(26)` → `Integer`                                                                   |
| `docs/architecture/MIGRATION_EXCEPTION_20260815_0023.md`     | **Status: GRANTED (one-off), by the project owner**                                                                                         |
| `docs/pharmacy-platform/CANONICAL_DRUG_CONTRACT.md`, ADR-006 | The frozen contract                                                                                                                         |

My independent reproduction matches that document exactly — same error, same
constraint name, same `alembic_version 20260505_0005`. The exception's reasoning
holds: the abort happens _inside_ `0023`, so a later corrective migration is
unreachable, and an earlier one would have to rewire this revision's
`down_revision` — also a modification of published history. In-place correction
is the only available repair, and the rule it excepts ("existing databases have
already run it") cannot apply to a migration no database can have run.

## 5. NR-028 — the second blocker, new

`20260820_0004_surgical_safety_checklists.py` creates
`hospital_surgical_safety_checklists` with foreign keys into the hospital domain.
**No migration in the corpus creates any of it.**

| ORM table                                                                                                                                                                                                            | Physical on any migration-built DB | Named anywhere in the migration corpus |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------- |
| `hospitals`                                                                                                                                                                                                          | no                                 | yes — only as an FK target             |
| `hospital_operation_theaters`                                                                                                                                                                                        | no                                 | yes — only as an FK target             |
| `hospital_surgical_safety_checklists`                                                                                                                                                                                | no                                 | yes — `20260820_0004` creates it       |
| `hospital_beds`, `hospital_buildings`, `hospital_campuses`, `hospital_clinics`, `hospital_cost_centers`, `hospital_departments`, `hospital_floors`, `hospital_medical_equipment`, `hospital_rooms`, `hospital_units` | no                                 | **no — absent entirely**               |

13 ORM tables, 0 migrations. Checked against three independently built
databases: a `20260908_0002` build (391 tables), a `20260819_0003` build (410
tables), and the failed `upgrade head` (32 tables). Zero `hospital*` tables in
any of them.

This is the same authoring pattern as NR-003, one step further: a migration
written against an ORM-created schema, where the referenced tables exist because
`create_all` made them. It is **not** a typo and cannot be fixed by editing
`20260820_0004`; the hospital domain needs migrations.

## 6. Executable proof that the chain is exactly two links

Run on the NR-003 branch in a git worktree — no merge into any branch.

| Step | Command                                                         | Result                                                                                                                                                                                          |
| ---- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `upgrade head`, fresh DB, NR-003 branch                         | **EXIT 1** — 98 revisions (up from 94), now fails at `20260820_0004`, `UndefinedTable: relation "hospital_operation_theaters" does not exist`. Blocker 1 is genuinely fixed; blocker 2 appears. |
| 2    | `upgrade 20260819_0003`, fresh DB                               | **EXIT 0** — 92 revisions, **410 tables**, stamped `20260819_0003`                                                                                                                              |
| 3    | Probe-create the 13 hospital tables from the ORM, in FK order   | all 13 created                                                                                                                                                                                  |
| 4    | `upgrade head`                                                  | **EXIT 1** — `DuplicateTable`: `20260820_0004` has no idempotency guard (NR-029)                                                                                                                |
| 5    | Drop only `hospital_surgical_safety_checklists`, `upgrade head` | **EXIT 0** — stamped **`20260909_0001`**, single head, **432 tables**                                                                                                                           |
| 6    | Introspect                                                      | **`verified_by character varying`, `verified_at timestamp with time zone`** — present                                                                                                           |
| 7    | `downgrade -1`                                                  | `20260909_0001 → 20260908_0001`, `drug_id` removed                                                                                                                                              |
| 8    | `upgrade head` again                                            | stamped `20260909_0001`, `drug_id` restored, both ICU columns intact, single head                                                                                                               |

### The ICU operation on that schema

`critical_care` application code is **byte-identical** between this branch and
the NR-003 branch (verified by `git rev-parse` on all four files), so the
following is evidence about the code on both.

| Scenario                                         | Result                                                                                                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Happy path                                       | **200** · `awaiting_verification → active` · `verified_by` set to the second actor · version 1→2 · 1 completed receipt · 1 audit row |
| Replay, same key and actor                       | **409** · state unchanged · still exactly 1 receipt                                                                                  |
| Initiator verifies their own infusion            | **422** "requires an independent clinical actor" · unchanged                                                                         |
| Cross-tenant                                     | **404** · row untouched                                                                                                              |
| Stale / absent `If-Match` / absent key           | **409 / 428 / 400**                                                                                                                  |
| Two different actors race one row                | exactly **[200, 409]** · version 1→2 · 2 audit rows                                                                                  |
| Same actor, same key, raced                      | exactly **[200, 409]** · exactly 1 receipt                                                                                           |
| Unauthenticated · 5 roles without `system:admin` | **401** · **403**                                                                                                                    |

**Status of this evidence.** The `critical_care` schema here was built entirely
by migrations at head, so this is stronger than the earlier "VERIFIED under
repair". But the _database_ is not purely migration-built: 12 hospital tables
were probe-created to get past NR-028. The honest label is **VERIFIED, conditional
on NR-003 landing and NR-028 being closed** — and it must not be shortened to
VERIFIED while either is open.

## 7. Drift recheck, classified

Measured on the head-built database (`20260909_0001`, 432 tables) and compared
with the `20260908_0002` build (391 tables) used for earlier evidence.

|                          | 391-table build | head build | Δ       |
| ------------------------ | --------------- | ---------- | ------- |
| Mapped ORM tables        | 781             | 780        | −1      |
| Physical tables          | 391             | **432**    | +41     |
| Mapped tables absent     | 405             | **364**    | **−41** |
| Tables with column drift | 84              | **83**     | −1      |
| Missing columns          | 692             | **691**    | −1      |

Reaching head resolves five of the six divergences that were pinned as critical:

| Table                            | 391-table build                         | head build | Classification                                    |
| -------------------------------- | --------------------------------------- | ---------- | ------------------------------------------------- |
| `critical_care_infusions`        | `verified_by`, `verified_at`            | **CLEAN**  | **MIGRATION_BLOCKED** → resolved at head          |
| `lab_users`                      | `failed_login_attempts`, `locked_until` | **CLEAN**  | **MIGRATION_BLOCKED** → resolved at head (NR-025) |
| `users`                          | same two                                | **CLEAN**  | **MIGRATION_BLOCKED** → resolved at head          |
| `service_accounts`               | `lab_id`                                | **CLEAN**  | **MIGRATION_BLOCKED** → resolved at head          |
| `clinical_lab_facility_bindings` | 2 NIAM columns                          | **CLEAN**  | **MIGRATION_BLOCKED** → resolved at head          |
| `organizations`                  | 4 columns                               | 4 columns  | **SCHEMA_DRIFT** — unresolved at head             |

Remaining drift at head, by classification:

| Classification                                                                              | Count                       | Detail                                                                                                                          |
| ------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **SCHEMA_DRIFT** — physical table exists, ORM writes columns it lacks, head does not fix it | **83 tables / 691 columns** | pharmacy 27, radiology 17, nhdw 14, nursing 13, fin 3, ecosystem 3, gov 3, and `organizations`, `national_facilities`, `niam_*` |
| **MISSING_PHYSICAL_TABLE**                                                                  | **364**                     | includes the 13 hospital tables (NR-028) and the whole `cc_*` care-continuum family                                             |
| **DUPLICATE_OWNER**                                                                         | **1**                       | `national_facilities` — two owners disagreeing by 24 columns (NR-006)                                                           |
| **MIGRATION_BLOCKED** → now resolved                                                        | 5                           | the table above                                                                                                                 |
| **INTENTIONAL**                                                                             | 0 established               | nothing in the corpus marks a divergence as deliberate; **UNKNOWN** rather than assumed                                         |
| **DORMANT**                                                                                 | 0 established               | not distinguishable from SCHEMA_DRIFT without per-domain intent, which is not mine to assert                                    |

`INTENTIONAL` and `DORMANT` are reported as **zero established, not zero
existing.** Some of the 83 are probably deliberate; deciding which needs each
domain owner, and guessing would convert UNKNOWN into a classification.

## 8. Test architecture — the two lanes

|                  | SQLite lane                                                                                             | PostgreSQL lane                                                                                                        |
| ---------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Schema source    | `Base.metadata.create_all` from the ORM                                                                 | `alembic upgrade <rev>`                                                                                                |
| Configured by    | `conftest.py`, which **hard-assigns** `DATABASE_URL = "sqlite:///:memory:"`, overriding the environment | `GULA_VERIFICATION_POSTGRES_URL`, read by `tests/verification/harness.py`                                              |
| Size / time      | 2 733 tests, 256 s                                                                                      | 25 + 7 tests, 13 s + 2 s                                                                                               |
| Can prove        | business logic, validation, route wiring, error mapping                                                 | migrations, FK enforcement, row locking, transaction and isolation behaviour, real concurrency, ORM↔database agreement |
| **Cannot** prove | anything in the right-hand column — a schema built from the ORM cannot disagree with the ORM            | —                                                                                                                      |
| Kept             | **yes, unchanged**                                                                                      | added                                                                                                                  |

Neither lane is redundant. The SQLite lane is fast and isolated and nothing here
removes or weakens it; it simply cannot see NR-003, NR-023, NR-025, NR-026 or
NR-028, all five of which are properties of what migrations build. The
PostgreSQL lane exists to see exactly those, and it skips — never passes — when
no database is configured.

## 9. Remaining blockers

| Blocker                                                                    | Owner                                   | Needs                                                                                 |
| -------------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------- |
| **NR-003** — repair authored and authorised, not landed                    | `claude/nr-003-canonical-drug-identity` | The owner lands it. Nothing further to design.                                        |
| **NR-028** — 13 hospital tables, no migrations                             | Hospital domain + Platform/Alembic      | A new migration for the domain. **Schema change → human approval. Not written here.** |
| **NR-029** — `20260820_0004` and `20260820_0005` have no idempotency guard | Platform/Alembic                        | Guards, so a partial upgrade is resumable by re-running                               |
| **NR-026** — 83 tables / 691 columns still drifting at head                | per domain                              | Per-domain reconciliation; head does not fix it                                       |
| **NR-006** — `national_facilities` dual owner                              | National + Core                         | Ownership decision                                                                    |
| NR-024, NR-019, NR-018, NR-020 remainder, NR-027                           | as recorded                             | unchanged by this pass                                                                |

## 10. What was deliberately not done

- **No migration was written.** NR-028 needs one; that is a schema change and
  needs explicit approval per `CLAUDE.md`.
- **No historical migration was modified.** The one in-place correction that
  exists was authored and authorised elsewhere, and was only read here.
- **No merge, no push, no force-push, no deployment.** The NR-003 branch was
  examined in a detached `git worktree`, which changes no branch.
- **`20260815_0023` was not duplicated.** Adding another migration to re-add the
  same columns would double-add on any database that later reaches head.
- **NR-003 was not bypassed.** Every result above was obtained with its own
  authorised repair applied, not around it.
- The 12 probe-created hospital tables exist **only** on a disposable database,
  and every claim resting on them is labelled conditional.

---

## 11. Precondition re-check for the ICU FINAL PROOF brief — 2026-09-25, `52184a75`

The ICU final-proof brief gates itself: _"execute only after the canonical
PostgreSQL migration head becomes applicable from a fresh database."_ That gate was
re-measured rather than inherited from §6, because §6 reached head only with
probe-created tables, which the brief explicitly refuses as final evidence.

### What was executed

One `alembic upgrade head` against a database created empty moments before
(`gula_precond_090016`, PostgreSQL 16, 0 tables at start), schema from migrations
alone. No manual column, no `ALTER TABLE`, no SQLite.

| Measurement                        | Value                                                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Exit code                          | `1`                                                                                                          |
| Revisions Alembic executed         | 94                                                                                                           |
| Revision that aborted              | `20260815_0023` — _Institution-scoped drug substitution rules_                                               |
| PostgreSQL error                   | `psycopg2.errors.DatatypeMismatch`                                                                           |
| Detail                             | key columns `original_drug_catalog_id` and `id` are of incompatible types: `character varying` and `integer` |
| Alembic stamp left in the database | `20260505_0005`                                                                                              |
| Tables left in the database        | 32                                                                                                           |

The stamp and the failure point are **different revisions**, and conflating them
sends a diagnostician to the wrong file. `20260505_0006` opens an
`autocommit_block` for a `CREATE INDEX CONCURRENTLY`, which commits everything open
at that moment; the 62 revisions that ran after it were rolled back together when
`20260815_0023` raised. So `20260505_0005` is a **rollback boundary**, not where the
upgrade stopped. `pharmacy_drug_catalog` is absent from the resulting database for
the same reason. `INV-DEPLOY-01` has been corrected accordingly.

### The chain, re-established from Alembic's own graph

`ScriptDirectory` reports a single head, `20260908_0001`, and for
`20260820_0005` — the revision that adds `critical_care_infusions.verified_by` and
`.verified_at` — 93 ancestors, among them **both** blockers:

| Link | Revision        | Defect                                                                                                                               | Evidence                                                             |
| ---- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| 1    | `20260815_0023` | `VARCHAR(26)` foreign key onto an `INTEGER` primary key (NR-003)                                                                     | **Executed and observed today** — `DatatypeMismatch`                 |
| 2    | `20260820_0004` | `ForeignKeyConstraint(["operation_theater_id"], ["hospital_operation_theaters.id"])`; that table is created by no migration (NR-028) | Static AST + physical absence across three migration-built databases |

`20260820_0005` carries `down_revision = "20260820_0004"`, so the two ICU columns are
ordered strictly behind NR-028. **The hospital domain's missing migrations are what
strand a patient-safety column addition** — that ordering, not the hospital domain
itself, is why NR-028 is P0.

### Verdict against the brief's own gate

**STATUS: BLOCKED.** The precondition is not satisfied, so the 18 numbered proofs
were not attempted and `VERIFIED` is not claimed for
`POST /critical-care/infusions/{id}/verify`. The prior status stands unchanged and
unshortened: **VERIFIED CONDITIONAL / VERIFIED under repair**, meaning every
invariant was demonstrated on a database that an operator cannot currently build.

Clearing the gate needs two things this pass had no authority to do: the owner lands
the authorised NR-003 repair, and someone approves a migration for the hospital
domain (a schema change under `CLAUDE.md`).

### Regression guard added

`tests/migrations/test_migration_corpus_completeness.py::test_the_icu_verification_columns_are_ordered_behind_the_known_blockers`
pins the ordering, so when either blocker clears the test fails and the recorded ICU
evidence must be re-measured instead of inherited. Its revision graph reproduces
Alembic's ancestor sets exactly (101 revisions; identical sets for `20260820_0005`
and for head), and it was negative-proofed: pinning a non-ancestor makes it fail,
restoring makes it pass.

Two defects were found and fixed in that guard while building it — it missed the 33
revisions declared as annotated assignments, and it could not follow the two merge
revisions' multiple parents. Both would have made it pass vacuously.

---

## 12. Re-analysis after the handoff packets — 2026-09-25

The three analyses the handoff brief asked to re-run, plus one classification that
changed materially.

Companions produced in this pass: [`NR-003-OWNER-HANDOFF.md`](./NR-003-OWNER-HANDOFF.md) ·
[`NR-028-AUTHORIZATION-PACKET.md`](./NR-028-AUTHORIZATION-PACKET.md)

### 12.1 Migration graph

| Tree                             | Revisions | Heads | Head            |
| -------------------------------- | --------- | ----- | --------------- |
| `fe961550` (this branch)         | 101       | 1     | `20260908_0001` |
| `dcf00fa1` (NR-003 owner branch) | 102       | 1     | `20260909_0001` |

Single head on both. The repair's new revision chains off the old head rather than
forking beside it, so no merge revision is needed.

### 12.2 Dependency analysis

Both blockers are ancestors of `20260820_0005`, which has 93 ancestors — from
Alembic's own graph, cross-checked against a file-based reader that reproduces it
exactly. The hospital domain is a 7-tier acyclic graph of 13 tables with **zero
foreign keys leaving the domain**; full per-table detail is in the authorization
packet.

### 12.3 Drift classification — on a database that can actually be built

Previous drift figures were measured on a head-built database that only existed
because tables were probe-created from the ORM. This pass instead built the
**deepest legitimately reachable** database and classified against that: the NR-003
owner branch upgraded to `20260819_0003`, the revision immediately before the NR-028
blocker.

| Measurement            | Value                                                           |
| ---------------------- | --------------------------------------------------------------- |
| Database               | created empty, then `alembic upgrade 20260819_0003`, **exit 0** |
| Revisions committed    | 92                                                              |
| Physical tables        | 410                                                             |
| Probe-created tables   | **0** — nothing was created from the ORM                        |
| Mapped tables clean    | 310                                                             |
| Mapped tables drifting | **84 / 693 columns**                                            |
| Mapped tables absent   | 386                                                             |
| Multi-owned            | `national_facilities` (unchanged — NR-006)                      |

Worst-drifting: `pharmacy_drug_catalog` 25, `national_facilities` 24,
`nursing_pressure_injury_assessments` 19, `nursing_nutrition_assessments` 18,
`pharmacy_prescription_items` 18, `radiology_reports` 17, `nhdw_admissions` 16,
`radiology_dicom_storage` 15.

#### Four pinned entries are now CLEAN, and one finding changes because of it

`test_schema_drift_guard.py` pins six critical-drift entries, measured on the
probe-assisted head build. Re-measured on this migrations-only database:

| Pinned entry                                                                | Re-classified   | Consequence                                                                 |
| --------------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------- |
| `critical_care_infusions` `{verified_by, verified_at}`                      | **still DRIFT** | NR-023 stands. The columns arrive at `20260820_0005`, which is unreachable. |
| `lab_users` `{failed_login_attempts, locked_until}`                         | **CLEAN**       | see below                                                                   |
| `users` `{failed_login_attempts, locked_until}`                             | **CLEAN**       | see below                                                                   |
| `service_accounts` `{lab_id}`                                               | **CLEAN**       | no longer a schema finding                                                  |
| `clinical_lab_facility_bindings` `{niam_facility_id, niam_organization_id}` | **CLEAN**       | no longer a schema finding                                                  |
| `organizations` `{org_id, org_type, parent_org_id, updated_at}`             | **still DRIFT** | stands                                                                      |

**NR-025 changes status.** The account-lockout columns were recorded as absent from
both `lab_users` and `users`, which made `INV-AUTHN-02` unmeasurable — the state had
nowhere to live. On a database built only by migrations to a reachable revision, both
columns **exist**. So the schema blocker on WP-004 is gone: repeated failed
authentications can now be executed against real PostgreSQL. The runtime behaviour
itself remains **UNKNOWN — not executed**, and that is the only thing still missing.

The `CLINICAL_COMMAND_ALLOWANCE` pins are confirmed exactly: `pharmacy_prescriptions`
15 columns, `radiology_orders` 7. `TOTAL_DRIFTED_TABLES = 84` also matches.

#### What was deliberately not changed

The guard's pins were **not** edited. They describe the head-built database, and head
cannot currently be built; deciding which database the guard should treat as canonical
is a real decision, not a number to quietly adjust. Four of its per-table tests would
now fail against this database — correctly, because reality moved in the _good_
direction. Retiring those pins belongs with the NR-028 authorization, when head
becomes buildable and one canonical database exists to pin against. Recorded rather
than guessed at.

### 12.4 Status after this pass

| Finding         | Status                                                                                                                                                            |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NR-003          | OWNER-AUTHORIZED REPAIR AVAILABLE / NOT MERGED — `f92d4132`, verified by execution (94 → 98 revisions), single head preserved                                     |
| NR-028          | **BLOCKED — HUMAN SCHEMA AUTHORIZATION REQUIRED.** 13 tables, 224 columns, 18 internal FKs, 7 tiers, 0 external references. Packet written; no migration written. |
| ICU final proof | BLOCKED BY MIGRATION HEAD — not attempted                                                                                                                         |
| NR-025          | schema blocker **cleared**; runtime behaviour still UNKNOWN. WP-004 is now executable.                                                                            |
| NR-026          | 84 tables / 693 columns drifting on a reachable database — measured without probe tables for the first time                                                       |
| NR-006          | unchanged — `national_facilities` still has two ORM owners disagreeing by 24 columns                                                                              |

### 12.5 Drift at canonical head — measured without probe tables for the first time

`claude/p0-1-hospital-migrations` @ `efcc4b6e` reaches head from a fresh database
(exit 0, 103 revisions, stamp `20260909_0001`, 423 physical tables, **0 probe-created
tables**). Every previous head figure in this document rested on a head build that
only existed because tables were created from the ORM. This supersedes them.

| Measurement | At head (canonical)         | At `20260819_0003` (§12.3) |
| ----------- | --------------------------- | -------------------------- |
| Clean       | 324                         | 310                        |
| Drifting    | **83 tables / 691 columns** | 84 / 693                   |
| Absent      | 373                         | 386                        |
| Multi-owned | `national_facilities`       | `national_facilities`      |

The canonical figures match the previously recorded 83 / 691 exactly, which
retrospectively validates the probe-assisted measurement — but the evidence level is
now POSTGRESQL on a database an operator can build, not a probe.

#### Five of the six pinned critical-drift entries are CLEAN at head

| Pinned entry                                                                | At canonical head                                     |
| --------------------------------------------------------------------------- | ----------------------------------------------------- |
| `critical_care_infusions` `{verified_by, verified_at}`                      | **CLEAN** — NR-023 is resolved by the migration chain |
| `lab_users` `{failed_login_attempts, locked_until}`                         | **CLEAN**                                             |
| `users` `{failed_login_attempts, locked_until}`                             | **CLEAN**                                             |
| `service_accounts` `{lab_id}`                                               | **CLEAN**                                             |
| `clinical_lab_facility_bindings` `{niam_facility_id, niam_organization_id}` | **CLEAN**                                             |
| `organizations` `{org_id, org_type, parent_org_id, updated_at}`             | **still DRIFT**                                       |

`CLINICAL_COMMAND_ALLOWANCE` holds exactly — `pharmacy_prescriptions` 15,
`radiology_orders` 7. One new entry appears: `pharmacy_drug_substitution_rules` drifts
by 2 (`fhir_id`, `fhir_resource_type`), reachable only once NR-003 creates the table.

The hospital domain at head: **10 tables still absent** — `bed_assignments`,
`hospital_beds`, `hospital_buildings`, `hospital_campuses`, `hospital_clinics`,
`hospital_cost_centers`, `hospital_floors`, `hospital_medical_equipment`,
`hospital_rooms`, `hospital_units`.

#### Consequence for the ICU evidence

`critical_care_infusions` being clean at head means the ICU final proof's precondition
is **satisfiable** — on `claude/p0-1-hospital-migrations`, not on this branch. The
proof was **not attempted**: the handoff brief rules it out, and the branch is
unmerged. `POST /critical-care/infusions/{id}/verify` therefore stays
**VERIFIED CONDITIONAL**, unshortened, until that chain lands and the slice is re-run
against it.

The drift guard's pins were still not edited, for the reason in §12.3 and now a
sharper one: the canonical database exists only on an unmerged branch. Retiring the
pins belongs with the decision that lands it.
