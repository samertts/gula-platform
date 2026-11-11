# Verification Impact Model

Workstream 6. Analysis of `self_audit_agent.py`'s verification-selection
problem, building on the concrete fix already shipped in Phase 10.7.5 (the
`IMPORT_MATCHED` tier). No further code change is made in this workstream
— the one safely, immediately actionable improvement identified
(parallel test execution) requires a new dependency, which is explicitly
out of this workstream's authority to add unilaterally (see below).

## Current state (as of this session)

Three tiers, in order, in `_select_impact_aware_tests`/`_verify_after_fix`:

1. **`TARGETED`** — exact `tests/test_<stem>.py` naming match.
2. **`IMPORT_MATCHED`** (added Phase 10.7.5) — reverse-dependency `grep`
   for any test file that imports the changed module directly, even
   without the naming convention.
3. **`UNKNOWN_broadened_to_full_suite`** — the full `pytest tests/` run,
   300s timeout, preserved and never removed.

Every changed file is also now `py_compile`-checked directly (Defect A's
fix), never a fixed stand-in.

## Measured impact of the `IMPORT_MATCHED` tier

Checked against every real F401 candidate in `backend/app/` (54 files,
this session's snapshot): **3 of 54** (5.6%) had no exact `test_<stem>.py`
but DID have `IMPORT_MATCHED` coverage (`app/middleware.py`,
`app/payments/fx_routes.py`, `app/payments/models.py` — all exploited in
the Workstream 5 field report, all resolved in 2.6s–31.9s instead of a
300s-budget full-suite run). The remaining candidates (e.g.
`app/core/hybrid_router.py`) are imported by **nothing** in `tests/` —
confirmed via the same reverse-dependency search, not assumed — and
correctly still require the full suite.

**This is the real, measured ceiling of a static-import-based approach**:
it can only help a file that some test already imports by name. It cannot
help a file with genuinely zero test coverage — no static analysis can
invent test coverage that doesn't exist.

## Options considered for the remaining gap (full-suite ≈346s vs. 300s budget)

| Option | Verdict | Reasoning |
|---|---|---|
| Increase the timeout | **Rejected** (explicitly, per this workstream's own instruction) | Papers over the gap instead of narrowing it; the full suite's real runtime will keep growing as the codebase does |
| Remove the full-suite fallback | **Rejected** | The whole point of the fallback is "unknown impact is never treated as safe to skip" — removing it converts a slow-but-safe path into a fast-but-unsafe one |
| Better reverse-dependency analysis (import graph, not just direct imports — e.g. transitively, A imports B imports C, test only imports A) | **Proposed, not implemented** | Real potential gain, but transitively walking the whole import graph statically (without executing anything) risks false confidence: a transitive import doesn't prove the test actually *exercises* the changed code path, only that the module loads. Would need real evaluation against false-negative risk before trusting it — not done here without that evidence |
| Route-to-test / domain-to-test mapping (e.g. group by top-level package) | **Rejected as a distinct mechanism** | Would be *less* precise than the existing import-based match (a coarse "same package" grouping can both over-select unrelated tests and under-select a test in a different package that happens to import the changed file) — no evidence it beats what's already built |
| Coverage-based cached test selection (build a real file→test map from one full instrumented run, e.g. `pytest --cov`, cache it, invalidate on suite changes) | **Proposed, not implemented** | The most *precise* option in principle (actual runtime execution coverage, not static imports) — but requires either a new dependency (`pytest-cov`, "No unnecessary package installation" per this operation's own resource rules) or an already-available one (checked: not installed) and a cache-invalidation strategy (stale cache after tests/source change = false confidence, arguably worse than the static-import tier at the moment). Left as a legitimate, evidence-backed future direction, not built speculatively |
| Test partitioning / safe parallel execution (`pytest-xdist -n auto`) | **The single most promising option, not implemented** | 4 CPUs available (checked: `nproc` → 4); parallelizing the full suite would very plausibly bring 346s under the 300s budget without touching a single test's logic or assertions — same verification standard, just faster wall-clock. **Requires a new dependency** (`pytest-xdist` — confirmed not installed via `pip show`). Adding a new package to `backend/requirements*.txt` is explicitly outside "no unnecessary package installation," and is exactly the kind of dependency-management change this operation's own resource rules ask to avoid deciding unilaterally. **Recommended as the concrete next step, pending an explicit decision to add the dependency** — this is the one item in this analysis with a clear, low-risk, high-confidence payoff if authorized |

## What this workstream did NOT do (and why)

- Did not add `pytest-xdist` or any other new dependency — flagged as the
  clear next step above, but adding it wasn't authorized by this pass and
  isn't a "smallest reversible" call to make unilaterally for a
  production backend's dependency manifest.
- Did not implement transitive import-graph analysis or coverage-based
  caching — both have real, unresolved false-negative/staleness risks
  that would need to be evaluated with evidence, not assumed away for
  the sake of building something.
- Did not re-measure the full suite's exact current runtime in this
  workstream (already measured precisely in Phase 10.7: 345.66s,
  2937 passed / 27 skipped / 1 pre-existing unrelated failure) — re-running
  an unchanged full suite for an unchanged timing question is exactly the
  "do not repeat already-proven tests" case this operation's own resource
  rules ask to avoid.

## RESULT

**PARTIALLY VERIFIED.** The one improvement already shipped
(`IMPORT_MATCHED`) is measured and real (3/54 candidates helped, 0 false
positives across all Workstream 5 usage). The remaining gap's best next
step (parallel execution) is identified with a concrete, checked
technical basis (4 CPUs available, dependency confirmed absent) but not
implemented, since it requires a dependency-management decision outside
this workstream's unilateral authority. No verification standard was
weakened to produce this result.
