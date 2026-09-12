# ADR-027 — Architectural evidence is derived from authoritative sources, never snapshotted by hand

**Status:** Accepted
**Date:** 2026-09-12
**Supersedes:** nothing
**Related:** NR-069, NR-063, NR-065, NR-066, NR-067, `backend/tests/orm_resolution.py`

## Context

Most of this repository's architecture guards reduce to one predicate:

> Does a migration create this table?

NR-063 (latent create paths), NR-065 (orchestration build preconditions),
NR-066 (the governance audit write), NR-067 (reachable unbuilt reads and
writes) and NR-022's Stable Core all ask it. It decides whether a finding is a
live defect or a latent one, and therefore whether it blocks.

That predicate was answered by a checked-in file,
`docs/architecture/evidence-created-tables.json`, assembled by matching
`op.create_table("literal", ...)` across the migration chain.

## The failure

Three tables are not created that way. `20260814_0002_organization_structure.py`
routes its creates through a local helper:

```python
def _create_if_missing(name, columns, constraints):
    bind = op.get_bind()
    if name in sa.inspect(bind).get_table_names():
        return
    op.create_table(name, *columns, *constraints)
```

The literal is at the **call site**; `op.create_table` receives a parameter. So
`niam_admin_units`, `niam_organization_representatives` and
`niam_organization_ownerships` were recorded as unbuilt while the chain builds
them — and `niam_admin_units` is the target of
`niam_role_assignments.unit_id`, one of the five canonical authorization scopes.

## Root cause

The artifact was **hand-maintained with no generator and no agreement guard.**

A snapshot cannot detect a creation form its author did not model, and nothing
compared it back to the migrations. Eight other non-literal sites (module-level
`_TABLE` constants) had been resolved into the file by hand at some earlier
point, which is itself the symptom: the file was being manually patched toward
correctness instead of derived.

## Decision

**Architectural evidence that can be derived from an authoritative repository
source MUST be derived from it, not snapshotted.**

Concretely:

1. `built_tables()` in `backend/tests/orm_resolution.py` derives from
   `backend/migrations/versions/` and resolves every creation form the chain
   uses — a literal, a module-level string constant, and a local helper that
   forwards one of its own parameters to `op.create_table`.
2. The JSON artifact is retained for consumers outside the test suite and is
   **asserted equal to the derivation**. When they disagree, the migrations are
   right and the artifact is stale.
3. **No guard reads the artifact directly.** Four did; all four now import
   `built_tables()`. A second reader is a second source of truth.
4. The extractor is tested against **synthetic migrations**, one per creation
   form, not only against this repository — so the tests cannot pass by being
   wrong in the same way the chain is, and do not break when an unrelated
   migration is edited.

## Validation

Old method (literal-only, applied today): 411 tables.
Artifact as it actually stood before the repair: 419 tables.
New method (derived): **422 tables**, a strict superset of both.
Difference: exactly the three helper-created tables. No removals, no
provenance changes.

Blast radius, measured by recomputing every consumer under the 419-table
artifact and the 422-table derivation:

| Consumer | Before (419) | After (422) | Verdict |
| --- | ---: | ---: | --- |
| NR-067 reachable unbuilt reads | 418 | 418 | UNAFFECTED |
| NR-067 reachable modules | 20 | 20 | UNAFFECTED |
| NR-067 unbuilt writes | 268 | 268 | UNAFFECTED |
| NR-022 live subject references | 1 | 1 | UNAFFECTED |
| NR-022 Stable Core built | 5 / 5 | 5 / 5 | UNAFFECTED |
| NR-065 orchestration tables built | 0 | 0 | UNAFFECTED |

**No published finding changed.** Nothing on those paths touches the three
tables. That is the honest outcome: a real defect in the evidence base with no
effect on the conclusions drawn from it.

For contrast, a naive literal-only extractor applied today would report 430
reachable reads across 24 modules and 276 writes — figures that were never
published, and are recorded here only to show what the failure mode costs when
it is not caught.

## Impact

- Positive: the predicate has one derivation, one set of tests, and a
  self-check against the artifact. The failure class cannot recur silently.
- Cost: `built_tables()` now parses the migration chain on first call. It is
  `lru_cache`d and the whole derivation is well under a second.
- Precedent: this is the second instance of the same class in this codebase.
  The first was resolving ORM models by bare class name, where 32 names map to
  more than one table (recorded in `orm_resolution.py`). Both were one
  predicate re-implemented per consumer instead of derived once.

## Consequences for future work

When a guard needs a fact about the system:

1. Identify the authoritative source (migrations, AST, the database, the router).
2. Derive the fact from it.
3. Test the derivation against synthetic positive **and negative** cases.
4. If a cached artifact is kept, assert it against the derivation.
5. Never let a second consumer read the cache directly.

A fact that is cheap to derive and expensive to keep correct by hand should
never be kept by hand.
