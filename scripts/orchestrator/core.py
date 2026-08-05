"""Shared constants, dataclasses, and path helpers for the Orchestrator Engine.

The Orchestrator Engine (GULA-ORCHESTRATOR-001) is the executive brain of the
engineering platform. It never writes production code and never performs
reviews directly; it coordinates every engineering activity. It transforms a
single human objective into a complete, managed engineering workflow by
classifying, planning, routing, scheduling, checkpointing, and tracking work
that is executed by the other engines (Builder, Reviewer, Deployer, Learner,
Optimizer, Kernel).

It builds on the Execution Kernel (GULA-KERNEL-001) primitives (state,
findings, severity, phase budgets) and stays independent of the Builder and
Reviewer implementations (it talks to their contracts, not their internals).
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

ORCHESTRATOR_DIR = REPO_ROOT / ".ai" / "core" / "orchestrator"
STATE_DIR = ORCHESTRATOR_DIR / "state"
CHECKPOINT_DIR = STATE_DIR / "checkpoints"
MISSION_DIR = STATE_DIR / "missions"
HISTORY_DIR = ORCHESTRATOR_DIR / "history"
DOCS_DIR = REPO_ROOT / "docs" / "orchestrator"

MAX_TASK_MINUTES = MAX_PHASE_MINUTES
MAX_TASK_FILES = MAX_PHASE_FILES

# Engines the Orchestrator can route work to (Phase 3). The Orchestrator never
# performs these activities itself.
ENGINES: tuple[str, ...] = (
    "kernel",
    "builder",
    "reviewer",
    "deployer",
    "learner",
    "optimizer",
)

# Engineering surfaces mapped to the engine that owns them.
SURFACE_ROUTING: dict[str, str] = {
    "backend": "builder",
    "frontend": "builder",
    "database": "builder",
    "deployment": "deployer",
    "verification": "reviewer",
    "knowledge": "learner",
    "optimization": "optimizer",
    "architecture": "builder",
    "security": "builder",
    "infrastructure": "deployer",
    "testing": "builder",
    "documentation": "learner",
    "observability": "optimizer",
    "research": "learner",
}

# Mission types the Classifier can determine (superset of Builder types).
MISSION_TYPES: tuple[str, ...] = (
    "feature",
    "bug",
    "refactor",
    "deployment",
    "security",
    "performance",
    "architecture",
    "documentation",
    "knowledge",
    "infrastructure",
    "testing",
    "research",
)

MISSION_TYPE_NAMES: dict[str, str] = {
    "feature": "New capability implemented for the platform",
    "bug": "Defect repaired with a regression test",
    "refactor": "Structure improved without changing behavior",
    "deployment": "Artifact shipped to an environment",
    "security": "Vulnerability or security posture hardened",
    "performance": "Latency, memory, or throughput improved",
    "architecture": "System structure or contracts changed",
    "documentation": "Knowledge captured for humans or agents",
    "knowledge": "Platform knowledge learned and stored",
    "infrastructure": "Runtime, CI, or hosting changed",
    "testing": "Verification coverage added or improved",
    "research": "Investigation without committed code",
}

MISSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "feature": ("build", "add", "create", "implement", "new", "feature", "support", "introduce"),
    "bug": ("bug", "fix", "error", "broken", "crash", "fails", "regression", "defect", "incorrect"),
    "refactor": ("refactor", "clean up", "restructure", "simplify", "rename", "extract", "tidy"),
    "deployment": ("deploy", "release", "ship", "rollout", "provision environment", "publish"),
    "security": ("security", "vulnerability", "cve", "permission", "authorize", "encrypt", "auth", "harden"),
    "performance": ("performance", "slow", "latency", "benchmark", "optimize", "throughput", "memory", "profile"),
    "architecture": ("architecture", "adr", "design", "module boundary", "contract", "layering", "hexagonal"),
    "documentation": ("document", "documentation", "docstring", "readme", "guide", "manual"),
    "knowledge": ("knowledge", "learn", "lesson", "playbook", "brain", "index", "registry"),
    "infrastructure": ("docker", "kubernetes", "ci/cd", "terraform", "helm", "infra", "pipeline", "cloud", "runner"),
    "testing": ("test", "coverage", "unit test", "pytest", "verification suite", "vitest"),
    "research": ("research", "investigate", "analyze", "study", "survey", "evaluate"),
}

# Baseline complexity (0-4) and risk (0-4) per mission type.
TYPE_COMPLEXITY: dict[str, int] = {
    "feature": 2, "bug": 1, "refactor": 2, "deployment": 1, "security": 3,
    "performance": 2, "architecture": 3, "documentation": 0, "knowledge": 0,
    "infrastructure": 2, "testing": 1, "research": 1,
}
TYPE_RISK: dict[str, int] = {
    "feature": 2, "bug": 1, "refactor": 2, "deployment": 3, "security": 4,
    "performance": 1, "architecture": 3, "documentation": 0, "knowledge": 0,
    "infrastructure": 3, "testing": 0, "research": 0,
}

# Complexity and priority level scales.
COMPLEXITY_LEVELS: tuple[str, ...] = ("trivial", "low", "moderate", "high", "critical")
PRIORITY_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")
RISK_LEVELS: tuple[str, ...] = ("negligible", "low", "moderate", "high", "critical")

# Duration ranges (minutes) by complexity level.
DURATION_BY_COMPLEXITY: dict[str, tuple[int, int]] = {
    "trivial": (1, 10),
    "low": (10, 40),
    "moderate": (40, 120),
    "high": (120, 300),
    "critical": (300, 600),
}


class MissionStatus(StrEnum):
    """Lifecycle states for an Orchestrator mission."""

    RECEIVED = "received"
    CLASSIFIED = "classified"
    PLANNED = "planned"
    ROUTED = "routed"
    EXECUTING = "executing"
    TRACKING = "tracking"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    CLOSED = "closed"
    FAILED = "failed"


class TaskStatus(StrEnum):
    """Lifecycle states for a routed task."""

    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureClass(StrEnum):
    """Phase 6 — failure taxonomy."""

    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    CONFIGURATION = "configuration"
    CREDENTIAL = "credential"
    INFRASTRUCTURE = "infrastructure"
    IMPLEMENTATION = "implementation"
    KNOWLEDGE = "knowledge"


def make_id(prefix: str) -> str:
    """Generate a short deterministic-unique identifier."""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


@dataclass
class MissionClassification:
    """Phase 1 — the Classifier's verdict on one objective."""

    objective: str
    mission_type: str = ""
    priority: str = "medium"
    complexity: str = "low"
    risk: str = "low"
    dependencies: list[str] = field(default_factory=list)
    duration_minutes: int = 30
    required_specialists: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    classified_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {k: (list(v) if isinstance(v, list) else v) for k, v in vars(self).items()}


@dataclass
class AssignedTask:
    """A work unit routed to an engine (Phase 3)."""

    task_id: str
    name: str
    engine: str
    surface: str
    estimated_minutes: int = 0
    estimated_files: int = 0
    depends_on: list[str] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    evidence: str = ""
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "engine": self.engine,
            "surface": self.surface,
            "estimated_minutes": self.estimated_minutes,
            "estimated_files": self.estimated_files,
            "depends_on": self.depends_on,
            "status": self.status,
            "evidence": self.evidence,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class OrchestratedPlan:
    """Phase 2+4 — mission decomposed and scheduled with dependencies."""

    plan_id: str
    mission_id: str
    objective: str
    program: str = ""
    tasks: list[AssignedTask] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)
    parallel_groups: list[list[str]] = field(default_factory=list)
    critical_path: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)

    def all_done(self) -> bool:
        return all(t.status == TaskStatus.COMPLETED.value for t in self.tasks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "mission_id": self.mission_id,
            "objective": self.objective,
            "program": self.program,
            "tasks": [t.to_dict() for t in self.tasks],
            "execution_order": self.execution_order,
            "parallel_groups": self.parallel_groups,
            "critical_path": self.critical_path,
            "created_at": self.created_at,
        }


@dataclass
class Checkpoint:
    """Phase 5 — durable progress marker for resume-without-restart."""

    checkpoint_id: str
    mission_id: str
    step: str
    state: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "mission_id": self.mission_id,
            "step": self.step,
            "state": self.state,
            "created_at": self.created_at,
        }


@dataclass
class FailureDecision:
    """Phase 6 — outcome of classifying and handling a failure."""

    task_id: str
    error: str
    failure_class: str = FailureClass.PERMANENT.value
    action: str = "escalate"
    retry_allowed: bool = False
    resume_point: str = ""
    human_action_required: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class ResourceUsage:
    """Phase 7 — resource snapshot and split advisory."""

    mission_id: str
    context_bytes: int = 0
    repo_bytes: int = 0
    execution_seconds: int = 0
    files_read: int = 0
    files_modified: int = 0
    memory_bytes: int = 0
    split_recommended: bool = False
    split_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class MissionRecord:
    """Phase 9 — the persistent record of a mission."""

    mission_id: str
    objective: str
    mission_type: str = ""
    status: str = MissionStatus.RECEIVED.value
    priority: str = "medium"
    complexity: str = "low"
    risk: str = "low"
    plan_id: str = ""
    progress_percent: float = 0.0
    health_score: float = 100.0
    assigned_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    timeline: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    failure_history: list[dict[str, Any]] = field(default_factory=list)
    recovery_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)
    closed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "mission_type": self.mission_type,
            "status": self.status,
            "priority": self.priority,
            "complexity": self.complexity,
            "risk": self.risk,
            "plan_id": self.plan_id,
            "progress_percent": self.progress_percent,
            "health_score": self.health_score,
            "assigned_tasks": self.assigned_tasks,
            "completed_tasks": self.completed_tasks,
            "blocked_tasks": self.blocked_tasks,
            "timeline": self.timeline,
            "decisions": self.decisions,
            "failure_history": self.failure_history,
            "recovery_history": self.recovery_history,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    MISSION_DIR.mkdir(parents=True, exist_ok=True)
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
