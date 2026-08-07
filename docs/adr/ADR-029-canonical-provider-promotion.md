# ADR-029: Canonical Provider Promotion

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — refines ADR-028 application)
**Related:** ADR-028, ADR-024, ADR-011

---

## Context

The structural migration phase (ADR-028) reduces the 57 acknowledged Shared
Core reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

Commits 1.1 and 1.2 archived provably-dead reimplementations (`platform/`
facades, `identity/events.py`) — the canonical providers for those
capabilities were already live, so archiving the duplicates was correct.

Commit 1.3 targets the `workflow_engine` finding
(`backend/app/identity/workflows/engine.py`). Investigation shows the three
canonical candidate providers for `workflow_engine` are **not behaviorally
equivalent** to the live engine:

- `backend/app/workflows/` is an **empty directory** (no `__init__.py`);
- `shared/workflow/engine.py` is a 75-LOC **synchronous in-memory** engine
  (no persistence, approvals, or DB) with zero runtime importers;
- `app/capabilities/workflow_engine/` is a **stub** whose repository raises
  `NotImplementedError` and whose routes are not registered in `factory.py`.

The live engine is an async, SQLAlchemy-backed engine with persisted
definitions, instances, approvals, and notifications backing the live
`/niam/workflows/*` API. Archiving it would break the persisted API, and no
canonical provider could host it. This is therefore **not a removal** — it is
a **promotion**: the live implementation must become the canonical provider.

The canonical ownership of the Workflow Engine is being changed, so this
decision is recorded as an ADR (Documentation Policy).

## Decision

Adopt **Canonical Provider Promotion** as a recognized migration mode within
ADR-028 for the `workflow_engine` capability, defined as follows:

1. **Live code is promoted, not archived.** The live implementation moves
   (`git mv`, history preserved) into the canonical provider path named by
   `SHARED_CORE_CATALOG`. Behavior travels intact with the moving code.
2. **Models move with the engine.** ORM models travel with the implementation
   so the canonical provider is self-contained; Shared Core never imports
   from a domain.
3. **The route/API layer stays where it is.** Domain-owned API surface
   (`/niam/workflows/*`) remains in its domain and is re-pointed to consume
   the canonical provider (identity → Shared Core, the correct dependency
   direction).
4. **All in-repo consumers are re-pointed atomically** in the same commit;
   no compatibility facade is created under the old namespace (a re-export
   would re-introduce the duplicate module path).
5. **Dormant canonical shells are left untouched.** Non-equivalent shells
   (`shared/workflow`, `capabilities/workflow_engine`) remain dormant,
   pre-existing state; they are not orphaned by a promotion (orphan check
   must PASS).
6. **ADR-028 Rules 1–7 still apply verbatim.** Promotion commits must
   preserve behavior, carry evidence, keep the backend authoritative, produce
   a Migration Impact Report, stay reversible via single `git revert`, and
   execute one commit at a time with a stop for approval.

The first application of this decision is the promotion of
`backend/app/identity/workflows/engine.py` (+ `models.py`) to
`backend/app/workflows/`, resolving the `workflow_engine` finding (52 → 51)
by ownership correction.

## Alternatives Considered

### A. Archive-and-repoint (Commit 1.1/1.2 approach)

Rejected: no canonical provider is behaviorally equivalent to the live
engine. Archiving would break the persisted `/niam/workflows` API or require
a full reimplementation into a shell first — higher risk, higher cost, and
it temporarily deletes working behavior (violates the promotion principle).

### B. Implement the missing canonical provider, then archive

Rejected: this duplicates the live engine (write a new engine to replace one
that already works) with no behavior gain, and it recreates the finding in
new code before deleting the old. Promotion carries the proven
implementation instead of re-inventing it.

### C. Register the live module as canonical by exception

Rejected: whitelisting `app.identity.workflows.engine` as canonical without
moving it would keep Shared Core implementation inside a domain (inverted
dependency, domain-sovereignty violation) and require a constitution
exception. Moving the code to the already-designated canonical path achieves
the same finding reduction with no exception.

### D. Promote only the engine, keep models in identity

Rejected: the canonical provider would then depend on `app.identity.workflows`
(Shared Core importing from a domain), recreating the inversion the promotion
exists to fix. Models must move with the engine.

## Consequences

**Positive**

- The `workflow_engine` Shared Core capability finally has a real, populated
  canonical provider; the catalog's declared owner now matches reality.
- The acknowledged-findings baseline shrinks by ownership correction
  (52 → 51) and never re-opens the duplicate.
- Domain Sovereignty improves: the identity domain consumes a Shared Core
  capability instead of implementing it.
- Behavior is preserved exactly — verified by byte-identical OpenAPI
  (1696 paths) and an identical 4993-test backend suite.
- The migration remains a single-`git-revert` reversible promotion.

**Negative**

- The old namespace `app.identity.workflows.engine/models` is vacated; any
  out-of-repo consumer importing it would break (none exist in-repo;
  consumers were re-pointed atomically in the same commit).
- The canonical package gains ~352 LOC of live implementation, shifting
  maintenance ownership from identity domain to Shared Core (intended).

**Neutral**

- The dormant shells (`shared/workflow/`,
  `app/capabilities/workflow_engine/`) remain in place; their eventual
  consolidation is future work, out of scope for this ADR.

## References

- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-024 — Platform Constitution (`docs/adr/ADR-024-Platform-Constitution.md`)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (`workflow_engine`), `SHARED_CORE_PROVIDER_PREFIXES`
- `docs/baselines/CANONICAL_PROMOTION_PLAN_WORKFLOW_ENGINE.md` — the promotion plan
- `docs/baselines/COMMIT_1_3_VERIFICATION_REPORT.md` — execution evidence
