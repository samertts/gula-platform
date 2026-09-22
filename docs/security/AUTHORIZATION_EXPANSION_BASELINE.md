# Authorization Expansion — Phase 0 Baseline

## Raw baseline

```
HEAD:      16fdddfe04c99be671b125c0f741a1e21737c9a8
Branch:    claude/mustafa-parallel-engineering
Git status: clean
Migration: single head, 20260908_0005
Registered routers (app.include_router(...) in app/factory.py): 89
```

No large suite was re-run for this baseline (per this pass's test
policy — only targeted verification below). The last full focused-tier
run (previous continuation) was 320 passed / 4 skipped; unaffected since
no code has changed since then.

## Existing capability/authorization documentation found and reconciled

`docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md` (55KB, pre-existing,
not written this pass) is the canonical design document for Platform
Authority. Its own Section 16 is explicitly titled "NO IMPLEMENTATION
(confirmation)" — it is a design/reconciliation document, not a claim
that its full conceptual hierarchy is built. Per this pass's own Phase 1
instruction ("do not claim an implemented hierarchy merely because the
architecture document describes it"), only what is independently
confirmed against real code below is treated as VERIFIED.

**VERIFIED distinct today (re-confirmed by direct code read this pass,
not merely cited from the doc): three non-overlapping authorization
axes actually exist in this codebase**:

1. **Platform Authority** — `app/identity/platform_authority/` — 4 real
   capabilities (`PlatformCapability` enum:
   `platform.federation.manage`, `platform.trust.manage`,
   `platform.certificates.manage`, `platform.governance.manage`),
   resolved via `require_platform_capability(actor, db, capability)`
   (`app/identity/platform_authority/authorization.py`) — fail-closed,
   identity from the session-resolved actor only, capability from a
   caller-supplied constant only, never client input.
2. **Organization RBAC (NIAM)** — `AuthorizationDecisionService` +
   `Membership`/`RolePermissionService` — resolves role+permission
   within an `organization_id`; denies when absent outside
   `NON_ORGANIZATIONAL_READS`.
3. **Legacy monolith tenant isolation** — `current_user.lab_id` /
   `require_permission(...)` (`app/security/dependencies.py`) — the
   mechanism behind every one of this session's own vertical-slice
   audits (Laboratory, Imaging, EMS, Nursing, NHDW, Payments, Devices,
   Biomedical, Command Center, Public Health).

These three are additive, never substitutive — confirmed by direct
code read, not assumed from the architecture doc's prose.

## What actually changed since the last continuation

Nothing in code. This is a discovery-only pass; see
`docs/security/AUTHORIZATION_COVERAGE_MATRIX.md` and
`docs/security/AUTHORIZATION_GAP_REGISTER.md` for the inventory itself.
