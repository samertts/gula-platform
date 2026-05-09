# Standards Mapping Matrix

This matrix links sovereign-phase requirements to recognized healthcare,
information-security, and digital-health standards. Mapping is **declarative**
— it does not certify GULA against any standard; it identifies the surface
area on which conformance work would happen.

Legend:
- ✅ Documented architectural fit; no code changes required
- 🟡 Documented assumption; partial code enforcement
- 🔴 Documentation only; code enforcement pending in a future approved phase
- — Not applicable

## A. Healthcare Interoperability Standards

| Domain | Standard | GULA surface | State | Phase |
|--------|----------|--------------|-------|-------|
| Clinical messaging | **HL7 v2.x** (ORM, ORU, ADT) | `services/device_bridge/` (LabLink-Core ASTM/HL7) | 🟡 device-side; institutional HL7 still 🔴 | 16 |
| Resource model | **HL7 FHIR R4** (Patient, Specimen, Observation, DiagnosticReport, Encounter, ServiceRequest) | Adapter mapping in `interoperability/fhir/*` (scaffold) | 🔴 | 16, 19 |
| Public-health reporting | **DHIS2** aggregation | Anonymized analytics export pipeline | 🔴 | 20 |
| Laboratory results | **LOINC** | `LabResult.test_code` mapping | 🟡 codes accepted; canonical mapping table 🔴 | 19 |
| Diagnoses | **ICD-10 / ICD-11** | `lab_orders.icd_codes` | 🟡 stored; cross-walk 🔴 | 19, 22 |
| Clinical terminology | **SNOMED CT** | terminology-governance module (scaffold) | 🔴 | 19 |
| Specimen workflow | **HL7 v2 OBR/SPM** | order_state state machine | 🟡 | 16 |

## B. Healthcare Quality & Accreditation

| Standard | Scope | GULA touchpoint | State | Phase |
|----------|-------|-----------------|-------|-------|
| **CAP** (College of American Pathologists) | Lab proficiency, QC | Result release governance, calibration audit | 🔴 (documentation) | 18 |
| **CLSI** (Clinical and Laboratory Standards Institute) | QC and reference intervals | Reference-range data governance | 🔴 | 18 |
| **ISO 15189** | Medical laboratory competence | Document control + audit chain + chain-of-custody | 🟡 audit chain in place | 18 |

## C. Information Security & Privacy

| Standard | Scope | GULA touchpoint | State | Phase |
|----------|-------|-----------------|-------|-------|
| **ISO 27001** | ISMS controls | Security middleware, secrets policy, incident framework | 🟡 | 17, 18 |
| **ISO 27799** | Health information security | Patient-data encryption-at-rest (`national_id`), audit immutability | 🟡 | 18, 19 |
| **NIST SP 800-53** moderate baseline | Federal control set | Auth, audit, contingency, risk assessment | 🔴 (mapping doc only) | 18 |
| **OWASP ASVS L2** | App security verification | Existing security middleware stack | 🟡 | 18 |

## D. Digital Health Governance

| Standard / Reference | Scope | GULA touchpoint | State | Phase |
|----------------------|-------|-----------------|-------|-------|
| **WHO Digital Health guidelines** | National DH governance | National deployment checklist | 🔴 | 18, 24 |
| **GDPR (Art. 9 — health data)** *(referenced as a maturity baseline; jurisdictional mapping required)* | Lawful processing, data-subject rights | Consent, retention, audit | 🔴 | 24 |
| **National Iraqi Data Protection** *(jurisdictional)* | Sovereign retention + cross-border rules | Data sovereignty doc | 🔴 | 24 |

## E. Operational & DR

| Reference | Scope | GULA touchpoint | State | Phase |
|-----------|-------|-----------------|-------|-------|
| **ISO 22301** Business continuity | BC/DR program | DR readiness, runbooks | 🟡 | 17, 23 |
| **NIST SP 800-34** Contingency planning | Tabletop, recovery objectives | Failover playbooks | 🔴 (process only) | 17, 23 |

## F. AI Governance

| Reference | Scope | GULA touchpoint | State | Phase |
|-----------|-------|-----------------|-------|-------|
| **ISO/IEC 42001** AI management system | AI governance program | AI capability scoping, explainability | 🔴 | 21 |
| **WHO Ethics & governance of AI for health** | Clinical AI ethics | Human-override, fail-closed | 🟡 | 21 |
| **EU AI Act — high-risk system practices** *(maturity reference, jurisdiction-dependent)* | Risk management, transparency | AI auditability hooks | 🔴 | 21 |

---

## Mapping Discipline

For each standard above, the corresponding phase document must contain:

1. **Scope statement** — which clauses/articles are in scope.
2. **Enforcement model** — code, process, or documentation-only.
3. **Evidence map** — where in the codebase or runbooks evidence lives.
4. **Gap register** — what is missing for formal certification.

The mapping does not assert certification. It asserts auditable readiness.
