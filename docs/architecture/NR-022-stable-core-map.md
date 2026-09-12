# NR-022 — The minimum viable Stable Core

**Status:** DECISION-READY. No implementation performed; no model moved.
**Method:** cached 829-class ownership scan + a new deterministic `create_table`
parse of the whole migration chain (`created_tables.json`, 419 tables). No
repository-wide rescan.

## 1. The measurement that reframes NR-022

Foreign-key references were counted across `app/` to find what the codebase
actually depends on, then each candidate was checked against **`op.create_table`
in the migration chain** — not merely "the name appears in a migration", which
matches foreign-key references and gives false positives.

| Rank | Table | FK refs | Physically created? |
| --- | --- | ---: | --- |
| 1 | `national_practitioners` | 88 | **NO** |
| 2 | `national_citizens` | 77 | **NO** |
| 3 | `labs` | 76 | yes — `20250322_0000` |
| 4 | `national_facilities` | 66 | yes — `20260813_0004` |
| 5 | `national_patients` | 63 | **NO** |
| 6 | `lab_users` | 56 | yes — `20250322_0000` |
| 7 | `niam_accounts` | 36 | yes — `20260723_0001` |
| 8 | `niam_organizations` | 35 | yes — `20260723_0001` |
| 9 | `national_encounters` | 35 | **NO** |
| 10 | `niam_persons` | 28 | yes — `20260723_0001` |
| 11 | `patients` | 24 | yes — `20250322_0000` |

**NR-022's headline needs a correction and gains a sharper one.** It is recorded
as "four of the five most-depended-on tables do not exist". Three of the top five
do not exist. The more precise and more serious statement is:

> The four most-depended-on **National Core** concepts — practitioner, citizen,
> patient, encounter — are all unbuilt, and **263 foreign-key references point
> at tables no migration creates.**

Across the whole chain, 419 tables are physically created against 828 ORM-mapped.

## 2. The structural finding: there are two Cores

**The built Core** — what the platform actually runs on:

| Concept | Table | Owner | PK | Tenancy |
| --- | --- | --- | --- | --- |
| Tenant | `labs` | `models.lab.Lab` | `INTEGER` | — (is the tenant) |
| Legacy actor | `lab_users` | `models.lab_user.LabUser` | `INTEGER` | `lab_id` |
| Account | `niam_accounts` | `identity.models.account.Account` | ULID | — |
| Person | `niam_persons` | `identity.models.person.Person` | ULID | — |
| Organization | `niam_organizations` | `identity.models.niam_organization.NIAMOrganization` | ULID | — |
| Facility | `national_facilities` | `models.clinical_scope.NationalFacility` | `VARCHAR(26)` | — |
| Lab patient | `patients` | `models.patient.Patient` | `INTEGER` | `lab_id` |

**The declared Core** — what the dependency graph points at, none of it built:
`national/domain/{practitioner,citizen,patient,encounter}.py`, all ULID-keyed on
`NationalBase`.

The platform runs on one Core while its foreign keys name another. That is the
whole of NR-022, stated structurally.

## 3. Recommended Stable Core — five concepts, and no more

The Core is deliberately **the built one**. It is small because everything in it
must satisfy every rule below; anything that cannot is a domain concept.

| # | Concept | Canonical owner | Persistence owner |
| --- | --- | --- | --- |
| 1 | **Account** (authN subject) | `identity.models.account.Account` | `niam_accounts` |
| 2 | **Person** (natural person) | `identity.models.person.Person` | `niam_persons` |
| 3 | **Organization** | `identity.models.niam_organization.NIAMOrganization` | `niam_organizations` |
| 4 | **Facility** | `models.clinical_scope.NationalFacility` | `national_facilities` |
| 5 | **Tenant** | `models.lab.Lab` | `labs` |

Per-concept boundaries (the ten dimensions), stated once because they are
uniform — which is the point of a Core:

- **Identity strategy.** ULID `String(26)` for 1–4. `labs` is `INTEGER` and is
  the one exception, grandfathered by `20250322_0000` (immutable bootstrap).
  Core identifiers are opaque and public; internal integer keys must never
  appear on a public surface.
- **API/read boundary.** Core is readable by any domain through its owner
  module. No domain may re-map a Core table — enforced today by
  `test_canonical_table_ownership.py` (828/828, empty ledger).
- **Mutation boundary.** Only the owning module writes. Domains reference by
  foreign key and never insert.
- **Authorization boundary.** Identity Platform (NIAM) is the single trusted
  provider; no subsystem implements its own authN/authZ. Consent gating for
  citizen-subject reads goes through the canonical consent store (NR-060).
- **Audit requirement.** Every Core mutation writes to the hash-chained
  `AuditLog`. Core is where identity and scope are decided, so unaudited Core
  writes are unreconstructable.
- **Tenancy rule.** **Core entities are not tenant-scoped.** `labs` *is* the
  tenant; facility, organization, person and account are cross-tenant by nature.
  Tenant scoping belongs to domain rows that reference them (`lab_id` on
  `patients`, `lab_users`). This is the rule NR-060's contradiction C-3 needs:
  consent about a citizen is national (`consents`, no `lab_id`), consent about a
  lab's handling of a patient is tenant-scoped (`trust_consent_records`).
- **Event boundary.** Core emits through the existing Outbox
  (`services/outbox_service.py`); it does not consume domain events.
- **Dependency direction.** Domains → Core, never the reverse. **Already true
  and worth keeping:** `national_facilities` has six columns and no outbound
  foreign key; it is a sink.

## 4. Deliberately NOT in the Core

- **Patient / Citizen subject.** `patients` (built, `INTEGER`, `lab_id`),
  `national_patients` (unbuilt) and `national_citizens` (unbuilt) are three
  answers to "who is the subject". Choosing between them is a data decision with
  migration consequences and is **the decision NR-022 actually needs**. Putting
  any of them in the Core before that decision would pick a winner by accident.
- **Practitioner.** 88 references, unbuilt, and the single highest-weight
  concept in the repository. Phase 3.
- **Encounter.** NR-051 named `national/workflow_runtime` and the encounter
  owner already; it is a clinical-episode concept, not identity, and the
  frontend already reads `/national-data/encounters` (NR-054).
- Everything else. A Core that grows is not a Core.

## 5. Contradictions

| # | Contradiction |
| --- | --- |
| K-1 | 263 foreign keys name four tables no migration creates. |
| K-2 | Two identifier schemes inside the proposed Core: `labs`/`lab_users`/`patients` are `INTEGER`, everything else ULID. Already recorded as NR-025. |
| K-3 | Two Person-like concepts are built and populated differently: `niam_persons` (identity) and `patients` (LIMS). No mapping is declared between them. |
| K-4 | `national_facilities` is Core and built, but its ULID key is referenced by domains that key on `INTEGER`, so joins cross identifier schemes. |

## 6. The decision this map asks for

Exactly one, and it unblocks the rest:

> **Is the canonical data subject `patients` (built, lab-scoped, integer) or a
> national citizen/patient record (unbuilt, ULID, cross-tenant)?**

- Choosing **`patients`** means the National Core is retired as a design, 263
  foreign keys are re-pointed, and `national/domain/` becomes a read model.
- Choosing **national** means building four tables plus a backfill and a dual-
  read period, with `patients` demoted to a lab-local projection.

Both are irreversible in the data. Neither is derivable from the repository,
which is why this document stops here rather than implementing one.

## 7. Status

**DECISION-READY.** No code changed, no model moved, no migration written. The
`create_table` parse is cached at `created_tables.json` for Phases 3 and 5.
