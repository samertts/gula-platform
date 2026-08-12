# Phase 19 — Sovereign National Health Data Fabric

**Goal:** Establish the architectural and governance preparation for
sovereign-grade national health data infrastructure: master patient index,
longitudinal record continuity, federated identity reconciliation,
terminology governance, and reconciliation audit lineage.

This phase is **architecture + governance**. The existing
`backend/app/services/mpi/` package is the seed; this phase formalises the
boundary and the safeguards.

## Documents

| File | Subject |
|------|---------|
| [`01-architecture.md`](./01-architecture.md) | Data-fabric architecture |
| [`02-mpi-readiness.md`](./02-mpi-readiness.md) | MPI readiness framework |
| [`03-terminology-governance.md`](./03-terminology-governance.md) | Terminology governance |
| [`04-reconciliation-governance.md`](./04-reconciliation-governance.md) | Reconciliation safeguards & merge governance |
| [`05-longitudinal-continuity.md`](./05-longitudinal-continuity.md) | Longitudinal-record continuity |
| [`06-patient-safety-risk.md`](./06-patient-safety-risk.md) | Patient-safety risk analysis |

## Sovereign Invariants Honored

- TI-3, TI-5 (no cross-tenant identity bleed via reconciliation)
- AI-2 (chain continuity through merges)
- CS-3 (logical merges; constituent histories preserved)
