# 05 — Security & Governance

**Program:** GOC Discovery & Design
**Status:** DISCOVERY — findings only; no remediation implemented
**Date:** 2026-11-15
**Classification:** Internal — contains exploitable findings

---

## 1. Summary

Seven security findings were identified in the live `/control-plane` surface. Four are
**Critical** (F-01…F-04). Because the router is registered in the application factory, all
findings are reachable in the current build by any authenticated user.

| ID | Finding | Severity | CWE |
|---|---|---|---|
| F-01 | Missing function-level authorization on all 21 endpoints | Critical | CWE-862 |
| F-02 | Approval/deployer identity taken from request body; self-approval | Critical | CWE-290 / CWE-639 |
| F-03 | SSRF via caller-supplied component health endpoint | Critical | CWE-918 |
| F-04 | Non-durable operational state (integrity/recovery) | Critical | CWE-664 |
| F-05 | Inconsistent/unverified audit emission on mutating paths | High | CWE-778 |
| F-06 | No tenant-scope enforcement (cross-tenant administration) | Critical | CWE-863 |
| F-07 | Unvalidated free-form request bodies (`dict[str, Any]`) | Medium | CWE-20 |

## 2. Findings

### F-01 — Missing function-level authorization

**Evidence:** `routes.py` defines `_user(request_user=Depends(get_current_user))` and every
one of the 21 endpoints depends on `_user`. No endpoint uses `require_permission`,
`require_admin`, or any role check.

**Attack:** an authenticated `technician` (lowest operational role) calls
`POST /control-plane/releases/deploy`, `POST /control-plane/policies`, or
`PUT /control-plane/config/global/<component>` and changes platform behavior.

**Impact:** total loss of the operational authorization boundary. The most privileged
operations in the platform are reachable from the least privileged session.

**Required control:** deny-by-default permission gate per endpoint; permission catalog
(`control_plane:read|register|configure|policy|release|deploy|fleet|audit`); role→permission
mapping approved by governance; negative tests for each role.

### F-02 — Approval identity spoofing and self-approval

**Evidence:**

```python
user_str = data.get("user", "unknown")
if data.get("approve_first", False):
    approved = sdk.releases.approve(release_id, user_str)
release = await sdk.releases.deploy(release_id, user_str)
```

**Attack:** caller supplies `{"user": "chief.architect", "approve_first": true}`. The
approval is recorded under a name the caller chose, in the same request that deploys.

**Impact:** separation of duties is void. The audit trail asserts an approval that never
happened. This is the single most dangerous finding for clinical governance: a release that
affects laboratory result handling can appear properly approved.

**Required control:** principal identity derived only from the authenticated token; approval
recorded with subject, role, tenant, timestamp, and request correlation ID; approval and
deployment as separate permissions *and* separate requests; self-approval rejected by rule;
optional quorum (two distinct principals) for production channel.

### F-03 — SSRF via component health endpoint

**Evidence:** `HealthAggregator.check_component` fetches `comp.health_endpoint` with `httpx`;
the value originates from the registration request body.

**Attack:** register a component with
`health_endpoint: "http://169.254.169.254/latest/meta-data/"` or an internal admin service,
then call `GET /control-plane/health` to trigger the fetch. Response content is returned in
`ComponentHealth.details`.

**Impact:** internal network reconnaissance, metadata credential exposure, interaction with
adjacent services, and a serialized-fetch denial-of-service (5 s timeout per component).

**Required control:** probe allowlist from deployment configuration; scheme restricted to
`http`/`https`; DNS resolution checked against private/loopback/link-local/metadata ranges;
redirects disabled; bounded concurrency; per-target circuit breaker; timeouts enforced;
response size capped; response body never returned to callers (status + latency only).

### F-04 — Non-durable operational state

**Evidence:** no concrete tables, no migrations; managers hold `dict` state in singletons.

**Impact:** after restart the GOC reports an empty platform (or worse, contradicts reality);
audit entries reference components that no longer exist; multi-worker deployments diverge;
disaster recovery cannot reconstruct operational decisions.

**Required control:** persisted models + migrations; append-only history; startup
reconciliation against the real system; explicit "unknown state" rather than empty-but-green
reporting.

### F-05 — Inconsistent audit emission

**Evidence:** 11 control audit actions exist in `audit.py`; there is no single choke point
guaranteeing emission on every mutating endpoint.

**Impact:** an operation can succeed without an audit record — the failure mode that matters
most in a regulated environment.

**Required control:** audit on the write path (transactional outbox or equivalent), not
per-handler; a test asserting every mutating endpoint produces exactly one audit entry;
reject the operation if the audit write fails.

### F-06 — No tenant-scope enforcement

**Evidence:** `TenantLevel` exists; no endpoint asserts tenant dominance.

**Impact:** a directorate operator can read or mutate another directorate's components,
configuration, and releases. Violates national tenancy isolation requirements.

**Required control:** ABAC scope assertion on every read/write (`actor_tenant ⊒ target_tenant`);
tenant stamped on every persisted row; negative isolation tests (the platform already has a
tenant-isolation matrix for other surfaces — reuse it).

### F-07 — Unvalidated request bodies

**Evidence:** handlers take `data: dict[str, Any]` and index keys directly
(`data["component"]`, `data["name"]`), producing 500s on malformed input and offering no
schema in OpenAPI.

**Impact:** weak contract, poor client experience, unhandled exceptions, and loss of
generated-client safety.

**Required control:** Pydantic request models with strict fields and constraints; explicit
422 behavior; schema visible in OpenAPI; generated client regenerated.

## 3. Governance requirements

| Requirement | Why |
|---|---|
| Two-person rule for production channel | Single-call approval defeats separation of duties |
| Immutable approval record with correlation ID | Post-incident reconstruction |
| Explicit permission catalog approved in ADR | Prevents ad-hoc privilege growth |
| Tenant dominance rule encoded once, reused | Eliminates per-endpoint inconsistency |
| Deny-by-default | New endpoints must opt into access, not out |
| Clinical-safety interlock | Release cannot advance while clinical safety state is degraded |

## 4. Threat model (abbreviated STRIDE)

| Threat | Vector | Mitigation |
|---|---|---|
| Spoofing | F-02 body-supplied approver | Principal from token only |
| Tampering | F-01 unauthorized policy/config writes | Permission gate + audit + versioning |
| Repudiation | F-05 missing audit | Write-path audit, fail-closed |
| Information disclosure | F-03 SSRF; broad read endpoints | Probe allowlist; tenant scoping |
| Denial of service | serialized probes; unbounded deploy requests | Bounded concurrency; rate limits; circuit breaker |
| Elevation of privilege | F-01, F-06 | Deny-by-default + tenant dominance |

## 5. Alignment with platform security constitution

| Constitution requirement | GOC obligation |
|---|---|
| OWASP ASVS / API Top 10 | Function-level authorization (API1/API5), SSRF prevention (API7), input validation (API3) |
| Least privilege | Explicit per-endpoint permissions |
| Defense in depth | Auth gate + tenant scope + audit + gate enforcement |
| Zero trust | No implicit trust from network position or session type |
| Immutable audit | Hash-chained shared audit; fail-closed on audit failure |
| Multi-tenancy | Tenant dominance on every operation |

## 6. Residual risk statement

Until P0 and P1 of the roadmap complete, the `/control-plane` surface must be considered an
**untrusted administrative interface**. It must not be exposed to non-administrative
accounts, and any deployment that exposes it beyond a controlled network is accepting
Critical residual risk.

## 7. Interim containment options (decision required, not implemented)

These are options for the Program Director. This package does not implement any of them.

| Option | Effect | Cost | Reversibility |
|---|---|---|---|
| A. Remove router registration | Surface disappears entirely | 1-line change | Trivial |
| B. Gate the router behind admin-only dependency | Blocks F-01/F-06 abuse; F-02/F-03 remain | Small | Trivial |
| C. Restrict by network/reverse-proxy policy | Reduces exposure; does not fix in-app flaws | Ops change | Trivial |
| D. Proceed directly to P0 fixes | Closes F-02/F-03/F-05 properly | Small | Trivial |

**Recommendation:** B + D in the same change window; A if the surface is not yet needed in
production. Do not select C alone — it hides the flaws rather than removing them.

## 8. What this document does not do

It does not remediate. No code, route, migration, or configuration was changed. Findings are
inputs to [ADR-026](../adr/ADR-026-global-operations-center.md) and to the P0/P1 gates in
[08](08_ROADMAP_AND_ACCEPTANCE.md).
