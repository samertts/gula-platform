# ADR-036: Workflow Runtime Retirement (broken national workflow_runtime → canonical engine)

**Status:** Accepted
**Date:** 2026-08-08
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — applies ADR-028 to the `workflow_engine` capability)
**Related:** ADR-028, ADR-029, ADR-031, ADR-032, ADR-035, ADR-024, ADR-011

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

Wave 4 order 19 targets the `workflow_engine` capability (classification §2.12).
The canonical provider is the **live, promoted engine**:

- `backend/app/workflows/engine.py::WorkflowEngine` — 237 LOC, `def_id`-keyed
  definitions (create/activate/status draft→active), `list/get/start_instance/
  submit_approval/cancel_instance/get_pending_approvals`, using `AsyncSession`
  and `app.workflows.models` (WorkflowDefinition/WorkflowInstance/
  WorkflowApproval). Exposed over HTTP at **`/niam/workflows`** via
  `backend/app/identity/workflows/routes.py` (wired through the NIAM router in
  `factory.py`), with a live frontend page (`frontend-v3/src/pages/niam/
  WorkflowsPage.tsx` at route `niam/workflows`).

### Finding #44

`backend/app/national/workflow_runtime/` — a **wired-but-broken** duplicate
workflow runtime:

- `api/routes.py` exposes **20 endpoints** under `/national/workflows/*`
  (definitions CRUD + execute, executions, approvals, templates, stats,
  health).
- `application/service.py` is **0 bytes** — so every handler's
  `_get_service()` lazy import (`WorkflowRuntimeService`) raises `ImportError`
  and every route returns HTTP 500.
- The package reimplements (by shadowing) the canonical `WorkflowEngine`
  surface, but provides no functioning behavior: no service implementation,
  no ORM-bound execution path reachable at runtime.

**Behavioral equivalence:** the finding is broken. Archiving it removes a
wired **500-surface** and re-points consumers at the live canonical
`/niam/workflows` surface. No working behavior is lost; the only change is
positive (a broken HTTP surface disappears).

**Consumer inventory (complete):**
- Backend: only `backend/app/factory.py` (lines 635-637) imports the router;
  `backend/app/platform/workflow.py` is dead code that lazily imports
  `WorkflowRuntimeService` (never imported anywhere — verified repo-wide; its
  lazy import would fail against the broken package anyway).
- Frontend: the national page
  `frontend-v3/src/pages/national/workflow-runtime/
  NationalWorkflowRuntimeApiPage.tsx` calls `/national/workflows/*` (currently
  500); the generated client
  `frontend-v3/src/api/generated/client.ts` has a `national.workflow_runtime.api`
  section (API object + hooks) referenced by nothing else; nav entry
  `frontend-v3/src/permissions/index.ts` (`/national/workflow-runtime`).
- Scripts: `scripts/generate_frontend_client.py` module registry and
  `scripts/zero_drift_engine.py` nav metadata reference the module.
- Docs: WORKFLOW_CATALOG.md, MODULE_DEPENDENCY_MATRIX.md,
  DIGITAL_DNA_ATLAS.md, EXTENSION_GUIDE.md, MASTER_REMAINING_WORK.md.

**No client depends on the 500 responses.** The single frontend consumer of
the broken surface shows errors today; the canonical `/niam/workflows` page is
live and replaces it.

## Decision

Archive the broken `national/workflow_runtime` package and re-point consumers
to the canonical engine, per ADR-028 and ADR-029:

1. **Archive the whole package**, history preserved via `git mv` to
   `archive/platform-shared-core/` as flat, named files
   (`national_workflow_runtime_*.py`) following the Commit 1.14 convention
   (whole-`national/workflows/` package archive). A header docstring on each
   archived file records the source path, the finding, and reversibility.
   The 0-byte `application/service.py` (the finding's evidence) is archived
   with a header documenting the 0-byte state.
2. **Remove the factory wiring** (`factory.py` include of the workflow router):
   the `/national/workflows/*` 500-surface disappears from the app.
3. **Archive `backend/app/platform/workflow.py`** — dead code (zero importers)
   that would break against the removed package; preserved as
   `archive/platform-shared-core/platform_workflow.py`.
4. **Re-point the frontend client.** The broken national page
   (`national/workflow-runtime`) is removed; the canonical page
   `/niam/workflows` (NiamWorkflowsPage) already exists, is wired, and is the
   single workflow management surface. Generated client section, nav entry,
   and the generator/zero-drift registries are updated atomically in the same
   commit.
5. **No schema change, no data change.** The `national_workflow_*` tables were
   never reachable (the service was 0 bytes); no migration exists. Canonical
   `workflow` tables are untouched.
6. **ADR-028 Rules 1-7 apply verbatim.** The commit preserves behavior, carries
   evidence, keeps the backend authoritative, produces a Migration Impact
   Report, stays reversible via a single `git revert`, and executes one commit
   at a time with a stop for approval.

The first application is Commit 3.6, resolving finding #44 (31 → 30).

## Alternatives Considered

### A. Do nothing (keep the 500-surface)

Rejected. The surface is broken and returns 500 for every call. It shadows the
canonical engine in the scan and keeps a wired non-functional surface in the
national layer. The classification and ADR-028 demand evidence-based
retirement of broken duplicates.

### B. Re-point the routes to the canonical `/niam/workflows` engine

Rejected. The canonical engine and the broken runtime have different
contracts (def_id-keyed definitions + instances vs type-keyed definitions +
executions). Re-writing the broken router to call the canonical engine would
create a second, non-authoritative HTTP surface duplicating `/niam/workflows`
and maintain two workflow APIs forever. The canonical surface already exists;
clients re-point to it directly.

### C. Promote `national/workflow_runtime` into canonical and complete it

Rejected. The canonical `WorkflowEngine` is live and complete. Promoting a
0-byte stub backwards would downgrade the canonical provider and recreate the
finding (same reasoning as ADR-031 alternative C).

### D. Re-point the `/workflow-engine` capability scaffold

Rejected. `backend/app/capabilities/workflow_engine/` is itself a stub
(hardcoded dict responses, abstract repository with no concretion); it is not
a functioning canonical target.

### E. Keep the broken page and re-point its API calls

Rejected. The national page only ever rendered 500s; a live canonical page
already exists at `/niam/workflows`. Keeping a second page that calls a
non-existent surface adds dead UI.

## Consequences

**Positive**

- The `workflow_engine` Shared Core capability has exactly ONE live
  implementation: the canonical `WorkflowEngine` at `/niam/workflows`.
- The acknowledged-findings baseline shrinks (31 → 30) and never re-opens the
  duplicate.
- A wired 500-surface (20 routes) is removed from the national layer; boot
  route count and OpenAPI shrink by the documented delta (expected, NOT a
  byte-identical regression).
- Dead code (`platform/workflow.py`) and dead UI/registry entries are removed
  with evidence.

**Negative**

- Any out-of-repo client that called `/national/workflows/*` directly would
  break (the only in-repo client is the removed national page; it returned 500
  today). The canonical `/niam/workflows` surface is the replacement.
- The national workflow runtime domain types, enums, ABCs, and repositories
  are archived (not available under `app.national.workflow_runtime`); they are
  preserved verbatim in `archive/platform-shared-core/` for provenance and
  reversibility.

**Neutral**

- Canonical workflow tables, the `/niam/workflows` API, and the NIAM
  WorkflowsPage are unchanged.
- The `workflow_engine` scan rule's remaining signal
  (`class ... WorkflowEngine`) matches only the canonical allowlist path
  (`backend/app/workflows`), which the gate exempts.

## References

- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-031 — Audit Re-Point to Canonical (`docs/adr/ADR-031-audit-repoint-canonical.md`)
- ADR-035 — Rule Engine Promotion (`docs/adr/ADR-035-rule-engine-promotion.md`)
- `backend/app/workflows/engine.py` — canonical `WorkflowEngine`
- `backend/app/identity/workflows/routes.py` — `/niam/workflows` HTTP surface
- `backend/app/national/workflow_runtime/` — archived package (finding #44)
- `archive/platform-shared-core/` — archive convention (Commit 1.14, orders 16/17)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (`workflow_engine`)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — §2.12 (#44), Wave 4 table
