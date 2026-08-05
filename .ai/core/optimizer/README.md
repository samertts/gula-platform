# Optimizer Engine (GULA-OPTIMIZER-001)

Continuously improves the entire platform without changing business
behavior. It never changes functional requirements — it improves
implementation quality only: performance, scalability, reliability,
maintainability, developer experience, and resource efficiency, always
preserving correctness. Baseline metrics enter the engine from deterministic
repo evidence; verified optimizations feed back to the Reviewer and the
Learner.

## Pipeline

audit → analyze → bottlenecks → architecture → resources → dx → debt →
optimize → evolve → validate → report

## Phases

| Phase | Module | Responsibility |
|---|---|---|
| 0 | `audit.py` | System audit -> `OPTIMIZER_AUDIT_REPORT.md` |
| 1 | `analyze.py` | Deterministic performance baseline (11 metrics) |
| 2 | `bottlenecks.py` | Bottleneck detection (12 categories) |
| 3 | `architecture.py` | Architecture recommendations (10 techniques) |
| 4 | `resources.py` | Resource recommendations (10 targets) |
| 5 | `developer_experience.py` | Developer-experience scores (8 dimensions) |
| 6 | `debt.py` | Technical-debt records (7 categories) |
| 7 | `safe.py` | Safe-optimization loop (measure → verify → rollback) |
| 8 | `evolution.py` | Evolution proposals (7 targets) |
| 9 | `quality.py` | Quality validation (6 checks, score) |
| 10 | `report.py` | `OPTIMIZER_IMPLEMENTATION_REPORT.md` |

## Commands

All commands are reachable through `python scripts/kernel.py optimizer-<cmd>`
and `python scripts/optimizer.py <cmd>`:

- `optimizer-audit`, `optimizer-analyze`, `optimizer-bottlenecks`,
  `optimizer-architecture`, `optimizer-resources`, `optimizer-dx`,
  `optimizer-debt`, `optimizer-optimize`, `optimizer-evolve`,
  `optimizer-validate`, `optimizer-report`, `optimizer-run`,
  `optimizer-check`.

The success criterion runs end-to-end without manual intervention:

```
python scripts/kernel.py optimizer-run
```

## Principles

- Never optimize blindly: always measure first, never optimize without evidence.
- Every optimization is measurable, reversible, auditable, and safe.
- Performance must never reduce correctness; security outranks performance.
- Correctness always outranks speed.
- Optimizations never change functional requirements or business behavior.
- Regressions trigger automatic rollback; nothing is applied without
  governance approval (evolution proposals require approval).
- Deterministic, evidence-driven, continuously improving optimization.
