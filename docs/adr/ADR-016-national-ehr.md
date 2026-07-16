# ADR-016: National Electronic Health Record Platform

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Architecture Committee, CTO

---

## Context

The GULA platform must evolve to serve as a single longitudinal medical record for every Iraqi citizen. Currently, patient health data is fragmented across laboratory information systems, hospital systems, physician records, and paper files. There is no unified electronic health record (EHR) that provides a complete, continuous view of a citizen's health journey from birth through all healthcare encounters.

**Requirements:**
- Single longitudinal record per citizen spanning all healthcare encounters (labs, visits, hospitalizations, prescriptions, immunizations)
- FHIR R4 compliance for interoperability with national and international health systems
- Zero duplication of existing GULA clinical data — all current lab results, patient records, and order histories must be accessible through the EHR without migration
- Role-based access with patient consent management
- Support for Iraqi national health identifiers and SNDHS integration
- Scalable to Iraq's ~45 million citizens with hundreds of millions of clinical records

**Constraints:**
- Must not duplicate or replace existing GULA database tables — EHR must be a logical layer over existing data
- Must maintain backward compatibility with all existing GULA APIs and integrations
- Must operate within existing infrastructure (PostgreSQL 16, Redis 7)
- Must comply with Iraqi health data sovereignty and privacy regulations

## Decision

Build a **FHIR R4-native EHR platform** that reuses existing GULA clinical, FHIR, and data models as its foundation rather than creating a separate EHR database. The EHR is a logical and API layer, not a data silo.

### Architecture

```
+-----------------------------------------------------+
|                 National EHR Platform               |
+-----------------------------------------------------+
|                                                      |
|  +-------------+  +-------------+  +-------------+  |
|  | FHIR R4 API |  | Patient     |  | Clinical    |  |
|  | (read/write)|  | Timeline    |  | Document   |  |
|  |             |  | Service     |  | Service     |  |
|  +------+------+  +------+------+  +------+------+  |
|         |                |                |          |
|  +------+----------------+----------------+------+  |
|  |           EHR Orchestration Layer              |  |
|  |  (FHIR resource mapping, consent, audit)       |  |
|  +------+----------------+----------------+-------+  |
|         |                |                |          |
|  +------+-----+  +------+------+  +------+-------+  |
|  | GULA Core  |  | SNDHS       |  | External     |  |
|  | Data Models |  | Integration |  | FHIR Sources |  |
|  +------------+  +-------------+  +--------------+  |
|                                                      |
+-----------------------------------------------------+
```

### Key Design Decisions

1. **FHIR R4 as canonical format** — All EHR data is exposed as FHIR R4 resources. The orchestration layer maps between GULA's internal models and FHIR resources in real time. No ETL batch pipelines, no duplicate storage.

2. **Logical patient record** — The EHR Patient resource composes data from `patients`, `lab_results`, `lab_orders`, `visits`, and external sources into a unified view. The underlying tables remain the source of truth.

3. **Consent management** — Patients control access to their EHR via explicit consent records. The consent engine intercepts all FHIR read/write operations and enforces patient preferences.

4. **National identity integration** — Citizens are identified by their SNDHS Health ID (primary), Iraqi National ID, or existing GULA patient UUID. All identifiers are linked in a patient identity registry.

5. **Audit and provenance** — Every FHIR operation is logged with full provenance tracking, meeting both clinical and Iraqi regulatory requirements.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | FHIR Patient, Observation, DiagnosticReport resources; read-only; patient timeline | 8 weeks |
| **Phase 2** | FHIR Condition, Medication, Immunization, Procedure resources; write support | 8 weeks |
| **Phase 3** | Consent management, patient portal integration, national identity linking | 6 weeks |
| **Phase 4** | Full FHIR R4 compliance certification, performance optimization, production rollout | 6 weeks |

## Consequences

### Positive
- **Zero database duplication** — No new EHR tables; all data remains in its existing canonical location
- **Full FHIR R4 compliance** — Interoperable with international health systems and standards
- **Backward compatible** — All existing GULA APIs continue to work unchanged
- **Gradual rollout** — Each phase adds capabilities without disrupting existing operations
- **Single source of truth** — No risk of EHR data diverging from operational data
- **Patient-centric design** — Built around the citizen's longitudinal health journey

### Negative
- **Orchestration complexity** — Real-time FHIR mapping adds latency and complexity compared to storing pre-computed FHIR resources
- **Query performance** — Composing patient records across multiple tables requires careful optimization, indexing, and caching
- **Consent overhead** — Every read operation must check consent, adding latency to all FHIR queries
- **FHIR learning curve** — Team must develop deep FHIR R4 expertise

### Risks
- **Performance under load** — Composing FHIR resources from multiple tables at national scale (~45M citizens) may require aggressive caching. Mitigated by: Redis caching of frequently accessed resources, materialized views for common queries, read replicas for FHIR queries.
- **Consent complexity** — Fine-grained consent (per-resource-type, per-practitioner, time-limited) is complex to implement correctly. Mitigated by: phased consent rollout, starting with all-or-nothing consent, adding granularity later.
- **FHIR version evolution** — FHIR R4 will eventually be superseded. Mitigated by: abstraction layer between FHIR resources and internal models, making FHIR version upgrades a mapping change rather than a data migration.

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 7** — Architecture decisions must be recorded as ADRs
- **Engineering Constitution Section 3** — Data integrity and patient safety are paramount
- **ADR-003** — Multi-tenant isolation via `lab_id` is preserved; EHR adds national-level access controls
- **ADR-006** — Clinical AI integration leverages EHR data for intelligence
- **ADR-010** — SNDHS-lite integration provides the national identity foundation
- **Iraqi Health Data Privacy Regulations** — Patient consent and data sovereignty
- **FHIR R4 International Patient Access (IPA)** — Interoperability standard compliance
