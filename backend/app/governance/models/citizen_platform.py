from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app._compat import UTC

from ..base import GovernanceBaseEntity


class QRCodeRecord(GovernanceBaseEntity):
    __tablename__ = "gov_qr_codes"

    id = Column(String(36), primary_key=True)
    citizen_id = Column(String(36), nullable=False, index=True)
    token = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1, nullable=False)


class RecoveryRequestRecord(GovernanceBaseEntity):
    __tablename__ = "gov_recovery_requests"

    id = Column(String(36), primary_key=True)
    citizen_id = Column(String(36), nullable=False, index=True)
    method = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    verification_token = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1, nullable=False)


class GuardianRecord(GovernanceBaseEntity):
    __tablename__ = "gov_guardians"

    id = Column(String(36), primary_key=True)
    citizen_id = Column(String(36), nullable=False, index=True)
    guardian_id = Column(String(36), nullable=False, index=True)
    guardian_type = Column(String(50), nullable=False, default="legal_guardian")
    relationship = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1, nullable=False)
