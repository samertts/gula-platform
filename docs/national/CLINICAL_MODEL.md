# Clinical Model — National Healthcare Platform

## Overview

The clinical model encompasses all EHR models in `app/ehr/` and additional
clinical content models across the platform. Each model is FHIR R4-compatible,
versioned, soft-deletable, and carries a full audit trail.

---

## 1. Patient Summary Model

The patient summary is an aggregated view — not a single table. It is assembled
from multiple EHR models to provide a comprehensive overview.

**Route:** `GET /ehr/patients/{patient_id}/summary`  
**Composed from:**
- `ProblemListItem` — active problems (clinical_status = "active")
- `AllergyIntolerance` — active allergies (status = "active")
- `MedicationStatement` — current medications (status = "active")
- `ImmunizationRecord` — recent immunizations (last 2 years)
- `ConditionRecord` — chronic conditions
- `Encounter` — recent encounters (last 6 months)
- `VitalSigns` — latest vital signs (via Observation canonical)

**Schema (returned JSON):**

| Field | Source | Description |
|-------|--------|-------------|
| `patient_id` | National Patient | Patient identifier |
| `full_name_ar` | National Citizen | Arabic full name |
| `full_name_en` | National Citizen | English full name |
| `date_of_birth` | National Citizen | DOB |
| `gender` | National Citizen | Gender |
| `blood_group` | National Citizen | Blood type |
| `health_number` | National Citizen | Public health identifier |
| `problems` | ProblemListItem[] | Active problems |
| `allergies` | AllergyIntolerance[] | Active allergies |
| `medications` | MedicationStatement[] | Current medications |
| `immunizations` | ImmunizationRecord[] | Recent immunizations |
| `conditions` | ConditionRecord[] | Chronic conditions |
| `recent_encounters` | Encounter[] | Last 6 months |

---

## 2. Problem List Model

**Table:** `ehr_problem_list_items`  
**Model class:** `ProblemListItem`  
**App location:** `app/ehr/models/clinical_summary.py`

### Fields

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(26) PK | ULID primary key |
| `patient_id` | FK → national_patients | Patient |
| `citizen_id` | FK → national_citizens (nullable) | Citizen |
| `encounter_id` | FK → national_encounters (nullable) | Encounter context |
| `status` | Enum(ProblemStatus) | ACTIVE, RESOLVED, INACTIVE, ENTERED_IN_ERROR |
| `code` | String(50) | Problem code |
| `code_system` | String(20) | Code system (ICD10, SNOMED) |
| `display` | String(300) | Display name |
| `display_ar` | String(300) | Arabic display name |
| `clinical_status` | String(50) | Clinical status |
| `verification_status` | String(50) | Verification status |
| `category` | String(100) | Problem category |
| `severity` | String(50) | Severity |
| `onset_date` | Date | When problem started |
| `resolution_date` | Date | When problem resolved |
| `body_site` | String(200) | Anatomical location |
| `notes` | Text | Clinical notes |

### Indexes
- `ix_ehr_problem_patient` — patient_id + status
- `ix_ehr_problem_citizen` — citizen_id
- `ix_ehr_problem_code` — code
- `ix_ehr_problem_not_deleted` — is_deleted + patient_id

---

## 3. Diagnoses Model

**Table:** `ehr_diagnoses`  
**Model class:** `DiagnosisRecord`  
**App location:** `app/ehr/models/clinical_summary.py`

### Fields

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(26) PK | ULID primary key |
| `patient_id` | FK → national_patients | Patient |
| `citizen_id` | FK → national_citizens (nullable) | Citizen |
| `encounter_id` | FK → national_encounters (nullable) | Encounter |
| `practitioner_id` | FK → national_practitioners (nullable) | Diagnosing practitioner |
| `diagnosis_type` | Enum(DiagnosisType) | PRIMARY, SECONDARY, COMORBIDITY, COMPLICATION, ADMISSION, DISCHARGE |
| `rank` | Integer | Priority order (0 = primary) |
| `icd10_code` | String(20) | ICD-10 code |
| `icd10_description` | String(500) | ICD-10 description |
| `snomed_code` | String(20) | SNOMED CT code |
| `snomed_description` | String(500) | SNOMED CT description |
| `diagnosis_text` | String(500) | Free-text diagnosis |
| `diagnosis_text_ar` | String(500) | Arabic diagnosis text |
| `diagnosis_date` | Date | When diagnosed |
| `resolution_date` | Date | When resolved |
| `is_active` | Boolean | Active flag |
| `is_chronic` | Boolean | Chronic condition flag |
| `certainty` | String(50) | CONFIDENT, PROVISIONAL, DIFFERENTIAL, RULED_OUT |

### Indexes
- `ix_ehr_diagnosis_patient` — patient_id + diagnosis_type
- `ix_ehr_diagnosis_citizen` — citizen_id
- `ix_ehr_diagnosis_encounter` — encounter_id
- `ix_ehr_diagnosis_icd10` — icd10_code
- `ix_ehr_diagnosis_active` — patient_id + is_active

---

## 4. Conditions Model

**Table:** `ehr_conditions`  
**Model class:** `ConditionRecord`  
**App location:** `app/ehr/models/clinical_summary.py`

### Fields

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(26) PK | ULID primary key |
| `patient_id` | FK → national_patients | Patient |
| `citizen_id` | FK → national_citizens (nullable) | Citizen |
| `encounter_id` | FK → national_encounters (nullable) | Encounter context |
| `practitioner_id` | FK → national_practitioners (nullable) | Recording practitioner |
| `clinical_status` | String(50) | ACTIVE, RECURRENCE, RELAPSE, INACTIVE, REMISSION, RESOLVED |
| `verification_status` | String(50) | UNCONFIRMED, PROVISIONAL, DIFFERENTIAL, CONFIRMED, REFUTED |
| `category` | String(100) | problem-list-item, encounter-diagnosis |
| `severity` | String(50) | MILD, MODERATE, SEVERE |
| `code` | String(50) | Condition code |
| `code_system` | String(20) | Code system |
| `code_display` | String(300) | Display name |
| `code_display_ar` | String(300) | Arabic display |
| `icd10_code` | String(20) | ICD-10 code |
| `icd10_description` | String(500) | ICD-10 description |
| `body_site` | String(200) | Anatomical location |
| `laterality` | String(20) | LEFT, RIGHT, BILATERAL |
| `onset_date` | Date | Onset |
| `abatement_date` | Date | Resolution/abatement |
| `notes` | Text | Clinical notes |

---

## 5. Allergies Model

**Table:** `ehr_allergies`  
**Model class:** `AllergyIntolerance`  
**App location:** `app/ehr/models/allergy.py`

### Fields

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(26) PK | ULID primary key |
| `patient_id` | FK → national_patients | Patient |
| `citizen_id` | FK → national_citizens (nullable) | Citizen |
| `encounter_id` | FK → national_encounters (nullable) | Encounter |
| `practitioner_id` | FK → national_practitioners (nullable) | Practitioner |
| `allergy_type` | String(50) | ALLERGY, INTOLERANCE |
| `category` | String(50) | FOOD, MEDICATION, ENVIRONMENT, BIOLOGIC |
| `criticality` | String(50) | LOW, HIGH, UNABLE_TO_ASSESS |
| `code` | String(50) | Allergy code |
| `code_system` | String(20) | Code system |
| `code_display` | String(300) | Display name |
| `code_display_ar` | String(300) | Arabic display |
| `severity` | Enum(AllergySeverity) | MILD, MODERATE, SEVERE, LIFE_THREATENING |
| `status` | Enum(AllergyStatus) | ACTIVE, RESOLVED, CONFIRMED, REFUTED, ENTERED_IN_ERROR |
| `verification_status` | String(50) | UNCONFIRMED, CONFIRMED, REFUTED |
| `reaction` | String(500) | Reaction description |
| `reaction_details` | JSON | Structured reaction data |
| `onset_date` | Date | When allergy first observed |
| `last_occurrence_date` | Date | Most recent reaction |
| `notes` | Text | Clinical notes |

---

## 6. Medications Model

Four-table medication suite covering the complete medication use lifecycle
from prescription to administration.

### 6.1 MedicationStatement

**Table:** `ehr_medication_statements`  
**Model class:** `MedicationStatement`

Records medications a patient is currently taking or has taken (patient-reported
or clinician-confirmed).

| Column | Type | Description |
|--------|------|-------------|
| `medication_code` | String(50) | Medication code |
| `medication_name` | String(300) | Medication name |
| `medication_name_ar` | String(300) | Arabic name |
| `medication_brand` | String(200) | Brand name |
| `medication_form` | String(100) | TABLET, CAPSULE, INJECTION, etc. |
| `strength_value` | String(50) | Strength (e.g., "500") |
| `strength_unit` | String(50) | Unit (e.g., "mg") |
| `dosage_text` | String(300) | Dosage instructions |
| `route` | String(100) | ORAL, IV, IM, SC, etc. |
| `frequency` | String(200) | BID, TID, QD, etc. |
| `timing` | JSON | Structured timing |
| `status` | String(50) | ACTIVE, COMPLETED, STOPPED |
| `date_started` | Date | Start date |
| `date_ended` | Date | End date |
| `reason_code` | String(50) | Reason for medication |

### 6.2 MedicationRequest

**Table:** `ehr_medication_requests`  
**Model class:** `MedicationRequest`

Represents a prescription or medication order.

| Column | Type | Description |
|--------|------|-------------|
| `prescriber_id` | FK → national_practitioners | Prescribing clinician |
| `medication_code` | String(50) | Medication code |
| `status` | Enum(MedicationOrderStatus) | DRAFT, ACTIVE, COMPLETED, DISCONTINUED, CANCELLED |
| `intent` | String(50) | ORDER, PLAN, PROPOSAL |
| `priority` | String(20) | ROUTINE, URGENT, ASAP, STAT |
| `dosage_instruction` | Text | Dosage instructions |
| `dosage_instructions` | JSON | Structured dosage |
| `quantity` | Integer | Quantity prescribed |
| `quantity_unit` | String(50) | Unit |
| `refills` | Integer | Number of refills |
| `duration_days` | Integer | Treatment duration |
| `authored_on` | DateTime | When prescribed |
| `valid_from` | Date | Prescription valid from |
| `valid_to` | Date | Prescription valid to |
| `substitution_allowed` | Boolean | Generic substitution |

### 6.3 MedicationDispense

**Table:** `ehr_medication_dispenses`  
**Model class:** `MedicationDispense`

Records the supply of medication to a patient.

| Column | Type | Description |
|--------|------|-------------|
| `medication_request_id` | FK → ehr_medication_requests | Source prescription |
| `dispenser_id` | FK → national_practitioners | Dispensing pharmacist |
| `medication_code` | String(50) | Medication code |
| `status` | String(50) | PREPARED, VERIFIED, DISPENSED |
| `quantity` | Integer | Quantity dispensed |
| `days_supply` | Integer | Days supply |
| `prepared_by` | FK → practitioner | Prep pharmacist |
| `verified_by` | FK → practitioner | Verifying pharmacist |
| `dispensed_at` | DateTime | Dispensing time |
| `lot_number` | String(100) | Lot/batch number |
| `expiry_date` | Date | Expiry date |

### 6.4 MedicationAdministration

**Table:** `ehr_medication_administrations`  
**Model class:** `MedicationAdministration`

Records actual administration of medication to a patient.

| Column | Type | Description |
|--------|------|-------------|
| `medication_request_id` | FK → ehr_medication_requests | Source prescription |
| `administrator_id` | FK → national_practitioners | Administering clinician |
| `medication_code` | String(50) | Medication code |
| `status` | Enum(MedicationAdministrationStatus) | COMPLETED, NOT_DONE, IN_PROGRESS, STOPPED |
| `dose_value` | String(50) | Dose given |
| `dose_unit` | String(50) | Unit |
| `route` | String(100) | Route |
| `site` | String(100) | Administration site |
| `method` | String(100) | Administration method |
| `administration_time` | DateTime | When administered |
| `reason_not_given` | String(500) | Reason if not given |

---

## 7. Care Plans Model

### 7.1 CarePlan

**Table:** `ehr_care_plans`  
**Model class:** `CarePlan`

| Column | Type | Description |
|--------|------|-------------|
| `patient_id` | FK → national_patients | Patient |
| `encounter_id` | FK → national_encounters (nullable) | Encounter context |
| `practitioner_id` | FK → national_practitioners (nullable) | Responsible practitioner |
| `status` | Enum(CarePlanStatus) | DRAFT, ACTIVE, COMPLETED, REVISED, CANCELLED |
| `intent` | String(50) | PLAN, PROPOSAL, ORDER |
| `title` | String(300) | Care plan title |
| `title_ar` | String(300) | Arabic title |
| `description` | Text | Detailed description |
| `period_start` | Date | Plan start |
| `period_end` | Date | Plan end |
| `category` | String(100) | ASSESSMENT, MANAGEMENT, etc. |
| `contributor` | JSON | Contributing practitioners |
| `supporting_info` | JSON | Supporting information |

### 7.2 CarePlanGoal

**Table:** `ehr_care_plan_goals`  
**Model class:** `CarePlanGoal`

| Column | Type | Description |
|--------|------|-------------|
| `care_plan_id` | FK → ehr_care_plans | Parent care plan |
| `description` | String(500) | Goal description |
| `description_ar` | String(500) | Arabic goal |
| `status` | String(50) | IN_PROGRESS, ACHIEVED, NOT_ACHIEVED, CANCELLED |
| `priority` | Integer | Priority order |
| `target_date` | Date | Target achievement date |
| `achievement_date` | Date | Actual achievement date |
| `outcome` | String(500) | Outcome description |
| `measured_by` | String(200) | Measurement method |

### 7.3 CarePlanActivity

**Table:** `ehr_care_plan_activities`  
**Model class:** `CarePlanActivity`

| Column | Type | Description |
|--------|------|-------------|
| `care_plan_id` | FK → ehr_care_plans | Parent care plan |
| `goal_id` | FK → ehr_care_plan_goals (nullable) | Related goal |
| `activity_type` | String(100) | MEDICATION, PROCEDURE, ENCOUNTER, OBSERVATION |
| `code` | String(50) | Activity code |
| `description` | String(500) | Description |
| `status` | String(50) | SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED |
| `scheduled_start` | Date | Scheduled start |
| `scheduled_end` | Date | Scheduled end |
| `performer` | String(26) | Responsible practitioner |

---

## 8. Social History Model

**Table:** `ehr_social_history`  
**Model class:** `SocialHistoryRecord`

| Column | Type | Description |
|--------|------|-------------|
| `smoking_status` | Enum(SmokingStatus) | NEVER, CURRENT, FORMER, PASSIVE, UNKNOWN |
| `smoking_pack_years` | Integer | Pack-year history |
| `smoking_quit_date` | Date | Quit date |
| `alcohol_status` | Enum(AlcoholStatus) | NEVER, CURRENT, FORMER, HEAVY, BINGE |
| `alcohol_frequency` | String(100) | Frequency description |
| `occupation` | String(200) | Current occupation |
| `occupation_history` | JSON | Past occupations |
| `occupational_hazards` | Text | Hazard exposure |
| `disability_type` | Enum(DisabilityType) | PHYSICAL, VISUAL, HEARING, MENTAL, MULTIPLE, NONE |
| `disability_detail` | String(500) | Disability details |
| `exercise_frequency` | String(50) | Exercise frequency |
| `diet_notes` | Text | Dietary information |
| `lifestyle_factors` | JSON | Additional lifestyle data |

---

## 9. Family History Model

**Table:** `ehr_family_history`  
**Model class:** `FamilyHistoryRecord`

| Column | Type | Description |
|--------|------|-------------|
| `relationship` | String(50) | PARENT, SIBLING, CHILD, GRANDPARENT, etc. |
| `relative_name` | String(200) | Relative's name |
| `relative_citizen_id` | String(26) | Relative's citizen ID (if in system) |
| `condition_code` | String(50) | Condition code |
| `condition_display` | String(300) | Condition name |
| `condition_display_ar` | String(300) | Arabic name |
| `icd10_code` | String(20) | ICD-10 code |
| `age_at_onset` | Integer | Relative's age at onset |
| `is_deceased_due_to` | Boolean | Deceased due to condition |
| `notes` | Text | Clinical notes |

---

## 10. Risk Factors Model

**Table:** `ehr_risk_factors`  
**Model class:** `RiskFactorRecord`

| Column | Type | Description |
|--------|------|-------------|
| `risk_type` | String(100) | CARDIOVASCULAR, DIABETES, STROKE, FALLS, etc. |
| `risk_level` | Enum(RiskLevel) | LOW, MODERATE, HIGH, VERY_HIGH |
| `score_name` | String(200) | QRISK3, CHADS2, etc. |
| `score_value` | Float | Calculated score |
| `score_maximum` | Float | Maximum possible score |
| `score_percent` | Float | Percentage of maximum |
| `score_version` | String(50) | Algorithm version |
| `factors` | JSON | Individual risk factor breakdown |
| `recommendations` | Text | Clinical recommendations |
| `assessment_date` | DateTime | Assessment date |
| `next_assessment_date` | Date | Scheduled reassessment |
| `is_high_risk` | Boolean | High risk flag |

---

## 11. Clinical Notes Model

**Table:** `ehr_clinical_notes`  
**Model class:** `ClinicalNote`

| Column | Type | Description |
|--------|------|-------------|
| `note_type` | Enum(ClinicalNoteType) | SOAP, PROGRESS, NURSING, OPERATIVE, CONSULTATION, EMERGENCY, DISCHARGE_SUMMARY |
| `title` | String(300) | Note title |
| `title_ar` | String(300) | Arabic title |
| `content` | Text | Note content |
| `content_format` | String(20) | html, plaintext, markdown |
| `version` | Integer | Version number |
| `prior_version_id` | Self-referencing FK | Previous version |
| `superseded_by_id` | Self-referencing FK | Superseding version |
| `is_final` | Boolean | Finalized |
| `is_signed` | Boolean | Signed |
| `signed_by` | FK → practitioner | Signing practitioner |
| `signed_at` | DateTime | Signature timestamp |
| `cosigned_by` | FK → practitioner | Cosigner |
| `electronic_signature` | Text | Digital signature |
| `signature_hash` | String(128) | Signature verification hash |
| `authored_at` | DateTime | Authoring timestamp |
| `facility_id` | FK → facility | Facility |
| `department_id` | FK → department | Department |
| `tags` | JSON | Note tags |

### Versioning
Clinical notes support full versioning:
- `prior_version_id` links to the previous version
- `superseded_by_id` links to the version that supersedes this one
- When amended, a new note is created with `prior_version_id` pointing to
  the original; the original gets `superseded_by_id` pointing to the new one
- Amendment reason is recorded in the new note

---

## 12. Attachments Model

**Table:** `ehr_clinical_attachments`  
**Model class:** `ClinicalAttachment`

| Column | Type | Description |
|--------|------|-------------|
| `source_type` | String(50) | encounter, clinical_note, lab_result, etc. |
| `source_id` | String(26) | ID of source entity |
| `file_name` | String(300) | Original filename |
| `file_type` | String(100) | File type/extension |
| `file_size_bytes` | Integer | File size |
| `storage_path` | String(500) | Object storage path |
| `storage_bucket` | String(100) | Storage bucket |
| `content_hash` | String(128) | SHA-256 hash |
| `mime_type` | String(100) | MIME type |
| `caption` | String(500) | Caption |
| `caption_ar` | String(500) | Arabic caption |
| `is_watermarked` | Boolean | Watermark applied |
| `is_encrypted` | Boolean | Encrypted at rest |
| `is_confidential` | Boolean | Confidential document |
| `category` | String(50) | LAB_RESULT, IMAGING, SCAN, CONSENT, etc. |
| `sort_order` | Integer | Display order |

---

## 13. Immunizations Model

**Table:** `ehr_immunizations`  
**Model class:** `ImmunizationRecord`

| Column | Type | Description |
|--------|------|-------------|
| `vaccine_code` | String(50) | Vaccine product code |
| `vaccine_code_system` | String(20) | Coding system |
| `vaccine_name` | String(300) | Vaccine name |
| `vaccine_name_ar` | String(300) | Arabic name |
| `administration_date` | DateTime | When given |
| `manufacturer` | String(200) | Manufacturer |
| `lot_number` | String(100) | Lot/batch |
| `expiry_date` | Date | Vaccine expiry |
| `dose_number` | Integer | Dose in series |
| `dose_series` | String(50) | Series name |
| `total_doses` | Integer | Total series doses |
| `route` | String(100) | IM, SC, ID, ORAL |
| `site` | String(100) | LEFT_ARM, RIGHT_ARM, etc. |
| `is_completed` | Boolean | Series complete |
| `status` | String(50) | COMPLETED, NOT_DONE, ENTERED_IN_ERROR |
| `reason_not_given` | String(500) | Contraindication/refusal |
| `adverse_event` | Text | AE description |
| `facility_id` | FK → facility | Administering facility |

---

## 14. Timeline Model

**Table:** `ehr_patient_timeline`  
**Model class:** `PatientTimelineEvent`

The timeline is an event-sourced, materialized view of patient activity.
Events are inserted by various services (encounter, lab, pharmacy) to provide
a unified chronological patient history.

| Column | Type | Description |
|--------|------|-------------|
| `event_type` | Enum(TimelineEventType) | ENCOUNTER, DIAGNOSIS, MEDICATION, LAB_RESULT, IMMUNIZATION, etc. |
| `event_date` | DateTime | When the event occurred |
| `source_type` | String(50) | Source domain (encounter, ehr, lab) |
| `source_id` | String(26) | ID of source record |
| `title` | String(300) | Event title |
| `title_ar` | String(300) | Arabic title |
| `description` | Text | Event details |
| `facility_id` | FK → facility | Facility |
| `practitioner_id` | FK → practitioner | Practitioner |
| `encounter_id` | FK → encounter | Related encounter |
| `severity` | String(50) | INFO, WARNING, CRITICAL |
| `is_highlighted` | Boolean | Highlighted event |
| `is_critical` | Boolean | Critical event (e.g., critical lab result) |
| `icon` | String(50) | Icon identifier |
| `color` | String(20) | Color code |

### Timeline Event Types

| Event Type | Source | Trigger |
|------------|--------|---------|
| ENCOUNTER | Encounter | Encounter created/completed |
| DIAGNOSIS | EHR | Diagnosis added |
| MEDICATION | EHR | Medication prescribed/administered |
| LAB_RESULT | Lab | Result recorded |
| IMMUNIZATION | EHR | Immunization given |
| ALLERGY | EHR | Allergy recorded |
| PROCEDURE | EHR | Procedure performed |
| REFERRAL | Care Continuum | Referral sent/received |
| ADMISSION | Hospital | Patient admitted |
| DISCHARGE | Hospital | Patient discharged |
| TRANSFER | Hospital | Patient transferred |
| CARE_PLAN | EHR | Care plan created/updated |
| CLINICAL_NOTE | EHR | Note authored |

### Indexes
- `ix_ehr_timeline_patient` — patient_id + event_date
- `ix_ehr_timeline_citizen` — citizen_id
- `ix_ehr_timeline_type` — event_type + event_date
- `ix_ehr_timeline_source` — source_type + source_id
- `ix_ehr_timeline_facility` — facility_id
- `ix_ehr_timeline_critical` — is_critical + event_date
