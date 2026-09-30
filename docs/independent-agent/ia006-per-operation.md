# IA-006 — per-operation verification of the 86 served `/ehr` operations

Runtime re-run against `gula_agent2` (head `20260916_0001`, 423 tables) **after**
all IA-005 fixes. Verdict unchanged, which is correct: IA-005 was never why this
surface fails — the absent tables are.

`serialization` reports the IA-005 status of the response path, not whether the
route reached it. No operation reached serialization against the head database.

| # | verb | path | class | HTTP (head DB) | DB dependency | authorization | serialization |
|---|---|---|---|---|---|---|---|
| 1 | POST | `/ehr/allergies` | **BROKEN** | `500` | 1 absent (`ehr_allergies`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 2 | DELETE | `/ehr/allergies/{allergy_id}` | **BROKEN** | `500` | 1 absent (`ehr_allergies`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 3 | GET | `/ehr/allergies/{allergy_id}` | **BROKEN** | `500` | 1 absent (`ehr_allergies`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 4 | PUT | `/ehr/allergies/{allergy_id}` | **BROKEN** | `500` | 1 absent (`ehr_allergies`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 5 | POST | `/ehr/attachments` | **BROKEN** | `500` | 1 absent (`ehr_clinical_attachments`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 6 | DELETE | `/ehr/attachments/{attachment_id}` | **BROKEN** | `500` | 1 absent (`ehr_clinical_attachments`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 7 | GET | `/ehr/attachments/{attachment_id}` | **BROKEN** | `500` | 1 absent (`ehr_clinical_attachments`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 8 | PUT | `/ehr/attachments/{attachment_id}` | **BROKEN** | `500` | 1 absent (`ehr_clinical_attachments`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 9 | DELETE | `/ehr/care-plan-activities/{activity_id}` | **BROKEN** | `500` | 2 absent (`ehr_care_plan_activities`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 10 | PUT | `/ehr/care-plan-activities/{activity_id}` | **BROKEN** | `500` | 2 absent (`ehr_care_plan_activities`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 11 | DELETE | `/ehr/care-plan-goals/{goal_id}` | **BROKEN** | `500` | 2 absent (`ehr_care_plan_goals`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 12 | PUT | `/ehr/care-plan-goals/{goal_id}` | **BROKEN** | `500` | 2 absent (`ehr_care_plan_goals`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 13 | POST | `/ehr/care-plans` | **BROKEN** | `500` | 1 absent (`ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 14 | DELETE | `/ehr/care-plans/{plan_id}` | **BROKEN** | `500` | 1 absent (`ehr_care_plans`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 15 | GET | `/ehr/care-plans/{plan_id}` | **BROKEN** | `500` | 3 absent (`ehr_care_plan_activities`, `ehr_care_plan_goals`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 16 | PUT | `/ehr/care-plans/{plan_id}` | **BROKEN** | `500` | 3 absent (`ehr_care_plan_activities`, `ehr_care_plan_goals`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 17 | POST | `/ehr/care-plans/{plan_id}/activities` | **BROKEN** | `500` | 2 absent (`ehr_care_plan_activities`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 18 | POST | `/ehr/care-plans/{plan_id}/goals` | **BROKEN** | `500` | 2 absent (`ehr_care_plan_goals`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 19 | POST | `/ehr/clinical-notes` | **BROKEN** | `500` | 1 absent (`ehr_clinical_notes`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 20 | DELETE | `/ehr/clinical-notes/{note_id}` | **BROKEN** | `500` | 1 absent (`ehr_clinical_notes`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 21 | GET | `/ehr/clinical-notes/{note_id}` | **BROKEN** | `500` | 1 absent (`ehr_clinical_notes`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 22 | PUT | `/ehr/clinical-notes/{note_id}` | **BROKEN** | `500` | 1 absent (`ehr_clinical_notes`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 23 | GET | `/ehr/clinical/facilities/{national_facility_id}/notes/{note_id}` | **PARTIAL** | `403` | 1 absent (`ehr_clinical_notes`) | deny-by-default gate VERIFIED (10 tables present, discriminates) | field allowlist — never exposed |
| 24 | POST | `/ehr/conditions` | **BROKEN** | `500` | 1 absent (`ehr_conditions`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 25 | DELETE | `/ehr/conditions/{condition_id}` | **BROKEN** | `500` | 1 absent (`ehr_conditions`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 26 | GET | `/ehr/conditions/{condition_id}` | **BROKEN** | `500` | 1 absent (`ehr_conditions`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 27 | PUT | `/ehr/conditions/{condition_id}` | **BROKEN** | `500` | 1 absent (`ehr_conditions`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 28 | POST | `/ehr/diagnoses` | **BROKEN** | `500` | 1 absent (`ehr_diagnoses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 29 | DELETE | `/ehr/diagnoses/{diagnosis_id}` | **BROKEN** | `500` | 1 absent (`ehr_diagnoses`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 30 | GET | `/ehr/diagnoses/{diagnosis_id}` | **BROKEN** | `500` | 1 absent (`ehr_diagnoses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 31 | PUT | `/ehr/diagnoses/{diagnosis_id}` | **BROKEN** | `500` | 1 absent (`ehr_diagnoses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 32 | GET | `/ehr/encounters/{encounter_id}/clinical-notes` | **BROKEN** | `500` | 1 absent (`ehr_clinical_notes`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 33 | POST | `/ehr/family-history` | **BROKEN** | `500` | 1 absent (`ehr_family_history`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 34 | DELETE | `/ehr/family-history/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_family_history`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 35 | GET | `/ehr/family-history/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_family_history`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 36 | PUT | `/ehr/family-history/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_family_history`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 37 | POST | `/ehr/immunizations` | **BROKEN** | `500` | 1 absent (`ehr_immunizations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 38 | DELETE | `/ehr/immunizations/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_immunizations`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 39 | GET | `/ehr/immunizations/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_immunizations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 40 | PUT | `/ehr/immunizations/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_immunizations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 41 | POST | `/ehr/medication-administrations` | **BROKEN** | `500` | 1 absent (`ehr_medication_administrations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 42 | DELETE | `/ehr/medication-administrations/{admin_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_administrations`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 43 | GET | `/ehr/medication-administrations/{admin_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_administrations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 44 | PUT | `/ehr/medication-administrations/{admin_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_administrations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 45 | POST | `/ehr/medication-dispenses` | **BROKEN** | `500` | 1 absent (`ehr_medication_dispenses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 46 | DELETE | `/ehr/medication-dispenses/{dispense_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_dispenses`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 47 | GET | `/ehr/medication-dispenses/{dispense_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_dispenses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 48 | PUT | `/ehr/medication-dispenses/{dispense_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_dispenses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 49 | POST | `/ehr/medication-requests` | **BROKEN** | `500` | 1 absent (`ehr_medication_requests`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 50 | DELETE | `/ehr/medication-requests/{request_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_requests`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 51 | GET | `/ehr/medication-requests/{request_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_requests`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 52 | PUT | `/ehr/medication-requests/{request_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_requests`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 53 | POST | `/ehr/medication-statements` | **BROKEN** | `500` | 1 absent (`ehr_medication_statements`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 54 | DELETE | `/ehr/medication-statements/{statement_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_statements`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 55 | GET | `/ehr/medication-statements/{statement_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_statements`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 56 | PUT | `/ehr/medication-statements/{statement_id}` | **BROKEN** | `500` | 1 absent (`ehr_medication_statements`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 57 | GET | `/ehr/patient/{patient_id}` | **BROKEN** | `500` | 7 absent (`ehr_allergies`, `ehr_care_plans`, `ehr_clinical_notes`, `ehr_conditions`, `ehr_diagnoses`, `ehr_immunizations`, `ehr_medication_statements`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 58 | GET | `/ehr/patient/{patient_id}/summary` | **BROKEN** | `500` | 5 absent (`ehr_allergies`, `ehr_conditions`, `ehr_diagnoses`, `ehr_immunizations`, `ehr_medication_statements`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 59 | GET | `/ehr/patients/{patient_id}/allergies` | **BROKEN** | `500` | 1 absent (`ehr_allergies`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 60 | GET | `/ehr/patients/{patient_id}/attachments` | **BROKEN** | `500` | 1 absent (`ehr_clinical_attachments`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 61 | GET | `/ehr/patients/{patient_id}/care-plans` | **BROKEN** | `500` | 3 absent (`ehr_care_plan_activities`, `ehr_care_plan_goals`, `ehr_care_plans`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 62 | GET | `/ehr/patients/{patient_id}/clinical-notes` | **BROKEN** | `500` | 1 absent (`ehr_clinical_notes`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 63 | GET | `/ehr/patients/{patient_id}/conditions` | **BROKEN** | `500` | 1 absent (`ehr_conditions`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 64 | GET | `/ehr/patients/{patient_id}/diagnoses` | **BROKEN** | `500` | 1 absent (`ehr_diagnoses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 65 | GET | `/ehr/patients/{patient_id}/family-history` | **BROKEN** | `500` | 1 absent (`ehr_family_history`) | authenticated only — no permission check (NR-070) | no `metadata` column — not exposed |
| 66 | GET | `/ehr/patients/{patient_id}/immunizations` | **BROKEN** | `500` | 1 absent (`ehr_immunizations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 67 | GET | `/ehr/patients/{patient_id}/medication-administrations` | **BROKEN** | `500` | 1 absent (`ehr_medication_administrations`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 68 | GET | `/ehr/patients/{patient_id}/medication-dispenses` | **BROKEN** | `500` | 1 absent (`ehr_medication_dispenses`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 69 | GET | `/ehr/patients/{patient_id}/medication-requests` | **BROKEN** | `500` | 1 absent (`ehr_medication_requests`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 70 | GET | `/ehr/patients/{patient_id}/medication-statements` | **BROKEN** | `500` | 1 absent (`ehr_medication_statements`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 71 | GET | `/ehr/patients/{patient_id}/problem-list` | **BROKEN** | `500` | 1 absent (`ehr_problem_list_items`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 72 | GET | `/ehr/patients/{patient_id}/risk-factors` | **BROKEN** | `500` | 1 absent (`ehr_risk_factors`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 73 | GET | `/ehr/patients/{patient_id}/social-history` | **BROKEN** | `500` | 1 absent (`ehr_social_history`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 74 | GET | `/ehr/patients/{patient_id}/timeline` | **BROKEN** | `500` | 8 absent (`ehr_allergies`, `ehr_care_plans`, `ehr_clinical_notes`, `ehr_conditions`, `ehr_diagnoses`, `ehr_immunizations`, `ehr_medication_statements`, `ehr_patient_timeline`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 75 | POST | `/ehr/problem-list` | **BROKEN** | `500` | 1 absent (`ehr_problem_list_items`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 76 | DELETE | `/ehr/problem-list/{item_id}` | **BROKEN** | `500` | 1 absent (`ehr_problem_list_items`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 77 | GET | `/ehr/problem-list/{item_id}` | **BROKEN** | `500` | 1 absent (`ehr_problem_list_items`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 78 | PUT | `/ehr/problem-list/{item_id}` | **BROKEN** | `500` | 1 absent (`ehr_problem_list_items`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 79 | POST | `/ehr/risk-factors` | **BROKEN** | `500` | 1 absent (`ehr_risk_factors`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 80 | DELETE | `/ehr/risk-factors/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_risk_factors`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 81 | GET | `/ehr/risk-factors/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_risk_factors`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 82 | PUT | `/ehr/risk-factors/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_risk_factors`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 83 | POST | `/ehr/social-history` | **BROKEN** | `500` | 1 absent (`ehr_social_history`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 84 | DELETE | `/ehr/social-history/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_social_history`) | authenticated only — no permission check (NR-070) | returns no record — not exposed |
| 85 | GET | `/ehr/social-history/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_social_history`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
| 86 | PUT | `/ehr/social-history/{record_id}` | **BROKEN** | `500` | 1 absent (`ehr_social_history`) | authenticated only — no permission check (NR-070) | was IA-005 exposed → **FIXED** |
