from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class AccountRequestStatus(StrEnum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
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
    rejection_reason_encrypted = Column(String(1024), nullable=True)
    account_id = Column(
        String(26),
        ForeignKey("niam_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
