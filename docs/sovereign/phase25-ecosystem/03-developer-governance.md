# Phase 25-03 — Developer Governance

## Developer Categories

| Category | Capabilities | Onboarding |
|----------|--------------|------------|
| Internal platform engineers | Full platform access (per RBAC) | HR + security onboarding |
| Government partner developers | Their own adapter; sandbox | Government partner onboarding |
| Certified vendor developers | Their own adapter; sandbox | Vendor contract |
| Research developers | Aggregate / DEID adapter sandbox | Research consortium onboarding |
| Patient-app developers | Patient-side OAuth in sandbox | Privacy review |

A developer category never grants access to production data outside the
adapter's manifest.

## Sandbox Discipline

- Synthetic data only.
- Sandbox tenants are explicitly labelled in the UI / API responses.
- Sandbox-to-production promotion is governance-led.

## Code-Side Boundaries

- Internal adapters live in `backend/app/interoperability/`.
- External adapter integrations are **external services**; we expose
  endpoints for them.
- We never run third-party code in our process.

## Governance Surfaces for Developers

- Capability registry (Phase 21) and operation registry (Phase 16) are
  visible to developers building against them.
- Manifest schema is published.
- Audit shapes are documented.

## Developer Documentation Discipline

- Internal documentation in this `docs/sovereign/` tree.
- External-facing developer documentation is governance-reviewed before
  publication.
- Documentation does not leak internal model field names, RBAC role names,
  or audit-chain layout.

## Code-Submission Discipline

For internal contributions:

- All migrations are forward-compatible, idempotent (CLAUDE.md).
- All new endpoints respect tenant isolation.
- All new AI capabilities go through Phase 21.
- All new adapters go through Phase 16 governance.

For partner-supplied integrations (where they ship code that runs at
their end, not ours):

- Their code is their concern.
- Their contract specifies signing, retention, audit access.
- We treat their system as untrusted from a Phase-16-trust-domain
  perspective regardless of how trustworthy the relationship is.

## Developer Audit

Internal developer accounts and their actions on production systems are
audited per the existing operational audit policy. Production-touching
operations are restricted (per CLAUDE.md) and require approval where
applicable.

## Developer Communication Channels

- Internal: existing engineering channels.
- Partner: written communication only on capability changes; verbal only
  for incident response.
- Patient-app developers: support portal + ticketing (governance-led).

## Out of Scope

- Public developer hackathons (decided by program owner)
- Open source platform-wide contribution policy (decided by institution)
