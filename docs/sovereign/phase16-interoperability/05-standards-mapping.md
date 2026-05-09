# Phase 16-05 — Interoperability Standards Mapping

This document expands the global `STANDARDS_MAPPING_MATRIX.md` for the
interoperability surface specifically. It identifies the **resource-level**
mappings each institutional adapter must support.

## FHIR R4

| FHIR Resource | GULA model | Direction | Notes |
|---------------|------------|-----------|-------|
| `Patient` | `Patient` | both | National ID maps to `identifier[system="urn:iq:national-id"]`; SNDHS health ID maps to `identifier[system="urn:iq:sndhs-health-id"]`. Both encrypted at rest, dual-read aware. |
| `Specimen` | `Sample` | both | Chain-of-custody timestamps preserved as `Specimen.collection.collected*` and `Specimen.processing[]`. |
| `Observation` | `LabResult` | both | LOINC code in `code.coding[system="http://loinc.org"]`; reference range from result; abnormal flag in `interpretation`. |
| `DiagnosticReport` | aggregate of `LabOrder` + `LabResult[]` | outbound | One report per completed order. |
| `ServiceRequest` | `LabOrder` | inbound | Authorising practitioner referenced by FHIR Practitioner identifier; mapped to internal `lab_users` only via reconciliation. |
| `Encounter` | `Visit` (SNDHS) | both | Only when `SNDHS_ENABLE_VISITS=true`. |
| `Practitioner` | `lab_users` | inbound (read-only) | Never written to from external; reconciliation only. |
| `Organization` | `Lab` | inbound (read-only) | Cross-institution registry references. |
| `Coverage` | `BillingProfile` (insurer adapter) | both | Insurer-only; not exposed to clinical adapters. |

### FHIR Profiles

GULA-specific FHIR profiles (constraints) live alongside the adapter:

- `gula-patient` — requires national identifier
- `gula-observation-lab` — requires LOINC code, requires lab `Organization`
- `gula-diagnostic-report-lab` — requires linked `Specimen` and `Observation` array

Profiles are versioned per adapter manifest revision.

## HL7 v2.x

| Trigger Event | Direction | Mapping target |
|---------------|-----------|----------------|
| ADT^A04 (register patient) | inbound | reconciliation candidate; never auto-create across tenants |
| ORM^O01 (order new) | inbound | `LabOrder` create within target tenant |
| ORU^R01 (result unsolicited) | both | `LabResult` create / outbound report |
| QBP^Q11 (lookup) | inbound | scoped read; honors TI-1 |

LabLink-Core (`services/device_bridge/`) already speaks HL7 v2 to
**instruments**; institutional HL7 v2 is the future Phase-16 surface.

## DHIS2

DHIS2 is a national aggregation target (Phase 20). The interop surface here
is one-way (outbound), de-identified, k-anonymized, with rates aggregated by:

- province
- facility (where contractually permitted)
- demographic bucket

No DHIS2 push contains raw patient identifiers. No DHIS2 push runs from a
clinical-write code path; all aggregation is offline-batch.

## ICD

ICD-10 (current) and ICD-11 (target):

- ICD codes are stored as strings on `lab_orders.icd_codes` (existing).
- Cross-walk tables (ICD-10 ↔ ICD-11) live in the terminology-governance
  module and are versioned.
- Adapters MUST NOT emit a code that is not in the active cross-walk version.

## LOINC

- LOINC is the canonical lab-test vocabulary.
- `lab_results.test_code` accepts LOINC; non-LOINC codes carry an explicit
  `code_system` qualifier and are mapped before any FHIR emission.
- A non-LOINC code that has no mapping fails closed at the adapter (no FHIR
  emission, audit row written, dead-letter for human review).

## SNOMED CT

- SNOMED is used for clinical findings, problem lists, and structured
  reports.
- For Phase 16, SNOMED appears in optional `Observation.interpretation` and
  `Condition` resources only — no SNOMED-driven workflow is enabled in
  production yet.
- The SNOMED licence boundary is observed: GULA does not redistribute SNOMED
  content; mappings ship as references, not embedded SNOMED data.

## Cross-Standard Conflict Policy

Where two standards disagree (e.g., a FHIR profile constraint vs. an HL7 v2
requirement), the policy is:

1. Prefer the standard mandated by the receiving peer's manifest.
2. If both are required, dual-emit (one event per standard) and link the
   emissions in the audit chain.
3. Never silently drop a field to satisfy a peer-side constraint.

## Validation

Every adapter SHOULD ship a validation suite:

- positive examples (passes profile)
- negative examples (fails profile, fails closed correctly)
- terminology drift examples (unmapped code, dead-letter)

Validation is part of stage-6 sandbox approval.
