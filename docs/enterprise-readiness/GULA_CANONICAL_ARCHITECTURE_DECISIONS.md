# GULA Canonical Architecture Decisions

**BATCH-2 · 2026-09-10 · `production_ready: false`**

Only two kinds of entry appear here: a decision the repository's own evidence
settles, and a decision it does not. Nothing is recorded on the strength of what
would be reasonable, conventional, or clinically sensible. Where the evidence
runs out, the entry says so and names the question.

Evidence base: `GULA_CANONICAL_DISPOSITION_MATRIX.{md,json}`.

---

## 1. Canonical ownership

One owner, many consumers. Derived from foreign-key direction and from which
domain's base maps the table.

### Settled by evidence

| Entity | Canonical owner | Evidence |
|---|---|---|
| Drug / catalog | `pharmacy` | 27/27 tables physical, zero drift, `drug_id` UUID4 public identity — the finished reference implementation |
| Drug batch, prescription, dispense record, stock | `pharmacy` | reconciled in P0-2 M3/M4; settled, not reopened |
| Blood unit, component, crossmatch, transfusion | `blood_bank` | own base, own state machine, no cross-base FKs |
| Lab order, result, specimen, report | `models` (core) + `lims` | `app.models.base.Base` maps `patients`, `labs`, `lab_orders`, `lab_results`; 121/143 physical |
| Patient (lab-scoped) | `models` (core) — `patients`, physical, 22 inbound references |
| Lab user / staff | `models` (core) — `lab_users`, physical, 21 inbound references |
| Workspace, membership, session, authority | `identity` | 87/87 physical, 83 `KEEP` |
| Radiology study/report | `radiology` | 17/17 physical (drifting, hence `RECONCILE`) |
| Data-warehouse aggregates | `nhdw` | 14/14 physical |

### Decided by the platform owner (2026-09-10)

These were escalated because the repository could not settle them. They are now
settled by decision, not by evidence, and are recorded as such.

| Entity | Canonical owner | Consequence |
|---|---|---|
| **Patient** | **Core `patients`** | `national_patients` must not be an independent source of truth. It becomes a `PROJECTION` if a national read model is needed, or is retired. Its own evidence — 0 reachable operations against 51 inbound references — supports that. |
| **Facility** | **Core Facility**, for operations | A national facility directory may exist as a registry/projection where distinct national governance attributes require it. It must not become a second owner of facility identity. NR-006 resolves under this rule. |

A `PROJECTION` may be read and rebuilt. It may never be written to as a source
of truth, and no foreign key may point at it.

### Still unsettled

| Entity | Competing owners | Why the repository cannot decide |
|---|---|---|
| **Practitioner** | `national_practitioners` (58 references, unbuilt) vs core `lab_users` (21 references, physical) | The same question as Patient, and not covered by the Patient ruling. |
| **Encounter** | `national_encounters` (29 reachable operations, unbuilt) | No competing owner, but no owner has built it either. |

---

## 2. Identity classification

The Pharmacy model is the established pattern and is **not** reopened:
internal `INTEGER` primary key, immutable public `UUID4`, mutable business
`drug_code` that is never a key.

| Class | Rule | Status |
|---|---|---|
| Internal DB PK | `INTEGER`, never public | Pharmacy, identity, core: settled |
| Public ID | `UUID4`, immutable, the only identifier an API may expose | Pharmacy: settled |
| Business code | mutable, never a key, never a join target | Pharmacy `drug_code`: settled |
| External ID | identifier owned by another domain; **not** converted merely because the consumer uses integer keys | `patient_id`, `citizen_id`, `encounter_id`, `medication_dispense_id` remain `String(26)`: settled |

**Measured gap.** Every EHR table keys on `VARCHAR` — the Generation-B shape
Pharmacy was moved off. If EHR is built, it needs the same identity
reconciliation, not a copy of its current models. This is an observation from
the physical evidence, not yet a decision.

---

## 3. Tenancy scope

Derived from the presence of `lab_id` / `facility_id` / `patient_id` columns.

| Scope | Rule | Examples |
|---|---|---|
| `TENANT` | has `lab_id`; every query must filter it | pharmacy, lims, blood bank, core patients |
| `FACILITY` | has `facility_id` | parts of blood bank inventory, some EHR |
| `PATIENT` | patient-keyed, no `lab_id` | most EHR clinical records |
| `GLOBAL` | national reference data; a tenant filter would be **wrong** | clinical guidelines, `national_*` reference tables |

**A tenant filter must not be added to a `GLOBAL` entity, and must never be
missing from a `TENANT` one.** One live violation of the second half is recorded
as NR-021.

---

## 4. Decisions this batch deliberately did not make

Each would be irreversible, and none is derivable from the repository.

1. **Is `national_patients` the same entity as `patients`?** Merge, project, or
   keep both. Affects `ehr`, `care_continuum`, `nursing`, `national_data` —
   every domain whose foreign keys point at it.
2. **Who owns `national_facilities`?** Core or national. NR-006.
3. **Should the 216 `CREATE_PHYSICAL` tables be built, and in what order?**
   The matrix says they are required by reachable operations; it does not say
   the product wants those operations.
4. **Should the 39 `RETIRE` candidates be deleted?** Evidence says nothing uses
   them. Evidence cannot say nobody intends to.
5. **Which of the 10 unregistered declarative bases join `target_metadata`?**
   Registering changes what autogenerate emits — a schema decision, recorded in
   §5 of the final report with a recommendation per base.

---

## 5. Single platform contract

Checked, and holding: identity, authorization (RBAC + ABAC), the error envelope,
audit hash-chaining, the outbox event path and reference data are each
implemented once and consumed by every domain. No domain was found carrying its
own parallel implementation of any of them.

The divergence that does exist is not in the contract but beneath it: domains
disagree about which entity is canonical (§1), so they consume the same
contract against different notions of the same person.

---

# BATCH-2.5 — National Core ownership and identity

Full evidence: `GULA_NATIONAL_CORE_IDENTITY_CONTRACT.md` / `.json`.

## D-07 — Practitioner belongs to the National core

`lab_users` and `national_practitioners` are **two distinct entities**, not one
duplicated entity:

| | `lab_users` | `national_practitioners` |
|---|---|---|
| Owner | **Core** | **National** |
| Nature | authentication principal | professional registry |
| Carries | email, password hash, lockout, `perm_version` | licence, specialty, qualification, verification |
| Tenancy | `lab_id NOT NULL` | none — global |
| Key | `Integer` (physical) | `INTEGER` (to be built) |

They link through an optional nullable `lab_users.practitioner_id`. A
practitioner may have no GULA account; an account may belong to a non-clinical
user.

Decisive evidence: Core has **no** practitioner entity — the ordering clinician
is `lab_orders.doctor_name String(200)`, free text. `license_number` is
**globally** unique, which a tenant-scoped entity cannot carry. And the
repository already shows what it looks like when it means *projection*
(`national_patients.lab_patient_id`); Practitioner has no such pointer.

## D-08 — Encounter: tenant-owned canonical, national projection

`national_encounters` is a **`PROJECTION`** — read-only, rebuildable, never a
foreign-key target. `CanonicalEncounter` already implements that shape and is
the thing to extend.

The canonical transactional encounter is **tenant-scoped and clinically owned**:
`Encounter` already declares `lab_id NOT NULL`; the three production tables that
reference an encounter do so with tenant-local unconstrained strings; and the
real episode record in service today is `lab_orders`.

**BLOCKED — CLINICAL OWNER REQUIRED:** whether to extend `lab_orders` into a
general clinical encounter, or create a tenant-scoped `clinical_encounters` that
`lab_orders` references. Both fit every observation. Until it is answered, the
five legacy string columns stay exactly as they are.

## D-09 — Identity types are chosen per entity, not by blanket rule

`INTEGER` internal key for registry entities whose cardinality is bounded by
population or profession (Citizen, Practitioner, Department, Organization);
`BIGINT` for Encounter alone, because encounters are *events* whose row count
grows with time; **no new key at all** for the Patient projection; and
`String(26)` retained for `national_facilities`, which is already physical and
already the target of a physical foreign key.

Public identifiers are `UUID4` throughout and are the only identifier an API
returns. `license_number`, `facility_code`, `department_code`, `org_code` and
`national_health_number` are business codes — uniquely constrained, mutable,
never join targets.

## D-10 — NR-006 is resolved by evidence and is BATCH-3 item 1

`app/models/clinical_scope.py::NationalFacility` is authoritative: it declares
exactly the six columns migration `20260813_0004` creates and is the target of
the physical foreign key from `clinical_ehr_facility_bindings`.
`app/national/domain/facility.py::Facility` declares eighteen different columns
with zero physical backing.

This is **not a merge**. `clinical_scope.py` states in-source that the national
EHR facility is a *separate resource* from the operational facility and that no
relationship may be inferred from identifier similarity. The two are bridged by
review, through `clinical_ehr_facility_bindings`.

Resolving it unblocks NR-023, whose canonical repair — one shared `MetaData` —
is held up by exactly this one table-name collision.

---

# BATCH-2.6 — Final architecture closure

## D-11 — NR-023: the safe architecture, and why it is still BLOCKED

Three architectures were evaluated against actual SQLAlchemy/Alembic behaviour,
not against documentation.

### Option A — one canonical MetaData

Assemble a single `MetaData` at env.py time with `Table.to_metadata()`. No
declarative base changes, no application schema changes: infrastructure only.

**Measured: it works.** All 363 cross-`MetaData` foreign-key references resolve,
and `sort_tables_and_constraints` succeeds over all 651 tables — the failure
that has blocked autogenerate since it was first recorded disappears entirely.

**And it is unsafe today.** Running `compare_metadata` against a database
migrated to head produced **5,101 operations, including 76 `DROP TABLE`** —
larger than the 74-table hazard BATCH-2.5 closed. Resolving the foreign keys
does not make autogenerate safe; it makes a second, larger problem reachable.

### Option B — explicit multi-MetaData orchestration

Run autogenerate per base with the referenced tables copied in and
`include_object` restricted to the base's own tables.

**Rejected on evidence.** It does not avoid the collision — a base referencing
`national_facilities` must still choose which of the two mappings it means — and
it multiplies the exclusion surface by the number of bases, turning one
reviewable decision into eighteen. It also cannot see cross-base drift, which is
the drift most likely to hurt.

### Option C — combined MetaData with explicit, guarded resolution

Option A plus: a named collision resolution, a named exclusion list for physical
tables with no ORM model, and a fail-closed check that refuses to build the
metadata when anything appears that is not on either list.

**This is the correct target architecture.** It preserves canonical ownership
(no base changes), FK integrity (one namespace), determinism (fail closed), and
it excludes nothing silently.

### It cannot be implemented yet — three proven dependencies

| # | Dependency | Measured | Why it blocks |
|---|---|---|---|
| 1 | **NR-006** — `national_facilities` claimed by two registered metadata | 1 collision | A single namespace must pick one mapping. The naive "first wins" happens to pick the physical one by list order — correct by accident, which is not a design |
| 2 | **NR-030** — physical tables mapped by no ORM class | **12** | Each is a `DROP TABLE` candidate. Six are Financial Engine Phase A (schema-only *by design*); six are unexplained |
| 3 | **NR-029** — foreign keys naming a table that exists nowhere | **2 targets, 3 declarations** | `niam_identity_authorities`, `niam_user_sessions`. These break even a combined `MetaData` — no design resolves a reference to something that does not exist |

Dependency 1 requires an ownership decision. Dependency 3 requires a model
change. Neither is infrastructure-only, and BATCH-2.6 forbids resolving
`national_facilities` through an unapproved schema change.

### **NR-023 = BLOCKED**

The exact architectural dependency: *a single canonical `MetaData` requires one
table-name namespace (NR-006), a complete ORM registry (NR-030) and no dangling
foreign keys (NR-029). All three are proven; none is infrastructure-only.*

### What was implemented — infrastructure only

env.py now imports the fourteen model modules no other import reached. **The
DROP-TABLE hazard falls from 76 tables to 12** — an 84% reduction — and the
registry becomes truthful. Verified: `upgrade head`, `downgrade -1`,
`upgrade head` clean on a fresh database with `PYTHONPATH` unset.

This does not fix NR-023 and is not claimed to.

## D-12 — "Registered" is not "complete"

The BATCH-2.5 hazard was a base registered with **zero** tables. BATCH-2.6 found
that was the extreme end of a spectrum: `IdentityBase` was registered and held
39 tables while **48 of its own were never imported**.

The invariant is therefore not *"no registered metadata is empty"* but *"every
physical table is mapped by a registered metadata, or explicitly and namedly
excluded"*. `backend/tests/test_alembic_metadata_registry.py` asserts the
stronger form, fails closed, and reads the import graph out of env.py rather
than restating it — proven by deleting one import and watching it fail.

## D-13 — NR-006: Operational Facility vs National Facility Resource

Two entities, not one duplicated entity. **Do not merge them.**

| | Operational Facility | National Facility Resource |
|---|---|---|
| Canonical owner | **Core** | **Core** (national EHR directory) |
| Physical table | `facilities` | `national_facilities` |
| Physical mapping | `app.models` | **`app/models/clinical_scope.py::NationalFacility`** |
| Identity | `INTEGER` PK | `String(26)` PK — already physical, do not retype |
| Columns | operational | exactly the 6 from migration `20260813_0004` |
| Authoritative for | scheduling, staffing, operations, tenancy | national directory identity, `facility_code` |
| Relationship | ← `clinical_ehr_facility_bindings` → | a **reviewed** bridge, physically enforced |
| Synchronisation | none — they are different resources | registry is externally sourced; GULA does not write it back |
| Consumers | operations, authorization scope | clinical scope bridges, national reporting |

`app/models/clinical_scope.py` states in-source that the national EHR facility
is a **separate resource** from the operational facility and that no
relationship may be inferred from identifier similarity. The bridge exists
precisely because the mapping is a decision, not an inference.

**`app/national/domain/facility.py::Facility` is the duplicate**: 18 columns,
zero physical backing, `extend_existing=True`, claiming a name another base
already owns physically. It must be renamed or retired.

**Not implemented in BATCH-2.6.** It is an ORM schema change, nine sibling
foreign keys inside the national domain point at the name, and NR-023 is blocked
on more than this alone — so resolving it here would not unblock autogenerate.
**BATCH-3 item 1.**

## D-14 — Encounter: the episode already exists

BATCH-2.5 left this as Option A (extend `lab_orders`) versus Option B (a new
tenant-scoped `clinical_encounters`). The dependency analysis produced a third
answer that neither option stated, and the evidence for it is unambiguous.

**`visits` is already the clinical episode, and it is already physical.**

```
visits: id UUID PK, patient_id INTEGER FK -> patients, visit_type, status,
        created_at, closed_at
lab_orders.visit_id UUID  FK -> visits.id   (constraint fk_lab_orders_visit_id)
```

Migration `20260505_0003_sndhs_phase1_visits_table.py` states the architecture in
its own docstring: *"Visit-based architecture: every clinical action is anchored
to a visit."*

### Why this settles Option A vs Option B

**Option A — extend `lab_orders` — is refused by the evidence.**
`lab_orders` has **8** inbound foreign-key references and every one is internal
to `app.database.Base`. No other domain references it. Meanwhile **11 packages**
reference an *encounter*. The domains have already voted, in code, that the
episode is not the laboratory order. A pharmacy sale, a blood-bank reservation
and a nursing assessment are not laboratory orders, and anchoring them to one
would require creating a lab order to have an episode.

**Option B's shape is right; building a new table is wrong.** `visits` already
has Option B's exact structure — a tenant-scoped episode that `lab_orders`
references — with the foreign key already enforced. Creating
`clinical_encounters` would produce a **fourth** episode representation
alongside `lab_orders`, `visits` and `national_encounters`.

### RECOMMENDED — Option B, realised by adopting `visits`

| | |
|---|---|
| Canonical clinical episode | **`visits`** (physical, UUID PK) |
| `national_encounters` | **PROJECTION** — read-only, rebuildable, never an FK target |
| `lab_orders` | references the episode; it is **not** the episode |

**Advantages.** The table, its key and its `lab_orders` foreign key already
exist and are already deployed. It is UUID-keyed, which suits an entity whose
identity crosses domains. Migration complexity is additive: extend `visits`,
then migrate the five unconstrained string columns to `visit_id UUID`. It gives
one episode for laboratory, pharmacy, blood bank, nursing, radiology and billing
alike.

**Disadvantages, stated plainly.** `visits` has only six columns — no facility,
no practitioner, no encounter-type taxonomy beyond `visit_type`, no period
semantics beyond `closed_at`; extension is required. It carries **no `lab_id`**:
tenancy is derived through `patients.lab_id`, which is indirect and needs an
explicit decision. It is mapped by **no ORM model at all** (it is one of the
twelve in NR-030), so nothing reads or writes it today. It is gated off by
`SNDHS_ENABLE_VISITS`, and `docs/sndhs/phase1/RUNBOOK.md` must be read before
that flag is touched on real data.

**Affected entities:** `visits`, `lab_orders`, `billing_invoices.encounter_ref`,
`blood_bank_{patient_samples,reservations,reactions}.encounter_id`,
`pharmacy_sales.encounter_id`, plus 47 ORM foreign keys across
`care_continuum` (16), `ehr` (14), `nursing` (12) and `national` (5).

**Future limitation of not deciding:** every new domain invents a sixth episode
type. There are already five incompatible ones — `String(26)`, `String(64)`,
`String(100)`, `String(128)` and `UUID`.

### Still requiring a human

The recommendation is evidence-backed, but three sub-questions are not
derivable from the repository and are **BLOCKED — CLINICAL OWNER REQUIRED**:

1. Does `visits` gain an explicit `lab_id`, or does tenancy stay derived through
   `patients`?
2. What is the encounter-type taxonomy — is `visit_type` extended, or replaced
   by the `EncounterType` enum the national layer already defines?
3. Does adopting `visits` require enabling `SNDHS_ENABLE_VISITS`, and what is the
   backfill path for orders that predate it?

No table is created and no migration is written in BATCH-2.6.

---

# BATCH-2.7 — Physical / ORM ownership reconciliation

## D-15 — NR-029 was a naming error, not a missing table

`niam_identity_authorities` and `niam_user_sessions` are **class names**, not
table names: `IdentityAuthority` is `niam_gov_authorities`, `UserSession` is
`niam_sessions`. Both tables exist and PostgreSQL already enforces all three
foreign keys against them. The migrations were right; three ORM strings were
wrong. Corrected in place — no migration, no schema change.

**One of NR-023's three blockers is closed.** Remaining: NR-006 and NR-030.

## D-16 — NR-030: the twelve are classified, and seven are permanent

| Class | Count | Rule |
|---|---:|---|
| `KEEP_PHYSICAL_NO_ORM` | 7 | a named, justified, permanent exclusion — never silent |
| `MAP_EXISTING_ORM` | 2 | the nursing pair; blocked behind NR-026 |
| `CREATE_ORM` | 1 | `radiology_ai_analysis_jobs` — mechanical, unauthorised here |
| `BLOCKED` | 2 | `sndhs_audit_logs`, `visits` |

The seven permanent exclusions mean the combined-MetaData architecture can never
simply "map everything". It must carry an explicit exclusion list, which is why
Option C in D-11 was specified with one.

## D-17 — NR-026 is a live outage, not drift

`ClinicalChecklist` says `nursing_checklists`; `EscalationRecord` says
`nursing_escalations`. Neither name appears in any `create_table`. The migration
creates `nursing_clinical_checklists` and `nursing_escalation_records` — and
names the *indexes* after the short forms, which is where the mistake came from.

Live HTTP routes query both models, so **two nursing features fail at runtime**,
one of them clinical escalation. Raised from P1 drift to **P0 live defect**.

**Deliberately not half-fixed.** Renaming `__tablename__` alone would take these
from failing loudly to succeeding with wrong types —
`EscalationRecord.escalated_to` is `String(26)` against a physical `integer` and
sits in a live filter. Name and types land together, or not at all.

## D-18 — Visit is the clinical episode anchor

Established, with nothing in the repository disproving it:

- the migration that created `visits` states it — *"every clinical action is
  anchored to a visit"*;
- `lab_orders.visit_id → visits.id` is enforced in the database today;
- no competing physical episode table exists.

`national_encounters` is the **projection**; `CanonicalEncounter` is already its
implementation. Full mapping in `GULA_VISIT_ENCOUNTER_ARCHITECTURE.md`.

**Correction to D-14:** `visits` has **no** code consumers. BATCH-2.6 reported
it as consumed; every hit was a substring false positive. Adoption is therefore
lower-risk than stated — there is no live usage to migrate — and the table is
currently inert schema.

Three sub-questions remain **BLOCKED — CLINICAL OWNER REQUIRED**, unchanged.

## D-19 — NR-006 stands, unchanged

`clinical_scope.NationalFacility` and `national.domain.facility.Facility` are
**not merged**. The operational facility (`facilities`, INTEGER) and the national
facility resource (`national_facilities`, String(26)) are separate resources
bridged by review through `clinical_ehr_facility_bindings`, as `clinical_scope.py`
states in-source. No schema migration in this batch. Still BATCH-3 item 1.
