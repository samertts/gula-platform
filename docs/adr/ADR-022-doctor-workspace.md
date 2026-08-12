# ADR-022: National Doctor Clinical Workspace

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Clinical Product Manager, UX Lead

---

## Context

Physicians in Iraqi healthcare facilities lack a unified digital workspace for managing patient care. They currently piece together patient information from multiple sources: laboratory results from GULA, clinical notes from paper records or disparate systems, imaging from separate PACS viewers, and prescriptions from pharmacy systems. This fragmented workflow reduces clinical efficiency and increases the risk of errors.

**Requirements:**
- Unified clinical workspace for physicians to manage patient care end-to-end
- Patient dashboard with alerts, recent results, upcoming appointments, and care gaps
- Longitudinal patient record with full clinical history (labs, diagnoses, medications, immunizations, procedures, notes)
- Clinical orders (laboratory, imaging, medications, referrals) with order set support
- Clinical documentation (consult notes, progress notes, discharge summaries)
- Result review with trend visualization and AI-powered interpretation (via ADR-021)
- Integration with all national platform services (EHR, intelligence, notifications, ecosystem)
- Offline support for clinical documentation in low-connectivity settings

**Constraints:**
- Must be FHIR-native — all clinical data stored and exchanged as FHIR R4 resources
- Must support offline-first operation for rural clinics with intermittent internet
- Must integrate with existing GULA laboratory workflows (orders, results, samples)
- Must provide role-based access aligned with physician credentialing and patient consent
- Must not duplicate functionality of the Citizen Super App (physician and citizen views are separate)

## Decision

Extend the existing `clinical/` module with a comprehensive doctor clinical workspace. The workspace is a web-based application (responsive, desktop-first) that serves as the primary clinical application for physicians across Iraq. It is FHIR-native, offline-first, and integrates with all national platform services.

### Architecture

```
+------------------------------------------------------------------+
|               National Doctor Clinical Workspace                  |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |                   Presentation Layer                        |   |
|  |  React (desktop-first responsive)  |  Arabic-first UI       |   |
|  |  Offline-first (IndexedDB)         |  Clinical-grade UX     |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Feature Modules                          |   |
|  |                                                              |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |  | Patient  |  | Clinical |  | Orders & |  | Clinical |     |   |
|  |  | Dashboard|  | Record   |  | Results  |  | Notes    |     |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |                                                              |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |  | Care     |  | Referrals|  | Clinical |  | AI       |     |   |
|  |  | Plans    |  | & Consult|  | Decision |  | Insights |     |   |
|  |  |          |  |          |  | Support  |  | (ADR-021)|     |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Service Layer                            |   |
|  |  Sync Engine  |  Offline Manager  |  Notification Handler  |   |
|  |  FHIR Client  |  Cache Manager    |  Auth (OAuth 2.0)      |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
+------------------------------+------------------------------------+
                               |
+------------------------------+------------------------------------+
|                    Clinical Platform Services                      |
+------------------------------------------------------------------+
|                                                                   |
|  +----------+  +----------+  +----------+  +----------+  +----+  |
|  | EHR API  |  | Orders   |  | Intelli- |  | Ecosys-  |  |Lab |  |
|  |(ADR-016) |  | Service  |  | gence AI |  | tem Gate |  |API |  |
|  |          |  |          |  |(ADR-021) |  |(ADR-019) |  |    |  |
|  +----------+  +----------+  +----------+  +----------+  +----+  |
|                                                                   |
+------------------------------------------------------------------+
```

### Key Design Decisions

1. **FHIR-native from day one** — The workspace uses FHIR R4 as its internal data model. All clinical data is created, read, updated, and queried as FHIR resources. This ensures seamless interoperability with the National EHR (ADR-016) and other FHIR-compliant systems.

2. **Desktop-first responsive design** — Physicians primarily work on desktop/laptop computers in clinical settings. The workspace is designed for large screens with rich data visualization, but is responsive for tablet use during rounds.

3. **Clinical-grade UX** — The workspace follows clinical workflow patterns: rounding lists, patient charts, order sets, and structured documentation. UX is designed with input from Iraqi physicians and follows established EHR usability best practices.

4. **Offline-first for rural clinics** — Clinical documentation and order entry work offline, syncing when connectivity is restored. This is critical for the many Iraqi clinics with intermittent internet access.

5. **AI-assisted clinical decisions** — Workspace integrates with the National Health Intelligence Platform (ADR-021) for result interpretation, risk scores, drug interaction checks, and clinical decision support — all presented as advisory, non-blocking guidance.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | Patient dashboard, longitudinal record (read-only), FHIR integration | 10 weeks |
| **Phase 2** | Clinical orders, result review with trends, offline support | 8 weeks |
| **Phase 3** | Clinical documentation, care plans, referrals, AI insights | 10 weeks |
| **Phase 4** | Clinical decision support, rounding workflows, production optimization | 8 weeks |

## Consequences

### Positive
- **Unified physician experience** — All patient care activities in one workspace
- **FHIR-native** — Seamless interoperability with national and international health systems
- **Offline-first** — Usable in rural Iraqi clinics with limited connectivity
- **AI-powered** — Clinical decision support integrated directly into workflow
- **Integrated with all platforms** — EHR, intelligence, ecosystem, laboratory
- **Clinical-grade** — Designed for physician workflows, not a generic portal

### Negative
- **Complexity** — Clinical workspace is the most feature-rich application in the platform
- **Training requirement** — Physicians need training on the workspace, which requires change management
- **Performance demands** — Rich clinical data visualization requires significant client-side resources
- **Regulatory approval** — Clinical software may require Iraqi Ministry of Health certification

### Risks
- **Clinical safety** — A software error could lead to incorrect treatment. Mitigated by: FHIR validation on all writes, clinical content reviewed by domain experts, alert fatigue management, no hard stops for non-safety-critical decisions.
- **Adoption resistance** — Physicians accustomed to paper or existing systems may resist change. Mitigated by: phased rollout, physician champions, parallel run with legacy systems, continuous feedback integration.
- **Offline data conflicts** — Two physicians editing the same patient record offline could create conflicts. Mitigated by: last-writer-wins with audit log, conflict detection UI, real-time collaboration when online (WebSocket).

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 1** — Patient-centric, physician-empowering design
- **Engineering Constitution Section 3** — Data integrity; FHIR-native ensures consistent clinical data
- **ADR-016** — EHR platform provides the longitudinal patient record
- **ADR-021** — Intelligence platform provides AI clinical decision support
- **ADR-019** — Ecosystem enables integration with external clinical systems
- **FHIR R4 Clinical Practice Guidelines** — Structured data collection
- **Iraqi Ministry of Health Clinical Software Standards** — Certification alignment
- **HIPAA Security Rule** — Technical safeguards for clinical data access
