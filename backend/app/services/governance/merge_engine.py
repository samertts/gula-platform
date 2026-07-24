from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from backend.app.services.governance.identity_governance import (
    IdentityGovernanceService,
)

logger = logging.getLogger("gula.identity.merge")


@dataclass
class MergeProposal:
    primary_hn: str = ""
    duplicate_hn: str = ""
    confidence_score: float = 0.0
    matched_fields: list[str] = field(default_factory=list)
    reviewed_by: str = ""
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    notes: str = ""


class IdentityMergeEngine:
    def __init__(self, identity_service: IdentityGovernanceService):
        self._identity = identity_service
        self._proposals: dict[str, MergeProposal] = {}
        self._merge_history: list[dict[str, Any]] = []

    def calculate_confidence(
        self, primary_hn: str, duplicate_hn: str,
    ) -> float:
        primary = self._identity._get_by_health_number(primary_hn)
        duplicate = self._identity._get_by_health_number(duplicate_hn)

        score = 0.0
        matched = []

        if primary.national_id_hash and primary.national_id_hash == duplicate.national_id_hash:
            score += 0.5
            matched.append("national_id")
            logger.debug("National ID match: +0.5")

        if primary.full_name and duplicate.full_name:
            from difflib import SequenceMatcher
            ratio = SequenceMatcher(None, primary.full_name.lower(), duplicate.full_name.lower()).ratio()
            if ratio > 0.9:
                score += 0.2
                matched.append("name")
                logger.debug("Name match (%.2f): +0.2", ratio)

        if primary.date_of_birth and duplicate.date_of_birth and primary.date_of_birth == duplicate.date_of_birth:
            score += 0.15
            matched.append("date_of_birth")
            logger.debug("DOB match: +0.15")

        if primary.phone and duplicate.phone and primary.phone == duplicate.phone:
            score += 0.1
            matched.append("phone")
            logger.debug("Phone match: +0.1")

        return min(score, 1.0)

    def propose_merge(
        self,
        primary_hn: str,
        duplicate_hn: str,
        confidence_threshold: float = 0.6,
    ) -> MergeProposal | None:
        confidence = self.calculate_confidence(primary_hn, duplicate_hn)
        if confidence < confidence_threshold:
            logger.info(
                "Merge confidence %.2f below threshold %.2f for %s <-> %s",
                confidence,
                confidence_threshold,
                primary_hn,
                duplicate_hn,
            )
            return None

        proposal = MergeProposal(
            primary_hn=primary_hn,
            duplicate_hn=duplicate_hn,
            confidence_score=confidence,
        )
        self._proposals[proposal.primary_hn + ":" + proposal.duplicate_hn] = proposal
        logger.info(
            "Merge proposed: %s <- %s (confidence: %.2f)",
            primary_hn,
            duplicate_hn,
            confidence,
        )
        return proposal

    def approve_merge(self, proposal_key: str, reviewed_by: str = "") -> MergeProposal:
        proposal = self._proposals.get(proposal_key)
        if not proposal:
            raise ValueError(f"Merge proposal not found: {proposal_key}")

        primary = self._identity._get_by_health_number(proposal.primary_hn)
        duplicate = self._identity._get_by_health_number(proposal.duplicate_hn)

        duplicate.status = "merged"
        duplicate.metadata["merged_into"] = proposal.primary_hn

        duplicate.add_history_entry({
            "action": "identity_merged",
            "merged_into": proposal.primary_hn,
            "confidence": proposal.confidence_score,
            "reviewed_by": reviewed_by,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        primary.add_history_entry({
            "action": "received_merged_identity",
            "merged_from": proposal.duplicate_hn,
            "confidence": proposal.confidence_score,
        })

        proposal.status = "approved"
        proposal.resolved_at = datetime.now(UTC)
        proposal.reviewed_by = reviewed_by

        self._merge_history.append({
            "primary_hn": proposal.primary_hn,
            "duplicate_hn": proposal.duplicate_hn,
            "confidence": proposal.confidence_score,
            "action": "merged",
            "reviewed_by": reviewed_by,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        logger.info(
            "Identity merged: %s <- %s (reviewed by %s)",
            proposal.primary_hn,
            proposal.duplicate_hn,
            reviewed_by,
        )
        return proposal

    def reject_merge(self, proposal_key: str, notes: str = "") -> MergeProposal:
        proposal = self._proposals.get(proposal_key)
        if not proposal:
            raise ValueError(f"Merge proposal not found: {proposal_key}")

        proposal.status = "rejected"
        proposal.resolved_at = datetime.now(UTC)
        proposal.notes = notes

        self._merge_history.append({
            "primary_hn": proposal.primary_hn,
            "duplicate_hn": proposal.duplicate_hn,
            "confidence": proposal.confidence_score,
            "action": "rejected",
            "notes": notes,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        logger.info("Merge rejected: %s <-> %s", proposal.primary_hn, proposal.duplicate_hn)
        return proposal

    def get_proposal(self, primary_hn: str, duplicate_hn: str) -> MergeProposal | None:
        return self._proposals.get(f"{primary_hn}:{duplicate_hn}")

    def list_pending_proposals(self) -> list[MergeProposal]:
        return [p for p in self._proposals.values() if p.status == "pending"]

    def get_merge_history(self) -> list[dict[str, Any]]:
        return list(self._merge_history)
