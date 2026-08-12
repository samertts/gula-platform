# Changelog — National Healthcare Platform

All notable changes to the National Healthcare Platform domain modules.

---

## MISSION-015: National Health Data Platform (2026-07-15)

### Added

- **Canonical Data Model** — 8 canonical tables (`CanonicalPatient`,
  `CanonicalEncounter`, `CanonicalObservation`, `CanonicalCondition`,
  `CanonicalMedication`, `CanonicalProcedure`, `CanonicalImmunization`,
  `CanonicalAllergy`) for unified analytics across source systems
- **Master Data Management (MDM)** — `GoldenRecord`, `SourceRecord`,
  `MatchEvaluation` models; deterministic, probabilistic, and ML-assisted
  matching algorithms; confidence-based auto-merge and human review workflows
- **Event Store** — `StoredEvent` model with append-only semantics; aggregate
  event streams; snapshot mechanism; sequential event numbering
- **Data Governance** — `DataCatalogEntry`, `RetentionPolicy`, `ConsentDirective`
  models for data lifecycle management
- **Data Lake** — Columnar export pipeline (Parquet) for AI/ML workloads
- **ODS (Operational Data Store)** — Materialized views for operational reporting
- **Streaming Pipeline** — `app/routes/national_streaming.py` with FHIR
  subscription forwarding, HL7 message streaming, change data capture, and
  real-time analytics endpoints
- **AI/ML Data** — `DeidentificationJob`, `FeatureStore`, `FeatureValue`,
  `TrainingDataset`, `VectorEmbedding` models for clinical AI
- **Data Platform Service** — `app/services/data_platform_service.py` (633 lines)
  implementing canonical transformation, MDM operations, streaming ingestion,
  and warehouse queries

### Architecture

- New `app/health_data/` module with canonical/, event_store/, mdm/, ods/,
  warehouse/, streaming/, governance/, data_lake/ subdirectories
- New `app/routes/national_data.py` (943 lines) with golden record management,
  canonical data CRUD, MDM operations, data governance, and deidentification
- New `app/routes/national_streaming.py` (280 lines) for real-time data streaming
- Event store provides immutable audit trail for all platforms
- MDM resolves identity across EHR, Hospital, Care Continuum, and National domains

---

## MISSION-014: Clinical Platform (2026-07-14)

### Added

- **Terminology Service** — 8 code system models (ICD-10, ICD-11, SNOMED CT,
  LOINC, ATC, RxNorm, CPT, UCUM); `TerminologyCode` with hierarchy;
  `TerminologyMapping` for cross-system mappings; `ValueSet` and
  `ValueSetMember` for code collections; `CodeSystem` registry;
  `TerminologyVersion` tracking
- **Clinical Decision Support (CDS)** — `OrderSet` and `OrderSetItem` for
  evidence-based order sets; configurable items with types (lab, imaging,
  medication, procedure); department and condition scoping
- **Clinical Knowledge** — `ClinicalGuideline` with full lifecycle (DRAFT →
  REVIEW → APPROVED → ACTIVE → REVISED → RETIRED); Arabic-first content;
  evidence level rating; version management; reference management
- **Clinical Quality** — `QualityIndicator` with numerator/denominator
  definition; target and benchmark values; department scoping; national
  indicator support; `IndicatorMeasurement` for tracking results over time
- **Research** — Research module skeleton for future clinical trial support
- **Clinical AI** — AI module skeleton for future clinical intelligence
- **Clinical Service** — `app/services/clinical_service.py` (1347 lines) with
  TerminologyService, CDSService, ClinicalKnowledgeService, QualityService,
  ResearchService, and ClinicalAIService
- **Clinical Routes** — `app/routes/clinical.py` (1344 lines) with 80+ endpoints
  covering terminology CRUD, value set management, guideline lifecycle,
  order set management, quality indicator tracking, and CDS evaluation

### Architecture

- New `app/clinical/` module with terminology/, cds/, knowledge/, quality/,
  research/, ai/ subdirectories
- Shared `ClinicalBase = declarative_base()` in `app/clinical/base.py`
- Terminology supports multiple coding systems and cross-system mappings
- Quality indicators support both departmental and national scope
- Guideline lifecycle with proper state transitions

---

## MISSION-013: Care Continuum Platform (2026-07-13)

### Added

- **Referral Network** — `ReferralRequest`, `ReferralResponse`,
  `ReferralTimeline`, `CrossOrgReferral`, `ReferralAttachment` models;
  full referral lifecycle (DRAFT → SENT → ACCEPTED → COMPLETED / CANCELLED);
  cross-organization referral support with consent verification
- **Care Journeys** — `CareJourney`, `FollowUpPlan`, `CareCoordination`,
  `ClinicalHandover`, `TransitionsOfCare`, `CommunityCareRecord`,
  `HomeCarePlan` models; milestone tracking; care team management;
  social determinants of health tracking
- **Chronic Disease Management** — `ChronicDiseaseRegistry`,
  `DiseaseManagementPlan`, `RiskStratification`, `SelfMonitoringRecord`,
  `ClinicalPathwayEnrollment`; supports diabetes, hypertension, CKD, COPD,
  asthma, heart failure, cancer, thyroid, arthritis, mental health
- **Maternal & Child Health** — `PregnancyRecord`, `AntenatalCareVisit`,
  `DeliveryRecord`, `PostnatalCareVisit`, `BreastfeedingRecord`,
  `GrowthMonitoring`, `ChildDevelopmentRecord`; full antenatal to postnatal
  continuum; high-risk pregnancy tracking; newborn care
- **Immunization** — `ImmunizationSchedule`, `VaccinationRecord`,
  `VaccineInventory`, `ColdChainMonitor`, `Contraindication`,
  `ReminderSchedule`; national immunization schedule support; contraindication
  tracking; cold chain monitoring; reminder delivery
- **Primary Care** — `PrimaryCareEncounter`, `FamilyMedicineRecord`,
  `HealthAssessment`, `PreventiveCareRecord`, `CommunityClinicRecord`;
  comprehensive primary care encounter with vitals, diagnosis, treatment plan
- **Public Health** — `HealthProgram`, `ProgramEnrollment`, `ScreeningRecord`,
  `CommunityOutreach`, `HealthEducationSession`, `EpiSurveillance`;
  KPI tracking; budget management; geographic targeting
- **Patient Tasks** — `PatientTask`, `TaskReminder`, `PatientEducation`,
  `EducationalMaterialAssignment`; task assignment with reminders;
  acknowledgement tracking; patient-facing task support
- **Care Continuum Service** — `app/services/care_continuum_service.py`
  (1088 lines) with 60+ service functions
- **Care Continuum Routes** — `app/routes/care_continuum.py` (1017 lines)
  with 50+ endpoints

### Architecture

- New `app/care_continuum/` module with models/, commands/, queries/,
  events/, services/, routes/ subdirectories
- All models inherit from `CareContinuumTenantAuditEntity` with tenant isolation
- Enums: `ReferralDirection`, `ChronicDiseaseType`, `DiseaseSeverity`,
  `PregnancyStatus`, `VaccinationStatus`, `HealthProgramType`,
  `CareProgramStatus`, `FollowUpStatus`, `CareContinuumEventType`
- All models reference `national_patients`, `national_citizens`,
  `national_encounters`, `national_facilities`, `national_practitioners`
  for cross-platform interoperability

---

## MISSION-012: National Hospital Platform (2026-07-12)

### Added

- **Hospital Master Data** — `HospitalMaster` with full facility profile
  (code, name, type, license, contact, address); hospital type classification
- **Physical Hierarchy** — `Campus`, `Building`, `Floor`, `Room`, `Bed`;
  strict tree structure from hospital down to individual bed
- **Bed Management** — `BedAssignment` linking patients to beds with
  admission/discharge timestamps; bed availability status; bed type tracking
- **Organizational Hierarchy** — `Department` (clinical and administrative);
  `Unit` (cross-department); `Clinic` (outpatient); department specialization
- **Operation Theater Management** — `OperationTheater` with scheduling
  attributes; equipment assignments; OT status tracking
- **Medical Equipment** — `MedicalEquipment` registry; maintenance scheduling;
  calibration tracking; equipment assignment to departments
- **Cost Centers** — `CostCenter` for financial tracking; budget allocation;
  cost attribution
- **Appointments** — `Appointment` model for scheduling at department/clinician
  level; appointment status tracking; wait list management
- **Hospital Service** — `app/services/hospital_service.py` (536 lines)
  implementing business logic for all hospital operations
- **Hospital Routes** — `app/routes/hospital.py` (805 lines) with 40+ endpoints

### Architecture

- New `app/hospital/` module with models/, commands/, queries/, events/,
  services/, routes/ subdirectories
- Models inherit from `HospitalBaseEntity` with tenant isolation, audit trail,
  soft delete, and optimistic locking
- Physical and organizational hierarchies are orthogonal for flexible querying
- Bed management integrated with ADT workflow

---

## MISSION-011: National EHR Platform (2026-07-11)

### Added

- **Problem List** — `ProblemListItem` model; active problem tracking with
  clinical and verification status; ICD-10 coding; body site; onset/resolution
- **Conditions** — `ConditionRecord` model; full Condition resource analogue;
  ICD-10 coding; body site with laterality; clinical status lifecycle
- **Diagnoses** — `DiagnosisRecord` model; typed (PRIMARY, SECONDARY,
  COMORBIDITY, COMPLICATION); ICD-10 and SNOMED coding; rank ordering;
  chronic flag; certainty classification
- **Allergies** — `AllergyIntolerance` model; severity (MILD→LIFE_THREATENING);
  status lifecycle (ACTIVE→RESOLVED→CONFIRMED→REFUTED); reaction tracking;
  criticality; verification status
- **Medication Suite** — 4 models: `MedicationStatement` (current/active meds),
  `MedicationRequest` (prescriptions), `MedicationDispense` (fulfillment),
  `MedicationAdministration` (administration records); full FHIR R4 lifecycle
- **Care Plans** — `CarePlan` with goals and activities; status lifecycle
  (DRAFT→ACTIVE→COMPLETED→REVISED); period tracking; contributor management
- **Clinical Notes** — `ClinicalNote` model; SOAP, progress, nursing,
  operative, consultation, emergency, discharge summary types; versioning
  (prior/superseded); digital signature support; cosigner workflow
- **Immunizations** — `ImmunizationRecord` model; vaccine coding with
  manufacturer, lot, expiry; dose series tracking; adverse event reporting
- **Family History** — `FamilyHistoryRecord` model; relationship mapping;
  ICD-10 coded conditions; onset age; deceased-due-to tracking
- **Social History** — `SocialHistoryRecord` model; smoking (status, pack-years,
  quit history); alcohol (status, frequency); occupation; disability;
  exercise; diet; lifestyle factors
- **Risk Factors** — `RiskFactorRecord` model; score-based (name, value,
  maximum, percentage); risk level; assessment scheduling; high-risk flagging
- **Attachments** — `ClinicalAttachment` model; source-linked (encounter, note);
  encrypted/watermarked support; content hashing; multi-bucket storage
- **Patient Timeline** — `PatientTimelineEvent` model; type-based events with
  icons, colors, severity; critical event highlighting; source-linked
  (encounter, note, result); facility-scoped
- **Patient Summary** — Aggregated view combining problem list, allergies,
  medications, immunizations, and recent encounters into a unified summary
- **EHR Service** — `app/services/ehr_service.py` (1325 lines) with 40+
  functions covering all EHR operations
- **EHR Routes** — `app/routes/ehr.py` (2073 lines) with 60+ endpoints
- **FHIR API** — `app/routes/ehr_fhir.py` (1005 lines) with 12+ FHIR R4
  endpoints serving Patient, Encounter, Condition, Observation,
  MedicationRequest, MedicationStatement, CarePlan, Procedure,
  AllergyIntolerance, Immunization, DocumentReference, and Bundle resources

### Architecture

- New `app/ehr/` module with models/, commands/, queries/, events/,
  services/, routes/ subdirectories
- New `EHRBase = declarative_base()` in `app/ehr/base.py`
- All models inherit from `EHRBaseEntity` with ulid PK, FHIR compat,
  versioning, soft delete, and audit trail
- 13 model classes across 12 table files
- All models reference national identity tables for cross-platform linking
