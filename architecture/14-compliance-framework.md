# GULA Platform — Compliance Framework

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [FHIR R4/R5](#1-fhir-r4r5)
2. [HL7 v2.x](#2-hl7-v2x)
3. [IHE Profiles](#3-ihe-profiles)
4. [DICOM](#4-dicom)
5. [SNOMED CT](#5-snomed-ct)
6. [LOINC](#6-loinc)
7. [ICD-10/ICD-11](#7-icd-10icd-11)
8. [UCUM](#8-ucum)
9. [ISO 27001](#9-iso-27001)
10. [ISO 27701](#10-iso-27701)
11. [OWASP ASVS](#11-owasp-asvs)
12. [OWASP API Security](#12-owasp-api-security)
13. [NIST CSF](#13-nist-csf)
14. [NIST 800-53](#14-nist-800-53)
15. [CIS Controls](#15-cis-controls)
16. [OpenAPI 3.1](#16-openapi-31)
17. [AsyncAPI 2.6](#17-asyncapi-26)

---

## 1. FHIR R4/R5

### 1.1 Relevance to GULA

GULA's National Layer exposes citizen health records via FHIR-compatible APIs. FHIR R4 is the primary target; R5 compatibility is maintained for future alignment with international health information exchanges.

### 1.2 Implementation Status

| FHIR Resource | Status | Location |
|---------------|--------|----------|
| Patient | CONFORMANT | `backend/app/national/fhir/patient.py` |
| Practitioner | CONFORMANT | `backend/app/national/fhir/practitioner.py` |
| Organization | CONFORMANT | `backend/app/national/fhir/organization.py` |
| Observation | CONFORMANT | `backend/app/national/fhir/observation.py` |
| Encounter | CONFORMANT | `backend/app/national/fhir/encounter.py` |
| Bundle | CONFORMANT | `backend/app/national/fhir/bundle.py` |
| Search | CONFORMANT | `backend/app/national/fhir/search.py` |
| Terminology | INTEGRATED | `backend/app/national/fhir/terminology.py` |
| Validation | CONFIGURED | `backend/app/national/fhir/validation.py` |

### 1.3 Compliance Checks

- FHIR Resource structure validation against R4/R5 schemas
- Search parameter compliance with FHIR Search API spec
- Bundle format compliant with FHIR Bundle resource spec
- Proper use of canonical URLs and identifiers

### 1.4 Evidence Files

- `backend/app/national/fhir/` — FHIR mapping implementations
- `backend/app/lims/fhir_mappers.py` — LIMS-to-FHIR mapping
- `backend/app/interoperability/` — FHIR/HL7 interop

### 1.5 Gap Analysis

| Gap | Priority | Impact |
|-----|----------|--------|
| US Core profile not fully supported | Medium | US interoperability |
| IPA profile documentation incomplete | Low | International patient access |
| FHIR subscription not implemented | Low | Event-driven FHIR |

---

## 2. HL7 v2.x

### 2.1 Relevance to GULA

Lab instruments communicate using HL7 v2.x (primarily v2.5.1) and ASTM protocols. The Device Bridge (`services/device_bridge/`) parses these messages and normalizes results.

### 2.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| HL7 message parsing | PRODUCTION | `services/device_bridge/` |
| ASTM E1381-02 parsing | PRODUCTION | `shared/device/astm.py` |
| Device adapters | PRODUCTION | `shared/device/adapters.py` |
| Result normalization | PRODUCTION | `services/device_bridge/` |

### 2.3 Supported Message Types

| Message | Type | Purpose |
|---------|------|---------|
| ORU^R01 | Observation Result | Lab results |
| ORM^O01 | Order Entry | Lab orders |
| ADT^A01 | Admit Patient | Patient registration |
| ADT^A08 | Update Patient | Patient update |
| QBP^Q11 | Query by Parameter | Lab order query |

### 2.4 Code References

- `services/device_bridge/` — HL7 device bridge
- `shared/device/astm.py` — ASTM protocol
- `shared/device/adapters.py` — Device adapters

---

## 3. IHE Profiles

### 3.1 Relevance to GULA

IHE (Integrating the Healthcare Enterprise) profiles define integration patterns for healthcare systems. GULA implements applicable profiles for cross-enterprise document sharing and patient identity management.

### 3.2 Implementation Status

| IHE Profile | Status | Location |
|-------------|--------|----------|
| XDS (Cross-Enterprise Document Sharing) | PLANNED | Future |
| PIX (Patient Identifier Cross-Referencing) | CONFORMANT | `backend/app/services/mpi/` |
| PDQ (Patient Demographics Query) | CONFORMANT | `backend/app/services/mpi/api.py` |
| ATNA (Audit Trail and Node Authentication) | CONFORMANT | `backend/app/audit/`, `backend/app/models/audit_log.py` |
| CT (Consistent Time) | CONFORMANT | `backend/app/_compat.py` (UTC) |

### 3.3 Evidence Files

- `backend/app/services/mpi/` — PIX/PDQ implementation
- `backend/app/audit/audit_log.py` — ATNA audit trail
- `backend/app/models/audit_log.py` — Hash-chained audit

---

## 4. DICOM

### 4.1 Relevance to GULA

DICOM (Digital Imaging and Communications in Medicine) is relevant for future radiology and medical imaging modules. Currently not implemented in the clinical laboratory scope.

### 4.2 Implementation Status

| Component | Status |
|-----------|--------|
| DICOM structured reports | NOT IMPLEMENTED |
| DICOM image storage | NOT IMPLEMENTED |
| DICOM modalities | NOT IMPLEMENTED |

### 4.3 Gap Analysis

| Gap | Priority | Impact |
|-----|----------|--------|
| No DICOM support | Low | PACS integration needed for radiology module |
| No imaging storage | Low | Future radiology/imaging features |

---

## 5. SNOMED CT

### 5.1 Relevance to GULA

SNOMED CT provides clinical terminology for symptoms, findings, procedures, and body structures. Used in clinical decision support and FHIR observations.

### 5.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Terminology server | INTEGRATED | `backend/app/national/fhir/terminology.py` |
| Expression constraints | PARTIAL | `backend/app/clinical/terminology/` |
| Clinical findings | PARTIAL | `backend/app/clinical/knowledge/` |
| FHIR terminology | INTEGRATED | `backend/app/national/fhir/terminology.py` |

### 5.3 Evidence Files

- `backend/app/national/fhir/terminology.py` — Terminology services
- `backend/app/clinical/terminology/` — Clinical terminology
- `backend/app/clinical/knowledge/` — Clinical knowledge base

---

## 6. LOINC

### 6.1 Relevance to GULA

LOINC (Logical Observation Identifiers Names and Codes) identifies laboratory observations. Every lab test type result should map to a LOINC code for interoperability.

### 6.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| LOINC mapping service | PARTIAL | In clinical services |
| Test type → LOINC mapping | MANUAL | Lab configuration |
| FHIR Observation LOINC | CONFORMANT | `backend/app/national/fhir/observation.py` |

### 6.3 Evidence Files

- `backend/app/national/fhir/observation.py` — LOINC-coded observations
- `backend/app/clinical/terminology/` — Terminology services

---

## 7. ICD-10/ICD-11

### 7.1 Relevance to GULA

ICD (International Classification of Diseases) codes are used for diagnosis coding, morbidity/mortality statistics, and insurance claims.

### 7.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| ICD-10 diagnosis codes | PARTIAL | `backend/app/clinical/terminology/` |
| ICD-11 compatibility | PLANNED | Future |
| Claims coding | PARTIAL | `backend/app/financial/` |

### 7.3 Evidence Files

- `backend/app/clinical/terminology/` — Diagnosis coding
- `backend/app/financial/` — Claims and financial

---

## 8. UCUM

### 8.1 Relevance to GULA

UCUM (Unified Code for Units of Measure) standardizes units used in laboratory results. All lab results must express units using UCUM codes.

### 8.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| UCUM unit validation | INTEGRATED | Lab result validation |
| UCUM unit conversion | PARTIAL | `backend/app/lims/` |
| FHIR Quantity UCUM | CONFORMANT | `backend/app/national/fhir/observation.py` |

### 8.3 Evidence Files

- `backend/app/national/fhir/observation.py` — UCUM-coded quantities
- `backend/app/lims/fhir_mappers.py` — LIMS unit mapping

---

## 9. ISO 27001

### 9.1 Relevance to GULA

ISO 27001 provides the framework for an Information Security Management System (ISMS). Relevant for the platform's security posture and certifications for health data processing.

### 9.2 Implementation Status

| Control Area | Status | Evidence |
|--------------|--------|----------|
| Information security policy | CONFORMANT | `CLAUDE.md` security invariants |
| Asset management | CONFORMANT | Codebase organization |
| Access control | CONFORMANT | `backend/app/security/` |
| Cryptography | CONFORMANT | `shared/security/encryption.py` |
| Physical security | N/A | Cloud infrastructure (Render/DigitalOcean) |
| Operations security | CONFORMANT | `backend/app/core/` |
| Communications security | CONFORMANT | TLS, API gateway |
| Incident management | CONFORMANT | `backend/app/core/self_healing.py` |
| Business continuity | PARTIAL | Backup/restore procedures |
| Compliance | CONFORMANT | Audit logging |

### 9.3 Evidence Files

- `backend/app/security/` — Security controls
- `backend/app/audit/` — Audit logging
- `backend/app/core/self_healing.py` — Incident response

---

## 10. ISO 27701

### 10.1 Relevance to GULA

ISO 27701 extends ISO 27001 for privacy information management. Relevant for handling patient PII/PHI under Iraqi and international privacy regulations.

### 10.2 Implementation Status

| Control | Status | Location |
|---------|--------|----------|
| PII inventory | CONFORMANT | PII/PHI data catalog |
| Consent management | CONFORMANT | `backend/app/models/consent.py` |
| Privacy notices | PARTIAL | UI text |
| Data subject rights | PARTIAL | Future citizen portal |
| Breach notification | PARTIAL | Alert system |

### 10.3 Evidence Files

- `backend/app/models/consent.py` — Consent tracking
- `backend/app/security/encryption.py` — PII encryption
- `backend/app/national/security/` — Privacy controls

---

## 11. OWASP ASVS

### 11.1 Relevance to GULA

OWASP Application Security Verification Standard provides a framework for verifying application security. GULA targets Level 2 (standard) with Level 3 (advanced) for clinical data.

### 11.2 Implementation Status

| ASVS Category | Target Level | Status |
|---------------|--------------|--------|
| V1: Architecture | L2 | CONFORMANT |
| V2: Authentication | L3 | CONFORMANT |
| V3: Session Management | L3 | CONFORMANT |
| V4: Access Control | L3 | CONFORMANT |
| V5: Validation & Sanitization | L3 | CONFORMANT |
| V6: Encrypted Data | L3 | CONFORMANT |
| V7: Logging & Monitoring | L2 | CONFORMANT |
| V8: Data Protection | L3 | CONFORMANT |
| V9: Communications | L2 | CONFORMANT |
| V10: Malicious Code | L2 | CONFORMANT |
| V11: Business Logic | L2 | PARTIAL |
| V12: Files & Resources | L2 | CONFORMANT |
| V13: API & Web Service | L3 | CONFORMANT |

### 11.3 Evidence Files

- `backend/app/security/` — Authentication, authorization, encryption
- `backend/app/firewall/` — API firewall
- `backend/app/core/idempotency.py` — Idempotency protection

---

## 12. OWASP API Security

### 12.1 Relevance to GULA

OWASP API Security Top 10 identifies the most critical API security risks. All GULA APIs must be verified against these risks.

### 12.2 Implementation Status

| Risk | Mitigation | Location |
|------|-----------|----------|
| API1: Broken Object Level Auth | Tenant isolation (lab_id filter) | All routes |
| API2: Broken Authentication | JWT + blacklist + rate limit | `backend/app/security/auth.py` |
| API3: Excessive Data Exposure | DTOs limit field exposure | All schemas |
| API4: Lack of Resources & Rate Limiting | Rate limiter + concurrency cap | `backend/app/security/rate_limit.py` |
| API5: Broken Function Level Auth | RBAC + ABAC | `backend/app/security/rbac.py`, `abac.py` |
| API6: Mass Assignment | Pydantic validation | All schemas |
| API7: Security Misconfiguration | Hardened defaults | `backend/app/config.py` |
| API8: Injection | SQLAlchemy ORM + input validation | All routes |
| API9: Improper Asset Management | API versioning | Route versioning |
| API10: Logging & Monitoring | Structured logging + audit | `backend/app/core/logging_config.py` |

### 12.3 Evidence Files

- `backend/app/security/rate_limit.py` — Rate limiting
- `backend/app/firewall/api_firewall.py` — API firewall
- `backend/app/main.py` — Security middleware

---

## 13. NIST CSF

### 13.1 Relevance to GULA

NIST Cybersecurity Framework provides a policy framework for cybersecurity. Used alongside ISO 27001 for comprehensive security governance.

### 13.2 Implementation Status

| Function | Category | Status |
|----------|----------|--------|
| IDENTIFY | Asset Management | CONFORMANT |
| IDENTIFY | Risk Assessment | PARTIAL |
| IDENTIFY | Governance | CONFORMANT |
| PROTECT | Access Control | CONFORMANT |
| PROTECT | Data Security | CONFORMANT |
| PROTECT | Awareness Training | N/A (org-level) |
| PROTECT | Protective Technology | CONFORMANT |
| DETECT | Anomalies & Events | CONFORMANT |
| DETECT | Continuous Monitoring | CONFORMANT |
| RESPOND | Response Planning | PARTIAL |
| RESPOND | Communications | PARTIAL |
| RECOVER | Recovery Planning | PARTIAL |
| RECOVER | Improvements | CONFORMANT |

### 13.3 Evidence Files

- `backend/app/security/` — Protect and Detect controls
- `backend/app/core/self_healing.py` — Respond controls
- `config/prometheus/` — Continuous monitoring

---

## 14. NIST 800-53

### 14.1 Relevance to GULA

NIST 800-53 provides a comprehensive catalog of security and privacy controls for federal information systems. Relevant for government deployments.

### 14.2 Implementation Status

| Control Family | Select Controls | Status |
|----------------|----------------|--------|
| AC (Access Control) | AC-2, AC-3, AC-6, AC-17 | CONFORMANT |
| AU (Audit & Accountability) | AU-2, AU-3, AU-6, AU-12 | CONFORMANT |
| IA (Identification & Auth) | IA-2, IA-5, IA-8 | CONFORMANT |
| SC (System & Comms Protection) | SC-8, SC-12, SC-13, SC-28 | CONFORMANT |
| SI (System & Info Integrity) | SI-4, SI-7, SI-12 | CONFORMANT |
| CP (Contingency Planning) | CP-2, CP-9, CP-10 | PARTIAL |
| IR (Incident Response) | IR-4, IR-5, IR-6 | PARTIAL |

### 14.3 Evidence Files

- `backend/app/security/` — AC, IA, AU controls
- `backend/app/core/self_healing.py` — SI, IR controls
- `backend/app/database.py` — SC controls

---

## 15. CIS Controls

### 15.1 Relevance to GULA

CIS Critical Security Controls provide prioritized cybersecurity best practices. Used alongside NIST and ISO for defense-in-depth.

### 15.2 Implementation Status

| Control | Implementation | Status |
|---------|---------------|--------|
| 1: Inventory of Assets | Docker, module registry | CONFORMANT |
| 2: Software Inventory | SBOM in CI | CONFORMANT |
| 3: Data Protection | Encryption, audit | CONFORMANT |
| 4: Secure Configuration | Hardened defaults | CONFORMANT |
| 5: Account Management | RBAC, session management | CONFORMANT |
| 6: Access Control Management | RBAC + ABAC | CONFORMANT |
| 7: Continuous Vulnerability Mgmt | Trivy, safety in CI | CONFORMANT |
| 8: Audit Log Management | Structured audit | CONFORMANT |
| 9: Email & Web Protections | Cloudflare WAF | CONFORMANT |
| 10: Malware Defenses | Container scanning | CONFORMANT |
| 11: Recovery | Backup procedures | PARTIAL |
| 12: Network Infrastructure Mgmt | Docker networking | CONFORMANT |
| 13: Network Monitoring | Prometheus, Grafana | CONFORMANT |
| 14: Security Awareness Training | N/A (org-level) | N/A |
| 15: Service Provider Mgmt | Render, DigitalOcean | CONFORMANT |
| 16: Application Software Security | CI security gates | CONFORMANT |
| 17: Incident Response | Self-healing, alerting | CONFORMANT |
| 18: Penetration Testing | Scheduled scans | PARTIAL |

### 15.3 Evidence Files

- `.github/workflows/ci.yml` — CI with security scanning
- `backend/app/core/self_healing.py` — Incident response
- `config/prometheus/` — Monitoring

---

## 16. OpenAPI 3.1

### 16.1 Relevance to GULA

OpenAPI 3.1 is the specification for RESTful API documentation. GULA's FastAPI framework auto-generates OpenAPI specs.

### 16.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Auto-generated spec | CONFORMANT | FastAPI /openapi.json |
| Schema definitions | CONFORMANT | Pydantic models |
| Path documentation | CONFORMANT | Route docstrings |
| Authentication documentation | CONFORMANT | Security schemes |
| JSON Schema compatibility | CONFORMANT | OpenAPI 3.1 (JSON Schema 2020-12) |

### 16.3 Evidence Files

- `backend/app/main.py` — OpenAPI configuration
- `backend/app/routes/` — All route definitions
- Pydantic models throughout — Schema definitions

---

## 17. AsyncAPI 2.6

### 17.1 Relevance to GULA

AsyncAPI 2.6 is the specification for event-driven APIs. Relevant for documenting outbox events, WebSocket streams, and pub/sub channels.

### 17.2 Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Event documentation | PLANNED | Future AsyncAPI spec |
| Outbox events | PARTIAL | `backend/app/lims/events.py` |
| WebSocket endpoints | PLANNED | Future |
| Channel documentation | NOT STARTED | |

### 17.3 Gap Analysis

| Gap | Priority | Impact |
|-----|----------|--------|
| No AsyncAPI spec | Medium | Event-driven API documentation |
| Channel definitions incomplete | Medium | Integration documentation |

### 17.4 Evidence Files

- `backend/app/lims/events.py` — Event definitions (starting point for AsyncAPI)
- `backend/app/national/events/` — National events
- `backend/app/kernel/event_bus/` — Event bus infrastructure

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial compliance framework |

**Review Cycle**: This document must be reviewed and updated quarterly or when compliance requirements change.
