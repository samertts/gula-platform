from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC
from app.database import Base


class MFADevice(Base):
    __tablename__ = "mfa_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("lab_users.id"), nullable=False, index=True)
    device_type = Column(String(30), nullable=False)
    device_name = Column(String(100), nullable=True)
    secret = Column(String(500), nullable=True)
    credential_id = Column(String(500), nullable=True, index=True)
    public_key = Column(Text, nullable=True)
    sign_count = Column(Integer, default=0)
    transports = Column(String(500), nullable=True)
    backup_codes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class MFASession(Base):
    __tablename__ = "mfa_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("lab_users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    mfa_method = Column(String(30), nullable=False)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
