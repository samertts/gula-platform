from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus, AccountType
from app.identity.repositories.account_repository import AccountRepository
from app.identity.services.account_lifecycle_service import AccountLifecycleService
from app.security.auth import _DUMMY_HASH, hash_password, verify_password

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
        email = email.strip().lower() if email else None
        phone = re.sub(r"\s+", "", phone) if phone else None
        username = username.strip().lower() if username else None
        if not any((email, phone, username)):
            raise ValueError("At least one normalized account identifier is required")
        if password is not None and len(password) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must contain at least {PASSWORD_MIN_LENGTH} characters")

        password_hash = None
        if password:
            password_hash = hash_password(password)

        account = Account(
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
        normalized_login = login.strip()
        if "@" in normalized_login:
            normalized_login = normalized_login.lower()
        else:
            normalized_login = re.sub(r"\s+", "", normalized_login)
        account = await self.repo.find_by_login(normalized_login)
        if not account:
            verify_password(password, _DUMMY_HASH)
            return None

        if account.status in {
            AccountStatus.pending_verification.value,
            AccountStatus.suspended.value,
            AccountStatus.disabled.value,
            AccountStatus.deactivated.value,
        } or not account.is_active:
            verify_password(password, account.password_hash or _DUMMY_HASH)
            return None

        password_is_valid = verify_password(password, account.password_hash or _DUMMY_HASH)

        if account.is_locked or account.status == AccountStatus.locked.value:
            now = datetime.now(UTC)
            # A lock without an expiry is an explicit/manual lock. It must not
            # be cleared by an unauthenticated login attempt. Only an expired
            # timed lockout may be reopened automatically.
            if account.locked_until is None:
                return None
            if account.locked_until > now:
                return None
            AccountLifecycleService.transition(account, AccountStatus.active)
            account.failed_login_attempts = 0
            await self.repo.session.flush()

        if not account.password_hash or not password_is_valid:
            account.failed_login_attempts += 1
            account.last_failed_login = datetime.now(UTC)
            if account.failed_login_attempts >= ACCOUNT_LOCKOUT_THRESHOLD:
                AccountLifecycleService.transition(account, AccountStatus.locked)
                account.locked_until = datetime.now(UTC) + timedelta(
                    minutes=ACCOUNT_LOCKOUT_DURATION_MINUTES,
                )
                account.lock_reason = f"Account locked after {ACCOUNT_LOCKOUT_THRESHOLD} failed attempts"
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
        AccountLifecycleService.transition(account, AccountStatus.locked)
        account.locked_until = None
        account.lock_reason = reason
        await self.repo.session.flush()
        return True

    async def unlock_account(self, account_id: str) -> bool:
        account = await self.repo.get_by_id(account_id)
        if not account:
            return False
        AccountLifecycleService.transition(account, AccountStatus.active)
        account.locked_until = None
        account.lock_reason = None
        account.failed_login_attempts = 0
        await self.repo.session.flush()
        return True
