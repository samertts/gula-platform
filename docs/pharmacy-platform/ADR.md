# Architecture Decision Records — National Pharmacy Information Platform (NPIP)

---

## ADR-001: National Drug Catalog as Single Source of Truth

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Pharmacy Product Manager, Ministry of Health Representative

### Context

Iraqi hospitals currently maintain separate drug lists, leading to inconsistent naming, duplication, and inability to aggregate national medication data. The pharmacy platform needs a unified medication reference.

### Decision

Establish a **National Drug Catalog** as the single source of truth for all medication data across the GULA platform. All medication references (prescriptions, dispensing, inventory, EHR ordering) use the catalog entry as their canonical drug identifier.

### Rationale

1. **Standardisation** — A single catalog ensures consistent drug naming, coding (ATC), and barcoding (GS1) across all facilities.
2. **National reporting** — Aggregate medication usage data at the national level requires a common drug identifier. Without a unified catalog, cross-facility reporting is impossible.
3. **Clinical safety** — Inconsistent drug naming leads to medication errors (wrong drug selection, confusion between look-alike/sound-alike names). A curated catalog prevents this.
4. **Integration** — EHR prescribing, pharmacy dispensing, and nursing administration all reference the same catalog entry, ensuring end-to-end consistency.
5. **Maintenance** — A single catalog is easier to maintain, update, and quality-control than N distributed lists.

### Consequences

- **Positive**: Standardisation, national reporting capability, reduced errors, simplified integration
- **Negative**: Catalog must be kept current (new drugs, discontinued drugs, pricing changes); requires a formal governance process for catalog additions/changes; migration required for existing facilities with local drug lists

---

## ADR-002: GS1 Barcode Standard for All Medications

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Supply Chain Manager

### Context

Medication tracking from receipt to administration requires barcode identification. Multiple standards exist globally (GS1, NDC, local codes), and Iraqi pharmaceutical supply uses a mix of standards.

### Decision

Adopt **GS1-128 / GS1 DataMatrix** as the primary barcode standard for all medication tracking in NPIP.

### Rationale

1. **Global standard** — GS1 is the most widely adopted supply chain standard globally, including in healthcare (GS1 Healthcare). Most international pharmaceutical manufacturers already use GS1 barcodes.
2. **Data capacity** — GS1 DataMatrix can encode GTIN, lot number, expiry date, and serial number in a single small barcode, supporting full traceability.
3. **End-to-end** — GS1 supports the complete medication journey: manufacturer → distributor → pharmacy receipt → dispensing → patient administration. The same barcode is scanned at each step.
4. **Patient safety** — GS1 barcodes encode expiry dates, enabling automatic expiry checking at dispensing. Serialisation supports counterfeit detection.
5. **Iraqi alignment** — The Iraqi Ministry of Health is adopting GS1 standards for pharmaceutical supply chain management. NPIP alignment positions the platform for future regulatory requirements.

### Consequences

- **Positive**: Global standard, full traceability, expiry checking, counterfeit detection, regulatory alignment
- **Negative**: Existing inventory with non-GS1 barcodes requires relabeling; GS1 barcode scanners required at all pharmacy locations; GTIN lookup service needed for drug identification

---

## ADR-003: Drug Interaction Engine as Service Not DB Constraint

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Clinical Product Manager, Engineering Lead

### Context

Drug-drug interaction checking could be implemented as database constraints (trigger-based on prescription creation) or as a service layer module.

### Decision

Implement drug interaction checking as a **service module** (`ClinicalEngine`) rather than database-level constraints.

### Rationale

1. **Knowledge base complexity** — Drug interaction data is complex: severity levels, mechanisms, management recommendations, evidence levels. Database constraints cannot represent this richness.
2. **External data sources** — The interaction knowledge base is derived from external sources (DrugBank, IBM Micromedex) that change regularly. A service layer can update without schema migrations.
3. **Context-dependent checking** — Interactions depend on patient-specific factors (age, renal function, concurrent conditions). Database triggers lack access to this context.
4. **Performance** — Interaction checking for a full polypharmacy regimen involves N² drug pair comparisons. This is better handled by a service that can cache results and use indexed lookups.
5. **Extensibility** — A service can be extended to include drug-food interactions, drug-lab interactions, and pharmacogenomic interactions without schema changes.

### Consequences

- **Positive**: Rich safety logic, flexible knowledge base updates, context-aware checking, extensible
- **Negative**: Potential latency for check requests (mitigated by caching); service must be highly available during dispensing; knowledge base licensing costs may apply

---

## ADR-004: Controlled Substance Audit Trail Mandatory

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Compliance Officer, Ministry of Health Representative

### Context

Controlled substances (narcotics, psychotropics, precursors) are subject to strict regulatory oversight in Iraq. The pharmacy platform must provide a complete, tamper-evident audit trail for all controlled substance transactions.

### Decision

Make controlled substance audit trail **mandatory and non-bypassable** for all Schedule I-IV medications. Every transaction records who, what, when, quantity before/after, balance after, requiring dual signatures for Schedule I-II.

### Rationale

1. **Regulatory compliance** — Iraqi MOH regulations require complete traceability for controlled substances. Non-compliance can result in facility license suspension.
2. **Diversion prevention** — A complete audit trail deters and detects medication diversion. Sequential, non-repeating transaction IDs prevent record tampering.
3. **Balance reconciliation** — Automated balance-after calculation with mandatory reconciliation at defined intervals (daily for Schedule I, weekly for Schedule II) ensures discrepancies are detected early.
4. **Legal protection** — Complete records protect pharmacists and nurses from unfounded allegations of diversion or misuse.
5. **Audit readiness** — Regulators can audit any controlled substance transaction from receipt to patient administration with a single query.

### Consequences

- **Positive**: Full regulatory compliance, diversion detection, legal protection, audit readiness
- **Negative**: Slower workflow for controlled substances (dual signatures required); offline mode limitations for controlled substances; additional storage and backup requirements for audit data

---

## ADR-005: ATC Classification System for Iraq

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Clinical Product Manager, Ministry of Health Representative

### Context

The NPIP drug catalog needs a classification system for drug organisation, therapeutic alternative identification, and national reporting.

### Decision

Use the **WHO ATC (Anatomical Therapeutic Chemical) classification system** as the primary drug classification, with Iraqi Ministry of Health extensions for locally specific medications.

### Rationale

1. **International standard** — ATC is the WHO-recommended classification system, used globally for drug utilisation research and reporting.
2. **Therapeutic alternatives** — ATC's 5-level hierarchy enables automatic identification of therapeutic alternatives at the chemical subgroup (Level 4) level.
3. **National reporting** — Iraqi MOH reporting requirements align with ATC classification. Aggregate consumption data (DDD/1000 inhabitants/day) is ATC-based.
4. **Integration** — International drug databases and interaction knowledge bases use ATC codes. Using ATC simplifies data exchange.
5. **Iraqi extensions** — The system supports adding custom ATC-like codes for medications that are approved in Iraq but not in the WHO ATC index, ensuring complete coverage without breaking standard compatibility.

### Consequences

- **Positive**: International standard, therapeutic alternatives, national reporting compatibility, integration ready
- **Negative**: ATC maintenance overhead (WHO updates ATC annually); custom Iraqi extensions require governance; training needed for pharmacy staff on ATC navigation

---

## ADR-006: Pharmacy Drug Identity Model (NR-003)

**Status:** Accepted
**Date:** 2026-09-09
**Deciders:** Platform Owner
**Supersedes:** nothing. **Extends:** ADR-001, ADR-002, ADR-005

### Context

Three incompatible Pharmacy generations exist in this repository:

- **Generation A (physical/Alembic)** — 23 tables created by `20260716_0003`, `Integer` primary keys, `drug_id` foreign keys, `drug_code` business code, catalog global with no `lab_id`.
- **Generation B (ORM/API)** — `backend/app/pharmacy/`, `String(26)` application-generated primary keys, `drug_catalog_id` foreign keys, `code`, and a **tenant-scoped** catalog carrying `lab_id`. It cannot execute against Generation A.
- **Generation C (documented target)** — `docs/pharmacy-platform/ARCHITECTURE.md`, a normalized 22-model design (formulation / package / pricing / ATC hierarchy / ingredients). Not implemented; it references drugs by `drug_id` and leaves the immutable drug identity undefined.

NR-003 surfaced as a foreign-key type clash, but the underlying defect is this three-way divergence. Analysis established that `drug_code` is **unique but mutable**: it is changeable through the service layer, has no defined minting authority, is absent from Generation C's catalog key fields, and is denormalized into four clinical-safety rule tables without a foreign key.

### Decision

The National Drug Catalog is **global** and MoH-governed (per ADR-001). Its identity model is:

| Concern                             | Identity                                | Rule                                                                         |
| ----------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------- |
| Internal database key               | `Integer` primary key                   | Never exposed publicly                                                       |
| Public/canonical GULA drug identity | **opaque UUID4**, server-generated      | Immutable, unique, non-null, indexed                                         |
| Business/catalog code               | `drug_code`                             | Mutable. Never a primary key, foreign key, or clinical-rule key              |
| Package identifier                  | GTIN (GS1)                              | Package level only (ADR-002)                                                 |
| Classification                      | ATC                                     | Classification only, never identity (ADR-005)                                |
| FHIR identity                       | `fhir_id`                               | FHIR resource identity only                                                  |
| Synchronisation identity            | `sync_id`                               | Offline/sync identity only                                                   |
| Facility inventory                  | internal foreign key to the drug entity | Tenant scope belongs to inventory and location records, never to the catalog |
| Clinical safety rules               | internal foreign key to the drug entity | Never a duplicated `drug_code` as the authoritative relationship             |

**The GULA UUID4 drug identity is a platform identity, not a national regulatory registration number.**

A future Ministry of Health drug registration identifier must be added as an **additional external identifier**. It must not replace the internal primary key or the public UUID identity without a separate architecture decision.

### Rejected alternatives

- **`Integer` primary key as the public identity** — rejected: sequential and enumerable, and it couples the public contract to a storage detail.
- **`drug_code` as the canonical immutable identity** — rejected: mutable through the service layer, no defined minting authority, absent from Generation C's catalog key fields. Uniqueness is not immutability.
- **GTIN as the drug identity** — rejected: GTIN identifies a _package_, not a drug.
- **ATC as identity** — rejected: a classification, not unique per product.
- **`String(26)` (Generation B) as the catalog primary key** — rejected: it is a truncated UUID4 (`uuid4().hex.upper()[:26]`), not a ULID; it has no time ordering, and adopting it would require rewriting 23 tables' primary keys with no corresponding benefit.

### Consequences

- **Positive**: identity is separated from storage, classification, packaging and pricing; clinical rules can no longer be silently detached by a business-code edit; the public contract stops exposing a database sequence; room is preserved for a future MoH identifier.
- **Negative**: the catalog gains a second identifier column that must be backfilled exactly once and never regenerated; Generation B must be reconciled to Generation A before the model can be realised; Generation C normalisation remains outstanding.

### Implementation status

**NOT IMPLEMENTED.** This record captures the decision only. Two blockers are documented in the NR-003 implementation report and must be resolved by the platform owner before any schema or code change:

1. Repairing the `String(26)` → `Integer` foreign keys on `pharmacy_drug_substitution_rules` requires modifying migration `20260815_0023`, which the repository's mandatory migration policy forbids.
2. Reconciling Generation B to Generation A is a full-domain rewrite, not a localized change.
