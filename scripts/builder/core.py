"""Shared constants, dataclasses, and path helpers for the Builder Engine.

The Builder Engine (GULA-BUILDER-001) is the primary engineering execution
system. It transforms a human objective into a complete, verified,
production-ready implementation. It builds on the Execution Kernel
(GULA-KERNEL-001): every Builder phase uses Kernel primitives (state,
checkpoints, findings, severity) and never reimplements Kernel functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.kernel.core import (
    MAX_PHASE_FILES,
    MAX_PHASE_MINUTES,
    REPO_ROOT,
    Severity,
    utcnow,
)

BUILDER_DIR = REPO_ROOT / ".ai" / "core" / "builder"
STATE_DIR = BUILDER_DIR / "state"
CHECKPOINT_DIR = STATE_DIR / "checkpoints"
DOCS_DIR = REPO_ROOT / "docs" / "builder"

MAX_TASK_MINUTES = MAX_PHASE_MINUTES
MAX_TASK_FILES = MAX_PHASE_FILES

# Phase 1 — mission types the Analyzer can classify.
MISSION_TYPES: tuple[str, ...] = (
    "feature",
    "bug",
    "refactor",
    "deployment",
    "security",
    "documentation",
    "infrastructure",
    "performance",
    "testing",
    "architecture",
)

MISSION_TYPE_NAMES: dict[str, str] = {
    "feature": "New capability implemented for the platform",
    "bug": "Defect repaired with a regression test",
    "refactor": "Structure improved without changing behavior",
    "deployment": "Artifact shipped to an environment",
    "security": "Vulnerability or security posture hardened",
    "documentation": "Knowledge captured for humans or agents",
    "infrastructure": "Runtime, CI, or hosting changed",
    "performance": "Latency, memory, or throughput improved",
    "testing": "Verification coverage added or improved",
    "architecture": "System structure or contracts changed",
}

# Keyword signals used to classify free-form objectives deterministically.
MISSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "feature": ("build", "add", "create", "implement", "new", "feature", "support", "introduce"),
    "bug": ("bug", "fix", "error", "broken", "crash", "fails", "regression", "defect", "incorrect"),
    "refactor": ("refactor", "clean up", "restructure", "simplify", "rename", "extract"),
    "deployment": ("deploy", "release", "ship", "rollout", "provision environment"),
    "security": ("security", "vulnerability", "cve", "permission", "authorize", "encrypt", "auth"),
    "documentation": ("document", "documentation", "docstring", "readme", "guide", "manual"),
    "infrastructure": ("docker", "kubernetes", "ci", "terraform", "helm", "infra", "pipeline", "cloud"),
    "performance": ("performance", "slow", "latency", "benchmark", "optimize", "throughput", "memory"),
    "testing": ("test", "coverage", "unit test", "pytest", "verification suite"),
    "architecture": ("architecture", "adr", "design", "module boundary", "contract", "layering"),
}

# Complexity and risk level scales (Phase 1).
COMPLEXITY_LEVELS: tuple[str, ...] = ("trivial", "low", "moderate", "high", "critical")
RISK_LEVELS: tuple[str, ...] = ("negligible", "low", "moderate", "high", "critical")

# Per-mission-type baseline complexity (0-4) and risk (0-4).
TYPE_COMPLEXITY: dict[str, int] = {
    "feature": 2, "bug": 1, "refactor": 2, "deployment": 1, "security": 3,
    "documentation": 0, "infrastructure": 2, "performance": 2, "testing": 1,
    "architecture": 3,
}
TYPE_RISK: dict[str, int] = {
    "feature": 2, "bug": 1, "refactor": 2, "deployment": 3, "security": 4,
    "documentation": 0, "infrastructure": 3, "performance": 1, "testing": 0,
    "architecture": 3,
}

# Engineering surface areas the Impact Analyzer (Phase 3) tracks.
IMPACT_AREAS: tuple[str, ...] = (
    "modules",
    "apis",
    "database",
    "frontend",
    "tests",
    "documentation",
    "deployment",
    "security",
    "knowledge",
    "registry",
)


class MissionStatus(StrEnum):
    """Phase 2 — lifecycle states for a Builder mission."""

    ANALYZED = "analyzed"
    PLANNED = "planned"
    IMPACTED = "impacted"
    EXECUTING = "executing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"


class TaskStatus(StrEnum):
    """Phase 2 — lifecycle states for a single Builder task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class MissionAnalysis:
    """Phase 1 — output of the Mission Analyzer for one objective."""

    mission_id: str
    objective: str
    mission_type: str
    complexity: str
    risk: str
    dependencies: list[str] = field(default_factory=list)
    required_knowledge: list[str] = field(default_factory=list)
    expected_files: list[str] = field(default_factory=list)
    execution_cost: str = ""
    execution_time_minutes: int = 0
    outputs: list[str] = field(default_factory=list)
    verification_strategy: str = ""
    rollback_strategy: str = ""
    confidence: float = 0.0
    analyzed_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {k: (list(v) if isinstance(v, list) else v) for k, v in vars(self).items()}


@dataclass
class PlanTask:
    """Phase 2 — the smallest schedulable unit (max 5 min / 50 files)."""

    task_id: str
    name: str
    estimated_minutes: int = 0
    estimated_files: int = 0
    verification: str = ""
    checkpoint: str = ""
    status: str = TaskStatus.PENDING.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "estimated_minutes": self.estimated_minutes,
            "estimated_files": self.estimated_files,
            "verification": self.verification,
            "checkpoint": self.checkpoint,
            "status": self.status,
        }


@dataclass
class MicroPhase:
    """Phase 2 — a group of tasks under one phase."""

    micro_id: str
    name: str
    tasks: list[PlanTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "micro_id": self.micro_id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
        }


@dataclass
class PlanPhase:
    """Phase 2 — Program > Phase > Micro Phase > Task."""

    phase_id: str
    name: str
    microphases: list[MicroPhase] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "microphases": [m.to_dict() for m in self.microphases],
        }


@dataclass
class MissionPlan:
    """Phase 2 — full decomposition of a mission."""

    plan_id: str
    mission_id: str
    program: str
    phases: list[PlanPhase] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)

    def all_tasks(self) -> list[PlanTask]:
        return [task for phase in self.phases for micro in phase.microphases for task in micro.tasks]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "mission_id": self.mission_id,
            "program": self.program,
            "created_at": self.created_at,
            "phases": [p.to_dict() for p in self.phases],
        }


@dataclass
class ImpactAnalysis:
    """Phase 3 — engineering surface impacted by a mission."""

    mission_id: str
    affected_modules: list[str] = field(default_factory=list)
    affected_apis: list[str] = field(default_factory=list)
    affected_database: list[str] = field(default_factory=list)
    affected_frontend: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    affected_documentation: list[str] = field(default_factory=list)
    affected_deployment: list[str] = field(default_factory=list)
    affected_security: list[str] = field(default_factory=list)
    affected_knowledge: list[str] = field(default_factory=list)
    affected_registry: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {k: (list(v) if isinstance(v, list) else v) for k, v in vars(self).items()}


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
class KnowledgeReference:
    """Phase 6 — a reusable artifact located in the knowledge system."""

    source: str
    path: str
    title: str
    relevance: float = 0.0
    matched: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "path": self.path,
            "title": self.title,
            "relevance": self.relevance,
            "matched": self.matched,
        }


@dataclass
class ReviewFinding:
    """Phase 7 — one self-review finding across a quality area."""

    area: str
    severity: Severity
    detail: str
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "area": self.area,
            "severity": self.severity,
            "detail": self.detail,
            "passed": self.passed,
        }


@dataclass
class ReviewReport:
    """Phase 7 — aggregate self-review verdict."""

    mission_id: str
    findings: list[ReviewFinding] = field(default_factory=list)
    reviewed_at: str = field(default_factory=utcnow)

    def failed(self) -> list[ReviewFinding]:
        return [f for f in self.findings if not f.passed]

    def verdict(self) -> str:
        return "PASS" if not self.failed() else "FAIL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "verdict": self.verdict(),
            "reviewed_at": self.reviewed_at,
            "findings": [f.to_dict() for f in self.findings],
        }


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
