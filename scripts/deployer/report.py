"""Phase 10 — Implementation Report.

Generate DEPLOYER_IMPLEMENTATION_REPORT.md covering infrastructure,
deployment flow, rollback flow, monitoring, security, availability,
recovery, performance, and future improvements.
"""

from __future__ import annotations

from datetime import UTC, datetime

from scripts.deployer.core import (
    REPORT_PATH,
    read_json,
)
from scripts.kernel.core import REPO_ROOT


def deployment_stats() -> dict:
    """Aggregate deployment history from the registry."""
    data = read_json(REPO_ROOT / ".ai" / "core" / "deployer" / "history" / "registry.json")
    deployments = data.get("deployments", {})
    stats = {"total": len(deployments), "live": 0, "rolled_back": 0, "failed": 0}
    for info in deployments.values():
        status = info.get("status")
        if status in stats:
            stats[status] += 1
    return stats


def render() -> str:
    stats = deployment_stats()
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return "\n".join([
        "# GULA Deployment Engine — Implementation Report",
        "",
        f"Generated: {now}",
        "",
        "## Engine Summary",
        "",
        "The Deployment Engine (GULA-DEPLOYER-001) transforms verified",
        "software into a production-ready, observable, secure, and recoverable",
        "platform. It never develops application features — it only deploys,",
        "validates, secures, monitors, scales, and recovers production systems.",
        "",
        "Principles enforced: only reviewed code is deployed; every deployment",
        "is reproducible, reversible, observable, has rollback, and is",
        "documented.",
        "",
        "## Phase Coverage",
        "",
        "| Phase | Module | Responsibility |",
        "|---|---|---|",
        "| 0 | `audit.py` | Deployment surface audit -> `DEPLOYER_AUDIT_REPORT.md` |",
        "| 1 | `architecture.py` | Topology for 8 environments (local..offline) |",
        "| 2 | `execution.py` | Build, validate, sign, tag, registry, package, deploy |",
        "| 3 | `infrastructure.py` | Servers, volumes, networks, proxy, DNS, certs, secrets, datastores |",
        "| 4 | `health.py` | 10-component health validation; reject on failure |",
        "| 5 | `rollback.py` | Snapshots, version history, automatic rollback, verified restore |",
        "| 6 | `scaling.py` | Horizontal/vertical/worker/queue scaling + K8s readiness |",
        "| 7 | `observability.py` | Prometheus, Grafana, Alertmanager, logs, metrics, tracing, alerts |",
        "| 8 | `security.py` | 9-area security verification; block on failure |",
        "| 9 | `knowledge.py` | Registry, history, inventory, runbooks, recovery, lessons |",
        "| 10 | `report.py` | This implementation report |",
        "",
        "## Infrastructure",
        "",
        "The managed datastores are PostgreSQL, Redis, RabbitMQ, and MinIO, each",
        "with TLS, replication, backups, and dedicated volumes on the shared",
        "overlay network. The reverse proxy terminates TLS, and certificates are",
        "managed with automatic renewal. Secrets live in a managed vault with",
        "rotation.",
        "",
        "## Deployment Flow",
        "",
        "Build container -> validate container -> validate compose -> sign image",
        "-> tag semantic version -> push registry -> package release -> deploy.",
        "Only reviewed code enters the pipeline; the Reviewer gates the change",
        "set before this engine runs.",
        "",
        "## Rollback Flow",
        "",
        "A snapshot (version, configuration, database, storage) is captured",
        "before every deployment. When health validation rejects a release, the",
        "engine rolls back automatically, restores the pre-deployment state,",
        "and verifies the restore before returning to service.",
        "",
        "## Monitoring",
        "",
        "Prometheus scrapes metrics, Grafana hosts dashboards, Alertmanager",
        "fires incident alerts, Loki collects logs, and Tempo/Jaeger receive",
        "traces through OpenTelemetry. Platform dashboards cover API latency,",
        "database health, queue depth, infrastructure, and incidents.",
        "",
        "## Security",
        "",
        "Nine areas are verified before promotion: secrets, TLS, certificates,",
        "firewall, container security, dependency security, least privilege,",
        "image scanning, and supply chain validation. Any failed area blocks the",
        "deployment.",
        "",
        "## Availability & Recovery",
        "",
        "Rolling deployments with automated rollback keep the platform"
        " available during release. Disaster recovery is a warm standby with"
        " replicated data. Recovery procedures are codified in the runbook:"
        " restore version -> restore configuration -> restore database ->"
        " verify health -> record lesson.",
        "",
        "## Performance",
        "",
        "Horizontal, vertical, worker, and queue scaling policies scale the"
        " platform under load. Scaling is declarative (min/max replicas with"
        " a metric and threshold), which is also the model Kubernetes HPA"
        " consumes for the future K8s migration.",
        "",
        "## Deployment Statistics",
        "",
        f"- Total deployments: **{stats['total']}**",
        f"- Live: {stats['live']} | Rolled back: {stats['rolled_back']} | Failed: {stats['failed']}",
        "",
        "## Future Improvements",
        "",
        "- Provision Terraform modules for Hetzner cloud infrastructure.",
        "- Adopt Traefik as the reverse proxy with Let's Encrypt issuance.",
        "- Migrate the scaling model to Kubernetes HPA and cluster autoscaling.",
        "- Expand image signing to cosign with a registry trust policy.",
        "- Add canary metrics-based promotion gates for staging and production.",
        "",
    ])


def write_report() -> None:
    REPORT_PATH.write_text(render(), encoding="utf-8")
