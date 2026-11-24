# DEPENDENCY GRAPH — PROGRAM-GULA-PARALLEL-001

## Wave A (Discovery) — dependency-free

All 9 agents audit in parallel from the same read-only snapshot. No agent depends on
another agent's report to begin. Write sets are disjoint.

```
Wave A (parallel)
  A01 ─┐
  A02 ─┤
  A03 ─┤
  A04 ─┼──> Wave B (orchestrator consolidation)
  A05 ─┤
  A06 ─┤
  A07 ─┤
  A08 ─┤
  A09 ─┘
```

## Wave B (Consolidation) — orchestrator only

Inputs: all 9 agent reports. Outputs: `MASTER_REMEDIATION_REGISTER.md`, updated
`CONFLICT_REGISTER.md`. No agent participates.

## Wave C (Safe Remediation) — dependency-ordered

```
MASTER_REMEDIATION_REGISTER (approved)
        │
        ├──> A02 design-system fixes ──┐
        ├──> A03 page fixes ───────────┼──> (need A02 shared components stable first
        │                              │    for page-level styling; coordinate via ORCH)
        ├──> A09 independent tests ────┤    (needs target behavior fixed by A02/A03/A08)
        └──> A08 standalone CI/docs ───┘

A01, A04, A05, A06, A07  ──> review fixes; produce protected-change plans (no edits)
```

Dependency rules:
- **A03 depends on A02** for shared component/token changes: pages may not redefine
  tokens locally; A02 must land shared-component fixes first (or explicitly defer).
- **A09 depends on A02/A03/A08** for tests that assert corrected behavior; A09 may write
  independent characterization tests of current behavior at any time.
- **A04/A05/A07 approval gate:** any finding touching auth, clinical logic, API
  contracts, DB, or migrations requires independent approval before an eligible
  remediator may act.
- **No two agents may write the same file at any time** (enforced by ownership matrix).

## Wave D (Integration & Verification) — orchestrator only

```
Wave C outputs (approved only)
   -> diff review
   -> ownership check
   -> conflict/overlap check
   -> gate execution (package-local scripts)
   -> regression check
   -> INTEGRATION_LOG entry
   -> (NO merge to main, NO deploy)
```

## External dependencies (environmental, not program steps)

- Gate execution assumes local toolchains are installed (Node/pnpm for frontend-v3,
  Python for backend). If absent, gates are recorded as `BLOCKED — toolchain missing`,
  not as passed.
- No network fetch, no package installation, no new services, no paid dependencies.
- Git history/migration reconciliation is an **independent high-risk track**: not
  performed in this program beyond re-verification (see PROGRAM_CONTROL §2.6).
