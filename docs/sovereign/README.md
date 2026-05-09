# GULA Sovereign National Healthcare Infrastructure Program

**Status:** Documentation & Architectural Scaffolding (non-breaking)
**Audience:** Ministries, regulators, lab/hospital institutional integrators, platform operators, internal architects
**Scope:** Phases 16–25 of the Sovereign National Healthcare Infrastructure Transformation
**Compatibility guarantee:** Zero breaking API changes. All artifacts in this tree are
documentation, governance scaffolding, or non-wired Python interface stubs. None
of them register routes, modify schemas, or alter runtime behavior.

---

## Why This Exists

GULA has completed production-hardening phases 1–15 (tenant isolation, observability,
chaos validation, audit integrity, AI guardrails, migration resilience, clinical
safety, operational survivability). Those phases delivered a *production-grade*
medical-laboratory SaaS.

This program (phases 16–25) is the **strategic maturation layer** that prepares
the same platform — without rewriting it — for sovereign national operation
across ministries, insurers, hospitals, provincial directorates, regulated
private labs, telecommunications providers, and electronic payment gateways.

It is explicitly **not**:

- a feature-expansion initiative
- a UI redesign
- a startup-scaling phase
- a rapid-growth experiment

It is a controlled architectural-readiness, governance-readiness, and
survivability-readiness phase.

---

## Phase Index

| Phase | Title | Folder |
|------:|-------|--------|
| 16 | National Institutional Interoperability | [`phase16-interoperability/`](./phase16-interoperability/) |
| 17 | National Operational Infrastructure | [`phase17-operational-infrastructure/`](./phase17-operational-infrastructure/) |
| 18 | National Regulatory & Governance Readiness | [`phase18-regulatory-governance/`](./phase18-regulatory-governance/) |
| 19 | Sovereign National Health Data Fabric | [`phase19-health-data-fabric/`](./phase19-health-data-fabric/) |
| 20 | National Epidemiology & Health Intelligence Grid | [`phase20-epidemiology-grid/`](./phase20-epidemiology-grid/) |
| 21 | National Clinical AI Governance | [`phase21-clinical-ai-governance/`](./phase21-clinical-ai-governance/) |
| 22 | National Health Economics & Insurance Intelligence | [`phase22-health-economics/`](./phase22-health-economics/) |
| 23 | National Crisis & Continuity Survivability | [`phase23-crisis-continuity/`](./phase23-crisis-continuity/) |
| 24 | National Digital Health Legal & Governance Ecosystem | [`phase24-legal-governance/`](./phase24-legal-governance/) |
| 25 | National Health Platform Ecosystem | [`phase25-ecosystem/`](./phase25-ecosystem/) |

## Cross-Phase Artifacts

| Document | Purpose |
|----------|---------|
| [`SOVEREIGN_INVARIANTS.md`](./SOVEREIGN_INVARIANTS.md) | Non-negotiable invariants preserved across all phases |
| [`STANDARDS_MAPPING_MATRIX.md`](./STANDARDS_MAPPING_MATRIX.md) | FHIR / HL7 / DHIS2 / ICD / LOINC / SNOMED CT / ISO / CAP / CLSI mapping |
| [`NATIONAL_DEPLOYMENT_CHECKLIST.md`](./NATIONAL_DEPLOYMENT_CHECKLIST.md) | Pre-deployment governance + operational checklist |
| [`INTEGRATION_RISK_ANALYSIS.md`](./INTEGRATION_RISK_ANALYSIS.md) | Cross-institutional integration risks |
| [`REMAINING_NATIONAL_RISKS.md`](./REMAINING_NATIONAL_RISKS.md) | Residual national-scale risks ranked by severity |

---

## Code Scaffolding (non-wired)

A small, **deliberately non-registered** Python package lives at
[`backend/app/interoperability/`](../../backend/app/interoperability/). It
provides:

- `AdapterBase` — abstract institutional-adapter interface
- `TrustDomain` — bounded trust-domain dataclass
- `InteropAuditEvent` — interop-only audit event shape
- `failure_isolation.py` — retry/circuit-isolation helpers (pure-Python)

These modules are intentionally **not imported by `main.py`** and **not
registered as FastAPI routes**. They exist to anchor architectural shape
without altering production runtime behavior. Wiring is a future,
explicitly-approved phase.

---

## Reading Order

If you only have time for the executive view, read in this order:

1. [`SOVEREIGN_INVARIANTS.md`](./SOVEREIGN_INVARIANTS.md)
2. [`NATIONAL_DEPLOYMENT_CHECKLIST.md`](./NATIONAL_DEPLOYMENT_CHECKLIST.md)
3. [`REMAINING_NATIONAL_RISKS.md`](./REMAINING_NATIONAL_RISKS.md)
4. Phase 16 + Phase 21 + Phase 23 (interoperability, AI governance, crisis continuity)

If you are a regulator or auditor, start with phase 18 + phase 24.
If you are a national integrator, start with phase 16 + phase 19.
If you are operational ops, start with phase 17 + phase 23.

---

## Compatibility Guarantees

Every document in this tree is bound by the GULA platform's existing
non-negotiable invariants (CLAUDE.md, "Core Principles"). In particular:

1. No artifact in this tree weakens tenant isolation.
2. No artifact removes or shortens audit retention.
3. No artifact reduces clinical-safety guarantees.
4. No artifact changes the behavior of an existing production endpoint.
5. No artifact silently expands AI execution authority.

If a future implementer cannot satisfy a documented assumption without
violating one of those invariants, the **invariant wins**, and the assumption
must be redesigned.
