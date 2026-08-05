"""Shared constants, dataclasses, and path helpers for the Deployment Engine.

The Deployment Engine (GULA-DEPLOYER-001) transforms verified software into
a production-ready, observable, secure, and recoverable platform. It never
develops application features. It only deploys, validates, secures,
monitors, scales, and recovers production systems.

General principles:
- Only reviewed code may be deployed.
- Every deployment is reproducible, reversible, observable, has rollback,
  and is documented.

The engine integrates with the Builder (produces verified code), the
Reviewer (approves the change set), and the Orchestrator (routes deployment
missions to this engine). It mirrors the Kernel's primitives (state,
severity, phase budgets) and stays independent of the other engines'
internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from scripts.kernel.core import (
    MAX_PHASE_FILES,
    MAX_PHASE_MINUTES,
    REPO_ROOT,
    utcnow,
)

DEPLOYER_DIR = REPO_ROOT / ".ai" / "core" / "deployer"
STATE_DIR = DEPLOYER_DIR / "state"
SNAPSHOT_DIR = STATE_DIR / "snapshots"
HISTORY_DIR = DEPLOYER_DIR / "history"
DOCS_DIR = REPO_ROOT / "docs" / "deployer"
REPORT_PATH = REPO_ROOT / "DEPLOYER_IMPLEMENTATION_REPORT.md"
AUDIT_PATH = REPO_ROOT / "DEPLOYER_AUDIT_REPORT.md"

MAX_TASK_MINUTES = MAX_PHASE_MINUTES
MAX_TASK_FILES = MAX_PHASE_FILES

# Environments the architecture supports (Phase 1).
ENVIRONMENTS: tuple[str, ...] = (
    "local",
    "development",
    "testing",
    "staging",
    "production",
    "disaster_recovery",
    "edge",
    "offline",
)

# Audit categories (Phase 0).
AUDIT_COMPONENTS: tuple[str, ...] = (
    "docker",
    "docker-compose",
    "traefik",
    "cloudflare",
    "vercel",
    "hetzner",
    "terraform",
    "kubernetes",
    "helm",
    "github-actions",
    "environment-variables",
    "secrets",
    "certificates",
    "dns",
    "storage",
    "backups",
    "monitoring",
)

# Platform services the Deployer manages (Phase 3+).
SERVICES: tuple[str, ...] = (
    "backend",
    "frontend",
    "postgres",
    "redis",
    "rabbitmq",
    "minio",
    "worker",
    "api-gateway",
    "clickhouse",
    "kafka",
)

# Managed infrastructure services (Phase 3).
MANAGED_SERVICES: tuple[str, ...] = (
    "postgres",
    "redis",
    "rabbitmq",
    "minio",
)

# Health components validated in Phase 4.
HEALTH_COMPONENTS: tuple[str, ...] = (
    "api",
    "frontend",
    "database",
    "redis",
    "message-queue",
    "storage",
    "authentication",
    "metrics",
    "tracing",
    "logging",
)

# Observability services (Phase 7).
OBSERVABILITY_SERVICES: tuple[str, ...] = (
    "prometheus",
    "grafana",
    "alertmanager",
    "loki",
    "tempo",
    "jaeger",
)

# Security verification areas (Phase 8).
SECURITY_AREAS: tuple[str, ...] = (
    "secrets",
    "tls",
    "certificates",
    "firewall",
    "container-security",
    "dependency-security",
    "least-privilege",
    "image-scanning",
    "supply-chain",
)

# Image digest/signature trust anchor for supply-chain validation (Phase 8).
IMAGE_DIGEST_PREFIX = "sha256:"


class Environment(StrEnum):
    """The eight deployment environments."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DISASTER_RECOVERY = "disaster_recovery"
    EDGE = "edge"
    OFFLINE = "offline"


class DeploymentStatus(StrEnum):
    """Lifecycle states for one deployment event."""

    PLANNED = "planned"
    PACKAGED = "packaged"
    VALIDATED = "validated"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    LIVE = "live"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    """Outcome of one health/validation check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class RollbackKind(StrEnum):
    """Phase 5 — what a rollback restores."""

    VERSION = "version"
    CONFIGURATION = "configuration"
    DATABASE = "database"
    SNAPSHOT = "snapshot"
    INFRASTRUCTURE = "infrastructure"


class ScalingMode(StrEnum):
    """Phase 6 — scaling strategies."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    WORKER = "worker"
    QUEUE = "queue"


def make_id(prefix: str) -> str:
    """Generate a short deterministic-unique identifier."""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


@dataclass
class InfrastructureItem:
    """Phase 0 — one audited infrastructure component."""

    name: str
    category: str
    present: bool = False
    evidence: list[str] = field(default_factory=list)
    notes: str = "NOT FOUND"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "present": self.present,
            "evidence": self.evidence,
            "notes": self.notes,
        }


@dataclass
class DeploymentTarget:
    """Phase 1 — an environment's deployment topology."""

    environment: str
    hosts: list[str] = field(default_factory=list)
    strategy: str = "rolling"
    services: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class ReleaseArtifact:
    """Phase 2 — a packaged, signed, versioned artifact."""

    artifact_id: str
    name: str
    version: str
    image: str = ""
    digest: str = ""
    registry: str = ""
    signed: bool = False
    validated: bool = False
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class ManagedResource:
    """Phase 3 — an infrastructure resource the Deployer manages."""

    resource_id: str
    service: str
    kind: str
    spec: dict[str, Any] = field(default_factory=dict)
    managed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class ValidationCheck:
    """Phase 4 — one health/validation probe result."""

    component: str
    check: str
    status: str = ValidationStatus.PASS.value
    endpoint: str = ""
    latency_ms: int = 0
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class DeploymentSnapshot:
    """Phase 5 — a point-in-time state captured for rollback."""

    snapshot_id: str
    deployment_id: str
    version: str
    config_digest: str = ""
    database_backup: str = ""
    storage_backup: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class ScalingPolicy:
    """Phase 6 — auto-scaling rules for a service."""

    policy_id: str
    service: str
    mode: str = ScalingMode.HORIZONTAL.value
    min_replicas: int = 1
    max_replicas: int = 5
    metric: str = "cpu_utilization"
    threshold: float = 80.0
    enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class ObservabilityConfig:
    """Phase 7 — observability integration status."""

    component: str
    enabled: bool = False
    endpoint: str = ""
    retention_days: int = 30

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class SecurityCheck:
    """Phase 8 — one security verification result."""

    area: str
    finding: str
    passed: bool = False
    severity: str = "low"
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class DeploymentRecord:
    """Phase 9 — the persistent record of a deployment event."""

    deployment_id: str
    version: str
    environment: str
    status: str = DeploymentStatus.PLANNED.value
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    validations: list[dict[str, Any]] = field(default_factory=list)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    rollbacks: list[dict[str, Any]] = field(default_factory=list)
    security: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)
    closed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    import json

    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    import json

    ensure_dirs()
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
