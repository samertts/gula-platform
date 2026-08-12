from __future__ import annotations

from sqlalchemy.orm import Session

from app.governance.models.citizen_platform import (
    GuardianRecord,
    QRCodeRecord,
    RecoveryRequestRecord,
)
from app.governance.repositories.base import GovernanceRepository


class QRCodeRepository(GovernanceRepository[QRCodeRecord]):
    def __init__(self, db: Session):
        super().__init__(db, QRCodeRecord, audit_resource="gov_qr")

    def get_active(self, qr_id: str) -> QRCodeRecord | None:
        return (
            self._db.query(QRCodeRecord)
            .filter(QRCodeRecord.id == qr_id, QRCodeRecord.is_active.is_(True))
            .first()
        )

    def list_by_citizen(self, citizen_id: str) -> list[QRCodeRecord]:
        return (
            self._db.query(QRCodeRecord)
            .filter(QRCodeRecord.citizen_id == citizen_id)
            .order_by(QRCodeRecord.created_at.desc())
            .all()
        )


class RecoveryRequestRepository(GovernanceRepository[RecoveryRequestRecord]):
    def __init__(self, db: Session):
        super().__init__(db, RecoveryRequestRecord, audit_resource="gov_recovery")

    def get_pending(self, request_id: str) -> RecoveryRequestRecord | None:
        return (
            self._db.query(RecoveryRequestRecord)
            .filter(
                RecoveryRequestRecord.id == request_id,
                RecoveryRequestRecord.status == "pending",
            )
            .first()
        )

    def list_by_citizen(self, citizen_id: str) -> list[RecoveryRequestRecord]:
        return (
            self._db.query(RecoveryRequestRecord)
            .filter(RecoveryRequestRecord.citizen_id == citizen_id)
            .order_by(RecoveryRequestRecord.created_at.desc())
            .all()
        )


class GuardianRepository(GovernanceRepository[GuardianRecord]):
    def __init__(self, db: Session):
        super().__init__(db, GuardianRecord, audit_resource="gov_guardians")

    def get_active(self, citizen_id: str) -> list[GuardianRecord]:
        return (
            self._db.query(GuardianRecord)
            .filter(
                GuardianRecord.citizen_id == citizen_id,
                GuardianRecord.is_active.is_(True),
            )
            .all()
        )

    def is_guardian(self, guardian_id: str, ward_id: str) -> bool:
        return (
            self._db.query(GuardianRecord)
            .filter(
                GuardianRecord.guardian_id == guardian_id,
                GuardianRecord.citizen_id == ward_id,
                GuardianRecord.is_active.is_(True),
            )
            .first()
        ) is not None
