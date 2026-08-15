from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class AccountRequestStatus(StrEnum):
    pending_review = "pending_review"
    under_review = "under_review"
    pending_verification = "pending_verification"
    verified = "verified"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    cancelled = "cancelled"


class AccountCreationRequest(IdentityBaseEntity):
    """Review-gated account intake; it never grants an account or authority."""

    __tablename__ = "niam_account_creation_requests"

    request_uuid = Column(String(36), unique=True, nullable=False)
    status = Column(String(30), default=AccountRequestStatus.pending_review.value, nullable=False)
    requested_account_type = Column(String(20), default="human", nullable=False)

    # Contact/name values are encrypted at rest. Lookup columns are keyed blind indexes.
    contact_email_encrypted = Column(String(1024), nullable=True)
    contact_email_lookup = Column(String(64), nullable=True)
    contact_phone_encrypted = Column(String(1024), nullable=True)
    contact_phone_lookup = Column(String(64), nullable=True)
    display_name_encrypted = Column(String(1024), nullable=True)

    # Idempotency and abuse correlation are stored only as keyed digests.
    idempotency_key_hash = Column(String(64), unique=True, nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    source_ip_hash = Column(String(64), nullable=True)

    reviewed_by_account_id = Column(
        String(26),
        ForeignKey("niam_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_reason_encrypted = Column(String(1024), nullable=True)
    rejection_reason_encrypted = Column(String(1024), nullable=True)
    verification_method = Column(String(50), nullable=True)
    verification_provider = Column(String(100), nullable=True)
    verification_reference = Column(String(255), nullable=True)
    verification_attempts = Column(Integer, nullable=False, default=0)
    verification_locked_at = Column(DateTime(timezone=True), nullable=True)
    verification_failure_reason_code = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    activation_token_hash = Column(String(64), nullable=True, index=True)
    activation_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    account_id = Column(
        String(26),
        ForeignKey("niam_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
