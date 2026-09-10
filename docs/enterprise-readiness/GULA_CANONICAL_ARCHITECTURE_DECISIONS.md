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
