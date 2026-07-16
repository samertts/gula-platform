# ADR-012: National Identity Platform Architecture

**Status:** Accepted  
**Date:** 2026-07-16  
**Deciders:** Platform Architecture Team  
**References:** MPI (ADR-005), Security (ADR-003), National Domain (ADR-009)

## Context

GULA requires a unified national identity platform serving 40M+ Iraqi citizens,
foreign residents, and temporary visitors. The codebase had three independent
identity implementations (MPI, National Domain, Governance) with conflicting
models, health-number formats, and merge engines — risking data integrity.

## Decision Drivers

- **Single source of truth** — one canonical citizen record per person
- **Offline-first** — edge clinics must register and authenticate without connectivity
- **FHIR R4 compliant** — identity resources must map cleanly to Patient/Practitioner/RelatedPerson
- **Zero-trust** — all identity operations require attestation and audit
- **Clinical safety** — identity merges require human review at thresholds <0.90

## Decision

Adopt a **layered identity architecture** with three tiers:

### Tier 1: Core Patient Identity (existing — stable)

- `Patient` model (`models/patient.py`) — per-lab patient records with `health_id`,
  `national_id_hash`, `family_id_hash`, `guardian_id`
- Used by lab workflows (order entry, results reporting)
- Resolved to canonical citizen via MPI on create

### Tier 2: Master Patient Index (existing — enhanced)

- `Citizen` model (`services/mpi/models.py`) — canonical national identity
- `IdentityClaim` — bridges lab patients to canonical citizens
- `MergeAudit` — hash-chained merge ledger
- Fellegi-Sunter probabilistic matcher (0.90 auto-claim, 0.70-0.90 review)

### Tier 3: National Identity Registry (newly wired)

- `national_citizens` table — comprehensive citizen registry with health numbers
- `HealthNumberSequence` — collision-proof sequential health numbers
- Identity types: citizen, newborn, foreigner, visitor, unknown (emergency)
- `HealthCard` — physical/digital health cards with QR and PIN
- `Family`/`FamilyMember` — household relationships and guardian linking

### Unification Strategy

1. **All new registrations** flow through `CitizenService` → writes `national_citizens`
2. **HealthNumberSequence** is the sole health-number authority (`IQ{year}{seq:06d}`)
3. **MergeAudit** (Tier 2) is the canonical merge ledger; Tier 3 merge events
   emit to the same audit trail
4. **IdentityGovernanceService** will be converted from in-memory to DB-backed
   using `national_citizens` + `national_merge_audit`

### Authentication

- **Primary:** JWT (HS256) with Redis blacklist + perm_version invalidation
- **Password:** bcrypt with timing-safe dummy hash
- **Rate limiting:** 10/min auth, 30/min public, 60/min user, 20/min admin
- **Brute-force:** Dynamic IP blocking at 5x threshold
- **Missing** (deferred to PI-003): Passkeys/WebAuthn, TOTP, OAuth2/OIDC, SAML

### Authorization

- **RBAC:** 9+ roles × 13+ permissions (backend) + 23 roles × 30+ permissions (national)
- **ABAC:** Attribute engine with subject/resource/environment rules
- **Consent:** 4-tier access policy with break-glass override
- **Purpose-of-use:** 10 purposes with minimum-necessary data filtering
- **VIP/Minor/Foreigner protection:** Purpose-specific access rules

## Consequences

### Positive
- Single health-number format eliminates collision risk
- All identity types flow through consistent registration pipeline
- Full API surface for citizen, family, health-card operations
- Every identity operation has audit trail (MPI MergeAudit + national events)

### Negative
- Tier 2 and Tier 3 citizen tables are NOT yet unified — dual-write risk
- Three merge engines still exist (MPI, Governance, National) — must consolidate
- IdentityGovernanceService (470 lines) remains in-memory — data loss on restart
- No offline identity cache or sync mechanism

### Neutral
- Migration from per-lab to national identity is incremental (lab by lab)
- Backward compatibility with existing Patient model maintained

## Implementation Plan

1. Fix SQLAlchemy `not column` negation bugs (DONE — 369 fixes across 31 files)
2. Wire national API routes (DONE — citizen, identity, family, health-card)
3. Persist governance services to DB (NEXT)
4. Unify Tier 2 MPI Citizen ↔ Tier 3 national_citizens (PI-002)
5. Add MFA/TOTP/WebAuthn (PI-003)
