"""Server-side evidence of a completed NIAM step-up authentication event.

A step-up event is created only after a real second factor has been verified
against the administrator's OWN NIAM account (``shared.auth.mfa.verify_totp``
over ``Account.mfa_secret``). It is never created from client-supplied flags,
timestamps, account identifiers or authentication claims.

The event is bound to:
  * the authenticated principal (``account_id``),
  * the authenticated session (``session_id`` + ``session_jti``),
  * the factor method that was actually verified (``mfa_method``),
  * the server-recorded verification timestamp (``verified_at``), and
  * a fingerprint of the factor secret (``factor_fingerprint``) so rotating or
    revoking the factor invalidates all evidence derived from it.

``code_fingerprint`` makes a submitted factor single-use inside a freshness
window, defeating replay of an observed one-time code.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint

from app.identity.base import IdentityBaseEntity


class NiamStepUpEvent(IdentityBaseEntity):
    __tablename__ = "niam_step_up_events"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "code_fingerprint", name="uq_niam_step_up_account_code"
        ),
    )

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    event_id = Column(String(26), unique=True, nullable=False, index=True)

    account_id = Column(
        String(26),
        ForeignKey("niam_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        String(26),
        ForeignKey("niam_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The exact access-token JTI presented when the factor was verified. A
    # different token (refresh, replay, session substitution) cannot reuse it.
    session_jti = Column(String(128), nullable=False, index=True)

    mfa_method = Column(String(30), nullable=False)
    code_fingerprint = Column(String(64), nullable=False, index=True)
    factor_fingerprint = Column(String(64), nullable=False)

    verified_at = Column(DateTime(timezone=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(120), nullable=True)
