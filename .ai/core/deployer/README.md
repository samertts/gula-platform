# Deployer Engine (GULA-DEPLOYER-001)

Transforms verified software into a production-ready, observable, secure,
and recoverable platform. It never develops application features — it only
deploys, validates, secures, monitors, scales, and recovers production
systems. Verified code enters the engine from the Reviewer; execution plans
are coordinated by the Orchestrator.

## Pipeline

build → validate → sign → tag → package → deploy → verify → monitor → backup

## Phases

| Phase | Module | Responsibility |
|---|---|---|
| 0 | `audit.py` | Deployment surface audit -> `DEPLOYER_AUDIT_REPORT.md` |
| 1 | `architecture.py` | Topology for 8 environments (local..offline) |
| 2 | `execution.py` | Build, validate, sign, tag, registry, package, deploy |
| 3 | `infrastructure.py` | Servers, volumes, networks, proxy, DNS, certs, secrets, datastores |
| 4 | `health.py` | 10-component health validation; reject deployment on failure |
| 5 | `rollback.py` | Snapshots, version history, automatic rollback, verified restore |
| 6 | `scaling.py` | Horizontal/vertical/worker/queue scaling within policy bounds |
| 7 | `observability.py` | Prometheus/Grafana/Loki/Tempo/Jaeger + dashboards + alerts |
| 8 | `security.py` | 9 security areas; block deployment on failure |
| 9 | `knowledge.py` | Deployment registry, inventory, runbook, lessons learned |
| 10 | `report.py` | `DEPLOYER_IMPLEMENTATION_REPORT.md` + deployment statistics |

## Commands

All commands are reachable through `python scripts/kernel.py deployer-<cmd>`
and `python scripts/deployer.py <cmd>`:

- `deployer-audit`, `deployer-architecture`, `deployer-pipeline`,
  `deployer-infrastructure`, `deployer-health`, `deployer-rollback`,
  `deployer-scaling`, `deployer-observability`, `deployer-security`,
  `deployer-knowledge`, `deployer-report`, `deployer-deploy`,
  `deployer-check`.

The success criterion runs end-to-end without manual intervention:

```
python scripts/kernel.py deployer-deploy 1.4.0 production
```

## Principles

- Only reviewed code is deployed; the Reviewer verdict gates releases.
- Every deployment is reproducible, reversible, observable, and documented.
- A snapshot is captured before every deploy; health rejection triggers
  automatic rollback and verified restore.
- Security failures (secrets, TLS, supply chain, images, least privilege)
  block deployment — never deploy insecure.
- Scaling decisions stay within declared policy bounds; Kubernetes readiness
  is assessed before migrations.
- Every deployment is recorded in the registry, every rollback becomes a
  lesson, and the runbook grows with each incident.
- Deterministic, auditable, recoverable deployment coordination.
