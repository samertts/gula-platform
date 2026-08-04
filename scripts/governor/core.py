"""Shared constants, dataclasses, and path helpers for the Governor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOVERNOR_DIR = REPO_ROOT / ".ai" / "core" / "governor"
STATE_DIR = GOVERNOR_DIR / "state"
CHECKPOINT_DIR = STATE_DIR / "checkpoints"
DOCS_DIR = REPO_ROOT / "docs" / "governor"

MAX_PHASE_MINUTES = 5
MAX_PHASE_FILES = 50

# Immutable chain of authority (Phase 1). Index 0 is the highest authority.
AUTHORITY_CHAIN: tuple[str, ...] = (
    "constitution",
    "governor",
    "architect",
    "orchestrator",
    "reviewer",
    "builder",
    "deployer",
    "learner",
    "optimizer",
)

# The authoritative engine registry used by the mission router and
# self-governance audit (Phase 2 / Phase 11). Every engine exposes the
# full Phase 10 communication contract: inputs, outputs, status, events,
# progress, health, errors, artifacts, dependencies, completion.
ENGINE_REGISTRY: dict[str, dict[str, Any]] = {
    "architect": {
        "authority_rank": 2,
        "responsibilities": [
            "approve architectural decisions",
            "enforce Clean Architecture / SOLID / DDD",
            "approve ADRs",
        ],
        "artifacts": ["ADR", "architecture-compliance report"],
        "inputs": ["mission brief", "impact analysis", "ADR proposal"],
        "outputs": ["approved ADR", "architecture decision", "architecture compliance verdict"],
        "status": "idle",
        "events": ["decision.requested", "decision.approved", "decision.rejected"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["constitution", "governor"],
        "completion": "decision issued",
    },
    "orchestrator": {
        "authority_rank": 3,
        "responsibilities": [
            "coordinate multi-engine missions",
            "manage mission lifecycle",
            "enforce phase budgets",
        ],
        "artifacts": ["mission plan", "phase checkpoints"],
        "inputs": ["mission routing result", "engine availability"],
        "outputs": ["execution plan", "phase transitions", "checkpoint records"],
        "status": "idle",
        "events": ["mission.started", "phase.completed", "mission.completed"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["governor", "architect"],
        "completion": "mission plan delivered",
    },
    "reviewer": {
        "authority_rank": 4,
        "responsibilities": [
            "review code, docs, knowledge",
            "approve deployments",
            "gate quality",
        ],
        "artifacts": ["review report", "approval record"],
        "inputs": ["change set", "test results", "deployment request"],
        "outputs": ["review verdict", "deployment approval"],
        "status": "idle",
        "events": ["review.requested", "review.approved", "review.rejected"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["orchestrator", "builder"],
        "completion": "review verdict issued",
    },
    "builder": {
        "authority_rank": 5,
        "responsibilities": [
            "implement changes",
            "write tests",
            "create knowledge artifacts",
        ],
        "artifacts": ["code changes", "tests"],
        "inputs": ["approved plan", "impact analysis", "test stubs"],
        "outputs": ["implemented change", "passing tests", "knowledge artifact draft"],
        "status": "idle",
        "events": ["build.started", "build.completed", "build.failed"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["architect", "reviewer"],
        "completion": "change delivered for review",
    },
    "deployer": {
        "authority_rank": 6,
        "responsibilities": [
            "deploy builds",
            "rollback",
            "environment health",
        ],
        "artifacts": ["deployment record", "health check"],
        "inputs": ["reviewed build", "deployment approval", "target environment"],
        "outputs": ["deployment record", "post-deploy health", "rollback record"],
        "status": "idle",
        "events": ["deploy.started", "deploy.completed", "deploy.rolled_back"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["reviewer", "builder"],
        "completion": "deployment verified",
    },
    "learner": {
        "authority_rank": 7,
        "responsibilities": [
            "extract lessons",
            "update knowledge lifecycle",
            "verify learning",
        ],
        "artifacts": ["lesson records", "knowledge updates"],
        "inputs": ["mission outcome", "failure records", "review reports"],
        "outputs": ["verified lessons", "knowledge lifecycle transitions"],
        "status": "idle",
        "events": ["learning.started", "lesson.verified", "knowledge.updated"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["builder", "reviewer"],
        "completion": "lessons verified and recorded",
    },
    "optimizer": {
        "authority_rank": 8,
        "responsibilities": [
            "optimize performance with benchmarks",
            "reduce technical debt",
        ],
        "artifacts": ["benchmark reports", "optimization proposals"],
        "inputs": ["benchmark baseline", "performance report", "technical debt registry"],
        "outputs": ["benchmark comparison", "optimization proposal"],
        "status": "idle",
        "events": ["optimization.started", "optimization.benchmarked", "optimization.proposed"],
        "progress": "0",
        "health": "healthy",
        "errors": [],
        "dependencies": ["learner", "reviewer"],
        "completion": "benchmarked proposal delivered",
    },
}

# Lifecycle states for knowledge artifacts (Phase 4).
KNOWLEDGE_LIFECYCLE: tuple[str, ...] = ("draft", "verified", "approved", "deprecated", "archived")


class Severity(StrEnum):
    """Violation / risk severity model (Constitution 32.3)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Finding:
    """A single finding from an audit or self-governance pass."""

    id: str
    title: str
    severity: Severity
    category: str
    detail: str = ""
    evidence: str = ""
    proposed_fix: str = ""


@dataclass
class Mission:
    """Mission classification record (Phase 2)."""

    mission_id: str
    name: str
    mission_type: str
    size: str
    risk: str
    complexity: int
    required_engines: list[str] = field(default_factory=list)
    reason: str = ""


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import json

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
