# Architecture Decision Records — Nursing Platform

---

## ADR-001: Nursing as Independent Bounded Context

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, Clinical Product Manager

### Context

Nursing workflows (shift management, vital signs, assessments, medication administration, handovers) are currently handled ad-hoc within the clinical module. As nursing requirements grow, embedding them in the clinical module creates tight coupling and diffuses ownership.

### Decision

Model the Nursing Platform as an **independent bounded context** with its own module (`backend/app/nursing/`), models, services, and routes.

### Rationale

1. **Domain independence** — Nursing has distinct workflows, terminology, and regulatory requirements that differ from physician or laboratory domains. A dedicated bounded context allows domain experts to own the model.
2. **Evolution autonomy** — Nursing features can evolve independently of other platform modules. Changes to nursing workflows do not affect physician or lab features.
3. **Team scalability** — A dedicated nursing domain allows a separate team to develop and maintain the platform without blocking other teams.
4. **Offline semantics** — Nursing offline requirements (vital signs during internet outage, medication admin in offline mode) have different conflict resolution strategies from other domains.
5. **Regulatory scope** — Nursing documentation has specific legal and regulatory requirements that may differ from general clinical documentation.

### Consequences

- **Positive**: Domain clarity, independent evolution, team scalability, appropriate offline semantics
- **Negative**: Data duplication with clinical module (patient demographics, medication orders); cross-domain queries require joins; integration overhead for nurse-patient assignment across modules

---

## ADR-002: Reuse EHR Medication Models for Medication Administration

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Clinical Product Manager

### Context

The BCMA workflow requires medication data (drug name, dose, route, schedule) that is already managed by the EHR medication ordering system. Duplicating this data in the nursing module creates a risk of inconsistency.

### Decision

Reuse EHR medication models as the **source of truth** for medication data. The Nursing Platform models (`MedicationAdminRecord`, `MedicationSchedule`) reference EHR orders by foreign key rather than duplicating drug data.

### Rationale

1. **Single source of truth** — Medication orders are created and managed by the EHR. Nursing should read and reference, not duplicate.
2. **Consistency** — Drug names, doses, routes, and frequencies are defined once in the EHR formulary. Nursing BCMA validates against these definitions.
3. **Audit trail** — The medication administration record links directly to the originating order, providing a complete chain from prescribing to administration.
4. **Reuse of validation** — EHR order validation (dose range, interaction checks) is already implemented; nursing benefits without reimplementing.

### Consequences

- **Positive**: No duplication, consistent drug data, full audit chain, validation reuse
- **Negative**: Tight coupling to EHR order schema; schema changes in EHR require nursing model updates; offline medication administration requires cached order data

---

## ADR-003: Vital Signs as Nursing-Specific Model (Not Generic Observation)

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Clinical Product Manager

### Context

The GULA platform has a generic `Observation` model used for laboratory results. Vital signs could theoretically use the same model with different observation types. However, nursing vital signs have distinct workflow requirements (set-based recording, EWS calculation, charting, trending).

### Decision

Create **nursing-specific vital signs models** (`VitalSignSet`, `VitalSignObservation`) separate from the generic observation model.

### Rationale

1. **Workflow differences** — Vital signs are recorded as a set (all observations taken at one time). Lab results are individual observations that accumulate over time. A set-based model better represents nursing workflow.
2. **EWS calculation** — Early Warning Score calculation requires a complete set of observations recorded together. Using a generic observation model would require complex grouping logic.
3. **Charting requirements** — Vital sign charting (trend lines, ranges, alerts) has different visualisation needs than lab results.
4. **Recording context** — Vital signs track the measurer, device used, patient position, and clinical context that are not relevant to lab results.
5. **Performance** — Vital signs are recorded at high frequency (every 1-4 hours for inpatients). A dedicated table with optimised indexes for time-series queries outperforms a generic observation model.

### Consequences

- **Positive**: Workflow-optimised, clean EWS calculation, simpler charting, better performance
- **Negative**: Data duplication with generic observation model; FHIR mapping to `Observation` resource requires transformation logic; lab result trend viewers cannot show vital signs without cross-model queries

---

## ADR-004: Structured Assessments Over Free Text

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Clinical Product Manager, UX Lead, Engineering Lead

### Context

Nursing assessments (pain, fall risk, pressure ulcer risk) are currently documented as free-text notes. This leads to inconsistent documentation, incomplete assessments, and inability to trend scores over time.

### Decision

Implement **structured assessment models** with standardised scoring tools (numeric pain scale, Morse fall risk, Braden scale) rather than free-text documentation.

### Rationale

1. **Clinical standards** — Iraqi Ministry of Health and international guidelines (NICE, AHRQ) recommend standardised assessment tools. Structured models enforce evidence-based practice.
2. **Trendability** — Numerical scores can be trended over time to track patient improvement or deterioration. Free text cannot be trended.
3. **Decision support** — Structured scores trigger automated clinical decision support (e.g., fall risk score > 45 triggers fall prevention protocol).
4. **Reporting** — Structured assessments enable aggregate reporting (e.g., percentage of patients with fall risk assessment completed, average pain scores by ward).
5. **Research** — Structured data enables clinical research and quality improvement initiatives.

### Consequences

- **Positive**: Standardised care, trendable scores, automated decision support, aggregate reporting
- **Negative**: More complex model than free text; new assessment tools require schema changes; training required for nurses to use structured forms

---

## ADR-005: Barcode Medication Administration (BCMA) Workflow

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Clinical Product Manager, Engineering Lead, Patient Safety Officer

### Context

Medication administration errors are a leading cause of patient harm. The nursing platform must implement a barcode-assisted workflow to reduce errors while integrating with the existing EHR medication ordering system and National Pharmacy Platform (NPIP).

### Decision

Implement a **full BCMA workflow** with the five rights verification (right patient, right drug, right dose, right route, right time), barcode scanning support, and electronic signature capture.

### Rationale

1. **Patient safety** — BCMA reduces medication administration errors by 50-80% in published studies. The five rights verification enforces safety checks that are easy to bypass in manual workflows.
2. **Iraqi context** — Iraqi hospitals are increasingly adopting barcode wristbands for patient identification. BCMA leverages existing investment in patient identification infrastructure.
3. **Integration** — The BCMA model (`MedicationAdminRecord`) links to both the EHR medication order (for validation) and the NPIP dispensing record (for medication identification), creating a complete closed-loop medication management system.
4. **Audit trail** — Every administration is logged with electronic signature, providing a complete record for clinical and legal purposes.
5. **Controlled substances** — The same workflow supports controlled substance administration with additional witness verification requirements.

### Consequences

- **Positive**: Significant error reduction, closed-loop medication management, complete audit trail
- **Negative**: Barcode scanning adds time to the administration process; requires barcode printers and scanners at point of care; technical failures (unreadable barcodes, system offline) need fallback procedures; training required for adoption
