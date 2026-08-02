from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus, AccountType
from app.identity.repositories.account_repository import AccountRepository
from app.security.auth import hash_password, verify_password

PASSWORD_MIN_LENGTH = 12
ACCOUNT_LOCKOUT_THRESHOLD = 5
ACCOUNT_LOCKOUT_DURATION_MINUTES = 30
PASSWORD_EXPIRY_DAYS = 90


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AccountRepository(session)

    async def create_account(
        self,
        identity_id: str,
        account_type: AccountType = AccountType.human,
        email: str | None = None,
        phone: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> Account:
        password_hash = None
        if password:
            password_hash = hash_password(password)

        account = Account(
            id=...,
            uuid=str(uuid.uuid4()),
            identity_id=identity_id,
            account_type=account_type.value,
            status=AccountStatus.pending_verification.value,
            email=email,
            phone=phone,
            username=username,
            password_hash=password_hash,
            password_changed_at=datetime.now(UTC) if password else None,
            password_expires_at=(
                datetime.now(UTC) + timedelta(days=PASSWORD_EXPIRY_DAYS) if password else None
            ),
            is_active=True,
            is_locked=False,
            failed_login_attempts=0,
            email_verified=False,
            phone_verified=False,
            identity_verified=False,
        )
        return await self.repo.create(account)

    async def authenticate(self, login: str, password: str) -> Account | None:
        account = await self.repo.find_by_email(login)
        if not account:
            account = await self.repo.find_by_username(login)
        if not account:
            return None

        # PROGRAM-05 Rule 10 / Appendix-B: suspended and deactivated accounts
        # must never authenticate, regardless of credentials.
        if account.status in (
            AccountStatus.suspended.value,
            AccountStatus.deactivated.value,
        ):
            return None

        if account.is_locked:
            if account.locked_until and account.locked_until > datetime.now(UTC):
                return None
            account.is_locked = False
            account.failed_login_attempts = 0
            await self.repo.session.flush()

        if not account.password_hash:
            return None

        if not verify_password(password, account.password_hash):
            account.failed_login_attempts += 1
            account.last_failed_login = datetime.now(UTC)
            if account.failed_login_attempts >= ACCOUNT_LOCKOUT_THRESHOLD:
                account.is_locked = True
                account.locked_until = datetime.now(UTC) + timedelta(
                    minutes=ACCOUNT_LOCKOUT_DURATION_MINUTES,
                )
                account.lock_reason = (
                    f"Account locked after {ACCOUNT_LOCKOUT_THRESHOLD} failed attempts"
                )
            await self.repo.session.flush()
            return None

        account.failed_login_attempts = 0
        account.last_login = datetime.now(UTC)
        await self.repo.session.flush()
        return account

    async def get_account(self, account_id: str) -> Account | None:
        return await self.repo.get_by_id(account_id)

    async def find_by_email(self, email: str) -> Account | None:
        return await self.repo.find_by_email(email)

    async def change_password(self, account_id: str, old_password: str, new_password: str) -> bool:
        account = await self.repo.get_by_id(account_id)
        if not account or not account.password_hash:
            return False
        if not verify_password(old_password, account.password_hash):
            return False
        account.password_hash = hash_password(new_password)
        account.password_changed_at = datetime.now(UTC)
        account.password_expires_at = datetime.now(UTC) + timedelta(days=PASSWORD_EXPIRY_DAYS)
        await self.repo.session.flush()
        return True

    async def lock_account(self, account_id: str, reason: str) -> bool:
        account = await self.repo.get_by_id(account_id)
        if not account:
            return False
        account.is_locked = True
        account.locked_until = None
        account.lock_reason = reason
        await self.repo.session.flush()
        return True

    async def unlock_account(self, account_id: str) -> bool:
        account = await self.repo.get_by_id(account_id)
        if not account:
            return False
        account.is_locked = False
        account.locked_until = None
        account.lock_reason = None
        account.failed_login_attempts = 0
        await self.repo.session.flush()
        return True

    # ── PROGRAM-05 Rule 10 — auditable account lifecycle state machine ──────

    # Allowed transitions. Keys/values are AccountStatus values.
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        "pending_verification": {"active", "suspended", "deactivated"},
        "active": {"suspended", "deactivated", "pending_verification"},
        "suspended": {"active", "deactivated"},
        "deactivated": {"active"},
        "locked": {"active", "suspended", "deactivated"},
    }

    async def transition_status(
        self,
        account_id: str,
        new_status: AccountStatus,
        reason: str,
        actor_id: str | None = None,
    ) -> tuple[Account, str] | None:
        """Move an account to a new lifecycle state.

        Returns (account, audit_action) on success; None when the transition
        is not allowed. Every transition is persisted and auditable.
        """
        account = await self.repo.get_by_id(account_id)
        if not account:
            return None
        allowed = self.ALLOWED_TRANSITIONS.get(account.status, set())
        if new_status.value not in allowed:
            return None

        old_status = account.status
        account.status = new_status.value
        if new_status == AccountStatus.active:
            account.activated_at = datetime.now(UTC)
        elif new_status == AccountStatus.deactivated:
            account.deactivated_at = datetime.now(UTC)
            account.deactivation_reason = reason
        await self.repo.session.flush()

        action = {
            AccountStatus.suspended: "account_suspended",
            AccountStatus.deactivated: "account_deactivated",
            AccountStatus.active: "account_restored",
        }.get(new_status, "account_status_changed")

        await self._audit_transition(
            account=account,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            action=action,
            actor_id=actor_id,
        )
        return account, action

    async def _audit_transition(
        self,
        account: Account,
        old_status: str,
        new_status: AccountStatus,
        reason: str,
        action: str,
        actor_id: str | None,
    ) -> None:
        from app.identity.models.audit import AuditAction
        from app.identity.services.audit_service import AuditService

        audit = AuditService(self.repo.session)
        await audit.record(
            action=AuditAction(action),
            actor_id=actor_id,
            actor_type="admin" if actor_id else "system",
            target_type="account",
            target_id=account.id,
            changes={
                "old_status": old_status,
                "new_status": new_status.value,
                "reason": reason,
            },
            outcome="success",
        )

    async def suspend_account(self, account_id: str, reason: str, actor_id: str | None = None):
        return await self.transition_status(account_id, AccountStatus.suspended, reason, actor_id)

    async def deactivate_account(self, account_id: str, reason: str, actor_id: str | None = None):
        return await self.transition_status(account_id, AccountStatus.deactivated, reason, actor_id)

    async def activate_account(self, account_id: str, reason: str, actor_id: str | None = None):
        return await self.transition_status(account_id, AccountStatus.active, reason, actor_id)
