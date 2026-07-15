# Architecture Decision Records — National Healthcare Platform

---

## ADR-001: National EHR on Separate Declarative Base

**Status:** Accepted  
**Date:** 2026-07-14

### Context
The existing application uses a single `declarative_base()` in `database.py`.
Adding ~47 new domain models with class names that may overlap (e.g., `Patient`,
`Consent`) causes `InvalidRequestError: Multiple classes found for path "X"`.
EHR models (ProblemListItem, AllergyIntolerance, CarePlan, etc.) reference
national identity models (Citizen, Patient, Encounter, Practitioner) which
live in a different module with its own base.

### Decision
Create three separate declarative bases:
- `EHRBase = declarative_base()` in `app/ehr/base.py` for EHR clinical models
- `CareContinuumBase = declarative_base()` in `app/care_continuum/base.py`
- `ClinicalBase = declarative_base()` in `app/clinical/base.py`

Foundation mixins (TimestampMixin, SoftDeleteMixin, OptimisticLockMixin) work
correctly across bases because they only define `Column(...)` at class level.
The national domain (`app/national/`) also has its own base, `NationalBase`.

### Consequences
- **Positive:** Models from different domains can have the same class name
  without collisions (e.g., `ImmunizationRecord` in EHR vs immunization in
  Care Continuum lives in different schemas)
- **Positive:** Each domain can evolve its schema independently
- **Positive:** Migrations can be scoped per domain
- **Negative:** Cross-domain foreign keys require explicit schema references
  (`ForeignKey("national_patients.id")` instead of Python class references)
- **Negative:** Domain boundaries are enforced at the schema level, requiring
  explicit coordination for cross-domain queries

---

## ADR-002: EHR Baseline with FHIR R4 Compatibility

**Status:** Accepted  
**Date:** 2026-07-14

### Context
The EHR module must store and serve longitudinal clinical records that are
FHIR R4-compatible. Each model must map cleanly to a FHIR resource or
sub-resource. The models must support Arabic-first content, versioning,
soft-delete, and audit trails.

### Decision
Build all EHR models as direct FHIR R4 resource analogues:

| EHR Model | FHIR R4 Resource | Key FHIR Mapping |
|-----------|-----------------|------------------|
| ProblemListItem | Condition (problem-list-item) | `category` = problem-list-item |
| ConditionRecord | Condition | Full Condition resource |
| DiagnosisRecord | Condition (encounter-diagnosis) | Encounter diagnosis reference |
| AllergyIntolerance | AllergyIntolerance | Complete |
| MedicationStatement | MedicationStatement | Complete |
| MedicationRequest | MedicationRequest | Complete |
| MedicationDispense | MedicationDispense | Complete |
| MedicationAdministration | MedicationAdministration | Complete |
| CarePlan | CarePlan | Complete |
| ClinicalNote | DocumentReference | Composition → DocumentReference |
| ImmunizationRecord | Immunization | Complete |
| FamilyHistoryRecord | FamilyMemberHistory | Complete |
| PatientTimelineEvent | (list/feed) | Timeline as event stream |
| RiskFactorRecord | RiskAssessment | Complete |
| SocialHistoryRecord | Observation (social-history) | Category = social-history |

Each model includes:
- `fhir_id` column for FHIR resource ID
- `fhir_resource_type` column for resource type discriminator
- Soft-delete support (is_deleted, deleted_at)
- Version tracking (version integer)
- `to_dict()` serialization method

### Consequences
- **Positive:** Straightforward FHIR API generation via mappers
- **Positive:** FHIR search parameters map cleanly to table indexes
- **Positive:** Third-party integration requires minimal transformation
- **Negative:** Some FHIR resources map to multiple tables (e.g., Medication
  has 4 tables), increasing join complexity
- **Negative:** FHIR extensions must be stored in JSON metadata columns

---

## ADR-003: Hospital Platform Master Data Model

**Status:** Accepted  
**Date:** 2026-07-14

### Context
The hospital platform must model the complete physical and organizational
hierarchy of healthcare facilities. This includes hospitals, campuses,
buildings, floors, rooms, beds, departments, units, clinics, operation
theaters, medical equipment, and cost centers. The model must support
bed management, patient flow (ADT), and resource scheduling.

### Decision
Model the physical hierarchy as a strict tree:

```
HospitalMaster
  └── Campus
       └── Building
            └── Floor
                 └── Room
                      └── Bed

Department ── independent of physical hierarchy
Unit ── cross-cuts departments
Clinic ── associated with Hospital
OperationTheater ── associated with Hospital
MedicalEquipment ── associated with Hospital
CostCenter ── associated with Hospital
```

ADT is tracked via `BedAssignment` which links a patient to a bed within
a time window. `Appointment` (from `models/organization.py`) provides
scheduling at the department/clinician level.

### Consequences
- **Positive:** Clean physical hierarchy enables precise location tracking
- **Positive:** Bed management is a simple FK relationship
- **Positive:** Reporting can aggregate at any level (hospital → bed)
- **Negative:** Deep joins required for facility-wide queries
- **Negative:** Physical and organizational hierarchies are orthogonal
  (a department may span multiple floors)

---

## ADR-004: Care Continuum Platform with Referral Network

**Status:** Accepted  
**Date:** 2026-07-14

### Context
Healthcare is not confined to a single facility. The Care Continuum Platform
must model cross-facility referrals, chronic disease management across time,
maternal/child health journeys, immunization schedules, public health programs,
and patient tasks. It must participate in the national referral network.

### Decision
Build eight model families that share a common `CareContinuumTenantAuditEntity`:

1. **ReferralNetwork** — `ReferralRequest`, `ReferralResponse`,
   `ReferralTimeline`, `CrossOrgReferral`, `ReferralAttachment` — tracks
   referrals across facilities with status machine (DRAFT → SENT → ACCEPTED →
   COMPLETED / CANCELLED)
2. **CareJourney** — `CareJourney`, `FollowUpPlan`, `CareCoordination`,
   `ClinicalHandover`, `TransitionsOfCare`, `CommunityCareRecord`,
   `HomeCarePlan` — longitudinal care coordination
3. **ChronicDisease** — `ChronicDiseaseRegistry`, `DiseaseManagementPlan`,
   `RiskStratification`, `SelfMonitoringRecord`, `ClinicalPathwayEnrollment`
4. **MaternalChild** — `PregnancyRecord`, `AntenatalCareVisit`,
   `DeliveryRecord`, `PostnatalCareVisit`, `BreastfeedingRecord`,
   `GrowthMonitoring`, `ChildDevelopmentRecord`
5. **Immunization** — `ImmunizationSchedule`, `VaccinationRecord`,
   `VaccineInventory`, `ColdChainMonitor`, `Contraindication`,
   `ReminderSchedule`
6. **PrimaryCare** — `PrimaryCareEncounter`, `FamilyMedicineRecord`,
   `HealthAssessment`, `PreventiveCareRecord`, `CommunityClinicRecord`
7. **PublicHealth** — `HealthProgram`, `ProgramEnrollment`, `ScreeningRecord`,
   `CommunityOutreach`, `HealthEducationSession`, `EpiSurveillance`
8. **PatientTasks** — `PatientTask`, `TaskReminder`, `PatientEducation`,
   `EducationalMaterialAssignment`

### Consequences
- **Positive:** Comprehensive coverage of care continuum use cases
- **Positive:** All models reference national identity (Citizen, Patient,
  Encounter, Facility, Practitioner) for cross-org interoperability
- **Positive:** Referral network supports the national referral workflow
- **Negative:** High model count (50+) increases migration complexity
- **Negative:** Cross-org data sharing requires consent enforcement

---

## ADR-005: Clinical Terminology with Reusable Models

**Status:** Accepted  
**Date:** 2026-07-14

### Context
Clinical systems require standardized terminology (ICD-10, ICD-11, SNOMED CT,
LOINC, ATC, RxNorm, CPT, UCUM) for diagnoses, procedures, labs, medications,
and units. Terminology codes must be versioned, mapped across systems, and
assembled into value sets for CDS and quality measurement.

### Decision
Build a generic terminology model family:

1. **CodeSystem** — registry of supported code systems
2. **TerminologyVersion** — version tracking per code system
3. **TerminologyCode** — individual codes with display, definition, hierarchy
4. **TerminologyMapping** — cross-system code mappings (1:1, 1:N, N:1)
5. **ValueSet** — named collections of codes for specific use cases
6. **ValueSetMember** — membership in value sets
7. **ICD10Code**, **ICD11Code**, **SNOMEDCTCode**, **LOINCCode**,
   **ATCCode**, **RxNormCode**, **CPTCode**, **UCUMCode** — system-specific
   code tables for optimized lookup

On top of terminology, build:
- **ClinicalGuideline** — evidence-based guidelines with versioning
- **OrderSet** — order sets composed of order set items
- **QualityIndicator** — quality measures with numerator/denominator

### Consequences
- **Positive:** Single terminology engine for all code systems
- **Positive:** Cross-system mappings enable semantic interoperability
- **Positive:** Value sets enable CDS rules and quality measurement
- **Negative:** Terminology tables can grow very large (millions of rows)
- **Negative:** Keeping terminology synchronized with upstream sources
  requires a maintenance process

---

## ADR-006: Canonical Data Model for National Data Platform

**Status:** Accepted  
**Date:** 2026-07-14

### Context
The National Health Data Platform must ingest data from multiple source systems
(across all five platforms) and present a unified, queryable view. A canonical
data model is needed to normalize data from disparate sources into a common
format suitable for analytics, reporting, and AI/ML.

### Decision
Implement a three-layer canonical data architecture:

1. **Canonical Tables** — `CanonicalPatient`, `CanonicalEncounter`,
   `CanonicalObservation`, `CanonicalCondition`, `CanonicalMedication`,
   `CanonicalProcedure`, `CanonicalImmunization`, `CanonicalAllergy` —
   normalized representations of clinical data keyed by patient + time
2. **ODS (Operational Data Store)** — aggregated views that join canonical
   data with reference data for operational reporting
3. **Data Lake** — raw event data in columnar format (Parquet) for ad-hoc
   analytics and ML training

Each canonical record stores:
- `source_system` — which platform created the data
- `source_id` — original ID in the source system
- `patient_id` / `citizen_id` — cross-reference to national identity
- `recorded_at` — when the data was recorded
- `effective_period` — when the data is clinically relevant

### Consequences
- **Positive:** Unified query interface across all source systems
- **Positive:** Source system changes do not break downstream analytics
- **Positive:** Enables cross-platform analytics (e.g., lab results + diagnoses)
- **Negative:** ETL latency between source systems and canonical tables
- **Negative:** Schema evolution requires coordinated version bumps

---

## ADR-007: Event Store for Immutable Audit Trail

**Status:** Accepted  
**Date:** 2026-07-14

### Context
Healthcare systems require an immutable, auditable record of all data
accesses and mutations. The national platform must support:
- Compliance with healthcare data regulations
- Forensic audit of all patient data access
- Reconstruction of data state at any point in time
- Detection of unauthorized access

### Decision
Implement an event store in `app/health_data/event_store/` that records every
state-changing operation as an immutable event:

- **`StoredEvent`** table with columns: `event_id`, `event_type`, `aggregate_id`,
  `aggregate_type`, `data` (JSON), `metadata` (JSON), `recorded_at`,
  `principal_id`, `source_ip`, `trace_id`
- Events are append-only — never updated or deleted
- Events are sequentially numbered within each aggregate
- The current state of an aggregate is reconstructible by replaying events
- A snapshot mechanism stores aggregate state every N events for performance

Additionally, the `AuditLog` table (in `audit_log.py`) provides a hash chain
for tamper detection:
- Each log entry contains `previous_hash` and `hash` fields
- Hash is computed over `(previous_hash + timestamp + action + user_id + data)`
- Tampering is detectable by recomputing the chain

### Consequences
- **Positive:** Complete, immutable audit trail for regulatory compliance
- **Positive:** Event sourcing enables CQRS and event-driven architecture
- **Positive:** Tamper detection via hash chain satisfies forensic requirements
- **Negative:** Storage grows without bound (requires archival strategy)
- **Negative:** Reconstructing state from events adds read latency without
  snapshot caching

---

## ADR-008: Master Data Management for Golden Records

**Status:** Accepted  
**Date:** 2026-07-14

### Context
Patients receive care at multiple facilities, resulting in duplicate records
across the system. The platform needs a Master Data Management (MDM) system
to detect, resolve, and maintain golden patient records. This must handle
identity merging across citizens, patients, and foreigner/visitor records.

### Decision
Implement MDM in `app/health_data/mdm/` with the following components:

1. **GoldenRecord** — the canonical patient identity that all duplicates
   resolve to. Stores the best-known attributes from all source records.
2. **SourceRecord** — maps source records (from any domain) to the golden
   record, recording which source contributed each attribute.
3. **MatchEvaluation** — stores pairwise matching results with confidence
   scores from each matching algorithm.

Matching algorithms (in `app/national/services/identity_service.py`):
- Deterministic: exact match on health number, national ID hash
- Probabilistic: weighted scoring on name components, DOB, gender, phone
- ML-assisted: vector embeddings for fuzzy name matching

Merge workflow (in `app/national/workflows/merge_identity_workflow.py`):
1. Candidate detection (automatic or manual)
2. Confidence scoring
3. If score > threshold: auto-merge with audit trail
4. If score between thresholds: flag for human review
5. If score < threshold: no action

### Consequences
- **Positive:** Single source of truth for patient identity
- **Positive:** Auto-merge for high-confidence matches reduces manual work
- **Positive:** Full audit trail for all merges (who, when, why)
- **Negative:** Merged records require cascading updates across all domains
- **Negative:** Rollback of false merges is complex and requires compensation
  workflows
