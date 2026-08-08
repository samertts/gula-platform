# DOMAIN_REGISTRY.md

> **PROGRAM-STABLE-004** — the canonical Domain Registry (Phase 1/6).
> Generated: 2026-08-06T04:28:40+00:00

## Domains

| Code | Name (en) | Name (ar) | Version | Workspace | Modules |
|---|---|---|---|---|---|
| laboratory | GULA Laboratory | مختبر غولا | 1.0.0 | laboratory | 13 |
| pharmacy | GULA Pharmacy | صيدلية غولا | 1.0.0 | pharmacy | 8 |
| radiology | GULA Radiology | أشعة غولا | 1.0.0 | radiology | 8 |
| hospital | GULA Hospital | مستشفى غولا | 1.0.0 | hospital | 1 |
| blood_bank | GULA Blood Bank | بنك الدم | 1.0.0 | blood_bank | 8 |
| public_health | GULA Public Health | الصحة العامة | 1.0.0 | public_health | 7 |
| insurance | GULA Insurance | التأمين الصحي | 1.0.0 | insurance | 16 |
| emergency | GULA Emergency | الطوارئ | 1.0.0 | hospital | 14 |
| research | GULA Research | البحث العلمي | 1.0.0 | research | 25 |
| citizen_portal | GULA Citizen Portal | بوابة المواطن | 1.0.0 | citizen | 21 |
| provider_portal | GULA Provider Portal | بوابة مقدمي الرعاية | 1.0.0 | professional | 3 |

## Workspace Bindings (Phase 6)

| Domain | Workspace |
|---|---|
| laboratory | laboratory |
| pharmacy | pharmacy |
| radiology | radiology |
| hospital | hospital |
| blood_bank | blood_bank |
| public_health | public_health |
| insurance | insurance |
| emergency | hospital |
| research | research |
| citizen_portal | citizen |
| provider_portal | professional |

## Sovereignty

No Domain owns another Domain. No Domain manages another Domain. No Domain reads another Domain's database. Every workspace renders ONLY its own Domain's UI.

## Source Roots

| Domain | Source |
|---|---|
| laboratory | `app/lims` |
| pharmacy | `app/pharmacy` |
| radiology | `app/radiology` |
| hospital | `app/hospital` |
| blood_bank | `app/blood_bank` |
| public_health | `app/public_health` |
| insurance | `app/insurance` |
| emergency | `app/ems`, `app/critical_care` |
| research | `app/research_platform`, `app/biomedical` |
| citizen_portal | `app/citizen_platform` |
| provider_portal | `app/identity/professional_registry` |

## Adding a Future Domain

1. Declare the Domain Blueprint in `app/domain_platform/manifest.py`.
2. Bind it to exactly ONE workspace type (from the identity workspace catalog).
3. Consume ONLY Shared Core services.
4. Expose cross-domain capabilities ONLY as versioned contracts.
5. Register, activate, and certify through `/niam/domains`.
