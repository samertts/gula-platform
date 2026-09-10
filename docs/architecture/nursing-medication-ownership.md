# Medication Domain — Canonical Ownership (NR-032)

**Batch:** BATCH-3.1 · **Finding:** NR-032 (P0) · **Status:** PARTIALLY VERIFIED —
trace and ownership decision complete; execution requires approval.
**Authoritative source:** PostgreSQL at Alembic head `20260912_0001`.
**No table was created. No migration was written.**

---

## 1. The finding is not a Nursing finding

BATCH-3 recorded NR-032 as "four Nursing medication endpoints query tables that do
not exist." Tracing it shows Nursing is one consumer of five. Nine modules import
`app.ehr.models.medication`:

| Module | Models used | Reachable? |
|---|---|---|
| `nursing/medication.py` | Request, Administration | yes — 4 routes |
| `nursing/services.py` | Request, Administration | yes — 2 routes |
| `pharmacy/services.py` | Dispense | **yes — every POS sale carrying a patient or citizen id** |
| `citizen_platform/medications.py` | Statement | yes |
| `citizen_platform/routes.py` | Dispense | yes |
| `national/fhir/medication_statement.py` | Statement | export path |
| `national/fhir/medication_request.py` | Request | export path |
| `national_data/models/canonical_medication.py` | all four | analytics view |
| `ehr/models/__init__.py` | all four | re-export |

Pinned by `test_every_dependent_domain_is_named` so the scope cannot quietly grow.

## 2. Runtime proof

```
ehr_medication_requests:        UndefinedTable — relation does not exist
ehr_medication_administrations: UndefinedTable — relation does not exist
```

* Zero `ehr_*` tables exist at head (423 tables present).
* No migration in `backend/migrations/versions/` creates one.
* `EHRBase.metadata` **is** registered in `migrations/env.py`, so the models are
  visible to autogenerate — they were declared and never built.

## 3. Why the tables cannot simply be created

Two blockers, both structural:

1. **They depend on the unbuilt National Core.** Every model declares real
   `ForeignKey`s to `national_patients`, `national_citizens`,
   `national_encounters` and `national_practitioners`. None of the four exists
   (NR-022). Building medication means building the National Core first — an
   architecture decision, not a migration.
2. **They cannot express the tenancy their callers apply.** No `ehr_medication_*`
   model has a `lab_id` column. `nursing/medication.py` filters
   `MedicationAdministration.lab_id` and `MedicationRequest.lab_id` in six
   places, and Pharmacy treats a dispense as institutional. Creating the tables
   as declared would hand six lab-scoped callers a table with no tenant column —
   converting a loud failure into a silent cross-tenant read.

They are also `String(26)`-keyed, against an INTEGER-keyed Pharmacy domain and an
INTEGER-keyed Nursing domain — the same Generation-A/Generation-B split as NR-003
and NR-026.

## 4. The medication entities, as the repository actually defines them

| Concept | Canonical owner today | Evidence |
|---|---|---|
| **Drug catalogue** | `pharmacy_drug_catalog` | built; INTEGER; deliberately **not** lab-scoped — shared reference data |
| **Prescription / Medication Request** | `pharmacy_prescriptions` + `pharmacy_prescription_items` | built; lab-scoped; carries prescriber, status, validity, refills; items carry dosage, frequency, route, duration |
| **Dispensing** | `pharmacy_dispense_records` | built; lab-scoped; dispensed_by/at, quantity, verification, counselling |
| **Medication Administration (MAR)** | **none** | no table in any domain records a drug being given |
| Medication Statement (patient-reported) | none built | `ehr_medication_statements` declared only |
| Medication Event / History | not a distinct entity | `national_data/canonical_medication.py` is a read-only union view |

The decisive asymmetry: **prescribing and dispensing both have a built owner;
administration has none.** Three of the four Nursing endpoints are about
administration.

## 5. Decision matrix

| | Option A — build `ehr_medication_*` | Option B — Nursing consumes Pharmacy | Option C — new canonical MAR table | Option D — retire the endpoints |
|---|---|---|---|---|
| **Canonical owner** | EHR / National Core | Pharmacy | Nursing | — |
| **Evidence** | models exist, nothing else | prescriptions + items + dispense all built and lab-scoped | no administration table anywhere | zero frontend consumers |
| **Data impact** | none (all empty) | none | none | none |
| **Migration impact** | blocked: needs 4 National Core tables first | **none** | one additive table | none |
| **API impact** | none | schedule/alerts endpoints re-point at Pharmacy | record/sign endpoints gain a real table | 4 routes removed |
| **Frontend impact** | none | none | none | none — no caller found in `frontend-v3`, `mobile`, `mobile-expo`, `client` |
| **Security impact** | **negative** — no `lab_id`, silent cross-tenant reads | positive — inherits Pharmacy's lab scoping | positive — lab-scoped like the other 15 Nursing tables | neutral |
| **National compatibility** | aligned in theory, unbuildable in practice | Pharmacy already carries `fhir_id`/`fhir_resource_type` | add the same two columns | loses the capability |
| **Recommendation** | **REJECT for now** | **ADOPT** for schedule/alerts | **ADOPT** for administration/signature | reject — the clinical need is real |

### Decision

**NR-032 resolves as B + C, not A.**

* `GET /nursing/medication-schedule/{patient_id}` and
  `GET /nursing/medication-alerts/{patient_id}` read *prescriptions*. Pharmacy
  owns prescriptions. Nursing must **consume** `pharmacy_prescriptions` +
  `pharmacy_prescription_items` — both already lab-scoped and INTEGER-keyed, so
  no identity translation is needed.
* `POST /nursing/medication-admin/record` and `/sign` write an *administration*.
  Nothing owns that. It is a bedside nursing clinical act, so **Nursing owns it**:
  one additive `nursing_medication_administrations` table, INTEGER key +
  `sync_id`, `lab_id` NOT NULL, `prescription_item_id` referencing the Pharmacy
  line, following exactly the pattern the fifteen reconciled tables use.
* `ehr_medication_*` stays **BLOCKED behind NR-022**. It is not deleted — it is
  the National Core's medication model and belongs to that decision. It must not
  be built to make an endpoint execute.

Missed-doses and late-doses derive from the two sources above and need no third.

## 6. The P0 this trace uncovered outside Nursing — NR-034

`PharmacyService` builds an EHR `MedicationDispense` for every sale line whenever
the caller supplies `patient_id` or `citizen_id`; the POS request model accepts
both (`app/pharmacy/routes.py`). The INSERT targets `ehr_medication_dispenses`,
so **a pharmacy point-of-sale transaction that names a patient cannot commit**.
Sales without a patient context are unaffected, which is why the existing POS
tests pass.

Pharmacy already owns `pharmacy_dispense_records`, which is built and lab-scoped.
The fix is to write the dispense there — but it changes a clinical write path in a
domain outside this batch's scope, so it is recorded as **NR-034 (P0)** rather
than applied here.

## 7. Cross-domain intersections recorded (not implemented)

**Visit / Encounter** — `ehr_medication_*` reference `national_encounters`;
Nursing references none. No second Visit model was created. This strengthens the
existing Visit/Encounter package: medication is another domain waiting on that
decision.

**Patient identity** — three widths in play: Pharmacy and Nursing use
`patients.id` (INTEGER); EHR uses `national_patients.id` (`String(26)`); Nursing's
medication code passes an INTEGER route parameter into a `String(26)` comparison.
Consuming Pharmacy avoids the translation entirely.

**Practitioner / Organization** — EHR points at `national_practitioners`;
Pharmacy and Nursing use `lab_users.id`. Practitioner is CLOSED as NATIONAL
(BATCH-2.6), so this remains a National Core dependency, not a Nursing one.

**State machines** — medication statuses observed: `active` (request),
`completed` (administration), `pending`/`ordered`/`planned` (coordination, §NR-033).
Classification: `active`/`completed` on the EHR models are **DEAD** (no table can
hold them); Pharmacy's `PrescriptionStatus` and `DispenseStatus` enums are
**LIVE**. No change made to the state registry — carried to the state-ownership
batch.

## 8. Tenancy and authorization

| Route | Auth | Tenant filter | Audit | Verdict |
|---|---|---|---|---|
| `/nursing/medication-schedule/{id}` | `get_current_user` | `lab_id` passed, column absent | none | fails before any check |
| `/nursing/medication-schedule/{id}/missed-doses` | `get_current_user` | same | none | same |
| `/nursing/medication-alerts/{id}` | `get_current_user` | same | none | same |
| `/nursing/medication-admin/record` | `get_current_user` | same | `log_action` (fixed in BATCH-3) | same |
| `/nursing/medication-admin/sign` | `get_current_user` | same | `log_action` (fixed in BATCH-3) | same |
| `/nursing/medication-admin/verify` | `get_current_user` | n/a — pure computation | none | **works today** |

No new authorization mechanism is proposed. Consuming Pharmacy inherits the
existing lab scoping; the new MAR table would carry `lab_id` like every other
Nursing table.

## 9. Verification

| Command | Result | Status |
|---|---|---|
| `pytest tests/test_ehr_medication_dependency_p0.py` | 10 passed | VERIFIED |
| `SELECT ... information_schema.tables LIKE 'ehr%'` | 0 rows | VERIFIED |
| `SELECT ... national_patients/citizens/encounters/practitioners` | 0 of 4 | VERIFIED |
| ORM `SELECT` on Request and Administration | `UndefinedTable` both | VERIFIED |
| `lab_id in MedicationAdministration.__table__.columns` | `False` | VERIFIED |
| grep for frontend callers of the 4 routes | none in frontend-v3/mobile/mobile-expo/client | VERIFIED |
| Pharmacy owner tables present and INTEGER-keyed | 4 of 4 | VERIFIED |

## 10. Recommended next batch

**MED-001 — Medication ownership execution** (needs approval; touches two domains):
1. NR-034 first: re-point the Pharmacy POS dispense write at
   `pharmacy_dispense_records`. P0, in a built domain, no schema change.
2. Re-point the two Nursing read endpoints at Pharmacy prescriptions.
3. One additive migration for `nursing_medication_administrations`.
4. Leave `ehr_medication_*` untouched and BLOCKED behind NR-022.
