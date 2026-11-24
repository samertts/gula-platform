# 04 — Gap Analysis

**Program:** GOC Discovery & Design
**Status:** DISCOVERY
**Date:** 2026-11-15

---

## 1. Gap register

Severity uses the platform scale: **S1 Critical** (blocks operational authority; patient or
data safety), **S2 High** (materially unsafe or non-compliant), **S3 Medium** (degraded
operability), **S4 Low** (quality/maintainability).

| ID | Gap | Severity | Blocks operational authority | Effort |
|---|---|---|---|---|
| G-01 | No authorization model — any authenticated user can mutate operational state | S1 | Yes | M |
| G-02 | Release approval identity from request body; self-approval possible | S1 | Yes | S |
| G-03 | SSRF via caller-supplied component health endpoint | S1 | Yes | S |
| G-04 | No durable state — registry/releases/policies/config lost on restart | S1 | Yes | L |
| G-05 | Zero tests — no regression protection | S1 | Yes | M |
| G-06 | No enforced release gates (staging/canary/production) | S2 | Yes | L |
| G-07 | Dashboard sections are placeholders (clinical/security/ai/compliance) | S2 | Yes | M |
| G-08 | `auto_heal` flips status without probing the real system | S2 | Yes | S |
| G-09 | No incident management (SEV levels, escalation, post-mortem) | S2 | Yes | L |
| G-10 | No change management / blast-radius control | S2 | Yes | L |
| G-11 | Config writes lack versioning and rollback | S3 | No | M |
| G-12 | No incident/compliance reporting export | S3 | No | M |
| G-13 | In-memory state is not multi-worker consistent | S2 | Yes | (G-04) |
| G-14 | Request bodies typed `dict[str, Any]` — no contract, no validation | S3 | No | M |
| G-15 | Audit emission not consistently verified across all mutating endpoints | S2 | Yes | S |
| G-16 | No maintenance-window enforcement at the deploy boundary | S3 | No | S |
| G-17 | `rollback` has state fields but no endpoint or verification | S3 | No | M |
| G-18 | No tenant isolation enforcement on any endpoint | S1 | Yes | M |

**S1 gaps: 6** (G-01, G-02, G-03, G-04, G-05, G-18)

## 2. Gap detail — the six critical gaps

### G-01 — No authorization model

**Current:** all 21 endpoints depend on `get_current_user` only. `require_permission` and
`require_admin` are used elsewhere in the platform but not here.

**Impact:** a `technician` or `staff` account can register components, overwrite
configuration, create policies, and deploy releases. Operational authority is effectively
platform-wide for any authenticated principal.

**Required:** explicit permission set (`control_plane:read`, `:register`, `:configure`,
`:policy`, `:release`, `:deploy`, `:fleet`, `:audit`) mapped to roles; deny-by-default.

### G-02 — Release approval spoofing

**Current:** approver/deployer identity read from the request body; `approve_first`
performs approval and deployment in one call.

**Impact:** separation of duties is unenforceable; audit records an attacker-chosen name.

**Required:** identity taken exclusively from the authenticated principal; approval and
deployment as distinct permissions and distinct calls; self-approval rejected; audit binds
to the token subject and the authentication context.

### G-03 — SSRF via health endpoint

**Current:** `HealthAggregator` issues `httpx.get(health_endpoint)` for any registered
component; `health_endpoint` comes from the caller.

**Impact:** server-side request forgery against internal networks, metadata endpoints, and
adjacent services; also a denial-of-service vector via slow endpoints (5 s timeout per
component, aggregated serially).

**Required:** allowlist of probe targets (scheme, host, port, path prefix) from deployment
configuration; block link-local, loopback, private ranges, and metadata addresses unless
explicitly permitted; aggregate with bounded concurrency and a circuit breaker.

### G-04 / G-13 — Non-durable, non-shared state

**Current:** `ComponentRegistry`, `FleetManager`, `ReleaseManager`, `PolicyManager`,
`ConfigurationManager` are process singletons with dict storage; no tables, no migrations.

**Impact:** restart erases the operational record; multiple workers disagree; no historical
reconstruction; audit cannot be reconciled against the state that produced it.

**Required:** persisted models for components, releases, approvals, fleet nodes,
configuration versions, and policies; append-only history; single source of truth shared by
all workers.

### G-05 — Zero tests

**Current:** no test file references `control_plane`.

**Impact:** every change is unverifiable; regressions are undetectable; no evidence exists
for the safety properties this package demands.

**Required:** unit tests per manager, contract tests per endpoint, authorization matrix
tests (role × endpoint × effect), tenancy isolation tests, approval-integrity tests, SSRF
negative tests, and persistence round-trip tests.

### G-18 — No tenant isolation enforcement

**Current:** tenant level exists as a vocabulary (`TenantLevel`) and bridges the kernel
registry, but no endpoint filters or asserts tenant scope.

**Impact:** cross-directorate and cross-hospital operational access is possible, violating
the platform's tenancy constitution.

**Required:** ABAC scope assertion on every read and write (actor tenant must dominate
target tenant), plus negative tests proving isolation.

## 3. Prioritization logic

Ordering is driven by **irreversibility**, not effort:

1. **G-02, G-03** are small (S) and close live abuse paths that produce bogus audit records
   or outbound network access. Do first.
2. **G-01, G-18** are the authorization/tenancy foundation; doing them after persistence
   would require reworking every endpoint twice.
3. **G-04** is large (L) and unblocks everything downstream; it must land before release
   gates and incidents, which need history.
4. **G-05** is not a phase — it is a condition attached to every phase. No phase may close
   without its tests.
5. **G-06, G-09, G-10** deliver the operational value; they require G-04 and G-05.

## 4. Explicit non-goals

The following are **not** gaps and must not be "fixed" into existence:

| Non-goal | Reason |
|---|---|
| Reimplement CI/CD | ADR-018: orchestrate, do not replace |
| Reimplement observability (Prometheus/Grafana/OTel) | Already provided platform-wide |
| Reimplement secret storage | Kernel `SecretsLoader` is authoritative |
| Clinical decision support | Constitutionally excluded from GOC |
| GLOSI registry mutation | GLOSI is an independent governance layer |
| A general-purpose workflow BPM engine | Scope creep; workflows are limited to operational runbooks |

## 5. Gap → phase mapping

| Phase | Closes | Gate to exit |
|---|---|---|
| P0 Containment | G-02, G-03, G-15 | Abuse paths closed; tests green |
| P1 Authorization | G-01, G-18, G-14 | Role×endpoint matrix enforced + tested |
| P2 Durability | G-04, G-13, G-11, G-17 | Restart-survival + multi-worker tests green |
| P3 Release safety | G-06, G-08, G-16 | Gate enforcement + auto-halt tests green |
| P4 Incidents & change | G-09, G-10, G-12 | SEV lifecycle + change workflow tested |
| P5 Dashboard completeness | G-07 | No placeholder sections remain |

Full acceptance criteria: [08](08_ROADMAP_AND_ACCEPTANCE.md).
