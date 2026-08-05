"""Phase 3 — Infrastructure Management.

Automatically manage servers, volumes, networks, the reverse proxy, DNS,
certificates, secrets, storage, and the managed datastores: Redis, RabbitMQ,
PostgreSQL, MinIO, plus health services. Deterministic specs; the Deployer
applies them to the target environment.
"""

from __future__ import annotations

from scripts.deployer.core import (
    ManagedResource,
    make_id,
)

# Infrastructure resource kinds the Deployer manages.
RESOURCE_KINDS: tuple[str, ...] = (
    "server",
    "volume",
    "network",
    "reverse-proxy",
    "dns",
    "certificate",
    "secret",
    "storage",
    "service",
)

# Managed datastore templates (idempotent desired state).
DATASTORE_SPECS: dict[str, dict] = {
    "postgres": {
        "kind": "service",
        "version": "17",
        "tls": True,
        "replication": "primary-replica",
        "backups": "pg_dump nightly + WAL archive",
        "volumes": ["pgdata-primary", "pgdata-replica"],
        "network": "gula-net",
    },
    "redis": {
        "kind": "service",
        "version": "7",
        "persistence": "AOF",
        "replication": "sentinel",
        "volumes": ["redis-data"],
        "network": "gula-net",
    },
    "rabbitmq": {
        "kind": "service",
        "version": "4",
        "tls": True,
        "mirrored_queues": True,
        "volumes": ["rabbitmq-data"],
        "network": "gula-net",
    },
    "minio": {
        "kind": "storage",
        "version": "latest",
        "tls": True,
        "erasure_coding": True,
        "volumes": ["minio-data"],
        "network": "gula-net",
    },
}


def manage_resources(services: tuple[str, ...] | None = None) -> list[ManagedResource]:
    """Produce the managed-resource set for the platform datastores."""
    resources: list[ManagedResource] = []
    selected = services or tuple(DATASTORE_SPECS)
    for service in selected:
        if service not in DATASTORE_SPECS:
            continue
        spec = DATASTORE_SPECS[service]
        resources.append(ManagedResource(
            resource_id=make_id("RES"),
            service=service,
            kind=spec["kind"],
            spec=dict(spec),
            managed=True,
        ))
    return resources


def desired_network() -> ManagedResource:
    """The shared overlay network for all platform services."""
    return ManagedResource(
        resource_id=make_id("NET"),
        service="platform",
        kind="network",
        spec={"name": "gula-net", "driver": "overlay", "encrypted": True},
        managed=True,
    )


def reverse_proxy_spec(domain: str = "gula.iq") -> ManagedResource:
    """Reverse proxy + TLS termination + DNS entry for a domain."""
    return ManagedResource(
        resource_id=make_id("RPOXY"),
        service="gateway",
        kind="reverse-proxy",
        spec={
            "domain": domain,
            "tls": True,
            "hsts": True,
            "gzip": True,
            "limits": {"connections": 10000, "rate": "100r/s"},
        },
        managed=True,
    )


def certificate_spec(domain: str, issuer: str = "letsencrypt") -> ManagedResource:
    """Managed certificate for a domain with automatic renewal."""
    return ManagedResource(
        resource_id=make_id("CRT"),
        service="tls",
        kind="certificate",
        spec={"domain": domain, "issuer": issuer, "renew": True},
        managed=True,
    )


def secrets_spec(provider: str = "vault") -> ManagedResource:
    """Managed secrets backend with rotation and least privilege."""
    return ManagedResource(
        resource_id=make_id("SEC"),
        service="secrets",
        kind="secret",
        spec={"provider": provider, "rotation_days": 90, "lease_ttl": "1h"},
        managed=True,
    )


def render_plan(resources: list[ManagedResource]) -> str:
    lines = ["Infrastructure management plan (GULA-DEPLOYER-001):"]
    for resource in resources:
        keys = ", ".join(sorted(resource.spec.keys())[:4])
        lines.append(
            f"  {resource.kind:<14} {resource.service:<10} "
            f"[{resource.resource_id}] {{ {keys} }}"
        )
    return "\n".join(lines)
