from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class RiskEvent(IdentityBaseEntity):
    __tablename__ = "niam_adaptive_risk_events"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(String(100), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = Column(String(100), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)

    event_type = Column(
        String(50), nullable=False, index=True,
    )

    severity = Column(String(20), nullable=False, index=True)

    risk_score = Column(Integer, nullable=False)

    details = Column(JSON, nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    location_city = Column(String(200), nullable=True)
    location_country = Column(String(200), nullable=True)
    location_lat = Column(String(50), nullable=True)
    location_lng = Column(String(50), nullable=True)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    mitigated = Column(Boolean, default=False, nullable=False)
    mitigation_action = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class RiskPolicy(IdentityBaseEntity):
    __tablename__ = "niam_adaptive_risk_policies"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    policy_id = Column(String(100), unique=True, nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    risk_threshold_low = Column(Integer, nullable=False)
    risk_threshold_medium = Column(Integer, nullable=False)
    risk_threshold_high = Column(Integer, nullable=False)
    risk_threshold_critical = Column(Integer, nullable=False)

    actions = Column(JSON, nullable=False)

    scope = Column(JSON, nullable=True)

    enabled = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class AdaptiveMFASession(IdentityBaseEntity):
    __tablename__ = "niam_adaptive_mfa_sessions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    mfa_id = Column(String(100), unique=True, nullable=False, index=True)

    account_id = Column(String(100), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), ForeignKey("niam_user_sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    mfa_type = Column(String(30), nullable=False)

    challenge = Column(String(500), nullable=False)
    challenge_expires_at = Column(DateTime(timezone=True), nullable=False)

    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)

    status = Column(String(20), default="pending", nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)


class ImpossibleTravelEvent(IdentityBaseEntity):
    __tablename__ = "niam_adaptive_travel_events"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    travel_id = Column(String(100), unique=True, nullable=False, index=True)

    account_id = Column(String(100), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)

    previous_ip = Column(String(45), nullable=True)
    previous_location_city = Column(String(200), nullable=True)
    previous_location_country = Column(String(200), nullable=True)
    previous_lat = Column(String(50), nullable=True)
    previous_lng = Column(String(50), nullable=True)
    previous_timestamp = Column(DateTime(timezone=True), nullable=True)

    current_ip = Column(String(45), nullable=False)
    current_location_city = Column(String(200), nullable=True)
    current_location_country = Column(String(200), nullable=True)
    current_lat = Column(String(50), nullable=True)
    current_lng = Column(String(50), nullable=True)
    current_timestamp = Column(DateTime(timezone=True), nullable=False)

    distance_km = Column(Float, nullable=True)
    time_delta_minutes = Column(Float, nullable=True)
    speed_kmh = Column(Float, nullable=True)

    impossible = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class SessionPolicy(IdentityBaseEntity):
    __tablename__ = "niam_adaptive_session_policies"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    policy_id = Column(String(100), unique=True, nullable=False, index=True)

    name = Column(String(200), nullable=False)

    applies_to = Column(String(50), nullable=False, index=True)

    max_sessions = Column(Integer, default=1, nullable=False)
    allow_concurrent = Column(Boolean, default=False, nullable=False)
    require_mfa = Column(Boolean, default=False, nullable=False)
    session_timeout_minutes = Column(Integer, nullable=True)
    inactivity_timeout_minutes = Column(Integer, nullable=True)
    notify_previous_device = Column(Boolean, default=True, nullable=False)
    terminate_previous_on_new_login = Column(Boolean, default=True, nullable=False)
    enforce_geo_restriction = Column(Boolean, default=False, nullable=False)
    allowed_geo = Column(JSON, nullable=True)
    enforce_ip_restriction = Column(Boolean, default=False, nullable=False)
    allowed_ips = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
