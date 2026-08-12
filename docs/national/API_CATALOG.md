# API Catalog — National Healthcare Platform

## Overview

All API endpoints are served by the GULA backend monolith (FastAPI) at
port 8000, fronted by the API gateway at port 8080. Endpoints are organized
by domain module.

**Prefix conventions:**
- `/ehr/*` — Clinical document architecture
- `/hospital/*` — Hospital information system
- `/care-continuum/*` — Continuity of care
- `/clinical/*` — Medical knowledge & decision support
- `/national-data/*` — Analytics, MDM, governance
- `/national-data/streaming/*` — Real-time data feeds
- `/fhir/*` — HL7 FHIR R4 API

---

## 1. EHR Endpoints (85 endpoints)

**Route module:** `app/routes/ehr.py`  
**Service module:** `app/services/ehr_service.py` (1325 lines)  
**Prefix:** `/ehr`

### Clinical Notes (6)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/clinical-notes` | Create a clinical note |
| GET | `/ehr/clinical-notes/{note_id}` | Get a clinical note |
| PUT | `/ehr/clinical-notes/{note_id}` | Update a clinical note |
| DELETE | `/ehr/clinical-notes/{note_id}` | Soft-delete a clinical note |
| GET | `/ehr/patients/{patient_id}/clinical-notes` | List clinical notes for a patient |
| GET | `/ehr/encounters/{encounter_id}/clinical-notes` | List clinical notes for an encounter |

### Allergies (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/allergies` | Create an allergy record |
| GET | `/ehr/allergies/{allergy_id}` | Get an allergy record |
| PUT | `/ehr/allergies/{allergy_id}` | Update an allergy record |
| DELETE | `/ehr/allergies/{allergy_id}` | Soft-delete an allergy record |
| GET | `/ehr/patients/{patient_id}/allergies` | List allergies for a patient |

### Medication Statements (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/medication-statements` | Create a medication statement |
| GET | `/ehr/medication-statements/{stmt_id}` | Get a medication statement |
| PUT | `/ehr/medication-statements/{stmt_id}` | Update a medication statement |
| DELETE | `/ehr/medication-statements/{stmt_id}` | Soft-delete a medication statement |
| GET | `/ehr/patients/{patient_id}/medication-statements` | List medication statements for a patient |

### Medication Requests (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/medication-requests` | Create a medication request |
| GET | `/ehr/medication-requests/{req_id}` | Get a medication request |
| PUT | `/ehr/medication-requests/{req_id}` | Update a medication request |
| DELETE | `/ehr/medication-requests/{req_id}` | Soft-delete a medication request |
| GET | `/ehr/patients/{patient_id}/medication-requests` | List medication requests for a patient |

### Medication Dispenses (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/medication-dispenses` | Create a medication dispense |
| GET | `/ehr/medication-dispenses/{disp_id}` | Get a medication dispense |
| PUT | `/ehr/medication-dispenses/{disp_id}` | Update a medication dispense |
| DELETE | `/ehr/medication-dispenses/{disp_id}` | Soft-delete a medication dispense |
| GET | `/ehr/patients/{patient_id}/medication-dispenses` | List medication dispenses for a patient |

### Medication Administrations (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/medication-administrations` | Create a medication administration |
| GET | `/ehr/medication-administrations/{adm_id}` | Get a medication administration |
| PUT | `/ehr/medication-administrations/{adm_id}` | Update a medication administration |
| DELETE | `/ehr/medication-administrations/{adm_id}` | Soft-delete a medication administration |
| GET | `/ehr/patients/{patient_id}/medication-administrations` | List medication administrations for a patient |

### Care Plans (10)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/care-plans` | Create a care plan |
| GET | `/ehr/care-plans/{plan_id}` | Get a care plan with goals and activities |
| PUT | `/ehr/care-plans/{plan_id}` | Update a care plan |
| DELETE | `/ehr/care-plans/{plan_id}` | Soft-delete a care plan |
| GET | `/ehr/patients/{patient_id}/care-plans` | List care plans for a patient |
| POST | `/ehr/care-plans/{plan_id}/goals` | Add a goal to a care plan |
| PUT | `/ehr/care-plans/goals/{goal_id}` | Update a care plan goal |
| DELETE | `/ehr/care-plans/goals/{goal_id}` | Soft-delete a care plan goal |
| POST | `/ehr/care-plans/{plan_id}/activities` | Add an activity to a care plan |
| PUT | `/ehr/care-plans/activities/{activity_id}` | Update a care plan activity |

### Problem List (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/problem-list` | Add a problem list item |
| GET | `/ehr/problem-list/{item_id}` | Get a problem list item |
| PUT | `/ehr/problem-list/{item_id}` | Update a problem list item |
| DELETE | `/ehr/problem-list/{item_id}` | Soft-delete a problem list item |
| GET | `/ehr/patients/{patient_id}/problem-list` | List problem list items for a patient |

### Conditions (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/conditions` | Create a condition record |
| GET | `/ehr/conditions/{condition_id}` | Get a condition record |
| PUT | `/ehr/conditions/{condition_id}` | Update a condition record |
| DELETE | `/ehr/conditions/{condition_id}` | Soft-delete a condition record |
| GET | `/ehr/patients/{patient_id}/conditions` | List conditions for a patient |

### Diagnoses (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/diagnoses` | Create a diagnosis record |
| GET | `/ehr/diagnoses/{diagnosis_id}` | Get a diagnosis record |
| PUT | `/ehr/diagnoses/{diagnosis_id}` | Update a diagnosis record |
| DELETE | `/ehr/diagnoses/{diagnosis_id}` | Soft-delete a diagnosis record |
| GET | `/ehr/patients/{patient_id}/diagnoses` | List diagnoses for a patient |

### Family History (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/family-history` | Create a family history record |
| GET | `/ehr/family-history/{record_id}` | Get a family history record |
| PUT | `/ehr/family-history/{record_id}` | Update a family history record |
| DELETE | `/ehr/family-history/{record_id}` | Soft-delete a family history record |
| GET | `/ehr/patients/{patient_id}/family-history` | List family history for a patient |

### Social History (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/social-history` | Create a social history record |
| GET | `/ehr/social-history/{record_id}` | Get a social history record |
| PUT | `/ehr/social-history/{record_id}` | Update a social history record |
| DELETE | `/ehr/social-history/{record_id}` | Soft-delete a social history record |
| GET | `/ehr/patients/{patient_id}/social-history` | List social history for a patient |

### Risk Factors (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/risk-factors` | Create a risk factor record |
| GET | `/ehr/risk-factors/{risk_id}` | Get a risk factor record |
| PUT | `/ehr/risk-factors/{risk_id}` | Update a risk factor record |
| DELETE | `/ehr/risk-factors/{risk_id}` | Soft-delete a risk factor record |
| GET | `/ehr/patients/{patient_id}/risk-factors` | List risk factors for a patient |

### Immunizations (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/immunizations` | Create an immunization record |
| GET | `/ehr/immunizations/{immunization_id}` | Get an immunization record |
| PUT | `/ehr/immunizations/{immunization_id}` | Update an immunization record |
| DELETE | `/ehr/immunizations/{immunization_id}` | Soft-delete an immunization record |
| GET | `/ehr/patients/{patient_id}/immunizations` | List immunizations for a patient |

### Attachments (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ehr/attachments` | Create a clinical attachment record |
| GET | `/ehr/attachments/{attachment_id}` | Get a clinical attachment record |
| PUT | `/ehr/attachments/{attachment_id}` | Update a clinical attachment record |
| DELETE | `/ehr/attachments/{attachment_id}` | Soft-delete a clinical attachment record |
| GET | `/ehr/patients/{patient_id}/attachments` | List attachments for a patient |

### Timeline (1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ehr/patients/{patient_id}/timeline` | Get patient's unified clinical timeline |

### Summary (1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ehr/patients/{patient_id}/summary` | Get patient's clinical summary |

---

## 2. Hospital Endpoints (39 endpoints)

**Route module:** `app/routes/hospital.py`  
**Service module:** `app/services/hospital_service.py` (536 lines)  
**Prefix:** `/hospital`

### Hospital Master (5)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals` | List hospitals |
| GET | `/hospital/hospitals/{hospital_id}` | Get hospital |
| POST | `/hospital/hospitals` | Create hospital |
| PUT | `/hospital/hospitals/{hospital_id}` | Update hospital |
| DELETE | `/hospital/hospitals/{hospital_id}` | Deactivate hospital |

### Campus (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/campuses` | List campuses |
| POST | `/hospital/campuses` | Create campus |
| PUT | `/hospital/campuses/{campus_id}` | Update campus |

### Building (2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/campuses/{campus_id}/buildings` | List buildings |
| POST | `/hospital/buildings` | Create building |

### Floor (2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/buildings/{building_id}/floors` | List floors |
| POST | `/hospital/floors` | Create floor |

### Department (4)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/departments` | List departments |
| POST | `/hospital/departments` | Create department |
| PUT | `/hospital/departments/{dept_id}` | Update department |
| DELETE | `/hospital/departments/{dept_id}` | Deactivate department |

### Clinic (2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/clinics` | List clinics |
| POST | `/hospital/clinics` | Create clinic |

### Room (2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/floors/{floor_id}/rooms` | List rooms |
| POST | `/hospital/rooms` | Create room |

### Bed (7)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/rooms/{room_id}/beds` | List beds |
| POST | `/hospital/beds` | Create bed |
| POST | `/hospital/beds/{bed_id}/assign` | Assign patient to bed |
| POST | `/hospital/beds/{bed_id}/discharge` | Discharge patient from bed |
| POST | `/hospital/beds/{bed_id}/transfer` | Transfer patient to another bed |
| GET | `/hospital/beds/occupancy` | Bed occupancy dashboard |
| GET | `/hospital/beds/assignments/history` | Bed assignment history |

### Unit (2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/units` | List units |
| POST | `/hospital/units` | Create unit |

### Operation Theater (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/operation-theaters` | List operation theaters |
| POST | `/hospital/operation-theaters` | Create operation theater |
| PUT | `/hospital/operation-theaters/{ot_id}/status` | Update operation theater status |

### Medical Equipment (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/equipment` | List medical equipment |
| POST | `/hospital/equipment` | Create medical equipment |
| PUT | `/hospital/equipment/{equipment_id}` | Update medical equipment |

### Cost Center (2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/hospitals/{hospital_id}/cost-centers` | List cost centers |
| POST | `/hospital/cost-centers` | Create cost center |

### Appointments (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hospital/appointments` | List hospital appointments |
| POST | `/hospital/appointments` | Create hospital appointment |
| GET | `/hospital/kpis` | Hospital KPIs dashboard |

---

## 3. Care Continuum Endpoints (74 endpoints)

**Route module:** `app/routes/care_continuum.py`  
**Service module:** `app/services/care_continuum_service.py` (1088 lines)  
**Prefix:** `/care-continuum`

### Primary Care (8)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/primary-care/encounters` | Create primary care encounter |
| GET | `/care-continuum/primary-care/encounters/{encounter_id}` | Get primary care encounter |
| GET | `/care-continuum/primary-care/encounters` | List primary care encounters |
| PUT | `/care-continuum/primary-care/encounters/{encounter_id}` | Update primary care encounter |
| POST | `/care-continuum/family-medicine/records` | Create family medicine record |
| GET | `/care-continuum/family-medicine/records` | List family medicine records |
| POST | `/care-continuum/community-clinic/records` | Create community clinic record |
| GET | `/care-continuum/community-clinic/records` | List community clinic records |

### Health Assessments (2)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/health-assessments` | Create health assessment |
| GET | `/care-continuum/health-assessments` | List health assessments |

### Preventive Care (2)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/preventive-care/records` | Create preventive care record |
| GET | `/care-continuum/preventive-care/records` | List preventive care records |

### Referral Network (9)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/referrals` | Create referral request |
| POST | `/care-continuum/referrals/{referral_id}/accept` | Accept referral |
| POST | `/care-continuum/referrals/{referral_id}/reject` | Reject referral |
| POST | `/care-continuum/referrals/{referral_id}/complete` | Complete referral |
| GET | `/care-continuum/referrals` | List referrals |
| GET | `/care-continuum/referrals/{referral_id}/timeline` | Get referral timeline |
| POST | `/care-continuum/referrals/cross-org` | Create cross-organization referral |
| POST | `/care-continuum/referral-responses` | Create referral response |
| GET | `/care-continuum/referrals/analytics` | Get referral network analytics |

### Care Journeys (11)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/care-journeys` | Create care journey |
| GET | `/care-continuum/care-journeys/{journey_id}` | Get care journey |
| GET | `/care-continuum/care-journeys` | List care journeys |
| POST | `/care-continuum/follow-up-plans` | Create follow-up plan |
| GET | `/care-continuum/follow-up-plans` | List follow-up plans |
| POST | `/care-continuum/care-coordination` | Create care coordination |
| GET | `/care-continuum/care-coordination` | List care coordination |
| POST | `/care-continuum/transitions-of-care` | Create transition of care |
| POST | `/care-continuum/clinical-handovers` | Create clinical handover |
| POST | `/care-continuum/home-care-plans` | Create home care plan |
| GET | `/care-continuum/home-care-plans` | List home care plans |

### Community Care (2)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/community-care/records` | Create community care record |
| GET | `/care-continuum/community-care/records` | List community care records |

### Chronic Disease (8)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/chronic-disease/registry` | Add chronic disease registry entry |
| GET | `/care-continuum/chronic-disease/registry` | List chronic disease registry |
| GET | `/care-continuum/chronic-disease/registry/{disease_type}` | Get disease-specific registry |
| POST | `/care-continuum/chronic-disease/management-plans` | Create disease management plan |
| GET | `/care-continuum/chronic-disease/management-plans` | List disease management plans |
| POST | `/care-continuum/chronic-disease/risk-stratifications` | Create risk stratification |
| GET | `/care-continuum/chronic-disease/risk-stratifications` | List risk stratifications |
| POST | `/care-continuum/chronic-disease/self-monitoring` | Create self-monitoring record |

### Maternal & Child Health (10)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/maternal/pregnancies` | Create pregnancy record |
| GET | `/care-continuum/maternal/pregnancies/{pregnancy_id}` | Get pregnancy record |
| GET | `/care-continuum/maternal/pregnancies` | List pregnancy records |
| POST | `/care-continuum/maternal/antenatal-visits` | Create antenatal care visit |
| POST | `/care-continuum/maternal/deliveries` | Create delivery record |
| POST | `/care-continuum/maternal/postnatal-visits` | Create postnatal care visit |
| POST | `/care-continuum/maternal/growth-monitoring` | Create growth monitoring record |
| POST | `/care-continuum/maternal/breastfeeding` | Create breastfeeding record |
| POST | `/care-continuum/maternal/child-development` | Create child development record |
| GET | `/care-continuum/maternal/timeline/{patient_id}` | Get maternal health timeline |

### Immunization (9)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/immunizations/vaccinations` | Create vaccination record |
| GET | `/care-continuum/immunizations/vaccinations` | List vaccination records |
| POST | `/care-continuum/immunizations/schedules` | Create immunization schedule |
| GET | `/care-continuum/immunizations/schedules` | List immunization schedules |
| GET | `/care-continuum/immunizations/missed` | Get missed vaccinations |
| POST | `/care-continuum/immunizations/reminder-schedules` | Create reminder schedule |
| GET | `/care-continuum/immunizations/coverage-stats` | Get immunization coverage stats |
| POST | `/care-continuum/immunizations/cold-chain` | Create cold chain monitor reading |
| POST | `/care-continuum/immunizations/coordinate-ehr` | Coordinate EHR immunization record |

### Public Health (8)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/public-health/programs` | Create health program |
| GET | `/care-continuum/public-health/programs` | List health programs |
| POST | `/care-continuum/public-health/programs/{program_id}/enroll` | Enroll patient in health program |
| POST | `/care-continuum/public-health/screening-campaigns` | Create screening campaign |
| GET | `/care-continuum/public-health/screening-campaigns` | List screening campaigns |
| POST | `/care-continuum/public-health/community-visits` | Create community visit |
| POST | `/care-continuum/public-health/school-health` | Create school health visit |
| POST | `/care-continuum/public-health/occupational-health` | Create occupational health record |
| POST | `/care-continuum/public-health/health-education` | Create health promotion activity |

### Patient Tasks (4)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/care-continuum/patient-tasks` | Create patient task |
| GET | `/care-continuum/patient-tasks` | List patient tasks |
| POST | `/care-continuum/self-follow-up-tasks` | Create self-follow-up task |
| POST | `/care-continuum/educational-materials/assign` | Assign educational material to patient |
| GET | `/care-continuum/patients/{patient_id}/care-gaps` | Detect care gaps for a patient |

---

## 4. Clinical Endpoints (65 endpoints)

**Route module:** `app/routes/clinical.py`  
**Service module:** `app/services/clinical_service.py` (1347 lines)  
**Prefix:** `/clinical`

### Terminology (17)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clinical/terminology/codes` | List terminology codes |
| POST | `/clinical/terminology/codes` | Create terminology code |
| GET | `/clinical/terminology/codes/{code_id}` | Get terminology code |
| PUT | `/clinical/terminology/codes/{code_id}` | Update terminology code |
| DELETE | `/clinical/terminology/codes/{code_id}` | Delete terminology code |
| GET | `/clinical/terminology/versions` | List terminology versions |
| POST | `/clinical/terminology/versions` | Create terminology version |
| POST | `/clinical/terminology/mappings` | Create code mapping |
| GET | `/clinical/terminology/value-sets` | List value sets |
| POST | `/clinical/terminology/value-sets` | Create value set |
| POST | `/clinical/terminology/value-set-members` | Add value set member |
| GET | `/clinical/terminology/code-systems` | List code systems |
| POST | `/clinical/terminology/code-systems` | Register code system |
| GET | `/clinical/terminology/icd10` | List ICD-10 codes |
| GET | `/clinical/terminology/loinc` | List LOINC codes |
| GET | `/clinical/terminology/snomed` | List SNOMED CT codes |
| GET | `/clinical/terminology/fhir/$expand` | Value set expansion |
| GET | `/clinical/terminology/fhir/$lookup` | Code system lookup |

### Knowledge (14)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clinical/knowledge/guidelines` | List clinical guidelines |
| POST | `/clinical/knowledge/guidelines` | Create clinical guideline |
| GET | `/clinical/knowledge/guidelines/{guideline_id}` | Get clinical guideline |
| PUT | `/clinical/knowledge/guidelines/{guideline_id}` | Update clinical guideline |
| GET | `/clinical/knowledge/protocols` | List clinical protocols |
| POST | `/clinical/knowledge/protocols` | Create clinical protocol |
| GET | `/clinical/knowledge/protocols/{protocol_id}` | Get clinical protocol |
| PUT | `/clinical/knowledge/protocols/{protocol_id}` | Update clinical protocol |
| GET | `/clinical/knowledge/pathways` | List clinical pathways |
| POST | `/clinical/knowledge/pathways` | Create clinical pathway |
| GET | `/clinical/knowledge/pathways/{pathway_id}` | Get clinical pathway |
| PUT | `/clinical/knowledge/pathways/{pathway_id}` | Update clinical pathway |
| POST | `/clinical/knowledge/guidelines/{guideline_id}/approvals` | Approve guideline |
| GET | `/clinical/knowledge/standing-orders` | List standing orders |
| POST | `/clinical/knowledge/standing-orders` | Create standing order |
| GET | `/clinical/knowledge/recommendations` | List clinical recommendations |

### CDS (8)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/clinical/cds/order-set-recommendations` | Order set recommendations |
| POST | `/clinical/cds/contraindication-check` | Contraindication check |
| POST | `/clinical/cds/duplicate-order-check` | Duplicate order check |
| POST | `/clinical/cds/drug-interaction-check` | Drug interaction check |
| POST | `/clinical/cds/alerts` | Create CDS alert |
| GET | `/clinical/cds/alerts` | List CDS alerts |
| PUT | `/clinical/cds/alerts/{alert_id}/acknowledge` | Acknowledge CDS alert |
| GET | `/clinical/cds/reminders` | List CDS reminders |
| POST | `/clinical/cds/care-bundle-compliance` | Care bundle compliance check |

### Quality (12)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clinical/quality/indicators` | List quality indicators |
| POST | `/clinical/quality/indicators` | Create quality indicator |
| POST | `/clinical/quality/measurements` | Record indicator measurement |
| GET | `/clinical/quality/audit-records` | List quality audit records |
| POST | `/clinical/quality/audit-records` | Create quality audit record |
| POST | `/clinical/quality/compliance-checks` | Run compliance check |
| GET | `/clinical/quality/compliance-checks` | List compliance checks |
| GET | `/clinical/quality/benchmarks` | List quality benchmarks |
| POST | `/clinical/quality/mortality-reviews` | Create mortality review |
| POST | `/clinical/quality/incident-reports` | Create incident report |
| POST | `/clinical/quality/safety-events` | Record safety event |
| GET | `/clinical/quality/dashboard` | Quality dashboard |

### Research (4)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/clinical/research/registries` | Create research registry |
| GET | `/clinical/research/registries` | List research registries |
| POST | `/clinical/research/cohorts` | Create research cohort |
| GET | `/clinical/research/cohorts` | List research cohorts |
| POST | `/clinical/research/export-deidentified` | Export deidentified data |

### Clinical AI (5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/clinical/ai/copilot` | Clinical AI co-pilot |
| POST | `/clinical/ai/risk-prediction` | Risk prediction |
| POST | `/clinical/ai/care-gaps` | AI-powered care gap detection |
| POST | `/clinical/ai/diagnostic-assistant` | Diagnostic assistant |
| POST | `/clinical/ai/explain` | AI explanation |

---

## 5. National Data Platform Endpoints (34 endpoints)

**Route module:** `app/routes/national_data.py`  
**Service module:** `app/services/data_platform_service.py` (633 lines)  
**Prefix:** `/national-data`

### Canonical Data (7)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/national-data/canonical/patients` | List canonical patient records |
| GET | `/national-data/canonical/patients/{patient_id}` | Get canonical patient record |
| GET | `/national-data/canonical/encounters` | List canonical encounter records |
| GET | `/national-data/canonical/encounters/{encounter_id}` | Get canonical encounter record |
| POST | `/national-data/canonical/encounters` | Record a canonical encounter |
| GET | `/national-data/canonical/observations` | List canonical observations |
| GET | `/national-data/canonical/observations/{observation_id}` | Get canonical observation |
| POST | `/national-data/canonical/observations` | Record a canonical observation |

### MDM / Golden Records (5)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/national-data/mdm/golden-records` | List golden records |
| POST | `/national-data/mdm/golden-records` | Create golden record |
| GET | `/national-data/mdm/golden-records/{golden_id}` | Resolve a golden record |
| POST | `/national-data/mdm/duplicate-check` | Check for duplicate records |
| POST | `/national-data/mdm/merge` | Perform merge action |

### Event Store (2)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/national-data/events` | Record an event |
| GET | `/national-data/events/{aggregate_type}/{aggregate_id}` | Replay events for aggregate |

### Governance (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/national-data/governance/catalog` | List data catalog entries |
| POST | `/national-data/governance/catalog` | Create data catalog entry |
| POST | `/national-data/governance/quality-checks` | Record data quality check |
| GET | `/national-data/governance/lineage/{entity_type}/{entity_id}` | Get data lineage |
| POST | `/national-data/governance/lineage` | Record data lineage entry |
| GET | `/national-data/governance/retention-policies` | List retention policies |
| POST | `/national-data/governance/retention-policies` | Create retention policy |
| GET | `/national-data/governance/consent-directives` | List consent directives |
| POST | `/national-data/governance/consent-directives` | Create consent directive |

### AI/ML Data (8)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/national-data/ai/deidentification-jobs` | Create de-identification job |
| GET | `/national-data/ai/deidentification-jobs` | List de-identification jobs |
| GET | `/national-data/ai/feature-store` | List feature definitions |
| POST | `/national-data/ai/feature-store` | Create feature definition |
| POST | `/national-data/ai/feature-values` | Store feature values |
| GET | `/national-data/ai/feature-values/{entity_id}` | Get feature values for entity |
| GET | `/national-data/ai/training-datasets` | List training datasets |
| POST | `/national-data/ai/training-datasets` | Create training dataset |
| GET | `/national-data/ai/vector-embeddings/{entity_id}` | List vector embeddings for entity |
| POST | `/national-data/ai/vector-embeddings` | Store vector embedding |

---

## 6. Streaming Endpoints (5 endpoints)

**Route module:** `app/routes/national_streaming.py`  
**Prefix:** `/national-data/streaming`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/national-data/streaming/fhir-subscription` | FHIR subscription endpoint |
| POST | `/national-data/streaming/hl7` | HL7 message streaming endpoint |
| POST | `/national-data/streaming/events` | Event streaming endpoint |
| POST | `/national-data/streaming/cdc` | Change Data Capture feed |
| POST | `/national-data/streaming/cdc/records` | Record CDC change |

---

## 7. FHIR Endpoints (20+ endpoints)

**Route module:** `app/routes/ehr_fhir.py`  
**Prefix:** `/fhir`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/fhir/Patient/{id}` | Read Patient resource |
| GET | `/fhir/Patient` | Search Patient resources |
| POST | `/fhir/Patient` | Create Patient resource |
| GET | `/fhir/Encounter/{id}` | Read Encounter resource |
| GET | `/fhir/Encounter` | Search Encounter resources |
| POST | `/fhir/Encounter` | Create Encounter resource |
| GET | `/fhir/Condition/{id}` | Read Condition resource |
| GET | `/fhir/Condition` | Search Condition resources |
| GET | `/fhir/Observation/{id}` | Read Observation resource |
| GET | `/fhir/Observation` | Search Observation resources |
| POST | `/fhir/Observation` | Create Observation resource |
| GET | `/fhir/MedicationRequest/{id}` | Read MedicationRequest resource |
| GET | `/fhir/MedicationRequest` | Search MedicationRequest resources |
| GET | `/fhir/MedicationStatement/{id}` | Read MedicationStatement resource |
| GET | `/fhir/MedicationStatement` | Search MedicationStatement resources |
| GET | `/fhir/CarePlan/{id}` | Read CarePlan resource |
| GET | `/fhir/CarePlan` | Search CarePlan resources |
| GET | `/fhir/Procedure/{id}` | Read Procedure resource |
| GET | `/fhir/Procedure` | Search Procedure resources |
| GET | `/fhir/AllergyIntolerance/{id}` | Read AllergyIntolerance resource |
| GET | `/fhir/AllergyIntolerance` | Search AllergyIntolerance resources |
| GET | `/fhir/Immunization/{id}` | Read Immunization resource |
| GET | `/fhir/Immunization` | Search Immunization resources |
| GET | `/fhir/DocumentReference/{id}` | Read DocumentReference resource |
| GET | `/fhir/DocumentReference` | Search DocumentReference resources |
| GET | `/fhir/ConceptMap` | List concept maps |
| GET | `/fhir/ValueSet` | List value sets |
| POST | `/fhir/ValueSet` | Create value set |
| GET | `/fhir/ValueSet/{id}/$expand` | Value set expansion |
| GET | `/fhir/CodeSystem` | List code systems |
| GET | `/fhir/$lookup` | Code system lookup |
| GET | `/fhir/$validate-code` | Code validation |
| GET | `/fhir/_capabilities` | Capability statement |
| GET | `/fhir/_metadata` | Server metadata |

---

## API Summary

| Module | Endpoint Count | Service Lines | Route Lines |
|--------|---------------|---------------|-------------|
| EHR | 85 | 1325 | 2073 |
| Hospital | 39 | 536 | 805 |
| Care Continuum | 74 | 1088 | 1017 |
| Clinical | 65 | 1347 | 1344 |
| National Data | 34 | 633 | 943 |
| Streaming | 5 | — | 280 |
| FHIR | 20+ | — | 1005 |
| **Total** | **322+** | **4929** | **7467** |
