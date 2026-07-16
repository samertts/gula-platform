from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.governance.models.identity import GovernanceIdentityRecord
from app.governance.repositories.base import GovernanceRepository


class IdentityRecordRepository(GovernanceRepository[GovernanceIdentityRecord]):
    def __init__(self, db: Session):
        super().__init__(db, GovernanceIdentityRecord, audit_resource="gov_identity")

    def get_by_health_number(self, health_number: str) -> GovernanceIdentityRecord | None:
        return (
            self._db.query(GovernanceIdentityRecord)
            .filter(GovernanceIdentityRecord.health_number == health_number)
            .first()
        )

    def get_by_national_id_hash(self, nid_hash: str) -> GovernanceIdentityRecord | None:
        return (
            self._db.query(GovernanceIdentityRecord)
            .filter(
                GovernanceIdentityRecord.national_id_hash == nid_hash,
                GovernanceIdentityRecord.identity_status == "active",
            )
            .first()
        )

    def search(self, query: str, skip: int = 0, limit: int = 20) -> list[GovernanceIdentityRecord]:
        if not query:
            return self.list(skip=skip, limit=limit)
        pattern = f"%{query}%"
        return (
            self._db.query(GovernanceIdentityRecord)
            .filter(
                or_(
                    GovernanceIdentityRecord.full_name.ilike(pattern),
                    GovernanceIdentityRecord.health_number.ilike(pattern),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
