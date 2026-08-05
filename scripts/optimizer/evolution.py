"""Phase 8 — Evolution Engine.

Generate improvement proposals across the whole platform: improvement
proposals, architecture evolution, refactoring candidates, infrastructure
improvements, automation opportunities, AI capability improvements, and
knowledge improvements. Nothing is applied automatically — every proposal
requires governance approval before it is implemented. Deterministic and
durable so evolution is tracked, not lost.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.optimizer.core import (
    EVOLUTION_TARGETS,
    PROPOSAL_DIR,
    EvolutionProposal,
    ProposalStatus,
    read_json,
    write_json,
)

PROPOSALS_PATH = PROPOSAL_DIR / "evolution.json"

# Target -> (title, rationale) seed proposals derived from the optimization record.
EVOLUTION_SEEDS: dict[str, tuple[str, str]] = {
    "improvement-proposals": (
        "Streamline optimization proposal tracking",
        "Proposals should carry measured before/after evidence when approved.",
    ),
    "architecture-evolution": (
        "Promote verified architecture recommendations to ADRs",
        "Verified ARC recommendations should become decision records.",
    ),
    "refactoring-candidates": (
        "Schedule high-severity debt for refactoring",
        "Highest-severity debt records should feed the next refactoring mission.",
    ),
    "infrastructure-improvements": (
        "Apply verified resource recommendations to infrastructure",
        "Resource savings should be measured against the baseline after change.",
    ),
    "automation-opportunities": (
        "Automate bottleneck re-detection in CI",
        "Run bottleneck detection on the CI and record findings in the registry.",
    ),
    "ai-capability-improvements": (
        "Feed optimization results back to the Learner",
        "Every verified optimization should become reusable engineering knowledge.",
    ),
    "knowledge-improvements": (
        "Publish optimization knowledge to the knowledge store",
        "Optimization lessons should be searchable alongside mission lessons.",
    ),
}


def propose_evolution() -> list[EvolutionProposal]:
    """Create one evolution proposal per target."""
    start = int(_next_proposal_number())
    proposals: list[EvolutionProposal] = []
    for offset, target in enumerate(EVOLUTION_TARGETS):
        title, rationale = EVOLUTION_SEEDS.get(target, ("Evolve platform", ""))
        proposals.append(EvolutionProposal(
            proposal_id=f"EVO-{start + offset:06d}",
            target=target,
            title=title,
            rationale=rationale,
        ))
    return proposals


def persist_proposals(proposals: list[EvolutionProposal]) -> Path:
    payload = {"proposals": [p.to_dict() for p in proposals], "updated_at": utcnow()}
    write_json(PROPOSALS_PATH, payload)
    return PROPOSALS_PATH


def load_proposals() -> list[EvolutionProposal]:
    data = read_json(PROPOSALS_PATH)
    return [EvolutionProposal(**item) for item in data.get("proposals", [])]


def set_proposal_status(proposal_id: str, status: str) -> EvolutionProposal | None:
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
    for item in read_json(PROPOSALS_PATH).get("proposals", []):
        match = re.match(r"EVO-(\d{6})", item.get("proposal_id", ""))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{highest + 1:06d}"
