# GULA World Benchmark Policy

## Continuous Benchmarking

GULA continuously benchmarks itself against the world's best healthcare platforms. This is not imitation — it is learning. The purpose is to identify gaps, validate architecture decisions, and adopt proven ideas that fit GULA's architecture and mission.

## Reference Platforms

The following platforms are continuously studied and benchmarked:

| Platform | Focus | Key Learnings |
|----------|-------|---------------|
| **NHS England** | National architecture, FHIR adoption, citizen services | API strategy, national identity, population health |
| **Estonia e-Health** | Digital-first, blockchain audit, citizen-owned data | KSI blockchain, data sovereignty, X-road integration |
| **Finland Kanta** | National archive, citizen portal, pharmacy integration | National data lake, consent management, prescription exchange |
| **Singapore NEHR** | National EHR, immunization registry, COVID response | National patient index, outbreak management, lab integration |
| **Australia My Health Record** | Citizen-controlled health records, clinical document sharing | Consent models, document exchange, national identifier |
| **Epic** | Enterprise EHR, interoperability, patient portal | Cosmos research, App Orchard, clinical workflows, MyChart |
| **Oracle Health (Cerner)** | Enterprise EHR, population health, HealtheIntent | Population health analytics, unified clinical data |
| **MEDITECH** | Community hospitals, integrated care | Expanse platform, clinical mobility, workflow design |
| **InterSystems TrakCare** | Unified healthcare information system | TrakCare Lab, interoperability, unified patient record |
| **OpenHIE** | Health information exchange architecture | IOL, CR, SHR, HWR modular architecture |
| **DHIS2** | Public health surveillance, LMIS | Aggregate analytics, tracker, metadata model, Android SDK |
| **OpenELIS** | Laboratory information system | Global lab workflows, reference ranges, QC, instrument integration |
| **OpenMRS** | Patient-centric EHR, modular design | Module system, concept dictionary, form engine, cohort builder |
| **OpenEMR** | Practice management, billing | ONC certification, telehealth, patient portal |
| **Bahmni** | Hospital system for low-resource settings | IPD/OPD workflows, pharmacy, radiology integration |
| **GNU Health** | Social medicine, primary care | Family medicine, social determinants, epidemiology |
| **WHO Digital Health** | Global guidance, interoperability | SMART guidelines, digital adaptation kits |
| **HL7 FHIR** | Healthcare interoperability standard | RESTful healthcare APIs, resource model, FHIR R5 |
| **IHE** | Integration profiles | XDS, XDS-I, PIX, PDQ, ATNA, BPPC |
| **OpenEHR** | Clinical modeling, archetypes | Composition model, archetype methodology |

## Review Cycle

1. **Quarterly review** of all reference platforms for new capabilities and direction changes.

2. **Feature-specific deep dives** when a capability gap is identified in GULA.

3. **Pre-release review** before major releases to ensure no critical gap exists.

## Gap Analysis

4. Every identified capability is classified:
   - **Already exists in GULA** — validate implementation quality, improve if needed
   - **Partially implemented** — complete the implementation
   - **Missing but needed** — design and implement
   - **Missing and not needed** — document rationale
   - **Not suitable for GULA** — document architectural justification

5. Gap analysis is published in `docs/reference/world_benchmark/GAP_ANALYSIS.md`.

## Adoption Rules

6. **Never clone.** Extract the underlying idea, problem, and value. Design a GULA-native solution.

7. **Justify every adoption.** Why does GULA need this? Who benefits? What is the cost?

8. **Document every rejection.** If a leading platform has a capability that GULA does not, explain why.

## Continuous Update

9. The reference platform library in `docs/reference/world_benchmark/` is updated quarterly.

10. Architecture decisions referencing reference platforms link to the relevant analysis.
