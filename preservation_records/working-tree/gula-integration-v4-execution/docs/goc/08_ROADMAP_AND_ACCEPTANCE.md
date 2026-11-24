# 08 — Roadmap & Acceptance

**Program:** GOC Discovery & Design
**Status:** PROPOSED — requires [ADR-026](../adr/ADR-026-global-operations-center.md) acceptance
**Date:** 2026-11-15
**Rule:** no phase may close while any of its exit gates fails. A gate is a test, not an opinion.

---

## 1. Sequencing principle

Order is driven by **irreversibility and blast radius**, not by delivery optics:

1. Stop live abuse first (P0) — cheapest, highest risk reduction.
2. Establish the authorization and tenancy boundary (P1) before writing persisted endpoints,
   otherwise every endpoint must be reworked twice.
3. Make state durable (P2) — releases and incidents require history.
4. Enforce release safety (P3) — the operational value proposition.
5. Incidents and change management (P4) — depend on durable history.
6. Complete the dashboard (P5) — depends on everything above.

Nothing in P0–P5 starts until ADR-026 is **Accepted**. This package is design only.

## 2. Phase table

| Phase | Scope | Closes | Depends on |
|---|---|---|---|
| P0 Containment | Close approval spoofing, SSRF, and unverified audit on live surface | G-02, G-03, G-15 | — |
| P1 Authorization | Deny-by-default permissions + tenant dominance + typed contracts | G-01, G-18, G-14 | P0 |
| P2 Durability | Persisted models, migrations, repository layer, startup reconciliation | G-04, G-13, G-11, G-17 | P1 |
| P3 Release safety | Stage gates, clinical interlock, verified rollback | G-06, G-08, G-16 | P2 |
| P4 Incidents & change | SEV lifecycle, change requests, maintenance windows, reporting | G-09, G-10, G-12 | P2 |
| P5 Dashboard | Remove placeholders; environment-aware read model | G-07 | P2, P3, P4 |

---

## 3. P0 — Containment

**Goal:** make the currently registered `/control-plane` surface non-exploitable, even
before any redesign.

| Work item | Detail |
|---|---|
| P0-1 | Principal identity from authenticated token only; remove every body-supplied `user`/`approver` field |
| P0-2 | Split approval and deployment into distinct endpoints with distinct permission checks |
| P0-3 | Reject self-approval (`approver == requester`) at the domain layer |
| P0-4 | Probe allowlist for `health_endpoint` (scheme, host, port, path prefix); block loopback, private, link-local, metadata ranges; disable redirects; cap response size; return status+latency only |
| P0-5 | Single audit choke point on the write path; fail-closed when audit write fails |
| P0-6 | Interim router gating (admin-only dependency or disable per environment) until P1 lands |

**Exit gates**

| Gate | Test |
|---|---|
| E0.1 | Body-supplied identity is ignored (request with forged `user` records the token subject) |
| E0.2 | Self-approval rejected with a specific error code |
| E0.3 | SSRF negative suite: loopback, RFC1918, link-local, `169.254.169.254`, redirect chain — all rejected |
| E0.4 | Every mutating endpoint emits exactly one audit entry; audit-write failure aborts the operation |
| E0.5 | Router unreachable with a non-admin token |
| E0.6 | Full existing test suite still green (no regressions) |

**Rollback:** each item is independently revertible; P0-6 is a one-line change.

---

## 4. P1 — Authorization & contracts

**Goal:** replace "any authenticated user" with a deny-by-default, tenant-scoped, typed API.

| Work item | Detail |
|---|---|
| P1-1 | Permission catalog (`control_plane:*`) as versioned code constant |
| P1-2 | Role → permission mapping approved by governance (ADR-026 annex) |
| P1-3 | `require_permission(...)` on all 21 endpoints, deny-by-default |
| P1-4 | Tenant dominance predicate in one place; applied on read and write |
| P1-5 | Pydantic request/response models for every endpoint; regenerate client |
| P1-6 | Explicit error taxonomy (401/403/404/409/422) with stable codes |

**Exit gates**

| Gate | Test |
|---|---|
| E1.1 | Role × endpoint × expected-effect matrix passes for every role and every endpoint |
| E1.2 | Catalog completeness: every route declares ≥1 permission (static test) |
| E1.3 | Tenant isolation negative matrix passes (cross-directorate, cross-hospital, missing tenant) |
| E1.4 | OpenAPI: every request/response has a concrete schema; generated client compiles |
| E1.5 | No endpoint returns 500 on malformed input (fuzz/negative suite) |

---

## 5. P2 — Durability

**Goal:** operational truth survives restart, failover, and multi-worker deployment.

| Work item | Detail |
|---|---|
| P2-1 | Eight entity models (`goc_*`) per [06 §2](06_DATA_PERSISTENCE_AND_RESILIENCE.md) |
| P2-2 | Additive, reversible migrations (one per entity group) |
| P2-3 | Repository layer; services use repositories only |
| P2-4 | Remove mutable process-global state from managers; `sdk.py` becomes composition root only |
| P2-5 | Transactional outbox for audit; consumer drains it |
| P2-6 | Startup reconciliation: DB vs live probes → `unknown` where unverifiable |
| P2-7 | Optimistic concurrency (`version`) on state tables |
| P2-8 | Heartbeat ingestion + expiry job |
| P2-9 | Extend backup/DR to cover `goc_*` tables; restore drill |

**Exit gates**

| Gate | Test |
|---|---|
| E2.1 | Register → restart → state intact |
| E2.2 | Two workers observe identical state (shared DB) |
| E2.3 | DB unavailable ⇒ `503` + `state: unknown` (never green) |
| E2.4 | Concurrent config writes ⇒ stale rejected with `409` + current version |
| E2.5 | Audit failure aborts the write; outbox drains without loss |
| E2.6 | Migration up→down→up leaves a clean schema |
| E2.7 | DR restore of `goc_*` tables verified on PostgreSQL 16 |
| E2.8 | Startup reconciliation marks unverifiable components `unknown`, not `active` |

---

## 6. P3 — Release safety

**Goal:** a bad release cannot silently reach a laboratory bench.

| Work item | Detail |
|---|---|
| P3-1 | Stage state machine (DRAFT→PENDING_APPROVAL→STAGING→CANARY→PRODUCTION, halt/rollback) |
| P3-2 | Stage-skip and unknown-stage rejection |
| P3-3 | Gate evaluation: CI verdict, canary budget, approval validity, declared target |
| P3-4 | Clinical-safety interlock; halt + auto-incident on degraded state |
| P3-5 | Rollback endpoint with post-rollback verification |
| P3-6 | Replace optimistic `auto_heal` with verified remediation only |
| P3-7 | Maintenance-window enforcement at the deploy boundary |

**Exit gates**

| Gate | Test |
|---|---|
| E3.1 | Stage skip rejected; unknown stage rejected |
| E3.2 | Failed canary budget halts release (no override path) |
| E3.3 | Degraded clinical interlock halts release and opens an incident |
| E3.4 | Undeclared target environment/component rejected |
| E3.5 | Rollback restores prior version and is verified |
| E3.6 | No status transition occurs without a successful probe |
| E3.7 | Attempt to deploy during closed maintenance window rejected |

---

## 7. P4 — Incidents & change management

**Goal:** operational failures are classified, escalated, and reconstructed.

| Work item | Detail |
|---|---|
| P4-1 | `goc_incident` entity + SEV-1..SEV-4 taxonomy |
| P4-2 | Open/acknowledge/escalate/resolve/close lifecycle with transitions |
| P4-3 | Escalation policy per severity |
| P4-4 | Post-mortem reference requirement before SEV-1/2 closure |
| P4-5 | Change-request entity linked to releases |
| P4-6 | Compliance/reporting export (retention-aware) |

**Exit gates**

| Gate | Test |
|---|---|
| E4.1 | SEV lifecycle transitions enforced (invalid transitions rejected) |
| E4.2 | SEV-1/2 cannot close without post-mortem reference |
| E4.3 | Escalation fires on defined conditions |
| E4.4 | Change request required for production deploy |
| E4.5 | Compliance export reproducible and retention-bounded |

---

## 8. P5 — Dashboard completeness

**Goal:** no placeholder sections; environment-aware operational picture.

| Work item | Detail |
|---|---|
| P5-1 | Dedicated `goc/dashboard` read model |
| P5-2 | Replace `clinical`/`security`/`ai`/`compliance` placeholders with real read models or explicit `not_available` with reason |
| P5-3 | Environment dimension (dev/staging/prod) in every section |
| P5-4 | Read-only guarantee verified (no write paths from dashboard) |

**Exit gates**

| Gate | Test |
|---|---|
| E5.1 | No section returns placeholder prose; unavailable data returns `not_available` + reason |
| E5.2 | Dashboard performs zero state mutations (asserted) |
| E5.3 | Environment filtering verified |
| E5.4 | Dashboard reflects persisted state after restart |

---

## 9. Cross-cutting acceptance (all phases)

| Requirement | Evidence |
|---|---|
| Behavior preservation for non-GOC surfaces | full existing suite green at every phase boundary |
| No vendor lock-in | new dependencies justified; OTLP/HTTP only |
| Free/open-source first | dependency register updated per phase |
| Audit integrity | hash-chain verification test |
| No secrets in repo | gitleaks clean; `.env` untracked |
| Reversibility | every phase revertible by `git revert` of its commits |
| Documentation | ADR-026 updated; runbook per phase |

## 10. Definition of "operational authority"

The GOC may be described as the operational authority **only** when all of the following hold
simultaneously:

1. All S1 gaps (G-01, G-02, G-03, G-04, G-05, G-18) are closed and proven by their gates.
2. N1–N4 proof obligations all pass in CI on the integration branch.
3. Backup/DR covers `goc_*` tables and a restore drill has been executed.
4. Permission catalog and role mapping are approved in ADR-026 annex.
5. No endpoint remains guarded by authentication alone.

Until then, every document and status report must describe the surface as a
**prototype under containment**.

## 11. Effort indication (relative, not a schedule)

| Phase | Relative effort | Risk |
|---|---|---|
| P0 | S | Low — small, targeted, revertible |
| P1 | M | Medium — touches all 21 endpoints |
| P2 | L | Medium — migrations + repository rewrite |
| P3 | L | High — clinical interlock semantics |
| P4 | M | Low–Medium — new domain, no legacy |
| P5 | M | Low |

No calendar estimates are given: the constitution forbids fabricated schedules. Effort is
expressed relative to one another so sequencing decisions can be made without invented dates.

## 12. Decision requested

ADR-026 asks the Program Director to:

1. **Accept** the target architecture and the four non-negotiables (N1–N4).
2. **Approve** P0 containment as the first change window.
3. **Confirm** the permission catalog and role mapping approach (§5 of [07](07_TARGET_ARCHITECTURE.md)).
4. **Decide** the open questions in [06 §7](06_DATA_PERSISTENCE_AND_RESILIENCE.md) and [07 §11](07_TARGET_ARCHITECTURE.md).

No implementation begins before 1–3 are answered.
