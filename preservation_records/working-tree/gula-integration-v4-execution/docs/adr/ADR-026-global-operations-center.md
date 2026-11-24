# ADR-026: Global Operations Center

**Status:** Proposed
**Date:** 2026-11-15
**Deciders:** Program Director, Platform Architect, Security Lead, Clinical Safety Lead
**Extends:** [ADR-018 National Platform Operations Center](ADR-018-national-operations.md)
**Discovery & design package:** [`docs/goc/`](../goc/README.md)

---

## Context

ADR-018 (Accepted, 2026-07-15) committed the platform to a National Platform Operations
Center implemented as `control_plane/`. That decision defined the *intent*: a lightweight
orchestration layer over existing tooling, a workflow engine, a read-only dashboard, a
release pipeline with approval gates, and SEV-1..SEV-4 incident management.

Discovery performed for this ADR (see [`docs/goc/02_DISCOVERY_CURRENT_STATE.md`](../goc/02_DISCOVERY_CURRENT_STATE.md))
establishes that the implementation realizes **27% of ADR-018** (12 met / 14 partial /
19 absent of 45 commitments), and that the absent mass is concentrated in the
safety-critical categories: authorization, release gates, incidents, and quality.

Concrete verified findings on the live, factory-registered `/control-plane` surface:

| ID | Finding | CWE |
|---|---|---|
| F-01 | 21 endpoints, 0 role checks — any authenticated user can mutate operational state | CWE-862 |
| F-02 | Approver identity read from the request body; `approve_first` allows single-call self-approval | CWE-290 / CWE-639 |
| F-03 | SSRF: `HealthAggregator` fetches a caller-supplied `health_endpoint` | CWE-918 |
| F-04 | No persistence: no tables, no migrations; all state in process singletons | CWE-664 |
| F-05 | Audit emission not enforced on the write path | CWE-778 |
| F-06 | No tenant-scope enforcement on any endpoint | CWE-863 |
| F-07 | Free-form `dict[str, Any]` request bodies; no schema, no validation | CWE-20 |

Additional structural gaps: zero test files reference `control_plane`; no incident, change,
or compliance implementation exists; and the ADR-018 mandated `workflows/` and `dashboard/`
modules do not exist.

The platform therefore has an **unhardened administrative surface registered in production
reach**, and no accepted design that says what a safe version must be. ADR-026 addresses the
design question. It does **not** authorize implementation.

**Requirements**

- A single operational authority for the national platform across governorates, directorates,
  hospitals, and laboratories.
- Durable operational truth shared across workers.
- Deny-by-default authorization scoped to the tenant hierarchy.
- Approvals attributable to authenticated principals, with separation of duties.
- Releases that cannot silently reach a laboratory bench.
- An immutable audit trail for every operational action.
- Explicit non-replacement of CI/CD, observability, and secret management.

**Constraints**

- No clinical decision authority; no modification of results or QC data.
- GLOSI is an independent governance layer and must remain read-only to GOC.
- Free/open-source and self-hosted first; vendor-neutral (OTLP/HTTP) telemetry only.
- Additive, reversible migrations; no alteration of existing clinical/identity tables.
- Design-only in this phase: no runtime code, migrations, routes, or deployment changes.

## Decision

Adopt the **Global Operations Center (GOC)** as the target operational authority, replacing
the `control_plane` prototype's execution model while retaining its domain vocabulary
(components, fleet, releases, policies, tenants, digital twins).

### 1. Four non-negotiables

Every GOC design decision must satisfy all four; weakening any one is a rejection criterion.

| # | Property | Definition |
|---|---|---|
| **N1** | **Durable** | Operational truth is persisted; survives restart, failover, and multi-worker deployment; unverifiable state is reported `unknown`, never green. |
| **N2** | **Authorized** | Deny-by-default, explicit versioned permission catalog, tenant dominance (`actor_tenant ⊒ target_tenant`) enforced on every read and write. |
| **N3** | **Approval integrity** | Approval is an append-only record bound to the authenticated principal, role, tenant, correlation ID, and time; requester ≠ approver ≠ deployer; self-approval structurally impossible. |
| **N4** | **Blast-radius bounded** | Enforced stage gates (staging → canary → production), declared targets only, automatic halt on clinical-safety signals, no override path. |

### 2. ADR-018 is partially realized, not satisfied

This ADR explicitly does **not** claim to complete ADR-018. It records that ADR-018 remains
partially realized and makes the absent safety categories a precondition for the GOC being
granted operational authority. Completion is tracked in
[`docs/goc/03_CAPABILITY_MATRIX.md`](../goc/03_CAPABILITY_MATRIX.md).

### 3. Orchestrate, never replace

| Concern | Owner | GOC role |
|---|---|---|
| Build/test execution | CI/CD (GitHub Actions) | Request, observe, gate on result |
| Metrics/traces | Prometheus / Grafana / OTel | Read; link; never re-store raw telemetry |
| Secret material | Kernel `SecretsLoader` | Reference only; never read or persist values |
| Runtime scheduling | Kubernetes / Compose | Express intent; delegate execution |
| Clinical decisions | Clinical services | **Never participate** |
| Governance knowledge | GLOSI | Read-only reference by decision ID |

### 4. GLOSI boundary (hard)

GOC may reference GLOSI decision records by ID in its audit trail. GOC may never create,
approve, modify, or delete a GLOSI record, and must not import GLOSI internals. This
preserves GLOSI's function as an independent check on platform direction.

### 5. Authorization model

A versioned permission catalog (`control_plane:read|register|configure|policy|release|approve|deploy|fleet|audit|incident`)
with a governance-approved role mapping. Deny-by-default; a static test asserts every route
declares at least one permission. Separation of duties is enforced in the domain layer so a
new endpoint cannot bypass it. Missing tenant context denies; it never defaults to national.

### 6. Delivery sequence

| Phase | Scope | Exit condition |
|---|---|---|
| P0 | Containment — approval identity, SSRF, audit choke point, interim gating | Abuse paths closed; negative suites green |
| P1 | Authorization & contracts — catalog, tenant dominance, Pydantic models | Role×endpoint matrix and isolation matrix green |
| P2 | Durability — `goc_*` models, migrations, repositories, outbox, reconciliation | Restart/multi-worker/DR gates green |
| P3 | Release safety — stage gates, clinical interlock, verified rollback | Gate and auto-halt suites green |
| P4 | Incidents & change — SEV lifecycle, change requests, reporting | Lifecycle and export gates green |
| P5 | Dashboard completeness — no placeholders | Read-only and post-restart gates green |

Detailed gates: [`docs/goc/08_ROADMAP_AND_ACCEPTANCE.md`](../goc/08_ROADMAP_AND_ACCEPTANCE.md).

### 7. Definition of operational authority

The GOC may be described as the operational authority only when all S1 gaps (G-01, G-02,
G-03, G-04, G-05, G-18) are closed with passing gates, N1–N4 proof obligations run in CI,
backup/DR covers `goc_*` tables with an executed restore drill, and the permission catalog is
approved in this ADR's annex. Until then the surface is described as a **prototype under
containment**.

## Consequences

### Positive

- Converts a live, unaudited administrative surface into a designed, gated authority plane.
- Reuses the prototype's sound domain model instead of discarding it.
- Makes separation of duties, tenant isolation, and clinical-safety interlocks explicit and
  testable rather than implied.
- Establishes a durable operational ledger that can be reconciled against the audit chain.
- Preserves ADR-018's intent while correcting its unstated assumption that a prototype
  equals a safe operations center.

### Negative

- P0–P5 is substantial work; the prototype cannot be relied upon in the interim.
- Persistence and authorization rework touches all 21 endpoints.
- Additional tables and background jobs increase operational surface (outbox consumer,
  heartbeat expiry).
- Requires governance approval of a permission catalog and role mapping before P1 can close.

### Risks

| Risk | Mitigation |
|---|---|
| Prototype is treated as production-ready before P0 | Every GOC document states "prototype under containment"; router gating in P0 |
| Clinical interlock semantics are wrong | Open question Q5 escalated to Clinical Safety Lead before P3 |
| Scope creep toward a general BPM platform | §3 and [07 §9](../goc/07_TARGET_ARCHITECTURE.md) prohibitions, each a negative test |
| Approval quorum decision deferred too long | Q1 in [06 §7](../goc/06_DATA_PERSISTENCE_AND_RESILIENCE.md) resolved at ADR acceptance |
| GLOSI coupling emerges accidentally | Hard boundary in §4, reviewed at each phase gate |

## Compliance

| Constitution requirement | ADR-026 obligation |
|---|---|
| ADR-001 Engineering Constitution (ADR before implementation) | This ADR must be Accepted before P0 begins |
| ADR-018 National Platform Operations Center | Extended, not superseded; conformance tracked in `03_CAPABILITY_MATRIX.md` |
| ADR-024 Platform Constitution | Orchestrate-not-replace, vendor-neutral telemetry, self-hosted first |
| ADR-025 Data Preservation Constitution | Additive, reversible migrations; no alteration of clinical/identity tables |
| Multi-tenancy constitution | Tenant dominance enforced on every read and write |
| Immutable audit log | Write-path audit, fail-closed, hash-chained |
| OWASP ASVS / API Top 10 | F-01 (API1/API5), F-03 (API7), F-07 (API3) remediated in P0/P1 |
| Clinical safety | Clinical-safety interlock (N4); no clinical decision authority |
| GLOSI independence | Read-only reference boundary (§4) |

## Annex (to be completed at acceptance)

- Permission catalog version and role → permission mapping.
- Answers to open questions in [`06 §7`](../goc/06_DATA_PERSISTENCE_AND_RESILIENCE.md) and
  [`07 §11`](../goc/07_TARGET_ARCHITECTURE.md).
- Decision on interim containment option (A/B/C/D in
  [`05 §7`](../goc/05_SECURITY_AND_GOVERNANCE.md)).

## References

- [`docs/goc/README.md`](../goc/README.md) — package index and scope boundaries
- [`docs/goc/01_EXECUTIVE_SUMMARY.md`](../goc/01_EXECUTIVE_SUMMARY.md)
- [`docs/goc/02_DISCOVERY_CURRENT_STATE.md`](../goc/02_DISCOVERY_CURRENT_STATE.md)
- [`docs/goc/03_CAPABILITY_MATRIX.md`](../goc/03_CAPABILITY_MATRIX.md)
- [`docs/goc/04_GAP_ANALYSIS.md`](../goc/04_GAP_ANALYSIS.md)
- [`docs/goc/05_SECURITY_AND_GOVERNANCE.md`](../goc/05_SECURITY_AND_GOVERNANCE.md)
- [`docs/goc/06_DATA_PERSISTENCE_AND_RESILIENCE.md`](../goc/06_DATA_PERSISTENCE_AND_RESILIENCE.md)
- [`docs/goc/07_TARGET_ARCHITECTURE.md`](../goc/07_TARGET_ARCHITECTURE.md)
- [`docs/goc/08_ROADMAP_AND_ACCEPTANCE.md`](../goc/08_ROADMAP_AND_ACCEPTANCE.md)
- [`docs/adr/ADR-018-national-operations.md`](ADR-018-national-operations.md)
