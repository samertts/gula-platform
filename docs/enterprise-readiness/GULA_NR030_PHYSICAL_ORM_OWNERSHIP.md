# NR-030 — Physical Tables With No ORM Owner

**Batch:** BATCH-2.7 · **Status: PARTIALLY VERIFIED — 12 classified, 0 deleted, 0 created**

Every one of these is a `DROP TABLE` candidate for a single-MetaData
autogenerate. They are now an **explicit, named, justified exclusion list**, not
a silent one.

---

## 1. Classification

| Table | Created by | Rows possible | Consumer | Class |
|---|---|---|---|---|
| `fin_ads_campaigns` | `20260506_0001_financial_engine_phase_a` | flag off | none | **KEEP_PHYSICAL_NO_ORM** |
| `fin_ads_clicks` | " | flag off | none | **KEEP_PHYSICAL_NO_ORM** |
| `fin_ads_conversions` | " | flag off | none | **KEEP_PHYSICAL_NO_ORM** |
| `fin_clinical_behavior` | " | flag off | none | **KEEP_PHYSICAL_NO_ORM** |
| `fin_fraud_logs` | " | flag off | none | **KEEP_PHYSICAL_NO_ORM** |
| `fin_market_benchmarks` | " | flag off | none | **KEEP_PHYSICAL_NO_ORM** |
| `idempotency_keys` | `20250322_0000_create_base_schema` | **yes, actively** | `app/core/idempotency.py` (raw SQL) | **KEEP_PHYSICAL_NO_ORM** |
| `nursing_clinical_checklists` | `20260716_0002_nursing_platform` | no writer reaches it | `ClinicalChecklist` — wrong name | **MAP_EXISTING_ORM** |
| `nursing_escalation_records` | " | no writer reaches it | `EscalationRecord` — wrong name | **MAP_EXISTING_ORM** |
| `radiology_ai_analysis_jobs` | `20260716_0004_radiology_platform` | no | none | **CREATE_ORM** |
| `sndhs_audit_logs` | `20260505_0005_sndhs_phase1_audit_logs_v2` | no writer exists | none | **BLOCKED** |
| `visits` | `20260505_0003_sndhs_phase1_visits_table` | no writer exists | none (FK from `lab_orders`) | **BLOCKED** |

## 2. KEEP_PHYSICAL_NO_ORM — seven tables

**The six Financial Engine tables** are schema-only *by design*. `CLAUDE.md`:
*"Phase A is schema-only — the data model is bootstrapped but routes and
services are deferred to Phase B+. Do not add business logic to
`backend/app/financial/` without explicit approval."* Writing models would be
doing Phase B. `ENABLE_FINANCIAL_ENGINE` and `ENABLE_ADS` both default false.
None has a foreign key or any code reference.

**`idempotency_keys`** is deliberately raw SQL. `app/core/idempotency.py`
issues `SELECT`, `INSERT`, `UPDATE` and `DELETE` against it directly — it sits
in the request hot path and does not want an ORM round trip. PK `key`, FK
`lab_id → labs`. This table **holds live data** and must never be dropped.

## 3. MAP_EXISTING_ORM — a live defect, not drift

The nursing models exist and name tables that no migration creates:

| ORM class | Says | Migration creates |
|---|---|---|
| `ClinicalChecklist` | `nursing_checklists` | `nursing_clinical_checklists` |
| `EscalationRecord` | `nursing_escalations` | `nursing_escalation_records` |

`nursing_checklists` and `nursing_escalations` appear in **no `create_table`
anywhere**. The confusion is visible in the migration itself, which creates
`nursing_clinical_checklists` but names its indexes `ix_nursing_checklists_*`.

**These are reached by live HTTP routes.** `nursing/routes.py:980`
(`create_checklist`) and `:1084` (escalation listing) query them through
`nursing/services.py`. Both therefore fail at runtime with *relation
"nursing_checklists" does not exist*. **Two nursing features are dead in
production**, which is the same defect class as the Pharmacy M3 finding where
every ORM `INSERT` failed before a row was created.

**Not repaired here, deliberately.** Renaming `__tablename__` alone would take
these from "always fails loudly" to "sometimes succeeds with the wrong types":
NR-026 records that `escalated_to` is `String(26)` in the ORM against a physical
`integer`, and `EscalationRecord.escalated_to == nurse_id` is one of the live
filters. A quietly wrong query is worse than a loud failure. The
`__tablename__` and the column types must be corrected in one change — that is
the NR-026 nursing reconciliation, and this finding raises its severity from
drift to a live outage.

## 4. CREATE_ORM — one table

`radiology_ai_analysis_jobs`: 34 columns, 6 foreign keys to real radiology
tables (`radiology_exams`, `radiology_series`, `radiology_images`, `patients`,
`labs`, `lab_users`), 6 indexes. It is the **only one of eighteen** radiology
tables with no model, and no radiology `__tablename__` resembles it — so this is
an omission, not a deliberate physical-only table. Writing the model is
mechanical and low-risk, but §2 forbids creating ORM classes automatically, so
it is recorded for the radiology owner.

## 5. BLOCKED — two tables

**`sndhs_audit_logs`.** A parallel, UUID-keyed, purpose-tagged, append-only
audit surface created alongside `audit_logs` rather than mutating it. Its own
migration promises *"see `backend/app/services/sndhs_audit.py` (added in a
follow-up step)"* — **that file does not exist**. So the table was built, the
service never was. Whether SNDHS audit is a second audit surface or eventually
replaces `audit_logs` is an architecture decision with retention implications.

**`visits`.** The proposed canonical clinical episode. Writing its model is part
of adopting Visit, which waits on the three clinical-owner questions in
`GULA_VISIT_ENCOUNTER_ARCHITECTURE.md`.

## 6. Effect on NR-023

Still a blocker. The 12 are now classified and named, and none is a silent
exclusion — but seven are permanent exclusions and five need work, so the
combined-MetaData architecture would still need the exclusion list wired in
before it could run safely.

**Nothing was deleted, no ORM class was created, no migration was written.**
