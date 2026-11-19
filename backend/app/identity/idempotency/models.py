"""Canonical NIAM idempotency key store.

One shared table for every Platform Authority operation that creates a
new credential-bearing row and is unsafe to retry blindly
(`generate_api_key`, `issue_certificate`, `rotate_certificate`,
`rotate_api_key`) -- not four separate tables, not embedded columns on
`APIKey`/`DigitalCertificate` (see docs/security/IDEMPOTENCY_SCHEMA_PROPOSAL.md
and docs/adr/ADR-026-niam-idempotency-key-store.md for the full design
rationale). `result_type`/`result_id` are a polymorphic reference to the
row the operation actually created -- the table never stores the
request payload itself, only its fingerprint, and never stores any
secret or private key material.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class NiamIdempotencyKey(IdentityBaseEntity):
    __tablename__ = "niam_idempotency_keys"
    __table_args__ = (
        UniqueConstraint("operation", "actor_account_id", "key_hash", name="uq_niam_idempotency_scope"),
    )

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    operation = Column(String(50), nullable=False, index=True)
    actor_account_id = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    key_hash = Column(String(64), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    result_type = Column(String(50), nullable=True, index=True)
    result_id = Column(String(26), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
