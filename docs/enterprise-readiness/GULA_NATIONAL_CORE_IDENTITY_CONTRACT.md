# GULA National Core — Ownership and Identity Contract

**Batch:** BATCH-2.5 (decision batch — no migrations, no schema changes)
**Scope:** Practitioner ownership, Encounter ownership, and the identity model
for the seven national-core entities.
**Method:** repository evidence only. Every number below is reproducible from
the working tree; none is estimated. Where the evidence does not settle a
question, the answer is recorded as BLOCKED rather than guessed.

---

## 0. What changed in the measurement itself

Earlier NR-023 numbers in this repository were measured **before**
`import_all_models()` was added to `backend/migrations/env.py`. With the full
import graph in place, the figures are different and the earlier ones should
not be quoted:

| Quantity | Earlier (partial graph) | Now (full env.py graph) |
|---|---|---|
| Registered `MetaData` objects | 10 resolved | **18 registered, 18 distinct** |
| Unresolvable FK targets | 13 | **24** |
| Unresolvable FK references | ~130 | **360** |
| Targets mapped by *no* metadata | 1 (`citizens`) | **0** |
| Table names claimed by two metadata | 1 | **1** (`national_facilities`) |

The single most important correction: **no FK target is unmapped.** Every one
of the 24 is mapped — just by a *different* `MetaData` than the table that
references it. NR-023 is therefore not "the national core does not exist"; it
is "foreign keys cannot cross a `MetaData` boundary". That distinction changes
the fix.

---

## 1. Practitioner — ownership

### Evidence

| # | Observation | Where |
|---|---|---|
| P1 | Exactly **one** practitioner entity exists in the repository: `national_practitioners`. | `backend/app/national/domain/practitioner.py` |
| P2 | **Zero** practitioner or provider tables appear in any of the 106 migrations. The entity has no physical schema. | `grep create_table backend/migrations/versions/` |
| P3 | Core has no practitioner entity. The ordering clinician is stored as **free text**: `lab_orders.doctor_name String(200)`. | `backend/app/models/lab_order.py:30` |
| P4 | `lab_users` is an **authentication principal**, not a professional record: `email`, `password_hash`, `failed_login_attempts`, `locked_until`, `perm_version`, `lab_id NOT NULL`. It carries no licence, specialty, qualification or verification state. | `backend/app/models/lab_user.py` |
| P5 | `Practitioner` extends `AuditEntity` — **no `lab_id`**. Every registry entity in the same package (facility, organization, department, hospital, laboratory, clinic, ward, directorate, employee, provider) is likewise non-tenant; every clinical-episode entity (encounter, admission, discharge, visit, observation, appointment, referral, patient) is `TenantAuditEntity`. The package already partitions registry from episode by tenancy. | `backend/app/national/domain/*.py` |
| P6 | `license_number` is `unique=True` **globally**. A tenant-scoped entity cannot carry a globally unique licence. | `practitioner.py:22` |
| P7 | **78 foreign-key columns** across `care_continuum` (56), `ehr` (21) and `national_data` (1) reference `national_practitioners.id`. | env.py metadata probe |
| P8 | **Zero persistence.** No `query(Practitioner)`, no repository, no service, no route. The only consumer is a FHIR mapper. | `grep -rn "Practitioner" backend/app/` |
| P9 | `national_patients.lab_patient_id Integer` exists — the repository's own projection pointer back to Core `patients`. **No equivalent pointer exists on Practitioner.** | `backend/app/national/domain/patient.py:13` |

### Decision — **B: Practitioner belongs to the National core**

The evidence forces a sharper statement than the three options allow: there are
**two distinct entities**, not one duplicated entity.

| Entity | Owner | Nature | Key | Tenancy |
|---|---|---|---|---|
| `lab_users` | **Core** | authentication principal / account | `Integer` (physical) | `lab_id NOT NULL` |
| `national_practitioners` | **National** | professional registry: licence, specialty, qualification, verification | see §3 | none — global |

They are related by an **optional link**, not by identity. A practitioner may
have no GULA account; an account may belong to a non-clinical user. The link
belongs on the account side as a nullable `lab_users.practitioner_id`, and it
is a BATCH-3 item, not this batch.

**Why not A (Core owns Practitioner).** Nothing in Core defines the entity —
P2, P3, P4. The globally unique licence (P6) cannot be expressed inside Core's
tenant model.

**Why not C (Core canonical + National projection).** A projection requires a
Core canonical entity to project *from*, and there is none (P2, P3). The
repository shows exactly what it looks like when it *does* mean projection —
`lab_patient_id` on `national_patients` (P9) — and Practitioner has no such
pointer.

**Consequence for the 78 references.** They are correct in direction: clinical
records attribute care to a registry practitioner. They are wrong in mechanism
(cross-`MetaData`) and in type (§3).

---

## 2. Encounter — ownership

### Evidence

| # | Observation | Where |
|---|---|---|
| E1 | `Encounter` extends `TenantAuditEntity` → **`lab_id Integer NOT NULL`**. A national encounter registry cannot mandate a lab id: an encounter at a facility that is not a GULA lab has none. The declaration contradicts national scope. | `backend/app/national/domain/encounter.py:6` |
| E2 | Three **physical, deployed** tables already reference an encounter as an **unconstrained string, in three different widths, with no foreign key**: `billing_invoices.encounter_ref VARCHAR(128) NOT NULL`; `blood_bank_patient_samples` / `_reservations` / `_reactions`.`encounter_id VARCHAR(100)`; `pharmacy_sales.encounter_id VARCHAR(26)`. | migrations `20260814_0009`, `20260901_0001`, `20260815_0022` |
| E3 | **42 foreign-key columns** reference `national_encounters.id`: `care_continuum` 16, `ehr` 14, `nursing` 12. All are `String(26)`. | env.py metadata probe |
| E4 | `CanonicalEncounter` already exists as a **read-only projection**: `__abstract__`, no table, outer-joins `national_encounters → national_patients → lab_orders`, and derives `lab_id` from `national_patients.lab_id` — **not** from `Encounter.lab_id`. The repository already models the national encounter view as a projection over a tenant-owned record, and already ignores the encounter's own tenant column. | `backend/app/national_data/models/canonical_encounter.py` |
| E5 | The only writer is `create_encounter(db, data)` — `Encounter(**data)`, no tenant enforcement, no state machine, no audit. It cannot execute: the table does not exist. | `backend/app/national/services/encounter_service.py:35` |
| E6 | Core's actual clinical episode today is `lab_orders`: physical, `Integer` PK, `lab_id NOT NULL`, with a real state machine. | `backend/app/domain/order_state.py` |

### Decision — **C: a tenant-owned clinical canonical entity, plus a National projection**

- The **canonical transactional encounter is tenant-scoped and clinically
  owned**. E1, E2 and E6 all point the same way: the mandatory `lab_id`, the
  tenant-local production references, and the fact that the real episode record
  in service today is `lab_orders`.
- `national_encounters` becomes a **`PROJECTION`** — read-only, rebuildable,
  never a foreign-key target. `CanonicalEncounter` (E4) is already the shape of
  that projection and is the thing to extend, not to replace.

**Why not A as literally stated** ("Core Clinical, full stop"): a national read
model already exists and is wanted (E4). Suppressing it would delete working
intent.

**Why not B** (National owns it): E1, E2, E6.

### BLOCKED — CLINICAL OWNER REQUIRED

Which clinical entity is canonical is **not** settled by the evidence:

- **(i)** extend `lab_orders` into a general clinical encounter, or
- **(ii)** create a new tenant-scoped `clinical_encounters` table that
  `lab_orders` references.

Both are consistent with every observation above. Choosing between them decides
whether a pharmacy sale, a blood-bank reservation and a lab order can share one
episode — a clinical modelling question, not a schema-mechanics one. Recorded
as **BLOCKED — CLINICAL OWNER REQUIRED**. It is not guessed here.

Until it is answered, the three existing production string columns (E2) stay
exactly as they are. They must not be retyped to chase a decision that has not
been made.

---

## 3. Identity model

### Why the current `VARCHAR` proposal is not adopted as-is

The national core proposes `VARCHAR` keys everywhere. Three measured facts
argue against copying that shape, and one argues against reflexively replacing
it.

**Fact 1 — one name, two incompatible identifier schemes.** Fifteen functions
in the tree are called `_ulid()`, and they do two different things:

- **13** return `str(uuid.uuid4()).replace('-', '').upper()[:26]` — the first 26
  hex characters of a random UUID4. That is **not a ULID**: no timestamp prefix,
  no Crockford base32, no monotonic ordering. It pays the full 26-byte cost of a
  string key while delivering **none** of the only benefit that would justify
  choosing ULID over UUID, and silently truncates 128 bits to 104.
- **2** are genuine ULIDs — 48-bit millisecond timestamp plus 80 random bits,
  Crockford base32, time-sortable — in `app/services/consent_service.py` and
  `app/services/mpi/resolver.py`.

So identifiers minted under one name are not mutually ordered, and a call site
does not reveal which scheme it gets. Critically, **every declarative base uses
the fake one**; the real implementation is confined to two services and mints no
primary keys. Recorded as **NR-025**.

**Fact 2 — P0-2 already paid to undo this shape.** Milestones M1–M4 moved 27
pharmacy tables off `String(26)` `_ulid()` keys because the physical schema was
`Integer` while the ORM said `String(26)`, so no query round-tripped. Building
the national core on `VARCHAR` would recreate, at national scale, the defect
four milestones were spent removing.

**Fact 3 — but do not force one type everywhere.** `national_facilities` is
**already physical** with a `String(26)` primary key and an existing physical
foreign key pointing at it (`clinical_ehr_facility_bindings.national_facility_id`).
Retyping a live key to satisfy a rule is exactly the "modify schema merely to
make the tooling clean" move this batch forbids.

### Identifier classes

Per the settled `CANONICAL_DRUG_CONTRACT` §11:

| Class | Rule |
|---|---|
| `INTERNAL_KEY` | database primary key; never in a payload, never in a URL |
| `PUBLIC_ID` | UUID4, immutable, the **only** identifier an API returns |
| `BUSINESS_CODE` | human-facing, mutable, uniquely constrained, **never** a join target |
| `NATIONAL_IDENTIFIER` | encrypted at rest, HMAC-indexed, never a key, dual-read NULL-tolerant |
| `EXTERNAL_IDENTIFIER` | opaque, owned by another system, never a key |
| `FHIR_IDENTIFIER` | interop projection, non-authoritative, nullable |

### Per-entity contract

| Entity | Owner | `INTERNAL_KEY` | `PUBLIC_ID` | `NATIONAL_IDENTIFIER` | `EXTERNAL_IDENTIFIER` | `FHIR_IDENTIFIER` | `BUSINESS_CODE` |
|---|---|---|---|---|---|---|---|
| **Citizen** | National | `INTEGER` | `UUID4` | national ID (encrypted + HMAC) | — | `fhir_id String(64)` | `national_health_number` |
| **Patient (national)** | **PROJECTION** of Core `patients` | *none — carries `patient_id INTEGER`* | reuses Core patient's `UUID4` | inherited, not restated | `lab_patient_id INTEGER` | `fhir_id` | — |
| **Practitioner** | National | `INTEGER` | `UUID4` | national ID (encrypted + HMAC) | `health_profession_number`, nullable `lab_user_id INTEGER` | `fhir_id` | `license_number` |
| **Encounter** | **BLOCKED** (see §2) | `BIGINT` | `UUID4` | — (an encounter has none; the *patient* does) | the three legacy string refs, until migrated | `fhir_id` | `encounter_number` (per tenant) |
| **Department** | National (facility-scoped) | `INTEGER` | `UUID4` | — | — | `fhir_id` | `department_code` (unique within facility) |
| **Facility (operational)** | **Core `facilities`** | `INTEGER` *(already physical)* | `UUID4` | — | — | `fhir_id` | `facility_code` |
| **Facility (national EHR directory)** | **Core `national_facilities`** | `String(26)` *(already physical — do not retype)* | — | — | bridged via `clinical_ehr_facility_bindings` | — | `facility_code` (already uniquely constrained) |
| **Organization** | National | `INTEGER` | `UUID4` | — | — | `fhir_id` | `org_code` |

### Why each key type

- **`INTEGER` for registry entities** (Citizen, Practitioner, Department,
  Organization). Their cardinality is bounded by population or by profession:
  a 45-million-person registry sits three orders of magnitude below the
  2.1-billion `INTEGER` ceiling. `INTEGER` also matches the settled Pharmacy
  contract, so one rule governs both domains.
- **`BIGINT` for Encounter, and only Encounter.** Encounters are *events*, not
  entities: their row count grows with time, not with population. At national
  volume the `INTEGER` ceiling is reachable within the system's service life,
  and a primary-key type change on the largest clinical table is the single
  most expensive migration a platform can be made to perform. This is the one
  place where the extra four bytes are cheaper than the alternative.
- **No new key at all for the Patient projection.** A projection has no
  independent identity. Giving `national_patients` its own key is what made it
  look like a second source of truth in the first place.
- **`String(26)` retained for `national_facilities`.** It is physical, it is the
  target of a physical foreign key, and it belongs to a *separate* resource from
  the operational facility — stated explicitly in `app/models/clinical_scope.py`:
  the national EHR facility is a distinct resource from the operational facility,
  and no relationship may be inferred from identifier similarity. Changing it
  would be schema churn for tooling convenience.

### Rules that follow

1. No API response may contain an `INTERNAL_KEY`. Response builders are
   explicit, as M4 did for Pharmacy.
2. `license_number`, `facility_code`, `department_code`, `org_code`,
   `national_health_number` are `BUSINESS_CODE`s: uniquely constrained, mutable,
   and **never** join targets. `Practitioner.license_number` is currently
   `unique=True` and used as an identifier — it must be demoted to a business
   code when the table is built.
3. National identifiers keep the existing SNDHS rules: encrypted at rest,
   dual-read NULL-tolerant, never plaintext, never a key.
4. External identifiers arriving from another domain keep **their** type. A
   `String(26)` reference is not converted merely because this domain uses
   integer keys.
5. No foreign key may point at a `PROJECTION`.

---

## 4. NR-023 — where it actually stands

### Proven root cause

Cross-`MetaData` foreign keys. SQLAlchemy resolves `ForeignKey("table.col")`
only within the referrer's own `MetaData`. `target_metadata` is a list of **18
distinct** `MetaData` objects, and Alembic sorts each independently.

Reproduced with **no database connection** — this is a pure metadata failure:

```
=== per-metadata topological sort (what autogenerate does) ===
  FAIL  app.ehr.base.EHRBase              ehr_allergies.encounter_id -> national_encounters
  FAIL  app.trust.base.TrustBase          trust_consent_records.lab_id -> labs
  FAIL  app.care_continuum.base...        cc_care_journeys.organization_id -> national_organizations
  FAIL  app.identity.base.IdentityBase    niam_assignments.clinical_organization_resource_id -> organizations
  FAIL  app.nursing.base.NursingBase      nursing_shifts.department_id -> hospital_departments
  FAIL  app.national_data.base...         dp_consent_directives.patient_id -> patients
  (12 of 18 sort cleanly)
```

360 unresolvable references, 24 distinct targets, **all 24 mapped somewhere**.

Confirmed end to end against a clean database migrated to head `20260912_0001`
(423 tables, all 7 CI-required tables present, `downgrade -1 && upgrade head`
clean):

```
$ alembic revision --autogenerate -m "..."
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
'ehr_allergies.citizen_id' could not find table 'national_citizens'
exit=1   # migration directory unchanged: 106 files before, 106 after
```

The named column moves between runs — `practitioner_id`, `encounter_id`,
`citizen_id` — because import order decides which foreign key is reached first.
The class of failure does not move.

### The canonical repair, and the one thing blocking it

One shared `MetaData` across all bases. It is blocked by **exactly one**
table-name collision:

```
national_facilities: ['app.database.Base', 'app.national.base.NationalBase']
```

That is **NR-006**, and the evidence now settles which mapping is real:

| Mapping | Columns | Physical? |
|---|---|---|
| `app.models.clinical_scope.NationalFacility` (`app.database.Base`) | 6: `id, facility_code, name, status, created_at, updated_at` | **Yes** — matches migration `20260813_0004` exactly, and is the target of the physical FK from `clinical_ehr_facility_bindings` |
| `app.national.domain.facility.Facility` (`app.national.base`) | 18, entirely different | **No** — zero physical backing, declared `extend_existing=True` |

So NR-006's resolution is no longer a coin-flip: the `app.database.Base`
mapping is authoritative, and the national-domain class is a second, unbacked
claim on a name that is already taken.

### What was NOT done, and why

Renaming or retiring `app.national.domain.facility.Facility` would unblock the
shared `MetaData`. It is deliberately **not** done in this batch: it is an ORM
schema change, and nine sibling foreign keys inside the national domain point
at the name. It is the first item of BATCH-3.

### The safe infrastructure correction that WAS made

`backend/migrations/env.py` now calls `import_all_models()` **before**
`target_metadata` is built.

This fixes a real hazard introduced by the NR-018 registrations: a base-only
import registers **no tables**, so `PharmacyBase`, `RadiologyBase`, `NHDWBase`
and `NursingBase` each resolved to an **empty** `MetaData`. Autogenerate would
have compared zero mapped tables against a populated database and proposed
**dropping all 74 of them** (27 + 18 + 14 + 15). After the change they resolve
to 27 / 18 / 14 / 15 respectively.

### Status

**NR-023 is NOT fixed.** The required invariant — *autogenerate executes
deterministically and never fails because of an unresolved metadata
relationship* — is **not met**. 6 of 18 metadata objects still fail to sort.
The blocker is proven, named, and reduced to a single decision.

NR-018 remains **PARTIALLY VERIFIED**: zero-diff cannot be proven while
autogenerate cannot run, and no proof is fabricated here.

---

# BATCH-2.6 — Finalised contract and ownership matrix

Documentation only. No National Core schema is implemented.

## 5. The seven entities

`Person` and `Health Identity` are added here; they were implicit before.

| Entity | Internal DB PK | Public ID | National identifier | External identifier | FHIR identifier | Business identifier | Scope | Canonical owner |
|---|---|---|---|---|---|---|---|---|
| **Person** | `INTEGER` | `UUID4` | Iraqi national ID — encrypted at rest, HMAC-indexed | — | `fhir_id String(64)` | — | GLOBAL | **National** (`national_citizens`) |
| **Patient** | `INTEGER` *(physical, Core `patients`)* | `UUID4` | inherited from Person, never restated | `lab_patient_id INTEGER` on the projection | `fhir_id` | medical record number | TENANT (`lab_id`) | **Core `patients`** |
| **Practitioner** | `INTEGER` | `UUID4` | national ID — encrypted, HMAC-indexed | `health_profession_number`, nullable `lab_user_id INTEGER` | `fhir_id` | `license_number` | GLOBAL | **National** |
| **Organization** | `INTEGER` | `UUID4` | — | — | `fhir_id` | `org_code` | GLOBAL | **National** |
| **Facility (operational)** | `INTEGER` *(physical)* | `UUID4` | — | — | `fhir_id` | `facility_code` | GLOBAL | **Core `facilities`** |
| **Facility (national resource)** | `String(26)` *(physical — do not retype)* | — | — | bridged via `clinical_ehr_facility_bindings` | — | `facility_code` (unique) | GLOBAL | **Core `national_facilities`** |
| **Encounter** | `UUID` *(physical, `visits.id`)* | the same `UUID` | — | the five legacy string columns, until migrated | `fhir_id` | `visit_type` | TENANT — **derived** through `patients.lab_id` | **Core `visits`** (see D-14) |
| **Health Identity** | `INTEGER` | `UUID4` | `sndhs_health_id`, `national_health_number` | payer/insurer member ids | `fhir_id` | `national_health_number` | GLOBAL | **National** |

Encounter's key changes from the BATCH-2.5 proposal. That proposal specified
`BIGINT` for a table yet to be built; the table exists and is keyed `UUID`.
Retyping a live primary key to satisfy a rule is the churn this contract
forbids, and UUID suits an identity that crosses domain boundaries.

## 6. Ownership matrix

| Entity | Canonical owner | National role | Physical owner | Identity | Tenant / scope | Dependencies | Consumers | FHIR role | Status |
|---|---|---|---|---|---|---|---|---|---|
| Person | National | **source of truth** | none — not built | `INTEGER` + `UUID4` | GLOBAL | — | Patient, Health Identity | `Patient`/`RelatedPerson` subject | **NOT STARTED** |
| Patient | Core `patients` | **PROJECTION** (`national_patients`) | `patients` | `INTEGER` + `UUID4` | TENANT | Person | orders, results, pharmacy, blood bank, nursing, EHR | `Patient` | **VERIFIED** (physical) |
| Practitioner | National | source of truth | none — not built | `INTEGER` + `UUID4` | GLOBAL | Organization, Facility | 78 FK columns across ehr, care_continuum, national_data | `Practitioner` / `PractitionerRole` | **BLOCKED** on build |
| Organization | National | source of truth | none — not built | `INTEGER` + `UUID4` | GLOBAL | — | Facility, Practitioner, Department | `Organization` | **NOT STARTED** |
| Facility (operational) | Core `facilities` | consumer | `facilities` | `INTEGER` + `UUID4` | GLOBAL | Organization | operations, authorization scope | `Location` | **VERIFIED** (physical) |
| Facility (national resource) | Core `national_facilities` | **registry** | `national_facilities` | `String(26)` | GLOBAL | — | clinical scope bridges | `Organization`/`Location` directory | **PARTIALLY VERIFIED** — NR-006 duplicate mapping |
| Encounter | Core `visits` | **PROJECTION** (`national_encounters`) | `visits` | `UUID` | TENANT (derived) | Patient | 11 packages; 5 legacy string columns | `Encounter` | **PARTIALLY VERIFIED** — physical, unmapped, flag-gated |
| Health Identity | National | source of truth | none — not built | `INTEGER` + `UUID4` | GLOBAL | Person | SNDHS integration, payer routing | `Patient.identifier` | **NOT STARTED** |

## 7. Rules, restated as they now apply

1. **No universal PK type.** `INTEGER` for population-bounded registries, `UUID`
   where an identity crosses domains and already exists that way (`visits`),
   `String(26)` retained where it is already physical (`national_facilities`).
   The type follows the entity, never a house rule.
2. **Mutable business codes are not canonical identity.** `license_number`,
   `facility_code`, `org_code`, `national_health_number`, `visit_type` are
   uniquely constrained, mutable, and never join targets.
3. **Projections are not transactional owners.** `national_patients` and
   `national_encounters` are read-only and rebuildable. **No foreign key may
   point at a projection** — which is precisely what the 47 ORM foreign keys to
   `national_encounters` currently do, and why they must be repointed.
4. **External IDs remain external.** A `String(26)` reference arriving from
   another domain is not converted because this domain uses integer keys.
5. **Tenant scope is explicit.** Encounter's is currently *derived* through
   `patients.lab_id`; making it explicit is one of the three questions blocked
   on a clinical owner.
