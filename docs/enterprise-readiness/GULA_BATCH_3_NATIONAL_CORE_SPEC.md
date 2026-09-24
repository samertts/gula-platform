# BATCH-3 — National Core Specification

**Specification only. Not implemented. No migrations created.**
2026-09-10 · `production_ready: false`

Two independent analyses converged on this batch. BATCH-2 reached it from
foreign-key direction; the global capability discovery reached it from clinical
value. A third has now joined them: `alembic revision --autogenerate` cannot run
at all because of this same gap (NR-023).

## 1. Why this is first

Four of the five most-depended-on tables in the repository do not exist:

| Table | Inbound references | Physical |
|---|---|---|
| `national_practitioners` | 58 | no |
| `national_citizens` | 51 | no |
| `national_patients` | 51 | no |
| `national_encounters` | 42 | no |
| `national_facilities` | 44 | **yes — and mapped by two bases** |

`care_continuum` (45/45 tables), `ehr` (16/18), `nursing` and `national_data`
all declare foreign keys into this core. Nothing above it can be built, and
autogenerate cannot emit a migration for anything while it is missing.

## 2. Canonical ownership — decided

Per the authorising decision, and recorded in
`GULA_CANONICAL_ARCHITECTURE_DECISIONS.md`:

| Entity | Canonical owner | Consequence |
|---|---|---|
| **Patient** | **Core `patients`** (`app.models.base.Base`, physical, 22 inbound refs) | `national_patients` must **not** become a second transactional owner |
| **Facility** | **Core Facility** for operations | a national directory may exist as a registry/projection only |
| **Practitioner** | **National** (BATCH-2.5) | `lab_users` is an account, `national_practitioners` is a professional registry — two entities, not one. Linked by an optional nullable `lab_users.practitioner_id`. |
| **Encounter** | **Clinical (tenant-owned) canonical + National `PROJECTION`** (BATCH-2.5) | Which clinical table is canonical is **BLOCKED — CLINICAL OWNER REQUIRED** |

A national read model is permitted and must be classified `PROJECTION`. A
projection may be read from and rebuilt; it may never be written to as a source
of truth, and no foreign key may point *at* it.

## 3. Entities in scope

Measured state, not aspiration:

| Entity | Table | Physical | Scope | Reachable ops | PK today |
|---|---|---|---|---|---|
| Citizen | `national_citizens` | no | GLOBAL | 10 | `VARCHAR` |
| Patient (national view) | `national_patients` | no | TENANT | 0 | `VARCHAR` |
| Practitioner | `national_practitioners` | no | FACILITY | 0 | `VARCHAR` |
| Encounter | `national_encounters` | no | TENANT | 29 | `VARCHAR` |
| Department | `national_departments` | no | FACILITY | 0 | `VARCHAR` |
| Facility | `national_facilities` | **yes** | GLOBAL | 0 | `VARCHAR` |
| Organization | `national_organizations` | no | GLOBAL | 0 | `VARCHAR` |

**Every one keys on `VARCHAR`** — the Generation-B shape Pharmacy was moved off
in P0-2. Building them as they stand would recreate the defect P0-2 spent four
milestones removing.

BATCH-2.5 added a third reason not to copy it: one name covers two
incompatible schemes. Of the fifteen `_ulid()` definitions, **13** return
`str(uuid.uuid4()).replace("-","").upper()[:26]` — the first 26 hex characters
of a random UUID4, which is **not a ULID** (no timestamp prefix, no monotonic
ordering, full 26-byte cost, none of the benefit) — while **2** are genuine
Crockford-base32 ULIDs. Every declarative base uses the fake one. Recorded as
**NR-025**.

## 4. Identity model

**Superseded in detail by
`docs/enterprise-readiness/GULA_NATIONAL_CORE_IDENTITY_CONTRACT.md`, which
gives the per-entity contract (internal key, public id, national identifier,
external identifiers, FHIR identifier, business code) and justifies each type.**
Two departures from a blanket rule are deliberate: `Encounter` takes `BIGINT`
because its row count grows with time rather than population, and
`national_facilities` keeps its physical `String(26)` key because retyping a
live key to satisfy a rule is schema churn for tooling convenience.

Follow the settled Pharmacy contract otherwise; it is the reference
implementation and is not reopened:

- internal `INTEGER` primary key, never exposed by an API;
- immutable public `UUID4` — the only identifier a response may carry;
- mutable business codes (facility code, licence number) that are never keys
  and never join targets;
- external identifiers from other domains stay `String(26)` and are not
  converted merely because this domain uses integer keys.

The national ID and health ID carry the existing SNDHS rules: encrypted at
rest, dual-read tolerant of `NULL`, never plaintext.

## 5. Tenancy

| Entity | Scope | Rule |
|---|---|---|
| Citizen, Facility, Organization | GLOBAL | national reference data — a tenant filter here would be **wrong** |
| Patient, Encounter | TENANT | every query filters `lab_id`; no exceptions |
| Practitioner, Department | FACILITY | scoped through facility, which is itself global |

NR-021 is the cautionary case: nine reachable methods on one service queried
without a tenant filter, on tables that all carried `lab_id`.

## 6. Audit, authorization, migration, API, clients

- **Audit** — every mutation writes to the SHA-256 hash-chained audit log. No
  new mechanism; the existing one is one of GULA's genuine strengths.
- **Authorization** — RBAC + ABAC as they stand. Do not introduce a parallel
  model. NR-021 was fixed by *reusing* the existing `_lab_id` helper.
- **Migration** — fail-closed, in the M3/M4 pattern: refuse in both directions
  unless the affected tables are empty, reporting per-table counts rather than
  casting. Every migration idempotent, every new column nullable or defaulted.
- **API** — public UUIDs only; explicit response builders so an internal integer
  key cannot leak, exactly as M4 did for Pharmacy.
- **Clients** — no existing client contract changes, because none of these
  endpoints can currently return a row. Web, Android, iOS and desktop are
  unaffected until the endpoints work; that is when versioning matters.

## 7. Blockers and open decisions

**Blocking, must be answered before implementation:**

1. **Is `national_patients` the same entity as core `patients`?** The
   authorising decision names Core Patient canonical. What remains is whether
   `national_patients` becomes a `PROJECTION` of it, or is retired outright.
   Its own evidence — 0 reachable operations, 51 inbound references — supports
   projection-or-retire, not independent existence.
2. ~~**Practitioner.**~~ **ANSWERED (BATCH-2.5): National.** The two are
   distinct entities — `lab_users` is an authentication principal (no licence,
   no specialty, no verification state, `lab_id NOT NULL`); `national_practitioners`
   is a professional registry with a globally unique `license_number` and no
   tenant column. Core has no practitioner entity at all: the ordering clinician
   is `lab_orders.doctor_name String(200)`, free text. They link through an
   optional nullable `lab_users.practitioner_id`, not through identity.
3. **`national_facilities` (NR-006).** Physical and mapped by two bases —
   **now the single blocker for NR-023, and evidence-determined.**
   `app/models/clinical_scope.py::NationalFacility` declares exactly the six
   columns migration `20260813_0004` creates and is the target of the physical
   FK from `clinical_ehr_facility_bindings`; `app/national/domain/facility.py::Facility`
   declares eighteen different columns with zero physical backing. Keep the
   former, rename or retire the latter, and follow the rename through the nine
   sibling foreign keys inside the national domain. **This is BATCH-3 item 1.**

4. **Which clinical table is the canonical Encounter** — extend `lab_orders`,
   or create a tenant-scoped `clinical_encounters` that `lab_orders` references?
   **BLOCKED — CLINICAL OWNER REQUIRED.** Both are consistent with the evidence;
   the choice decides whether a pharmacy sale, a blood-bank reservation and a lab
   order can share one episode.

**Blocking but already answered elsewhere:** NR-023 — autogenerate cannot run.
BATCH-2.5 proved the root cause is **not** "the core does not exist": all 24
unresolvable foreign-key targets **are** mapped, just by a different `MetaData`
than the table referencing them. `target_metadata` is 18 distinct `MetaData`
objects and Alembic sorts each independently, so 6 of the 18 fail. The canonical
repair is one shared `MetaData`, blocked by exactly one table-name collision —
item 3 above. This batch must still be written by hand and verified against a
clean database.

## 8. Acceptance criteria

1. Every entity in §3 exists physically with an `INTEGER` key and a public `UUID4`.
2. `GULA-SCHEMA-003` findings fall by at least the 5 core tables; `GULA-SCHEMA-004`
   falls materially as cross-base foreign keys resolve.
3. `alembic revision --autogenerate` runs to completion (NR-023 closes).
4. Tenant isolation tests pass for every TENANT-scoped entity, in both directions.
5. Migration refuses on non-empty tables, proven in both directions.
6. No API returns an internal integer key.
7. No entity in §3 has two owners.

## 9. Explicitly out of scope

EHR, clinical, care_continuum, nursing, governance, national_data — every one
of them waits. Building any of them inside this batch would reintroduce the
coupling this batch exists to remove.

---

# BATCH-2.6 — Scope freeze and per-base verification

## 9. NR-018 — per-base status, measured

Against a database migrated to head `20260912_0001`. "Missing" means mapped but
not physical; "unmapped owned" means physical but mapped by no registered
metadata — a `DROP TABLE` candidate.

| Base | Mapped | Physical | Missing | Duplicate | Cross-MetaData FKs | Unmapped owned | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `PharmacyBase` | 27 | 27 | 0 | 0 | 0 | 0 | **VERIFIED** |
| `NHDWBase` | 14 | 14 | 0 | 0 | 0 | 0 | **VERIFIED** |
| `RadiologyBase` | 18 | 17 | 1 | 0 | 0 | **1** | PARTIALLY VERIFIED |
| `NursingBase` | 15 | 13 | 2 | 0 | **49** | **2** | PARTIALLY VERIFIED |
| `FinBase` | 37 | 31 | 6 | 0 | 0 | **6** | PARTIALLY VERIFIED |
| `HospitalBase` | 14 | 4 | 10 | 0 | 0 | 0 | PARTIALLY VERIFIED |
| `DataPlatformBase` | 36 | 0 | 36 | 0 | 13 | 0 | PARTIALLY VERIFIED |
| `DocIntelBase` | 21 | 0 | 21 | 0 | 0 | 0 | PARTIALLY VERIFIED |

**No base has duplicate ownership.** Only Pharmacy and NHDW are zero-diff
capable; every other base carries a real, explainable diff. Nothing was modified
to reduce a diff.

## 10. BATCH-3 scope — FROZEN

Nothing enters B3 unless it is a **proven hard dependency** of the National
Core. EHR, Care Continuity, Governance and National Data are explicitly not
pulled in.

### B3_REQUIRED

1. **NR-006** — rename or retire `app/national/domain/facility.py::Facility` and
   follow the 9 sibling foreign keys. ORM only; no physical schema change.
2. **NR-029** — resolve `niam_identity_authorities` and `niam_user_sessions`:
   define the models, or remove the 3 declarations. No metadata design resolves
   a reference to something that exists nowhere.
3. **NR-030** — decide the 12 unmapped physical tables. Six are Financial Engine
   Phase A (schema-only *by design* — they need an explicit exclusion, not a
   model); six are unexplained.
4. **Practitioner** — build `national_practitioners` per the identity contract.
   78 inbound foreign-key columns; ownership already CLOSED as National.

### B3_DEPENDENCY (blocked on a decision, not on effort)

- Adopt `visits` as the canonical clinical episode — blocked on three
  clinical-owner questions.
- Repoint the 47 ORM foreign keys away from `national_encounters` — a projection
  may not be a foreign-key target.
- Migrate the 5 legacy unconstrained episode columns to `visit_id UUID`.
- NR-007 `(entity, state)` keying — blocked on attributing the 28 synthetic keys.

### B4+

Person, Organization, Health Identity; national platform (29); clinical record
(45); care continuity (47); governance and data (79); hospital (9).

### DEFER

`app.insurance` (13); NR-017 warehouse; NR-026 nursing reconciliation; NR-025
identifier unification; NR-028 package root.

### RETIRE

`app.national.task_engine` (15); the duplicate national-domain `Facility`; the
five zero-caller Blood Bank legacy commands.

### BLOCKED

| Item | Blocked on |
|---|---|
| NR-023 autogenerate | NR-006 **and** NR-029 **and** NR-030 |
| NR-018 zero-diff proof | NR-023 |
| Encounter canonical adoption | clinical owner |
| NR-007 mechanical keying | clinical owner |
| Blood Bank legacy route audit | a behavioural API decision on 7 live endpoints |

---

# BATCH-2.7 — Scope freeze updated

**NR-029 leaves B3_REQUIRED** — resolved as a three-word ORM correction.

**NR-026 enters B3_REQUIRED**, promoted from DEFER on new evidence: it is a P0
live defect, not drift. Two nursing features fail at runtime, one of them
clinical escalation.

### B3_REQUIRED — now four items

1. **NR-006** — rename or retire `app/national/domain/facility.py::Facility`.
2. **NR-030** — wire the classified exclusion list into the combined-MetaData
   build. *What* the twelve tables are is now settled; only the wiring remains.
3. **Practitioner** — build `national_practitioners` per the identity contract.
4. **NR-026** — correct the two nursing `__tablename__` values **and** the 23
   drifted column types in one change.

### RETIRE — added

Six Blood Bank transition keys that are unreachable in both directions:
`crossmatch_requested`, `draft`, `issued_order`, `ordered_transfusion`,
`received_sample`, `testing_crossmatch`.

### BLOCKED — updated

| Item | Blocked on |
|---|---|
| NR-023 autogenerate | **NR-006 and NR-030** (NR-029 closed) |
| NR-018 zero-diff proof | NR-023 |
| Visit adoption | clinical owner — 3 questions |
| NR-007 mechanical keying | clinical owner — 15 UNRESOLVED keys |
| Blood Bank legacy route audit | a behavioural API decision on 7 live endpoints |
