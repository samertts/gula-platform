# GULA Platform — Master Data Catalog

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Database Tables by Schema](#1-database-tables-by-schema)
2. [FHIR Resource Mappings](#2-fhir-resource-mappings)
3. [Audit Data Domains](#3-audit-data-domains)
4. [Data Classification](#4-data-classification)
5. [Data Lineage](#5-data-lineage)
6. [PII/PHI Inventory](#6-piiphi-inventory)
7. [Retention Policies](#7-retention-policies)

---

## 1. Database Tables by Schema

### 1.1 Public Schema (LIMS — core laboratory operations)

| Table | Model Module | Purpose | Classification | PII | Audit Trail |
|-------|-------------|---------|---------------|-----|-------------|
| `labs` | `backend/app/models/lab.py` | Laboratory organizations | Internal | ❌ | ✅ |
| `lab_users` | `backend/app/models/lab_user.py` | Lab staff accounts | Confidential | ✅ | ✅ |
| `patients` | `backend/app/models/patient.py` | Lab-local patient records | Confidential | ✅ | ✅ |
| `lab_orders` | `backend/app/models/lab_order.py` | Lab test orders | Confidential | ❌ | ✅ |
| `lab_results` | `backend/app/models/lab_result.py` | Test results (clinical) | Confidential | ❌ | ✅ |
| `samples` | `backend/app/models/sample.py` | Patient samples tracking | Confidential | ❌ | ✅ |
| `test_types` | `backend/app/models/test_type.py` | Available test definitions | Internal | ❌ | ❌ |
| `test_results` | `backend/app/models/test_result.py` | Individual test results | Confidential | ❌ | ✅ |
| `audit_logs` | `backend/app/models/audit_log.py` | Immutable audit trail | Internal | ❌ | N/A (is audit) |
| `outbox_events` | `backend/app/models/outbox.py` | Transactional outbox | Internal | ❌ | ❌ |
| `subscriptions` | `backend/app/models/subscription.py` | Lab subscription plans | Confidential | ❌ | ✅ |
| `feature_flags` | `backend/app/models/subscription.py` | Per-lab feature overrides | Internal | ❌ | ✅ |
| `consent` | `backend/app/models/consent.py` | Patient consent records | Confidential | ✅ | ✅ |
| `claims` | `backend/app/models/claim.py` | Insurance claims | Confidential | ❌ | ✅ |
| `quality_control` | `backend/app/models/quality_control.py` | QC measurements | Internal | ❌ | ✅ |
| `ai_interactions` | `backend/app/models/ai_interaction.py` | AI usage audit | Confidential | ❌ | ✅ |
| `organizations` | `backend/app/models/organization.py` | Organizational entities | Internal | ❌ | ✅ |
| `edge_*` | `backend/app/models/edge.py` | Edge device management | Internal | ❌ | ✅ |
| `users` | `backend/app/models/user.py` | Platform users | Confidential | ✅ | ✅ |

### 1.2 National Schema (citizen-facing tables)

| Table | Model Module | Purpose | Classification | PII | Audit |
|-------|-------------|---------|---------------|-----|-------|
| `national_citizens` | `backend/app/national/domain/citizen.py` | Canonical citizen records | Restricted | ✅ (strong) | ✅ |
| `identity_claims` | MPI integration | Lab↔citizen linkage | Restricted | ✅ | ✅ |
| `mpi_merge_audit` | MPI integration | Identity merge decisions | Restricted | ✅ | ✅ |
| `visits` | `backend/app/national/domain/visit.py` | Clinical visits | Confidential | ❌ | ✅ |
| `encounters` | `backend/app/national/domain/encounter.py` | Clinical encounters | Confidential | ❌ | ✅ |
| `appointments` | `backend/app/national/domain/appointment.py` | Patient appointments | Confidential | ❌ | ✅ |
| `admissions` | `backend/app/national/domain/admission.py` | Hospital admissions | Confidential | ❌ | ✅ |
| `addresses` | `backend/app/national/domain/address.py` | Citizen addresses | Confidential | ✅ | ✅ |
| `biometrics` | `backend/app/national/domain/biometrics.py` | Biometric data | Restricted | ✅ | ✅ |
| `family_*` | `backend/app/national/domain/family.py` | Family relationships | Confidential | ✅ | ✅ |
| `health_cards` | `backend/app/national/domain/health_card.py` | Health card records | Restricted | ✅ | ✅ |
| `insurance` | `backend/app/national/domain/insurance.py` | Insurance coverage | Confidential | ✅ | ✅ |

### 1.3 LIMS Domain Tables (from `backend/app/lims/models.py`)

| Table | Purpose | Classification |
|-------|---------|---------------|
| `auto_validation_rules` | Rules for auto-validating results | Internal |
| `calibrations` | Equipment calibrations | Internal |
| `chain_of_custody` | Sample chain of custody | Confidential |
| `consumables` | Lab consumable inventory | Internal |
| `delta_check_rules` | Delta check validation rules | Internal |
| `departments` | Lab departments | Internal |
| `devices` | Lab devices and instruments | Internal |
| `profiles` | Test profile definitions | Internal |
| `panels` | Test panel configurations | Internal |
| `reference_ranges` | Reference range definitions | Internal |
| `reagents` | Reagent inventory | Internal |
| `result_notes` | Clinical notes on results | Confidential |
| `specimen_types` | Specimen type definitions | Internal |
| `storage_conditions` | Sample storage tracking | Internal |

### 1.4 Kernel Platform Tables (from `backend/app/kernel/`)

| Table/Store | Module | Purpose |
|-------------|--------|---------|
| Service registry (in-memory) | `kernel/module/registry.py` | Module registration |
| Capability registry (in-memory) | `kernel/features/capabilities.py` | Capability registration |
| Plugin registry (in-memory) | `kernel/plugin/registry.py` | Plugin catalog |
| Tenant registry (DB-backed) | `kernel/tenant/registry.py` | Tenant configuration |
| Event store (DB-backed) | `kernel/event_bus/store.py` | Event persistence |

---

## 2. FHIR Resource Mappings

| FHIR Resource | GULA Entity | Location | Mapping Completeness |
|---------------|-------------|----------|---------------------|
| Patient | `Citizen` + `Patient` | `backend/app/national/fhir/patient.py` | COMPLETE |
| Practitioner | `LabUser` + `Practitioner` | `backend/app/national/fhir/practitioner.py` | COMPLETE |
| Organization | `Lab` + `Organization` | `backend/app/national/fhir/organization.py` | COMPLETE |
| Observation | `LabResult` | `backend/app/national/fhir/observation.py` | COMPLETE |
| Encounter | `Visit` + `Encounter` | `backend/app/national/fhir/encounter.py` | COMPLETE |
| Bundle | Bulk operations | `backend/app/national/fhir/bundle.py` | COMPLETE |
| SearchParameter | FHIR search | `backend/app/national/fhir/search.py` | COMPLETE |
| ValueSet | Terminology | `backend/app/national/fhir/terminology.py` | COMPLETE |
| OperationOutcome | Error responses | `backend/app/national/fhir/validation.py` | COMPLETE |
| DocumentReference | Clinical documents | Future | NOT STARTED |
| DiagnosticReport | Lab reports | `backend/app/lims/fhir_mappers.py` | PARTIAL |
| ServiceRequest | Lab orders | `backend/app/lims/fhir_mappers.py` | PARTIAL |

---

## 3. Audit Data Domains

| Domain | Audit Table | Audit Granularity | Retention | Hash Chain |
|--------|-------------|-------------------|-----------|------------|
| Authentication | `audit_logs` | Per login/logout | 2 years | ❌ |
| Patient CRUD | `audit_logs` | Per record change | 7 years | ✅ |
| Order CRUD | `audit_logs` | Per order change | 7 years | ✅ |
| Result CRUD | `audit_logs` | Per result change | 7 years | ✅ |
| Validation | `audit_logs` | Per validation action | 7 years | ✅ |
| Identity merge | `mpi_merge_audit` | Per merge decision | Permanent | ✅ |
| Gateway calls | `audit_logs` | Per external API call | 2 years | ❌ |
| Feature changes | `audit_logs` | Per feature flag toggle | 2 years | ❌ |
| Subscription changes | `audit_logs` | Per plan change | 5 years | ❌ |
| AI interactions | `ai_interactions` | Per AI query | 2 years | ❌ |
| Error events | Application logs | Per error | 90 days (log) | N/A |

---

## 4. Data Classification

### 4.1 Classification Levels

| Level | Definition | Examples | Handling Requirements |
|-------|-----------|----------|----------------------|
| 🔴 **RESTRICTED** | Highest sensitivity. Legal/regulatory protection. Data breach would cause severe harm. | National ID (hashed), biometrics, health card numbers, merge audit trail | Encryption at rest (AES-256-GCM), strict access control, full audit, never logged, never exposed in API responses |
| 🟡 **CONFIDENTIAL** | Sensitive operational data. Limited to authorized personnel. | Patient demographics, lab results, insurance info, user accounts, claims | Access control (RBAC + ABAC), audit all mutations, PII encrypted at rest |
| 🟢 **INTERNAL** | Not public but low sensitivity. Internal operations data. | Lab configurations, test types, QC results, feature flags, subscription tiers | Access controlled but limited audit requirements |
| ⚪ **PUBLIC** | Intended for public consumption. | Application name, version, health check status, documentation | No special handling |

### 4.2 Classification by Table

| Table | Classification | Rationale |
|-------|---------------|-----------|
| `national_citizens` | 🔴 RESTRICTED | Canonical identity record |
| `identity_claims` | 🔴 RESTRICTED | Lab↔citizen linkage |
| `mpi_merge_audit` | 🔴 RESTRICTED | Identity merge trail |
| `biometrics` | 🔴 RESTRICTED | Biometric identifiers |
| `health_cards` | 🔴 RESTRICTED | Health card numbers |
| `patients` | 🟡 CONFIDENTIAL | Patient PII |
| `lab_users` | 🟡 CONFIDENTIAL | User accounts |
| `lab_orders` | 🟡 CONFIDENTIAL | Clinical orders |
| `lab_results` | 🟡 CONFIDENTIAL | Clinical results |
| `samples` | 🟡 CONFIDENTIAL | Sample chain of custody |
| `claims` | 🟡 CONFIDENTIAL | Insurance claims |
| `consent` | 🟡 CONFIDENTIAL | Patient consent |
| `labs` | 🟢 INTERNAL | Lab configurations |
| `test_types` | 🟢 INTERNAL | Test definitions |
| `outbox_events` | 🟢 INTERNAL | Event routing |
| `audit_logs` | 🟢 INTERNAL | Audit trail (no PII in details) |

---

## 5. Data Lineage

### 5.1 Core Clinical Flow

```
Lab Device → Device Bridge → Result Service → Validation → Storage
    (ASTM/HL7)   (services/   (routes/        (domain/     (models/
                  device_bridge) results.py)    order_state) lab_result)

Order → Patient → Sample Collection → Result Entry → Validation → Report
 (routes/  (routes/   (routes/         (routes/       (domain/     (services/
 clinical_  patients)  samples)         results)       order_state) pdf_report)
 orders)
```

### 5.2 National Identity Flow

```
LIMS creates patient → MPI Resolve API → Citizen Match/Find → IdentityClaim
  (models/patient)     (services/mpi/)     (mpi/matcher.py)    (identity_claims)
                            ↓
                    Citizen created/merged
                    (national/domain/citizen.py)
                            ↓
                    Outbox event published
                    (services/outbox_service.py)
```

### 5.3 Audit Flow

```
User Action → API Route → Service → Audit Service → AuditLog (DB)
                                  ↘ Audit Context (request_id, user_id, lab_id)
```

### 5.4 Event Flow

```
Business Transaction → OutboxEvent (DB) → OutboxWorker → EventBus → Handler(s)
```

---

## 6. PII/PHI Inventory

### 6.1 Personally Identifiable Information (PII)

| PII Element | Location | Encrypted At Rest | Classification | Retention |
|-------------|----------|-------------------|---------------|-----------|
| Full name (Arabic) | `patients`, `national_citizens`, `lab_users` | ❌ (hashed for matching) | Confidential | Lifetime |
| Full name (English) | `national_citizens` | ❌ | Confidential | Lifetime |
| Father's name | `national_citizens` | ❌ | Confidential | Lifetime |
| Mother's name | `national_citizens` | ❌ | Confidential | Lifetime |
| Date of birth | `patients`, `national_citizens` | ❌ | Confidential | Lifetime |
| Phone number | `patients`, `national_citizens`, `lab_users` | ❌ | Confidential | 2 years after last activity |
| Email | `national_citizens`, `lab_users` | ❌ | Confidential | 2 years after last activity |
| Address | `patients`, `national_citizens`, `addresses` | ❌ | Confidential | Lifetime |
| Photo | `national_citizens` | ❌ | Confidential | Lifetime |

### 6.2 Protected Health Information (PHI)

| PHI Element | Location | Classification | Retention |
|-------------|----------|---------------|-----------|
| Lab test results | `lab_results`, `test_results` | Confidential | 7 years |
| Clinical notes | `result_notes` | Confidential | 7 years |
| Sample tracking | `samples`, `chain_of_custody` | Confidential | 3 years |
| Diagnoses | ICD codes in results | Confidential | 7 years |
| Medical history | `care_continuum` data | Confidential | 7 years |
| Consent records | `consent` | Confidential | 7 years after expiry |

### 6.3 High-Risk Identifiers

| Identifier | Location | Encryption | Access Control |
|------------|----------|------------|----------------|
| National ID (NID) | `patients.national_id` | 🔐 AES-256-GCM | RESTRICTED |
| NID hash | `national_citizens.national_id_hash` | HMAC-SHA256 (not reversible) | RESTRICTED |
| Health number | `national_citizens.health_number` | ❌ (system identifier) | CONFIDENTIAL |
| Biometric data | `biometrics` | 🔐 AES-256-GCM | RESTRICTED |

---

## 7. Retention Policies

### 7.1 Data Retention Schedule

| Data Category | Retention Period | Deletion Method | Legal Basis |
|---------------|-----------------|-----------------|-------------|
| Clinical results | 7 years after report | Soft delete → hard delete after 10 years | Iraqi health regulations |
| Patient records | Lifetime + 10 years after death | Soft delete with merge | National health record |
| User accounts | 90 days after account closure | Soft delete | Operational |
| Audit logs | 7 years | Hard delete after 7 years | Regulatory |
| Identity merge audit | Permanent | Never deleted | Legal |
| Outbox events | 90 days after processing | Hard delete | Operational |
| Session tokens | 24 hours (TTL) | Automatic Redis expiry | Security |
| Idempotency keys | 24 hours (TTL) | Hard delete | Operational |
| Error logs | 90 days | Log rotation | Operational |
| Failed outbox events | 30 days after final failure | Hard delete | Operational |
| AI interactions | 2 years | Hard delete | Operational |

### 7.2 Deletion Procedures

| Method | Description | Example |
|--------|-------------|---------|
| Soft delete | `deleted_at` timestamp set; record hidden from queries | `patients`, `lab_orders` |
| Hard delete | Record permanently removed from database | `outbox_events`, sessions |
| Anonymization | Identifiers replaced with anonymous tokens | Analytics datasets |
| Encryption key destruction | Data remains but decryption key destroyed | PII at rest |

### 7.3 Retention Enforcement

- Daily CRON: `DELETE FROM outbox_events WHERE processed_at < NOW() - INTERVAL '90 days'`
- Monthly CRON: Soft-deleted records older than retention period flagged for hard delete
- Annual review: Retention policy review by Data Protection Officer

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial master data catalog |

**Review Cycle**: This document must be reviewed and updated quarterly or when schema changes are made.
