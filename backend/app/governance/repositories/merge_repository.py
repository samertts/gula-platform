from __future__ import annotations

from sqlalchemy.orm import Session

from app.governance.models.health_number import MergedIdentityRecord
from app.governance.models.identity import MergeProposal
from app.governance.repositories.base import GovernanceRepository


class MergeProposalRepository(GovernanceRepository[MergeProposal]):
    def __init__(self, db: Session):
        super().__init__(db, MergeProposal, audit_resource="gov_merge_proposals")

    def get_by_key(self, proposal_key: str) -> MergeProposal | None:
        return (
            self._db.query(MergeProposal)
            .filter(MergeProposal.proposal_key == proposal_key)
            .first()
        )

    def list_pending(self) -> list[MergeProposal]:
        return (
            self._db.query(MergeProposal)
            .filter(MergeProposal.status == "pending")
            .order_by(MergeProposal.created_at.desc())
            .all()
        )


class MergedIdentityRecordRepository(GovernanceRepository[MergedIdentityRecord]):
    def __init__(self, db: Session):
        super().__init__(db, MergedIdentityRecord, audit_resource="gov_merged_identities")

    def get_by_health_number(self, health_number: str) -> list[MergedIdentityRecord]:
        return (
            self._db.query(MergedIdentityRecord)
            .filter(
                (MergedIdentityRecord.primary_health_number == health_number)
                | (MergedIdentityRecord.secondary_health_number == health_number),
            )
            .order_by(MergedIdentityRecord.occurred_at.desc())
            .all()
        )
