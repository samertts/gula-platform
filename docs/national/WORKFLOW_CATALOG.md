# Workflow Catalog — National Healthcare Platform

## Overview

The platform uses a **workflow engine** in `app/national/workflows/` with a
canonical runtime: `backend/app/workflows/engine.py::WorkflowEngine`, exposed
over HTTP at **`/niam/workflows`** (via `app/identity/workflows/routes.py`).
Each workflow is a state machine with typed steps and compensation support.
The earlier broken `app/national/workflow_runtime/` package (0-byte service)
was archived in Commit 3.6 (ADR-036); the canonical engine is the single live
workflow implementation.

**Workflow Base:** `app/national/workflows/base.py`  
**Runtime:** `backend/app/workflows/engine.py` → `/niam/workflows`  
**Workflow Implementations:**
- `patient_registration.py`
- `encounter_workflow.py`
- `referral_workflow.py`
- `merge_identity_workflow.py`
- `death_registration_workflow.py`

---

## 1. Patient Admission Workflow

**Workflow class:** `PatientRegistrationWorkflow`  
**File:** `app/national/workflows/patient_registration.py`

### States

```
REGISTRATION_STARTED → IDENTITY_VERIFICATION → DOCUMENT_COLLECTION →
BIOMETRICS_CAPTURE → ELIGIBILITY_CHECK → HEALTH_NUMBER_ASSIGNMENT →
CONSENT_COLLECTION → REGISTRATION_COMPLETED
```

### Steps

| Step | Action | System | Compensation |
|------|--------|--------|-------------|
| 1. IDENTITY_VERIFICATION | Verify national ID or passport | Identity Service | Log verification failure |
| 2. DOCUMENT_COLLECTION | Upload ID documents | Document Service | Mark documents as obsolete |
| 3. BIOMETRICS_CAPTURE | Capture fingerprints/photo | Biometrics Service | Delete biometric data |
| 4. ELIGIBILITY_CHECK | Check insurance/coverage | Insurance Service | None (read-only) |
| 5. HEALTH_NUMBER_ASSIGNMENT | Assign IQxxxxxxxx number | Health Number Sequence | Release health number |
| 6. CONSENT_COLLECTION | Record consent directives | Consent Service | Revoke consent |
| 7. REGISTRATION_COMPLETED | Create Citizen + Patient | Citizen Service | Soft-delete citizen record |

### Workflow Detail

```python
class PatientRegistrationWorkflow(BaseWorkflow):
    steps = [
        WorkflowStep("IDENTITY_VERIFICATION", verify_identity),
        WorkflowStep("DOCUMENT_COLLECTION", collect_documents),
        WorkflowStep("BIOMETRICS_CAPTURE", capture_biometrics),
        WorkflowStep("ELIGIBILITY_CHECK", check_eligibility),
        WorkflowStep("HEALTH_NUMBER_ASSIGNMENT", assign_health_number),
        WorkflowStep("CONSENT_COLLECTION", collect_consent),
        WorkflowStep("REGISTRATION_COMPLETED", complete_registration),
    ]

    def verify_identity(self, ctx):
        # Check national_id_hash against civil registry
        # Validate document authenticity
        pass

    def assign_health_number(self, ctx):
        # SELECT next value from health_number_sequence
        # Format as IQ + 8 digits
        pass

    def complete_registration(self, ctx):
        # Create Citizen record
        # Create Patient record linked to facility
        # Assign default practitioner
        # Emit PatientRegistered event
        pass
```

### Entry Points
- **Portal:** Self-registration via citizen portal
- **Walk-in:** Front desk registration at facility
- **Emergency:** Simplified registration (unknown patient → merge later)
- **Integration:** Batch import from external registry

### Events Emitted
- `PatientRegistered` — citizen_id, health_number, facility_id
- `HealthNumberAssigned` — citizen_id, health_number
- `IdentityVerified` — citizen_id, verification_method

---

## 2. Referral Workflow

**Workflow class:** `ReferralWorkflow`  
**File:** `app/national/workflows/referral_workflow.py`  
**Domain:** Care Continuum Platform

### States

```
DRAFT → SENT → RECEIVED → REVIEWED → ACCEPTED → IN_PROGRESS →
COMPLETED → CANCELLED
```

### State Machine

```
                ┌──────────┐
                │   DRAFT   │
                └─────┬────┘
                      │ send
                      ▼
                ┌──────────┐
                │   SENT    │
                └─────┬────┘
                      │ receive
                      ▼
                ┌───────────┐
                │  RECEIVED  │
                └─────┬─────┘
                      │ review
                      ▼
            ┌─────────┴─────────┐
            │                   │
            ▼                   ▼
      ┌──────────┐       ┌───────────┐
      │ ACCEPTED │       │  REJECTED │
      └─────┬────┘       └─────┬─────┘
            │ start             │
            ▼                   │
      ┌──────────────┐         │
      │ IN_PROGRESS  │         │
      └──────┬───────┘         │
             │ complete        │
             ▼                 │
      ┌───────────┐            │
      │ COMPLETED │            │
      └───────────┘            │
                               │
                        ┌───────────┐
                        │ CANCELLED │
                        └───────────┘

  DRAFT → SENT → RECEIVED → REVIEWED → ACCEPTED → IN_PROGRESS → COMPLETED
                                         ACCEPTED → IN_PROGRESS → COMPLETED
  Any state → CANCELLED
  RECEIVED → REVIEWED → REJECTED
```

### Steps

| Step | Action | Detail |
|------|--------|--------|
| 1. DRAFT | Referral created | Referring clinician enters reason, clinical summary, attachments |
| 2. SENT | Referral transmitted | Notification sent to receiving facility |
| 3. RECEIVED | Referral received | Receiving facility acknowledges receipt |
| 4. REVIEWED | Clinical review | Receiving clinician reviews referral details |
| 5. ACCEPTED | Referral accepted | Appointment scheduled, patient notified |
| 6. REJECTED | Referral rejected | Reason documented, referring clinician notified |
| 7. IN_PROGRESS | Care delivered | Encounter created, clinical notes recorded |
| 8. COMPLETED | Referral closed | Discharge summary sent back to referrer |
| 9. CANCELLED | Referral cancelled | Either party may cancel with reason |

### Compensation

```python
def compensate(self, ctx):
    # Reverse in reverse order
    if ctx.state == "COMPLETED":
        self.reverse_complete(ctx)
    if ctx.state == "IN_PROGRESS":
        self.reverse_in_progress(ctx)
    if ctx.state in ("ACCEPTED", "REJECTED"):
        self.reverse_decision(ctx)
    if ctx.state == "RECEIVED":
        self.reverse_receipt(ctx)
    if ctx.state == "SENT":
        self.reverse_transmission(ctx)
    # DRAFT requires no compensation
```

### Roles Involved
- **Referring Practitioner** — initiates referral
- **Receiving Practitioner** — accepts/rejects referral
- **Referral Coordinator** — manages referral workflow
- **Patient** — receives notification

### Events Emitted
- `ReferralCreated` — referral_id, patient_id, referring_facility
- `ReferralSent` — referral_id, receiving_facility
- `ReferralAccepted` — referral_id, receiving_practitioner
- `ReferralRejected` — referral_id, reason
- `ReferralCompleted` — referral_id, outcome
- `ReferralCancelled` — referral_id, reason

### SLA Targets
| Priority | Review Time | Appointment Scheduled |
|----------|-------------|---------------------|
| STAT | 15 minutes | 2 hours |
| URGENT | 2 hours | 24 hours |
| ROUTINE | 24 hours | 7 days |

---

## 3. Order Workflow

**Domain:** EHR Platform + Care Continuum  
**Not a dedicated workflow class** — implemented as state machine in
`app/ehr/models/medication.py` and `app/care_continuum/models/referral.py`

### Medication Order Lifecycle

```
DRAFT → ACTIVE → COMPLETED → DISCONTINUED → ENTERED_IN_ERROR
         ACTIVE → CANCELLED
         DRAFT → CANCELLED
```

| State | Description |
|-------|-------------|
| DRAFT | Prescription being composed |
| ACTIVE | Prescription valid, can be dispensed |
| COMPLETED | All dispenses completed |
| DISCONTINUED | Clinician stopped the order |
| CANCELLED | Cancelled before completion |
| ENTERED_IN_ERROR | Recorded in error (data correction) |

### Lab Order Lifecycle

```
REQUESTED → COLLECTED → RECEIVED → IN_PROGRESS → COMPLETED → VERIFIED
              REQUESTED → CANCELLED
              COLLECTED → CANCELLED (specimen compromised)
```

| Step | Action |
|------|--------|
| 1. REQUESTED | Clinician orders lab test |
| 2. COLLECTED | Specimen collected from patient |
| 3. RECEIVED | Lab receives specimen |
| 4. IN_PROGRESS | Test being performed |
| 5. COMPLETED | Result recorded |
| 6. VERIFIED | Result verified by lab director |
| 7. CANCELLED | Order cancelled |

### Referral Order Lifecycle

See Referral Workflow above.

---

## 4. Medication Workflow

**Domain:** EHR Platform  
**Models:** MedicationRequest → MedicationDispense → MedicationAdministration

### Full Medication Lifecycle

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  MedicationRequest │────►│ MedicationDispense│────►│MedicationAdministration│
│  (Prescribe)      │     │ (Dispense)       │     │ (Administer)        │
└──────────────────┘     └──────────────────┘     └──────────────────────┘
```

### Step-by-Step

| Step | Actor | Action | Data Created |
|------|-------|--------|-------------|
| 1. PRESCRIBE | Clinician | Select medication, dosage, duration | MedicationRequest (status=ACTIVE) |
| 2. VERIFY | Pharmacist | Check interactions, allergies, dose | Update MedicationRequest |
| 3. DISPENSE | Pharmacist | Prepare and dispense medication | MedicationDispense (status=DISPENSED) |
| 4. ADMINISTER | Nurse/Clinician | Give medication to patient | MedicationAdministration (status=COMPLETED) |
| 5. DISCONTINUE | Clinician | Stop medication | MedicationRequest (status=DISCONTINUED) |

### Safety Checks (in CDS)

At each step, the CDS engine performs:
- **Step 1 (Prescribe):** Drug-drug interaction check, allergy check,
  duplicate therapy check, dose range check, renal dose adjustment
- **Step 2 (Verify):** Insurance formulary check, therapeutic duplication
- **Step 3 (Dispense):** Quantity limit check, dispense interval check
- **Step 4 (Administer):** Five rights verification (right patient, drug,
  dose, route, time), MAR reconciliation

### Medication Statement

The `MedicationStatement` model represents the patient's reported or
observed medication use. It is updated automatically when:
- A MedicationRequest is prescribed (active medication)
- A MedicationAdministration is recorded (received medication)
- Patient self-reports via portal

---

## 5. Care Plan Workflow

**Domain:** EHR Platform  
**Models:** CarePlan → CarePlanGoal → CarePlanActivity

### States

```
DRAFT → ACTIVE → COMPLETED → CANCELLED
         ACTIVE → REVISED → ACTIVE
         COMPLETED → ENTERED_IN_ERROR
```

### Workflow

| Phase | Action | Detail |
|-------|--------|--------|
| 1. ASSESS | Clinician evaluates patient | Assessment recorded in ClinicalNote |
| 2. PLAN | Set goals and activities | CarePlan created (status=DRAFT) |
| 3. APPROVE | Care team reviews plan | CarePlan (status=ACTIVE) |
| 4. EXECUTE | Activities performed | CarePlanActivity (status=IN_PROGRESS) |
| 5. MONITOR | Progress tracked | Goals measured, outcomes assessed |
| 6. UPDATE | Plan revised if needed | CarePlan (status=REVISED → ACTIVE) |
| 7. COMPLETE | Goals achieved | CarePlan (status=COMPLETED) |

### Goal Lifecycle

```
IN_PROGRESS → ACHIEVED → IMPROVED → WORSENED → NOT_ACHIEVED → CANCELLED
```

### Activity Lifecycle

```
SCHEDULED → IN_PROGRESS → COMPLETED → CANCELLED
```

### Care Plan Types

| Category | Description | Example |
|----------|-------------|---------|
| ASSESSMENT | Diagnostic evaluation | Pre-surgical workup |
| MANAGEMENT | Ongoing treatment | Diabetes management |
| REHABILITATION | Recovery plan | Post-stroke rehab |
| PALLIATIVE | End-of-life care | Hospice plan |
| PREVENTIVE | Prevention plan | Hypertension prevention |

---

## 6. Discharge Workflow

**Domain:** Hospital Platform  
**Models:** Encounter, Admission, Discharge, ClinicalNote (discharge_summary)

### States

```
ADMITTED → IN_CARE → DISCHARGE_PLANNED → DISCHARGE_IN_PROGRESS →
DISCHARGED
             DISCHARGE_PLANNED → DISCHARGE_CANCELLED → IN_CARE
```

### Steps

| Step | Actor | Action | Data Created |
|------|-------|--------|-------------|
| 1. ADMIT | Admission clerk | Register patient arrival | Encounter (status=ARRIVED), Admission record |
| 2. ASSESS | Clinician | Initial assessment | ClinicalNote, DiagnosisRecord |
| 3. TREAT | Care team | Deliver care | Medications, procedures, labs |
| 4. PLAN_DISCHARGE | Case manager | Set discharge criteria | Discharge plan in CarePlan |
| 5. PREPARE_DISCHARGE | Clinician | Write discharge summary | ClinicalNote (discharge_summary) |
| 6. MEDICATION_RECON | Pharmacist | Reconcile medications | MedicationStatement update |
| 7. EDUCATION | Nurse | Patient education | PatientTask, PatientEducation |
| 8. FOLLOW_UP | Case manager | Schedule follow-up | ReferralRequest, FollowUpPlan |
| 9. DISCHARGE | Clinician | Finalize discharge | Encounter (status=COMPLETED), Discharge record |

### Discharge Summary Components

| Component | Source | Required |
|-----------|--------|----------|
| Admission diagnosis | DiagnosisRecord | Yes |
| Discharge diagnosis | DiagnosisRecord | Yes |
| Procedures performed | ClinicalNote (operative) | If applicable |
| Medications at discharge | MedicationStatement | Yes |
| Medication changes | MedicationRequest diff | Yes |
| Lab results summary | LabResult | Recommended |
| Follow-up plan | FollowUpPlan | Yes |
| Referrals | ReferralRequest | If applicable |
| Patient instructions | ClinicalNote | Recommended |

### Events Emitted
- `DischargePlanned` — encounter_id, planned_date
- `DischargeSummaryCompleted` — encounter_id, note_id
- `PatientDischarged` — encounter_id, discharge_date, destination
- `DischargeCancelled` — encounter_id, reason

---

## 7. Transfer Workflow

**Domain:** Hospital Platform  
**Models:** Encounter, BedAssignment, Room, Facility

### States

```
IN_ORIGIN → TRANSFER_INITIATED → TRANSPORT → ARRIVED_AT_DESTINATION →
TRANSFER_COMPLETED
                       TRANSPORT → TRANSFER_CANCELLED → IN_ORIGIN
```

### Steps

| Step | Actor | Action | Detail |
|------|-------|--------|--------|
| 1. ORDER_TRANSFER | Clinician | Order patient transfer | Specify destination (room/bed) |
| 2. NOTIFY | Nurse | Notify receiving unit | Bed availability check |
| 3. PREPARE | Transport | Prepare patient | Clinical handover summary |
| 4. TRANSPORT | Transport | Move patient | Track departure/arrival times |
| 5. RECEIVE | Receiving nurse | Patient handover | Transfer of care documentation |
| 6. COMPLETE | System | Update bed assignments | Release source bed, assign destination bed |

### Transfer Types

| Type | Description | Examples |
|------|-------------|---------|
| Intra-facility | Same hospital, different unit | ICU → Ward, ER → Admission |
| Inter-facility | Different hospitals | Hospital A → Hospital B |
| Inter-ward | Same hospital, different ward | Surgical → Medical |
| Intra-bed | Same room, different bed | Isolation → General |
| Mode change | Inpatient → Outpatient | Scheduled procedure |

### Clinical Handover

For every transfer, a `ClinicalHandover` record is created (Care Continuum)
containing:
- Current condition summary
- Active problems and diagnoses
- Current medications
- Recent lab results
- Pending investigations
- Goals of care
- Code status
- Responsible clinician contact

### Bed Management Integration

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Patient in Bed A │────►│  Transfer Order   │────►│  Patient in Bed B│
│  (source)         │     │  (in transit)    │     │  (destination)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
  Bed A: OCCUPIED          Bed A: RESERVED           Bed A: AVAILABLE
  Bed B: AVAILABLE         Bed B: RESERVED           Bed B: OCCUPIED
```

### Events Emitted
- `TransferOrdered` — encounter_id, source, destination
- `TransferInProgress` — encounter_id, departure_time
- `TransferCompleted` — encounter_id, destination, arrival_time
- `TransferCancelled` — encounter_id, reason

---

## Workflow Engine Architecture

### Base Workflow

```python
class BaseWorkflow(ABC):
    name: str
    steps: list[WorkflowStep]

    async def execute(self, ctx: WorkflowContext) -> WorkflowResult:
        for step in self.steps:
            try:
                await step.handler(ctx)
                ctx.advance(step.name)
            except Exception as e:
                await self.compensate(ctx)
                raise WorkflowError(step.name, e)

    async def compensate(self, ctx: WorkflowContext):
        for step in reversed(self.completed_steps):
            if step.compensator:
                await step.compensator(ctx)
```

### Workflow Runtime

The canonical runtime (`backend/app/workflows/engine.py`, exposed at
`/niam/workflows`) provides:
- **Persistence** — workflow state stored in database for recovery
- **Scheduling** — delayed steps, timeout handling
- **Event emission** — state transitions published to event bus
- **Retry** — configurable retry policy per step
- **Audit** — all state transitions recorded in audit log

(The archived `national/workflow_runtime/` package never provided any of these
at runtime — its `application/service.py` was 0 bytes; every wired
`/national/workflows/*` handler returned HTTP 500. Archived per ADR-036.)

### Cross-Cutting Concerns

| Concern | Implementation |
|---------|---------------|
| **Compensation** | Reverse steps in reverse order |
| **Audit** | Every state transition logged |
| **Timeout** | Configurable per step (default 30s) |
| **Retry** | 3 retries with exponential backoff |
| **Persistence** | Workflow state in canonical `workflow` tables (`app/workflows/models.py`) |
| **Notifications** | State changes published to event bus |
| **Concurrency** | Per-patient serial execution via patient_id lock |
