# DOMAIN_VERSIONING.md

> **PROGRAM-STABLE-004** — Domain Versioning (independent releases).
> Generated: 2026-08-06T04:28:40+00:00

## Rules

- Every Domain is versioned **independently** with **SemVer** (`MAJOR.MINOR.PATCH`).
- **Backward compatibility is never broken.**
- A breaking change requires a **MAJOR** version and explicit certification.
- Version history is immutable and auditable.
- Every version is independently certifiable and independently deployable.

## Compatibility Policy

- `MAJOR` unchanged + `MINOR` bump → backward compatible (new features).
- `MAJOR` unchanged + `PATCH` bump → backward compatible (fixes).
- `MAJOR` bump → breaking change, allowed ONLY when certified.

## Current Releases

| Domain | Version |
|---|---|
| laboratory | 1.0.0 |
| pharmacy | 1.0.0 |
| radiology | 1.0.0 |
| hospital | 1.0.0 |
| blood_bank | 1.0.0 |
| public_health | 1.0.0 |
| insurance | 1.0.0 |
| emergency | 1.0.0 |
| research | 1.0.0 |
| citizen_portal | 1.0.0 |
| provider_portal | 1.0.0 |

## Enforcement

`DomainVersionRegistry` rejects any version that is lower than or equal to the current release and any uncertified breaking upgrade. The Phase 7 `backward_compatibility` check validates every Domain release.
