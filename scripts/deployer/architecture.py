"""Phase 1 — Deployment Architecture.

Design the deployment topology for every environment: local, development,
testing, staging, production, disaster recovery, edge, and offline. Each
environment has hosts, a deployment strategy, the services it runs, and the
infrastructure it requires. Deterministic; no I/O at import time.
"""

from __future__ import annotations

from scripts.deployer.core import (
    ENVIRONMENTS,
    DeploymentTarget,
)

# Default topology for each environment. `requires` names infrastructure the
# environment depends on; `services` names the deployable surface.
TOPOLOGY: dict[str, dict] = {
    "local": {
        "hosts": ["localhost"],
        "strategy": "compose-up",
        "services": ["backend", "frontend", "postgres", "redis", "rabbitmq", "minio"],
        "requires": ["docker", "docker-compose"],
        "notes": "single host, no TLS, source volumes for hot reload",
    },
    "development": {
        "hosts": ["dev.gula.local"],
        "strategy": "rolling",
        "services": ["backend", "frontend", "postgres", "redis", "rabbitmq", "minio", "worker"],
        "requires": ["docker", "docker-compose", "storage", "secrets"],
        "notes": "feature branch previews; auto-restart on merge",
    },
    "testing": {
        "hosts": ["test.gula.local"],
        "strategy": "blue-green",
        "services": ["backend", "frontend", "postgres", "redis", "rabbitmq", "minio", "worker"],
        "requires": ["github-actions", "docker-compose", "monitoring", "storage"],
        "notes": "ephemeral; mirrors production topology at reduced scale",
    },
    "staging": {
        "hosts": ["staging.gula.local"],
        "strategy": "canary",
        "services": ["backend", "frontend", "postgres", "redis", "rabbitmq", "minio", "worker"],
        "requires": ["reverse-proxy", "dns", "certificates", "monitoring", "storage", "backups"],
        "notes": "final pre-production gate; production-like config",
    },
    "production": {
        "hosts": ["gula.iq", "api.gula.iq"],
        "strategy": "rolling",
        "services": ["backend", "frontend", "postgres", "redis", "rabbitmq", "minio", "worker", "api-gateway"],
        "requires": ["reverse-proxy", "dns", "certificates", "secrets", "monitoring", "storage", "backups", "alerting"],
        "notes": "multi-az hosting; immutable images; automated rollback",
    },
    "disaster_recovery": {
        "hosts": ["dr.gula.iq"],
        "strategy": "replica",
        "services": ["backend", "frontend", "postgres", "redis", "rabbitmq", "minio"],
        "requires": ["replication", "backups", "dns-failover", "monitoring"],
        "notes": "warm standby with replicated data and RPO/RTO targets",
    },
    "edge": {
        "hosts": ["edge.gula.iq"],
        "strategy": "edge-cache",
        "services": ["frontend", "api-gateway"],
        "requires": ["cdn", "cache", "tls"],
        "notes": "static and API caching close to the citizen",
    },
    "offline": {
        "hosts": ["govnet-gateway"],
        "strategy": "air-gapped",
        "services": ["backend", "frontend", "postgres", "redis", "minio", "worker"],
        "requires": ["offline-repo", "air-gap-bundle", "local-dns"],
        "notes": "isolated ministry deployment; offline-first sync",
    },
}


def build_topology(environments: tuple[str, ...] = ENVIRONMENTS) -> list[DeploymentTarget]:
    """Produce a DeploymentTarget for each requested environment."""
    targets: list[DeploymentTarget] = []
    for env in environments:
        spec = TOPOLOGY.get(env, {})
        targets.append(DeploymentTarget(
            environment=env,
            hosts=spec.get("hosts", []),
            strategy=spec.get("strategy", "rolling"),
            services=spec.get("services", []),
            requires=spec.get("requires", []),
            notes=spec.get("notes", ""),
        ))
    return targets


def describe_targets(targets: list[DeploymentTarget]) -> str:
    lines = ["Deployment topology (GULA-DEPLOYER-001):"]
    for target in targets:
        lines.append(
            f"  {target.environment:<18} {target.strategy:<14} "
            f"hosts={', '.join(target.hosts) or '—'}"
        )
        lines.append(
            f"    services: {', '.join(target.services) or '—'} | "
            f"requires: {', '.join(target.requires) or '—'}"
        )
    return "\n".join(lines)


def environment_gaps(targets: list[DeploymentTarget], present: set[str]) -> list[str]:
    """Return environment requirement gaps given present infrastructure."""
    gaps: list[str] = []
    for target in targets:
        missing = [r for r in target.requires if r not in present]
        if missing:
            gaps.append(f"{target.environment}: missing {', '.join(sorted(missing))}")
    return gaps
