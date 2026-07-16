# Nursing Platform — Architecture

**Platform:** National Nursing Platform
**Mission:** 026
**Status:** Planned
**Version:** 0.1.0

---

## 1. Overview

The National Nursing Platform provides a dedicated digital workspace for nursing staff across Iraqi healthcare facilities. It is designed as an independent bounded context within the GULA platform, delivering shift management, task assignment, vital signs recording, structured patient assessments, clinical notes, and shift handovers. The platform is **offline-first** and **Arabic-first**, ensuring usability in all clinical environments regardless of connectivity.

### 1.1 Key Objectives

- Provide nursing-specific workflows not covered by generic clinical systems
- Enable structured vital signs collection with configurable Early Warning Score (EWS) calculation
- Support barcode-assisted medication administration (BCMA) with five-rights verification
- Deliver structured nursing assessments over free-text documentation
- Manage nursing shifts, assignments, and patient-nurse ratios
- Facilitate structured shift handovers (SBAR/ISBAR) for care continuity
- Integrate with EHR medication models to avoid duplication of drug data
- Operate offline in wards with intermittent internet connectivity

### 1.2 Scope

| Area | In Scope | Out of Scope |
|------|----------|--------------|
| Shift management | Scheduling, assignment, time tracking | Payroll integration |
| Clinical tasks | Task creation, assignment, completion | Physician order entry |
| Vital signs | Recording, charting, EWS calculation | Diagnostic interpretation |
| Assessments | Structured forms (pain, fall risk, pressure ulcer) | Medical diagnosis |
| Medication admin | BCMA, five rights, e-signature | Pharmacy dispensing |
| Handovers | SBAR-based shift handover | Discharge summaries |
| Notes | Free-text nursing notes | Physician progress notes |
| Care plans | Nursing care plan creation and tracking | Physician care plans |

---

## 2. System Context

```
+------------------------------------------------------------------+
|                      Nursing Platform                               |
|                 (Web + Mobile + Offline PWA)                       |
+------------------------------------------------------------------+
|                                                                     |
|  +---------------------+  +---------------------+  +-------------+ |
|  | Shift Management    |  | Task Management      |  | Vital Signs | |
|  | (Scheduling,        |  | (Assignment,         |  | (Recording, | |
|  |  Assignment, Clock) |  |  Completion, Status) |  |  Charting)  | |
|  +---------------------+  +---------------------+  +-------------+ |
|                                                                     |
|  +---------------------+  +---------------------+  +-------------+ |
|  | Assessments         |  | Medication Admin     |  | Handover    | |
|  | (Pain, Fall Risk,   |  | (BCMA, Five Rights,  |  | (SBAR,      | |
|  |  Pressure Ulcer)    |  |  E-Signature)        |  |  Shift Log) | |
|  +---------------------+  +---------------------+  +-------------+ |
|                                                                     |
|  +---------------------+  +---------------------+  +-------------+ |
|  | Nursing Notes       |  | Care Plans           |  | Dashboard   | |
|  | (Free-text,         |  | (Create, Track,      |  | (KPI,       | |
|  |  Structured Fields) |  |  Evaluate)           |  |  Alerts)    | |
|  +---------------------+  +---------------------+  +-------------+ |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      Nursing Service Layer                          |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  | NursingService      |  | MedicationAdmin-    |  | CareCoordina-| |
|  |                     |  | Service             |  | torService   | |
|  +---------------------+  +---------------------+  +--------------+ |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  | EWS Engine          |  | Sync Engine         |  | Offline Cache| |
|  | (NEWS/qSOFA/MEWS)   |  | (Delta Sync)        |  | (IndexedDB)  | |
|  +---------------------+  +---------------------+  +--------------+ |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      GULA Backend API                                |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  | /nursing/*          |  | /medication/*       |  | /ehr/*       | |
|  | (Nursing endpoints) |  | (EHR medication     |  | (Patient     | |
|  |                     |  |  models)            |  |  data)       | |
|  +---------------------+  +---------------------+  +--------------+ |
+------------------------------------------------------------------+
|                                                                     |
|  +-------------------------------------------------------------+   |
|  |  PostgreSQL 16 (Nursing Tables + EHR Medication Tables)       |   |
|  |  Redis 7 (Cache, Real-time Nurse Alerts)                     |   |
|  +-------------------------------------------------------------+   |
+------------------------------------------------------------------+
```

---

## 3. Module Structure

### 3.1 Backend Module (`backend/app/nursing/`)

```
backend/app/nursing/
├── __init__.py
├── base.py                        # NURSINGBase (separate from hospital models)
├── models/
│   ├── __init__.py
│   ├── nurse_shift.py             # Shift scheduling and assignment
│   ├── shift_assignment.py        # Nurse-patient shift assignments
│   ├── clinical_task.py           # Nursing-specific tasks
│   ├── vital_sign.py              # Vital signs recording
│   ├── vital_sign_observation.py  # Individual observation in a set
│   ├── nursing_assessment.py      # Structured assessment base
│   ├── pain_assessment.py         # Pain scale assessment (0-10, FLACC, etc.)
│   ├── fall_risk_assessment.py    # Morse / Hendrich II fall risk
│   ├── pressure_ulcer_assessment.py # Braden scale for pressure ulcers
│   ├── nursing_note.py            # Free-text nursing notes
│   ├── nursing_care_plan.py       # Care plans and goals
│   ├── medication_administration.py # BCMA record (five rights, e-sign)
│   ├── medication_schedule.py     # Scheduled medication times
│   ├── handover_report.py         # Shift handover (SBAR/ISBAR)
│   └── handover_patient.py        # Per-patient handover details
├── services/
│   ├── __init__.py
│   ├── nursing_service.py         # Core nursing business logic
│   ├── medication_admin_service.py # BCMA workflow
│   ├── care_coordinator_service.py # Task coordination, shift management
│   └── ews_engine.py              # Early Warning Score calculation
└── routes/
    ├── __init__.py
    ├── shifts.py                   # Shift management endpoints
    ├── tasks.py                    # Clinical task endpoints
    ├── vitals.py                   # Vital signs endpoints
    ├── assessments.py              # Assessment endpoints
    ├── medications.py              # Medication administration endpoints
    ├── handovers.py                # Handover endpoints
    ├── notes.py                    # Nursing notes endpoints
    └── care_plans.py               # Care plan endpoints
```

### 3.2 Frontend Module (React/Firebase)

```
frontend-v2/src/nursing/
├── components/
│   ├── ShiftBoard.jsx             # Shift schedule display
│   ├── TaskList.jsx               # Nursing task list
│   ├── VitalSignsChart.jsx        # Vital signs charting
│   ├── AssessmentForm.jsx         # Structured assessment form
│   ├── BCMAWorkflow.jsx           # Barcode medication administration
│   ├── HandoverPanel.jsx          # SBAR handover interface
│   └── NursingDashboard.jsx       # Nurse dashboard with KPIs
├── services/
│   ├── nursingApi.js              # API client for nursing endpoints
│   └── offlineNursingStore.js     # IndexedDB for offline nursing data
└── hooks/
    ├── useShift.js
    ├── useVitals.js
    └── useMedication.js
```

---

## 4. Core Entities (16 Models)

### 4.1 Shift Management (3)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `NurseShift` | `nurse_shifts` | Shift template/definition | shift_type (morning/evening/night), start_time, end_time, max_nurses, department_id |
| `ShiftAssignment` | `shift_assignments` | Nurse assigned to a specific shift | nurse_id, shift_id, assignment_date, role, patient_list, status |
| `ShiftClock` | `shift_clocks` | Clock-in/clock-out records | nurse_id, shift_id, clock_in_time, clock_out_time, total_hours, location |

### 4.2 Clinical Tasks (1)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `NursingTask` | `nursing_tasks` | Nursing-specific tasks | patient_id, task_type, description, priority, status, assigned_to, due_time, department_id, recurring, completed_at |

### 4.3 Vital Signs (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `VitalSignSet` | `vital_sign_sets` | Group of observations taken together | patient_id, recorded_at, recorded_by, location, method, ews_score, ews_category |
| `VitalSignObservation` | `vital_sign_observations` | Individual vital sign measurement | vital_sign_set_id, observation_type (hr, bp_systolic, bp_diastolic, rr, spo2, temp, etc.), value, unit, device_id, notes |

### 4.4 Assessments (3)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `NursingAssessment` | `nursing_assessments` | Base assessment record | patient_id, assessment_type, assessed_at, assessed_by, department_id, overall_score |
| `PainAssessment` | `pain_assessments` | Pain evaluation | assessment_id, pain_scale (numeric/FLACC/PAINAD), pain_score, pain_location, pain_quality, interventions, re_assessment_score |
| `FallRiskAssessment` | `fall_risk_assessments` | Fall risk evaluation | assessment_id, risk_tool (Morse/Hendrich), risk_score, risk_category, interventions |
| `PressureUlcerAssessment` | `pressure_ulcer_assessments` | Pressure ulcer risk (Braden) | assessment_id, sensory_score, moisture_score, activity_score, mobility_score, nutrition_score, friction_score, total_score, risk_category |

### 4.5 Nursing Notes (1)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `NursingNote` | `nursing_notes` | Clinical nursing documentation | patient_id, note_type, content, written_at, written_by, department_id, related_assessment_id, related_vitals_id |

### 4.6 Care Plans (1)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `NursingCarePlan` | `nursing_care_plans` | Nursing care plan with goals | patient_id, diagnosis, goals (JSON array), interventions (JSON array), evaluation, created_by, created_at, status, start_date, end_date |

### 4.7 Medication Administration (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `MedicationAdminRecord` | `medication_admin_records` | Medication administration record | patient_id, medication_id (from EHR), order_id, administered_at, administered_by, dose, route, site, status, barcode_verified, witness_id |
| `MedicationSchedule` | `medication_schedules` | Scheduled medication times | patient_id, medication_id, order_id, scheduled_time, status, admin_record_id |

### 4.8 Handovers (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `HandoverReport` | `handover_reports` | Shift handover document | from_shift_id, to_shift_id, from_nurse_id, to_nurse_id, handover_at, summary, sbar_situation, sbar_background, sbar_assessment, sbar_recommendation |
| `HandoverPatient` | `handover_patients` | Per-patient handover details | handover_report_id, patient_id, diagnosis, pending_tasks, critical_events, medications_due, follow_up_needed |

### 4.9 Dashboard (1)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `NursingDashboardCache` | `nursing_dashboard_cache` | Cached KPI data for nurse dashboard | nurse_id, department_id, shift_id, patient_count, task_count, pending_count, vitals_due, updated_at |

---

## 5. Service Layer

### 5.1 NursingService

The `NursingService` class handles all core nursing business logic:

| Method | Description |
|--------|-------------|
| `create_shift_assignment` | Assign nurse to shift with patient load balancing |
| `get_nurse_schedule` | Get schedule for a nurse within date range |
| `record_vital_signs` | Record a set of vital signs and calculate EWS |
| `create_assessment` | Create a structured assessment with scoring |
| `calculate_ews` | Calculate NEWS, qSOFA, or MEWS from vital signs |
| `get_patient_vitals_history` | Retrieve vitals timeline for a patient |
| `create_nursing_note` | Document nursing note with structured fields |
| `create_care_plan` | Create and track nursing care plans |
| `get_shift_handover` | Generate structured SBAR handover for shift |
| `get_nurse_dashboard` | Aggregate KPI data for nurse dashboard |

### 5.2 Medication Administration Service

The `MedicationAdminService` implements the BCMA workflow:

| Method | Description |
|--------|-------------|
| `verify_five_rights` | Verify right patient, drug, dose, route, time |
| `scan_barcode` | Process barcode scan (patient wristband + medication) |
| `validate_medication` | Validate medication against EHR order |
| `administer_dose` | Record medication administration with e-signature |
| `verify_witness` | Two-nurse verification for controlled substances |
| `get_schedule` | Get pending medication schedule for a patient |
| `get_admin_history` | Get medication administration history |

**Five Rights Verification:**

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Right Patient│────→│ Right Drug   │────→│ Right Dose   │
│ (Wristband   │     │ (Med Barcode │     │ (Order       │
│  Barcode)    │     │  Scan)       │     │  Validation) │
└──────────────┘     └──────────────┘     └──────────────┘
         │                   │                    │
         ↓                   ↓                    ↓
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Right Route  │────→│ Right Time   │────→│  Administer  │
│ (Formulary   │     │ (Schedule    │     │  + E-Sign    │
│  Check)      │     │  Validated)  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 5.3 Care Coordinator Service

The `CareCoordinatorService` manages nursing workflow coordination:

| Method | Description |
|--------|-------------|
| `assign_task` | Assign nursing task to a nurse |
| `reassign_tasks` | Bulk reassign tasks during shift change |
| `get_ward_status` | Real-time ward status (patients, tasks, vitals) |
| `calculate_nurse_patient_ratio` | Calculate current nurse-to-patient ratio |
| `identify_care_gaps` | Identify missed care or overdue tasks |
| `escalate_concern` | Escalate clinical concern to charge nurse/physician |

### 5.4 EWS Engine

The `EWSEngine` calculates Early Warning Scores:

| Score System | Parameters | Thresholds |
|-------------|------------|------------|
| **NEWS2** | RR, SpO2, temperature, BP, HR, consciousness, FiO2 | 0-4: low, 5-6: medium, 7+: high |
| **qSOFA** | RR, SBP, consciousness | 0: low risk, 1-2: high risk |
| **MEWS** | HR, SBP, RR, temperature, consciousness | 0-4: ward, 5-8: ICU step-up, 9+: ICU |

---

## 6. API Endpoints (50+)

### 6.1 Shifts (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/shifts` | List shifts with filters |
| POST | `/nursing/shifts` | Create shift definition |
| PUT | `/nursing/shifts/{id}` | Update shift definition |
| GET | `/nursing/assignments` | List shift assignments |
| POST | `/nursing/assignments` | Assign nurse to shift |
| PUT | `/nursing/assignments/{id}` | Update assignment |
| POST | `/nursing/clock-in` | Nurse clock-in |
| POST | `/nursing/clock-out` | Nurse clock-out |

### 6.2 Tasks (7)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/tasks` | List nursing tasks |
| POST | `/nursing/tasks` | Create task |
| GET | `/nursing/tasks/{id}` | Get task detail |
| PUT | `/nursing/tasks/{id}` | Update task |
| POST | `/nursing/tasks/{id}/complete` | Complete task |
| POST | `/nursing/tasks/{id}/assign` | Assign task |
| GET | `/nursing/tasks/my` | Current user's tasks |

### 6.3 Vital Signs (9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/vitals` | List vital sign sets |
| POST | `/nursing/vitals` | Record vital signs |
| GET | `/nursing/vitals/{id}` | Get vital sign set detail |
| GET | `/nursing/vitals/patient/{patient_id}` | Patient vitals history |
| GET | `/nursing/vitals/patient/{patient_id}/chart` | Chart data for vitals |
| GET | `/nursing/vitals/ews` | EWS scores for patients |
| GET | `/nursing/vitals/ews/{patient_id}` | Patient EWS trend |
| GET | `/nursing/vitals/due` | Patients due for vitals |
| POST | `/nursing/vitals/calculate-ews` | Calculate EWS from observations |

### 6.4 Assessments (9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/assessments` | List assessments |
| POST | `/nursing/assessments` | Create assessment |
| GET | `/nursing/assessments/{id}` | Get assessment detail |
| GET | `/nursing/assessments/patient/{patient_id}` | Patient assessment history |
| POST | `/nursing/assessments/pain` | Record pain assessment |
| POST | `/nursing/assessments/fall-risk` | Record fall risk assessment |
| POST | `/nursing/assessments/pressure-ulcer` | Record pressure ulcer assessment |
| GET | `/nursing/assessments/pain/patient/{patient_id}` | Pain score trend |
| GET | `/nursing/assessments/fall-risk/patient/{patient_id}` | Fall risk history |

### 6.5 Medication Administration (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/medications/schedule` | Medication schedule for ward |
| GET | `/nursing/medications/schedule/{patient_id}` | Patient medication schedule |
| POST | `/nursing/medications/scan` | Process barcode scan |
| POST | `/nursing/medications/verify` | Verify five rights |
| POST | `/nursing/medications/administer` | Record administration |
| POST | `/nursing/medications/{id}/witness` | Witness verification |
| GET | `/nursing/medications/history/{patient_id}` | Administration history |
| PUT | `/nursing/medications/{id}/missed` | Record missed dose |

### 6.6 Handovers (5)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/handovers` | List handover reports |
| POST | `/nursing/handovers` | Create handover report |
| GET | `/nursing/handovers/{id}` | Get handover detail |
| PUT | `/nursing/handovers/{id}` | Update handover |
| GET | `/nursing/handovers/{id}/patients` | Handover patient details |

### 6.7 Notes (5)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/notes` | List nursing notes |
| POST | `/nursing/notes` | Create nursing note |
| GET | `/nursing/notes/{id}` | Get note detail |
| PUT | `/nursing/notes/{id}` | Update note |
| GET | `/nursing/notes/patient/{patient_id}` | Patient's nursing notes |

### 6.8 Care Plans (5)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/care-plans` | List care plans |
| POST | `/nursing/care-plans` | Create care plan |
| GET | `/nursing/care-plans/{id}` | Get care plan detail |
| PUT | `/nursing/care-plans/{id}` | Update care plan |
| GET | `/nursing/care-plans/patient/{patient_id}` | Patient's care plans |

### 6.9 Dashboard (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/dashboard` | Nurse dashboard KPI data |
| GET | `/nursing/dashboard/ward` | Ward-level dashboard |
| GET | `/nursing/dashboard/alerts` | Nursing alerts |

### 6.10 Sync (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nursing/sync/changes` | Get changes since timestamp |
| POST | `/nursing/sync/push` | Push local nursing changes |
| GET | `/nursing/sync/status` | Sync status |

---

## 7. Medication Safety (BCMA)

### 7.1 Five Rights Verification

The BCMA workflow enforces the **five rights** of medication administration:

| Right | Verification Method | Failure Action |
|-------|-------------------|----------------|
| **Right Patient** | Scan patient wristband barcode (MRN or national ID) | Alert: patient mismatch, block administration |
| **Right Medication** | Scan medication barcode (GS1/NDC), match to order | Alert: drug mismatch, block administration |
| **Right Dose** | Validate dose against order (range check) | Warning: dose outside normal range, require override reason |
| **Right Route** | Validate route against order and formulary | Alert: route mismatch, block administration |
| **Right Time** | Validate administration time against schedule window (±60 min) | Warning: outside window, document reason |

### 7.2 Barcode Workflow

```
1. Nurse scans patient wristband
   → System displays patient identity confirmation
   → Patient ID verified in EHR

2. Nurse scans medication barcode
   → System identifies medication and matches to active orders
   → Drug name, dose, route displayed for confirmation

3. System validates five rights
   → All checks pass OR specific overrides documented

4. Nurse confirms administration
   → Electronic signature captured (username + password / biometric)
   → For controlled substances: second nurse witness required

5. System records administration
   → MAR updated, audit log created
   → Next dose scheduled time calculated
```

### 7.3 Electronic Signature

- **Standard administration**: username + password authentication
- **Controlled substances**: two-nurse verification (dual electronic signatures)
- **Override circumstances**: override reason code + electronic signature
- **Audit trail**: every administration event logged with timestamp, user, patient, medication, dose, route, verification status

---

## 8. Integration with EHR Medication Models

### 8.1 Reuse Principle

The Nursing Platform **reuses** existing EHR medication models rather than duplicating them:

| EHR Model | Reused For | Nursing Model |
|-----------|-----------|---------------|
| `medication_orders` (from EHR) | Source of truth for medication orders | `MedicationAdminRecord.order_id` FK references order |
| `medication_formulary` (from EHR) | Drug catalog, dosing, routes | Validated against during BCMA |
| `medication_dispensations` (from Pharmacy) | Dispensed medications | `MedicationAdminRecord.medication_id` FK references dispensation |
| `patients` | Patient identity | FK referenced by all nursing models |
| `lab_users` | Nurse identity | FK referenced by all nursing models |

### 8.2 Data Flow

```
EHR Doctor orders medication
       ↓
Pharmacy receives order, dispenses medication (with barcode)
       ↓
Nurse sees medication on schedule (/nursing/medications/schedule)
       ↓
Nurse scans patient wristband + medication barcode
       ↓
BCMA validates against EHR order, records administration
       ↓
MAR updated in nursing platform AND EHR (via event bus)
```

---

## 9. Reuse Summary

| Component | Reused From | How |
|-----------|-------------|-----|
| EHR medication orders | `ehr_service.py` / EHR models | Referenced by FK in medication administration |
| Patient model | `models/patient.py` | FK in all nursing models |
| LabUser model | `models/lab_user.py` | Nurse identity, task assignment |
| AuditService | `services/audit_service.py` | All nursing mutations logged |
| Auth/JWT | `security/auth.py` | Authentication for API access |
| RBAC | `security/rbac.py` | Permission checks on endpoints |
| Database session | `database.py` | Shared SQLAlchemy engine |
| Encryption | `security/encryption.py` | Patient data encryption |
| Event bus | `core/events.py` | Publish admin events to EHR |
| Notification service | `notifications/` | Nurse alerts, task notifications |

---

## 10. Offline-First Design

### 10.1 Strategy

- **Web**: Service Worker + IndexedDB for React PWA
- **Mobile**: React Native with SQLite local store
- **All operations work offline**: vital signs, assessments, notes, medication admin
- **Sync**: Delta sync with conflict resolution when connectivity returns

### 10.2 Local Cache

| Data | Cache Strategy | Sync |
|------|---------------|------|
| Patient list | Full cache (updated daily) | Delta sync |
| Medication schedule | 24-hour sliding window | Push admin records |
| Vital signs | Record locally, sync immediately when online | Outbox pattern |
| Assessments | Record locally, sync when online | Outbox pattern |
| Task status | Update locally, sync changes | Delta push |
| Handovers | Created locally, synced at shift end | Full push |

### 10.3 Conflict Resolution

- **Vital signs**: Last-writer-wins (per observation timestamp)
- **Assessments**: Last-writer-wins (assessor owns record)
- **Medication admin**: First-writer-wins (prevent double administration)
- **Tasks**: Last-writer-wins (status update)
- **Notes**: Merge strategy (append-only content)

---

## 11. RTL/Arabic-First

- All UI components designed for RTL layout as default
- Translation manager with comprehensive Arabic medical terminology
- Nursing-specific terms in Arabic: vital signs, assessment scales, handover templates
- Date/time formats follow Iraqi conventions
- Right-justified text alignment in all input fields and labels
- Direction-aware icons and spacing
- Print templates (handover, MAR, care plans) in Arabic with RTL rendering

---

## 12. EWS Scoring System

### 12.1 Supported Score Types

| Score | Parameters | Clinical Use |
|-------|-----------|-------------|
| **NEWS2** | RR, SpO2, FiO2, SBP, HR, consciousness, temperature | General ward deterioration detection |
| **qSOFA** | RR ≥22, SBP ≤100, altered mentation | Sepsis screening |
| **MEWS** | HR, SBP, RR, temperature, consciousness | ICU step-up criteria |

### 12.2 Escalation Framework

| EWS Score | Escalation | Monitoring Frequency |
|-----------|-----------|---------------------|
| 0-4 (Low) | Continue ward care | Per ward protocol |
| 5-6 (Medium) | Inform charge nurse, increase monitoring | Q2-4 hours |
| 7+ (High) | Immediate medical review, consider ICU | Q1 hour or continuous |

---

## 13. FHIR Mappings

| Nursing Entity | FHIR Resource | Mapping Notes |
|---------------|---------------|---------------|
| VitalSignSet | `Observation` (group) | category="vital-signs", hasMember to individual observations |
| VitalSignObservation | `Observation` | code (LOINC), valueQuantity, bodySite, device |
| NursingAssessment | `Observation` | category="assessment", code by assessment type |
| PainAssessment | `Observation` | code=loinc 38221-8 (pain severity), value by scale |
| FallRiskAssessment | `RiskAssessment` | method, basis, prediction, mitigation |
| NursingTask | `Task` | code, status, intent, requester, owner |
| MedicationAdminRecord | `MedicationAdministration` | medication, subject, effectiveDateTime, dose, route |
| NursingNote | `DocumentReference` | type="nursing note", content attachment |
| HandoverReport | `DocumentReference` | type="handover report", content with SBAR sections |
| NursingCarePlan | `CarePlan` | category="nursing", title, description, goal |
| ShiftAssignment | `Schedule` + `Slot` | PlanningHorizon, slot for nurse schedule |
