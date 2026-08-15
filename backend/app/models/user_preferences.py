"""User-owned accessibility and optional health-preference records.

Accessibility is presentation-only and is deliberately separate from health data.
Health preferences are encrypted at rest and are never used for authorization.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app._compat import UTC

from ..database import Base


class AccessibilityProfile(Base):
    """Low-risk, user-controlled presentation preferences."""

    __tablename__ = "accessibility_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_accessibility_profiles_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    preferences = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class HealthPreference(Base):
    """Optional sensitive preferences, encrypted at rest and consent-bound."""

    __tablename__ = "health_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_health_preferences_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    encrypted_payload = Column(Text, nullable=True)
    consent_granted = Column(Boolean, nullable=False, default=False)
    consent_version = Column(String(32), nullable=True)
    consented_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
