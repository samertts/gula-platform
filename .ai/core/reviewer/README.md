# Reviewer Engine (GULA-REVIEWER-001)

The independent engineering verification authority. Reviews every Builder
output before acceptance and reviews the repository itself, producing
deterministic PASS / PASS_WITH_WARNINGS / REJECT verdicts. Never writes
production features; it only validates.

## Areas

| Area | Module | Responsibility |
|---|---|---|
| architecture | `architecture_review.py` | Layering, SOLID/DI, module boundaries, ADRs, constitution |
| code | `code_review.py` | Unsafe patterns, dead code, duplication, complexity, naming, imports |
| security | `security_review.py` | Secrets, auth wiring, encryption, TLS, audit log, dependencies |
| tests | `test_review.py` | Suite presence, service-to-test mapping, assertion quality |
| deployment | `deployment_review.py` | Docker HEALTHCHECK, non-root USER, CI gates, rollback docs |
| documentation | `docs_review.py` | Core docs, API docs, ADRs, security docs, stale files |
| performance | `performance_review.py` | Caching, N+1, pagination, indexes, lazy loading |
| knowledge | `knowledge_review.py` | Registry, index, engine READMEs, skill/playbook layers, brain |

## Commands

All commands are reachable through `python scripts/kernel.py reviewer-<cmd>`
and `python scripts/reviewer.py <cmd>`:

- `reviewer-audit` — Phase 0, write `REVIEWER_AUDIT_REPORT.md`
- `reviewer-review` — run all eight areas and persist the verdict
- `reviewer-area <area>` — review one area
- `reviewer-gate` — 0 (pass) / 1 (reject) for CI acceptance
- `reviewer-report` — write `REVIEWER_IMPLEMENTATION_REPORT.md`
- `reviewer-check` — all self-checks
- `reviewer-<area>` — per-area shortcuts

## Decision Model

- `core.py` weights areas (security 0.20, architecture 0.15, code 0.15, tests
  0.15, knowledge 0.10, deployment 0.10, documentation 0.10, performance 0.05).
- Severity penalties: LOW 2.0, MEDIUM 5.0, HIGH 15.0, CRITICAL 30.0.
- Any HIGH/CRITICAL finding rejects its area. Any rejected area rejects the
  whole review. Systemic debt is aggregated per area so known baselines do not
  drown out regression signals.

## Independence

- The Reviewer composes Kernel primitives only (findings, severity, state).
- It never imports the Builder and never modifies production code.
- Every verdict is reproducible: same repository in, same verdict out.
