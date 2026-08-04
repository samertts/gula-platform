"""Phase 1 — Chain of Authority.

One immutable authority hierarchy. Every decision has exactly one owner.
No engine may override a higher authority. Only the Architect may approve
architectural decisions; the Reviewer must approve deployments; the
Constitution overrides everything.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import AUTHORITY_CHAIN, ENGINE_REGISTRY

ARCHITECT_OWNED_CATEGORIES = {"architecture", "architectural", "adr", "api-contract"}
REVIEWER_OWNED_CATEGORIES = {"deployment", "release", "merge", "review"}


@dataclass(frozen=True)
class OwnerDecision:
    """The resolved single owner for a decision."""

    decision: str
    category: str
    owner: str
    authority_rank: int
    reason: str


def rank(engine: str) -> int:
    """Return the authority rank of an engine (0 = highest authority).

    Unknown engines are treated as lowest authority (max rank + 1).
    """
    try:
        return AUTHORITY_CHAIN.index(engine)
    except ValueError:
        return len(AUTHORITY_CHAIN)


def can_override(actor: str, target: str) -> bool:
    """True when ``actor`` holds higher authority than ``target``.

    A lower rank value means higher authority, so the actor overrides the
    target only when its rank is strictly smaller.
    """
    return rank(actor) < rank(target)


def is_subordinate(actor: str, of: str) -> bool:
    """True when ``actor`` is below ``of`` in the authority chain."""
    return rank(actor) > rank(of)


def resolve_owner(decision: str, category: str = "general") -> OwnerDecision:
    """Resolve exactly one owner for a decision by category.

    Architectural decisions are owned by the Architect. Deployment decisions
    are owned by the Reviewer. Everything else falls to the Governor as the
    supreme coordination layer.
    """
    cat = (category or "").strip().lower()
    if cat in ARCHITECT_OWNED_CATEGORIES:
        return OwnerDecision(decision, category, "architect", rank("architect"),
                             "architectural decisions require Architect approval")
    if cat in REVIEWER_OWNED_CATEGORIES:
        return OwnerDecision(decision, category, "reviewer", rank("reviewer"),
                             "deployment/release decisions require Reviewer approval")
    return OwnerDecision(decision, category, "governor", rank("governor"),
                         "unassigned categories are owned by the Governor")


def assert_no_override(actor: str, target: str) -> None:
    """Raise when a lower-authority engine tries to override a higher one."""
    if not can_override(actor, target):
        raise AuthorityViolation(
            f"{actor} (rank {rank(actor)}) may not override {target} (rank {rank(target)})"
        )


def chain_summary() -> list[dict[str, object]]:
    """Render the authority chain with roles for documentation."""
    summary: list[dict[str, object]] = []
    for i, engine in enumerate(AUTHORITY_CHAIN):
        meta = ENGINE_REGISTRY.get(engine, {})
        summary.append(
            {
                "rank": i,
                "engine": engine,
                "responsibilities": meta.get("responsibilities", []),
            }
        )
    return summary


class AuthorityViolation(Exception):
    """Raised when a lower-authority engine overrides a higher authority."""
