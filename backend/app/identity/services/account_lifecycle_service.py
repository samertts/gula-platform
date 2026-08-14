from __future__ import annotations

from app.identity.models.account import Account, AccountStatus

LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    AccountStatus.pending_verification.value: frozenset({AccountStatus.active.value, AccountStatus.deactivated.value}),
    AccountStatus.active.value: frozenset({
        AccountStatus.suspended.value,
        AccountStatus.locked.value,
        AccountStatus.disabled.value,
        AccountStatus.deactivated.value,
    }),
    AccountStatus.suspended.value: frozenset({AccountStatus.active.value, AccountStatus.disabled.value}),
    AccountStatus.locked.value: frozenset({AccountStatus.active.value, AccountStatus.disabled.value}),
    AccountStatus.disabled.value: frozenset({AccountStatus.deactivated.value}),
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
    def transition(cls, account: Account, target: AccountStatus) -> Account:
        current = str(account.status)
        target_value = target.value
        if not cls.can_transition(current, target_value):
            raise InvalidAccountTransition(f"Illegal account transition: {current} -> {target_value}")

        account.status = target_value
        account.is_active = target not in {
            AccountStatus.disabled,
            AccountStatus.deactivated,
        }
        account.is_locked = target == AccountStatus.locked
        if target != AccountStatus.locked:
            account.locked_until = None
        return account

    @classmethod
    def activate(cls, account: Account) -> Account:
        return cls.transition(account, AccountStatus.active)

    @classmethod
    def suspend(cls, account: Account) -> Account:
        return cls.transition(account, AccountStatus.suspended)

    @classmethod
    def disable(cls, account: Account) -> Account:
        return cls.transition(account, AccountStatus.disabled)

    @classmethod
    def deactivate(cls, account: Account) -> Account:
        return cls.transition(account, AccountStatus.deactivated)
