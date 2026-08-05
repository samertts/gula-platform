"""Phase 2 — Skill Generation.

Automatically create a reusable Skill when a completed mission produced a
reusable solution. Each Skill carries a unique ID, category, technology,
confidence level, difficulty, dependencies, verification steps, and a
version. Skills persist as versioned markdown in `.ai/core/skills/` and are
registered so the next mission can reuse them instead of re-solving.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.learner.core import (
    CONFIDENCE_LEVELS,
    DIFFICULTY_LEVELS,
    SKILL_CATEGORIES,
    Extraction,
    Skill,
)

SKILL_DIR = REPO_ROOT / ".ai" / "core" / "skills"
ID_RE = re.compile(r"SKILL-(\d{6})")


def next_skill_id() -> str:
    """Return the next sequential skill ID based on existing files."""
    if not SKILL_DIR.exists():
        return "SKILL-000001"
    highest = 0
    for path in SKILL_DIR.glob("*.md"):
        match = ID_RE.search(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"SKILL-{highest + 1:06d}"


def infer_category(extraction: Extraction) -> str:
    """Choose the most fitting skill category from the extraction text."""
    text = " ".join([
        extraction.problem,
        extraction.solution,
        extraction.cause,
    ]).lower()
    tokens = set(re.findall(r"[a-z0-9]+", text))
    keyword_map = {
        "infrastructure": ("docker", "compose", "k8s", "kubernetes", "deploy", "redis", "postgres"),
        "backend": ("api", "service", "model", "database", "sql", "fastapi"),
        "frontend": ("react", "component", "typescript", "ui", "page", "frontend"),
        "database": ("migration", "sql", "index", "query", "schema"),
        "security": ("secret", "tls", "auth", "permission", "cve", "security"),
        "testing": ("test", "pytest", "fixture", "coverage"),
        "deployment": ("deploy", "release", "rollback", "snapshot", "registry"),
        "tooling": ("lint", "ruff", "shell", "path", "env", "node", "npm"),
        "architecture": ("architecture", "clean", "ddd", "dependency", "module"),
        "performance": ("benchmark", "latency", "memory", "perf", "cache"),
    }
    for category, keywords in keyword_map.items():
        if any(keyword in tokens for keyword in keywords):
            return category
    return "tooling"


def generate_skill(
    extraction: Extraction,
    *,
    title: str = "",
    technology: str = "",
    confidence: str = "medium",
    difficulty: str = "medium",
    dependencies: list[str] | None = None,
    verification: str = "",
) -> Skill | None:
    """Create a Skill when the extraction is reusable; otherwise return None."""
    if not extraction.reusable:
        return None
    if confidence not in CONFIDENCE_LEVELS:
        raise ValueError(f"invalid confidence level: {confidence}")
    if difficulty not in DIFFICULTY_LEVELS:
        raise ValueError(f"invalid difficulty level: {difficulty}")
    category = infer_category(extraction)
    if category not in SKILL_CATEGORIES:
        raise ValueError(f"invalid skill category: {category}")

    skill_id = next_skill_id()
    return Skill(
        skill_id=skill_id,
        title=title or _title_from_problem(extraction.problem),
        category=category,
        technology=technology,
        confidence=confidence,
        difficulty=difficulty,
        dependencies=list(dependencies or []),
        verification=verification or _default_verification(extraction),
        version="1.0",
        problem=extraction.problem,
        solution=extraction.solution,
    )


def persist_skill(skill: Skill) -> Path:
    """Write a Skill as versioned markdown and return its path."""
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(skill.title)
    path = SKILL_DIR / f"{skill.skill_id}_{slug}.md"
    path.write_text(_render(skill), encoding="utf-8")
    return path


def skill_exists(title: str) -> bool:
    """True when a skill with the same title already exists (no duplicates)."""
    needle = _slug(title)
    if not SKILL_DIR.exists():
        return False
    return any(_slug(p.stem.split("_", 1)[-1]) == needle for p in SKILL_DIR.glob("*.md"))


def find_skill_by_title(title: str) -> Skill | None:
    """Return the existing skill matching a title (reuse, never duplicate)."""
    needle = _slug(title)
    if not SKILL_DIR.exists():
        return None
    for path in SKILL_DIR.glob("*.md"):
        if _slug(path.stem.split("_", 1)[-1]) == needle:
            match = ID_RE.search(path.name)
            if match:
                text = path.read_text(encoding="utf-8", errors="replace")
                frontmatter = text.split("---", 2)[1] if text.count("---") >= 2 else ""
                confidence = "medium"
                category = "tooling"
                import re as _re
                conf = _re.search(r"confidence:\s*(\w+)", frontmatter)
                if conf:
                    confidence = conf.group(1)
                cat = _re.search(r"category:\s*(\w+)", frontmatter)
                if cat:
                    category = cat.group(1)
                return Skill(
                    skill_id=match.group(0),
                    title=title,
                    category=category,
                    confidence=confidence,
                )
    return None


def _render(skill: Skill) -> str:
    deps = ", ".join(skill.dependencies) or "—"
    return "\n".join([
        "---",
        f"id: {skill.skill_id}",
        "type: skill",
        f"title: {skill.title}",
        f'version: "{skill.version}"',
        f'created: "{utcnow()[:10]}"',
        "status: verified",
        f"confidence: {skill.confidence}",
        f"difficulty: {skill.difficulty}",
        f"category: {skill.category}",
        f"technology: {skill.technology}",
        f"dependencies: [{deps}]",
        "---",
        "",
        f"# {skill.skill_id}: {skill.title}",
        "",
        "## Problem",
        skill.problem or "—",
        "",
        "## Solution",
        skill.solution or "—",
        "",
        "## Verification",
        skill.verification or "—",
        "",
        "## Changelog",
        "| Version | Date | Author | Change |",
        "|---|---|---|---|",
        f"| {skill.version} | {utcnow()[:10]} | GULA-LEARNER | Initial creation |",
        "",
    ])


def _title_from_problem(problem: str) -> str:
    words = problem.strip().rstrip(".").split()
    return " ".join(words[:8]).title() if words else "Untitled Skill"


def _default_verification(extraction: Extraction) -> str:
    if extraction.security_impact:
        return f"Verify security impact: {extraction.security_impact}"
    if extraction.performance_impact:
        return f"Verify performance impact: {extraction.performance_impact}"
    return "Run the relevant test suite and confirm zero regressions"


def _slug(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
    return cleaned[:48]
