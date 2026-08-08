"""Shared constants, dataclasses, and path helpers for the Architect Engine.

The Architect Engine (GULA-ARCHITECT-001) is the Enterprise Autonomous
Architecture & Strategic Decision Engine. It never writes production
features — it makes, documents, and reviews architectural decisions that
preserve the GULA national platform constitution: FHIR R4, HL7, ISO 15189,
CAP, CLSI, multi-tenancy, RBAC/ABAC, immutable audit log, offline-first,
national deployment compatibility, Arabic-first, Ministry/Directorate/
Hospital/Laboratory hierarchy, Identity Platform, Analyzer Integration,
Event Bus, Clinical Safety, and national health platform compatibility.

The engine audits the architecture surface, models bounded contexts,
records architectural decisions (ADRs), governs dependencies, plans 1/3/5
year evolution, tracks architectural risk, reviews candidate designs,
simulates scale from 100 to 1M users, coordinates the AI engines (Builder,
Reviewer, Orchestrator, Learner, Optimizer, Deployer), measures architecture
health, and publishes an implementation report.

It mirrors the Kernel primitives (paths, phases, state) and stays
independent of the other engines' internals.
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

ARCHITECT_DIR = REPO_ROOT / ".ai" / "core" / "architect"
STATE_DIR = ARCHITECT_DIR / "state"
MODEL_DIR = STATE_DIR / "model"
DECISION_DIR = STATE_DIR / "decisions"
DEPENDENCY_DIR = STATE_DIR / "dependencies"
EVOLUTION_DIR = STATE_DIR / "evolution"
RISK_DIR = STATE_DIR / "risks"
REVIEW_DIR = STATE_DIR / "review"
SIMULATION_DIR = STATE_DIR / "simulation"
COORDINATION_DIR = STATE_DIR / "coordination"
HEALTH_DIR = STATE_DIR / "health"
HISTORY_DIR = ARCHITECT_DIR / "history"
DOCS_DIR = REPO_ROOT / "docs" / "architect"
REPORT_PATH = REPO_ROOT / "docs/reports/ARCHITECT_IMPLEMENTATION_REPORT.md"
AUDIT_PATH = REPO_ROOT / "docs/reports/ARCHITECT_AUDIT_REPORT.md"

MAX_TASK_MINUTES = MAX_PHASE_MINUTES
MAX_TASK_FILES = MAX_PHASE_FILES

# Architecture surfaces the Architect audits (Phase 0).
ARCHITECTURE_COMPONENTS: tuple[str, ...] = (
    "backend",
    "frontend",
    "database",
    "identity",
    "fhir-hl7",
    "multi-tenancy",
    "offline-first",
    "event-bus",
    "analyzer-integration",
    "security",
    "infrastructure",
    "deployment",
    "governance",
    "documentation",
    "testing",
    "ai-engines",
)

# Bounded-context seeds the Architect scans for in the backend (Phase 1).
BOUNDED_CONTEXT_SEEDS: tuple[str, ...] = (
    "patient",
    "lab",
    "sample",
    "order",
    "result",
    "quality-control",
    "claim",
    "consent",
    "identity",
    "communication",
    "dashboard",
    "admin",
)

# Trust boundaries of the platform (Phase 1).
TRUST_BOUNDARIES: tuple[str, ...] = (
    "public",
    "authenticated",
    "internal",
    "data-store",
    "external",
)

# Relationship kinds between bounded contexts (Phase 1).
RELATIONSHIP_TYPES: tuple[str, ...] = (
    "depends-on",
    "calls",
    "subscribes",
    "owns-data",
    "shares-data",
)

# Dependency governance verdicts (Phase 3).
DEPENDENCY_KINDS: tuple[str, ...] = (
    "circular",
    "skip-layer",
    "cross-context",
    "framework-coupled",
)

# Evolution horizons (Phase 4).
EVOLUTION_HORIZONS: tuple[str, ...] = (
    "1-year",
    "3-year",
    "5-year",
)

# Architectural risk levels (Phase 5).
RISK_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")

# Design-review dimensions (Phase 6).
REVIEW_DIMENSIONS: tuple[str, ...] = (
    "architecture",
    "scalability",
    "reliability",
    "maintainability",
    "security",
    "performance",
    "cost",
    "compliance",
)

# Scale simulation steps (Phase 7).
SCALE_STEPS: tuple[int, ...] = (100, 1_000, 10_000, 100_000, 1_000_000)

# AI engines the Architect coordinates (Phase 8).
AI_ENGINES: tuple[str, ...] = (
    "builder",
    "reviewer",
    "orchestrator",
    "learner",
    "optimizer",
    "deployer",
)

# Architecture health dimensions (Phase 9).
HEALTH_DIMENSIONS: tuple[str, ...] = (
    "layer-discipline",
    "dependency-governance",
    "context-cohesion",
    "decision-coverage",
    "risk-exposure",
    "national-compliance",
)


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


class ReviewVerdict(StrEnum):
    PASS = "pass"
    CONDITIONAL = "conditional"
    FAIL = "fail"


class RiskStatus(StrEnum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"


@dataclass
class AuditItem:
    """One audited architecture surface with evidence (Phase 0)."""

    item_id: str
    title: str
    status: str = "planned"
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
class BoundedContext:
    """A detected bounded context of the platform (Phase 1)."""

    name: str
    description: str = ""
    modules: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    subdomains: list[str] = field(default_factory=list)
    data_flow: str = ""
    control_flow: str = ""
    trust_boundary: str = "internal"
    discovered_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "modules": self.modules,
            "entities": self.entities,
            "subdomains": self.subdomains,
            "data_flow": self.data_flow,
            "control_flow": self.control_flow,
            "trust_boundary": self.trust_boundary,
            "discovered_at": self.discovered_at,
        }


@dataclass
class ContextRelationship:
    """A relationship between two bounded contexts (Phase 1)."""

    source: str
    target: str
    kind: str = "calls"
    note: str = ""
    data_flow: str = ""
    control_flow: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "note": self.note,
            "data_flow": self.data_flow,
            "control_flow": self.control_flow,
        }


@dataclass
class ArchitectureDecision:
    """An architectural decision record (ADR) (Phase 2)."""

    decision_id: str
    title: str
    status: str = DecisionStatus.PROPOSED.value
    context: str = ""
    decision: str = ""
    reason: str = ""
    alternatives: list[str] = field(default_factory=list)
    trade_offs: list[str] = field(default_factory=list)
    risk: str = ""
    cost: str = ""
    rollback: str = ""
    review_status: str = "pending-review"
    consequences: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "status": self.status,
            "context": self.context,
            "decision": self.decision,
            "reason": self.reason,
            "alternatives": self.alternatives,
            "trade_offs": self.trade_offs,
            "risk": self.risk,
            "cost": self.cost,
            "rollback": self.rollback,
            "review_status": self.review_status,
            "consequences": self.consequences,
            "created_at": self.created_at,
        }


@dataclass
class DependencyEdge:
    """A dependency detected between backend packages (Phase 3)."""

    source: str
    target: str
    kind: str = "calls"
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "evidence": self.evidence,
        }


@dataclass
class DependencyFinding:
    """A dependency-governance finding (Phase 3)."""

    finding_id: str
    kind: str
    source: str
    target: str
    severity: str = "low"
    evidence: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "kind": self.kind,
            "source": self.source,
            "target": self.target,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


@dataclass
class RoadmapMilestone:
    """One evolution milestone for a horizon (Phase 4)."""

    horizon: str
    title: str
    scope: str
    enabler: str = ""
    risk: str = ""
    technology: str = ""
    migration: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon": self.horizon,
            "title": self.title,
            "scope": self.scope,
            "enabler": self.enabler,
            "risk": self.risk,
            "technology": self.technology,
            "migration": self.migration,
        }


@dataclass
class RiskItem:
    """An architectural risk record (Phase 5)."""

    risk_id: str
    area: str
    title: str
    category: str = "technical"
    probability: str = "medium"
    impact: str = "medium"
    exposure: int = 0
    priority: str = "medium"
    status: str = RiskStatus.OPEN.value
    mitigation: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "area": self.area,
            "title": self.title,
            "category": self.category,
            "probability": self.probability,
            "impact": self.impact,
            "exposure": self.exposure,
            "priority": self.priority,
            "status": self.status,
            "mitigation": self.mitigation,
            "created_at": self.created_at,
        }


@dataclass
class ReviewFinding:
    """One design-review dimension verdict (Phase 6)."""

    dimension: str
    verdict: str = ReviewVerdict.PASS.value
    score: int = 100
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "verdict": self.verdict,
            "score": self.score,
            "notes": self.notes,
        }


@dataclass
class DesignReview:
    """A candidate design review (Phase 6)."""

    review_id: str
    candidate: str
    findings: list[ReviewFinding] = field(default_factory=list)
    verdict: str = ReviewVerdict.PASS.value
    created_at: str = field(default_factory=utcnow)

    def overall_score(self) -> int:
        if not self.findings:
            return 0
        return round(sum(f.score for f in self.findings) / len(self.findings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "candidate": self.candidate,
            "findings": [f.to_dict() for f in self.findings],
            "verdict": self.verdict,
            "overall_score": self.overall_score(),
            "created_at": self.created_at,
        }


@dataclass
class ScaleProjection:
    """One scale step projection (Phase 7)."""

    users: int
    requests_per_second: int
    database_connections: int
    cache_memory_gb: float
    storage_gb: float = 0.0
    monthly_cost_usd: int = 0
    app_replicas: int = 1
    tier: str = "single-node"
    predicted_bottleneck: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "users": self.users,
            "requests_per_second": self.requests_per_second,
            "database_connections": self.database_connections,
            "cache_memory_gb": self.cache_memory_gb,
            "storage_gb": self.storage_gb,
            "monthly_cost_usd": self.monthly_cost_usd,
            "app_replicas": self.app_replicas,
            "tier": self.tier,
            "predicted_bottleneck": self.predicted_bottleneck,
            "note": self.note,
        }


@dataclass
class CoordinationContract:
    """The Architect's coordination contract for one AI engine (Phase 8)."""

    engine: str
    role: str
    mandate: str = ""
    dependencies: list[str] = field(default_factory=list)
    status: str = "integrated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "role": self.role,
            "mandate": self.mandate,
            "dependencies": self.dependencies,
            "status": self.status,
        }


@dataclass
class HealthScore:
    """Architecture health assessment (Phase 9)."""

    dimensions: dict[str, int] = field(default_factory=dict)
    overall: int = 100
    maturity: int = 100
    maturity_level: str = "optimizing"
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimensions": self.dimensions,
            "overall": self.overall,
            "maturity": self.maturity,
            "maturity_level": self.maturity_level,
            "summary": self.summary,
        }


# Maturity model (CMMI-style) for the architecture maturity score (Phase 9).
MATURITY_LEVELS: tuple[tuple[int, int, str], ...] = (
    (0, 19, "initial"),
    (20, 39, "managed"),
    (40, 59, "defined"),
    (60, 79, "quantitatively-managed"),
    (80, 100, "optimizing"),
)


def maturity_level(maturity: int) -> str:
    """Map a maturity score to its level name deterministically."""
    for lower, upper, name in MATURITY_LEVELS:
        if lower <= maturity <= upper:
            return name
    return "initial"


def make_id(prefix: str) -> str:
    """Generate a unique identifier with a stable prefix."""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def ensure_dirs() -> None:
    """Create all Architect state directories."""
    for directory in (
        STATE_DIR,
        MODEL_DIR,
        DECISION_DIR,
        DEPENDENCY_DIR,
        EVOLUTION_DIR,
        RISK_DIR,
        REVIEW_DIR,
        SIMULATION_DIR,
        COORDINATION_DIR,
        HEALTH_DIR,
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
