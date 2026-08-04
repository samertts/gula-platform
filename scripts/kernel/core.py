"""Shared constants, dataclasses, and path helpers for the Execution Kernel.

The Kernel is the permanent execution layer shared by every AI Engine. It
provides governance, execution, coordination, resource management, state
management, security, communication, knowledge access, checkpointing, and
recovery. Every AI Engine depends on the Kernel; no engine implements Kernel
functionality independently.

The Kernel builds on the GULA Governor (GULA-GOVERNOR-001) policy layer and
reuses its implementations wherever they already exist — it never duplicates
functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
KERNEL_DIR = REPO_ROOT / ".ai" / "core" / "kernel"
STATE_DIR = KERNEL_DIR / "state"
CHECKPOINT_DIR = STATE_DIR / "checkpoints"
DOCS_DIR = REPO_ROOT / "docs" / "kernel"

MAX_PHASE_MINUTES = 5
MAX_PHASE_FILES = 50

# Phase 2 — autonomy levels, L0 (least) to L8 (most dangerous).
AUTONOMY_LEVELS: tuple[str, ...] = (
    "L0",  # read only
    "L1",  # analysis
    "L2",  # suggest
    "L3",  # modify workspace
    "L4",  # commit
    "L5",  # pull request
    "L6",  # deploy staging
    "L7",  # deploy production
    "L8",  # dangerous operations
)

AUTONOMY_NAMES: dict[str, str] = {
    "L0": "read only",
    "L1": "analysis",
    "L2": "suggest",
    "L3": "modify workspace",
    "L4": "commit",
    "L5": "pull request",
    "L6": "deploy staging",
    "L7": "deploy production",
    "L8": "dangerous operations",
}

# Phase 6 — lock resource types.
LOCK_TYPES: tuple[str, ...] = (
    "file",
    "module",
    "knowledge",
    "registry",
    "deployment",
    "database",
)

# Phase 15 — technical debt categories.
DEBT_CATEGORIES: tuple[str, ...] = (
    "architecture-drift",
    "knowledge-drift",
    "dependency-drift",
    "configuration-drift",
    "dead-code",
    "duplicate-code",
    "duplicate-knowledge",
    "large-modules",
    "outdated-docs",
    "security-debt",
    "performance-debt",
    "maintainability-debt",
)

# Phase 14 — failure classifications.
FAILURE_CLASSES: tuple[str, ...] = (
    "transient",
    "resource",
    "environment",
    "validation",
    "security",
    "permanent",
)

# The KERNEL contract (Phase 3) extends the Governor Phase 10 contract with
# execution metadata. Every engine must expose all 16 fields.
KERNEL_CONTRACT_FIELDS: tuple[str, ...] = (
    "inputs",
    "outputs",
    "events",
    "errors",
    "artifacts",
    "ownership",
    "dependencies",
    "health",
    "progress",
    "checkpoint",
    "capabilities",
    "resources",
    "timeout",
    "retry",
    "version",
    "status",
)

# Engine registry keyed by engine name with Kernel-level execution metadata
# (Phase 16). Compatibility, version, health, ownership, communication, and
# dependency matrices are derived from this single source of truth.
ENGINE_REGISTRY: dict[str, dict[str, Any]] = {
    "architect": {
        "version": "1.0.0",
        "ownership": ["architecture", "adr", "api-contract"],
        "capabilities": ["approve architecture", "approve ADR", "enforce Clean Architecture"],
        "inputs": ["mission brief", "impact analysis", "ADR proposal"],
        "outputs": ["approved ADR", "architecture decision"],
        "events": ["decision.requested", "decision.approved", "decision.rejected"],
        "errors": ["unapproved_architecture"],
        "artifacts": ["ADR", "architecture-compliance report"],
        "dependencies": ["constitution", "governor"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "decision",
        "resources": {"max_files": 5, "max_minutes": 5},
        "timeout": 300,
        "retry": 3,
        "status": "idle",
        "compatibility": ["constitution", "governor", "orchestrator"],
        "communication": ["orchestrator", "builder"],
    },
    "orchestrator": {
        "version": "1.0.0",
        "ownership": ["mission-lifecycle", "phase-budget"],
        "capabilities": ["coordinate missions", "schedule phases", "route work"],
        "inputs": ["mission routing result", "engine availability"],
        "outputs": ["execution plan", "phase transitions", "checkpoint records"],
        "events": ["mission.started", "phase.completed", "mission.completed"],
        "errors": ["schedule_conflict"],
        "artifacts": ["mission plan", "phase checkpoints"],
        "dependencies": ["governor", "architect"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "phase",
        "resources": {"max_files": 10, "max_minutes": 5},
        "timeout": 300,
        "retry": 3,
        "status": "idle",
        "compatibility": ["governor", "architect", "builder", "reviewer"],
        "communication": ["architect", "builder", "reviewer", "deployer"],
    },
    "reviewer": {
        "version": "1.0.0",
        "ownership": ["deployment-approval", "quality-gate"],
        "capabilities": ["review changes", "approve deployments", "gate quality"],
        "inputs": ["change set", "test results", "deployment request"],
        "outputs": ["review verdict", "deployment approval"],
        "events": ["review.requested", "review.approved", "review.rejected"],
        "errors": ["review_failed"],
        "artifacts": ["review report", "approval record"],
        "dependencies": ["orchestrator", "builder"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "verdict",
        "resources": {"max_files": 5, "max_minutes": 5},
        "timeout": 300,
        "retry": 2,
        "status": "idle",
        "compatibility": ["orchestrator", "builder", "deployer"],
        "communication": ["builder", "deployer", "orchestrator"],
    },
    "builder": {
        "version": "1.0.0",
        "ownership": ["implementation", "tests"],
        "capabilities": ["implement changes", "write tests", "create knowledge artifacts"],
        "inputs": ["approved plan", "impact analysis", "test stubs"],
        "outputs": ["implemented change", "passing tests", "knowledge artifact draft"],
        "events": ["build.started", "build.completed", "build.failed"],
        "errors": ["build_failed"],
        "artifacts": ["code changes", "tests"],
        "dependencies": ["architect", "reviewer"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "change",
        "resources": {"max_files": 50, "max_minutes": 5},
        "timeout": 600,
        "retry": 3,
        "status": "idle",
        "compatibility": ["architect", "reviewer", "learner"],
        "communication": ["reviewer", "learner", "optimizer"],
    },
    "deployer": {
        "version": "1.0.0",
        "ownership": ["deployment", "rollback", "environment"],
        "capabilities": ["deploy builds", "rollback", "verify environment health"],
        "inputs": ["reviewed build", "deployment approval", "target environment"],
        "outputs": ["deployment record", "post-deploy health", "rollback record"],
        "events": ["deploy.started", "deploy.completed", "deploy.rolled_back"],
        "errors": ["deploy_failed"],
        "artifacts": ["deployment record", "health check"],
        "dependencies": ["reviewer", "builder"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "deploy",
        "resources": {"max_files": 5, "max_minutes": 5},
        "timeout": 300,
        "retry": 2,
        "status": "idle",
        "compatibility": ["reviewer", "builder", "governor"],
        "communication": ["reviewer", "orchestrator"],
    },
    "learner": {
        "version": "1.0.0",
        "ownership": ["lessons", "knowledge-lifecycle"],
        "capabilities": ["extract lessons", "update knowledge lifecycle", "verify learning"],
        "inputs": ["mission outcome", "failure records", "review reports"],
        "outputs": ["verified lessons", "knowledge lifecycle transitions"],
        "events": ["learning.started", "lesson.verified", "knowledge.updated"],
        "errors": ["learning_failed"],
        "artifacts": ["lesson records", "knowledge updates"],
        "dependencies": ["builder", "reviewer"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "lesson",
        "resources": {"max_files": 5, "max_minutes": 5},
        "timeout": 300,
        "retry": 2,
        "status": "idle",
        "compatibility": ["builder", "reviewer", "optimizer"],
        "communication": ["optimizer", "reviewer"],
    },
    "optimizer": {
        "version": "1.0.0",
        "ownership": ["performance", "technical-debt"],
        "capabilities": ["optimize performance", "reduce technical debt", "benchmark"],
        "inputs": ["benchmark baseline", "performance report", "technical debt registry"],
        "outputs": ["benchmark comparison", "optimization proposal"],
        "events": ["optimization.started", "optimization.benchmarked", "optimization.proposed"],
        "errors": ["optimization_failed"],
        "artifacts": ["benchmark reports", "optimization proposals"],
        "dependencies": ["learner", "reviewer"],
        "health": "healthy",
        "progress": "idle",
        "checkpoint": "benchmark",
        "resources": {"max_files": 10, "max_minutes": 5},
        "timeout": 300,
        "retry": 3,
        "status": "idle",
        "compatibility": ["learner", "reviewer", "builder"],
        "communication": ["learner", "builder"],
    },
}


class Severity(StrEnum):
    """Violation / risk severity model (Constitution 32.3)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class MissionStatus(StrEnum):
    """Phase 1 — lifecycle states for a mission."""

    QUEUED = "queued"
    SCHEDULED = "scheduled"
    SIMULATING = "simulating"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    RECOVERED = "recovered"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    """Phase 1 — lifecycle states for an individual task."""

    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Finding:
    """A single finding from an audit or diagnostic pass."""

    id: str
    title: str
    severity: Severity
    category: str
    detail: str = ""
    evidence: str = ""
    proposed_fix: str = ""


@dataclass
class Task:
    """Phase 1/4 — a schedulable unit of mission work."""

    task_id: str
    mission_id: str
    engine: str
    status: str = TaskStatus.WAITING.value
    priority: int = 1  # higher = more urgent
    dependencies: list[str] = field(default_factory=list)
    estimated_minutes: float = 1.0
    assigned_at: str = ""
    result: str = ""


@dataclass
class ExecutionState:
    """Phase 1 — one global execution state for the whole platform."""

    current_mission: str = ""
    mission_history: list[str] = field(default_factory=list)
    running_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    waiting_tasks: list[str] = field(default_factory=list)
    blocked_tasks: list[str] = field(default_factory=list)
    engine_status: dict[str, str] = field(default_factory=dict)
    execution_context: dict[str, str] = field(default_factory=dict)
    context_budget: dict[str, int] = field(default_factory=dict)
    resource_budget: dict[str, Any] = field(default_factory=dict)
    health: str = "healthy"
    locks: list[str] = field(default_factory=list)
    current_owner: str = ""
    current_authority: str = ""
    execution_timeline: list[str] = field(default_factory=list)
    checkpoint_pointer: str = ""
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            k: (list(v) if isinstance(v, (list, dict)) else v)
            for k, v in vars(self).items()
        }


@dataclass
class Lock:
    """Phase 6 — a held resource lock."""

    lock_id: str
    resource: str
    lock_type: str
    owner: str
    acquired_at: str = field(default_factory=utcnow)
    released_at: str = ""
    ttl_seconds: int = 0  # 0 = no expiry; >0 enables automatic unlock


@dataclass
class MetricPoint:
    """Phase 13 — a single observability sample."""

    metric: str
    value: float
    timestamp: str = field(default_factory=utcnow)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class Span:
    """Phase 13 — a single tracing span."""

    span_id: str
    name: str
    engine: str
    parent: str = ""
    started_at: str = field(default_factory=utcnow)
    duration_ms: float = 0.0
    status: str = "ok"
    detail: str = ""


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
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
