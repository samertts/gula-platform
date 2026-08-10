# ADR-038: ABAC Route Enforcement on Protected HTTP Routes

**Status:** Accepted
**Date:** 2026-08-10
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — extends ADR-037 Wave B unit B1)
**Related:** ADR-037, ADR-028, ADR-029, PROGRAM_NEXT_PHASE_PLAN (Layer 1 RBAC/ABAC)

---

## Context

Program Next-Phase (ADR-037, `docs/programs/PROGRAM_NEXT_PHASE_PLAN.md`)
defines Layer 1 **RBAC / ABAC** as the authorization foundation for the
national platform. Wave A delivered the certified, deterministic ABAC engine
(`backend/app/security/abac.py`, commit `dcd32500`): fail-closed, explicit
attributes, deterministic `(priority, id)` rule ordering, purpose-of-use,
deque decision log with `on_decision` hook, and **server-derived subject**
(`subject_from_principal` — account vs lab-user token families). Wave A
certified the engine and its unit surface but did **not yet wire the engine to
the HTTP route layer**.

Wave B unit **B1** (authorized by the Program Director) enforces ABAC on
protected HTTP routes. The observed reality on the certified baseline
(`8444f039`):

- FastAPI `create_app()` exposes **2019 effective routes** (route-inventory
  probe via `_IncludedRouter.effective_route_contexts()`); `app.routes`
  itself holds only 118 lazy inclusion proxies.
- Protection today is authentication (`get_current_identity` /
  `get_actor_identity_id`, `backend/app/identity/security.py`) plus a
  per-route `require_permission`/`require_role` RBAC marker where explicitly
  coded. **There is no deterministic ABAC decision layer bound to the HTTP
  surface** — a request authorized by authentication+RBAC is admitted without
  an explicit resource/action authorization decision.
- The NIAM router surface (`backend/app/identity/api/router.py`,
  `prefix="/niam"`) wires **19 subrouters**; conflict-prone routes (account
  lock/unlock, sessions, devices, governance, domains) are today protected
  only by identity/RBAC checks — a token-family **authorization-leakage
  risk** (identity token vs lab token) that ABAC is designed to bind.
- Centralization mechanism verified by probing FastAPI internals: appending
  `Depends` to a subrouter's `dependencies` list after inclusion is **not**
  seen by the flattened dependant tree (FastAPI snapshots `dependencies` at
  `include_router` time); the working mechanism is
  `router.include_router(sub, dependencies=[...])`, which copies
  `[*parent_router.dependencies, *(dependencies or [])]` onto every effective
  route via `_RouterIncludeContext.for_include`.

## Decision

**Bind the certified A1 ABAC engine to every protected HTTP route as a
FastAPI dependency guard**, without a second framework and without changing
any handler logic, route path, method, request/response contract, or OpenAPI
surface.

1. **Resource registry + default policy** (`backend/app/security/
   abac_policies.py`): `NIAM_ABAC_RESOURCES` (18 resources — accounts,
   sessions, devices, auth, workspaces, professional, citizen, governance,
   authorities, domains, users, roles, permissions, audits, notifications,
   workflows, persons, health — each with a deterministic `niam_path_prefixes`
   mapping) and `build_default_abac_rules()`: exactly one **permissive**
   ALLOW rule per resource (`action="*"`, `priority=100`,
   `id="abac.niam.<suffix>.allow"`). The default policy is *allow-by-default
   for the NIAM surface* so that existing behavior is preserved; the ABAC
   decision layer is the **binding hook** where deny rules take precedence
   (deny-overrides) and any new/deny rule added in the future fails closed.
2. **Enforcement dependency** (`backend/app/security/abac_enforcement.py`):
   module-level lazy `_ENGINE` singleton (`get_abac_engine()`, `on_decision`
   logging), `reset_abac_engine()` for test isolation, `method_to_action()`
   (GET/HEAD→read, POST→create, PUT/PATCH→update, DELETE→delete),
   `enforce_abac_decision()` (server-derived `subject_from_principal`;
   authenticated-unauthorized → deterministic **403 `"Access denied"`**;
   `TypeError`/undecidable subject → fail closed to 403; engine errors never
   convert to 500), and the `require_abac(resource, purpose=None)` dependency
   factory marked `checker._abac_guard = True` with `_abac_resource` /
   `_abac_purpose` attached for coverage introspection.
3. **Wiring** (the only modified route surfaces):
   - `backend/app/identity/api/router.py`: each protected subrouter included
     via `router.include_router(sub, dependencies=[Depends(require_abac(
     "niam:<resource>"))])` — **18 subrouters guarded**. The auth subrouter is
     excluded (login/refresh remain public; logout carries an explicit guard).
   - `backend/app/identity/api/auth.py`: `POST /logout` gains
     `Depends(require_abac("niam:auth"))`.
   - `backend/app/domain_platform/routes.py`: router-level dependencies become
     `[Depends(get_current_identity), Depends(require_abac("niam:domains"))]`.
4. **Public/open surfaces are declared, never silently exposed**
   (`backend/app/security/abac_coverage.py`): `PUBLIC_ROUTE_SPECS` (43 specs —
   health, login, refresh, public endpoints) and `OPEN_EXEMPT_ROUTE_SPECS`
   (AI kernel service, LIMS quality, national tasks health,
   document-intelligence, citizen self-service cookie-gated surface).
   `RouteStatus` = public/open_exempt/protected_abac/protected_existing/
   unprotected; `route_coverage_report()` is the deterministic coverage gate
   (zero `unprotected`, zero `missing_abac`).
5. **No schema change, no migration, no frontend change, no handler change.**
   OpenAPI is **byte-identical** before/after (1677 paths / 2006 methods
   verified).
6. **Immutability of the audit trail**: the engine `on_decision` hook records
   every ABAC decision in the engine decision log + structured logs. Persistent
   hash-chained storage of route decisions is **explicitly deferred** to a
   later Wave-B unit (B1 does not alter the audit service).

The guard runs after authentication (401 unchanged for anonymous) and before
the handler; a denial aborts the request with 403 and never reaches business
logic.

## Alternatives Considered

### A. Global ASGI/HTTP middleware decision layer

Rejected. A blanket middleware cannot reliably map `(method, path) →
(resource, action)` for parameterized routes without duplicating FastAPI's
routing resolution, and cannot express per-route purpose/attribute context.
FastAPI dependency guards bind directly to the resolved route and keep the
decision next to the route contract. (Rejected in task analysis; also would
have required a "blanket global middleware" change to `factory.py`.)

### B. Second authorization framework (Oso/OPA/Casbin)

Rejected. Constitution: reuse before build, free/self-hosted first, no new
paid/unnecessary dependency. The certified A1 engine is in-repo, tested, and
deterministic. B1 reuses it verbatim.

### C. Append `Depends` to each subrouter's `dependencies` list after inclusion

Rejected after empirical probe: FastAPI snapshots `dependencies` at
`include_router` time, so post-hoc mutation is invisible to the flattened
dependant tree. The working mechanism is `include_router(..., dependencies=...)`.

### D. Guard only a subset of "conflict-prone" routes

Rejected. Partial coverage recreates the coverage-classification problem and
leaves unprotected routes indistinguishable from exempt ones. B1 guards the
entire protected surface deterministically and declares the small public/open
exemption set explicitly.

### E. Wire ABAC rule persistence (DB) now

Deferred. The default policy is code-defined (deterministic, no migration).
Persistence is planned for a later Wave-B unit; the `require_abac` guard
already accepts rules from any source because it uses the engine's rule store.

## Consequences

**Positive**

- Every protected HTTP route now passes through a deterministic ABAC decision
  (245 protected_abac routes); coverage is machine-checked (2019 effective
  routes, 0 unprotected, 0 missing_abac).
- Token-family leakage on conflict-prone NIAM routes is bound by the
  server-derived ABAC subject, not by per-route ad-hoc checks.
- Fail-closed semantics are uniform: anonymous → 401 (unchanged),
  authenticated-unauthorized → 403 `"Access denied"`, engine error/unknown
  resource/undecidable subject → deny. No security failure converts to 500.
- Zero behavior/contract change: OpenAPI byte-identical; boot routes 118;
  existing HTTP regressions (security-regression, integration-parity) green.
- 22 new B1 regression tests (policy registry, fail-closed, actor-source
  integrity, route-coverage gate, HTTP semantics).

**Negative**

- Any future route added inside a guarded NIAM subrouter automatically requires
  ABAC policy coverage (new routes could be denied if a deny rule is active) —
  this is the intended binding effect.
- The route-coverage registry (`abac_coverage.py`) must be maintained as new
  public/open routes are added (guarded by the coverage gate test, not silent).

**Neutral**

- Default policy remains allow-by-default (behavior-preserving); deny-overrides
  is the documented escalation path.
- Persistent audit-chain recording of route decisions is a later Wave-B unit.

## References

- ADR-037 — Next Program Authority (`docs/adr/ADR-037-next-program-authority.md`)
- PROGRAM_NEXT_PHASE_PLAN.md — Wave B = RBAC/ABAC engine + hierarchy model
- `backend/app/security/abac.py` — certified A1 engine (reused verbatim)
- `backend/app/security/abac_policies.py` / `abac_enforcement.py` /
  `abac_coverage.py` — new B1 modules
- `backend/app/identity/api/router.py`, `backend/app/identity/api/auth.py`,
  `backend/app/domain_platform/routes.py` — wiring points
- `backend/tests/unit/test_abac_route_enforcement.py` — 22 B1 tests
- `docs/programs/WAVE_B_B1_EXECUTION_REPORT.md` — execution + certification report
