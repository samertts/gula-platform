# GULA Healthcare Idea Backlog

**Discovery phase · 2026-09-10 · none of this is a commitment to build.**

Ideas are placed where the repository already has a home for them, so each one names a real
destination rather than a wish. Most are blocked on the same thing.

## P0

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| Closed-loop abnormal result follow-up | `clinical + lims` | A critical result that nobody acknowledges is the classic avoidable-harm pattern; GULA already has critical_alerts and an outbox to build it on | EHR/encounter |
| Longitudinal patient timeline | `ehr` | ehr_patient_timeline is already modelled and has no table; it is the spine every other clinical feature hangs off | National core |

## P1

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| Medication reconciliation across encounters | `pharmacy + ehr` | GULA owns dispensing end-to-end; reconciliation is the missing half and needs only the EHR side | EHR |
| Closed-loop referral tracking | `clinical + national` | national_referrals is mapped and absent; referral leakage is a measurable national problem | National core |
| Antimicrobial stewardship | `pharmacy + lims` | GULA uniquely holds both prescribing and culture results in one platform — few systems do | EHR |
| Blood utilisation intelligence | `blood_bank + nhdw` | Wastage and over-ordering are measurable from data GULA already has | NR-021 fix |
| National facility capacity and referral optimisation | `national` | Needs the facility directory settled first | NR-006 |
| Maternal risk stratification | `care_continuum` | cc_antenatal_care_visits is modelled; 45/45 care_continuum tables blocked on national core | National core |
| Outbreak detection from laboratory signal | `public_health + lims` | GULA sees lab results before notifications reach a ministry — a genuine national advantage | National core |

## P2

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| Care gaps / screening due lists | `care_continuum` | Standard population health; needs longitudinal record | — |
| Chronic disease programme registries | `chronic_care` | cc_chronic_disease_registry modelled, absent | National core |
| Pediatric growth monitoring | `care_continuum` | Well-defined algorithms, low ambiguity | — |
| Laboratory quality control analytics | `lims` | GULA has quality_control routes already; Westgard-style rules are deterministic | — |

## P3

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| Remote monitoring / wearables | `devices` | WearableMeasurement model exists; low national priority now | — |
| Oncology pathways | `clinical` | High complexity, needs terminology and EHR first | Terminology + EHR |
| Mental health and rehabilitation pathways | `clinical` | Underserved but dependent on the same core | — |
| Clinical trials / research infrastructure | `research_platform` | research_platform exists with 49 ops and 7/7 tables missing | — |

## RESEARCH

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| National digital twin | `simulation` | simulation package exists (5 tables, none physical); demo generator already produces a twin dataset | — |
| AI-assisted clinical documentation | `ai_fabric` | Must remain assistive; a note is a human authority artefact | — |

## EXPERIMENTAL

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| AI population-health prediction | `ai_fabric` | Only after deterministic indicators exist and can validate it | — |

## REJECTED

| Idea | Belongs in | Why | Blocked on |
|---|---|---|---|
| Replacing GULA's LIMS or pharmacy with OSS | `—` | Both are further along than the surveyed alternatives; replacement would lose verified work | — |
| Adopting an external FHIR server as the clinical datastore | `—` | Would create a second source of truth for patient and clinical records, which the architecture forbids | — |

## The pattern

Nearly every P0 and P1 idea is blocked on the national core or the EHR record that sits on
it. That is the same conclusion BATCH-2 reached from foreign keys, arrived at here from
clinical value instead. Two independent routes to one answer: **build the national core
first, and very little else is worth starting before it.**

