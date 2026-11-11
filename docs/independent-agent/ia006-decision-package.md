# IA-006 — architectural decision package

Lane `claude/independent-audit-1`, worktree `/home/user/gula-audit`, database
`gula_agent2` (head `20260916_0001`, 423 tables, untouched). No migration authored.
No ORM model deleted. IA-004 not modified. RB-4/RB-5/RB-6 not started.

**This document does not decide the architecture.** It assembles the evidence so one
person can decide in one sitting.

---

## 1. The decision is one question, not eighteen

Evidence reframes IA-006 substantially. The platform has **two FHIR R4 paths**, and
only one of them works.

| path | source tables | present in head DB | status |
|---|---|---|---|
| **A — lab-derived FHIR** `FHIRObservation.from_lab_result(result: dict, …)`, `FHIRDiagnosticReport.from_lab_order(order, results, …)` | `lab_results`, `lab_orders` | **yes** | **this is ADR-016 working as written** — a logical layer over existing data, no new tables |
| **B — clinical-content FHIR** 6 mappers importing `app.ehr.models` | the 18 `ehr_*` tables | **no** | cannot function |

Path A is proof that ADR-016's vision is implementable and partly implemented. Path B
is the part with no substrate.

So the question is **not** "should the EHR be a silo?". It is:

> **Does GULA persist clinical content it has never stored before — notes, allergies,
> immunizations, care plans, medication history, social history, risk scores — or does
> it expose FHIR only over the lab data it already has?**

Everything below serves that one question.

## 2. The blocking contradiction, stated precisely

`docs/adr/ADR-016-national-ehr.md` — **Accepted**, 2026-07-15, not superseded:

* Constraint: *"Zero database duplication — **No new EHR tables**."*
* Implementation strategy, **Phase 2**: *"FHIR Condition, Medication, Immunization,
  Procedure resources; **write support**."*
* The ADR never says where newly authored clinical content is persisted.

**Why the constraint cannot be satisfied as written.** The only physically present
clinical tables are lab-centric, and none has any column that could host clinical
content, nor a JSON extension point:

| table | columns | can it hold a note / allergy / immunisation / care plan? |
|---|---|---|
| `patients` | 16 — demographics + identity only | **no** |
| `lab_orders` | 12 — order lifecycle | **no** |
| `lab_results` | 16 — one test value | **no** |
| `visits` | 6 — `visit_type`, `status`, timestamps | **no** |

**STATIC VERIFIED** against the physical schema of `gula_agent2`.

So Phase 2 is unsatisfiable under the ADR's own constraint. Either the constraint or
the phase must move. That is the decision.

## 3. Lane-independence of this finding

Checked because the head database was built from a different lineage than this lane:

| | this lane (102 migrations) | integration lineage `ce097a0c` (112 migrations) |
|---|---|---|
| any migration creating an `ehr_*` table | **none** | **none** |
| any migration creating `national_patients` | **none** | **none** |

**INDEPENDENTLY VERIFIED across two lineages.** IA-006 is not an artefact of this
lane. (The one `ehr`-named migration in both is `clinical_ehr_scope_bridge`, which
creates the unrelated, present `clinical_ehr_*` binding tables.)

## 4. Decision matrix — all 18 tables

Columns map to the ten questions asked. (9) is uniform and stated after the table.

| # | table | (1) data represented | (2) writes | (3) reads | (4/5) canonical table that could hold it | (6/7) FHIR R4 target | FHIR mapper today | (8) lost if removed | (10) code assumes it exists |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `ehr_allergies` | Allergy / intolerance with criticality, severity, coded substance (ICD-10/SNOMED) + Arabic display | 3 | 3 | none | `AllergyIntolerance` | AllergyIntolerance mapper exists | the entire capability | yes — 3 write + 3 read routes served |
| 2 | `ehr_care_plans` | Care plan header: status, intent, period, category, contributor | 3 | 2 | none | `CarePlan` | CarePlan mapper exists | the entire capability | yes — 3 write + 2 read routes served |
| 3 | `ehr_care_plan_goals` | Goal under a care plan: target/achievement date, outcome | 3 | 2 | none | `CarePlan.goal` | CarePlan mapper exists | the entire capability | yes — 3 write + 2 read routes served |
| 4 | `ehr_care_plan_activities` | Scheduled activity under a plan/goal, coded | 3 | 2 | none | `CarePlan.activity` | CarePlan mapper exists | the entire capability | yes — 3 write + 2 read routes served |
| 5 | `ehr_clinical_notes` | Narrative note with version lineage (prior_version_id / superseded_by_id), signature, Arabic title | 3 | 4 | none | `DocumentReference / Composition` | NO mapper — would need one | the entire capability | yes — 3 write + 4 read routes served |
| 6 | `ehr_clinical_attachments` | Pointer store for uploaded files: storage_path/bucket, content_hash, mime, watermark/encryption flags | 3 | 2 | none | `DocumentReference` | NO mapper — would need one | the entire capability | yes — 3 write + 2 read routes served |
| 7 | `ehr_conditions` | Condition with clinical+verification status, coded, ICD-10 | 3 | 3 | none | `Condition` | Condition mapper exists | the entire capability | yes — 3 write + 3 read routes served |
| 8 | `ehr_diagnoses` | Encounter diagnosis with rank + ICD-10/SNOMED text | 3 | 3 | none | `Condition / Encounter.diagnosis` | Condition mapper exists | the entire capability | yes — 3 write + 3 read routes served |
| 9 | `ehr_problem_list_items` | Longitudinal problem list entry, coded | 3 | 2 | none | `Condition (problem-list-item)` | Condition mapper exists | the entire capability | yes — 3 write + 2 read routes served |
| 10 | `ehr_immunizations` | Vaccine administration: code, lot, manufacturer, administrator, dates | 3 | 3 | none | `Immunization` | Immunization mapper exists | the entire capability | yes — 3 write + 3 read routes served |
| 11 | `ehr_medication_requests` | Prescription order: 28 clinical cols incl. intent, status, form, brand | 3 | 2 | pharmacy_prescriptions (different identity + lab scope) | `MedicationRequest` | MedicationRequest mapper exists | the entire capability | yes — 3 write + 2 read routes served |
| 12 | `ehr_medication_dispenses` | Dispense event against a request | 3 | 2 | pharmacy_dispense_records (different identity + lab scope) | `MedicationDispense` | NO mapper — would need one | the entire capability | yes — 3 write + 2 read routes served |
| 13 | `ehr_medication_administrations` | Administration event against a request | 3 | 2 | none | `MedicationAdministration` | NO mapper — would need one | the entire capability | yes — 3 write + 2 read routes served |
| 14 | `ehr_medication_statements` | Patient-reported / reconciled medication history | 3 | 3 | none | `MedicationStatement` | MedicationStatement mapper exists | the entire capability | yes — 3 write + 3 read routes served |
| 15 | `ehr_family_history` | Relative's condition, coded, with relative link | 3 | 2 | none | `FamilyMemberHistory` | NO mapper — would need one | the entire capability | yes — 3 write + 2 read routes served |
| 16 | `ehr_social_history` | Smoking/alcohol/occupation/disability/exercise structured history | 3 | 2 | none | `Observation (social-history category)` | NO mapper — would need one | the entire capability | yes — 3 write + 2 read routes served |
| 17 | `ehr_risk_factors` | Clinical risk score: name, value, max, percent, version, factors, recommendations | 3 | 2 | none | `RiskAssessment` | NO mapper — would need one | the entire capability | yes — 3 write + 2 read routes served |
| 18 | `ehr_patient_timeline` | Projection over source records (source_type + source_id), display-oriented | 0 | 1 | lab_orders / lab_results / visits (all PRESENT) | `n/a — derived view` | n/a — not a FHIR resource | nothing today (never populated) | read-only route served; **no writer anywhere** |

### Reading the matrix

* **(4/5) canonical candidate is `none` for 15 of 18.** No existing table can hold the
  data, and no existing table has the required columns. Only `ehr_patient_timeline`
  has a real alternative (it is a projection over `lab_orders`/`lab_results`/`visits`,
  all present), and two medication tables have a *partial* neighbour in pharmacy whose
  identity and tenant scope differ.
* **(6/7) FHIR R4 can represent all 17 clinical tables without loss**, and **10 of 18
  already have a mapper written** in `app/national/fhir/`. Seven would need a new
  mapper: clinical notes and attachments (`DocumentReference`), medication dispense and
  administration, family history, social history (`Observation`), risk factors
  (`RiskAssessment`).
* **(8) what is lost if removed:** for the 17 with writers, the capability itself —
  these are not thin wrappers. Each carries 10–28 clinical columns, ICD-10/SNOMED
  coding, and Arabic-parallel display fields (`*_ar`), plus real domain structure:
  version lineage on notes (`prior_version_id`, `superseded_by_id`), criticality on
  allergies, lot/manufacturer on immunisations, score provenance on risk factors.
  For `ehr_patient_timeline`, nothing — it has never been populated.
* **(9) what would be required without a new table** is the same answer for all 17:
  a new persistence home must exist somewhere. The options are extending the lab-core
  tables (rejected above — no room, and it would duplicate the silo inside `patients`),
  a generic FHIR-resource JSONB store, or an external FHIR server. None exists today.
* **(10) does the code already assume the table exists:** yes for 17 — 51 write routes
  and 35 read routes are served unconditionally. `ehr_patient_timeline` is read-only
  and has **no writer anywhere in `app/`**.

### The three shapes the decision can take

Presented without a recommendation, because this is an ownership question.

1. **Amend ADR-016** so Phase 2 persists new clinical content in owned EHR tables.
   Consequence: 18 migrations become legitimate, 10 FHIR mappers already work, 7 need
   writing, and `national_patients` must be resolved first (§5).
2. **Hold the constraint** and introduce one generic FHIR-resource store instead of 18
   typed tables. Consequence: the 18 models and the 6 mappers that import them are
   retired; the 86 served operations are re-expressed over the generic store; clinical
   query performance and referential integrity both become application concerns.
3. **Narrow v1.0.0 to path A.** Ship FHIR over lab data only, and gate the `/ehr`
   router off by default so a deployment stops advertising 86 operations it cannot
   serve. Consequence: no migration, no model deleted, the capability is deferred, and
   `RELEASE_NOTES-v1.0.md` — which mentions the EHR **zero times** — already reads this
   way.

Option 3 is the only one this lane could execute without an architecture decision, and
it is still a served-surface change, so it is not taken here either.

## 5. `national_patients` — treated separately

### Why 66 FKs reference it, and which are live

**65 FK columns** across the ORM reference `national_patients.id`
(66 was the count including the `national_citizens` self-reference chain; the exact
figure measured here is 65 — **corrected**).

| | columns | tables |
|---|---|---|
| referencing table **present** in head DB — **live** | **4** | `niam_citizen_relationships`, `pharmacy_prescriptions`, `pharmacy_dispense_records`, `pharmacy_drug_returns` |
| referencing table absent — dormant | **61** | `cc_*` 35, `ehr_*` 15, `national_*` 11 |

63 of the 65 are `nullable=False`. **RUNTIME VERIFIED** against `gula_agent2`.

### What the migrated database already decided

For the four live referencing tables, the physical schema does **not** agree with this
lane's ORM:

| | physical (head DB) | this lane's ORM |
|---|---|---|
| `pharmacy_prescriptions.patient_id` | `INTEGER` → FK `patients.id` | `String(26)` → `national_patients.id` |
| `pharmacy_dispense_records.patient_id` | `INTEGER` → FK `patients.id` | `String(26)` → `national_patients.id` |
| `pharmacy_drug_returns.patient_id` | `INTEGER` → FK `patients.id` | `String(26)` → `national_patients.id` |
| `niam_citizen_relationships.patient_id` | `VARCHAR` , **no FK constraint** | `String(26)` → `national_patients.id` |

The integration lineage's own ORM already says `Column(Integer, nullable=True)` for
those pharmacy columns. **So for every table that actually got migrated, the recorded
decision is that `patients.id` is the canonical clinical patient.** That is the
strongest available answer to "is `patients` the intended canonical clinical patient":
for migrated tables, yes.

`niam_citizen_relationships.patient_id` having **no physical FK at all** is IA-004's
arm, visible from the other side. **IA-004 was not modified.**

### Is `niam_persons` identity-only?

No — and this matters. `niam_persons` is **present** (all 87 `niam_*` tables are) and
carries demographics: `given_name`, `middle_name`, `family_name`, `full_name_ar`,
`gender`, `birth_date`, `nationality`, `email`, `phone`, `address`, emergency contact,
`is_deceased`. It has no clinical linkage — no `lab_patient_id`, no `citizen_id`, no
clinical merge lineage.

So there are **three** demographic stores, not two:

| store | columns | present | role evidenced |
|---|---|---|---|
| `patients` | 16 | **yes** | per-lab LIMS patient; the FK target the migrations chose |
| `niam_persons` | 25 | **yes** | identity-platform person; demographics, no clinical link |
| `national_patients` | 45 | **no** | national clinical patient; Iraqi name structure, governorate/district, blood group, merge lineage, **and `lab_patient_id`** |

### Would replacing `national_patients` with `patients` be datatype-compatible?

**No.** `national_patients.id` is `VARCHAR(26)` (ULID); `patients.id` is `INTEGER`
(sequence). Re-pointing 65 FK columns means changing each column's type, and 63 are
NOT NULL. That is not a non-destructive change.

**And the model argues against replacement:** `national_patients.lab_patient_id`
exists. The model was written to *coexist* with legacy `patients` and bridge to it,
not to be replaced by it. That matches `CLAUDE.md`'s division of responsibility.

### Can it be solved incrementally without a destructive migration?

Partly, and only after the decision:

* **The 61 dormant references cost nothing to change** — the tables do not exist, so
  altering their ORM columns has no data implication. **STATIC VERIFIED.**
* **The 4 live references are already integer-typed in the database**, so aligning the
  ORM to the schema is an ORM-only change with no DDL. **RUNTIME VERIFIED** (all four
  tables hold 0 rows today).
* **What cannot be done incrementally** is deciding whether `national_patients` exists
  at all. If it does, it needs a migration and a statement of how it reconciles with
  `patients` and `niam_persons` without becoming a third source of truth for patient
  identity. If it does not, 45 columns of Iraqi-specific clinical identity
  (father/grandfather/mother name, governorate/district/subdistrict, blood group, merge
  lineage) have no home, and `patients` at 16 columns cannot absorb them.

**IA-006 / `national_patients`: NEEDS_DECISION.**

## 6. Evidence classification

| claim | state |
|---|---|
| ADR-016 forbids new EHR tables while Phase 2 mandates write support | **STATIC VERIFIED** (document) |
| no lab-core table can host EHR content | **STATIC VERIFIED** (physical schema) |
| no migration in either lineage creates an `ehr_*` table or `national_patients` | **INDEPENDENTLY VERIFIED** (two lineages) |
| path A (lab→FHIR) sources from present tables | **STATIC VERIFIED** |
| 10 of 18 tables already have a FHIR mapper; 6 mappers import `app.ehr.models` | **STATIC VERIFIED** |
| 65 FK columns reference `national_patients`; 4 live, 61 dormant | **RUNTIME VERIFIED** |
| the migrated schema points pharmacy at `patients.id INTEGER` | **RUNTIME VERIFIED** |
| `niam_persons` present and demographic, no clinical linkage | **RUNTIME VERIFIED** |
| ULID↔INTEGER incompatibility blocks a straight re-point | **STATIC VERIFIED** |
| which option the programme should choose | **NEEDS_DECISION** — not decided here |
| whether FHIR R4 can carry each table without loss | **STATIC VERIFIED** for the 10 with mappers; **reasoned, not proven** for the 7 without |
