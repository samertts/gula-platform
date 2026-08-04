"""Phase 4 — Knowledge Governance.

Prevent duplicate skills, playbooks, runbooks, ADRs, and knowledge.
Implement knowledge merge, ranking, confidence, archive, retirement, and
the Draft -> Verified -> Approved -> Deprecated -> Archived lifecycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .core import KNOWLEDGE_LIFECYCLE

ARTIFACT_KINDS = ("skill", "playbook", "runbook", "adr", "knowledge")
NEXT_LIFECYCLE = {
    "draft": "verified",
    "verified": "approved",
    "approved": "deprecated",
    "deprecated": "archived",
}


@dataclass
class KnowledgeItem:
    """A governed knowledge artifact."""

    artifact_id: str
    title: str
    kind: str = "knowledge"
    lifecycle: str = "draft"
    confidence: float = 0.5
    content: str = ""
    usage_count: int = 0
    tags: list[str] = field(default_factory=list)


def normalize_title(title: str) -> str:
    """Normalize a title for duplicate comparison (lowercase, no punctuation)."""
    return re.sub(r"[^a-z0-9]+", " ", title.strip().lower())


def title_similarity(a: str, b: str) -> float:
    """Cosine-style token overlap similarity between two titles (0..1)."""
    ta = set(normalize_title(a).split())
    tb = set(normalize_title(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1.0, len(ta | tb))


def content_similarity(a: str, b: str) -> float:
    """Token-set similarity for content; guards against near-duplicate docs."""
    ta = set(re.findall(r"[a-z0-9]+", a.lower()))
    tb = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1.0, len(ta | tb))


def find_duplicates(
    items: list[KnowledgeItem],
    title_threshold: float = 0.7,
    content_threshold: float = 0.8,
) -> list[tuple[str, str, float, str]]:
    """Return (id_a, id_b, score, kind) for near-duplicate pairs.

    A pair is considered a duplicate when the title similarity exceeds
    ``title_threshold`` OR the content similarity exceeds ``content_threshold``.
    """
    duplicates: list[tuple[str, str, float, str]] = []
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            if a.kind != b.kind:
                continue
            title_score = title_similarity(a.title, b.title)
            content_score = content_similarity(a.content, b.content)
            score = max(title_score, content_score)
            if score >= title_threshold or content_score >= content_threshold:
                duplicates.append((a.artifact_id, b.artifact_id, score, a.kind))
    return duplicates


def compute_confidence(item: KnowledgeItem) -> float:
    """Compute a confidence score from lifecycle, usage, and content length.

    Draft knowledge is never trusted; approved + used + substantive knowledge
    approaches 1.0.
    """
    lifecycle_weight = {
        "draft": 0.3,
        "verified": 0.6,
        "approved": 0.85,
        "deprecated": 0.2,
        "archived": 0.1,
    }.get(item.lifecycle, 0.3)
    usage = min(0.15, item.usage_count * 0.05)
    length = min(0.1, len(item.content) / 5000.0)
    score = lifecycle_weight + usage + length
    return round(max(0.0, min(1.0, score)), 3)


def rank_items(items: list[KnowledgeItem]) -> list[KnowledgeItem]:
    """Rank knowledge items by computed confidence (descending)."""
    for item in items:
        item.confidence = compute_confidence(item)
    return sorted(items, key=lambda i: i.confidence, reverse=True)


def can_transition(current: str, target: str) -> bool:
    """True when the lifecycle transition is a valid forward move."""
    if current not in KNOWLEDGE_LIFECYCLE or target not in KNOWLEDGE_LIFECYCLE:
        return False
    if current == target:
        return True
    return NEXT_LIFECYCLE.get(current) == target


def transition(item: KnowledgeItem, target: str) -> KnowledgeItem:
    """Move an item to a new lifecycle state, enforcing forward-only moves."""
    if not can_transition(item.lifecycle, target):
        raise ValueError(
            f"Cannot move {item.artifact_id} from '{item.lifecycle}' to '{target}' "
            f"(forward-only lifecycle)"
        )
    item.lifecycle = target
    item.confidence = compute_confidence(item)
    return item


def merge_items(primary: KnowledgeItem, duplicate: KnowledgeItem) -> KnowledgeItem:
    """Merge a duplicate into the primary item (keep the stronger artifact).

    The primary keeps its id, lifecycle (highest), and combined usage count.
    """
    order = {s: i for i, s in enumerate(KNOWLEDGE_LIFECYCLE)}
    if order.get(duplicate.lifecycle, 0) > order.get(primary.lifecycle, 0):
        primary.lifecycle = duplicate.lifecycle
    primary.usage_count += duplicate.usage_count
    primary.confidence = compute_confidence(primary)
    if duplicate.tags:
        primary.tags = sorted(set(primary.tags) | set(duplicate.tags))
    return primary
