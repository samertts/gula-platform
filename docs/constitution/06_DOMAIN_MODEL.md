# GULA Domain Model

## Core Domains

GULA's domain model is organized into bounded contexts that reflect real-world healthcare organization:

| Domain | Owner | Description |
|--------|-------|-------------|
| **Identity** | IAM | Users, patients, citizens, roles, permissions, authentication, authorization |
| **Patient** | Clinical | Patient demographics, medical history, family history, consent, preferences |
| **Laboratory** | Lab | Orders, specimens, results, quality control, instruments, reference ranges |
| **Clinical** | Clinical | Encounters, diagnoses, medications, procedures, care plans, clinical notes |
| **Orders** | Lab/Clinical | Lab orders, clinical orders, prescription orders, referral orders |
| **Results** | Lab/Clinical | Lab results, imaging results, pathology results, vital signs |
| **Pharmacy** | Pharmacy | Formulary, prescriptions, dispensing, inventory, drug interactions |
| **Radiology** | Radiology | Imaging studies, DICOM management, reporting, AI analysis |
| **Blood Bank** | Blood Bank | Donor management, collection, testing, inventory, transfusion |
| **Nursing** | Nursing | Care plans, medication administration, vitals, assessments, handover |
| **Emergency** | Emergency | Triage, EMS tracking, disaster response, bed management |
| **Public Health** | Public Health | Surveillance, outbreaks, reporting, epidemiology, immunization |
| **Analytics** | Cross-cutting | Dashboards, reports, trends, predictive models, BI |
| **Financial** | Admin | Billing, insurance claims, pricing, subscription management |
| **Compliance** | Legal | Regulatory compliance, audit, licensing, accreditation |
| **Integration** | Cross-cutting | FHIR APIs, IHE profiles, HL7 v2, device connectivity |
| **AI** | Cross-cutting | Clinical decision support, predictive analytics, NLP, computer vision |

## Domain Boundaries

1. **No circular references between domains.** Domain A may depend on Domain B's published API, but Domain B must never depend on Domain A's internals.

2. **Cross-domain communication uses events or published APIs.** Direct database access across domain boundaries is forbidden.

3. **Each domain owns its data.** If Domain A needs data from Domain B, it requests it through Domain B's API or subscribes to Domain B's events.

4. **Domain models may overlap in views but not in authoritative storage.** A Patient Order view may display lab results, but the result data is owned by the Results domain.
