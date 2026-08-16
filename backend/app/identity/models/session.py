from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class UserSession(IdentityBaseEntity):
    __tablename__ = "niam_sessions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    token_jti = Column(String(128), unique=True, nullable=False, index=True)
    refresh_token_jti = Column(String(128), unique=True, nullable=True, index=True)
    # Durable refresh-token lineage. Every rotated token remains in one family so
    # replay of an already-rotated token can invalidate all descendants.
    refresh_family_id = Column(String(36), nullable=True, index=True)
    refresh_replaced_by_jti = Column(String(128), nullable=True, index=True)

    session_type = Column(String(20), default="web", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_id = Column(String(26), ForeignKey("niam_devices.id", ondelete="SET NULL"), nullable=True)

    location_city = Column(String(100), nullable=True)
    location_country = Column(String(3), nullable=True)
    location_lat = Column(String(20), nullable=True)
    location_lng = Column(String(20), nullable=True)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    terminated_at = Column(DateTime(timezone=True), nullable=True)
    termination_reason = Column(String(100), nullable=True)
    terminated_by = Column(String(100), nullable=True)

    auth_method = Column(String(50), nullable=True)
    mfa_used = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Integer, nullable=True)

    policy_id = Column(String(36), nullable=True, index=True)
    governance_action = Column(String(50), nullable=True)
    risk_score_at_login = Column(Integer, nullable=True)
    risk_level_at_login = Column(String(20), nullable=True)
