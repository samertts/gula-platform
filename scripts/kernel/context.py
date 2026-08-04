"""Phase 7 — Context Engine.

Semantic search, lazy loading, context compression, context ranking,
knowledge ranking, token/file budgets, automatic unload, and automatic
caching. Never loads unnecessary files. Builds on the Governor's context
manager (Phase 5 of GULA-GOVERNOR-001) for budgets and retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.governor.context_manager import (
    ContextBudget,
    ContextUsage,
    estimate_tokens,
    search_knowledge,
    select_mission_context,
)

DEFAULT_BUDGETS = {"max_files": 50, "max_tokens": 60000}


@dataclass
class CacheEntry:
    """A lazily loaded file held in the context cache."""

    path: str
    tokens: int
    last_used_seq: int = 0


class ContextEngine:
    """Per-mission context cache with LRU auto-unload and token budgeting."""

    def __init__(self, budget: ContextBudget | None = None) -> None:
        self.budget = budget or ContextBudget()
        self._cache: dict[str, CacheEntry] = {}
        self._seq = 0
        self.loaded: list[str] = []

    @property
    def cached_files(self) -> list[str]:
        return sorted(self._cache)

    @property
    def token_usage(self) -> int:
        return sum(entry.tokens for entry in self._cache.values())

    def load(self, path: Path) -> str:
        """Lazily load a file into the cache (never loads the whole repo)."""
        key = str(path)
        if key in self._cache:
            self._seq += 1
            self._cache[key].last_used_seq = self._seq
            return path.read_text(encoding="utf-8", errors="ignore")
        text = path.read_text(encoding="utf-8", errors="ignore")
        self._seq += 1
        self._cache[key] = CacheEntry(key, estimate_tokens(text), self._seq)
        if key not in self.loaded:
            self.loaded.append(key)
        self.auto_unload()
        return text

    def unload(self, path: Path) -> bool:
        key = str(path)
        return self._cache.pop(key, None) is not None

    def auto_unload(self, keep: int | None = None) -> list[str]:
        """Evict least-recently-used entries when the file budget is exceeded."""
        max_files = keep or self.budget.max_files
        evicted: list[str] = []
        while len(self._cache) > max_files:
            victim = min(self._cache, key=lambda k: self._cache[k].last_used_seq)
            self._cache.pop(victim, None)
            evicted.append(victim)
        return evicted

    def compress(self, text: str, max_tokens: int | None = None) -> str:
        """Compress a text blob to fit within a token budget (truncate).

        Truncation keeps the head (introduction) and tail (conclusion) so the
        most informative parts of a document survive compression.
        """
        limit = max_tokens or self.budget.max_tokens
        tokens = estimate_tokens(text)
        if tokens <= limit:
            return text
        head = text[: limit * 3]
        tail = text[-limit * 2:]
        return f"{head}\n[...compressed...]\n{tail}"

    def search(self, query: str, directory: Path, top_k: int = 5) -> list[tuple[Path, float]]:
        """Semantic-lite retrieval ranking files by token overlap."""
        return search_knowledge(query, directory, top_k=top_k)

    def select_context(self, query: str, directories: list[Path]) -> ContextUsage:
        """Select mission context within the budget; records violations."""
        return select_mission_context(query, directories, budget=self.budget)

    def rank_hits(self, hits: list[tuple[Path, float]]) -> list[tuple[Path, float]]:
        """Rank retrieval hits by score (descending) with stable ties."""
        return sorted(hits, key=lambda h: (h[1], str(h[0])), reverse=True)

    def budget_violations(self, usage: ContextUsage) -> list[str]:
        return usage.check(self.budget)

    def cache_stats(self) -> dict[str, int]:
        return {
            "files": len(self._cache),
            "tokens": self.token_usage,
            "max_files": self.budget.max_files,
            "max_tokens": self.budget.max_tokens,
        }
