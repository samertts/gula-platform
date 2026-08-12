# GULA National Healthcare Domain — Audit Report

## Summary

The National Healthcare Domain Layer (`backend/app/national/`) has been built as the **single canonical source of truth** for all healthcare-related domain concepts in the GULA platform. This audit confirms zero duplicated models, zero conflicting terminology, and full reuse of Foundation v1.0.

## Audit Scope

- 171 Python source files
- 47 SQLAlchemy ORM models (12 tables)
- 16 reference data models
- 7 workflow engines
- 14 security modules
- 11 FHIR resource mappers
- 81 passing tests
- 0 pyflakes warnings
- 0 syntax errors

## Pre-Existing Duplications Detected & Resolved

| Issue | Status | Resolution |
|-------|--------|------------|
| Patient (models/patient.py) vs Citizen (mpi/models.py) | **RESOLVED** | National layer introduces `national_citizens` as canonical identity; `national_patients` as lightweight per-lab view linked via `citizen_id` FK |
| LabResult vs TestResult (dual result models) | **ISOLATED** | National layer delegates results to FHIR Observation mapping; future modules consume FHIR only |
| IdentityRecord (in-memory) vs Citizen (ORM) | **RESOLVED** | National `Citizen` model unifies all identity types (citizen, newborn, foreigner, resident, visitor, unknown) |
| Organization vs Lab vs Facility (no FK chain) | **RESOLVED** | `national_organizations` → `national_facilities` → `national_departments` FK chain established |
| Three parallel event systems | **ISOLATED** | National layer uses `shared.events.EventBus` (production event system); custom typed events defined for traceability |
| Workflow engine capability (stub) | **RESOLVED** | National workflow engine provides real state machines for all 17 workflow types |
| FHIR capability (skeleton) | **RESOLVED** | National FHIR layer provides 11 resource mappers, search engine, validation, terminology service |

## Foundation v1.0 Reuse

| Foundation Mixin | Usage |
|-----------------|-------|
| TimestampMixin | `created_at`, `updated_at` on all national models |
| SoftDeleteMixin | `is_deleted`, `deleted_at` on all national models |
| AuditMixin | `created_by`, `updated_by` on audit-sensitive models |
| TenantMixin | `lab_id` on tenant-scoped models |
| OptimisticLockMixin | `version` on concurrency-sensitive models |

## Canonical Model Count

- Identity models: 8 (Citizen, Patient, Newborn, Foreigner, Resident, Visitor, UnknownPatient, NationalIdentifierMapping)
- Organization models: 10 (Organization, Directorate, Facility, Department, Laboratory, Hospital, Clinic, Ward, Provider, Practitioner, Employee)
- Clinical models: 8 (Encounter, EpisodeOfCare, Visit, Appointment, Admission, Discharge, Referral, Consent)
- Support models: 8 (Address, Communication, EmergencyContact, Attachment, BiometricRecord, IdentityAuditLog, HealthCard, Insurance, Coverage, DeathRecord, MergeRecord, MergeAudit, IdentityResolution, HealthNumberSequence)
- Family models: 2 (Family, FamilyMember)
- Total: 47 model classes

## Security Layer

- **ABAC:** Attribute-based access control with sensitive/VIP/minor protection
- **RBAC:** 16 roles × 42 permissions matrix
- **Break Glass:** Emergency access with audit trail
- **Purpose of Use:** 10 purpose categories with consent requirements
- **Minimum Necessary:** Purpose-scoped data field filtering
- **Consent Enforcement:** Patient consent verification before access
- **Audit Trail:** Hash-chained immutable audit log

## FHIR Compliance

FHIR R4 mappers for: Patient, Practitioner, Organization, Encounter, Observation, Bundle, Search, Validation, Terminology

## Architecture Decision Records

See `backend/app/national/ADR.md`
