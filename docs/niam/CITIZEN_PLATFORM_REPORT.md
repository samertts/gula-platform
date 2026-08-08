# GULA Citizen Platform — Report

> Generated: 2026-08-05T22:30:00+00:00
> Program: PROGRAM-STABLE-003
> Module: `backend/app/identity/citizen_registry/`

---

## Verdict

**CERTIFIED — COUNTRY-AGNOSTIC CITIZEN REGISTRY**

## Mandate

"The citizen registry must be country-agnostic with configurable identifiers.
Never hard-code country rules."

## Design

The registry is driven by configurable **Identity Providers**. Each provider
declares which identifier types it accepts, its verification methods, and its
country. No country-specific logic exists in code.

| Provider field | Meaning |
|---|---|
| `provider_id` | Stable provider key (e.g. `IRQ-NID`) |
| `provider_type` | government, national_health, civil_registry, … |
| `country` | ISO-3166-1 alpha-3 (e.g. `IRQ`) |
| `identifier_types` | Accepted identifiers (JSON list) |
| `verification_methods` | e.g. authority_confirmation, biometric, … |
| `configuration` | Provider-specific extension config (JSON) |

## Configurable Identifier Types

national_id, civil_id, national_health_id, social_security_number, resident_id,
passport, tax_number, custom.

## Verified Behaviors (Tests)

| Scenario | Result |
|---|---|
| Register a provider with valid identifier types | ✅ |
| Reject unknown identifier type at registration | ✅ |
| Verify a citizen identifier against an active provider | ✅ |
| Reject a disabled/maintenance provider | ✅ |
| Reject identifier type the provider does not accept | ✅ |
| Reject completely unknown identifier type | ✅ |
| Reject unknown provider | ✅ |
| Resolve the default provider | ✅ |
| Identifier hashing deterministic + collision-free | ✅ |

## Security

Identifiers are stored **hashed** (SHA-256) in `niam_citizen_identity_verifications`
(`identifier_hash`), with an optional masked display value. Raw identifiers are
never persisted.

## API Surface (4 endpoints)

`/niam/citizens/providers` (POST/GET), `/niam/citizens/providers/default`,
`/niam/citizens/verify-identifier`.

## Verified Facts

- **Tests:** 10 citizen-registry tests pass.
- **Database:** `niam_identity_providers` + `niam_citizen_identity_verifications` created in `20260805_0002`.
- **Lint:** ruff clean.

## Open Items

- Actual outbound verification connectors (civil registry APIs) per provider.
- Seed a default provider for the primary deployment country in bootstrap.
