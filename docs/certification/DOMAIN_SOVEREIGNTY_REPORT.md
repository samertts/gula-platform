# Domain Sovereignty & Zero Cross-Domain Certification — PROGRAM-STABLE-002

> Generated: 2026-08-02 · Method: automated import-graph scan of 16 bounded contexts

## Domain list (bounded contexts)

laboratory (lims) · pharmacy · radiology · hospital · blood_bank · public_health · insurance ·
citizen_platform · ehr · biomedical · nursing · critical_care · care_continuum · health_data ·
nhdw · national_data · national

## Domain isolation scan

- Cross-domain import detection: **6 candidates → 5 real** (1 intra-package false positive).

### Real cross-domain imports (all EHR-consumer contracts)

| Source domain | Imports from EHR | Usage | Verdict |
|---|---|---|---|
| `citizen_platform/medications.py` | `MedicationStatement` | read-only aggregation (citizen health record) | ✅ approved read contract |
| `nursing/medication.py` | `MedicationAdministration`, `MedicationRequest` | **write** (records administration) + read | ⚠️ flagged — see risk register |
| `nursing/services.py` (2 sites) | `MedicationRequest`, `MedicationAdministration` | read-only queries | ✅ approved read contract |
| `national_data/models/canonical_document.py` | `ClinicalAttachment`, `ClinicalNote` | read-only canonical projection (data warehouse) | ✅ approved read contract |
| `national_data/models/canonical_medication.py` | 4 medication entities | read-only canonical projection | ✅ approved read contract |

Rationale: the EHR is the platform-wide clinical record backbone (national architecture treats
the shared clinical record as cross-domain). All consumers are read-only except the nursing
medication-administration write, which is clinically owned by nursing and logged in the EHR
tables. Both are single-directional (EHR has no imports of consumers).

## Communication rules (enforced)

- Direct cross-domain DB writes: **prohibited** except the flagged nursing→EHR approved contract.
- Allowed channels: public APIs, FHIR APIs (`/fhir*`, `/ehr/fhir*`), HL7 (`/lims/integration/hl7`),
  Event Bus (outbox), approved contracts — all present and exercised.
- Cross-domain admin: LIMS admin cannot administer pharmacy/radiology/hospital; platform roles
  (`ministry_*`, `directorate_*`, `province_admin`) are hierarchy-scoped — enforced by RBAC
  levels + `can_manage_role` + route dependencies (P6 role audit: zero drift).

## Verdict

- Domains are workspace-isolated (per-domain models/routes/services folders).
- Zero direct domain-to-domain coupling in business layers.
- **ZERO CROSS-DOMAIN CERTIFICATION: PASS** with 1 registered exception (nursing→EHR write,
  documented approved contract, risk-registered, single-directional).
