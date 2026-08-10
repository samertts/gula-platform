from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.base import _ulid
from app.identity.models.account import Account, AccountStatus, AccountType
from app.identity.models.audit import AuditAction
from app.identity.repositories.account_repository import AccountRepository
from app.identity.services.audit_service import AuditService
from app.identity.services.session_service import SessionService
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
        created = await self.repo.create(account)
        if created.id is Ellipsis or created.id is None:
            created.id = _ulid()

        await AuditService(self.repo.session).record(
            action=AuditAction.account_created,
            actor_type="system",
            target_type="account",
            target_id=created.id,
            metadata={
                "account_type": account.account_type,
                "initial_status": AccountStatus.pending_verification.value,
            },
            outcome="success",
        )
        return created

    async def authenticate(self, login: str, password: str) -> Account | None:
        account = await self.repo.find_by_email(login)
        if not account:
            account = await self.repo.find_by_username(login)
        if not account:
            return None

        # PROGRAM-05 Rule 10 / Appendix-B: suspended, deactivated, revoked and
        # retired accounts must never authenticate, regardless of credentials.
        if account.status in (
            AccountStatus.suspended.value,
            AccountStatus.deactivated.value,
            AccountStatus.revoked.value,
            AccountStatus.retired.value,
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

    async def find_by_username(self, username: str) -> Account | None:
        return await self.repo.find_by_username(username)

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

    # Allowed transitions. Keys/values are AccountStatus values. ``revoked``
    # and ``retired`` are terminal states: no transition leaves them.
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        "pending_verification": {"active", "suspended", "revoked", "deactivated"},
        "active": {"suspended", "revoked", "retired", "deactivated", "pending_verification"},
        "suspended": {"active", "revoked", "retired", "deactivated"},
        "revoked": set(),
        "retired": set(),
        "deactivated": {"active", "revoked", "retired"},
        "locked": {"active", "suspended", "revoked", "retired", "deactivated"},
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
        is not allowed. Every transition is persisted and auditable. Moving
        away from an operational state invalidates the account's active
        sessions (stale tokens stop working); history is never deleted — every
        transition is appended to the immutable audit chain.
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
            account.is_active = True
            account.is_locked = False
            account.locked_until = None
            account.lock_reason = None
            account.failed_login_attempts = 0
        elif new_status in (
            AccountStatus.suspended,
            AccountStatus.revoked,
            AccountStatus.retired,
            AccountStatus.deactivated,
        ):
            account.is_active = False
            account.deactivated_at = datetime.now(UTC)
            account.deactivation_reason = reason
        await self.repo.session.flush()

        action = {
            AccountStatus.suspended: "account_suspended",
            AccountStatus.deactivated: "account_deactivated",
            AccountStatus.revoked: "account_revoked",
            AccountStatus.retired: "account_retired",
            AccountStatus.active: "account_restored",
        }.get(new_status, "account_status_changed")

        if new_status not in (AccountStatus.active, AccountStatus.pending_verification):
            await self._invalidate_sessions(account, reason=f"account_{new_status.value}")

        await self._audit_transition(
            account=account,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            action=action,
            actor_id=actor_id,
        )
        return account, action

    async def _invalidate_sessions(self, account: Account, reason: str) -> None:
        """Terminate all active sessions so stale tokens stop working."""
        session_service = SessionService(self.repo.session)
        active = await session_service.get_active_sessions(account.id)
        count = len(active) if isinstance(active, list) else 0
        await session_service.terminate_all(account.id, reason=reason)
        if count:
            await AuditService(self.repo.session).record(
                action=AuditAction.account_sessions_invalidated,
                actor_type="system",
                target_type="account",
                target_id=account.id,
                metadata={"reason": reason, "sessions_terminated": count},
                outcome="success",
            )

    async def _audit_transition(
        self,
        account: Account,
        old_status: str,
        new_status: AccountStatus,
        reason: str,
        action: str,
        actor_id: str | None,
    ) -> None:
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

    async def revoke_account(self, account_id: str, reason: str, actor_id: str | None = None):
        """Permanently revoke an account (terminal state)."""
        return await self.transition_status(account_id, AccountStatus.revoked, reason, actor_id)

    async def retire_account(self, account_id: str, reason: str, actor_id: str | None = None):
        """Permanently retire an account (terminal state)."""
        return await self.transition_status(account_id, AccountStatus.retired, reason, actor_id)
