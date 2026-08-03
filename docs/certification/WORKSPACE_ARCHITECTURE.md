# Workspace Architecture & Domain Dependency Graph — PROGRAM-STABLE-002

> Generated: 2026-08-02

## Workspace model

One identity platform (NIAM) → multiple workspaces, one active per login session:

| Workspace | Routes prefix | Login scope | Permissions |
|---|---|---|---|
| Citizen | `/citizen*`, `/r/{token}`, `/patient-card*` | `citizen` / `patient` | read-only own data |
| Laboratory | `/orders /patients /samples /test-results /qc /lims /labs /alerts /stats /dashboard` | staff roles | role-scoped |
| Administration | `/admin*`, `/service-accounts`, `/tiers` | platform + lab admins | platform:* |
| Identity (NIAM) | `/mfa*`, `/auth*`, `/identity*`, `/notifications*` | all users | system:admin for governance |
| National/Government | `/national*`, `/national-data*`, `/nhdw*` | ministry roles | hierarchy-scoped |
| Enterprise (dormant) | `/hospital /pharmacy /radiology /blood-bank /edge /financial` | system:admin | gated |

Permissions never leak between workspaces: each route carries `require_permission` bound to the
shared RBAC vocabulary; frontend guards mirror identically (0 drift).

## Domain dependency graph (active layer)

```
                ┌──────────────────────────────┐
                │        SHARED CORE           │  rbac, identity, audit, security,
                │  (shared/ + backend/app/core)│  cache, events, health, barcode
                └──────────────┬───────────────┘
                               │ (imports only — no reverse edges)
   ┌─────────┬─────────┬───────┴──────┬──────────┬────────────┐
   │  lab    │  ehr    │   nursing ──▶│  ehr     │  citizen   │
   │ (lims)  │         │   (write ctr)│          │  platform  │
   └─────────┴─────────┴──────────────┴──────────┴────────────┘
        (all other domains are leaf contexts; see scan)
```

- L2 circular dependencies: **0**
- Cross-domain edges: 5 (all → EHR; 4 read contracts, 1 flagged write)
- Business-layer cross-context imports (P6 harness): **0**

## Verdict

**Workspace isolation: PASS. Zero cross-domain administration. Shared Core unique.**
