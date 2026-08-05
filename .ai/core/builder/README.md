# Builder Engine (GULA-BUILDER-001)

The primary engineering execution system. Transforms a human objective into a
complete, verified, production-ready implementation.

## Phases

| Phase | Module | Responsibility |
|---|---|---|
| 0 | `audit.py` | Repository audit -> `BUILDER_AUDIT_REPORT.md` |
| 1 | `analyzer.py` | Mission type / complexity / risk / dependencies / cost / time / outputs / verification / rollback |
| 2 | `planner.py` | Program > Phase > Micro Phase > Task (max 5 min / 50 files) |
| 3 | `impact.py` | Affected modules / APIs / DB / frontend / tests / docs / deployment / security / knowledge / registry |
| 4 | `executor.py` | Analyze > Plan > Validate > Execute > Test > Verify > Document > Knowledge > Checkpoint > Continue |
| 5 | `recovery.py` | Never restart: checkpoint, analyze, retry, resume, continue |
| 6 | `knowledge.py` | Search skills / playbooks / runbooks / ADR / registry / memory / constitution |
| 7 | `review.py` | Self review across 8 quality areas |
| 8 | `report.py` | `BUILDER_IMPLEMENTATION_REPORT.md` |

## Commands

All commands are reachable through `python scripts/kernel.py builder-<cmd>`
and `python scripts/builder.py <cmd>`:

- `builder-audit`, `builder-analyze`, `builder-plan`, `builder-impact`,
  `builder-execute`, `builder-recover`, `builder-knowledge`, `builder-review`,
  `builder-report`, `builder-check`.

## Principles

- The Builder never starts coding immediately: every mission is analyzed,
  decomposed, verified, and risk-estimated first.
- Every Builder phase reuses Kernel primitives (state, checkpoints, severity,
  findings) and never reimplements Kernel functionality.
- Every task respects the phase budget (5 minutes / 50 files).
- Missions always resume from checkpoints; progress is never lost.
- Deterministic, auditable, reversible engineering work.
