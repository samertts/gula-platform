from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app._compat import UTC
from app.database import Base


class ClinicalLabFacilityBindingStatus(StrEnum):
    """Reviewed lifecycle for an explicit legacy-lab to facility bridge."""

    pending = "pending"
    validated = "validated"
    active = "active"
    blocked = "blocked"
    revoked = "revoked"


_REASON_REQUIRED: Final[set[ClinicalLabFacilityBindingStatus]] = {
    ClinicalLabFacilityBindingStatus.blocked,
    ClinicalLabFacilityBindingStatus.revoked,
}

_ALLOWED_TRANSITIONS: Final[dict[ClinicalLabFacilityBindingStatus, set[ClinicalLabFacilityBindingStatus]]] = {
    ClinicalLabFacilityBindingStatus.pending: {
        ClinicalLabFacilityBindingStatus.validated,
        ClinicalLabFacilityBindingStatus.blocked,
    },
    ClinicalLabFacilityBindingStatus.validated: {
        ClinicalLabFacilityBindingStatus.active,
        ClinicalLabFacilityBindingStatus.blocked,
    },
    ClinicalLabFacilityBindingStatus.active: {
        ClinicalLabFacilityBindingStatus.revoked,
        ClinicalLabFacilityBindingStatus.blocked,
    },
    ClinicalLabFacilityBindingStatus.blocked: {ClinicalLabFacilityBindingStatus.pending},
    ClinicalLabFacilityBindingStatus.revoked: {ClinicalLabFacilityBindingStatus.pending},
}


def _binding_id() -> str:
    return str(uuid4()).replace("-", "").upper()[:26]


class ClinicalLabFacilityBinding(Base):
    """Explicit bridge from an inherited laboratory row to a facility resource.

    This table deliberately stores foreign keys to the internal resources. It does
    not assert or derive equality between ``labs.id`` and ``facilities.facility_id``.
    """

    __tablename__ = "clinical_lab_facility_bindings"
    __table_args__ = (
        UniqueConstraint("legacy_lab_id", "facility_resource_id", name="uq_clinical_lab_facility_binding"),
    )

    id = Column(String(26), primary_key=True, default=_binding_id)
    legacy_lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_resource_id = Column(
        Integer,
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        nullable=False,
        default=ClinicalLabFacilityBindingStatus.pending.value,
        index=True,
    )
    mapping_version = Column(Integer, nullable=False, default=1)
    decision_reason = Column(Text, nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def transition(
        self,
        target: ClinicalLabFacilityBindingStatus | str,
        *,
        reason: str | None = None,
    ) -> None:
        """Apply one reviewed state transition without altering either resource ID."""

        current = ClinicalLabFacilityBindingStatus(self.status)
        target_status = ClinicalLabFacilityBindingStatus(target)
        if target_status == current:
            return
        if target_status not in _ALLOWED_TRANSITIONS[current]:
            raise ValueError(
                f"Invalid clinical lab-facility binding transition: {current.value} -> {target_status.value}"
            )
        if target_status in _REASON_REQUIRED and not (reason or "").strip():
            raise ValueError(f"A reason is required when a binding becomes {target_status.value}")

        now = datetime.now(UTC)
        self.status = target_status.value
        self.mapping_version = (self.mapping_version or 1) + 1
        self.decision_reason = reason.strip() if reason and reason.strip() else None
        if target_status == ClinicalLabFacilityBindingStatus.validated:
            self.validated_at = now
        elif target_status == ClinicalLabFacilityBindingStatus.active:
            self.activated_at = now
        elif target_status == ClinicalLabFacilityBindingStatus.revoked:
            self.revoked_at = now

