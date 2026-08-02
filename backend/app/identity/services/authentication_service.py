from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.adaptive_auth.services import SessionGovernanceService
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
        self.session_governance = SessionGovernanceService(session)

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
            await self._audit(
                action="login_failed",
                actor_type="unknown",
                target_type="account",
                target_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"login": login, "reason": "invalid_credentials_or_status"},
            )
            return None

        # PROGRAM-05 Rule 8/9 — enforce per-account-type session policy:
        # terminate the oldest sessions when the concurrent limit is exceeded.
        policy_result = await self.session_governance.enforce_session_policy(
            account.id,
            account.account_type,
        )
        if policy_result.get("action") == "block_new_session":
            await self._audit(
                action="login_failed",
                actor_id=account.id,
                actor_type=account.account_type,
                target_type="account",
                target_id=account.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"reason": "session_policy_blocked", "detail": policy_result},
            )
            return None

        await self._audit(
            action="login_succeeded",
            actor_id=account.id,
            actor_type=account.account_type,
            target_type="account",
            target_id=account.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"policy_action": policy_result.get("action")},
        )

        return await self._create_session(
            account=account,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location_city=location_city,
            location_country=location_country,
            policy=policy_result,
        )

    async def _audit(
        self,
        action: str,
        actor_id: str | None = None,
        actor_type: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        from app.identity.models.audit import AuditAction
        from app.identity.services.audit_service import AuditService

        await AuditService(self.session).record(
            action=AuditAction(action),
            actor_id=actor_id,
            actor_type=actor_type,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome="success",
        )

    async def _create_session(
        self,
        account: Account,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        policy: dict | None = None,
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
            id=...,
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
            mfa_used=bool(account.mfa_enabled),
            policy_id=policy.get("policy_id") if policy else None,
        )
        await self.session_repo.create(session)

        await self._audit(
            action="session_started",
            actor_id=account.id,
            actor_type=account.account_type,
            target_type="session",
            target_id=session.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"session_uuid": session.uuid, "policy_action": (policy or {}).get("action")},
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_uuid": session.uuid,
            "account_uuid": account.uuid,
        }

    async def refresh_session(self, refresh_token_jti: str) -> dict | None:
        session = await self.session_repo.find_by_token_jti(refresh_token_jti)
        if not session or not session.is_active or session.expires_at < datetime.now(UTC):
            return None

        account = await self.account_repo.get_by_id(session.account_id)
        if not account or not account.is_active:
            return None

        await self.session_repo.soft_delete(session.id)
        return await self._create_session(
            account=account,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_id=session.device_id,
        )

    async def logout(self, session_uuid: str) -> None:
        session = await self.session_repo.get_by_uuid(session_uuid)
        if session:
            await self.session_repo.terminate_session(
                session_id=session.id,
                reason="user_logout",
                terminated_by="user",
            )
            await self._audit(
                action="logout_succeeded",
                actor_type="user",
                target_type="session",
                target_id=session.id,
                metadata={"session_uuid": session_uuid, "reason": "user_logout"},
            )

    async def logout_all_sessions(self, account_id: str) -> None:
        await self.session_repo.terminate_all_for_account(
            account_id=account_id,
            reason="user_logout_all",
        )
        await self._audit(
            action="logout_succeeded",
            actor_type="user",
            target_type="account",
            target_id=account_id,
            metadata={"reason": "user_logout_all"},
        )
