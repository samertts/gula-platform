"""Functional NIAM step-up authentication (owner-approved, 5-minute window).

Security model
--------------
* The second factor is verified with the EXISTING shared primitive
  ``shared.auth.mfa.verify_totp`` against the administrator's own
  ``Account.mfa_secret``. No duplicate MFA engine is introduced.
* No client-supplied account id, timestamp, MFA flag or auth claim is accepted.
  The actor is resolved server-side by ``get_current_niam_actor`` and every
  identifier used here is re-read from the database.
* Evidence is an ``NiamStepUpEvent`` bound to account, session, session JTI,
  method, factor fingerprint and server verification time.
* Missing, invalid, expired, revoked, replayed, mismatched or ambiguous
  evidence always denies. Configuration errors deny too.
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.config import load_niam_step_up_freshness_seconds
from app.identity.models.account import Account, AccountStatus
from app.identity.models.audit import AuditAction
from app.identity.models.session import UserSession
from app.identity.models.step_up import NiamStepUpEvent
from app.identity.services.audit_service import AuditService
from shared.auth.mfa import verify_totp

logger = logging.getLogger("gula.identity.step_up")

_TOTP_CODE = re.compile(r"^\d{6}$")
_ALLOWED_METHODS = frozenset({"totp"})
_CODE_DOMAIN = "niam-step-up-code-v1"
_FACTOR_DOMAIN = "niam-step-up-factor-v1"


class StepUpError(Exception):
    """Base class for fail-closed step-up failures."""


class StepUpConfigurationError(StepUpError):
    """The deployment configuration is invalid; step-up is unavailable."""


class StepUpDenied(StepUpError):
    """Evidence or verification was rejected."""


def _fingerprint(domain: str, *parts: str) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("utf-8"))
    for part in parts:
        digest.update(len(part).to_bytes(4, "big"))
        digest.update(part.encode("utf-8"))
    return digest.hexdigest()


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite drops tzinfo; always compare aware UTC timestamps."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class StepUpService:
    """Create and validate server-side NIAM step-up evidence.

    ``freshness_seconds`` is a *server-side* override used only by tests and
    deterministic boundary verification; callers over HTTP can never set it.
    """

    def __init__(self, db: AsyncSession, freshness_seconds: int | None = None) -> None:
        self.db = db
        self._freshness_override = freshness_seconds

    def _freshness(self) -> int:
        if self._freshness_override is not None:
            return self._freshness_override
        try:
            return load_niam_step_up_freshness_seconds()
        except ValueError as exc:
            raise StepUpConfigurationError(str(exc)) from exc

    @staticmethod
    def _enrolled_methods(account: Account) -> frozenset[str]:
        if not account.mfa_methods:
            return frozenset()
        return frozenset(part.strip().lower() for part in account.mfa_methods.split(",") if part.strip())

    async def _resolve_principal(self, actor: Any) -> tuple[Account, UserSession, datetime]:
        """Re-read principal + session from the database; never trust cached claims."""
        now = datetime.now(UTC)
        account = (
            await self.db.execute(select(Account).where(Account.id == actor.account.id))
        ).scalar_one_or_none()
        session = (
            await self.db.execute(select(UserSession).where(UserSession.id == actor.session.id))
        ).scalar_one_or_none()
        if account is None or session is None:
            raise StepUpDenied("principal_not_found")
        if (
            not account.is_active
            or account.is_locked
            or account.status != AccountStatus.active.value
        ):
            raise StepUpDenied("account_inactive")
        if session.account_id != account.id or session.token_jti != actor.session.token_jti:
            raise StepUpDenied("session_substitution")
        if not session.is_active or _as_utc(session.terminated_at) is not None:
            raise StepUpDenied("session_revoked")
        if _as_utc(session.expires_at) <= now:
            raise StepUpDenied("session_expired")
        return account, session, now

    async def _audit(
        self,
        action: AuditAction,
        account: Account,
        session: UserSession,
        outcome: str,
        metadata: dict,
        *,
        error_message: str | None = None,
    ) -> None:
        """Record step-up outcomes in the immutable identity audit log.

        A failed verification is best-effort audited (the denial stands even if
        the log is unavailable); a successful verification requires the audit
        entry to be written, so no unaudited step-up evidence can be produced.
        """
        try:
            await AuditService(self.db).record(
                action=action,
                actor_id=account.id,
                actor_type="account",
                target_type="account",
                target_id=account.id,
                session_id=session.id,
                outcome=outcome,
                metadata=metadata,
                error_message=error_message,
            )
        except Exception:
            logger.exception("step-up audit write failed (outcome=%s)", outcome)
            if outcome == "success":
                raise

    async def verify(self, actor: Any, code: str, method: str = "totp") -> NiamStepUpEvent:
        """Verify the administrator's OWN factor and persist fresh evidence."""
        freshness = self._freshness()
        if method not in _ALLOWED_METHODS:
            raise StepUpDenied("unsupported_factor")
        if not isinstance(code, str) or not _TOTP_CODE.fullmatch(code):
            raise StepUpDenied("invalid_factor_code")

        account, session, now = await self._resolve_principal(actor)

        if not account.mfa_enabled or not account.mfa_secret or method not in self._enrolled_methods(account):
            await self._audit(
                AuditAction.mfa_failed, account, session, "failure",
                {"reason": "factor_not_enrolled", "method": method},
            )
            raise StepUpDenied("factor_not_enrolled")

        code_fp = _fingerprint(_CODE_DOMAIN, account.id, code)
        replay_stmt = (
            select(NiamStepUpEvent.id)
            .where(
                NiamStepUpEvent.account_id == account.id,
                NiamStepUpEvent.code_fingerprint == code_fp,
                NiamStepUpEvent.is_active.is_(True),
                NiamStepUpEvent.revoked_at.is_(None),
                NiamStepUpEvent.verified_at >= now - timedelta(seconds=freshness),
            )
            .limit(1)
        )
        if (await self.db.execute(replay_stmt)).first() is not None:
            await self._audit(
                AuditAction.mfa_failed, account, session, "failure",
                {"reason": "replay_detected", "method": method},
            )
            raise StepUpDenied("replay_detected")

        try:
            verified = verify_totp(account.mfa_secret, code)
        except Exception:
            verified = False
        if not verified:
            await self._audit(
                AuditAction.mfa_failed, account, session, "failure",
                {"reason": "factor_verification_failed", "method": method},
            )
            raise StepUpDenied("factor_verification_failed")

        event = NiamStepUpEvent(
            uuid=str(uuid.uuid4()),
            event_id=uuid.uuid4().hex[:26].upper(),
            account_id=account.id,
            session_id=session.id,
            session_jti=session.token_jti,
            mfa_method=method,
            code_fingerprint=code_fp,
            factor_fingerprint=_fingerprint(_FACTOR_DOMAIN, account.mfa_secret),
            verified_at=now,
            expires_at=now + timedelta(seconds=freshness),
            is_active=True,
        )
        self.db.add(event)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            # Database-level replay guard: a concurrent request may have won
            # the race after our application-level replay check. Never surface
            # the raw integrity error or issue unaudited evidence.
            await self.db.rollback()
            await self._audit(
                AuditAction.mfa_failed, account, session, "failure",
                {"reason": "replay_detected_concurrent", "method": method},
            )
            raise StepUpDenied("replay_detected") from exc
        await self._audit(
            AuditAction.mfa_verified, account, session, "success",
            {"method": method, "event_id": event.event_id, "purpose": "step_up"},
        )
        return event

    async def assert_fresh(self, actor: Any, *, purpose: str) -> NiamStepUpEvent:
        """Fail-closed validation of an existing step-up signal for ``purpose``.

        The signal is fresh while ``0 <= elapsed <= freshness_seconds``; at
        exactly the configured boundary it is still valid, beyond it is stale.
        Future-dated evidence (clock skew) is rejected.
        """
        freshness = self._freshness()
        account, session, now = await self._resolve_principal(actor)

        stmt = (
            select(NiamStepUpEvent)
            .where(
                NiamStepUpEvent.account_id == account.id,
                NiamStepUpEvent.session_id == session.id,
                NiamStepUpEvent.session_jti == session.token_jti,
                NiamStepUpEvent.is_active.is_(True),
                NiamStepUpEvent.revoked_at.is_(None),
            )
            .order_by(NiamStepUpEvent.verified_at.desc())
        )
        events = list((await self.db.execute(stmt)).scalars().all())
        if not events:
            raise StepUpDenied("no_step_up_evidence")

        latest = events[0]
        verified_at = _as_utc(latest.verified_at)
        expires_at = _as_utc(latest.expires_at)
        elapsed = (now - verified_at).total_seconds()
        if elapsed < 0:
            raise StepUpDenied("clock_skew_rejected")
        if elapsed > freshness:
            raise StepUpDenied("stale_step_up_evidence")
        if now > expires_at:
            raise StepUpDenied("stale_step_up_evidence")

        # Factor revocation / rotation invalidates evidence derived from it.
        if not account.mfa_enabled or not account.mfa_secret:
            raise StepUpDenied("factor_revoked")
        if latest.mfa_method not in self._enrolled_methods(account):
            raise StepUpDenied("factor_revoked")
        if latest.factor_fingerprint != _fingerprint(_FACTOR_DOMAIN, account.mfa_secret):
            raise StepUpDenied("factor_revoked")

        # Two different factors/methods recorded at the same instant are
        # ambiguous evidence; never choose one on the caller's behalf.
        same_instant = [
            e for e in events if _as_utc(e.verified_at) == _as_utc(latest.verified_at)
        ]
        if len({(e.mfa_method, e.factor_fingerprint) for e in same_instant}) > 1:
            raise StepUpDenied("ambiguous_step_up_evidence")

        await self._audit(
            AuditAction.policy_enforced, account, session, "success",
            {"purpose": purpose, "event_id": latest.event_id, "elapsed_seconds": int(elapsed)},
        )
        return latest
