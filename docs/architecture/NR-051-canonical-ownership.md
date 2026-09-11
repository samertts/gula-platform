# NR-051 Canonical Ownership

Measured at `c1352b47`. Evidence is a single cached AST pass over every
`__tablename__` in `backend/app/` — 829 ORM classes, 828 distinct tables — plus
the application's own 1787-path OpenAPI schema. No repeated full scans.

## 1. Executive Summary

NR-051 was recorded as "six reusable concepts have 2–4 implementations and no
canonical owner". Measured against the persistence layer, **that framing
overstates the problem and mislocates it**.

**829 ORM classes mapped 828 distinct tables. Exactly one table had two ORM
owners.** At the layer that decides truth — who writes the row — GULA was
already 827/828 canonical. That one exception was NR-006, and §23 records how it
was closed in the same work: **the persistence layer is now 828/828, with no
declared exceptions.**

What NR-051 was counting was not competing owners. It was:

1. **tables within one owner** (notification ×4 are all `niam_notif_*` in
   Identity; workflow ×7 are all `national_workflow_*` in the national
   platform),
2. **projections** (53 tables under `hd_`, `dw_`, `dp_` — warehouse, ODS and
   MDM copies that are supposed to be derived), and
3. **different concepts sharing an English word** — the registered
   `…/providers` paths are AI, payment and federation *service* providers, not
   practitioners; `/lims/storage` is refrigerators, not object storage.

Three concepts remain genuinely contested; the one defect that was provable
is fixed.

## 2. Canonical Ownership Principles

A canonical owner has one authoritative model, one persistence owner, one
mutation path, one read boundary, one identity strategy, one audit boundary,
one tenancy rule. Projections, caches, FHIR representations and analytics
copies may exist — they must never become competing sources of truth.

The operational test used throughout this document: **what does the physical
schema say?** An ORM class that maps columns the database does not have is not
a rival owner. It is a fiction, and the migration settles the question.

## 3–5. Structure: Core, Domains, Projections

| role | tables | who |
| --- | ---: | --- |
| Core / legacy LIMS (unprefixed, `models/`) | 64 | `app/models/` — patients, facilities, organizations, consents, audit_logs, lab_orders, lab_results |
| Identity platform (`niam_`) | 87 | `app/identity/` |
| National platform (`national_`, `ref_`) | 110 | `app/national/` |
| Domains (`clinical_`, `lims_`, `pharmacy_`, `ins_`, `pay_`, `cc_`, `ehr_`, …) | 347 | ~15 domain packages |
| **Projections** (`hd_`, `dw_`, `dp_`) | **53** | `health_data`, `national_data` — derived, not sources |
| Other unprefixed domain tables | 168 | radiology, blood_bank, nursing, hospital, critical_care, ems, … |

The prefix convention is consistent enough to be load-bearing, and it is the
cheapest available ownership signal. That is worth preserving deliberately.

## 6–21. Ownership by concept

| concept | canonical owner | status | evidence |
| --- | --- | --- | --- |
| Patient / Person | `app/models/patient.py` → `patients` | **CONFIRMED** | 1 table, 1 owner |
| Notification | Identity / NIAM → `niam_notif_*` | **CONFIRMED** | 4 tables, all one domain — not four owners |
| Workflow | `national/workflow_runtime` → `national_workflow_*` | **CONFIRMED** | 7 tables, all one domain |
| Encounter | `national/domain/encounter` → `national_encounters` | **CONFIRMED** | others are projections (`hd_*`) or a primary-care subset (`cc_*`); NR-054 already bound the UI here |
| FHIR resource | `capabilities/fhir_interoperability` → `fhir_resource_records` | **CONFIRMED** | sole implementation, migration `20260815_0019` |
| Organization | Identity (`niam_organizations`) vs core (`organizations`) vs national | **PROBABLE — Identity** | 3 of 6 tables are Identity's; `hd_mdm_organization_index` is a projection |
| Terminology | `clinical/` → `clinical_code_systems`, `clinical_terminology_*` | **PROBABLE** | 6 of 10 tables; `ref_fhir_terminology` and `dp_terminology_registry` are reference/projection |
| Document | `national/document_platform` | **PROBABLE** | 5 of 10; `docint_*` is OCR/extraction *over* documents; `lims_report_attachments`, `cc_referral_attachments`, `ehr_clinical_attachments` are domain-local link tables, not rival stores |
| Practitioner / Provider | **none** | **CONFLICTED — three different concepts** | `ins_*` (5) are insurance *network* providers; `pay_providers`/`fin_providers` are payment providers; `national_practitioners` is the only practitioner registry |
| Consent | — | **CONFLICTED** | 7 tables across 6 domains: `niam_consents`, `niam_lifecycle_consents`, `consents`, `trust_consent_records`, `rp_consent_records`, `dp_consent_directives`, `national_consents` |
| Audit | `models/audit_logs` (hash chain) + per-domain append-only logs | **PROBABLE, needs a rule** | 16 tables across 8 domains; most are legitimately domain-scoped event logs, not rival audit trails |
| Facility | `models.clinical_scope.NationalFacility` | **RESOLVED BY EVIDENCE — see §23** | the physical schema settles it |
| Search / Storage / Reporting | **none — gaps, not duplicates** | per NR-050 | no generic implementation exists to own |

## 22. Duplicate concepts — what is actually duplicated

Only **consent** and **practitioner/provider** are genuine multi-owner
conflicts. Everything else previously counted as duplication is a projection, a
domain-local association, a within-owner table family, or a homonym.

## 23. Conflicting owners — `national_facilities` — RESOLVED AND EXECUTED

The one table with two ORM owners, open as **NR-006** since BATCH-2:

| | `models.clinical_scope.NationalFacility` | `national.domain.facility.Facility` (retired) |
| --- | --- | --- |
| columns mapped | 6 | 28 |
| of those, not physically created | 0 | **24**, three of them NOT NULL |
| physical columns omitted | 0 | 2 (`facility_code`, `status`) |
| unique | `facility_code` | `code` — a column that does not exist |
| matches the migration? | **yes** | **no** |

`20260813_0004_clinical_ehr_scope_bridge.py` creates the table with exactly the
first shape. The second mapped **24 columns that do not physically exist** — the
register's earlier figures of 18 and 8 were both undercounts, because neither
included what `AuditEntity` contributes. Any query through it raises
`UndefinedColumn`, and its `facility_type NOT NULL` could never be satisfied.

**This is not a preference between two designs. One of them cannot execute.**

### What made it latent, and what did not

`Facility` had **zero consumers**. Every `Facility` import in the repository
resolves to `app.models.organization.Facility`, which maps the unrelated
`facilities` table; the national one was named only by its own package
`__init__`. So no request path could reach it.

`create_all` could, and did. Three test modules build `NationalBase.metadata`
directly, so the suite was creating a `national_facilities` that no deployment
has. Nothing was written against that shape yet — but the next test to do so
would have passed locally and been wrong in production. That is the same failure
mode as NR-026, NR-032 and NR-034, waiting on an author rather than on a bug.

### The repair

`NationalBase.metadata` still has to carry `national_facilities`: **14 tables in
it hold a foreign key to that id** and would not resolve otherwise. That is a
requirement for a *table*, not for an *entity*. So the mapped class is replaced
by a bare `sqlalchemy.Table` mirroring the physical schema column for column.

- the 14 dependent foreign keys still resolve;
- `create_all` now builds the migration's shape, verified against it;
- `models.clinical_scope.NationalFacility` is the **sole ORM owner**, so nothing
  else in the codebase can write a facility row;
- no migration, no schema change, no data movement — the table was always
  correct; one of its two ORM views was not.

Held by `backend/tests/test_canonical_table_ownership.py`, whose exception ledger
is now **empty**: the rule holds across all 828 tables with no declared
exceptions. Negative-proven in both directions — reintroducing a second mapper
fails two tests, drifting the anchor by a single column fails a third.

## 24–26. Schema / API / identifier conflicts

- **Schema:** one, above. The other 827 tables have a single ORM owner.
- **API:** the `…/providers` homonym is the significant one — three unrelated
  concepts under one word across `ai`, `payments`, `insurance` and `niam`.
- **Identifier:** core uses `String(26)` ULIDs and `Integer` keys; the national
  platform uses `String(26)`; projections carry their own surrogate keys. No
  single identifier strategy spans the three. That is the substance of NR-022.

## 27–28. Dependency and migration order

```
Identity (niam_)            ← no upstream dependency
  └── Organization, Account, Person
National platform           ← depends on Identity
  └── Facility, Encounter, Workflow, Document, Reference data
Core / models               ← depends on neither; predates both
  └── Patient, Lab order, Result, Audit chain
Domains                     ← depend on Core + National
Projections (hd_, dw_, dp_) ← depend on everything; must never be written to directly
```

Migration order for any consolidation: Identity → National → Core → Domains →
Projections. Consent and practitioner cannot be consolidated before NR-022
settles the Core/National boundary, because both concepts straddle it.

## 29. NR-050 mapping

This resolves two of NR-050's three BLOCKED dispositions:

| NR-050 capability | was | now |
| --- | --- | --- |
| `workflow_engine` | BLOCKED on NR-051 | **CONSOLIDATE** onto `national/workflow_runtime` — owner CONFIRMED, sole persistent owner, 7 tables one domain |
| `document_management` | BLOCKED on NR-051 | **CONSOLIDATE** onto `national/document_platform` — owner PROBABLE; `docint_*` is processing, not storage |
| `healthcare_consent` | BLOCKED on NR-051 | **still BLOCKED** — consent is genuinely contested across 6 domains |

## 30. NR-022 dependencies

National Core cannot be scoped until consent ownership and the identifier
strategy are settled. Core should own: Identity, Account, Person, Organization,
Authorization, Audit, Consent, Reference Data, Terminology, Events. It should
**not** own Facility, Encounter, Document or Workflow — those have working
owners already, and moving them into Core would be growth for its own sake.

## 31. Open decisions

1. **Consent ownership** — 7 tables, 6 domains. The only remaining NR-050 blocker.
2. **Practitioner registry** — `national_practitioners` is the sole candidate;
   confirm the insurance/payment homonyms stay separate.
3. **Identifier strategy across Core/National** — NR-022.
4. **Audit rule** — which of the 16 audit tables must chain to the canonical log.

## 32. Recommended target architecture

Keep the shape that already exists, and make it explicit rather than
rearranging it:

```
Identity platform   — people, accounts, organizations, consent preferences
National platform   — facility, encounter, workflow, document, reference data
Core (models/)      — patient, order, result, the audit chain
Domains             — clinical behaviour over Core + National primitives
Projections         — derived, read-only, never a source
```

The persistence layer is already 827/828 canonical. The work is not a
re-architecture; it is resolving two contested concepts, one provable defect,
and writing the boundary down so it stops eroding.

## Evidence

| claim | method |
| --- | --- |
| 829 classes / 828 tables / 1 duplicate | single AST pass over `app/**/*.py` |
| `national_facilities` physical shape | `20260813_0004_clinical_ehr_scope_bridge.py` |
| both facility models dormant | import grep across `app/` |
| concept → table → domain | cached scan, re-queried without rescanning |
| provider homonyms | 1787-path OpenAPI schema from `create_app()` |

## Confidence

**HIGH** for the structural finding (now 828/828), the NR-006 resolution, and the
workflow/notification/encounter/FHIR owners — all measured.
**MEDIUM** for document, organization, terminology and audit — evidence points
one way, no rival has been excluded by test.
**LOW, and therefore still blocked,** for consent.
