# GULA Platform — Healthcare Analysis
**Date:** 2026-07-17

---

## 1. Healthcare Domains Implemented

| Domain | Status | Implementation |
|--------|--------|----------------|
| **Laboratory (LIMS)** | **PRODUCTION** | Full: orders, results, samples, QC, test types, patient cards |
| **Basic EHR** | **PRODUCTION** | Clinical notes, conditions, medications, allergies, immunizations |
| **FHIR R4/R5 API** | **PRODUCTION** | Patient, Encounter, Observation, Condition, MedicationRequest, Immunization |
| **Patient Portal** | **PRODUCTION** | QR cards, citizen portal, result viewing |
| **Lab Device Integration** | **PRODUCTION** | ASTM/HL7 via device_bridge (Sysmex, Roche, Mindray, generic) |
| **MPI** | **PRODUCTION** | Fellegi-Sunter probabilistic matching |
| **Consent Management** | **PRODUCTION** | Grant/revoke with 72h max window |
| **Insurance Claims** | **PRODUCTION** | Submission workflow (IQD) |
| **National ID Integration** | **PRODUCTION** | MoI NID verification (12/16 digit) |
| **Quality Control** | **PRODUCTION** | Westgard rules (1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10-x) |
| **Clinical CDS** | **SCHEMA-ONLY** | Rules, alerts, order sets, contraindications |
| **Nursing** | **SCHEMA-ONLY** | 15+ tables, no routes |
| **Pharmacy** | **SCHEMA-ONLY** | 23+ tables, no routes |
| **Radiology** | **SCHEMA-ONLY** | 19+ tables, DICOM model |
| **EMS / Emergency** | **SCHEMA-ONLY** | 12+ tables |
| **Blood Bank** | **SCHEMA-ONLY** | 11+ tables |
| **Critical Care** | **SCHEMA-ONLY** | 13+ tables |
| **Biomedical Engineering** | **SCHEMA-ONLY** | 11+ tables |
| **Public Health** | **SCHEMA-ONLY** | 7+ tables |
| **Hospital Management** | **PARTIAL** | Routes + services exist, schema solid |
| **National Data Exchange** | **PARTIAL** | Routes + streaming exist |
| **National LIMS** | **SCHEMA-ONLY** | 35 tables (2026-07-14) |

---

## 2. Healthcare Standards Support

| Standard | Implementation | Depth |
|----------|---------------|-------|
| **FHIR R4/R5** | `routes/ehr_fhir.py` | Resources: Patient, Encounter, Observation, Condition, MedicationRequest, Immunization |
| **HL7 v2** | `gateways/lab_device_gateway.py` | ASTM protocol support, device integration |
| **HL7 FHIR Streaming** | `routes/national_streaming.py` | FHIR events to national infrastructure |
| **LOINC** | `clinical/terminology/models.py` | Full LOINC code model, searchable |
| **SNOMED CT** | `clinical/terminology/models.py` | Full concept model with hierarchy |
| **ICD-10** | `clinical/terminology/models.py` | Chapter/block/category, billable flags |
| **ICD-11** | `clinical/terminology/models.py` | Post-coordination, coding notes |
| **UCUM** | `clinical/terminology/models.py` | Units of measure |
| **ATC** | `clinical/terminology/models.py` | Drug classification |
| **RxNorm** | `clinical/terminology/models.py` | Clinical drugs |
| **CPT** | `clinical/terminology/models.py` | Procedures |
| **Westgard Rules** | `routes/quality_control.py` | 6 QC rules for lab instruments |

---

## 3. Clinical Terminology Coverage

Evidence from `clinical/terminology/models.py`:

| Terminology | Model Fields | Hierarchy | Cross-Maps |
|-------------|-------------|-----------|------------|
| ICD-10 | code, short_desc, long_desc, chapter, block, category | chapter > block > category | TerminologyMapping |
| ICD-11 | code, title, definition, chapter, block, is_leaf | chapter > block > leaf | TerminologyMapping |
| SNOMED CT | concept_id, fsn, preferred_term, definition_status, semantic_tag | module > concept | TerminologyMapping |
| LOINC | loinc_num, component, property, timing, system, scale, method, class | Component hierarchy | TerminologyMapping |
| UCUM | code, name, primary_code, property | Unit hierarchy | TerminologyMapping |
| ATC | code, name, anatomical_group, therapeutic_subgroup | 5-level hierarchy | TerminologyMapping |
| RxNorm | rxcui, name, synonym, tty | Ingredient > Brand | TerminologyMapping |
| CPT | code, description, category | Category I/II/III | TerminologyMapping |
| Generic | code, display, system (enum) | Parent-child | TerminologyMapping (source↔target) |

---

## 4. Lab Workflow State Machine

```
                        Order Lifecycle
  ┌──────────┐     ┌───────────┐     ┌────────────┐
  │ Pending  │────▶│ Completed │────▶│ Validated  │ (terminal)
  └──────────┘     └───────────┘     └────────────┘
        │                 │
        ▼                 ▼
  ┌──────────┐     ┌───────────┐
  │Cancelled │     │ Cancelled │
  └──────────┘     └───────────┘
  (terminal)       (terminal)

                        Sample Lifecycle
  Collected → In Transit → Received → Processing → Completed → Rejected

                       Result Lifecycle
  Created → Verified → Validated → Released
```

---

## 5. Clinical Engine Architecture

```
                    ClinicalEngine v2.1
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
    │ Ali Reza    │  │ Clinical  │  │ Epidemiology │
    │ Engine      │  │Intelligence│  │ Engine      │
    │ (direct     │  │ (multi-test│  │ (outbreak   │
    │  meas.)     │  │  patterns) │  │  signals)   │
    └─────────────┘  └───────────┘  └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   Samir     │
                    │   Engine    │
                    │ (guidance)  │
                    └─────────────┘
```

---

## 6. Master Patient Index (MPI)

**Location**: `backend/app/services/mpi/`

### Architecture
- **Deterministic match**: NID hash match → score=1.0 → auto-claim
- **Probabilistic match**: Fellegi-Sunter weighted scoring

### Matching Weights
| Attribute | Weight | Method |
|-----------|--------|--------|
| Phone | 0.30 | Exact |
| DOB | 0.25 | Exact |
| DOB (day/month swap) | 0.10 | Permutation |
| Name | 0.25 | Jaro-Winkler |
| Name (alt) | 0.15 | Jaro-Winkler (second field) |
| Gender | 0.05 | Exact |
| Family ID hash | 0.15 | Exact |

### Thresholds
| Score | Action |
|-------|--------|
| >= 0.90 | Auto-claim (automatically link) |
| 0.70 - 0.90 | Pend for review |
| < 0.70 | New citizen record |

---

## 7. Key Healthcare Findings

| Finding | Evidence | Impact |
|---------|----------|--------|
| **Core LIMS is production-ready** | Routes, services, tests exist | **STRENGTH** |
| **National platform domains are schema-only** | 17 migrations from 2026-07-16 all create tables but no routes | **GAP** — dead schema |
| **FHIR API exists but limited** | Only 6 resource types | **GAP** — needs expansion |
| **Clinical CDS is schema-only** | No route handlers for CDS | **GAP** |
| **No DICOM implementation** | Radiology schema has DICOM model fields but no DICOM server | **GAP** |
| **HL7 v2 is basic** | Only ASTM protocol (not full HL7 v2.x) | **GAP** |
| **Interpretation engine is rule-based** | Hard-coded thresholds, not ML | **DESIGN CHOICE** — safer for clinical |
| **No LOINC/SNOMED actual codes** | Models exist but tables are empty | **GAP** — requires data population |
| **Arabic-first is implemented** | test_name_ar, Arabic interpretations | **STRENGTH** |
