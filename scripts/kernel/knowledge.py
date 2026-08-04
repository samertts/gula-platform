"""Phase 9 — Knowledge Engine.

Knowledge ranking, deduplication, merge, archive, lifecycle, confidence,
health, search, dependencies, and validation. Builds on the Governor's
knowledge governance (Phase 4 of GULA-GOVERNOR-001) and adds archive,
health, search, dependency graphs, and validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.governor.core import KNOWLEDGE_LIFECYCLE
from scripts.governor.knowledge_governance import (
    KnowledgeItem,
    compute_confidence,
    content_similarity,
    find_duplicates,
    merge_items,
    title_similarity,
)

from .core import utcnow


@dataclass
class KnowledgeArtifact:
    """A governed knowledge artifact with Kernel-level metadata."""

    item: KnowledgeItem
    dependencies: list[str] = field(default_factory=list)
    source: str = ""
    archived_at: str = ""
    health: str = "healthy"

    @property
    def artifact_id(self) -> str:
        return self.item.artifact_id


def archive(artifact: KnowledgeArtifact) -> KnowledgeArtifact:
    """Archive a deprecated artifact (final lifecycle state)."""
    if artifact.item.lifecycle != "deprecated":
        artifact.item.lifecycle = "deprecated"
    artifact.item.lifecycle = "archived"
    artifact.item.confidence = compute_confidence(artifact.item)
    artifact.archived_at = utcnow()
    artifact.health = "archived"
    return artifact


def search(items: list[KnowledgeArtifact], query: str, top_k: int = 5) -> list[KnowledgeArtifact]:
    """Rank artifacts by relevance to a query (title + content similarity)."""
    q = query.strip().lower()
    if not q:
        return items[:top_k]
    scored: list[tuple[KnowledgeArtifact, float]] = []
    for artifact in items:
        title_score = title_similarity(artifact.item.title, q)
        content_score = content_similarity(artifact.item.content, query)
        scored.append((artifact, max(title_score, content_score)))
    scored.sort(key=lambda pair: (pair[1], pair[0].artifact_id), reverse=True)
    return [artifact for artifact, _score in scored[:top_k]]


def dependency_graph(items: list[KnowledgeArtifact]) -> dict[str, list[str]]:
    """Build the knowledge dependency graph from declared dependencies."""
    return {
        artifact.artifact_id: list(artifact.dependencies)
        for artifact in items
    }


def health_check(items: list[KnowledgeArtifact]) -> dict[str, object]:
    """Produce a knowledge health summary (Phase 9 deliverable)."""
    counts = dict.fromkeys(KNOWLEDGE_LIFECYCLE, 0)
    for artifact in items:
        counts[artifact.item.lifecycle] = counts.get(artifact.item.lifecycle, 0) + 1
    duplicates = find_duplicates([artifact.item for artifact in items])
    unverified = sum(
        1 for artifact in items if artifact.item.lifecycle == "draft"
    )
    return {
        "total": len(items),
        "lifecycle_counts": counts,
        "duplicate_pairs": len(duplicates),
        "unverified_drafts": unverified,
        "checked_at": utcnow(),
        "health": "healthy" if not duplicates and not unverified else "degraded",
    }


def validate(artifact: KnowledgeArtifact) -> list[str]:
    """Validate an artifact against the knowledge policy."""
    violations: list[str] = []
    if artifact.item.lifecycle not in KNOWLEDGE_LIFECYCLE:
        violations.append(f"invalid lifecycle '{artifact.item.lifecycle}'")
    if not 0.0 <= artifact.item.confidence <= 1.0:
        violations.append("confidence out of range")
    if not artifact.item.title.strip():
        violations.append("missing title")
    if not artifact.item.artifact_id.strip():
        violations.append("missing artifact id")
    return violations


def validate_all(items: list[KnowledgeArtifact]) -> list[tuple[str, list[str]]]:
    return [(artifact.artifact_id, validate(artifact)) for artifact in items]


def rank(artifacts: list[KnowledgeArtifact]) -> list[KnowledgeArtifact]:
    """Rank artifacts by computed confidence (descending)."""
    for artifact in artifacts:
        artifact.item.confidence = compute_confidence(artifact.item)
    return sorted(artifacts, key=lambda a: a.item.confidence, reverse=True)


def merge(primary: KnowledgeArtifact, duplicate: KnowledgeArtifact) -> KnowledgeArtifact:
    primary.item = merge_items(primary.item, duplicate.item)
    primary.dependencies = sorted(set(primary.dependencies) | set(duplicate.dependencies))
    return primary
