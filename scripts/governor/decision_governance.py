"""Phase 3 — Decision Governance.

A decision registry with priority, ownership, conflict resolution, voting
rules, escalation rules, and rollback rules. Only the Architect may approve
architectural decisions; the Reviewer must approve deployments.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .authority import rank, resolve_owner
from .core import CHECKPOINT_DIR, read_json, utcnow, write_json

DECISION_FILE = CHECKPOINT_DIR.parent / "decisions.json"

PRIORITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
VOTE_THRESHOLD = 0.6  # majority of participating votes required
APPROVAL_QUORUM = 2  # minimum participating voters for a binding decision


@dataclass
class Decision:
    """A tracked engineering decision."""

    decision_id: str
    title: str
    category: str = "general"
    priority: str = "medium"
    owner: str = "governor"
    status: str = "proposed"  # proposed | decided | escalated | rejected | rolled_back
    context: str = ""
    alternatives: list[str] = field(default_factory=list)
    votes: dict[str, str] = field(default_factory=dict)  # voter -> "for"|"against"|"abstain"
    resolution: str = ""
    rollback_plan: str = ""
    created_at: str = field(default_factory=utcnow)
    decided_at: str = ""


def create_decision(
    decision_id: str,
    title: str,
    category: str = "general",
    priority: str = "medium",
    context: str = "",
    alternatives: list[str] | None = None,
    rollback_plan: str = "",
) -> Decision:
    """Create a decision and resolve its single owner from the authority map."""
    owner = resolve_owner(title, category).owner
    return Decision(
        decision_id=decision_id,
        title=title,
        category=category,
        priority=priority,
        owner=owner,
        context=context,
        alternatives=alternatives or [],
        rollback_plan=rollback_plan,
    )


def _requires_architect(decision: Decision) -> bool:
    return decision.owner == "architect" and decision.category.lower() in {
        "architecture", "architectural", "adr", "api-contract",
    }


def approve_decision(decision: Decision, approver: str) -> Decision:
    """Approve a decision subject to authority rules.

    Architectural decisions may only be approved by the Architect.
    Deployment decisions may only be approved by the Reviewer.
    """
    if _requires_architect(decision) and approver != "architect":
        raise PermissionError(
            f"Decision {decision.decision_id} is architectural; only the Architect may approve"
        )
    if decision.category.lower() == "deployment" and approver != "reviewer":
        raise PermissionError(
            f"Decision {decision.decision_id} is a deployment; only the Reviewer may approve"
        )
    decision.status = "decided"
    decision.resolution = f"Approved by {approver}"
    decision.decided_at = utcnow()
    return decision


def vote(decision: Decision, voter: str, choice: str) -> Decision:
    """Record a vote from an engine. Valid choices: for/against/abstain."""
    choice = choice.strip().lower()
    if choice not in {"for", "against", "abstain"}:
        raise ValueError(f"Invalid vote '{choice}'; expected for/against/abstain")
    decision.votes[voter] = choice
    return decision


def resolve_conflict(decision: Decision) -> str:
    """Resolve a conflict using majority voting rules.

    Returns the winning option or 'tie' when votes are not conclusive.
    """
    for_count = sum(1 for v in decision.votes.values() if v == "for")
    against = sum(1 for v in decision.votes.values() if v == "against")
    participants = len(decision.votes)
    if participants < APPROVAL_QUORUM:
        return "tie"
    total = for_count + against
    if total and for_count / total >= VOTE_THRESHOLD:
        return "approved"
    if total and against / total >= VOTE_THRESHOLD:
        return "rejected"
    return "tie"


def escalate_decision(decision: Decision, to_engine: str) -> Decision:
    """Escalate a decision to a higher authority for resolution.

    Escalation must always move UP the authority chain (lower rank).
    """
    if rank(to_engine) >= rank(decision.owner):
        raise PermissionError(
            f"Cannot escalate {decision.decision_id} to {to_engine}: not a higher authority "
            f"than owner {decision.owner}"
        )
    decision.owner = to_engine
    decision.status = "escalated"
    return decision


def rollback_decision(decision: Decision, reason: str) -> Decision:
    """Roll back a decided decision (e.g., failed deployment)."""
    if decision.status not in {"decided", "escalated"}:
        raise ValueError(f"Decision {decision.decision_id} is not in a reversible state")
    decision.status = "rolled_back"
    decision.resolution = f"Rolled back: {reason}"
    return decision


def load_decisions() -> dict[str, Decision]:
    data = read_json(DECISION_FILE)
    decisions: dict[str, Decision] = {}
    for did, raw in data.items():
        decision = Decision(**raw)
        decisions[did] = decision
    return decisions


def save_decisions(decisions: dict[str, Decision]) -> None:
    write_json(DECISION_FILE, {did: vars(d) for did, d in decisions.items()})


def decision_priority_weight(priority: str) -> int:
    return PRIORITY_ORDER.get(priority.strip().lower(), 1)
