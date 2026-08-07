# MASTER_ARCHITECTURE_v2 — GULA National Healthcare Platform

> PROGRAM-ALPHA | regenerated 2026-08-08 by `scripts/architecture/docs.py`
> Platform verdict: **PASS** — Domains **11/11**,
> isolation **PASS**.

## 1. Mission

Transform GULA into a sovereign national healthcare platform built on
**Shared Core**, **Domain Sovereignty**, **Workspace Architecture**, a
**Unified Digital Trust Platform**, **Zero Business Logic Duplication**,
**Zero Cross-Domain Administration**, **Country-Agnostic Design** and
**Backward Compatibility**. Nothing here reduces existing functionality,
breaks tests, weakens security, or duplicates infrastructure.

## 2. Layer model

```
┌─────────────────────────────────────────────────────────────┐
│  UI layer  —  citizen / laboratory / pharmacy / radiology /  │
│              hospital / blood_bank / provider / research /   │
│              insurance / public_health / government          │
│              (rendered ONLY inside the bound workspace)      │
├─────────────────────────────────────────────────────────────┤
│  Domain layer — 11 sovereign Domains                         │
│  each owns ONLY: entities, services, policies, validation,   │
│  reports, events, workflows, UI, public APIs                 │
│  communication ONLY via public REST/FHIR R4/HL7, versioned   │
│  contracts, and the Event Bus                                │
├─────────────────────────────────────────────────────────────┤
│  Shared Core — 50 authoritative services,     │
│  each existing EXACTLY once (see SHARED_CORE_REGISTRY.md)     │
├─────────────────────────────────────────────────────────────┤
│  Digital Trust — NIAM identity (citizen, professional, org,  │
│  service account, device), MFA, sessions, delegation, audit  │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure — storage, messaging, observability, cache,  │
│  scheduler, feature flags, backups (shared/ only)            │
└─────────────────────────────────────────────────────────────┘
```

## 3. Architecture invariants

1. Every reusable capability exists exactly once (Shared Core).
2. Every Domain is sovereign — it never reaches another Domain's tables,
   services, or permission store.
3. One identity, unlimited workspaces, ONE active workspace per identity;
   permissions never cross workspaces.
4. Cross-domain communication only via public APIs, FHIR R4, HL7, versioned
   contracts, or the Event Bus.
5. Country-specific behaviour lives only in the national layer; Domains stay
   country-agnostic.
6. Every architectural decision preserves backward compatibility (SemVer
   MAJOR = breaking, gated).

## 4. Bounded contexts (Domains)

| `laboratory` | GULA Laboratory | مختبر غولا | `laboratory` | lab_service, sample_service, test_result_service, quality_control_service | 0 |
| `pharmacy` | GULA Pharmacy | صيدلية غولا | `pharmacy` | pharmacy_service, inventory_service, dispensing_service | 0 |
| `radiology` | GULA Radiology | أشعة غولا | `radiology` | radiology_service, pacs_service, ai_assisted_read | 0 |
| `hospital` | GULA Hospital | مستشفى غولا | `hospital` | hospital_service, encounter_service, care_continuum_service | 0 |
| `blood_bank` | GULA Blood Bank | بنك الدم | `blood_bank` | blood_bank_service, compatibility_service | 0 |
| `public_health` | GULA Public Health | الصحة العامة | `public_health` | surveillance_service, immunization_service | 0 |
| `insurance` | GULA Insurance | التأمين الصحي | `insurance` | insurance_service, claims_service, fraud_service | 0 |
| `emergency` | GULA Emergency | الطوارئ | `hospital` | ems_service, critical_care_service | 0 |
| `research` | GULA Research | البحث العلمي | `research` | research_service, biomedical_service, data_science_service | 0 |
| `citizen_portal` | GULA Citizen Portal | بوابة المواطن | `citizen` | citizen_platform_service | 0 |
| `provider_portal` | GULA Provider Portal | بوابة مقدمي الرعاية | `professional` | provider_portal_service | 0 |

## 5. Certification

| Certificate | Result |
|---|---|
| Domain certification (9 checks / Domain) | **11/11** |
| Isolation (imports, cycles, shared state, permissions, DB, tables) | **PASS** |
| Shared Core reimplementation scan | **27 findings, 27 acknowledged** |
| Cross-domain administration | **0** |
| Country-agnostic | **PASS** |
| Architecture Constitution gate | **PASS** |

## 6. Governance

The Architecture Constitution (`ARCHITECTURE_CONSTITUTION.md`) is enforced by
`scripts/architecture/` and gated in CI. PRs that duplicate infrastructure,
break Shared Core, break Domain Sovereignty, break Workspace isolation, or
break Country-Agnostic design **automatically fail**.

## 7. Companion documents

| Document | Content |
|---|---|
| `SHARED_CORE_REGISTRY.md` | authoritative 50-service registry |
| `DOMAIN_SOVEREIGNTY.md` | the 11 Domains and their blueprints |
| `DOMAIN_DEPENDENCY_GRAPH.md` | dependency, contract and event topology |
| `WORKSPACE_ARCHITECTURE.md` | one identity, unlimited workspaces |
| `DIGITAL_TRUST_PLATFORM.md` | NIAM Digital Trust capabilities |
| `ARCHITECTURE_CONSTITUTION.md` | the permanent architecture gates |
| `ARCHITECTURE_CERTIFICATION.md` | Phase 9 certification verdict |
| `MASTER_REMAINING_WORK.md` | acknowledged debt + migration plan |

_Generated by scripts/architecture/docs.py._
