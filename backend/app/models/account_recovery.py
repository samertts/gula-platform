from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app._compat import UTC

from ..database import Base


class AccountRecoveryRequest(Base):
    """Server-owned recovery lifecycle record.

    Only digests and non-sensitive metadata are persisted.  The raw recovery
    secret is never stored, logged, or returned by an API response.
    """

    __tablename__ = "account_recovery_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), nullable=False, unique=True, index=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    account_kind = Column(String(16), nullable=False, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    lab_id = Column(Integer, nullable=True, index=True)
    operation = Column(String(40), nullable=False, index=True)
    state = Column(String(24), nullable=False, default="requested", index=True)
    assurance_level = Column(String(16), nullable=False, default="medium")
    risk_code = Column(String(64), nullable=False, default="standard_recovery")
    reason_code = Column(String(64), nullable=True)
    token_digest = Column(String(64), nullable=True, unique=True, index=True)
    idempotency_key_digest = Column(String(64), nullable=True, unique=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    recovered_at = Column(DateTime(timezone=True), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    requested_ip = Column(String(45), nullable=True)

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)
