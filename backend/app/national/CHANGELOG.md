# Changelog — National Healthcare Domain

## national-domain-v1.0 (2026-07-14)

### Added

- **Canonical Healthcare Models** (47 classes across 12 tables)
  - Identity: Citizen, Patient, Newborn, Foreigner, Resident, Visitor, UnknownPatient, NationalIdentifierMapping, HealthNumberSequence
  - Organization: Organization, Directorate, Facility, Department, Laboratory, Hospital, Clinic, Ward, Provider, Practitioner, Employee
  - Clinical: Encounter, EpisodeOfCare, Visit, Appointment, Admission, Discharge, Referral, Consent
  - Family: Family, FamilyMember
  - Support: Address, Communication, EmergencyContact, Attachment, BiometricRecord, IdentityAuditLog
  - Insurance: Insurance, Coverage, HealthCard
  - Records: DeathRecord, MergeRecord, MergeAudit, IdentityResolution

- **Identity Governance**
  - Newborn workflow (birth certificate → temporary health number → citizen)
  - Foreigner workflow (passport + visa → health number)
  - Visitor workflow (passport + visa → temporary health number)
  - Unknown patient workflow (emergency identifier → merge)
  - Identity merge with confidence scoring, human approval, audit chain

- **Family Registry**
  - Family model with ration card mapping
  - FamilyMember with relationship types
  - Guardian relationships (parent, child, spouse, dependent)
  - Historical family tracking

- **National Reference Data** (16 models)
  - Countries, Governorates, Districts, Subdistricts
  - Languages, Nationalities, Specialties, Professions
  - LOINC, SNOMED CT, ICD-10, ICD-11, UCUM
  - FHIR Terminology, Blood Groups, Facility Types

- **Workflow Engine** (7 state machines)
  - Patient Registration, Encounter, Referral
  - Merge Identity, Death Registration
  - Workflow compensation and rollback

- **Healthcare Security** (14 modules)
  - ABAC engine with VIP/Minor/Sensitive protection
  - RBAC with 16 roles × 42 permissions
  - Break Glass emergency access
  - Purpose of Use enforcement
  - Minimum Necessary Access filtering
  - Consent enforcement service
  - Immutable audit chain

- **FHIR Platform** (11 mappers)
  - Patient, Practitioner, Organization, Encounter
  - Observation, Bundle, Search, Validation
  - Terminology Service

- **API Layer** (10 route groups)
  - Citizens, Identity, Family, Encounter, Referral
  - Consent, Health Card, Reference, FHIR, Security

- **Developer Platform**
  - Repository interfaces and implementations
  - Application services
  - CQRS commands and queries
  - DTOs and permissions
  - Policy enforcement

- **Tests** (81 passing)
  - 52 unit tests
  - 2 integration tests
  - 5 security tests
  - 1 performance test
  - 2 FHIR validation tests
  - 3 identity merge tests

### Architecture

- Separate declarative base (`NationalBase`) prevents model conflicts with existing models
- Foundation v1.0 mixins properly inherited (first production use)
- All models: FHIR R4 compatible, versioned, soft-deletable, audit-trailed, optimistically locked
- Offline-ready with ULID primary keys and version-based conflict detection
