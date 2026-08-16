from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account
from app.identity.models.session import UserSession
from app.identity.repositories.account_repository import AccountRepository
from app.identity.repositories.session_repository import SessionRepository
from app.identity.services.account_service import AccountService

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthenticationService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.account_service = AccountService(session)
        self.account_repo = AccountRepository(session)
        self.session_repo = SessionRepository(session)

    async def login(
        self,
        login: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
    ) -> dict | None:
        account = await self.account_service.authenticate(login, password)
        if not account:
            return None

        return await self._create_session(
            account=account,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location_city=location_city,
            location_country=location_country,
        )

    async def _create_session(
        self,
        account: Account,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
    ) -> dict:
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())

        from app.security.auth import create_refresh_token, create_token

        access_token = create_token(
            {
                "jti": access_jti,
                "account_uuid": account.uuid,
                "identity_id": account.identity_id,
            },
        )

        refresh_token = create_refresh_token(
            {"jti": refresh_jti, "account_uuid": account.uuid},
        )

        session = UserSession(
            uuid=str(uuid.uuid4()),
            account_id=account.id,
            token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            session_type="web",
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location_city=location_city,
            location_country=location_country,
            started_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            mfa_used=False,
        )
        await self.session_repo.create(session)
        from app.identity.services.workspace_service import WorkspaceService

        await WorkspaceService(self.session).ensure_citizen_workspace(account)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_uuid": session.uuid,
            "account_uuid": account.uuid,
        }

    async def refresh_session(self, refresh_token: str) -> dict | None:
        from app.security.auth import blacklist_token, decode_refresh_token

        payload = decode_refresh_token(refresh_token)
        if not payload:
            return None
        refresh_jti = payload.get("jti")
        if not refresh_jti:
            return None

        session = await self.session_repo.find_by_refresh_token_jti(refresh_jti)
        if not session or not session.is_active or session.expires_at < datetime.now(UTC):
            return None

        account = await self.account_repo.get_by_id(session.account_id)
        if (
            not account
            or not account.is_active
            or account.status != "active"
            or account.is_locked
        ):
            return None

        remaining_seconds = max(1, int((session.expires_at - datetime.now(UTC)).total_seconds()))
        blacklist_token(refresh_jti, remaining_seconds)
        await self.session_repo.soft_delete(session.id)
        return await self._create_session(
            account=account,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_id=session.device_id,
        )

    async def logout(self, session_uuid: str, account_id: str | None = None) -> bool:
        session = await self.session_repo.get_by_uuid(session_uuid)
        if not session:
            return False
        if account_id is not None and str(session.account_id) != str(account_id):
            return False
        await self.session_repo.terminate_session(
            session_id=session.id,
            reason="user_logout",
            terminated_by="user",
        )
        return True

    async def logout_all_sessions(self, account_id: str) -> None:
        await self.session_repo.terminate_all_for_account(
            account_id=account_id,
            reason="user_logout_all",
        )
