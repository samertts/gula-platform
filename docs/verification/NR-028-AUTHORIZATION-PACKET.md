# NR-028 — Authorization Packet

**Generated:** 2026-09-25 · **Analysed from:** `fe961550` · **production_ready:** `false`

**This packet requests a decision. No migration was written.** Creating the 13 tables
below is a schema change, which `CLAUDE.md` places under _Requires human approval_.
The plan is specified to the point where it can be reviewed and authorized, and stops
there.

Companions: [`NR-003-OWNER-HANDOFF.md`](./NR-003-OWNER-HANDOFF.md) ·
[`MIGRATION_HEAD_TRUTH.md`](./MIGRATION_HEAD_TRUTH.md)

---

## STATUS UPDATE — a minimal migration already exists, and it reaches head

Found while auditing branches for this packet, **after** the analysis below was
written: `claude/p0-1-hospital-migrations` at **`efcc4b6e`** —
_fix(hospital): create the core schema the surgical checklist requires (P0-1)_ —
already implements the minimal option. It was verified here by execution, not read.

| Measurement                                        | Value                                                                              |
| -------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Branch / commit                                    | `claude/p0-1-hospital-migrations` @ **`efcc4b6e`** (builds on NR-003's `f92d4132`) |
| New revision                                       | `20260820_0003_hospital_core_schema.py`, `down_revision = 20260819_0003`           |
| Tables it creates                                  | **3** — `hospitals`, `hospital_departments`, `hospital_operation_theaters`         |
| Idempotency                                        | every create guarded by `_table_exists()`; `downgrade()` guarded too               |
| `alembic upgrade head` on a database created empty | **exit 0**                                                                         |
| Revisions executed                                 | **103**                                                                            |
| Stamp reached                                      | `20260909_0001`                                                                    |
| Physical tables                                    | 423                                                                                |
| Heads                                              | 1 (`20260909_0001`)                                                                |
| **`critical_care_infusions.verified_by`**          | **present** — `character varying`, nullable                                        |
| **`critical_care_infusions.verified_at`**          | **present** — `timestamp with time zone`, nullable                                 |

**So the canonical migration head is buildable from a fresh database on that branch,
and the two ICU columns arrive.** The ICU final proof's precondition is satisfiable
there. It was **not attempted** — this handoff brief rules it out explicitly.

### What this changes, and what it does not

- The decision is no longer "authorize a new migration". It is **"review and accept
  `efcc4b6e`, or require the full 13 tables first"**. The plan below stands as the
  specification of the full option.
- `efcc4b6e` makes a **second in-place modification of published history**: it
  repoints `20260820_0004.down_revision` from `20260819_0003` to `20260820_0003`. The
  commit states only that line changed, and the diff confirms it — no schema operation
  in that file was touched. That is nevertheless a second historical edit, alongside
  NR-003's, and needs the same explicit acceptance.
- **NR-028 is only partly resolved.** 10 of the 13 tables are still created by no
  migration and are still absent at head: `bed_assignments`, `hospital_beds`,
  `hospital_buildings`, `hospital_campuses`, `hospital_clinics`,
  `hospital_cost_centers`, `hospital_floors`, `hospital_medical_equipment`,
  `hospital_rooms`, `hospital_units`. The `/hospital` endpoints covering campuses,
  buildings, floors, rooms, beds, clinics, units, cost centres, equipment and bed
  assignments therefore still have no table to write to.
- Nothing was merged, cherry-picked or pushed. That branch was read in a detached
  worktree, which was removed afterwards.

---

## ROOT CAUSE

The hospital domain has a complete ORM — 14 mapped classes, a shared
`HospitalBaseEntity`, 40 registered HTTP endpoints — and **one** migration covering
one of its tables. The other 13 tables are declared in Python and exist in no
migration anywhere in the corpus.

`20260820_0004_surgical_safety_checklists.py` creates the 14th,
`hospital_surgical_safety_checklists`, with:

```python
sa.ForeignKeyConstraint(
    ["operation_theater_id"],
    ["hospital_operation_theaters.id"],
    ondelete="CASCADE",
)
```

`hospital_operation_theaters` is one of the 13. PostgreSQL therefore raises inside
the revision:

```
psycopg2.errors.UndefinedTable: relation "hospital_operation_theaters" does not exist
```

The domain was built ORM-first and never received migrations. The defect stayed
invisible because it was **masked** by NR-003: `20260815_0023` aborted five revisions
earlier, so no upgrade ever reached `20260820_0004`. Repairing NR-003 on its owner
branch is what exposed this.

Why it was not caught by tests: `backend/tests/conftest.py:28` hard-assigns
`DATABASE_URL = "sqlite:///:memory:"` and line 147 builds the schema with
`create_all` from the ORM. On that database the 13 tables always exist, because the
ORM is the source. ORM↔migration drift cannot be observed there **by construction**.

---

## AFFECTED TABLES

All 13 share `HospitalBaseEntity`, and all 13 carry `lab_id`, `version` and
`is_deleted` — tenant scope, optimistic lock, soft delete. None is created by any
migration. None is physically present on any migration-built database checked (a
`20260908_0002` build of 391 tables, a `20260819_0003` build of 410, the owner-branch
build stamped `20260815_0023`, and the failed `upgrade head` of 32 — **0 hospital
tables in every case**).

| #   | Table                                 | ORM owner (`app.hospital.models.…`) | Cols | Existing migration | Outbound FKs                                                                                                  | Inbound FKs                                                        |
| --- | ------------------------------------- | ----------------------------------- | ---- | ------------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1   | `hospitals`                           | `Hospital`                          | 22   | **none**           | —                                                                                                             | 7                                                                  |
| 2   | `hospital_campuses`                   | `Campus`                            | 15   | **none**           | `hospital_id → hospitals.id`                                                                                  | 1                                                                  |
| 3   | `hospital_cost_centers`               | `CostCenter`                        | 17   | **none**           | `hospital_id → hospitals.id`                                                                                  | 0                                                                  |
| 4   | `hospital_departments`                | `Department`                        | 17   | **none**           | `hospital_id → hospitals.id`, `parent_id → hospital_departments.id` (self)                                    | 4                                                                  |
| 5   | `hospital_units`                      | `Unit`                              | 15   | **none**           | `hospital_id → hospitals.id`                                                                                  | 0                                                                  |
| 6   | `hospital_buildings`                  | `Building`                          | 15   | **none**           | `campus_id → hospital_campuses.id`                                                                            | 1                                                                  |
| 7   | `hospital_clinics`                    | `Clinic`                            | 17   | **none**           | `hospital_id → hospitals.id`, `department_id → hospital_departments.id`                                       | 1                                                                  |
| 8   | `hospital_medical_equipment`          | `MedicalEquipment`                  | 22   | **none**           | `hospital_id → hospitals.id`, `department_id → hospital_departments.id`                                       | 0                                                                  |
| 9   | `hospital_operation_theaters`         | `OperationTheater`                  | 18   | **none**           | `hospital_id → hospitals.id`, `department_id → hospital_departments.id`                                       | **1 — `hospital_surgical_safety_checklists.operation_theater_id`** |
| 10  | `hospital_floors`                     | `Floor`                             | 15   | **none**           | `building_id → hospital_buildings.id`                                                                         | 1                                                                  |
| 11  | `hospital_rooms`                      | `Room`                              | 17   | **none**           | `floor_id → hospital_floors.id`, `department_id → hospital_departments.id`, `clinic_id → hospital_clinics.id` | 1                                                                  |
| 12  | `hospital_beds`                       | `Bed`                               | 15   | **none**           | `room_id → hospital_rooms.id`                                                                                 | 1                                                                  |
| 13  | `bed_assignments`                     | `BedAssignment`                     | 19   | **none**           | `bed_id → hospital_beds.id`                                                                                   | 0                                                                  |
| —   | `hospital_surgical_safety_checklists` | `SurgicalSafetyChecklist`           | 29   | `20260820_0004`    | `operation_theater_id → hospital_operation_theaters.id`                                                       | 0                                                                  |

**`bed_assignments` is the one to watch in review:** it is the only table in the
domain without a `hospital_` prefix, so any prefix-based search for the scope of this
work silently misses it. It is in scope.

**Total: 13 tables, 224 columns.** Of these, `efcc4b6e` covers **3** —
`hospitals`, `hospital_departments`, `hospital_operation_theaters` — leaving **10**
still created by no migration and absent at head.

### Affected modules

| Module                                         | Role                                                                              |
| ---------------------------------------------- | --------------------------------------------------------------------------------- |
| `app/hospital/models/`, `app/hospital/base.py` | the ORM declarations and `HospitalBaseEntity`                                     |
| `app/routes/hospital.py`                       | **40 endpoints** under prefix `/hospital`, registered at `app/factory.py:730-731` |
| `app/services/hospital_service.py`             | business logic                                                                    |
| `app/factory.py:180`                           | imports the models at startup                                                     |
| `app/nhdw/kpi.py`, `app/nhdw/services.py`      | warehouse reads over the domain                                                   |
| `app/national/domain/__init__.py`              | national-layer re-export                                                          |

### Affected tests

| Test                                                                                                          | Dependency                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tests/test_emergency_surgery_workflow_p0.py`                                                                 | imports `Bed`, `BedAssignment`, `OperationTheater` and `HospitalService` directly. A **P0-labelled** test that passes only because of the SQLite `create_all` database.                                           |
| `tests/migrations/test_migration_corpus_completeness.py`                                                      | pins NR-028 in `KNOWN_UNCREATED_FK_TARGETS` and pins the blocker ordering. **Expected to fail when this packet is authorized** — that is the signal to empty the baseline deliberately and re-run `upgrade head`. |
| `tests/conftest.py`                                                                                           | imports the hospital models into `_ddl_meta`                                                                                                                                                                      |
| `tests/test_ai_guardrails.py`, `test_governance.py`, `test_interop_mhd_pixm.py`, `test_national_bootstrap.py` | reference the domain indirectly                                                                                                                                                                                   |

---

## DEPENDENCY GRAPH

Derived from SQLAlchemy's own `ForeignKey` metadata, not from reading the models.

```
hospitals ─┬─> hospital_campuses ──> hospital_buildings ──> hospital_floors ─┐
           │                                                                │
           ├─> hospital_cost_centers                                        │
           ├─> hospital_units                                               ├─> hospital_rooms ──> hospital_beds ──> bed_assignments
           ├─> hospital_departments ─┬─> hospital_clinics ──────────────────┤
           │        ^     │          ├─> hospital_medical_equipment         │
           │        └─────┘ (self,   └─> hospital_operation_theaters        │
           │       parent_id)                    ^                          │
           │                                     │                          │
           └─────────────────────────────────────┼──────────────────────────┘
                                                 │
        20260820_0004: hospital_surgical_safety_checklists ──┘ (already exists; this is the FK that fails)
```

**Two properties of the graph, both material to the decision:**

1. **The graph is acyclic.** A valid creation order exists.
2. **There are zero foreign keys out of the domain.** Not one of the 13 tables
   references `labs`, `patients`, `lab_users` or anything else outside the hospital
   set. The migration is fully self-contained, which is what keeps its risk low.

### MIGRATION ORDER

Seven tiers. Tables within a tier are mutually independent and may be created in any
order within it.

| Tier | Tables                                                                                                |
| ---- | ----------------------------------------------------------------------------------------------------- |
| 1    | `hospitals`                                                                                           |
| 2    | `hospital_campuses`, `hospital_cost_centers`, `hospital_departments`, `hospital_units`                |
| 3    | `hospital_buildings`, `hospital_clinics`, `hospital_medical_equipment`, `hospital_operation_theaters` |
| 4    | `hospital_floors`                                                                                     |
| 5    | `hospital_rooms`                                                                                      |
| 6    | `hospital_beds`                                                                                       |
| 7    | `bed_assignments`                                                                                     |

`hospital_departments.parent_id` is **self-referential** and must be added as a named
`ForeignKeyConstraint` after the table exists, or declared with `use_alter=True` — not
inline, which would reference the table mid-creation.

---

## WHY CURRENT HEAD CANNOT BUILD

Executed, not argued. Two runs, each against a database created empty moments
before, PostgreSQL 16, schema from migrations alone.

| Branch                                               | Revisions run | Aborts at       | Error                                                                                |
| ---------------------------------------------------- | ------------- | --------------- | ------------------------------------------------------------------------------------ |
| `fe961550` (this branch)                             | 94            | `20260815_0023` | `DatatypeMismatch` — NR-003                                                          |
| `claude/nr-003-canonical-drug-identity` @ `dcf00fa1` | **98**        | `20260820_0004` | `UndefinedTable: relation "hospital_operation_theaters" does not exist` — **NR-028** |

So the chain is exactly two links, and with NR-003 repaired NR-028 is the **only**
remaining blocker between an empty database and head.

---

## WHY ICU IS BLOCKED

`20260820_0005_icu_infusion_independent_verification.py` adds the two columns the
high-alert infusion second-actor check writes:

```python
op.add_column("critical_care_infusions", sa.Column("verified_by", sa.String(200), nullable=True))
op.add_column("critical_care_infusions", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
```

It carries `down_revision = "20260820_0004"`. Alembic's own graph gives
`20260820_0005` 93 ancestors, including both blockers.

**So the hospital domain's missing migrations strand a patient-safety column
addition.** `POST /critical-care/infusions/{id}/verify` returns 500 with
`UndefinedColumn` on any database an operator can actually build — meaning a
high-alert infusion (norepinephrine, insulin, heparin, potassium chloride, propofol,
fentanyl, midazolam, epinephrine) **cannot be activated**, and the failed attempt
writes no receipt and no audit row (NR-024).

That ordering — not the hospital domain's own importance — is why NR-028 is P0. It is
pinned by
`test_the_icu_verification_columns_are_ordered_behind_the_known_blockers`.

---

## MINIMAL MIGRATION PLAN

**One new revision**, chaining off whatever is head at authorization time. Not
written here.

| Property                      | Specification                                                                                                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Revisions added               | exactly 1                                                                                                                                                              |
| Historical revisions modified | **0**                                                                                                                                                                  |
| Tables created                | 13, in the 7-tier order above                                                                                                                                          |
| Columns                       | 224, taken from the ORM declarations — no new column invented, no column renamed                                                                                       |
| Idempotency                   | every `create_table` guarded by `_table_exists()`, every index by `_index_exists()`, per the MANDATORY migration policy. This also closes NR-029 for the new revision. |
| Self-reference                | `hospital_departments.parent_id` added as a named constraint after creation, or `use_alter=True`                                                                       |
| Nullability                   | as declared in the ORM; no non-nullable column without a `server_default`, since the tables are new and empty this is satisfied trivially                              |
| `lab_id`                      | column only, matching the ORM — see **TENANT RISK**                                                                                                                    |
| Placement                     | `backend/migrations/versions/`, new file, new revision id                                                                                                              |

The revision must be generated with `alembic revision --autogenerate` and then
**reviewed and corrected by hand** against the tier order and the guards — not
shipped as raw autogenerate output, which orders tables alphabetically and emits
inline self-referential foreign keys.

### EXPECTED UPS/DOWNGRADE

**`upgrade()`** — creates the 13 tables in tier order 1 → 7. On a database that
already has some of them (a `create_all` test database, or a re-run after a partial
failure) every guarded step is a no-op, so the revision is resumable by re-running.

**`downgrade()`** — drops the 13 tables in **reverse** tier order, 7 → 1, so no drop
is blocked by an inbound foreign key.

A caveat the owner should note: `hospital_surgical_safety_checklists` is created by
`20260820_0004`, which is _later_. Downgrading past this new revision while that one
is still applied would leave a dangling foreign key — so this revision's
`downgrade()` is only valid from a state at or below `20260820_0004`. Alembic's own
ordering enforces that, but it is worth stating because it is the one place the two
revisions interact.

---

## DATA RISK

**None from the migration itself.** Assessed, not assumed:

- All 13 tables are **new**. There is no existing data to migrate, transform,
  backfill or discard.
- No `ALTER`, no type change, no rename, no drop of anything that exists.
- No `UPDATE` and no `DELETE` anywhere in the plan.
- The **PERMANENT DATA RULE** is satisfied by construction: nothing is deleted,
  operationally or otherwise, and all 13 tables carry `is_deleted` for
  archive-not-destroy semantics.

The one real risk is **the opposite** of data loss: today the 40 served `/hospital`
endpoints write nowhere on a real deployment. Creating the tables makes them start
persisting. That is the intent, but it means the domain's authorization and tenant
behaviour become live at the same moment — see **CLINICAL RISK**.

## FK RISK

**Low, and bounded.** The 18 foreign keys are all internal to the 13-table set plus
the one inbound key from `20260820_0004`. Zero references leave the domain, so no
other domain's table can be affected by getting this wrong.

Three specific things to get right, each with a known failure mode:

| Item                                            | Failure if wrong                                                                                                                                                                                                           |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tier order                                      | `UndefinedTable` — the same class of failure as NR-028 itself                                                                                                                                                              |
| `hospital_departments.parent_id` self-reference | `UndefinedTable` on its own table if declared inline                                                                                                                                                                       |
| `ondelete` semantics copied from the ORM        | The 18 keys declare **13 `CASCADE` and 5 `SET NULL`** — no `RESTRICT` anywhere. Each must be read from the ORM per column, never defaulted, or a delete propagates differently than the model intends. See the note below. |

### A tension the owner should see before authorizing

The ORM declares `ondelete="CASCADE"` on 13 of the 18 keys, including the whole
hierarchy beneath `hospitals`: `hospital_campuses`, `hospital_clinics`,
`hospital_cost_centers`, `hospital_departments`, `hospital_medical_equipment`,
`hospital_operation_theaters` and `hospital_units` all cascade from `hospitals.id`,
and `hospital_buildings → hospital_floors → hospital_rooms → hospital_beds →
bed_assignments` cascades down the physical chain.

Transcribed literally, that means **deleting one `hospitals` row physically destroys
the entire hospital's structure, down to individual bed assignments** — a database-level
cascade no application check can intercept.

This sits in tension with the **PERMANENT DATA RULE**: GULA does not operationally
delete data or business entities; it archives, deactivates, retires or supersedes.
All 13 tables already carry `is_deleted`, which is the mechanism the rule expects.

The migration is not the right place to resolve this, and this packet does **not**
propose changing the declared semantics — that would be inventing a model decision.
It is raised because authorizing the migration is the moment the cascade becomes
real, and because "the ORM says CASCADE" is a weaker reason than it looks when the
platform's own data rule says nothing should be deleted. Recorded for decision 2's
sibling: **does the hospital domain's `ondelete` semantics stand as declared?**

## TENANT RISK

**A real finding, and the one place this packet recommends going beyond a literal
ORM transcription — with the owner's decision.**

All 13 tables carry `lab_id`. **None of them has a foreign key to `labs.id`** — the
domain has zero outbound references. So tenant scope is enforced only by application
code; the database would accept a `lab_id` that belongs to no lab, and a row whose
`lab_id` was never checked.

Security invariant 1 in `CLAUDE.md` requires every patient-data query to filter by
`lab_id = current_user.lab_id`. Whether `/hospital`'s 40 endpoints actually do is
**UNKNOWN — not measured in this pass**, and it cannot be measured against a real
database until these tables exist. That is a genuine ordering problem: the tenant
audit needs the schema, and the schema is what this packet is asking to authorize.

**Decision needed:** transcribe the ORM exactly (`lab_id` as a bare column, matching
every other hospital table), or add the `labs.id` foreign key that the ORM does not
declare. Adding it is the safer schema but it is **a change to the declared model,
not a transcription of it**, so it is the owner's call and not a decision to slip into
a migration. Recommended: transcribe exactly, then run the tenant audit as a
follow-up finding with the schema in place.

## CLINICAL RISK

| Risk                          | Assessment                                                                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Of **authorizing**            | Bounded. 13 new empty tables in a self-contained domain. The clinical gain is large: it unblocks `20260820_0005` and with it the ICU high-alert infusion second-actor check.          |
| Of **not authorizing**        | **The ICU second-actor safety check stays unreachable on every buildable database.** A high-alert infusion cannot be activated; the attempt returns 500 and leaves no audit trail.    |
| Of **authorizing carelessly** | The `/hospital` surface starts persisting for the first time. Its tenant isolation and authorization are UNKNOWN, so a tenant audit must follow before the domain is used clinically. |

The clinical case for authorizing is strong. The clinical case for authorizing
**without a follow-up tenant audit** is not.

## ROLLBACK PLAN

1. `alembic downgrade -1` from the new revision — drops the 13 tables in reverse tier
   order. Safe: they are new, and on a rollback path nothing else references them.
2. If the upgrade fails part-way, **re-run it.** Every step is guarded, so the
   revision is idempotent and resumes. This is precisely what `20260820_0004` cannot
   do (NR-029), and why the guards are not optional.
3. No data restore is needed at any point, because no pre-existing data is touched.
4. Reverting the commit removes the revision file; any database that already applied
   it must be downgraded **first**, in that order.

## VERIFICATION PLAN

No step may be replaced by SQLite, by `create_all`, or by a mock.

| #   | Check                                              | Evidence level                            | Pass condition                                                                                                       |
| --- | -------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 1   | `alembic upgrade head` on a database created empty | POSTGRESQL                                | exit 0, reaches head                                                                                                 |
| 2   | Table census                                       | POSTGRESQL                                | all 13 present; `information_schema`                                                                                 |
| 3   | Column census against the ORM                      | POSTGRESQL                                | 224 columns, `missing_physical_columns()` empty for all 13                                                           |
| 4   | FK census                                          | POSTGRESQL                                | 18 internal keys plus the inbound one from `20260820_0004`, from `pg_constraint`                                     |
| 5   | Round trip                                         | POSTGRESQL                                | `downgrade -1 && upgrade head` clean — the CI migration-gate's own check                                             |
| 6   | Idempotency                                        | POSTGRESQL                                | re-running the revision on an already-upgraded database is a no-op, not `DuplicateTable`                             |
| 7   | Single head                                        | STATIC                                    | `ScriptDirectory.get_heads()` returns exactly one                                                                    |
| 8   | `critical_care_infusions`                          | POSTGRESQL                                | `verified_by` and `verified_at` present at head — the whole point                                                    |
| 9   | Corpus guards                                      | STATIC                                    | `KNOWN_UNCREATED_FK_TARGETS` emptied **deliberately**; the ordering guard now fails and is retired with its baseline |
| 10  | ICU slice                                          | REAL_HTTP_POSTGRES + CONCURRENCY_POSTGRES | the 15-test slice re-run on the canonical head; tripwires rewritten to the repaired expectations                     |
| 11  | Negative proof                                     | NEGATIVE_PROOF                            | drop `verified_by` from a disposable copy → the slice **must** fail; restore → passes                                |
| 12  | Tenant audit                                       | REAL_HTTP_POSTGRES                        | follow-up finding: do the 40 `/hospital` endpoints filter by `lab_id`? Currently UNKNOWN                             |

Checks 1–9 verify the migration. Checks 10–11 are the ICU final proof, which becomes
executable **only** after check 1 passes. Check 12 is the new obligation that
authorizing creates.

---

## CONSTRAINT COMPLIANCE

The plan was checked against each prohibition in the brief:

| Prohibited                        | Plan              | Why                                                                                                                                                        |
| --------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| historical migration modification | **not needed**    | One new revision. `20260820_0004` is untouched — it already declares the FK correctly; its target simply does not exist yet.                               |
| manual `ALTER TABLE`              | **not needed**    | Only `create_table` on new tables.                                                                                                                         |
| ORM `create_all`                  | **not needed**    | Alembic creates the tables; `create_all` is what hid the defect.                                                                                           |
| SQLite substitution               | **not needed**    | Every verification step is PostgreSQL.                                                                                                                     |
| duplicate migration               | **not needed**    | No table in the plan is created by any existing revision — established by AST over all 101 revisions and confirmed against four migration-built databases. |
| bypass of Alembic                 | **not needed**    | Standard `op.create_table` in one revision, in the normal chain.                                                                                           |
| bypass of authorization           | **not attempted** | This packet _is_ the authorization request. No migration file was written.                                                                                 |

NR-003's in-place edit is the one historical modification in the overall chain, and it
belongs to its own owner-authorized commit — **not** to this plan.

---

## REQUIRED HUMAN DECISION

Reframed by the status update: a minimal migration exists and reaches head, so the
question is which option to accept, not whether to write one.

| #   | Decision                                                                                            | Options                                                                          | Recommendation                                                                                                                                                                                                                                                                                                                                                         |
| --- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Accept `efcc4b6e`'s minimal 3-table migration, or require the full 13 first?**                    | accept minimal / require full / accept minimal **and** schedule the remaining 10 | **Accept the minimal now, and schedule the remaining 10 as a tracked follow-up.** It is verified to reach head from a fresh database, it is idempotent, and it unblocks an ICU patient-safety control today. Holding it hostage to 10 tables that block nothing clinical would keep `POST /critical-care/infusions/{id}/verify` broken for longer, for no safety gain. |
| 2   | **Does `efcc4b6e`'s repointing of `20260820_0004.down_revision` stand as an authorized exception?** | accept / reject                                                                  | Prerequisite for decision 1. It is a second in-place edit of published history, and the same reasoning that justified NR-003's applies — `20260820_0004` aborted inside itself on every clean database, so no deployed database can have recorded it. **Owner's call, not an inference.**                                                                              |
| 3   | **The remaining 10 tables: authorize, or retire the ORM models?**                                   | migrate / retire / defer                                                         | Genuinely open. 40 `/hospital` endpoints are registered and served, and most of them target the 10 absent tables — so either the schema arrives or the endpoints should stop being served. Deferring leaves served routes that cannot work, which is the condition that produced NR-028.                                                                               |
| 4   | **`lab_id` as a bare column, or with a `labs.id` foreign key?**                                     | transcribe / add FK                                                              | **Transcribe exactly**, then run the tenant audit as its own finding. `efcc4b6e` already transcribes it that way for its 3 tables. Adding an FK the ORM does not declare is a model change, not a transcription.                                                                                                                                                       |
| 5   | **Do the hospital domain's `ondelete` semantics stand as declared?**                                | stand / revise                                                                   | 13 of 18 keys are `CASCADE`, so deleting one `hospitals` row would physically destroy the hospital's whole structure — in tension with the PERMANENT DATA RULE. `efcc4b6e` transcribes `CASCADE` as declared. Revising it is a model decision, not a migration one.                                                                                                    |
| 6   | **Who owns the follow-up tenant audit of the 40 `/hospital` endpoints?**                            | —                                                                                | Required before the domain is used clinically. Currently **UNKNOWN — not measured.**                                                                                                                                                                                                                                                                                   |
| 7   | **Does the `20260815_0023` in-place correction stand as an authorized exception?**                  | accept / reject                                                                  | Prerequisite for NR-003, tracked in its own handoff.                                                                                                                                                                                                                                                                                                                   |

**Nothing proceeds until decisions 1 and 2 are recorded.**

---

## FINAL STATUS

- **NR-003** = OWNER-AUTHORIZED REPAIR AVAILABLE / NOT MERGED — `f92d4132`, verified by
  execution (94 → 98 revisions), single head preserved.
- **NR-028** = **BLOCKED — HUMAN SCHEMA AUTHORIZATION REQUIRED.** A minimal migration
  exists and is verified to reach head (`efcc4b6e`, exit 0, 103 revisions, 423 tables),
  but it is unmerged and carries a second historical edit that needs explicit
  acceptance. **10 of 13 tables remain uncovered.**
- **ICU FINAL PROOF** = BLOCKED BY MIGRATION HEAD **on this branch**. The precondition
  is satisfiable on `claude/p0-1-hospital-migrations`, where both columns exist at head.
  **Not attempted** — this brief rules it out.

No migration written here. No merge, no cherry-pick, no push, no deployment. The two
branches examined were read in detached worktrees, which were removed.
