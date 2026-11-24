# 07 — Target Architecture

**Program:** GOC Discovery & Design
**Status:** PROPOSED — requires [ADR-026](../adr/ADR-026-global-operations-center.md) acceptance
**Date:** 2026-11-15
**Inputs:** [02](02_DISCOVERY_CURRENT_STATE.md), [03](03_CAPABILITY_MATRIX.md), [04](04_GAP_ANALYSIS.md), [05](05_SECURITY_AND_GOVERNANCE.md), [06](06_DATA_PERSISTENCE_AND_RESILIENCE.md)

---

## 1. Design statement

The Global Operations Center is the **single operational authority** for running the GULA
national platform: it knows what components exist, what state they are in, what change is in
flight, who authorized it, and what happened afterwards. It is **not** a clinical system, an
observability replacement, or a CI/CD replacement.

```
        +-----------------------------------------------------------+
        |                    GOC  (authority plane)                 |
        |  registry . health . releases . fleet . config . policy   |
        |  approvals . incidents . audit . KPIs . dashboard         |
        +---------------------------+-------------------------------+
                                    | orchestrate (never replace)
        +---------------------------+-------------------------------+
        |                                                           |
   +----v-----+   +-----------+   +-----------+   +-----------+  +--v------+
   | CI/CD    |   | Prom /    |   | Secrets   |   | K8s /     |  | Edge    |
   | (GH      |   | Grafana / |   | (kernel   |   | Compose   |  | agents  |
   | Actions) |   | OTel      |   | loader)   |   | runtimes  |  | (labs)  |
   +----------+   +-----------+   +-----------+   +-----------+  +---------+
                                    |
                        observation only (read-only, by ID)
                                    v
                          +---------------------+
                          |  GLOSI  (governance |
                          |  knowledge registry)|
                          +---------------------+
```

## 2. Four non-negotiables

Every design choice below exists to satisfy one of these. If a proposal weakens any of them,
it is rejected regardless of convenience.

### N1 — Durable

Operational truth lives in the database, not in process memory. Every registered component,
release, approval, configuration version, policy change, incident, and fleet heartbeat is
persisted. Startup reconciles persisted state against live probes and marks unverifiable
entities `unknown` — never green. Multi-worker deployments read the same truth.

**Proof obligations:** restart-survival test, two-worker consistency test, DB-unavailable
degraded-read test, audit/write atomicity test.

### N2 — Authorized

Every endpoint is deny-by-default and gated by an explicit permission from a versioned
catalog, scoped by tenant dominance (`actor_tenant ⊒ target_tenant`). The authenticated
principal — never a request-body field — is the subject of every recorded action.

**Proof obligations:** role × endpoint × expected-effect matrix test, tenant-isolation
negative tests, catalog-completeness test (no route without a permission).

### N3 — Approval integrity

Approval is a first-class, append-only record bound to the authenticated principal,
their role, their tenant, the request correlation ID, and time. Requester, approver, and
deployer are distinct principals. Self-approval is structurally impossible, not merely
discouraged. Production channel may require quorum (open question Q1 in [06 §7](06_DATA_PERSISTENCE_AND_RESILIENCE.md)).

**Proof obligations:** self-approval rejection test, body-supplied-identity ignored test,
duplicate-approval rejection test, tamper-detection test on the approval record.

### N4 — Blast-radius bounded

Change advances through enforced stages (staging → canary → production) with automatic halt
on clinical-safety signals. No caller can jump stages. Deployment targets are constrained to
declared environments and declared components. A failed gate stops the release; it does not
"continue with a warning".

**Proof obligations:** stage-skip rejection test, automatic-halt-on-degraded-clinical-state
test, undeclared-target rejection test, rollback-execution test.

## 3. Layering (Clean Architecture)

The existing platform convention applies unchanged.

```
routes (thin HTTP)      →  application services  →  domain model  →  infrastructure
```

| Layer | GOC responsibility | Must not contain |
|---|---|---|
| Routes | Parse/validate Pydantic models, authorize, delegate, map errors | Business rules, direct DB access, in-memory state |
| Application services | Orchestration, gate evaluation, transaction boundaries, audit emission | HTTP concerns, raw SQL |
| Domain | Entities, value objects, invariants (`TenantDominance`, `ApprovalPolicy`, `ReleaseStage`) | Framework imports, persistence |
| Infrastructure | Repositories, probes, outbox, adapters to kernel/CI/observability | Business rules |

**Consequence:** the current `routes.py` + `sdk.py` singleton design is replaced. `sdk.py`
may survive only as a thin composition root that wires services; it must hold no mutable
operational state.

## 4. Component design (proposed)

| # | Component | Responsibility | Replaces |
|---|---|---|---|
| C1 | `goc/registry` | Component & dependency persistence, lifecycle transitions, reconciliation | `registry/component.py`, `registry/topology.py` |
| C2 | `goc/health` | Allowlisted probing, bounded concurrency, circuit breaker, state classification | `registry/health.py` |
| C3 | `goc/releases` | Release lifecycle, stage gates, rollback requests | `release/manager.py` |
| C4 | `goc/approvals` | Append-only approval records, quorum policy, separation-of-duties rules | inline body-supplied approval |
| C5 | `goc/fleet` | Node/container/edge inventory, heartbeat ingestion, expiry | `fleet/manager.py`, `fleet/provisioning.py` |
| C6 | `goc/config` | Versioned scoped configuration, optimistic concurrency, rollback | `config/manager.py` |
| C7 | `goc/policy` | Policy definitions; evaluation delegated to `core.policy_engine` | `policy/manager.py` |
| C8 | `goc/incidents` | SEV-1..SEV-4 lifecycle, escalation, post-mortem references | *(new — G-09)* |
| C9 | `goc/change` | Change requests, maintenance windows enforced at the deploy boundary | *(new — G-10)* |
| C10 | `goc/audit` | Single write-path choke point; fail-closed; correlation IDs | `audit.py` (kept, hardened) |
| C11 | `goc/dashboard` | Read-only composition of persisted state + delegated read models | `operations/center.py` (split out) |
| C12 | `goc/workflows` | Operational runbooks as versioned, tested definitions (limited scope) | *(new — G-06/A-03)* |

### 4.1 Explicit boundary — orchestrate, not replace

| Concern | Owner | GOC role |
|---|---|---|
| Build & test execution | CI/CD (GitHub Actions) | Request, observe, gate on result |
| Metrics & traces | Prometheus / Grafana / OTel | Read; embed links; never re-store raw telemetry |
| Secret material | Kernel `SecretsLoader` | Reference only; never read or persist values |
| Runtime scheduling | K8s / Compose | Describe intent; delegate execution |
| Clinical decisions | Clinical services | **Never participate** |
| Governance knowledge | GLOSI | Read-only reference by decision ID |

## 5. Authorization model (N2/N3)

### 5.1 Permission catalog (proposed, versioned)

| Permission | Grants | Default roles (proposal) |
|---|---|---|
| `control_plane:read` | View registry, health, topology, dashboard, KPIs | operator, ops_admin, auditor, platform_admin |
| `control_plane:register` | Create/update/retire components | ops_admin, platform_admin |
| `control_plane:configure` | Write configuration versions | ops_admin (tenant scope), platform_admin (global) |
| `control_plane:policy` | Create/disable policies | platform_admin, compliance_admin |
| `control_plane:release` | Create/request releases | ops_admin, platform_admin |
| `control_plane:approve` | Approve a release stage | release_approver, platform_admin |
| `control_plane:deploy` | Execute a deploy stage | deployer, platform_admin |
| `control_plane:fleet` | Mutate fleet inventory | ops_admin, platform_admin |
| `control_plane:audit` | Read audit log | auditor, platform_admin |
| `control_plane:incident` | Open/close incidents | on_call, ops_admin, platform_admin |

Role names above are **proposals requiring governance approval**; they do not exist until
accepted. The catalog is versioned so privilege growth is a reviewable event.

### 5.2 Separation of duties

```
request(release)   → principal A, permission control_plane:release
approve(stage)     → principal B, permission control_plane:approve,  B ≠ A
deploy(stage)      → principal C, permission control_plane:deploy,   C ≠ A
```

Enforced in the domain layer (`ApprovalPolicy`), not in route handlers, so it cannot be
bypassed by a new endpoint.

### 5.3 Tenant dominance

A single domain predicate `actor_tenant ⊒ target_tenant` is applied by the repository layer
as a query filter and re-asserted by the service layer before any write. Missing tenant
context ⇒ deny (never default to national). Tests use the platform's existing tenant
isolation matrix pattern.

## 6. Release pipeline (N4)

```
 DRAFT ─request→ PENDING_APPROVAL ─approve→ STAGING ─gate→ CANARY ─gate→ PRODUCTION
   │                    │                     │              │             │
   └────reject──────────┘                     └──halt─────────┴──halt───────┘
                                                    │
                                              ROLLED_BACK
```

Gate inputs (all must pass, no overrides):

1. CI build+test verdict for the exact artifact digest.
2. Canary error-rate and latency within declared budget.
3. **Clinical-safety interlock**: clinical safety state not degraded. A degraded interlock
   halts the release and opens an incident automatically.
4. Named approver distinct from requester (and quorum if adopted).
5. Deploy target is a declared environment + declared component.

Every transition writes an append-only record with correlation ID. A stage cannot be skipped
by omitting a field; unknown stage ⇒ reject.

## 7. Observability of the GOC itself

| Signal | Requirement |
|---|---|
| Metrics | `goc_*` counters/histograms: operations by permission, gate outcomes, probe latency, approval latency |
| Traces | Span per operational action, correlating HTTP → service → repository → outbox |
| Logs | Structured JSON with `correlation_id`, `principal_id`, `tenant_id`, `permission` |
| Health | `/control-plane/health` reports `ok` / `degraded` / `unknown`, backed by real probes |
| Alerts | Gate failure, audit-write failure, probe failure rate, stale heartbeats |

Vendor-neutral: OTLP export only, no proprietary agent (constitution: no vendor lock-in).

## 8. Failure and degradation design

| Failure | Behavior |
|---|---|
| DB unavailable | Read endpoints `503` + `state: unknown`; write endpoints `503`; never cached-green |
| Probe unavailable | Component `unreachable` with error class; never promoted to `active` |
| Audit write fails | Operation rejected (fail-closed) |
| Concurrent config write | Stale write rejected with `409` + current version |
| Worker crash mid-release | Release resumes from persisted state on startup reconciliation |
| Clock skew | Timestamps use DB clock; approval freshness bounded by max age |

## 9. What the GOC must never become

| Prohibited | Reason |
|---|---|
| Clinical decision authority | Platform constitution; clinical safety |
| Result/QC modification surface | Would invalidate laboratory accreditation |
| Second source of truth for metrics | Duplicates observability; drift |
| Secret store | Kernel loader is authoritative |
| GLOSI writer | Destroys independent governance value |
| General BPM platform | Scope creep; unbounded attack surface |
| Silent auto-remediation without verification | Burns trust in operational state (G-08) |

Each prohibition becomes a documented negative test in the P-phase acceptance suite.

## 10. Deployment shape

| Aspect | Proposal |
|---|---|
| Process | Same API service initially (modular monolith, ADR-002), separate router prefix |
| Storage | Platform PostgreSQL; new `goc_*` tables only (additive migrations) |
| Background work | Outbox consumer + heartbeat expiry job via existing task queue |
| Feature flag | GOC router enabled per environment; disabled by default outside staging/production |
| Exposure | Administrative network boundary; not reachable from public internet |

Splitting into a separate service is explicitly **deferred** — it adds blast-radius and
operational cost before the safety properties in N1–N4 are proven. Revisit only after P5.

## 11. Open design questions

Carried forward from [06 §7](06_DATA_PERSISTENCE_AND_RESILIENCE.md) plus:

1. Quorum for production approvals: required or optional per channel?
2. Separate operational database vs co-located with platform DB?
3. Fleet heartbeat volume: dedicated store or shared table + retention job?
4. Approval timestamp authority: DB clock vs token issued-at?
5. Does the clinical-safety interlock read from `core.self_healing.health`, the clinical
   service directly, or a dedicated safety-state projection?

These are inputs to ADR-026 acceptance, not assumptions.
