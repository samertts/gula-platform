# Phase 16 — National Institutional Interoperability

**Goal:** Establish sovereign-grade interoperability scaffolding so GULA can
exchange data with ministries, insurers, hospitals, statistics platforms,
licensed labs, telcos, and payment gateways **without weakening any existing
security or tenant-isolation invariant.**

This phase is **scaffolding + governance**, not wholesale integration. No
adapter implementation in this phase ships wired into production routing.

## Documents

| File | Subject |
|------|---------|
| [`01-architecture.md`](./01-architecture.md) | Interop architecture: bounded trust domains, modular adapters |
| [`02-adapter-framework.md`](./02-adapter-framework.md) | Adapter interface, lifecycle, manifest |
| [`03-trust-boundaries.md`](./03-trust-boundaries.md) | Institutional trust-boundary model |
| [`04-governance.md`](./04-governance.md) | Interoperability governance + change control |
| [`05-standards-mapping.md`](./05-standards-mapping.md) | FHIR / HL7 / DHIS2 / ICD / LOINC / SNOMED CT mapping detail |
| [`06-risk-analysis.md`](./06-risk-analysis.md) | Phase-16 specific risk analysis |
| [`07-rbac-extensions.md`](./07-rbac-extensions.md) | Institutional RBAC additions |

## Code Scaffolding

`backend/app/interoperability/` — abstract `AdapterBase`, `TrustDomain`
dataclass, `InteropAuditEvent` shape, `failure_isolation.py`. **Not** wired
into `main.py`.

## Sovereign Invariants Honored

- TI-3, TI-4, TI-5 (no cross-tenant identity bleed via adapters)
- AI-3, AI-4 (interop calls always audited)
- PB-1, PB-2 (adapter trust is bounded, not user-inherited)
- All inbound integrations **fail closed**

## Out of Scope (Deferred)

- Live FHIR endpoint registration
- Production wiring of adapters in `main.py`
- Real ministry/insurer credential issuance
- DHIS2 data aggregation jobs (Phase 20)
