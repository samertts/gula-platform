# 01 — Executive Summary

**Program:** GOC Discovery & Design
**Status:** DISCOVERY / DESIGN ONLY
**Date:** 2026-11-15
**Related:** [ADR-018](../adr/ADR-018-national-operations.md), [ADR-026](../adr/ADR-026-global-operations-center.md) (Proposed)

---

## 1. The finding in one paragraph

A Global Operations Center capability **partially exists** in this repository as
`backend/app/control_plane/` — 32 Python modules, ~2,715 lines, 21 HTTP endpoints under
`/control-plane`, registered and reachable at runtime. It is a genuine, useful foundation:
a component registry, health aggregation, a fleet/edge inventory, release records,
configuration and policy managers, a digital-twin model, multi-tenant hierarchy, KPIs, and
an audit bridge to the shared audit service. **However, it is an unhardened prototype, not
an operations center.** All operational state is held in process memory, there are zero
tests, every endpoint is authorized by "is a logged-in user" alone, release approval
identity is taken from the request body, and the health aggregator will fetch any URL a
caller supplies. It must not be treated as the operational authority until the gaps in
this package are closed.

## 2. What exists (verified)

| Capability | State | Evidence |
|---|---|---|
| Component registry (12 component types, 6 statuses) | Implemented (in-memory) | `control_plane/registry/component.py`, `enums.py` |
| Health aggregation with HTTP probes | Partial (SSRF-prone) | `registry/health.py` |
| Fleet / node / container / edge inventory | Partial (in-memory) | `fleet/manager.py`, `fleet/provisioning.py` |
| Release records + channels + rollback fields | Partial (no gates enforced) | `release/manager.py` |
| Configuration scopes (global/tenant/component/environment) | Partial (in-memory) | `config/manager.py`, `config/features.py` |
| Policy manager (8 domains, 4 effects) | Partial (bridges core policy engine) | `policy/manager.py` |
| Digital twin (infra/service/app/hospital) | Partial (read model only) | `digital_twin/` |
| Multi-tenant hierarchy (6 levels) | Partial (bridges kernel tenant registry) | `multi_tenant.py` |
| Operational KPIs | Partial | `analytics.py`, `GET /control-plane/kpis` |
| Audit bridge (11 control actions) | Implemented (delegates to shared audit) | `audit.py` |
| Autonomous ops (auto-heal, scaling, maintenance window) | Partial (in-memory toggles) | `operations/automation.py` |
| Operations dashboard snapshot | Partial (7 sections, 4 delegated) | `operations/center.py` |

## 3. What is absent (blocking for operational authority)

1. **No persistence.** No concrete SQLAlchemy tables, no migrations. `control_plane/base.py`
   contains only mixins. All state lives in singletons — lost on restart, divergent across
   workers. → [06](06_DATA_PERSISTENCE_AND_RESILIENCE.md)
2. **No authorization model.** 21 endpoints, 21 × `Depends(get_current_user)`, 0 ×
   `require_permission` or `require_admin`. Any authenticated user — including a
   `technician` — can register components, rewrite configuration, create policies, and
   deploy releases. → [05](05_SECURITY_AND_GOVERNANCE.md)
3. **No approval integrity.** `POST /control-plane/releases/deploy` reads the approver from
   the request body (`data.get("user", "unknown")`) and supports `approve_first` — an
   anonymous-to-privileged self-approval in a single call. → [05](05_SECURITY_AND_GOVERNANCE.md)
4. **No incident management.** ADR-018 Phase 3 (SEV-1..SEV-4, escalation, post-mortems) has
   no implementation: no models, no endpoints, no workflow. The audit enum defines
   `control.incident` but nothing emits it.
5. **No workflow engine.** ADR-018 calls for `control_plane/workflows/` (operations as code).
   The directory does not exist.
6. **No dedicated dashboard module.** ADR-018 calls for `control_plane/dashboard/`; the
   snapshot is produced inline in `operations/center.py`. Four of seven dashboard sections
   are placeholder text delegating to other layers.
7. **No change management.** No change-request lifecycle, no maintenance windows enforced at
   the deployment boundary, no blast-radius control.
8. **No compliance reporting.** No regulatory export, no retention policy, no attestation
   artifacts.
9. **No tests.** Zero test files reference `control_plane`. Nothing is regression-protected.
10. **No multi-worker safety.** In-memory policy/config/registry means two API workers can
    disagree about platform state.

## 4. Risk position

The highest-severity findings are **authorization** (F-01), **approval spoofing** (F-02),
**SSRF via component health endpoint** (F-03), and **non-durable state** (F-04). Individually
each is sufficient to disqualify the prototype from production use as an operations center.
Detailed severity, impact, and remediation are in [05](05_SECURITY_AND_GOVERNANCE.md) and
[04](04_GAP_ANALYSIS.md).

Because `/control-plane` is already registered in the application factory, these risks are
**live today**, not hypothetical. Interim containment options are listed in
[05 §7](05_SECURITY_AND_GOVERNANCE.md). Containment is a decision for the Program Director;
this package does not implement it.

## 5. Proposal in one paragraph

Promote the prototype to a **GOC** with four non-negotiable properties: (1) **durable** —
every operational fact is persisted with an append-only audit chain; (2) **authorized** —
every action is gated by explicit RBAC/ABAC permissions scoped to the tenant hierarchy;
(3) **approval-integrity** — approvals are cryptographically attributed to the authenticated
principal, never to request-body fields, and self-approval is structurally impossible;
(4) **blast-radius bounded** — releases advance through enforced gates (staging → canary →
production) with automatic halt on clinical-safety signals. The GOC orchestrates existing
tooling (CI/CD, observability, secret management) and never replaces it. Full target design:
[07](07_TARGET_ARCHITECTURE.md).

## 6. Recommendation

| Recommendation | Detail |
|---|---|
| **Do not** treat `control_plane` as authoritative today | It has no persistence, no authorization, no tests |
| **Adopt** the prototype as the GOC seed | Its domain model (registry, fleet, release, policy, twin) is sound and reusable |
| **Accept** ADR-026 before any implementation | Design review is the gate; no code in this phase |
| **Sequence** work as P0 security → P1 durability → P2 gates → P3 incidents | See [08](08_ROADMAP_AND_ACCEPTANCE.md) |
| **Preserve** GLOSI independence | GOC references GLOSI decisions read-only; never mutates them |

## 7. Deliverables in this package

`README.md` + eight documents (01–08) + ADR-026. No runtime code, migration, route, or
deployment change is included, by design.
