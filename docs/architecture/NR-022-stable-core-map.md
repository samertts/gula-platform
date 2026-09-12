# NR-022 — The minimum viable Stable Core

**Status:** RECOMPUTED after Units 1-4. The decision §6 asked for has been taken,
and taken differently from how §6 framed it. No implementation performed; no
model moved. Sections marked **[Unit 5]** supersede what they replace.
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

**[Unit 5] The 263 is almost entirely latent, and that changes what it asks for.**
Unit 2 measured where those references *live*, not just where they point:
**261 of the 263 sit in owner tables that are themselves unbuilt.** The complete
live surface is two columns, both on `niam_citizen_relationships`:

```
niam_citizen_relationships.citizen_id -> national_citizens
niam_citizen_relationships.patient_id -> national_patients
```

So this is not 263 foreign keys waiting to be re-pointed. It is two live
references and 261 declarations inside a schema that was never built. Tracing
the two found NR-064: the only write path in that workflow queries both absent
tables and reports the failure as a generic 500.

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

- **Patient / Citizen subject.** **[Unit 5] Settled, and they stay out.** The
  approved decision rejects a universal data subject: Person is the canonical
  national subject, and Patient and Citizen are contextual roles over it. So
  there was never a winner to pick — Person is already Core concept #2, and
  Patient and Citizen are domain relationships that reference it. Their 138
  references (75 CITIZEN, 63 PATIENT) are classified and held by
  `test_subject_reference_semantics.py`.
- **Practitioner.** **[Unit 5] Settled by NR-061, and it stays out.** A
  practitioner is a Person holding a ProfessionalLicense and an Employment —
  `niam_persons` + `niam_licenses` + `niam_employments` + `niam_assignments`,
  all built. 15 of `national_practitioners`' 21 columns map onto that
  composition and the 6 that do not are additive columns on tables that already
  exist. **No practitioner table is required by reachable behaviour: 0 of the 57
  practitioner references live in a built table.** Adding a Practitioner Profile
  concept to the Core would create a second registry of natural persons, which
  is the one thing the decision forbids.
- **Encounter.** **[Unit 5] Correction:** the ORM owner is
  `app/national/domain/encounter.py`, not `national/workflow_runtime` as stated
  here previously. The conclusion is unchanged — it is a clinical-episode
  concept, not identity, its 35 references are classified ENCOUNTER, and the
  frontend already reads `/national-data/encounters` (NR-054).
- Everything else. A Core that grows is not a Core.

## 5. Contradictions

| # | Contradiction |
| --- | --- |
| K-1 | 263 foreign keys name four tables no migration creates — but **[Unit 5]** 261 of them sit in owners that are themselves unbuilt, so only two are live. |
| K-2 | Two identifier schemes inside the proposed Core: `labs`/`lab_users`/`patients` are `INTEGER`, everything else ULID. Already recorded as NR-025. |
| K-3 | Two Person-like concepts are built and populated differently: `niam_persons` (identity) and `patients` (LIMS). No mapping is declared between them. |
| K-4 | `national_facilities` is Core and built, but its ULID key is referenced by domains that key on `INTEGER`, so joins cross identifier schemes. |
| K-5 | **[Unit 5]** The one live Core-adjacent reference is broken: `POST /admin/citizen-relationships` is registered and queries two unbuilt tables (NR-064). The Core's own tables are fine; the first thing built on top of them is not. |
| K-6 | **[Unit 5]** §3 requires every Core mutation to reach the hash-chained `AuditLog`. That requirement is stated, not yet measured per endpoint: NR-062's corrected measurement shows 328 mutating endpoints in packages with no audit call and 1065 in modules with none, and "the package audits somewhere" does not prove a Core write audits. The Core is not among the unaudited packages, which is weaker than a proof. |
| K-7 | **[Unit 5]** Building anything adjacent to the Core now has two preconditions that did not exist when this map was written: NR-063 (no table may be built while its create path splats an unvalidated body) and NR-065 (no table may be built without tenancy and audit). Both are latent today and both gate the National Core work. |

## 6. [Unit 5] The decision was taken — and the question was wrong

This section asked for a choice between `patients` and a national subject
record. The approved decision **rejects the binary**:

> Canonical national identity subject = Person/Identity. Patient and Citizen are
> contextual roles and relationships, not replacements for Person. Do not bulk
> re-point all 263 foreign keys to one table.

That is a better answer than either branch offered, and it dissolves the
irreversibility both branches carried. Person is already Core concept #2 and
already built. Nothing is re-pointed in bulk; each reference is classified by
what it actually means, and the transition per class is additive — add,
backfill, validate, shadow-read.

The measured classification of all 263 (Unit 1):

| Class | Count | Resolves to |
| --- | ---: | --- |
| CITIZEN | 75 | portal/registry relationship over Person |
| PATIENT | 63 | clinical-domain subject |
| PRACTITIONER | 57 | the NR-061 composition, not a table |
| ENCOUNTER | 35 | clinical episode; not a subject at all |
| PERSON (actor) | 11 | canonical Person |
| ASSIGNMENT | 11 | `niam_assignments` |
| REVIEW | 9 | undecidable from the column name; named individually |
| PERSON (kin) | 2 | canonical Person |

Zero unclassified. The nine REVIEW sites could not be decided from their call
sites, and the reason became NR-063: those call sites are generic
`Model(**data)` passthroughs that never set the column at all.

**What still is not derivable from the repository**, and is therefore still open:

1. The nine REVIEW sites need clinical intent — does `verified_by` on a
   self-monitoring record require licensure?
2. NR-059 §5: does national task and workflow orchestration ship, or is it
   retired? NR-065 establishes that "ship" is not one migration either way.

Both are product questions. Neither blocks the Core, which is why this map is no
longer waiting on them.

## 7. Status

**[Unit 5] RECOMPUTED, and now held mechanically.** No code changed, no model
moved, no migration written. The `create_table` parse is cached at
`docs/architecture/evidence-created-tables.json`; the reference classification at
`evidence-subject-fk-classification.json`.

Two of this map's claims are no longer prose. `test_stable_core_invariants.py`
asserts that every Core concept is still built, that each has exactly one ORM
owner in the module named in §3, and that **nothing in the Core references a
table outside the Core and outside the Identity Platform substrate** — domains
reference Core, never the reverse. `labs`, `niam_persons` and
`national_facilities` declare no outbound foreign key at all; `niam_accounts`
references `niam_identities` and `niam_organizations` references itself, both
inside NIAM.

The rest of §3 — mutation boundary, authorization boundary, audit requirement —
remains a stated rule rather than a measured one, and K-6 says so.
