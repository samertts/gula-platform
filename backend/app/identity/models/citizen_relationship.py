from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String

from app._compat import UTC, StrEnum
from app.identity.base import IdentityBaseEntity


class CitizenRelationshipSource(StrEnum):
    canonical_account = "canonical_account"
    legacy_user = "legacy_user"
    legacy_lab_user = "legacy_lab_user"


class CitizenRelationshipType(StrEnum):
    self = "self"
    guardian = "guardian"
    caregiver = "caregiver"
    delegate = "delegate"
    authorized_representative = "authorized_representative"


class CitizenRelationshipStatus(StrEnum):
    pending = "pending"
    active = "active"
    expired = "expired"
    revoked = "revoked"
    blocked = "blocked"


class CitizenRelationship(IdentityBaseEntity):
    """Explicit, revocable account/person-to-citizen relationship.

    This table is additive and intentionally does not backfill from phone or
    national-ID matching. A relationship is usable only after an explicit
    verification/activation transition performed by an authorized workflow.
    """

    __tablename__ = "niam_citizen_relationships"

    source_kind = Column(String(30), nullable=False, index=True)
    canonical_account_id = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True, index=True,
    )
    legacy_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True,
    )
    legacy_lab_user_id = Column(
        Integer, ForeignKey("lab_users.id", ondelete="RESTRICT"), nullable=True, index=True,
    )

    citizen_id = Column(
        String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    patient_id = Column(
        String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=True, index=True,
    )

    relationship_type = Column(String(40), nullable=False, index=True)
    status = Column(String(20), default=CitizenRelationshipStatus.pending.value, nullable=False, index=True)
    purpose = Column(String(100), nullable=False, default="citizen_workspace")
    scope = Column(JSON, nullable=True)

    valid_from = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_account_id = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True,
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String(255), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "canonical_account_id IS NOT NULL OR legacy_user_id IS NOT NULL OR legacy_lab_user_id IS NOT NULL",
            name="ck_citizen_relationship_has_source",
        ),
        CheckConstraint(
            "(source_kind = 'canonical_account' AND canonical_account_id IS NOT NULL AND legacy_user_id IS NULL AND legacy_lab_user_id IS NULL) OR "
            "(source_kind = 'legacy_user' AND legacy_user_id IS NOT NULL AND canonical_account_id IS NULL AND legacy_lab_user_id IS NULL) OR "
            "(source_kind = 'legacy_lab_user' AND legacy_lab_user_id IS NOT NULL AND canonical_account_id IS NULL AND legacy_user_id IS NULL)",
            name="ck_citizen_relationship_source_matches_kind",
        ),
        Index("ix_citizen_relationship_access", "citizen_id", "status", "relationship_type"),
        Index("ix_citizen_relationship_expiry", "status", "expires_at"),
        {"extend_existing": True},
    )

    def is_active_at(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        if self.status != CitizenRelationshipStatus.active.value or self.revoked_at is not None:
            return False
        if self.valid_from and self.valid_from > now:
            return False
        return self.expires_at is None or self.expires_at > now

    def allows(self, resource: str, write: bool = False) -> bool:
        if not self.is_active_at():
            return False
        scope: dict[str, Any] = self.scope if isinstance(self.scope, dict) else {}
        resources = scope.get("resources", [])
        if not isinstance(resources, list):
            return False
        if "*" in resources:
            return True
        requested = f"{resource}:write" if write else resource
        if write:
            return requested in resources
        return resource in resources or f"{resource}:read" in resources
