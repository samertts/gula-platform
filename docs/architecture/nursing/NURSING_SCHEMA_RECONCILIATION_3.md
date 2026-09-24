# Nursing Domain — Full Schema Reconciliation (BATCH-3)

**Negative Register finding:** NR-026
**Status:** RESOLVED for the fifteen `nursing_*` tables; three dependent items remain BLOCKED and are named in §9.
**Authoritative source:** PostgreSQL 16.13 at Alembic head `20260912_0001`.
**Schema change:** none. No migration was written, added, renamed or modified. Migration
file count 106 before and 106 after; single head before and after.

---

## 1. What was wrong

The Nursing ORM and the Nursing schema described two different databases.

| Symptom | Count before | Count after |
|---|---:|---:|
| Models that could not execute a plain `SELECT` | 15 of 15 | 0 |
| Models naming a table no migration creates | 2 | 0 |
| Primary keys declared `String(26)` against an `INTEGER` column | 13 | 0 |
| Mapped columns with no physical column | 137 | 0 |
| Column type mismatches | 97 | 0 |
| Foreign-key declarations disagreeing with the database | all | 0 |
| API request fields with no column anywhere | 119 | 0 |
| Endpoints whose first `INSERT` could not satisfy a `NOT NULL` | 12 | 0 |
| Destructive operations in an autogenerate diff | table-level rewrite | 0 |

The domain was not partially broken. Every table was unreachable, in a platform whose
first principle is that patient data is never at risk. The tables are all empty
(`0` rows across all fifteen, measured immediately before and after this work), which is
consistent: nothing has ever successfully written to them.

## 2. Physical inventory (authoritative)

15 tables, 422 columns, 68 foreign keys, 0 rows. Every primary key is `integer`
with a `nextval(...)` default.

| Table | Columns | FKs | Rows | PK |
|---|---:|---:|---:|---|
| nursing_care_plans | 26 | 4 | 0 | integer |
| nursing_clinical_checklists | 27 | 6 | 0 | integer |
| nursing_delegations | 25 | 5 | 0 | integer |
| nursing_escalation_records | 27 | 5 | 0 | integer |
| nursing_fall_risk_assessments | 30 | 4 | 0 | integer |
| nursing_fluid_balance | 28 | 5 | 0 | integer |
| nursing_notes | 24 | 5 | 0 | integer |
| nursing_nutrition_assessments | 30 | 4 | 0 | integer |
| nursing_pain_assessments | 30 | 4 | 0 | integer |
| nursing_patient_assignments | 23 | 4 | 0 | integer |
| nursing_pressure_injury_assessments | 29 | 4 | 0 | integer |
| nursing_shift_handovers | 24 | 5 | 0 | integer |
| nursing_shifts | 23 | 2 | 0 | integer |
| nursing_tasks | 31 | 7 | 0 | integer |
| nursing_vital_signs | 45 | 4 | 0 | integer |

## 3. Identity decision

**Internal `INTEGER` serial key, plus a nullable portable `sync_id VARCHAR(26)`.**

This is not a new identity architecture — it is the one the schema already implements.
All fifteen tables carry both, every inbound foreign key is `INTEGER`, and `sync_id` has
a `UNIQUE` constraint on every table. The previous ORM had invented a second scheme
(`String(26)` primary keys with a `_ulid()` default) that no migration ever built.

Nursing therefore does **not** introduce a UUID or ULID primary key, and does not
convert the fifteen models to one. `sync_id` is the identifier that travels between
deployments; the integer key stays internal.

## 4. `escalated_to` — semantic proof

The BATCH-3 brief required the meaning of this field to be *proved*, not assumed, before
its type was changed. Three independent pieces of evidence agree:

1. **Physical:** `nursing_escalation_records.escalated_to` is `integer`, nullable,
   indexed as `ix_nursing_escalation_escalated_to`.
2. **Consumer:** the only query that reads it is
   `NursingService.get_nurse_dashboard`, which filters
   `EscalationRecord.escalated_to == nurse_id` where `nurse_id` is the authenticated
   user's `lab_users.id` — an integer.
3. **Sibling columns:** `escalated_by` (NOT NULL) is `integer` on the same table and is
   set from `user_id` by `NursingService.escalate`.

`escalated_to` is therefore **the `lab_users.id` of the clinician the escalation was
raised to**. It is `Integer` in the ORM and `int | None` at the API boundary. The
previous `str | None` request field could not have matched a row.

## 5. Cross-domain ownership

Nursing references four tables it does not own, by their canonical integer keys:
`labs`, `lab_users`, `patients`, `nhdw_admissions`. It defines no Patient, no
Practitioner, no User and no Encounter of its own, and this reconciliation created none.

Those four live on other declarative bases. A SQLAlchemy `ForeignKey` across MetaData
boundaries cannot resolve, and breaks `mapper._sorted_tables` on every `INSERT`
(NR-023) — the same wall Pharmacy hit, resolved the same way: **declare the column,
omit the ORM `ForeignKey`, and let PostgreSQL keep enforcing the constraint**, which it
still does (asserted by `test_the_physical_constraints_are_still_enforced_by_postgres`).

`nursing_shifts` is the one foreign-key target inside the Nursing MetaData, so the five
references to it keep a real `ForeignKey`.

## 6. Destructive-diff evidence (§14)

`alembic.autogenerate.compare_metadata` against `NursingBase.metadata`, restricted to
the fifteen Nursing tables. No file was written at any point.

| Operation | Before | After |
|---|---:|---:|
| `remove_table` | 2 (phantom names) + full rewrite of the rest | **0** |
| `remove_column` | — | **0** |
| `add_table` / `add_column` | — | **0** |
| `modify_type` | 97 | **0** |
| `remove_index` | 17 | **0** |
| `remove_constraint` | 16 | **0** |
| `add_index` | 18 | 5 |
| `remove_fk` | 63 | 63 |

The 68 remaining differences are both explained and both non-destructive:

* **63 × `remove_fk`** — the cross-base foreign keys of §5, targeting `lab_users` (26),
  `labs` (15), `patients` (13) and `nhdw_admissions` (9). None targets a Nursing table.
  These must never be emitted into a migration; the registry guard and the domain
  contract both pin this.
* **5 × `add_index`** — the shared `TenantMixin` marks `lab_id` indexed and SQLAlchemy
  names the index `ix_<table>_lab_id`, while five migrations created an abbreviated
  name (`ix_nursing_checklists_lab_id`, `ix_nursing_escalation_lab_id`,
  `ix_nursing_fall_risk_lab_id`, `ix_nursing_nutrition_lab_id`,
  `ix_nursing_pressure_injury_lab_id`). The index exists in both; only the name differs.
  Fixing it means either editing a mixin five other domains share or overriding
  `lab_id` in five models — neither is worth a duplicate index, so it is recorded here
  rather than silenced.

## 7. Defects found and fixed

Each of these was reached by executing the code, not by reading it.

| # | Defect | Consequence before the fix |
|---|---|---|
| 1 | 15 models keyed `String(26)` against `INTEGER` | no Nursing table could be read |
| 2 | `ClinicalChecklist` / `EscalationRecord` named `nursing_checklists` / `nursing_escalations` | `UndefinedTable` on every call; clinical escalation and clinical checklists were dead |
| 3 | 137 mapped columns did not exist | any `SELECT` naming them failed |
| 4 | `log_action` called positionally with 7 arguments at 13 sites | the laboratory was written to `user_role`, the details dict to `lab_id` — which psycopg2 cannot adapt — so the mutation's own transaction died and the audit detail was lost. Audit-log coverage is a platform invariant. |
| 5 | `audit_service.log_action` serialized details with no `default=` | a mutation carrying a timestamp raised `TypeError` inside the audit writer |
| 6 | `unassign_patient` set `is_active` / `end_date`, neither a column | every unassignment silently did nothing; the nurse kept the patient and the next assign returned 409 |
| 7 | `defer_task` set `due_time`, not a column | a deferred task kept its original deadline |
| 8 | `complete_task` set `patient_response`, not a column | the clinical outcome of a task was discarded |
| 9 | `resolve_escalation` set `resolution` and `resolved_by`, neither a column | the account of how a deteriorating patient was resolved was discarded |
| 10 | `get_net_balance` summed `amount_ml`, not a column | fluid balance raised `AttributeError` |
| 11 | `get_assigned_patients` read `encounter_id`, `department_id`, `start_date` | the assigned-patient list raised `AttributeError` |
| 12 | `start_shift` wrote a `datetime` into a `TIME` column and never set `shift_date` | a shift could not be started |
| 13 | `end_shift` wrote a `datetime` into `end_time` and never set `clocked_out_at` | a shift could not be ended |
| 14 | `assign_patient` passed `department_id` / `encounter_id` to a model without them | `TypeError` on every assignment |
| 15 | 12 tables had a `NOT NULL` column no request could fill | `NotNullViolation` on first write |
| 16 | services splatted the raw body into the model constructor | a client could set `id`, `lab_id`, `version`, `is_deleted` |
| 17 | routes coerced `current_user.id` to `str` at 17 sites | comparisons against `INTEGER` columns survived only by PostgreSQL's implicit cast of an unknown literal, and failed outright for any non-numeric id |
| 18 | `list_overdue_tasks` ordered by `due_time` | overdue tasks raised `AttributeError` |

## 8. API contract changes

Every changed endpoint was **non-functional before this change** — it either raised
`UndefinedTable`, `AttributeError`, `TypeError` or `NotNullViolation` on its first call —
and all fifteen tables are empty. No working client can therefore have depended on the
shapes that changed. The changes are still listed here in full because they are
breaking on paper.

**Rule adopted:** an API request field must name a real column of the table the request
is written into. Every Nursing request model now inherits `extra="forbid"`.

Accepting a clinical field and discarding it is worse than the failure it replaces: a
nurse who records a pupil reaction and receives `201 Created` is entitled to believe it
was recorded. 119 such fields existed. They are refused now, not dropped.

### 8.1 Renamed to the physical column (data now lands correctly)

| Request model | Was | Now |
|---|---|---|
| VitalSignsCreate | `bp_systolic`, `bp_diastolic`, `oxygen_device` | `systolic_bp`, `diastolic_bp`, `oxygen_therapy` |
| FluidBalanceCreate | `fluid_name`, `amount_ml`, `start_time`, `end_time`, `infusion_rate`, `bag_number` | `solution_name`, `volume_ml`, `started_at`, `ended_at`, `rate_ml_per_hour`, `batch_number` |
| PainAssessmentCreate | `duration`, `interventions_tried`, `effectiveness` | `pain_duration`, `intervention`, `intervention_response` |
| TaskCreate / TaskUpdate | `due_time` | `due_at` |
| TaskComplete | `patient_response` | `outcome` |
| TaskDefer | `new_due_time` | `due_at` |
| NursingNoteCreate | `documentation_time`, `documented_by` (server-injected) | `written_at`, `written_by` |
| EscalationResolve | `resolution` | `resolution_notes` (+ `outcome`) |
| HandoverCreate | `patient_summaries`, `critical_alerts`, `shift_date` | `patient_summary`, `critical_events`, server-set `handover_at` |

### 8.2 Types corrected to match the column

`nurse_id`, `assigned_to`, `delegated_to`, `escalated_to`, `from_nurse_id`,
`to_nurse_id`, `shift_id`, `from_shift_id`, `to_shift_id`, `witnessed_by`,
`supervised_by` — all `str` → `int`. Every path parameter that is a Nursing primary key
(`task_id`, `plan_id`, `note_id`, `handover_id`, `checklist_id`, `delegation_id`,
`escalation_id`) is `int`, so a non-numeric id is a 422 rather than a 500.

### 8.3 Newly required, because the column is `NOT NULL`

`TaskCreate.title`, `CarePlanCreate.care_plan_type`, `CarePlanCreate.title`,
`NursingNoteCreate.content`, `ChecklistCreate.title`, `DelegationCreate.task_type`,
`DelegationCreate.description`, `EscalationCreate.escalation_level`,
`EscalationCreate.patient_id`, `FluidBalanceCreate.fluid_type`,
`FluidBalanceCreate.volume_ml`, `FallRiskCreate.total_score` / `risk_level`,
`PressureInjuryCreate.total_score` / `risk_level`,
`NutritionCreate.total_score` / `risk_level`, `HandoverCreate.from_shift_id`.

### 8.4 Now server-owned (a client may not set them)

`assigned_at`, `delegated_at`, `escalated_at`, `handover_at`, `written_at`,
`start_time` + `clocked_in_at`, `end_time` + `clocked_out_at`, `acknowledged_at`,
`resolved_at`, `completed_at`, and the checklist's `total_items` / `completed_count`,
which are derived from the items themselves.

### 8.5 Refused, because no column can store them — schema extensions proposed

These require a schema change and are therefore **not** made here. Each is a candidate
for a future migration, on approval.

| Group | Fields | Proposed home |
|---|---|---|
| Clinical episode | `encounter_id` (10 request models) | BLOCKED on the Visit/Encounter decision (see `GULA_VISIT_ENCOUNTER_ARCHITECTURE.md`); no column may be added until an owner is named |
| Neurological observation | `pupil_left_size`, `pupil_left_reaction`, `pupil_right_size`, `pupil_right_reaction` | new columns on `nursing_vital_signs` |
| Vital-sign context | `temperature_site`, `glucose_context` | new columns on `nursing_vital_signs` |
| Structured nursing note | `subjective`, `objective`, `assessment`, `intervention`, `response`, `evaluation`, `plan`, `attachments`, `patient_education` | a SOAPIER extension of `nursing_notes`; today the note body is the single `content` column |
| Pressure-injury **wound** record | `stage`, `anatomical_location`, `length_cm`, `width_cm`, `depth_cm`, `wound_bed`, `exudate_*`, `wound_edges`, `periwound_skin`, `infection_signs`, `wound_culture`, `dressing_*`, `treatment_plan`, `photographs` | a new `nursing_pressure_injury_wounds` table. The existing table is a **Braden-style risk score**, not a wound description — this is a genuine semantic gap, not a rename |
| Nutrition detail | `weight_change_1mo_kg`, `appetite`, `dietary_restrictions`, `chewing_difficulty`, `dysphagia_risk`, `fluid_restriction_ml`, `calorie_target_kcal`, `protein_target_g`, `feeding_method`, `supplements`, `diet_type` | new columns on `nursing_nutrition_assessments`, which today is a MUST-style score |
| Fall-risk detail | `age_ge_65`, `fall_history_12mo`, `secondary_condition`, `assistive_device`, `iv_or_heparin_lock`, `gait_impaired`, `elimination`, `medications`, `interventions_ordered` | the table holds the Morse items under different names (`history_of_falls`, `secondary_diagnosis`, `ambulatory_aid`, `iv_therapy`, `gait`); the request model now uses the physical names |
| Task scheduling | `scheduled_time`, `is_recurring`, `recurrence_rule`, `clinical_instruction` | `nursing_tasks` has one deadline (`due_at`) and no recurrence; folding `scheduled_time` into `due_at` would silently conflate two different times |
| Shift roster | `department_id`, `patient_count`, `assigned_patients` | `nursing_shifts` records `ward` and `department` as text; the roster lives in `nursing_patient_assignments` |
| Care-plan review | `evaluation`, `next_review` | `outcome` and `review_date` are the columns that exist; the request models use those |

## 9. Still BLOCKED (not fixed here, and not silently worked around)

1. **Encounter / Visit ownership** — `encounter_id` has no owner. Refused at the
   boundary until the clinical owner decides (BATCH-2.7 §4).
2. **The four medication endpoints** (`/nursing/medication-schedule/*`,
   `/nursing/medication-alerts/*`, `/nursing/medication-admin/record`,
   `/nursing/medication-admin/sign`) query `app.ehr.models.medication`, whose four
   tables (`ehr_medication_statements`, `ehr_medication_requests`,
   `ehr_medication_dispenses`, `ehr_medication_administrations`) **do not exist in the
   database** — zero `ehr_*` tables at head. This is NR-026's shape in a second domain
   and is outside BATCH-3's authorised scope; it is recorded as **NR-032**. Creating
   EHR tables is a schema change requiring approval.
3. **The eight coordination endpoints** (`/nursing/coordination/*`) persist nothing.
   `CareCoordinatorService` builds a dictionary, writes an audit entry and returns it —
   there is no physician-message, referral, discharge-plan or family-communication
   table. Their `log_action` calls were among the thirteen miscalled sites, so until
   this batch they raised on every request. They now work as designed; whether
   "audit-entry only" *is* the design is a product decision, recorded as **NR-033**.

## 10. Verification performed

* 15/15 models execute a plain `SELECT`; full write round trip (server-assigned
  integer id → read back → soft delete).
* 0 type mismatches, 0 phantom columns, 0 phantom tables, 0 FK mismatches.
* `alembic downgrade -1 && alembic upgrade head` with `PYTHONPATH` unset: clean.
  Migration files 106 → 106; heads 1 → 1; `current` == `head` before and after.
* Row counts on all fifteen tables: 0 before, 0 after (the test fixtures clean up
  every table they write).
* Destructive diff: 0 destructive operations (§6).
* 24 focused tests: `backend/tests/test_nursing_domain_contract.py` (9) and
  `backend/tests/test_nursing_runtime.py` (15).
* Full backend suite green.

## 11. Test coverage added

`test_nursing_domain_contract.py` — derives every expectation from PostgreSQL rather
than from a hand-written list: all fifteen models name a real table, execute a `SELECT`,
declare no phantom column, match every column type, declare the physical primary key,
match the physical foreign keys, hold no cross-base `ForeignKey`, still have their
constraints enforced by the database, and produce no destructive autogenerate diff.

`test_nursing_runtime.py` — shift create/read, the clinical checklist path, the clinical
escalation path, tenant isolation on escalations, rejection of client-supplied
server-owned columns, unknown-field handling, the assignment lifecycle (including that
unassignment now actually ends the assignment), task create/complete/defer, shift
start/end, delegation, escalation acknowledge/resolve, net fluid balance, checklist
count derivation, audit-row correctness, and boundary rejection of an unstorable field.

Both suites read `GULA_SCHEMA_DATABASE_URL`, falling back to `MIGRATION_DATABASE_URL`,
which CI already exports for its migrated PostgreSQL service — so they run in CI without
any workflow change.
