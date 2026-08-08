"""Shared constants, dataclasses, and path helpers for the Learning Engine.

The Learning Engine (GULA-LEARNER-001) transforms every completed mission
into permanent engineering knowledge. It never develops features and never
deploys software. Its responsibility is to continuously improve the
intelligence of the entire engineering platform.

Knowledge belongs to the repository, never to an AI session. Every solved
problem permanently improves the platform: problems are extracted into
skills, playbooks, runbooks, memory, and the knowledge graph. Knowledge is
always searchable, versioned, and auditable.

The engine integrates with the Builder (produces code), the Reviewer
(verifies change sets), the Orchestrator (records mission history), and the
Deployer (records deployment history). It mirrors the Kernel's primitives
(state, severity, phase budgets) and stays independent of the other
engines' internals.
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

LEARNER_DIR = REPO_ROOT / ".ai" / "core" / "learner"
STATE_DIR = LEARNER_DIR / "state"
EXTRACTION_DIR = STATE_DIR / "extractions"
PATTERN_DIR = STATE_DIR / "patterns"
PROPOSAL_DIR = STATE_DIR / "proposals"
HISTORY_DIR = LEARNER_DIR / "history"
DOCS_DIR = REPO_ROOT / "docs" / "learner"
REPORT_PATH = REPO_ROOT / "docs/reports/LEARNER_IMPLEMENTATION_REPORT.md"
AUDIT_PATH = REPO_ROOT / "docs/reports/LEARNER_AUDIT_REPORT.md"

MAX_TASK_MINUTES = MAX_PHASE_MINUTES
MAX_TASK_FILES = MAX_PHASE_FILES

# Knowledge stores the Learner owns or audits (Phase 0).
AUDIT_COMPONENTS: tuple[str, ...] = (
    "registry",
    "graph",
    "memory",
    "skills",
    "playbooks",
    "runbooks",
    "adr",
    "constitution",
    "bridge-files",
    "templates",
    "reports",
    "search-indexes",
)

# Fields every extraction captures (Phase 1).
EXTRACTION_FIELDS: tuple[str, ...] = (
    "problem",
    "cause",
    "solution",
    "alternative_solutions",
    "rejected_solutions",
    "tradeoffs",
    "risks",
    "lessons",
    "performance_impact",
    "security_impact",
    "recommendations",
)

# Skill categories (Phase 2).
SKILL_CATEGORIES: tuple[str, ...] = (
    "infrastructure",
    "backend",
    "frontend",
    "database",
    "security",
    "testing",
    "deployment",
    "tooling",
    "architecture",
    "performance",
)

# Skill confidence levels (Phase 2).
CONFIDENCE_LEVELS: tuple[str, ...] = ("low", "medium", "high", "verified")

# Skill difficulty levels (Phase 2).
DIFFICULTY_LEVELS: tuple[str, ...] = ("easy", "medium", "hard")

# Playbook categories (Phase 3).
PLAYBOOK_KINDS: tuple[str, ...] = (
    "deployment",
    "recovery",
    "debugging",
    "performance",
    "security",
    "testing",
    "infrastructure",
)

# Runbook categories (Phase 4).
RUNBOOK_KINDS: tuple[str, ...] = (
    "incidents",
    "recovery",
    "monitoring",
    "production",
    "maintenance",
    "scaling",
    "backup",
    "rollback",
)

# Memory stores the Learner evolves (Phase 5).
MEMORY_KINDS: tuple[str, ...] = (
    "project",
    "engineering",
    "decision",
    "architecture",
    "deployment",
)

# Recurring-pattern kinds (Phase 6).
PATTERN_KINDS: tuple[str, ...] = (
    "repeated-bug",
    "repeated-refactoring",
    "repeated-design",
    "repeated-deployment-failure",
    "repeated-performance-issue",
    "repeated-security-finding",
)

# Engines the Learner evaluates for self-improvement (Phase 7).
ENGINES_EVALUATED: tuple[str, ...] = (
    "builder",
    "reviewer",
    "orchestrator",
    "deployer",
    "quality-system",
    "knowledge-system",
)

# Knowledge quality checks (Phase 8).
QUALITY_CHECKS: tuple[str, ...] = (
    "duplicate-ids",
    "broken-references",
    "registry-consistency",
    "graph-consistency",
    "version-consistency",
    "confidence-levels",
    "knowledge-coverage",
)


class KnowledgeStatus(StrEnum):
    PLANNED = "planned"
    EXTRACTED = "extracted"
    VERIFIED = "verified"
    OBSOLETE = "obsolete"
    DEPRECATED = "deprecated"


class ProposalStatus(StrEnum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


@dataclass
class KnowledgeItem:
    """A typed unit of knowledge (skill, playbook, runbook, lesson, ...)."""

    item_id: str
    kind: str
    title: str
    version: str = "1.0"
    status: str = KnowledgeStatus.EXTRACTED.value
    confidence: str = "medium"
    tags: list[str] = field(default_factory=list)
    body: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "title": self.title,
            "version": self.version,
            "status": self.status,
            "confidence": self.confidence,
            "tags": self.tags,
            "body": self.body,
            "created_at": self.created_at,
        }


@dataclass
class Extraction:
    """Structured knowledge extracted from a completed mission (Phase 1)."""

    source: str
    problem: str = ""
    cause: str = ""
    solution: str = ""
    alternative_solutions: list[str] = field(default_factory=list)
    rejected_solutions: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    performance_impact: str = ""
    security_impact: str = ""
    recommendations: list[str] = field(default_factory=list)
    reusable: bool = False
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "problem": self.problem,
            "cause": self.cause,
            "solution": self.solution,
            "alternative_solutions": self.alternative_solutions,
            "rejected_solutions": self.rejected_solutions,
            "tradeoffs": self.tradeoffs,
            "risks": self.risks,
            "lessons": self.lessons,
            "performance_impact": self.performance_impact,
            "security_impact": self.security_impact,
            "recommendations": self.recommendations,
            "reusable": self.reusable,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Extraction:
        return cls(
            source=data.get("source", ""),
            problem=data.get("problem", ""),
            cause=data.get("cause", ""),
            solution=data.get("solution", ""),
            alternative_solutions=data.get("alternative_solutions", []),
            rejected_solutions=data.get("rejected_solutions", []),
            tradeoffs=data.get("tradeoffs", []),
            risks=data.get("risks", []),
            lessons=data.get("lessons", []),
            performance_impact=data.get("performance_impact", ""),
            security_impact=data.get("security_impact", ""),
            recommendations=data.get("recommendations", []),
            reusable=data.get("reusable", False),
            created_at=data.get("created_at", ""),
        )


@dataclass
class Skill:
    """A reusable solution with metadata (Phase 2)."""

    skill_id: str
    title: str
    category: str
    technology: str = ""
    confidence: str = "medium"
    difficulty: str = "medium"
    dependencies: list[str] = field(default_factory=list)
    verification: str = ""
    version: str = "1.0"
    problem: str = ""
    solution: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "title": self.title,
            "category": self.category,
            "technology": self.technology,
            "confidence": self.confidence,
            "difficulty": self.difficulty,
            "dependencies": self.dependencies,
            "verification": self.verification,
            "version": self.version,
            "problem": self.problem,
            "solution": self.solution,
            "created_at": self.created_at,
        }


@dataclass
class Pattern:
    """A recurring engineering pattern with reusable knowledge (Phase 6)."""

    pattern_id: str
    kind: str
    area: str
    count: int
    threshold: int
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "kind": self.kind,
            "area": self.area,
            "count": self.count,
            "threshold": self.threshold,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "created_at": self.created_at,
        }


@dataclass
class Proposal:
    """An improvement proposal for the platform (Phase 7)."""

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
class QualityReport:
    """Knowledge-quality verification results (Phase 8)."""

    total_items: int = 0
    duplicate_ids: list[str] = field(default_factory=list)
    broken_references: list[str] = field(default_factory=list)
    registry_consistent: bool = True
    graph_consistent: bool = True
    version_consistent: bool = True
    confidence_consistent: bool = True
    coverage_pct: float = 0.0
    health_score: int = 100
    checks: dict[str, str] = field(default_factory=dict)


def make_id(prefix: str) -> str:
    """Generate a unique identifier with a stable prefix."""
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def ensure_dirs() -> None:
    """Create all Learner state directories."""
    for directory in (STATE_DIR, EXTRACTION_DIR, PATTERN_DIR, PROPOSAL_DIR, HISTORY_DIR):
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
