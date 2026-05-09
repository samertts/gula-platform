# Phase 17 — National Operational Infrastructure

**Goal:** Prepare GULA for sovereign operational deployment environments —
primary datacenters, DR sites, SOC/NOC, incident-response coordination, and
provincial / edge sites — without replacing the existing infrastructure
stack.

This phase is a **readiness layer** on top of the existing Docker Compose +
Kubernetes deployment artifacts. It does not introduce a new stack; it
documents and codifies how to run the existing stack at sovereign scale.

## Documents

| File | Subject |
|------|---------|
| [`01-dr-readiness.md`](./01-dr-readiness.md) | DR/failover readiness, RTO/RPO targets |
| [`02-runbooks.md`](./02-runbooks.md) | Operational runbooks — incident, recovery, escalation |
| [`03-incident-response.md`](./03-incident-response.md) | Incident-response framework |
| [`04-deployment-topology.md`](./04-deployment-topology.md) | Multi-region deployment topology |
| [`05-survivability-analysis.md`](./05-survivability-analysis.md) | Operational survivability & blast-radius |
| [`06-governance-checklist.md`](./06-governance-checklist.md) | Production governance checklist |
| [`07-dependency-register.md`](./07-dependency-register.md) | Infrastructure dependency register |

## Sovereign Invariants Honored

- OS-1 (DR preserves audit chain)
- OS-2 (regional isolation, no cross-region tenant bleed)
- OS-3 (degraded-network fail-closed for sensitive writes)
- OS-4 (offline-edge conflict-detectable sync)
- OS-5 (no orphaned/duplicate audit on partial-outage recovery)

## Out of Scope

- Replacing Docker Compose / Kubernetes (existing stack remains)
- Replacing PostgreSQL / Redis (existing dependencies remain)
- Sovereign cloud lift-and-shift (handled per-deployment)
