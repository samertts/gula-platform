# Phase 25-01 — Sovereign Ecosystem Governance Framework

## Position

The ecosystem is **the set of third-party systems and integrations** that
extend the platform without being part of it. Examples: a startup's
patient-engagement app, a research consortium's analytics workbench, an
insurer's portal, a sovereign-cloud monitoring tool.

The ecosystem is **regulated, not open**.

## Architectural Stance

- All third parties are **external systems** that interact via the same
  Phase 16 adapter pattern.
- No in-process plugin loader exists or will be built without an explicit
  full sandbox-design phase.
- "Marketplace" / "innovation hub" / "developer portal" are organisational
  artefacts — they do not relax the technical boundaries.

## Categories of Ecosystem Actor

| Category | Examples | Trust posture |
|----------|----------|---------------|
| Government partners | Ministry, NHIS, statistics | Phase 16 institutional adapters |
| Certified vendors | EHR vendors, lab info systems | Phase 16 single-tenant proxy adapters |
| Sandbox / pilot startups | New innovation | Sandbox tenant; no production data |
| Research consortia | Universities, NIH-equivalent | Aggregate / DEID adapters (Phase 20) |
| Patient-facing apps | Consumer apps | Patient-side OAuth + scoped FHIR access |
| Tooling vendors | Monitoring, audit support | Read-only operational access |

## Lifecycle

```
[applies] -> [governance review] -> [contract] -> [manifest authoring]
   -> [sandbox onboarding] -> [pilot tenant] -> [pilot evaluation]
   -> [production approval] -> [active]
   -> [continuous monitoring] -> [annual recertification]
   -> [retirement]
```

Each stage is signed by an authority body.

## Authority Bodies (recap)

- Government partners → IRB-Interop + ministry liaison
- Certified vendors → IRB-Interop
- Sandbox startups → sandbox governance committee
- Research consortia → IRB-AI (where AI involved) + privacy officer
- Patient-facing apps → privacy officer + clinical safety
- Tooling vendors → security officer

## Capabilities Available to Third Parties

The platform exposes a **scoped subset** of capabilities through adapters:

- FHIR read on patient-summary (patient-facing apps with consent)
- FHIR write on referred orders (certified EHR vendors)
- Aggregated read (research consortia, anonymised)
- Patient-card scan (patient-engagement apps with patient-token)
- Operational metrics (tooling vendors, read-only)

A capability not on this list is not exposed without a governance review.

## Capability-Scoping Discipline

- Third-party manifests are **strictly less permissive** than government
  manifests.
- Capability changes require new governance review.
- Quarterly review for capability creep.

## Auditability

- Every third-party call is `InteropAuditEvent` (Phase 16).
- Third parties receive their own activity logs (read-only).
- Patient-facing apps receive logs scoped to the patient who authenticated.

## Sandbox Posture

- Sandbox tenant runs the same code as production.
- Sandbox data is synthetic; no real patient data.
- Sandbox third parties cannot reach production tenants.
- Sandbox failures do not affect production.

Sandbox-to-production promotion is a governance event, not a
configuration toggle.

## Out of Scope

- Marketplace billing (institution decides, not the platform)
- Public API documentation portal (institution decides)
- Free tier (decided per deployment; default: no free tier in production)
