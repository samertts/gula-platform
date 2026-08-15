from __future__ import annotations

from datetime import datetime
from typing import Any

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus

LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    AccountStatus.requested.value: frozenset({
        AccountStatus.pending_verification.value,
        AccountStatus.rejected.value,
        AccountStatus.expired.value,
    }),
    AccountStatus.pending_verification.value: frozenset({
        AccountStatus.verified.value,
        AccountStatus.rejected.value,
        AccountStatus.expired.value,
    }),
    AccountStatus.verified.value: frozenset({
        AccountStatus.pending_approval.value,
        AccountStatus.rejected.value,
        AccountStatus.expired.value,
    }),
    AccountStatus.pending_approval.value: frozenset({
        AccountStatus.approved.value,
        AccountStatus.rejected.value,
        AccountStatus.expired.value,
    }),
    AccountStatus.approved.value: frozenset({
        AccountStatus.active.value,
        AccountStatus.deactivated.value,
    }),
    AccountStatus.active.value: frozenset({
        AccountStatus.suspended.value,
        AccountStatus.locked.value,
        AccountStatus.deactivated.value,
    }),
    AccountStatus.suspended.value: frozenset({
        AccountStatus.active.value,
        AccountStatus.deactivated.value,
    }),
    AccountStatus.locked.value: frozenset({
        AccountStatus.active.value,
        AccountStatus.deactivated.value,
    }),
    AccountStatus.disabled.value: frozenset({AccountStatus.deactivated.value}),
    AccountStatus.rejected.value: frozenset(),
    AccountStatus.expired.value: frozenset(),
    AccountStatus.deactivated.value: frozenset(),
}


class InvalidAccountTransition(ValueError):
    """Raised when an account state change is outside the lifecycle contract."""


class AccountLifecycleService:
    """Deny-by-default account lifecycle state machine."""

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        return target in LEGAL_TRANSITIONS.get(current, frozenset())

    @classmethod
    def transition(
        cls,
        account: Account | Any,
        target: AccountStatus,
        *,
        reason_code: str | None = None,
        actor_id: str | None = None,
        scope: dict[str, str | None] | None = None,
    ) -> Account | Any:
        current = str(account.status)
        target_value = target.value
        if not cls.can_transition(current, target_value):
            raise InvalidAccountTransition(f"Illegal account transition: {current} -> {target_value}")

        account.status = target_value
        account.is_active = target not in {
            AccountStatus.disabled,
            AccountStatus.deactivated,
            AccountStatus.rejected,
            AccountStatus.expired,
        }
        account.is_locked = target == AccountStatus.locked
        if target != AccountStatus.locked:
            account.locked_until = None
        # These values are intentionally runtime-only metadata for callers that
        # need to construct an audit event; no untrusted client data is persisted
        # on the Account model by this helper.
        account._lifecycle_transition = {
            "from": current,
            "to": target_value,
            "reason_code": reason_code,
            "actor_id": actor_id,
            "scope": scope or {},
            "occurred_at": datetime.now(UTC).isoformat(),
        }
        return account

    @classmethod
    def request_verification(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.pending_verification, reason_code="verification_required")

    @classmethod
    def mark_verified(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.verified, reason_code="verification_passed")

    @classmethod
    def request_approval(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.pending_approval, reason_code="approval_required")

    @classmethod
    def approve(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.approved, reason_code="approved")

    @classmethod
    def activate(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.active, reason_code="activated")

    @classmethod
    def suspend(cls, account: Account | Any, reason_code: str = "manual_suspension") -> Account | Any:
        return cls.transition(account, AccountStatus.suspended, reason_code=reason_code)

    @classmethod
    def lock(cls, account: Account | Any, reason_code: str = "security_lock") -> Account | Any:
        return cls.transition(account, AccountStatus.locked, reason_code=reason_code)

    @classmethod
    def reject(cls, account: Account | Any, reason_code: str = "rejected") -> Account | Any:
        return cls.transition(account, AccountStatus.rejected, reason_code=reason_code)

    @classmethod
    def expire(cls, account: Account | Any, reason_code: str = "expired") -> Account | Any:
        return cls.transition(account, AccountStatus.expired, reason_code=reason_code)

    @classmethod
    def deactivate(cls, account: Account | Any, reason_code: str = "permanent_deactivation") -> Account | Any:
        return cls.transition(account, AccountStatus.deactivated, reason_code=reason_code)

    @classmethod
    def reactivate(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.active, reason_code="reactivated")

    @classmethod
    def unlock(cls, account: Account | Any) -> Account | Any:
        return cls.transition(account, AccountStatus.active, reason_code="security_unlock")
