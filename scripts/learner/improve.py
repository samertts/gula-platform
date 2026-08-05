"""Phase 7 — Continuous Improvement.

Evaluate the six platform engines (Builder, Reviewer, Orchestrator, Deployer,
Quality System, Knowledge System) from the learning record and propose
concrete improvements. Proposals are stored with a stable ID and status so
the platform can track which improvement ideas are open, approved, rejected,
or implemented — the Learner never stops improving the platform itself.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.learner.core import (
    ENGINES_EVALUATED,
    PROPOSAL_DIR,
    Proposal,
    ProposalStatus,
    read_json,
    write_json,
)

# (target, title, rationale) seed proposals derived from the learning record.
IMPROVEMENT_SEEDS: dict[str, tuple[str, str]] = {
    "builder": (
        "Seed a Builder improvement proposal",
        "Builder outputs should be re-verifiable from the skill store",
    ),
    "reviewer": (
        "Seed a Reviewer improvement proposal",
        "Reviewer verdicts should feed skill confidence back into the knowledge store",
    ),
    "orchestrator": (
        "Seed an Orchestrator improvement proposal",
        "Orchestrator missions should trigger automatic knowledge extraction on completion",
    ),
    "deployer": (
        "Seed a Deployer improvement proposal",
        "Deployer runs should publish runbooks from deployment lessons",
    ),
    "quality-system": (
        "Seed a Quality System improvement proposal",
        "Quality gates should include a knowledge-coverage check",
    ),
    "knowledge-system": (
        "Seed a Knowledge System improvement proposal",
        "The knowledge graph should be browsable from the registry",
    ),
}


def propose_improvements() -> list[Proposal]:
    """Create one improvement proposal per evaluated engine."""
    start = int(_next_proposal_number())
    proposals: list[Proposal] = []
    for offset, target in enumerate(ENGINES_EVALUATED):
        title, rationale = IMPROVEMENT_SEEDS.get(target, ("Improve engine", ""))
        proposals.append(Proposal(
            proposal_id=f"PRO-{start + offset:06d}",
            target=target,
            title=title,
            rationale=rationale,
        ))
    return proposals


def persist_proposals(proposals: list[Proposal]) -> Path:
    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
    path = PROPOSAL_DIR / "proposals.json"
    payload = {"proposals": [p.to_dict() for p in proposals], "updated_at": utcnow()}
    write_json(path, payload)
    return path


def load_proposals() -> list[Proposal]:
    data = read_json(PROPOSAL_DIR / "proposals.json")
    return [Proposal(**item) for item in data.get("proposals", [])]


def set_proposal_status(proposal_id: str, status: str) -> Proposal | None:
    """Update a proposal's status by ID (idempotent)."""
    if status not in {ps.value for ps in ProposalStatus}:
        raise ValueError(f"invalid proposal status: {status}")
    proposals = load_proposals()
    for proposal in proposals:
        if proposal.proposal_id == proposal_id:
            proposal.status = status
            persist_proposals(proposals)
            return proposal
    return None


def _next_proposal_number() -> str:
    if not PROPOSAL_DIR.exists():
        return "000001"
    highest = 0
    path = PROPOSAL_DIR / "proposals.json"
    for item in read_json(path).get("proposals", []):
        match = re.match(r"PRO-(\d{6})", item.get("proposal_id", ""))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{highest + 1:06d}"
