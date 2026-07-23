from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class Device(IdentityBaseEntity):
    __tablename__ = "niam_devices"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=True, index=True)

    device_name = Column(String(200), nullable=True)
    device_type = Column(String(50), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)

    device_fingerprint = Column(String(255), unique=True, nullable=False, index=True)
    device_id = Column(String(255), unique=True, nullable=True)

    public_key = Column(Text, nullable=True)
    trusted = Column(Boolean, default=False, nullable=False, server_default="false")
    trusted_at = Column(DateTime(timezone=True), nullable=True)

    last_ip = Column(String(45), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
