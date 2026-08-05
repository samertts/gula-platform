"""Shared constants, dataclasses, and path helpers for the Optimization Engine.

The Optimization Engine (GULA-OPTIMIZER-001) continuously improves the
entire platform without changing business behavior. It never changes
functional requirements — it improves implementation quality only:
performance, scalability, reliability, maintainability, developer
experience, and resource efficiency.

Optimizations are always measured first, evidence-driven, reversible, and
safe. Security and correctness always outrank speed. The engine audits the
full system, measures a baseline, detects bottlenecks, recommends
architecture and resource improvements, improves developer experience,
tracks technical debt, verifies optimizations safely, proposes evolution,
validates quality, and publishes an implementation report.

The engine integrates with the Builder (produces code), the Reviewer
(verifies change sets), the Orchestrator (records mission history), the
Deployer (records deployment history), and the Learner (records knowledge).
It mirrors the Kernel's primitives (state, severity, phase budgets) and
stays independent of the other engines' internals.
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

OPTIMIZER_DIR = REPO_ROOT / ".ai" / "core" / "optimizer"
STATE_DIR = OPTIMIZER_DIR / "state"
BENCHMARK_DIR = STATE_DIR / "benchmarks"
BOTTLENECK_DIR = STATE_DIR / "bottlenecks"
DEBT_DIR = STATE_DIR / "debt"
PROPOSAL_DIR = STATE_DIR / "proposals"
HISTORY_DIR = OPTIMIZER_DIR / "history"
DOCS_DIR = REPO_ROOT / "docs" / "optimizer"
REPORT_PATH = REPO_ROOT / "OPTIMIZER_IMPLEMENTATION_REPORT.md"
AUDIT_PATH = REPO_ROOT / "OPTIMIZER_AUDIT_REPORT.md"

MAX_TASK_MINUTES = MAX_PHASE_MINUTES
MAX_TASK_FILES = MAX_PHASE_FILES

# Areas the Optimizer audits (Phase 0).
AUDIT_COMPONENTS: tuple[str, ...] = (
    "backend",
    "frontend",
    "database",
    "infrastructure",
    "docker",
    "knowledge",
    "deployment",
    "documentation",
    "testing",
    "ci-cd",
    "developer-environment",
)

# Performance metrics measured for the baseline (Phase 1).
PERFORMANCE_METRICS: tuple[str, ...] = (
    "api-latency",
    "database-queries",
    "memory-usage",
    "cpu-usage",
    "disk-usage",
    "network-traffic",
    "build-time",
    "startup-time",
    "bundle-size",
    "container-size",
    "execution-time",
)

# Bottleneck categories automatically detected (Phase 2).
BOTTLENECK_KINDS: tuple[str, ...] = (
    "slow-api",
    "duplicate-queries",
    "n-plus-one",
    "unused-code",
    "dead-code",
    "large-bundle",
    "slow-build",
    "blocking-operation",
    "large-dependency",
    "memory-leak",
    "cpu-hotspot",
    "storage-waste",
)

# Architecture optimization techniques (Phase 3).
ARCHITECTURE_TECHNIQUES: tuple[str, ...] = (
    "module-boundaries",
    "dependency-reduction",
    "caching",
    "indexing",
    "async-processing",
    "lazy-loading",
    "code-splitting",
    "compression",
    "queue-optimization",
    "database-optimization",
)

# Resource optimization targets (Phase 4).
RESOURCE_TARGETS: tuple[str, ...] = (
    "docker-images",
    "containers",
    "volumes",
    "redis",
    "postgresql",
    "rabbitmq",
    "minio",
    "worker-usage",
    "background-tasks",
    "infrastructure-cost",
)

# Developer-experience dimensions (Phase 5).
DX_DIMENSIONS: tuple[str, ...] = (
    "build-speed",
    "test-speed",
    "dev-startup",
    "repository-navigation",
    "knowledge-search",
    "automation",
    "tooling",
    "developer-feedback",
)

# Technical-debt categories (Phase 6).
DEBT_KINDS: tuple[str, ...] = (
    "duplicated-logic",
    "deprecated-code",
    "temporary-fixes",
    "architecture-drift",
    "dependency-problems",
    "configuration-drift",
    "documentation-drift",
)

# Evolution targets the Optimizer proposes improvements for (Phase 8).
EVOLUTION_TARGETS: tuple[str, ...] = (
    "improvement-proposals",
    "architecture-evolution",
    "refactoring-candidates",
    "infrastructure-improvements",
    "automation-opportunities",
    "ai-capability-improvements",
    "knowledge-improvements",
)

# Quality validation checks (Phase 9).
QUALITY_CHECKS: tuple[str, ...] = (
    "no-functional-regression",
    "performance-improved",
    "security-preserved",
    "documentation-updated",
    "knowledge-updated",
    "deployment-valid",
)

# Bottleneck severity levels (Phase 2).
BOTTLENECK_SEVERITIES: tuple[str, ...] = ("low", "medium", "high", "critical")


class OptimizationStatus(StrEnum):
    PLANNED = "planned"
    MEASURED = "measured"
    OPTIMIZED = "optimized"
    VERIFIED = "verified"
    REVERTED = "reverted"


class DebtStatus(StrEnum):
    OPEN = "open"
    APPROVED = "approved"
    ADDRESSED = "addressed"
    WONT_FIX = "wont-fix"


class ProposalStatus(StrEnum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


@dataclass
class AuditItem:
    """One audited optimization area with evidence (Phase 0)."""

    item_id: str
    title: str
    status: str = OptimizationStatus.PLANNED.value
    confidence: str = "low"
    tags: list[str] = field(default_factory=list)
    body: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "status": self.status,
            "confidence": self.confidence,
            "tags": self.tags,
            "body": self.body,
        }


@dataclass
class Metric:
    """A single baseline performance measurement (Phase 1)."""

    name: str
    value: float
    unit: str = ""
    baseline: bool = True
    threshold: float | None = None
    source: str = ""
    measured_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "baseline": self.baseline,
            "threshold": self.threshold,
            "source": self.source,
            "measured_at": self.measured_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Metric:
        return cls(
            name=data.get("name", ""),
            value=data.get("value", 0.0),
            unit=data.get("unit", ""),
            baseline=data.get("baseline", True),
            threshold=data.get("threshold"),
            source=data.get("source", ""),
            measured_at=data.get("measured_at", ""),
        )


@dataclass
class Bottleneck:
    """A detected performance/scalability bottleneck (Phase 2)."""

    bottleneck_id: str
    kind: str
    area: str
    severity: str = "medium"
    count: int = 1
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bottleneck_id": self.bottleneck_id,
            "kind": self.kind,
            "area": self.area,
            "severity": self.severity,
            "count": self.count,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "created_at": self.created_at,
        }


@dataclass
class ArchitectureRecommendation:
    """A recommended architecture optimization (Phase 3)."""

    recommendation_id: str
    technique: str
    area: str
    rationale: str = ""
    expected_impact: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "technique": self.technique,
            "area": self.area,
            "rationale": self.rationale,
            "expected_impact": self.expected_impact,
            "created_at": self.created_at,
        }


@dataclass
class ResourceRecommendation:
    """A recommended resource/infrastructure optimization (Phase 4)."""

    resource_id: str
    target: str
    area: str
    saving_type: str = ""
    recommendation: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "target": self.target,
            "area": self.area,
            "saving_type": self.saving_type,
            "recommendation": self.recommendation,
            "created_at": self.created_at,
        }


@dataclass
class DxFinding:
    """A developer-experience observation (Phase 5)."""

    dx_id: str
    dimension: str
    score: int = 0
    recommendation: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dx_id": self.dx_id,
            "dimension": self.dimension,
            "score": self.score,
            "recommendation": self.recommendation,
            "created_at": self.created_at,
        }


@dataclass
class DebtItem:
    """A prioritized technical-debt record (Phase 6)."""

    debt_id: str
    kind: str
    area: str
    impact: str = ""
    severity: str = "medium"
    status: str = DebtStatus.OPEN.value
    recommendation: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "kind": self.kind,
            "area": self.area,
            "impact": self.impact,
            "severity": self.severity,
            "status": self.status,
            "recommendation": self.recommendation,
            "created_at": self.created_at,
        }


@dataclass
class OptimizationRun:
    """A measured, verified, reversible optimization (Phase 7)."""

    optimization_id: str
    target: str
    before_value: float
    after_value: float
    tests_passed: bool = False
    benchmarked: bool = False
    regression: bool = False
    reverted: bool = False
    status: str = OptimizationStatus.PLANNED.value
    created_at: str = field(default_factory=utcnow)

    def delta_pct(self) -> float:
        if self.before_value == 0:
            return 0.0
        return round(
            (self.after_value - self.before_value) / abs(self.before_value) * 100, 2
        )

    def improved(self) -> bool:
        return self.delta_pct() < 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "optimization_id": self.optimization_id,
            "target": self.target,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "delta_pct": self.delta_pct(),
            "tests_passed": self.tests_passed,
            "benchmarked": self.benchmarked,
            "regression": self.regression,
            "reverted": self.reverted,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class EvolutionProposal:
    """A proposed platform evolution (Phase 8)."""

    proposal_id: str
    target: str
    title: str
    rationale: str
    status: str = ProposalStatus.OPEN.value
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target": self.target,
            "title": self.title,
            "rationale": self.rationale,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class OptimizationScore:
    """Quality validation of the optimization program (Phase 9)."""

    checks: dict[str, str] = field(default_factory=dict)
    score: int = 100
    regressions: list[str] = field(default_factory=list)
    verified_runs: int = 0
    improved_metrics: int = 0
    summary: str = ""


def make_id(prefix: str) -> str:
    """Generate a unique identifier with a stable prefix."""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def ensure_dirs() -> None:
    """Create all Optimizer state directories."""
    for directory in (
        STATE_DIR,
        BENCHMARK_DIR,
        BOTTLENECK_DIR,
        DEBT_DIR,
        PROPOSAL_DIR,
        HISTORY_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    import json

    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
