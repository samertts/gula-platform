# Phase 25-02 — Regulated Integration Preparation

## Integration Patterns

| Pattern | Use case | Mechanism |
|---------|----------|-----------|
| FHIR REST | Vendor EHR ↔ GULA | Phase 16 adapter, single-tenant proxy |
| HL7 v2 | Lab info system | Phase 16 adapter |
| Patient-facing FHIR | Citizen app | OAuth2 + scoped FHIR |
| Aggregate read | Research / consortium | Phase 20 anonymised export |
| Operational read | Tooling vendor | Read-only metrics endpoint |
| Webhook outbound | Notification vendors | Outbound signed events |

## Onboarding Process

1. Application received (description, capabilities sought).
2. Risk + privacy review.
3. Contract drafted; data classes, signing, retention, audit access
   covered.
4. Manifest authored; capability list strictly minimum.
5. Sandbox tenant credentials issued.
6. Sandbox demonstration: positive cases, fail-closed, rate limit, audit
   emission.
7. Pilot tenant approval (one tenant) for low-risk integrations; for
   higher-risk, require sandbox + governance sign-off then production.
8. Continuous monitoring + annual recertification.

## Patient-Side OAuth (Patient-Facing Apps)

- Patient authenticates to platform via mobile app.
- Patient grants scoped consent (e.g., "Show my last lab results to App
  X for 30 days").
- App receives a scoped, time-boxed token.
- All app calls audit-chained as if from the patient.
- Revocation endpoint available; revoked token rejected immediately.

This pattern uses the same adapter machinery; the principal is the
patient, not the institution.

## Capability Discovery

A regulator-approved capability list is published; vendors apply against
the list. New capabilities require governance addition (not vendor
self-declaration).

## Documentation Per Vendor

For each onboarded vendor:

- contract reference
- manifest version history
- capability changelog
- audit-emission test results
- recertification dates

## Termination

Termination of an integration:

- access revoked
- adapter status `retired`
- audit retained
- vendor receives final activity report

A terminated vendor does not retain capability through any cached state.

## Limits

- A vendor can hold multiple manifests (multiple integrations) if
  contractually permitted.
- A vendor MUST NOT hold integrations across multiple unrelated tenants
  without each tenant's separate authorisation.

## Out of Scope

- Vendor billing
- Vendor support tooling
- Vendor self-service onboarding (no — onboarding is governance-led)
