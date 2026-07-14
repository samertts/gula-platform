from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from app._compat import UTC


@dataclass
class EmergencyAccessRecord:
    access_id: str = ""
    user_id: str = ""
    patient_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    reason: str = ""
    accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notified_admin: bool = False
    reviewed: bool = False
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None


class EmergencyAccessService:
    def __init__(self) -> None:
        self._records: list[EmergencyAccessRecord] = []

    def grant_access(
        self, user_id: str, patient_id: str, resource_type: str, resource_id: str, reason: str
    ) -> EmergencyAccessRecord:
        import uuid
        record = EmergencyAccessRecord(
            access_id=str(uuid.uuid4()),
            user_id=user_id,
            patient_id=patient_id,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
        )
        self._records.append(record)
        return record

    def notify_admin(self, access_id: str) -> None:
        for r in self._records:
            if r.access_id == access_id:
                r.notified_admin = True
                break

    def review_access(self, access_id: str, reviewer: str) -> None:
        for r in self._records:
            if r.access_id == access_id:
                r.reviewed = True
                r.reviewed_by = reviewer
                r.reviewed_at = datetime.now(UTC)
                break

    def get_pending_reviews(self) -> list[EmergencyAccessRecord]:
        return [r for r in self._records if not r.reviewed]

    def get_records(self, patient_id: str | None = None) -> list[EmergencyAccessRecord]:
        if patient_id:
            return [r for r in self._records if r.patient_id == patient_id]
        return self._records
