# Architect Engine (GULA-ARCHITECT-001)

Enterprise Autonomous Architecture & Strategic Decision Engine. Produces a
deterministic architectural model of the platform — bounded contexts,
strategic decisions (ADRs), dependency analysis, technology evolution
roadmap, risk register, design reviews, scale simulation, AI-engine
coordination, and architecture health — without changing any code. All
output derives from deterministic repo evidence.

## Pipeline

audit → model → decisions → dependencies → evolution → risk → review →
simulation → coordination → health → report

## Phases

| Phase | Module | Responsibility |
|---|---|---|
| 0 | `audit.py` | System audit -> `ARCHITECT_AUDIT_REPORT.md` |
| 1 | `model.py` | Bounded-context model (12 contexts, subdomains, data/control flow) |
| 2 | `decisions.py` | Strategic ADRs (10 decisions with reason/trade-offs/cost/rollback) |
| 3 | `dependencies.py` | Dependency analysis (circular + skip-layer findings, lock-in scan) |
| 4 | `evolution.py` | Technology roadmap (9 milestones, migration, scalability tiers) |
| 5 | `risk.py` | Risk register (11 risks, exposure, priority, mitigations) |
| 6 | `review.py` | Design review across 8 dimensions with verdict |
| 7 | `simulation.py` | Scale simulation (100 -> 1M users, storage/cost/bottlenecks) |
| 8 | `coordination.py` | AI-engine coordination contracts (6 engines) |
| 9 | `health.py` | Architecture health + CMMI maturity (overall 59/100, maturity 72/100) |
| 10 | `report.py` | `ARCHITECT_IMPLEMENTATION_REPORT.md` |

## Commands

All commands are reachable through `python scripts/kernel.py architect-<cmd>`
and `python scripts/architect.py <cmd>`:

- `architect-audit`, `architect-model`, `architect-decisions`,
  `architect-dependencies`, `architect-evolution`, `architect-risk`,
  `architect-review`, `architect-simulation`, `architect-coordination`,
  `architect-health`, `architect-report`, `architect-run`,
  `architect-check`.

The success criterion runs end-to-end without manual intervention:

```
python scripts/kernel.py architect-run
```

## State

Persisted under `.ai/core/architect/state/`:

- `model/contexts.json`, `decisions.json`, `dependencies/findings.json`,
  `evolution/roadmap.json`, `risks/register.json`, `review/latest.json`,
  `simulation/projections.json`, `coordination/contracts.json`,
  `health/score.json`.

## Principles

- Architecture derives from deterministic repo evidence, never from opinion.
- Every strategic decision is an ADR with alternatives, trade-offs, cost,
  and a rollback strategy.
- Technology-lock-in detection scans for vendor SDKs (aws/azure/gcp/twilio/
  sendgrid/firebase/algolia) — every recommendation stays vendor-neutral.
- Risk exposure drives priority; mitigation plans are always attached.
- Scale projections make the path from single-node to national deployment
  explicit.
- Health is a number with a maturity level, not a vibe.
