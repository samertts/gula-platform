"""Phase 6 — Knowledge Integration.

Before solving any problem the Builder searches existing knowledge:
skills, playbooks, runbooks, ADRs, registry, memory, and the constitution.
It reuses existing solutions whenever possible and surfaces them as ranked
KnowledgeReference entries.
"""

from __future__ import annotations

from pathlib import Path

from scripts.builder.core import KnowledgeReference, read_json
from scripts.kernel.core import REPO_ROOT

# Knowledge sources searched in order. Each entry: (label, path, file_globs).
KNOWLEDGE_SOURCES: tuple[tuple[str, Path, tuple[str, ...]], ...] = (
    ("skills", REPO_ROOT / ".ai" / "core" / "skills", ("*.md",)),
    ("playbooks", REPO_ROOT / ".ai" / "core" / "playbooks", ("*.md",)),
    ("runbooks", REPO_ROOT / ".ai" / "core" / "runbooks", ("*.md",)),
    ("adr", REPO_ROOT / "docs" / "adr", ("*.md",)),
    ("registry", REPO_ROOT / ".ai" / "core" / "registry", ("*.md",)),
    ("memory", REPO_ROOT / ".ai" / "core" / "memory", ("*.md",)),
    ("constitution", REPO_ROOT, ("AI_OPERATING_CONSTITUTION.md",)),
    ("failures", REPO_ROOT / ".ai" / "core" / "failures", ("*.md",)),
)


class KnowledgeError(Exception):
    """Raised for invalid knowledge queries."""


def _terms(query: str) -> list[str]:
    return [token for token in query.lower().split() if len(token) >= 3]


def search(query: str, source: str | None = None, limit: int = 20) -> list[KnowledgeReference]:
    """Search knowledge sources for reusable artifacts matching a query."""
    if not query or not query.strip():
        raise KnowledgeError("query must not be empty")
    terms = _terms(query)
    references: list[KnowledgeReference] = []

    for label, root, globs in KNOWLEDGE_SOURCES:
        if source and label != source:
            continue
        if not root.exists():
            continue
        for glob in globs:
            for path in sorted(root.rglob(glob)):
                title = path.stem.replace("_", " ").replace("-", " ")
                matched = _match_file(path, terms)
                if matched:
                    references.append(KnowledgeReference(
                        source=label,
                        path=str(path.relative_to(REPO_ROOT)),
                        title=title,
                        relevance=_relevance(matched),
                        matched=matched,
                    ))

    references.sort(key=lambda ref: ref.relevance, reverse=True)
    return references[:limit]


def _match_file(path: Path, terms: list[str]) -> list[str]:
    """Return terms found in a file's name + first lines."""
    matched: list[str] = []
    text = path.name.lower()
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        text += " " + " ".join(lines[:30]).lower()
    except OSError:
        pass
    for term in terms:
        if term in text and term not in matched:
            matched.append(term)
    return matched


def _relevance(matched: list[str]) -> float:
    """Relevance grows with the number of matched terms (cap 1.0)."""
    return round(min(1.0, len(matched) * 0.35), 2)


def search_memory(query: str, limit: int = 10) -> list[KnowledgeReference]:
    """Search the persistent memory store (JSON) for relevant entries."""
    path = REPO_ROOT / ".ai" / "core" / "memory" / "memory_store.json"
    terms = _terms(query)
    references: list[KnowledgeReference] = []
    data = read_json(path)
    entries = data.get("entries", []) if isinstance(data, dict) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        content = " ".join(
            str(entry.get(key, "")) for key in ("content", "tier", "tags", "id")
        ).lower()
        matched = [term for term in terms if term in content]
        if matched:
            references.append(KnowledgeReference(
                source="memory",
                path=str(path.relative_to(REPO_ROOT)),
                title=str(entry.get("id", "memory-entry")),
                relevance=_relevance(matched),
                matched=matched,
            ))
    references.sort(key=lambda ref: ref.relevance, reverse=True)
    return references[:limit]


def collect(query: str, include_memory: bool = True, limit: int = 20) -> list[KnowledgeReference]:
    """Collect file-based and memory knowledge for a query."""
    references = search(query, limit=limit)
    if include_memory:
        references.extend(search_memory(query))
    references.sort(key=lambda ref: ref.relevance, reverse=True)
    return references[:limit]


def reuse_summary(references: list[KnowledgeReference]) -> str:
    """Compact summary of reuse candidates."""
    if not references:
        return "no reusable knowledge found"
    return "; ".join(f"{ref.source}/{ref.title} ({ref.relevance:.2f})" for ref in references[:5])
