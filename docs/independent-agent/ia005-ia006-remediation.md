# IA-005 and IA-006 — remediation

Independent lane (`claude/independent-audit-1`), worktree `/home/user/gula-audit`.
Follows RB-3 (`09250cd0`). RB-4, RB-5 and RB-6 not started.

**Outcome in one line:** IA-005 is **RESOLVED** with a mapper-driven fix across 12
ORM bases, proven by a regression test that fails before and passes after.
IA-006 is **NOT resolved and must not be**: the evidence is an accepted ADR that
forbids the very tables a migration would create. **Zero migrations were authored.**

---

# Part 1 — IA-005 (P0): resolved

## 1.1 Root cause

`shared/models/base.py:36` serialised by **physical column name**:

```python
for col in self.__table__.columns:
    val = getattr(self, col.name)          # ← the defect
    ...
    result[col.name] = val
```

A declarative class already owns the attribute `metadata`: SQLAlchemy puts the
base's `MetaData` registry there. A model needing a *column* called `metadata`
must therefore map it under a different Python name. So `getattr(self, "metadata")`
returned the registry — 577 tables — and `jsonable_encoder` walked it until the
stack was exhausted.

Confirmed by measurement, not inference:

* the column name is `metadata`; the mapped attribute is `metadata_` (132 models)
  or `extra_metadata` (5 models);
* `type(AllergyIntolerance.metadata).__name__ == "MetaData"`, and it **is**
  `SHARED_METADATA`;
* encoding one real record key-by-key, the only key that recursed was `metadata`;
* frame census on `POST /ehr/allergies`: 1 052 frames, 486 + 484 of them
  `fastapi/encoders.py:307` / `:356`.

## 1.2 The serialization contract, established before patching

| question | evidence | answer |
|---|---|---|
| how should `to_dict()` key its output? | all 12 ORM bases use `result[col.name]` | **physical column name** — so the external field is `metadata` |
| do responses expose `metadata` or `metadata_`? | keyed by `col.name` | **`metadata`**, and it must stay that way |
| do serialization aliases/schemas already exist? | no Pydantic response aliases found; `/ehr` *request* schemas accept `metadata_` inbound (`routes/ehr.py:77,89,232,…`) | no response aliasing; the inbound asymmetry is pre-existing and **left unchanged** |
| does anything depend on the current behaviour? | 13 sites in `national/*/infrastructure/repository.py` already do `model.metadata_ = domain.metadata` — correct code knows the attribute name | **nothing depends on receiving the registry**; the only code that consumed it crashes (§1.7) |
| how many mapped models carry the column? | full registry sweep with the app assembled | **137 tables / 137 models**; 119 have a `to_dict()` |
| which endpoints serialize them? | RB-3 probe + AST | 59 of 86 `/ehr` operations; the wider route population is measured only for `/ehr` |

**Correction to RB-3:** RB-3 reported **124** tables. That counted only
`SHARED_METADATA`. With every registry walked and the app fully assembled the
figure is **137**. The RB-3 direction and severity stand; the count was low.

A decisive generality check: across all **780** mapped classes, `metadata` is the
**only** physical column name that differs from its mapped attribute key, and no
column is unmapped. A mapper-driven fix therefore touches exactly the affected
models and changes nothing else.

## 1.3 Two false leads, killed by reading

`integration/base.py::UplinkBase.to_dict()` and `research_platform/research.py`
both hard-code `"metadata": self.metadata`, which looks identical to the defect.
Both classes are **dataclasses**, so `.metadata` is a genuine field. Not defects.

Likewise `governance/identity_governance.py::IdentityRecord` and
`rules_engine/domain/entities.py::RuleDefinition` — both dataclasses — and
`document_intelligence/.../wiring.py:602` (`field.metadata` on a domain object).

## 1.4 The fix

One canonical implementation in `shared/models/base.py`; the other 11 bases
delegate to it. Mapper-driven, with no special case for the name `metadata`:

```python
def serialize_columns(instance, *, redact=None) -> dict[str, Any]:
    attr_by_column: dict[str, str] = {}
    for attr_key, column in sa_inspect(type(instance)).columns.items():
        attr_by_column.setdefault(column.name, attr_key)

    result: dict[str, Any] = {}
    for col in instance.__table__.columns:
        if redact is not None and redact(col.name):
            result[col.name] = "[REDACTED]"
            continue
        attr_key = attr_by_column.get(col.name)
        val = getattr(instance, attr_key) if attr_key is not None else None
        if isinstance(val, datetime):
            val = val.isoformat()
        result[col.name] = val
    return result
```

It satisfies each constraint:

* **retrieves the mapped attribute** — through `sa_inspect(...).columns`, so
  `extra_metadata` resolves as readily as `metadata_`;
* **never returns the registry** — the value comes from the mapper key, never
  from `col.name`;
* **preserves the external field name** — the key is still `col.name`;
* **changes nothing unrelated** — `metadata` is the only mismatched name in 780
  models, so every other key/value pair is byte-identical;
* **keeps `identity/base.py`'s redaction** — passed in as `redact=_is_sensitive_column`;
* an unmapped column would yield `None` rather than a class attribute. None exist
  today; this is defensive, and it keeps the payload's shape either way.

Files changed: 14. Net **−21 lines** (12 duplicated loops became one).

| base | to_dict now |
|---|---|
| `shared/models/base.py` | `serialize_columns(self)` (canonical) |
| `app/{care_continuum,clinical,control_plane,governance,health_data,national,nursing,pharmacy,radiology,trust}/base.py` | `serialize_columns(self)` |
| `app/identity/base.py` | `serialize_columns(self, redact=_is_sensitive_column)` |

Six of those bases had no affected model today; they carried the identical
defective loop, so they were included to stop it recurring.

## 1.5 Tests — written before the fix

`backend/tests/verification/test_orm_metadata_column_serialization.py`, 13 tests,
dialect-free (`to_dict()` needs no database):

* the defect: metadata column returns its value; payload is JSON-encodable;
* the aliased spelling (`extra_metadata`) — this is what forbids a hard-coded
  `metadata_` special case;
* `None` metadata; JSON-serializable metadata (`{"k": "v"}`);
* no `MetaData`, `Table` or `SchemaItem` anywhere in a payload, checked recursively;
* a model **without** the column is byte-identical;
* ordinary columns keep their values; no key added or dropped; keys are exactly
  the physical column names;
* the real platform population (a guard asserts it is >100, so the sweep cannot
  pass vacuously);
* three real EHR models — `AllergyIntolerance`, `ClinicalNote`, `ConditionRecord`.

## 1.6 Regression results

| stage | result |
|---|---|
| baseline, before the fix | **9 failed**, 4 passed |
| after the fix | **13 passed** |
| perturbation — one line back to `getattr(instance, col.name)` | **9 failed**, 4 passed |
| restored | **13 passed** |

The 4 that pass throughout are the no-collateral-change and population guards,
which must hold in both states. The test discriminates on exactly the line that
matters.

Wider evidence:

| check | result |
|---|---|
| every affected model with a `to_dict()` | **119 / 119** serialise safely and JSON-encode; 0 failing |
| any `MetaData`/`Table`/`SchemaItem` in any payload | **none**, checked recursively |
| RB-3 `/ehr` code-path probe, 86 operations | `RecursionError` **27 → 1**; `200` **8 → 35**; the remaining 1 is the known harness limitation (NIAM tables absent from the scratch SQLite) |
| seeded-record probe | `GET /ehr/allergies/{id}` and `/patients/{pid}/allergies`: `RecursionError` → **`200`** with `metadata = None`, i.e. the column value |
| `tests/verification/` + `tests/independent/` | **104 passed, 145 skipped, 0 failed** |
| full backend suite `pytest tests/ -q` | **1 failed, 2846 passed, 185 skipped** (318 s) |

The single failure is `test_single_import_path.py::test_no_module_is_loaded_under_two_names`
— my own NR-087 guard — and it is **pre-existing, not a regression**. It passes in
isolation, fails in the assembled suite because the kernel tests load
`backend.app.integration.connectors.ntfy` under a second name, and **fails
identically with the IA-005 change stashed**. The stash was popped and the fix
re-verified green (13/13) afterwards.

Also recorded because it limits every suite number above: `tests/conftest.py:28`
overwrites `DATABASE_URL` with `sqlite:///:memory:` unconditionally, so **the
backend suite is SQLite evidence, not PostgreSQL**. Passing a real PostgreSQL URL
does not override it — it hung the run, and that run is void (ENVIRONMENT, not a
code defect).

## 1.7 IA-007 (P1) — found while establishing the contract, not fixed here

`app/insurance/financial/engine.py:840-842`:

```python
metadata = claim.metadata or {}          # ← the MetaData registry (truthy)
metadata["invoice_number"] = invoice_number
claim.metadata = metadata                 # ← never reaches the column
```

`InsuranceClaim` maps table `ins_claims`, whose physical `metadata` column is
mapped as `extra_metadata`. Executed:

```
TypeError: 'MetaData' object does not support item assignment
```

So `generate_invoice()` raises before it returns, and `batch_invoices()` with it.
The fix is two identifiers (`claim.extra_metadata`), but invoice generation is
billing logic, which `CLAUDE.md` puts behind human approval. **Left OPEN with the
patch specified.** IA-005's fix does not touch it — direct attribute access never
goes through `to_dict()`.

A systematic AST sweep for the same shape found 13 other candidate sites; all 13
are **correct** (`model.metadata_ = domain.metadata` in the national repositories).
IA-007 is this one site.

## 1.8 Remaining risks

* 18 affected models have **no** `to_dict()`; they are unaffected by this path but
  would be exposed if one were added. The new test's population sweep covers only
  models that have one.
* Route-level exposure was measured for `/ehr`. How many non-`/ehr` routes
  serialise an affected model is **still UNKNOWN** — the 119-model check proves the
  serializer, not each route.
* Any code reading `.metadata` directly on an affected instance is still wrong.
  IA-007 is the one live instance found; the sweep was AST-based over `app/` and
  could miss dynamic access (`getattr(obj, "metadata")`).
* The inbound/outbound asymmetry (`metadata_` in, `metadata` out) is untouched and
  remains a latent confusion for API clients.

---

# Part 2 — IA-006 (P1): not resolved, and not resolvable by implementation

## 2.1 Why no migration was authored

The instruction was to determine intended ownership and release status before
authoring anything. Doing so produced evidence that **forbids** the migrations.

**`docs/adr/ADR-016-national-ehr.md` — Status: Accepted, 2026-07-15, Engineering
Lead + Architecture Committee + CTO. Not superseded** (no ADR in `docs/adr/`
carries a supersession marker for it; the only "superseded" mention in that file
is about FHIR R4 versions).

It says, four times and unambiguously:

* Decision: *"reuses existing GULA clinical, FHIR, and data models as its
  foundation **rather than creating a separate EHR database**. The EHR is a logical
  and API layer, **not a data silo**."*
* Constraint: *"**Must not duplicate or replace existing GULA database tables** —
  EHR must be a logical layer over existing data."*
* Requirement: *"**Zero duplication** of existing GULA clinical data."*
* Consequence: *"**Zero database duplication — No new EHR tables**; all data
  remains in its existing canonical location."*

Corroborating, not contradicting: ADR-017, ADR-020 and ADR-022 all refer to the
EHR as an **API** that *provides* the longitudinal record — never as a schema.
And `docs/production/RELEASE_NOTES-v1.0.md` mentions the EHR **zero times**; v1.0
is an infrastructure release (Kubernetes, HA, observability, DR).

Authoring 18 `ehr_*` migrations would implement precisely the data silo an
accepted ADR forbids. That is not a judgement call this lane may take.

## 2.2 The real contradiction — ADR-016 is internally incomplete

This is the finding, and it is not "the code is wrong":

* ADR-016's implementation strategy, **Phase 2**: *"FHIR Condition, Medication,
  Immunization, Procedure resources; **write support**."*
* ADR-016 also mandates **no new EHR tables**.
* ADR-016 never says **where a newly authored clinical note, allergy or condition
  is persisted.** GULA's existing schema is lab-centric (`patients`,
  `lab_orders`, `lab_results`, `visits`); none of it can hold a clinical note.

So Phase 2 as written is unsatisfiable under the ADR's own constraint. `app/ehr/`
is a coherent implementation of Phase 2 that violates the constraint. Either the
constraint or the phase has to move. **That is the decision required, and it is
an architecture-committee decision, not an engineering one.**

## 2.3 Classification of all 19 missing tables

Classified on evidence — routers, `factory.py`, services, ORM models, migrations,
ADRs, release notes, runtime references — never on naming.

| missing table | class | served paths depending on it | evidence |
|---|---|---|---|
| `ehr_allergies` | **E** | 6 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_care_plan_activities` | **E** | 4 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_care_plan_goals` | **E** | 4 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_care_plans` | **E** | 9 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_clinical_attachments` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_clinical_notes` | **E** | 7 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_conditions` | **E** | 6 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_diagnoses` | **E** | 6 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_family_history` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_immunizations` | **E** | 6 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_medication_administrations` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_medication_dispenses` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_medication_requests` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_medication_statements` | **E** | 6 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_patient_timeline` | **C** | 1 | projection (`source_type`/`source_id`); **no writer anywhere in `app/`** — only queried at `ehr_service.py:1180-1188`; read-only route; ADR-016 permits materialised projections |
| `ehr_problem_list_items` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_risk_factors` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `ehr_social_history` | **E** | 3 | served + written through the API, but its existence contradicts ADR-016's *"No new EHR tables"* while ADR-016 Phase 2 mandates write support — the ADR never says where new clinical content persists |
| `national_patients` | **E** | reached by every patient-scoped route via `_get_patient`; **33 of 86** operations fail on it first | hub of **66 foreign keys**; `nhop-platform` owns `citizens` per CLAUDE.md; ADR-016 composes the Patient from `patients`/`lab_results`/`lab_orders`/`visits`, never from this table; also the silent arm of IA-004 |

**Totals: A = 0, B = 0, C = 1, D = 0, E = 18, F = 0.**

No table classifies **A** (required for Stable v1.0.0 and owned by GULA), because
no document places the EHR in v1.0.0 scope and the one accepted ADR forbids the
tables. **A is the only class that may receive a migration, and it is empty — so
no migration was authored.**

### Why each class was not given a table

* **C — `ehr_patient_timeline`.** A projection, not a source of truth
  (`source_type` + `source_id`). Nothing in `app/` ever writes it — the only
  references are a query at `ehr_service.py:1180-1188` plus imports. A projection
  with no projector is dormant. ADR-016 explicitly permits materialised views as a
  performance mitigation, so this table is *architecturally allowed* — but it is
  not required for v1.0.0 and would be empty if created. **Before its route can be
  REAL:** a projector must exist, driven by the source records, with a documented
  refresh contract.
* **E — the 17 clinical `ehr_*` tables.** Each is served and written through the
  API, and each contradicts §2.2. **Before their routes can be REAL:** ADR-016 must
  be amended (Phase 2 persists new clinical content in owned EHR tables) *or* the
  models retired and the routes mapped onto existing tables. Then, and only then,
  migrations.
  `ehr_clinical_attachments` is the strongest candidate for approval if the ADR is
  amended: it is a pointer store (`storage_path`, `storage_bucket`, `content_hash`,
  `mime_type`) for uploaded documents that exist nowhere else, so it duplicates no
  existing GULA data — it trips the literal "no new tables" clause, not the intent.
* **E — `national_patients`.** Treated separately, per instruction, because it is
  also implicated in IA-004. See §2.4.

## 2.4 `national_patients` — the decision required

Evidence:

* it is the hub of **66 foreign keys** across `ehr/`, `national/` and `identity/`
  — not a stray table;
* it itself references `national_citizens`, which is **also absent**;
* `CLAUDE.md` states `nhop-platform/` *"Owns the national citizen registry; GULA
  owns the per-lab LIMS view"*, and `nhop-platform/app/models/citizen.py` does own
  a `citizens` table in its own service;
* ADR-016 composes the EHR Patient from `patients`, `lab_results`, `lab_orders` and
  `visits` — **never** from `national_patients`;
* GULA already has `patients`, which is physically present in the head database;
* every patient-scoped `/ehr` route reaches it via `_get_patient`; **33 of 86**
  operations fail on it before touching their own table.

So there are three candidate patient identities — `patients` (GULA, exists),
`citizens` (nhop, exists in its own service), `national_patients` (GULA, exists
only as ORM). **The decision required:** does the GULA monolith host a national
patient registry at all?

* If **no** — `national_patients` is retired and the 66 FKs plus every
  `_get_patient` call are re-pointed at `patients`, with the national identity
  resolved across the nhop boundary. This is the reading most consistent with
  ADR-016 and `CLAUDE.md`.
* If **yes** — it needs an explicit owner, a migration, and a statement of how it
  reconciles with nhop's `citizens` and GULA's `patients` without becoming a third
  source of truth for patient identity.

**IA-004 was not modified.** Its migration
(`20260811_0002_citizen_relationship_foundation.py`) still skips the FK to
`national_patients` whenever the target is absent, silently. Whichever way the
decision goes, IA-004's silence is a separate defect and remains OPEN.

## 2.5 What was deliberately not done

* No migration authored — for any of the 19 tables.
* No ORM model deleted or archived.
* No physical table fabricated in any PostgreSQL database.
* No `/ehr` route disabled. RB-3's option 2 (gate the router behind a
  default-off flag so a fresh deployment stops advertising 86 operations it cannot
  serve) remains the smallest honest containment, but it is a served-surface change
  and needs the owner's decision, not this lane's.
* IA-004's migration and FK logic untouched.
* Alembic transaction semantics unchanged.

## 2.6 IA-006 acceptance, measured against the stated criteria

| criterion | state |
|---|---|
| every required Stable-v1.0.0 EHR table has an explicit schema owner | **not met** — no table is in v1.0.0 scope; ownership is contested by ADR-016 |
| every required table represented in the migration chain | **not met** — 0 of 19; correctly so, pending the decision |
| physical schema matches the ORM contract | **not met** |
| required indexes/FKs/constraints exist | **not met** |
| no EHR route depends on an unexplained absent table | **partially met** — every dependency is now *explained* and classified, but not removed |
| dormant/external routes explicitly controlled and documented | **documented, not controlled** — the router is still mounted unconditionally |
| runtime verification proves the affected routes work | **not met** |

**IA-006 therefore remains OPEN.** It is blocked on an architecture decision, not
on engineering effort.

---

# Part 3 — RB-3 re-classification after this work

Re-run against the proven head database (`gula_agent2`, head `20260916_0001`,
423 tables) after the IA-005 fix.

| class | before (RB-3) | after |
|---|---|---|
| REAL | 0 | **0** |
| PARTIAL | 1 | **1** |
| BROKEN | 53 | **53** |
| STUB / UNIMPLEMENTED / INTENTIONALLY_EXTERNAL | 0 | **0** |

**Unchanged, and that is the correct result.** IA-005 was never the reason the
surface fails against the head database; the absent tables are. The head-DB
outcome is still 85 × `500 UndefinedTable` + 1 × `403`, so no route has runtime
evidence of working and none may be called REAL.

What did change is what happens *once* the schema exists — measured on the
code-path probe, and reported as such rather than as a head-DB claim:

| | before | after |
|---|---|---|
| `RecursionError` | 27 | **1** (harness limitation, not a defect) |
| `200` | 8 | **35** |
| `404` (correct not-found branch) | 50 | 50 |

Against the 10-point acceptance criteria, for the affected routes: (1) authentication
and (2) authorization are as NR-070 recorded — authenticated, not authorized, which
is a separate open finding; (3) database query, (4) persistence, (6) audit,
(7) tenant isolation and (10) no serialization recursion cannot be verified against
the head database while the tables are absent; (5) response serialization is now
**verified fixed** at the serializer and at the code-path layer; (8) 404/403
behaviour is correct where observed; (9) no fake success — nothing was made to
return 200 with empty data.

Acceptance for RB-3 is explicitly *not* "no longer returns UndefinedTable", and
this work does not claim it. RB-3 stays **BROKEN 53 / PARTIAL 1 / REAL 0**.

---

# Part 4 — IA-004

**IA-004 remains OPEN and was not modified.**

---

# Part 5 — database

| | |
|---|---|
| database used | `gula_agent2` (the isolated audit database) |
| migration head | `20260916_0001` |
| physical tables | **423** |
| head database untouched | **yes** — verified before and after; 423 tables, same head, no rows added, no table created |
| other databases used | none. `gula_canon`, Account 1's database and the primary worktree were never touched |
| scratch databases | file-backed **SQLite** only, inside the session scratchpad, for the code-path probes |

---

# Part 6 — release assessment

No percentage.

**Release blockers still OPEN:**

| blocker | state |
|---|---|
| RB-1 | RESOLVED on the integration lineage; **still open on `claude/autonomous-run-1`**, which lacks commits `f92d4132` and `efcc4b6e` |
| RB-2 | Reconciled as inventory; **371 absent ORM tables still have no ownership statement**, and the 4 Category-G orphans none |
| RB-3 | **OPEN** — 53 BROKEN, 1 PARTIAL, 0 REAL of 54 served `/ehr` paths |
| RB-4 | **OPEN** — not started; 0 of 12 FHIR create types insertable (NR-085) |
| RB-5 | **OPEN** — not started; 15 of 15 nursing tables unwritable (NR-076) |
| RB-6 | **OPEN** — not started; CI has produced no real signal since 2026-09-24 (NR-136, sibling lane) |

**Findings OPEN after this work:** IA-004 (P1), IA-006 (P1), IA-007 (P1),
NR-085, NR-076, NR-136, plus the `/ehr` authorization gap recorded in NR-070
(115 routes authenticated but carrying no permission check).

**Findings CLOSED by this work:** IA-005 (P0).

Blocked on the owner, not on engineering: the ADR-016 Phase 2 contradiction, the
`national_patients` ownership decision, IA-004's fix, IA-007's billing-path patch,
and whether the `/ehr` router should stay mounted while its schema is absent.

---

*IA-005/IA-006 remediation complete. RB-4, RB-5 and RB-6 not started.*
