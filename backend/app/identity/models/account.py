from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class AccountType(StrEnum):
    human = "human"
    machine = "machine"
    service = "service"
    system = "system"


class AccountStatus(StrEnum):
    active = "active"
    locked = "locked"
    suspended = "suspended"
    deactivated = "deactivated"
    pending_verification = "pending_verification"


class Account(IdentityBaseEntity):
    __tablename__ = "niam_accounts"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    identity_id = Column(
        String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    account_type = Column(String(20), default="human", nullable=False)
    status = Column(String(30), default="pending_verification", nullable=False, index=True)

    email = Column(String(200), unique=True, nullable=True, index=True)
    phone = Column(String(30), unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)

    password_hash = Column(String(255), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    password_expires_at = Column(DateTime(timezone=True), nullable=True)

    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_methods = Column(String(200), nullable=True)
    mfa_secret = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    lock_reason = Column(String(200), nullable=True)

    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    identity_verified = Column(Boolean, default=False, nullable=False)

    activated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivation_reason = Column(String(200), nullable=True)
