"""GULA-KERNEL-EXT-001 Phase 9 — Enterprise AI Memory.

Multi-tier memory: long-term, working, semantic, decision, and failure
tiers with recall, promotion, archival, and access accounting. Composes
the Kernel knowledge layer (scripts/kernel/knowledge.py search/rank) —
entries here are operational memory records, artifacts stay in knowledge.
Deterministic and testable; no I/O at import time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow

MEMORY_DIR = ".ai/core/memory/"

TIERS = ("long_term", "working", "semantic", "decision", "failure")

PROMOTION_ACCESSES = 3
ARCHIVE_ACCESS_THRESHOLD = 0


class MemoryError(Exception):
    """Raised for invalid memory operations."""


@dataclass
class MemoryEntry:
    """One operational memory record."""

    id: str
    tier: str
    content: str
    tags: list[str] = field(default_factory=list)
    source: str = ""
    created_at: str = field(default_factory=utcnow)
    last_accessed_at: str = ""
    access_count: int = 0
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.id.startswith("MEM-"):
            raise MemoryError(f"memory id must start with MEM-: {self.id!r}")
        if self.tier not in TIERS:
            raise MemoryError(f"unknown tier: {self.tier!r}")
        if not self.content.strip():
            raise MemoryError("memory content is required")
        if self.access_count < 0:
            raise MemoryError("access_count cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tier": self.tier,
            "content": self.content,
            "tags": list(self.tags),
            "source": self.source,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
            "access_count": self.access_count,
            "archived": self.archived,
        }


class MemoryStore:
    """Tiered memory with recall, promotion, archival, and audit."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._counters: dict[str, int] = {}
        self._history: list[dict[str, Any]] = []

    def remember(self, tier: str, content: str, tags: list[str] | None = None,
                 source: str = "") -> MemoryEntry:
        n = self._counters.get(tier, 0) + 1
        self._counters[tier] = n
        entry = MemoryEntry(f"MEM-{abs(hash((tier, n))) % 1000000:06d}", tier, content,
                            tags or [], source)
        self._entries[entry.id] = entry
        self._history.append({"event": "remembered", "id": entry.id, "tier": tier, "at": utcnow()})
        return entry

    def recall(self, query: str, tier: str | None = None, top_k: int = 5) -> list[MemoryEntry]:
        """Search active entries by content/tag substring (deterministic order)."""
        query = query.lower()
        candidates = [
            e for e in self._entries.values()
            if not e.archived and (tier is None or e.tier == tier)
        ]
        scored = []
        for entry in candidates:
            score = 0
            if query in entry.content.lower():
                score += 2
            if any(query in tag.lower() for tag in entry.tags):
                score += 1
            if score:
                scored.append((score, entry))
        ranked = sorted(scored, key=lambda pair: (-pair[0], pair[1].id))
        return [e for _, e in ranked[:top_k]]

    def entries(self, tier: str | None = None) -> list[MemoryEntry]:
        if tier is None:
            return list(self._entries.values())
        return [e for e in self._entries.values() if e.tier == tier]

    def touch(self, entry_id: str) -> MemoryEntry:
        entry = self._get(entry_id)
        entry.access_count += 1
        entry.last_accessed_at = utcnow()
        self._history.append({"event": "accessed", "id": entry_id, "at": entry.last_accessed_at})
        return entry

    def _get(self, entry_id: str) -> MemoryEntry:
        try:
            return self._entries[entry_id]
        except KeyError:
            raise MemoryError(f"unknown memory entry: {entry_id}") from None

    def promote(self, entry_id: str) -> MemoryEntry:
        """Working-memory entries reach promotion access count move to long-term."""
        entry = self._get(entry_id)
        if entry.tier != "working":
            raise MemoryError(f"only working entries can be promoted: {entry.tier}")
        if entry.access_count < PROMOTION_ACCESSES:
            raise MemoryError(
                f"working entry needs {PROMOTION_ACCESSES} accesses, has {entry.access_count}"
            )
        entry.tier = "long_term"
        self._history.append({"event": "promoted", "id": entry_id, "at": utcnow()})
        return entry

    def archive(self, entry_id: str) -> MemoryEntry:
        entry = self._get(entry_id)
        if entry.archived:
            raise MemoryError(f"already archived: {entry_id}")
        entry.archived = True
        self._history.append({"event": "archived", "id": entry_id, "at": utcnow()})
        return entry

    def archive_unaccessed(self) -> int:
        """Archive active entries never accessed since creation."""
        count = 0
        for entry in self._entries.values():
            if not entry.archived and entry.access_count == ARCHIVE_ACCESS_THRESHOLD:
                entry.archived = True
                count += 1
                self._history.append({"event": "archived", "id": entry.id, "at": utcnow()})
        return count

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "entries": [e.to_dict() for e in self._entries.values()],
            "history": list(self._history),
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path
