# DOMAIN_BLUEPRINT.md

> **PROGRAM-STABLE-004** — the official Domain Blueprint (Phase 1).
> Generated: 2026-08-06T04:28:40+00:00

## The Rule

Every Domain contains ONLY the eight blueprint sections below. Anything else belongs to Shared Core and must be moved there. Infrastructure (databases, queues, caches, encryption, logging, events, barcodes, QR, files, schedulers) is never a Domain concern.

## Blueprint Sections

| Section | Owns |
|---|---|
| entities | Domain entities, value objects, and aggregates |
| services | Domain services (application + domain logic) |
| policies | Domain policies / invariants / business rules |
| api | Public REST API surface (domain-namespaced) |
| events | Domain events the Domain emits or subscribes to |
| workflows | Domain workflows / state machines |
| reports | Domain reports (built on the Reporting Framework) |
| ui | Domain UI (rendered only inside its own workspace) |

## What a Domain Never Contains

- No database engine / session creation (direct DB coupling is forbidden).
- No queue, cache, encryption, or logging infrastructure.
- No reimplementation of any Shared Core service.
- No cross-domain imports (only versioned contracts).
- No administration of another Domain.
- No shared mutable state.
- No UI outside its own workspace.

## Blueprint Enforcement

The framework rejects any manifest that declares content outside these sections. The certification engine (`no_permission_leakage`, `no_direct_database_coupling`, `no_duplicated_infrastructure`) validates every Domain against this blueprint against the real codebase.

## Current Domain Blueprints

### `laboratory` — GULA Laboratory (v1.0.0)

Workspace: `laboratory`

- **entities:** `Order`, `Sample`, `Analyzer`, `TestDefinition`, `Result`, `QCLevel`
- **services:** `lab_service`, `sample_service`, `test_result_service`, `quality_control_service`
- **policies:** `iso_15189`, `clsi_policy`, `cap_policy`
- **api:** `/lab/orders`, `/lab/samples`, `/lab/results`, `/qc`
- **events:** `order.created`, `sample.collected`, `result.verified`
- **workflows:** `order_workflow`, `sample_workflow`, `verification_workflow`
- **reports:** `lab_workload_report`, `qc_summary_report`
- **ui:** `laboratory_dashboard`, `order_entry`, `result_review`

### `pharmacy` — GULA Pharmacy (v1.0.0)

Workspace: `pharmacy`

- **entities:** `Medication`, `Inventory`, `Dispensing`, `Prescription`
- **services:** `pharmacy_service`, `inventory_service`, `dispensing_service`
- **policies:** `prescription_policy`, `stock_control_policy`
- **api:** `/pharmacy/medications`, `/pharmacy/dispense`
- **events:** `medication.dispensed`, `inventory.low`
- **workflows:** `dispensing_workflow`
- **reports:** `pharmacy_stock_report`, `dispensing_report`
- **ui:** `pharmacy_dashboard`, `dispensing_screen`

### `radiology` — GULA Radiology (v1.0.0)

Workspace: `radiology`

- **entities:** `Study`, `Modality`, `Image`, `RadiologyReport`
- **services:** `radiology_service`, `pacs_service`, `ai_assisted_read`
- **policies:** `dicom_policy`, `radiation_safety_policy`
- **api:** `/radiology/studies`, `/radiology/reports`
- **events:** `study.ordered`, `study.completed`
- **workflows:** `study_workflow`
- **reports:** `radiology_throughput_report`
- **ui:** `radiology_dashboard`, `study_viewer`

### `hospital` — GULA Hospital (v1.0.0)

Workspace: `hospital`

- **entities:** `Encounter`, `Admission`, `Department`, `Bed`, `CarePlan`
- **services:** `hospital_service`, `encounter_service`, `care_continuum_service`
- **policies:** `admission_policy`, `care_continuum_policy`
- **api:** `/hospital/encounters`, `/hospital/admissions`
- **events:** `encounter.started`, `patient.admitted`
- **workflows:** `admission_workflow`, `discharge_workflow`
- **reports:** `hospital_census_report`
- **ui:** `hospital_dashboard`, `patient_flow`

### `blood_bank` — GULA Blood Bank (v1.0.0)

Workspace: `blood_bank`

- **entities:** `Donation`, `BloodUnit`, `Component`, `Crossmatch`
- **services:** `blood_bank_service`, `compatibility_service`
- **policies:** `transfusion_safety_policy`, `donor_safety_policy`
- **api:** `/blood-bank/donations`, `/blood-bank/units`
- **events:** `blood.donated`, `blood.unit_released`
- **workflows:** `donation_workflow`, `transfusion_workflow`
- **reports:** `blood_inventory_report`
- **ui:** `blood_bank_dashboard`

### `public_health` — GULA Public Health (v1.0.0)

Workspace: `public_health`

- **entities:** `SurveillanceCase`, `Immunization`, `Outbreak`, `Alert`
- **services:** `surveillance_service`, `immunization_service`
- **policies:** `notifiable_disease_policy`, `epidemic_response_policy`
- **api:** `/public-health/cases`, `/public-health/alerts`
- **events:** `case.reported`, `outbreak.declared`
- **workflows:** `surveillance_workflow`
- **reports:** `surveillance_dashboard_report`
- **ui:** `public_health_dashboard`

### `insurance` — GULA Insurance (v1.0.0)

Workspace: `insurance`

- **entities:** `Policy`, `Claim`, `Coverage`, `PreAuthorization`
- **services:** `insurance_service`, `claims_service`, `fraud_service`
- **policies:** `claims_policy`, `fraud_detection_policy`
- **api:** `/insurance/claims`, `/insurance/eligibility`
- **events:** `claim.submitted`, `claim.approved`
- **workflows:** `claims_workflow`, `preauth_workflow`
- **reports:** `claims_report`
- **ui:** `insurance_dashboard`

### `emergency` — GULA Emergency (v1.0.0)

Workspace: `hospital`

- **entities:** `EMSIncident`, `Triage`, `CriticalPatient`
- **services:** `ems_service`, `critical_care_service`
- **policies:** `triage_policy`, `critical_care_policy`
- **api:** `/emergency/incidents`, `/emergency/triage`
- **events:** `emergency.incident`, `critical.patient_admitted`
- **workflows:** `triage_workflow`
- **reports:** `emergency_response_report`
- **ui:** `emergency_dashboard`

### `research` — GULA Research (v1.0.0)

Workspace: `research`

- **entities:** `ResearchStudy`, `Cohort`, `BiobankSample`
- **services:** `research_service`, `biomedical_service`, `data_science_service`
- **policies:** `research_ethics_policy`, `data_minimization_policy`
- **api:** `/research/studies`
- **events:** `study.registered`
- **workflows:** `study_workflow`
- **reports:** `research_metrics_report`
- **ui:** `research_dashboard`

### `citizen_portal` — GULA Citizen Portal (v1.0.0)

Workspace: `citizen`

- **entities:** `CitizenAppointment`, `CitizenHealthRecord`
- **services:** `citizen_platform_service`
- **policies:** `citizen_read_only_policy`
- **api:** `/citizen/appointments`, `/citizen/records`
- **events:** `citizen.appointment_booked`
- **workflows:** `appointment_workflow`
- **reports:** `citizen_activity_report`
- **ui:** `citizen_portal`

### `provider_portal` — GULA Provider Portal (v1.0.0)

Workspace: `professional`

- **entities:** `ProviderProfile`, `ProviderSchedule`
- **services:** `provider_portal_service`
- **policies:** `provider_no_admin_policy`
- **api:** `/provider/portal`
- **events:** `provider.activity`
- **workflows:** `provider_workflow`
- **reports:** `provider_activity_report`
- **ui:** `provider_portal`
