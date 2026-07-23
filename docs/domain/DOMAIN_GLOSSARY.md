# GULA Platform — Domain Glossary

**Version:** 1.0 | **Last Updated:** 2026-07-23

Comprehensive terminology reference for all bounded contexts in the GULA Platform.
Each entry defines the term as it applies within GULA, cites the implementing ORM
model(s), and maps to FHIR R4 resources where applicable.

---

## Table of Contents

1. [Healthcare Terminology](#1-healthcare-terminology)
2. [Laboratory Terminology](#2-laboratory-terminology)
3. [Administrative Terminology](#3-administrative-terminology)
4. [Clinical Terminology](#4-clinical-terminology)
5. [FHIR Terminology](#5-fhir-terminology)
6. [Platform Terminology](#6-platform-terminology)
7. [National Health Terminology](#7-national-health-terminology)
8. [Financial Terminology](#8-financial-terminology)
9. [Model Index](#9-model-index)

---

## 1. Healthcare Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Patient** | Healthcare | A person receiving healthcare services. Each patient belongs to exactly one lab (tenant isolation). Patients may have a guardian (for minors) and a family ID hash linking family members. | `Patient`, `CanonicalPatient` | Patient | `backend/app/models/patient.py`, `backend/app/models/canonical_patient.py` |
| **Canonical Patient** | Healthcare | The master, deduplicated patient record in the MPI (Master Patient Index). Links one or more per-lab `Patient` records and/or `Citizen` records into a single identity via probabilistic matching (Fellegi-Sunter). | `CanonicalPatient`, `PatientLink`, `CitizenLink` | Patient (master) | `backend/app/models/canonical_patient.py` |
| **Citizen** | Healthcare | A person registered in the National Citizen Registry (owned by the NHOP platform). The canonical patient may link to a citizen record, bridging the per-lab LIMS view with the national registry. | `CitizenLink` (references `citizens` table) | Patient (national) | `docs/constitution/06_DOMAIN_MODEL.md`, `backend/app/models/canonical_patient.py` |
| **Guardian** | Healthcare | A parent or legal guardian of a minor patient. Linked via `guardian_id` on the `patients` table. A patient may have multiple dependents. | `Patient` (self-referential) | RelatedPerson | `backend/app/models/patient.py:33-35` |
| **Encounter** | Healthcare | A clinical interaction between a patient and a healthcare provider. In GULA, tracked via the `visits` table (SNDHS Phase 1) and lab orders. | `LabOrder`, `visits` table | Encounter | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Diagnosis** | Healthcare | A clinical determination of a patient's condition. May be associated with encounters, orders, and results. | (Clinical domain models) | Condition | `docs/constitution/06_DOMAIN_MODEL.md` |
| **Condition** | Healthcare | A diagnosed problem, illness, or abnormality. Part of the patient's problem list. | (Clinical domain models) | Condition | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Allergy** | Healthcare | An adverse reaction to a substance. Checked during order entry to prevent unsafe test or medication administration. | (Clinical domain models) | AllergyIntolerance | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Consent** | Healthcare | A record of patient authorisation for data access, sharing, or research participation. Has a scope, grantee, expiry, and one-way status lifecycle (active → revoked/expired). | `Consent` | Consent | `backend/app/models/consent.py` |
| **Problem List** | Healthcare | A longitudinal list of a patient's active and resolved medical problems. | (Clinical domain models) | List (problem-list) | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Clinical Note** | Healthcare | A structured or narrative record of a clinical encounter, following templates that capture relevant data elements without restricting narrative expression. | (Clinical domain models) | ClinicalImpression, DocumentReference | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |

---

## 2. Laboratory Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Lab Order** | Laboratory | A request for laboratory tests for a patient. Follows a state machine: pending → completed → validated (terminal), or pending/completed → cancelled (terminal). Uses optimistic locking (`version` column). | `LabOrder`, `OrderStatus` enum | ServiceRequest | `backend/app/models/lab_order.py`, `backend/app/domain/order_state.py` |
| **Order Status** | Laboratory | Canonical status values: `pending` (awaiting results), `completed` (results entered), `validated` (clinician-approved, immutable), `cancelled` (voided). Terminal states: validated, cancelled. | `OrderStatus` (StrEnum) | ServiceRequest.status | `backend/app/domain/order_state.py:21-30` |
| **Lab Result** | Laboratory | The outcome of a single lab test for a given order. Contains numeric value (or text), unit, reference range, flag (H/L/normal/critical), and a secure token for patient access. Uses optimistic locking. | `LabResult` | Observation | `backend/app/models/lab_result.py` |
| **Test Type** | Laboratory | The definition of a laboratory test: test code, name (English + Arabic), category, unit, reference ranges, and interpretive text for low/normal/high results in both languages. | `TestType` | ObservationDefinition | `backend/app/models/test_type.py` |
| **Sample** | Laboratory | A biological specimen collected from a patient for testing. Tracked by barcode (`SMP-` prefix), sample type (blood, urine, stool, swab, serum, plasma), collection details, status (collected/received/processing/analyzed/rejected), rejection reason, and storage location. | `Sample` | Specimen | `backend/app/models/sample.py` |
| **Test Result** | Laboratory | A test outcome linked to a canonical citizen record (via MPI). Uses LOINC test codes, supports both numeric and text results, reference ranges, critical/abnormal flags, and status lifecycle (pending → completed → verified → rejected). | `TestResult` | Observation | `backend/app/models/test_result.py` |
| **Reference Range** | Laboratory | The normal range for a test result (low/high). Age-specific, sex-specific, and pregnancy-specific where applicable. Ranges are versioned and traceable to source publications. | `TestType` (normal_range_low/high), `TestResult` (reference_min/max) | Observation.referenceRange | `backend/app/models/test_type.py`, `docs/constitution/10_LABORATORY_CONSTITUTION.md` |
| **Critical Value** | Laboratory | A test result that falls outside a life-threatening threshold. Triggers mandatory escalation with acknowledgment tracking. Unacknowledged criticals escalate at 15 and 30 minutes. | `LabResult` (flag="critical"), `TestResult` (is_critical=True) | Observation.interpretation | `docs/constitution/10_LABORATORY_CONSTITUTION.md` |
| **Flag** | Laboratory | A categorical indicator: H (high), L (low), normal, or critical. Set by the clinical engine based on reference range comparison. | `LabResult.flag` | Observation.interpretation | `backend/app/models/lab_result.py:39-40` |
| **Panel** | Laboratory | A group of commonly ordered tests (e.g., pre-operative panel, diabetic panel). Supports component tests, calculated results, and reflex testing rules. | (Panel management in lab domain) | DiagnosticReport | `docs/constitution/10_LABORATORY_CONSTITUTION.md` |
| **Delta Check** | Laboratory | A comparison of current results against previous results for the same patient and test. Significant changes are flagged for clinical review. | (Service layer) | Observation (with prior) | `docs/constitution/10_LABORATORY_CONSTITUTION.md` |
| **Quality Control (QC)** | Laboratory | Internal quality control tracking lab instrument performance. Records expected vs. measured values, standard deviation, level (low/normal/high), and Westgard rule violations. QC failures lock result reporting for affected tests. | `QualityControl` | (No direct FHIR mapping) | `backend/app/models/quality_control.py` |
| **Westgard Rules** | Laboratory | Statistical rules (1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10-x) used to evaluate QC data and determine whether an analytical run is in control. | `QualityControl.violation` | (No direct FHIR mapping) | `backend/app/models/quality_control.py:31` |
| **Proficiency Testing (EQA)** | Laboratory | External quality assessment: participation tracked per test with performance scoring and corrective action documentation. | (Service layer) | (No direct FHIR mapping) | `docs/constitution/10_LABORATORY_CONSTITUTION.md` |
| **Instrument** | Laboratory | A laboratory analyser device. Connected via the device bridge (ASTM/HL7). Supports bidirectional communication for order sending and result receiving. | `EdgeDevice` (for edge AI), device bridge config | Device | `docs/constitution/10_LABORATORY_CONSTITUTION.md`, `services/device_bridge/` |
| **Device Bridge** | Laboratory | The LabLink-Core service that reads from physical lab instruments (Sysmex, Roche, Mindray, generic), normalises results, and forwards them to the GULA backend via REST API. | (Integration service) | (No direct FHIR mapping) | `services/device_bridge/app/integration/gula_client.py` |
| **Specimen Integrity** | Laboratory | Chain-of-custody maintained from collection through disposal. Every handling event is recorded with responsible party, timestamp, and condition. Barcode/QR labeling survives freezing/thawing/solvents. | `Sample` | Specimen.collection, Specimen.processing | `docs/constitution/10_LABORATORY_CONSTITUTION.md` |

---

## 3. Administrative Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Lab** | Administrative | A laboratory facility that is the primary tenant-scoping entity. All patient data queries must filter by `lab_id`. Has a type (private/government/hospital/clinic), license number, director, and subscription. | `Lab` | Organization (with type=prov) | `backend/app/models/lab.py` |
| **Tenant** | Administrative | A multi-level organisational entity (Ministry → Governorate → Directorate → Facility → Department). Provides tenant isolation with hierarchical structure. Each tenant has feature flags and settings. | `Tenant` | Organization (hierarchical) | `backend/app/models/tenant.py` |
| **Organization** | Administrative | A healthcare organisation (e.g., Health Directorate). Belongs to a tenant, has a type, parent org hierarchy, and may contain multiple facilities. | `Organization` | Organization | `backend/app/models/organization.py` |
| **Facility** | Administrative | A physical healthcare facility (hospital, PHC, lab, clinic). Belongs to an organization and has a type. | `Facility` | Location | `backend/app/models/organization.py:32-47` |
| **Lab User** | Administrative | A user account within a specific lab. Has a role (staff, doctor, admin, etc.), lab_id scoping, province_id for provincial admins, and a password reset mechanism. | `LabUser` | Practitioner | `backend/app/models/lab_user.py` |
| **User** | Administrative | A platform user (may span multiple tenants). Has roles, permissions, MFA settings, organisation/facility/dept assignments, and user_type from 45+ healthcare role types. | `User` | Practitioner, RelatedPerson | `backend/app/models/user.py`, `backend/app/models/authorization.py` |
| **Role** | Administrative | A named set of permissions. Roles have hierarchy (parent_role_id), levels (department/governorate/national), MFA requirements, delegation support, and temporal assignments. | `Role`, `RoleAssignment`, `RoleGroup`, `RoleGroupMember` | (No direct FHIR mapping) | `backend/app/models/authorization.py:67-130` |
| **Permission** | Administrative | A fine-grained access right defined by domain, resource, and action. Has risk level, sensitivity, MFA requirement, and audit flag. | `Permission`, `RolePermission` | (No direct FHIR mapping) | `backend/app/models/authorization.py:48-65` |
| **Role Assignment** | Administrative | A link between a user and a role, scoped to an organization/facility/department with optional expiration, delegation tracking, and primary flag. | `RoleAssignment` | (No direct FHIR mapping) | `backend/app/models/authorization.py:95-111` |
| **Policy (ABAC)** | Administrative | An Attribute-Based Access Control policy with conditions, target, effect (allow/deny), obligations, priority, validity window, and signature. | `Policy` | (No direct FHIR mapping) | `backend/app/models/authorization.py:132-155` |
| **Break-Glass Session** | Administrative | An emergency access session that temporarily grants elevated permissions. Requires justification, emergency category, patient ID, and automatic expiry. All actions are audited. | `BreakGlassSession` | (No direct FHIR mapping) | `backend/app/models/authorization.py:192-206` |
| **Delegation** | Administrative | A temporary transfer of a role from a delegator to a delegate with defined scope, reason, and automatic expiry. | `Delegation` | (No direct FHIR mapping) | `backend/app/models/authorization.py:174-189` |
| **Subscription** | Administrative | The billing tier for a lab. Three orthogonal dimensions: Tier (starter/growth/enterprise), Deployment Mode (single/multi_branch/government), Security Level (standard/high_security/air_gapped). Enforces limits on patients, staff, orders, AI calls. | `LabSubscription` | (No direct FHIR mapping) | `backend/app/models/subscription.py` |
| **Upgrade Request** | Administrative | A citizen-initiated request to upgrade a lab's subscription tier. Weighted scoring drives upgrade recommendations to platform admins. | `UpgradeRequest`, `UpgradeDemandScore` | (No direct FHIR mapping) | `backend/app/models/subscription.py:78-137` |
| **MFA Device** | Administrative | A multi-factor authentication device (TOTP, WebAuthn, backup codes). Each user can have multiple devices; one may be primary. | `MFADevice`, `MFASession` | (No direct FHIR mapping) | `backend/app/models/mfa_device.py` |
| **OAuth2 Client** | Administrative | A registered OAuth2/OIDC client application with client credentials, redirect URIs, grant types, and scopes. | `OAuth2Client`, `OAuth2Token` | (No direct FHIR mapping) | `backend/app/models/oauth2_client.py` |
| **Service Account** | Administrative | A machine-to-machine account with API key authentication, roles, and scopes. Used for automated integrations. | `ServiceAccount` | (No direct FHIR mapping) | `backend/app/models/service_account.py` |

---

## 4. Clinical Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Medication** | Clinical | A pharmaceutical product prescribed or administered to a patient. Checked against formularies and drug interactions during order entry. | (Pharmacy domain models) | Medication, MedicationRequest | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Immunization** | Clinical | A vaccination administered to a patient. Tracked as part of the patient's medical history and public health surveillance. | (Clinical domain models) | Immunization | `docs/constitution/06_DOMAIN_MODEL.md` |
| **Care Plan** | Clinical | A structured plan of care for a patient, encompassing goals, interventions, and expected outcomes. Used in nursing and clinical workflows. | (Nursing domain models) | CarePlan | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Clinical Decision Support (CDS)** | Clinical | Evidence-based rules and algorithms that assist clinicians in decision-making. Must be attributed to sources and reviewable. AI-assisted CDS follows the AI Constitution. | (Service layer) | (No direct FHIR mapping) | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Order Set** | Clinical | A pre-defined group of tests or procedures commonly ordered together for a specific clinical context (pre-operative, diabetic panel, infectious workup). | (Service layer) | (No direct FHIR mapping) | `docs/constitution/10_LABORATORY_CONSTITUTION.md` |
| **Clinical Note** | Clinical | A structured record of a clinical encounter or observation. Follows templates that capture relevant data elements while allowing narrative expression. | (Clinical domain models) | ClinicalImpression, DocumentReference | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |
| **Handover** | Clinical | A structured transfer of patient care responsibility between clinicians. Includes structured summaries, task ownership, and accountability tracking. | (Clinical domain models) | (No direct FHIR mapping) | `docs/constitution/09_CLINICAL_CONSTITUTION.md` |

---

## 5. FHIR Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Resource** | FHIR | An FHIR R4 resource type (Patient, Observation, ServiceRequest, etc.). GULA ORM models correspond to FHIR resources with platform-specific extensions. | All ORM models | All FHIR resources | `docs/constitution/06_DOMAIN_MODEL.md` |
| **Profile** | FHIR | A FHIR Profile is a constraint or extension of a base FHIR resource for a specific use case. GULA's domain model defines platform-specific profiles. | (Integration models) | StructureDefinition | `backend/app/integration/` |
| **Extension** | FHIR | An FHIR Extension adds a field to a resource that is not part of the base specification. Used for GULA-specific data (e.g., lab_id, Arabic names). | Model-specific fields | Extension | `backend/app/integration/` |
| **Bundle** | FHIR | A container for a collection of FHIR resources. Used for batch operations, transaction bundles, and search result sets. | (Integration layer) | Bundle | `backend/app/integration/` |
| **Operation** | FHIR | A RESTful operation on an FHIR endpoint (read, search, create, update, delete, or custom `$operation`). | Routes | (RESTful operations) | `backend/app/routes/` |
| **Search Parameter** | FHIR | A named parameter used to search FHIR resources (e.g., `patient`, `date`, `code`). GULA maps search parameters to SQLAlchemy query filters. | (Service layer) | SearchParameter | `backend/app/services/` |
| **HL7 v2** | FHIR | Health Level 7 version 2 messaging protocol for lab instrument integration (ASTM E1381/1384). Device bridge processes HL7 ORU^R01 messages for result reporting. | (Device bridge service) | (Use FHIR for equivalency) | `services/device_bridge/` |
| **IHE Profile** | FHIR | Integrating the Healthcare Enterprise profiles for interoperability. GULA's integration platform implements relevant IHE profiles for lab and clinical data exchange. | (Integration layer) | (Cross-reference IHE) | `backend/app/integration/` |
| **LOINC** | FHIR | Logical Observation Identifiers Names and Codes — the standard coding system for lab test identification used in GULA's `TestResult.test_code` field. | `TestResult.test_code` | Observation.code | `backend/app/models/test_result.py:71` |

---

## 6. Platform Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Outbox** | Platform | The transactional outbox pattern: events are written to the `outbox_events` table inside the same DB transaction as the triggering business operation. A background worker delivers them (notifications, webhooks, sync signals). Guarantees at-least-once delivery. Status lifecycle: pending → processing → done / failed. | `OutboxEvent` | (No direct FHIR mapping) | `backend/app/models/outbox.py` |
| **Event Bus** | Platform | The delivery mechanism for outbox events. Background worker reads pending events and dispatches them to subscribers (notifications, webhooks, sync signals). | `OutboxEvent` | (No direct FHIR mapping) | `backend/app/models/outbox.py` |
| **Circuit Breaker** | Platform | A self-healing pattern that isolates failing DB or Redis connections. When the circuit is open, the platform flips to degraded mode and rejects writes. Part of the 3-layer self-healing system. | `core/self_healing.py` | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/core/self_healing.py` |
| **Degraded Mode** | Platform | A platform state where write operations are rejected because the DB circuit is open. `DegradedModeMiddleware` enforces this. Health checks and whitelisted paths are exempt. | `DegradedModeMiddleware` | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/core/self_healing.py` |
| **system_ready** | Platform | A boolean flag that blocks all non-health traffic until the platform has completed startup validation. Set by `StartupGuard` after: config validated, DB reachable, migrations checked, critical data seeded. | `StartupGuard` | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/core/startup_guard.py` |
| **Kernel** | Platform | The runtime environment that attaches context to every request (`KernelMiddleware`). Provides plugin system, event bus, background task scheduling, config management, and feature flag resolution. | `KernelMiddleware` | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/kernel/` |
| **Feature Flag** | Platform | Two parallel systems: (1) Per-tenant — enables/disables features per lab via `feature_flags` DB table with optional expiry. (2) Deployment-wide — environment variables controlling SNDHS, Financial Engine, ADS, background tasks, and runtime mode. | `FeatureFlag`, env vars (`SNDHS_ENABLE_*`, `ENABLE_FINANCIAL_ENGINE`, etc.) | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/core/feature_flags.py`, `backend/app/core/sndhs_flags.py`, `backend/app/models/subscription.py:140-163` |
| **Audit Log** | Platform | Immutable, SHA-256 hash-chained audit trail for all mutations. Each entry hashes the previous chain hash with the current record data. Tampering breaks the chain. Covers all clinical and administrative actions. | `AuditLog` | AuditEvent | `backend/app/models/audit_log.py` |
| **Authorization Audit** | Platform | A separate audit trail for authorization decisions (RBAC/ABAC). Records decisions, policies applied, risk scores, and emergency/break-glass access. | `AuthorizationAudit` | AuditEvent | `backend/app/models/authorization.py:209-227` |
| **Optimistic Lock** | Platform | A `version` column incremented on every UPDATE. If the caller's version doesn't match the DB, the update affects 0 rows and the caller receives HTTP 409 Conflict. Applied to `LabOrder`, `LabResult`, and `CanonicalPatient`. | `LabOrder.version`, `LabResult.version`, `CanonicalPatient.version` | (No direct FHIR mapping) | `backend/app/models/lab_order.py:46`, `backend/app/models/lab_result.py:53` |
| **Self-Healing** | Platform | Three-layer resilience system: (1) Circuit Breaker — isolates failing connections, (2) Auto-Repair Engine — GC, pool recycle, reconnects, (3) Adaptive Concurrency — halves in-flight limit on slow DB readings. | `core/self_healing.py`, `core/auto_repair.py` | (No direct FHIR mapping) | `CLAUDE.md` |
| **Adaptive Concurrency** | Platform | A background loop that dynamically adjusts `MAX_CONCURRENT_REQUESTS`: halves on 2 slow DB readings (>300ms), restores after 3 fast ones (<150ms). Clinical writes are exempt from shedding. | `main.py::_adaptive_concurrency_loop` | (No direct FHIR mapping) | `CLAUDE.md` |
| **Health Endpoints** | Platform | Five endpoints: `/health` and `/health/live` (liveness), `/health/ready` (readiness, used by Docker), `/health/status` (diagnostic), `/health/deep` (grade + latencies + memory). All bypass degraded mode and concurrency middleware. | `_ALWAYS_ALLOWED_PATHS` | (No direct FHIR mapping) | `CLAUDE.md` |
| **Edge Device** | Platform | A user device registered as a trusted, sandboxed node in the Managed Distributed Edge AI Platform. Has trust score, attestation, role mode (personal/clinic/enterprise), and kill switch. | `EdgeDevice` | (No direct FHIR mapping) | `backend/app/models/edge.py:43-81` |
| **Edge Task** | Platform | A computational task dispatched to an edge device for local AI inference. Has priority, privacy level, payload signature, trust requirements, timeout, and status lifecycle (pending → dispatched → running → completed/failed/cancelled/expired). | `EdgeTask` | (No direct FHIR mapping) | `backend/app/models/edge.py:84-117` |

---

## 7. National Health Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **SNDHS** | National Health | النظام الصحي الوطني — The Iraqi National Health Data System. GULA implements SNDHS-lite integration (Phase 1) adding national ID, health ID, visit tracking, and enhanced audit. | (SNDHS-specific columns on `Patient`, `LabOrder`, `AuditLog`) | (National profiles) | `CLAUDE.md`, `docs/sndhs/` |
| **National ID** | National Health | The Iraqi national identification number. Stored encrypted at rest on the `patients` table (`national_id_hash` for indexed lookup). Dual-read rule: must handle NULL for pre-backfill rows. | `Patient.national_id_hash` | Patient.identifier (national-id type) | `CLAUDE.md`, `backend/app/models/patient.py:30` |
| **Health ID** | National Health | An SNDHS-assigned health identifier. Indexed on both `Patient` and `CanonicalPatient`. Dual-read rule applies. | `Patient.health_id`, `CanonicalPatient.health_id` | Patient.identifier (health-id type) | `CLAUDE.md`, `backend/app/models/patient.py:28` |
| **Visit** | National Health | A clinical episode tracking record. When `SNDHS_ENABLE_VISITS` is enabled, lab orders can be linked to a `visit_id` for episode-level clinical tracking. Requires data backfill before enabling. | `visits` table, `LabOrder.visit_id` | Encounter | `CLAUDE.md`, `docs/sndhs/phase1/RUNBOOK.md` |
| **Citizen Registry** | National Health | The national repository of all Iraqi citizens, owned by the NHOP (National Health Oversight Platform). GULA accesses it via the NHOP API for identity verification and MPI matching. | `CitizenLink`, `CanonicalPatient` | Patient (national registry) | `CLAUDE.md`, `nhop-platform/` |
| **MPI (Master Patient Index)** | National Health | The probabilistic patient matching system that deduplicates patient records across labs and links them to the national citizen registry. Uses Fellegi-Sunter probabilistic matching algorithm. | `CanonicalPatient`, `PatientLink`, `CitizenLink` | Patient.link | `CLAUDE.md`, `backend/app/services/mpi/` |
| **NHOP** | National Health | National Health Oversight Platform — a separate FastAPI application (port 8100) that owns the national citizen registry and provides the authoritative identity source. | (NHOP models) | (National FHIR profiles) | `CLAUDE.md`, `nhop-platform/` |
| **Dual-Read Rule** | National Health | Any code that reads `national_id` or `sndhs_health_id` must gracefully handle `None` — existing rows from before SNDHS backfill will have null values. | `Patient.national_id_hash`, `Patient.health_id` | (Safety invariant) | `CLAUDE.md` |
| **SNDHS-lite Flags** | National Health | Deployment-wide environment variables controlling national health features: `SNDHS_ENABLE_VISITS` (default false), `SNDHS_ENABLE_NATIONAL_ID` (default false). Must not be enabled without reading the runbook. | `core/sndhs_flags.py` | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/core/sndhs_flags.py` |
| **Governorate** | National Health | An Iraqi administrative region (محافظة). There are 18 governorates in the GULA data model. Users and organizations are scoped by governorate_id for provincial administration. | `User.governorate_id`, `Organization.governorate_id` | (No direct FHIR mapping) | `backend/app/models/user.py:25`, `backend/app/models/organization.py:21` |
| **Family ID** | National Health | A civil registry family number, stored as HMAC-SHA256 hash (prefix `fam:`) on the patient record. Links all family members for family-based health tracking. | `Patient.family_id_hash` | Patient.link (family relationship) | `backend/app/models/patient.py:32` |

---

## 8. Financial Terminology

| Term | Category | Definition | Related Models | FHIR Mapping | References |
|------|----------|------------|----------------|--------------|------------|
| **Claim** | Financial | An insurance billing claim for lab services. Has status lifecycle: draft → validated → submitted → accepted/rejected → paid. Links to patient, lab, and order. | `Claim`, `ClaimItem` | Claim | `backend/app/models/claim.py` |
| **Claim Item** | Financial | An individual line item on a claim, representing one test/service with quantity, unit price, and total amount. | `ClaimItem` | Claim.item | `backend/app/models/claim.py:61-75` |
| **Financial Engine** | Financial | The Financial Engine module (Phase A = schema-only). Tables: `fin_campaigns`, `fin_conversions`, `fin_fraud_flags`. Feature-gated by `ENABLE_FINANCIAL_ENGINE` (default off). No business logic until Phase B+. | `fin_*` tables (migration only) | (No direct FHIR mapping) | `CLAUDE.md`, `backend/app/financial/` |
| **Campaign** | Financial | An advertising or promotional campaign. Feature-gated by `ENABLE_ADS` (default off). | `fin_campaigns` table | (No direct FHIR mapping) | `CLAUDE.md` |
| **Conversion** | Financial | A tracked advertising conversion event. | `fin_conversions` table | (No direct FHIR mapping) | `CLAUDE.md` |

---

## Model Index

Complete list of SQLAlchemy ORM models and their filenames:

| Model Class | Table | File |
|-------------|-------|------|
| `Lab` | `labs` | `backend/app/models/lab.py` |
| `LabUser` | `lab_users` | `backend/app/models/lab_user.py` |
| `Patient` | `patients` | `backend/app/models/patient.py` |
| `CanonicalPatient` | `canonical_patients` | `backend/app/models/canonical_patient.py` |
| `PatientLink` | `patient_links` | `backend/app/models/canonical_patient.py` |
| `CitizenLink` | `citizen_links` | `backend/app/models/canonical_patient.py` |
| `LabOrder` | `lab_orders` | `backend/app/models/lab_order.py` |
| `LabResult` | `lab_results` | `backend/app/models/lab_result.py` |
| `Sample` | `samples` | `backend/app/models/sample.py` |
| `TestType` | `test_types` | `backend/app/models/test_type.py` |
| `TestResult` | `test_results` | `backend/app/models/test_result.py` |
| `QualityControl` | `quality_controls` | `backend/app/models/quality_control.py` |
| `User` | `users` | `backend/app/models/user.py` |
| `Tenant` | `tenants` | `backend/app/models/tenant.py` |
| `Organization` | `organizations` | `backend/app/models/organization.py` |
| `Facility` | `facilities` | `backend/app/models/organization.py` |
| `Permission` | `permissions` | `backend/app/models/authorization.py` |
| `Role` | `roles` | `backend/app/models/authorization.py` |
| `RolePermission` | `role_permissions` | `backend/app/models/authorization.py` |
| `RoleAssignment` | `role_assignments` | `backend/app/models/authorization.py` |
| `RoleGroup` | `role_groups` | `backend/app/models/authorization.py` |
| `RoleGroupMember` | `role_group_members` | `backend/app/models/authorization.py` |
| `Policy` | `abac_policies` | `backend/app/models/authorization.py` |
| `FieldSecurity` | `field_security` | `backend/app/models/authorization.py` |
| `Delegation` | `delegations` | `backend/app/models/authorization.py` |
| `BreakGlassSession` | `break_glass_sessions` | `backend/app/models/authorization.py` |
| `AuthorizationAudit` | `authorization_audit` | `backend/app/models/authorization.py` |
| `AuditLog` | `audit_logs` | `backend/app/models/audit_log.py` |
| `OutboxEvent` | `outbox_events` | `backend/app/models/outbox.py` |
| `Consent` | `consents` | `backend/app/models/consent.py` |
| `Claim` | `claims` | `backend/app/models/claim.py` |
| `ClaimItem` | `claim_items` | `backend/app/models/claim.py` |
| `LabSubscription` | `lab_subscriptions` | `backend/app/models/subscription.py` |
| `UpgradeRequest` | `upgrade_requests` | `backend/app/models/subscription.py` |
| `UpgradeDemandScore` | `upgrade_demand_scores` | `backend/app/models/subscription.py` |
| `FeatureFlag` | `feature_flags` | `backend/app/models/subscription.py` |
| `MFADevice` | `mfa_devices` | `backend/app/models/mfa_device.py` |
| `MFASession` | `mfa_sessions` | `backend/app/models/mfa_device.py` |
| `OAuth2Client` | `oauth2_clients` | `backend/app/models/oauth2_client.py` |
| `OAuth2Token` | `oauth2_tokens` | `backend/app/models/oauth2_token.py` |
| `ServiceAccount` | `service_accounts` | `backend/app/models/service_account.py` |
| `EdgeDevice` | `edge_devices` | `backend/app/models/edge.py` |
| `EdgeTask` | `edge_tasks` | `backend/app/models/edge.py` |
| `EdgeTelemetry` | `edge_telemetry` | `backend/app/models/edge.py` |
| `EdgeModel` | `edge_models` | `backend/app/models/edge.py` |
| `EdgeModelAssignment` | `edge_model_assignments` | `backend/app/models/edge.py` |
| `EdgePolicy` | `edge_policies` | `backend/app/models/edge.py` |
| `EdgeEvent` | `edge_events` | `backend/app/models/edge.py` |
| `AIInteraction` | `ai_interactions` | `backend/app/models/ai_interaction.py` |
| `AIRetrievalRef` | `ai_retrieval_refs` | `backend/app/models/ai_interaction.py` |
| `AIFeedback` | `ai_feedback` | `backend/app/models/ai_interaction.py` |
| `AIUnresolvedQuestion` | `ai_unresolved_questions` | `backend/app/models/ai_interaction.py` |
| `MedicalTerminologyNormalized` | `medical_terminology_normalized` | `backend/app/models/ai_interaction.py` |
| `AIEmbedding` | `ai_embeddings` | `backend/app/models/ai.py` |
| `AIConversation` | `ai_conversations` | `backend/app/models/ai.py` |
| `AIConversationMessage` | `ai_conversation_messages` | `backend/app/models/ai.py` |
| `AIAgentExecution` | `ai_agent_executions` | `backend/app/models/ai.py` |
| `AIKnowledgeNode` | `ai_knowledge_nodes` | `backend/app/models/ai.py` |
| `AIKnowledgeEdge` | `ai_knowledge_edges` | `backend/app/models/ai.py` |
| `AIModelRegistry` | `ai_model_registry` | `backend/app/models/ai.py` |
| `AIEvaluation` | `ai_evaluations` | `backend/app/models/ai.py` |
