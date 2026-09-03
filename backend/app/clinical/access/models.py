from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app.database import Base


def _core_id() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class CoreAccessGrant(Base):  # type: ignore[misc]
    """Explicit, bounded patient-to-provider access grant."""

    __tablename__ = "core_access_grants"

    id = Column(String(26), primary_key=True, default=_core_id)
    patient_person_id = Column(String(26), nullable=False, index=True)
    grantee_account_id = Column(String(26), nullable=False, index=True)
    resource_type = Column(String(40), nullable=False)
    resource_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    purpose = Column(String(40), nullable=False)
    scope = Column(JSON, nullable=False)
    status = Column(String(24), nullable=False, default="ACTIVE", index=True)
    version = Column(Integer, nullable=False, default=1)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(String(500), nullable=True)
    created_by_account_id = Column(String(26), nullable=False)
    revoked_by_account_id = Column(String(26), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_id = Column(String(26), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("patient_person_id", "grantee_account_id", "resource_type", "resource_id", "version", name="uq_core_access_grant_version"),
        CheckConstraint("status IN ('ACTIVE','EXPIRED','REVOKED')", name="ck_core_access_grant_status"),
        CheckConstraint("purpose IN ('TREATMENT','RESEARCH','BILLING','AUDIT','PUBLIC_HEALTH')", name="ck_core_access_grant_purpose"),
        CheckConstraint("version > 0", name="ck_core_access_grant_version_positive"),
        Index("ix_core_access_grant_effective", "grantee_account_id", "resource_type", "resource_id", "status", "expires_at"),
        Index("ix_core_access_grant_patient_status", "patient_person_id", "status", "created_at"),
    )


class CoreAccessHistory(Base):  # type: ignore[misc]
    """Append-only access/grant audit projection safe for citizen display."""

    __tablename__ = "core_access_history"

    id = Column(String(26), primary_key=True, default=_core_id)
    grant_id = Column(String(26), nullable=True, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    actor_account_id = Column(String(26), nullable=False, index=True)
    resource_type = Column(String(40), nullable=False)
    resource_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    purpose = Column(String(40), nullable=True)
    scope = Column(JSON, nullable=True)
    action = Column(String(48), nullable=False)
    decision = Column(String(16), nullable=False)
    reason_code = Column(String(80), nullable=True)
    correlation_id = Column(String(128), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)

    __table_args__ = (
        CheckConstraint("decision IN ('ALLOW','DENY')", name="ck_core_access_history_decision"),
        CheckConstraint("length(trim(action)) > 0", name="ck_core_access_history_action_nonempty"),
        Index("ix_core_access_history_patient_time", "patient_person_id", "occurred_at", "id"),
        Index("ix_core_access_history_scope_time", "organization_id", "facility_id", "workspace_id", "occurred_at"),
    )
