"""Consent — the governing access layer.

One row = one authorization: "actor (grantee_id) may access data of subject
(gpid = citizen_ulid) within scope, until expires_at."

Design invariants:
  - No PII — only ULIDs, scope strings, timestamps
  - No open-ended consents — expires_at is NOT NULL, API caps at 72h
  - No wildcard scope — scope is a namespaced string validated at the service
  - Status transitions one-way: active → revoked / expired
  - A tuple (gpid, grantee_id, scope, status='active') is unique — prevents
    duplicate overlapping grants
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app._compat import UTC

from ..database import Base


class Consent(Base):
    __tablename__ = "consents"
    __table_args__ = (
        UniqueConstraint("gpid", "grantee_id", "scope", "status", name="uq_consents_active_tuple"),
        Index("idx_consents_lookup", "gpid", "grantee_id", "status", "expires_at"),
        Index("idx_consents_expiry", "expires_at"),
        Index("idx_consents_gpid", "gpid"),
    )

    id = Column(String(26), primary_key=True)  # ULID
    gpid = Column(String(26), nullable=False)  # subject = citizen_ulid
    grantee_id = Column(String(64), nullable=False)  # actor identifier
    scope = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, default="active")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(
        Integer,
        ForeignKey("lab_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def is_valid_now(self) -> bool:
        """Pure check — no DB. True iff active and not expired."""
        if self.status != "active":
            return False
        now = datetime.now(UTC)
        exp = self.expires_at
        # Defensive: if stored naive, treat as UTC (postgres always tz-aware)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return exp > now
