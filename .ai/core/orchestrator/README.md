# Orchestrator Engine (GULA-ORCHESTRATOR-001)

The executive brain of the GULA engineering platform. Transforms a single
human objective into a complete, managed engineering workflow — without
writing production code and without performing reviews directly. It
coordinates the other engines (Builder for execution, Reviewer for
verification, Deployer for deployment, Learner for knowledge, Optimizer for
performance, Kernel for primitives).

## Pipeline

classify → plan → route → schedule → execute → verify → deploy → learn → report

## Phases

| Phase | Module | Responsibility |
|---|---|---|
| 0 | `audit.py` | Detect available engines and surfaces -> `ORCHESTRATOR_AUDIT_REPORT.md` |
| 1 | `classifier.py` | Mission type / priority / complexity / risk / duration / specialists |
| 2 | `planner.py` | Program > Phase > Task (max 5 min / 50 files per task) |
| 3 | `router.py` | Assign every task to the engine that owns its surface; record fallbacks |
| 4 | `dependencies.py` | Execution order, parallel groups, critical path, task graph |
| 5 | `checkpoint.py` | Durable save/resume per step; progress is never lost |
| 6 | `failure.py` | Classify failures; retry transient, escalate permanent |
| 7 | `resources.py` | Context/repo/time/memory limits + auto-split advisory |
| 8 | `dashboard.py` | `MISSION_STATUS.md` live view of a running mission |
| 9 | `history.py` | Mission registry, timeline, decision/failure/recovery logs |
| 10 | `report.py` | `ORCHESTRATOR_IMPLEMENTATION_REPORT.md` + mission stats |

## Commands

All commands are reachable through `python scripts/kernel.py orchestrator-<cmd>`
and `python scripts/orchestrator.py <cmd>`:

- `orchestrator-audit`, `orchestrator-mission`, `orchestrator-classify`,
  `orchestrator-plan`, `orchestrator-route`, `orchestrator-checkpoint`,
  `orchestrator-resume`, `orchestrator-status`, `orchestrator-history`,
  `orchestrator-report`, `orchestrator-check`.

Single-objective missions are launched end-to-end with:

```
python scripts/kernel.py orchestrator-mission "Build Patient Management"
```

## Principles

- The Orchestrator never codes and never reviews; it coordinates. Code is
  written by the Builder and verified by the Reviewer.
- Every task is routed to the engine that owns its surface
  (backend/frontend/database/security -> Builder, verification -> Reviewer,
  knowledge/documentation -> Learner, deployment/infrastructure -> Deployer).
  Absent engines fall back to the closest available engine and the decision is
  recorded as evidence.
- Every task respects the phase budget (5 minutes / 50 files). Missions that
  exceed resource thresholds are split before context is exhausted.
- Missions always resume from checkpoints; every failure is classified,
  recovered, and logged for the mission history.
- Deterministic, auditable, recoverable engineering coordination.
