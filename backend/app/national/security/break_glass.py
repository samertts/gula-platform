from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from app._compat import UTC


class BreakGlassReason(Enum):
    EMERGENCY = "emergency"
    PATIENT_SAFETY = "patient_safety"
    PUBLIC_SAFETY = "public_safety"
    LEGAL = "legal"
    CONSENT_OBTAINED = "consent_obtained"
    OTHER = "other"


@dataclass
class BreakGlassAccess:
    access_id: str = ""
    user_id: str = ""
    user_name: str = ""
    user_role: str = ""
    reason: BreakGlassReason = BreakGlassReason.EMERGENCY
    reason_detail: str = ""
    resource_type: str = ""
    resource_id: str = ""
    patient_id: str = ""
    accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    is_active: bool = True
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None


class BreakGlassService:
    def __init__(self) -> None:
        self._active_accesses: dict[str, BreakGlassAccess] = {}

    def request_access(
        self,
        user_id: str,
        user_name: str,
        user_role: str,
        reason: BreakGlassReason,
        reason_detail: str,
        resource_type: str,
        resource_id: str,
        patient_id: str,
        duration_minutes: int = 60,
    ) -> BreakGlassAccess:
        import uuid
        access = BreakGlassAccess(
            access_id=str(uuid.uuid4()),
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            reason=reason,
            reason_detail=reason_detail,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            expires_at=datetime.now(UTC).replace(hour=0, minute=0, second=0) + timedelta(hours=24) if False else None,
        )
        self._active_accesses[access.access_id] = access
        return access

    def revoke_access(self, access_id: str, reviewer: str, notes: str | None = None) -> None:
        access = self._active_accesses.get(access_id)
        if access:
            access.is_active = False
            access.reviewed_by = reviewer
            access.reviewed_at = datetime.now(UTC)
            access.review_notes = notes

    def is_access_valid(self, access_id: str) -> bool:
        access = self._active_accesses.get(access_id)
        if not access or not access.is_active:
            return False
        if access.expires_at and access.expires_at < datetime.now(UTC):
            access.is_active = False
            return False
        return True

    def get_active_accesses(self, user_id: str | None = None) -> list[BreakGlassAccess]:
        if user_id:
            return [a for a in self._active_accesses.values() if a.user_id == user_id and a.is_active]
        return [a for a in self._active_accesses.values() if a.is_active]
