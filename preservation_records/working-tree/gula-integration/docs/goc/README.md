# GOC — Global Operations Center

**Program:** GOC Discovery & Design
**Status:** DISCOVERY / DESIGN ONLY — no runtime code, no migrations, no routes, no deployment changes
**Decision record:** [ADR-026](../adr/ADR-026-global-operations-center.md) (Proposed)
**Extends:** [ADR-018 National Platform Operations Center](../adr/ADR-018-national-operations.md)
**Owner (proposed):** Platform Operations & Governance
**Last updated:** 2026-11-15

---

## 1. Purpose of this directory

This directory contains the **evidence-based discovery and design package** for the Global
Operations Center (GOC): the single operational authority for running the GULA national
platform across governorates, directorates, hospitals, and laboratories.

Nothing in this directory authorizes implementation. Every document is an input to a
design review. Implementation begins only after ADR-026 is **Accepted** by the Program
Director and the acceptance criteria in
[`08_ROADMAP_AND_ACCEPTANCE.md`](08_ROADMAP_AND_ACCEPTANCE.md) are agreed.

## 2. Reading order

| # | Document | Question it answers |
|---|----------|---------------------|
| 01 | [Executive Summary](01_EXECUTIVE_SUMMARY.md) | What exists today, what is missing, what is proposed? |
| 02 | [Discovery — Current State](02_DISCOVERY_CURRENT_STATE.md) | What is actually implemented, with file-level evidence? |
| 03 | [Capability Matrix](03_CAPABILITY_MATRIX.md) | Which ADR-018 commitments are met, partial, or absent? |
| 04 | [Gap Analysis](04_GAP_ANALYSIS.md) | What is missing and how severe is each gap? |
| 05 | [Security & Governance](05_SECURITY_AND_GOVERNANCE.md) | Where can GOC be abused, and what controls are required? |
| 06 | [Data, Persistence & Resilience](06_DATA_PERSISTENCE_AND_RESILIENCE.md) | Does GOC survive restart, failover, and multi-worker deployment? |
| 07 | [Target Architecture](07_TARGET_ARCHITECTURE.md) | What should GOC be, and what must it never become? |
| 08 | [Roadmap & Acceptance](08_ROADMAP_AND_ACCEPTANCE.md) | How is it delivered safely and how is "done" proven? |

## 3. Scope boundaries

**In scope**

- Operational authority over platform components: registry, health, releases, fleet,
  configuration, policy, audit, operational KPIs.
- Multi-tenant awareness across the national hierarchy
  (national → ministry → directorate → hospital → laboratory → department).
- Design for clinical-safety-preserving operations (a bad release must never silently
  reach a laboratory bench).

**Out of scope (explicitly excluded)**

- No clinical decision logic. GOC must never interpret, alter, or approve a patient result.
- No replacement of CI/CD, observability, or secret management tooling; GOC orchestrates.
- No changes to GLOSI. GLOSI is an **independent governance layer** (see §4).
- No runtime code, migrations, routes, or deployment manifest changes in this phase.

## 4. Relationship to GLOSI (hard boundary)

| | GLOSI | GOC |
|---|-------|-----|
| Role | Knowledge & evaluation registry that **precedes** architecture decisions | Operational authority for **running** the accepted architecture |
| Input | External projects, standards, research, security advisories | Registered platform components, releases, fleet nodes, policy |
| Output | Evaluations, decision records, procurement guidance | Health state, release execution, incidents, audit trail |
| Direction of dependency | Feeds GOC design decisions via ADRs | **Must not** write to, mutate, or couple to GLOSI internals |

**Rule:** GOC may *reference* GLOSI decision records (read-only, by ID) in its audit trail.
GOC may never create, approve, or modify a GLOSI decision. This preserves GLOSI's value as
an independent check on platform direction.

## 5. Why a GOC is needed at national scale

The platform already operates at a scale where uncoordinated change is an operational risk:

- Multiple deployment surfaces (API, workers, edge agent, laboratory desktop, mobile,
  citizen portal, professional portal).
- National hierarchy with strict tenant isolation requirements.
- Clinical safety obligations: a mis-sequenced release can invalidate results or corrupt
  QC baselines.
- Regulatory audit expectations: every operational action must be attributable,
  timestamped, and tamper-evident.

Today these concerns are spread across ad-hoc scripts, CI workflows, and an **unhardened
prototype** (`backend/app/control_plane/`) that is registered in the application factory.
Discovery (document 02) shows the prototype is not safe to rely on operationally.

## 6. Document status legend

| Term | Meaning in this package |
|------|-------------------------|
| **Implemented** | Verified in source, reachable at runtime. |
| **Partial** | Exists but incomplete, in-memory only, or missing a required control. |
| **Absent** | No implementation found. |
| **Proposed** | Target design; not implemented. Requires ADR-026 acceptance. |

**Nothing in this package is a claim of production readiness.** Every gap is tracked and
none is waived.
