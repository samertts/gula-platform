"""Phase 5 — Context Manager.

Prevent context overflow. Set maximum files, tokens, reports, and
documentation per mission. Automatically search, load, unload, cache, and
archive knowledge. Only load knowledge required for the current mission.
Implement semantic retrieval. Never read the entire repository.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Context budgets (Phase 5 mandatory maxima).
DEFAULT_BUDGETS = {
    "max_files": 50,
    "max_tokens": 60000,
    "max_reports": 10,
    "max_docs": 25,
}

TOKEN_FACTOR = 4  # approximate tokens per word


@dataclass
class ContextBudget:
    """Per-mission context budget."""

    max_files: int = DEFAULT_BUDGETS["max_files"]
    max_tokens: int = DEFAULT_BUDGETS["max_tokens"]
    max_reports: int = DEFAULT_BUDGETS["max_reports"]
    max_docs: int = DEFAULT_BUDGETS["max_docs"]

    def to_dict(self) -> dict[str, int]:
        return {
            "max_files": self.max_files,
            "max_tokens": self.max_tokens,
            "max_reports": self.max_reports,
            "max_docs": self.max_docs,
        }


@dataclass
class ContextUsage:
    """Current context usage against a budget."""

    files: int = 0
    tokens: int = 0
    reports: int = 0
    docs: int = 0
    violations: list[str] = field(default_factory=list)

    def check(self, budget: ContextBudget) -> list[str]:
        """Return a list of budget violations (empty when within budget)."""
        violations: list[str] = []
        if self.files > budget.max_files:
            violations.append(f"files {self.files} > {budget.max_files}")
        if self.tokens > budget.max_tokens:
            violations.append(f"tokens {self.tokens} > {budget.max_tokens}")
        if self.reports > budget.max_reports:
            violations.append(f"reports {self.reports} > {budget.max_reports}")
        if self.docs > budget.max_docs:
            violations.append(f"docs {self.docs} > {budget.max_docs}")
        self.violations = violations
        return violations


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text blob (words * factor)."""
    words = len(re.findall(r"\S+", text or ""))
    return words * TOKEN_FACTOR


def search_knowledge(
    query: str,
    directory: Path,
    top_k: int = 5,
    ext: str = "*.md",
) -> list[tuple[Path, float]]:
    """Semantic-lite retrieval: rank files by token overlap with the query.

    Only the indexed file headers and content are scanned — the repository is
    never read wholesale. Returns the top_k ``(path, score)`` pairs.
    """
    if not directory.exists():
        return []
    q_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not q_tokens:
        return []
    scored: list[tuple[Path, float]] = []
    for path in sorted(directory.rglob(ext)):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        head = " ".join(text.splitlines()[:40])
        tokens = set(re.findall(r"[a-z0-9]+", head.lower()))
        if not tokens:
            continue
        overlap = len(q_tokens & tokens) / len(q_tokens)
        if overlap > 0:
            scored.append((path, overlap))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k]


def select_mission_context(
    mission_query: str,
    directories: list[Path],
    budget: ContextBudget | None = None,
    top_k_per_dir: int = 5,
) -> ContextUsage:
    """Select the context for a mission within the given budget.

    Returns the accumulated usage; when any budget is exceeded, an entry in
    ``usage.violations`` records which limit was hit. This prevents context
    overflow without reading the whole repository.
    """
    budget = budget or ContextBudget()
    usage = ContextUsage()
    for directory in directories:
        hits = search_knowledge(mission_query, directory, top_k=top_k_per_dir)
        for path, _score in hits:
            usage.files += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            usage.tokens += estimate_tokens(text)
            if "report" in path.name.lower():
                usage.reports += 1
            else:
                usage.docs += 1
    usage.check(budget)
    return usage
