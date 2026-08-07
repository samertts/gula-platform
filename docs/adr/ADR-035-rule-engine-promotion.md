# ADR-035: Rule Engine Promotion (ExpressionEngine → shared/rules_engine)

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — applies ADR-029 to the rule_engine capability)
**Related:** ADR-028, ADR-029, ADR-024

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

Finding **#43** targets the `rule_engine` capability:

- **Current implementation (the finding):**
  `backend/app/national/rules_engine/domain/expression_engine.py` —
  `ExpressionEngine.evaluate_rule` (234 LOC, complete).
- **Canonical provider:** `shared/rules_engine` — currently holds **domain
  types only** (`domain/entities.py`, `domain/enums.py`). It has **no engine**
  implementation.
- **Behavioral equivalence:** the finding is the **ONLY real `evaluate_rule`
  in the platform**. `backend/app/kernel/rules_runtime.py` consumes the shared
  domain types but implements its own execution loop; there is no competing
  rule engine implementation to promote or preserve.

This is therefore **not a removal** (nothing is dead) and **not an archive**
(no duplicate canonical engine exists). It is a **Canonical Provider
Promotion** (ADR-029): the live, complete implementation is the only candidate
to become the canonical rule engine, so it must be promoted into the
designated canonical path.

The canonical ownership of the Rule Engine is being changed, so this decision
is recorded as an ADR (Documentation Policy).

## Decision

Promote `ExpressionEngine` (with its `EvaluationResult` companion) from
`backend/app/national/rules_engine/domain/expression_engine.py` into the
canonical provider `shared/rules_engine/engine.py`, per ADR-029:

1. **Live code is promoted, not archived.** `git mv` the implementation into
   `shared/rules_engine/engine.py` (history preserved). Behavior travels
   intact; the only source edits are dependency imports re-pointed from the
   national package to the Shared Core domain types it already re-exports.
2. **The canonical provider becomes self-contained.** The promoted engine
   imports its types from `shared.rules_engine.domain.*` (already the
   authoritative definitions) and `from datetime import UTC` — it never
   imports from `app.*`, so Shared Core keeps the correct dependency
   direction (no kernel → domain dependency).
3. **The route/API layer stays where it is.** The live
   `/national/rules/*` surface (11 endpoints in
   `national/rules_engine/api/routes.py`) remains domain-owned and consumes
   the canonical engine through the existing application service.
4. **All in-repo consumers are re-pointed atomically** in the same commit:
   `application/service.py`, `domain/simulation.py`, and the package
   `__init__.py`. No compatibility facade is created under the old module
   path (`app.national.rules_engine.domain.expression_engine` is vacated).
   The package-level public surface (`from app.national.rules_engine import
   ExpressionEngine`) continues to work via re-export from the canonical
   engine — this is the package's public API, not a duplicate module path.
5. **Dormant canonical shells are left untouched.** `backend/app/rules` does
   not exist; no shell is affected.
6. **ADR-028 Rules 1–7 and ADR-029 Rules 1–6 apply verbatim.** The promotion
   commit preserves behavior, carries evidence, keeps the backend
   authoritative, produces a Migration Impact Report, stays reversible via
   single `git revert`, and executes one commit at a time with a stop for
   approval.

The first application is Commit 2.1, resolving the `rule_engine` finding
(38 → 37) by ownership correction.

## Alternatives Considered

### A. Archive-and-repoint

Rejected: the canonical provider has no engine to re-point to. Archiving the
only real `evaluate_rule` would delete working behavior and leave
`shared/rules_engine` as types-only forever — the finding would not be
resolved, only renamed.

### B. Reimplement the engine inside shared, then archive

Rejected: this duplicates a complete, working engine (write a new one to
replace one that already works) with no behavior gain, and it recreates the
finding in new code before deleting the old. Promotion carries the proven
implementation instead of re-inventing it.

### C. Register the national engine as canonical by exception

Rejected: whitelisting `app.national.rules_engine.domain.expression_engine`
as canonical without moving it would keep Shared Core implementation inside a
domain (inverted dependency, domain-sovereignty violation) and require a
constitution exception. Moving the code to the already-designated canonical
path achieves the same finding reduction with no exception.

### D. Promote the engine but keep a facade at the old module path

Rejected: ADR-029 Rule 4 forbids a re-export facade under the vacated module
path — it would re-introduce the duplicate module path. All in-repo consumers
are re-pointed in the same commit instead.

## Consequences

**Positive**

- The `rule_engine` Shared Core capability finally has a real, populated
  canonical provider: `shared/rules_engine` becomes types + engine.
- The acknowledged-findings baseline shrinks by ownership correction
  (38 → 37) and never re-opens the duplicate.
- Domain Sovereignty improves: the national rules engine consumes a Shared
  Core capability instead of implementing it.
- Behavior is preserved exactly — verified by the identical backend suite,
  identical boot route count, and an identical OpenAPI surface (no contract
  change: the `/national/rules/*` API is untouched).

**Negative**

- The old module path `app.national.rules_engine.domain.expression_engine`
  is vacated; any out-of-repo consumer importing it directly would break
  (none exist in-repo; the three in-repo consumers are re-pointed atomically
  in the same commit).
- The canonical package gains ~234 LOC of live implementation, shifting
  maintenance ownership from the national domain to Shared Core (intended).

**Neutral**

- The national package's public surface (`app.national.rules_engine`) keeps
  exporting `ExpressionEngine`/`EvaluationResult` via re-export from the
  canonical engine, preserving package-level compatibility.

## References

- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-024 — Platform Constitution (`docs/adr/ADR-024-Platform-Constitution.md`)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (`rule_engine` → `shared/rules_engine`)
- `shared/rules_engine/` — canonical provider (domain types + promoted engine)
- `docs/baselines/COMMIT_2_1_VERIFICATION_REPORT.md` — execution evidence
