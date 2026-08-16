from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.session import UserSession
from app.identity.repositories.account_repository import AccountRepository
from app.identity.repositories.session_repository import SessionRepository
from app.identity.services.account_service import AccountService
from app.identity.session_policy import session_is_usable

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
            await self._audit_login_failure(login)
            return None

        result = await self._create_session(
            account=account,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location_city=location_city,
            location_country=location_country,
        )
        await self._audit_event(
            "login_success",
            actor_id=str(account.id),
            target_id=str(account.uuid),
            metadata={"auth_method": "password"},
        )
        return result

    async def _create_session(
        self,
        account: Account,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        refresh_family_id: str | None = None,
        auth_method: str = "password",
        mfa_used: bool = False,
        refresh_jti: str | None = None,
    ) -> dict:
        access_jti = str(uuid.uuid4())
        refresh_jti = refresh_jti or str(uuid.uuid4())
        refresh_family_id = refresh_family_id or str(uuid.uuid4())
        now = datetime.now(UTC)

        from app.security.auth import create_refresh_token, create_token

        access_token = create_token(
            {
                "jti": access_jti,
                "account_uuid": account.uuid,
                "identity_id": account.identity_id,
            },
        )

        refresh_token = create_refresh_token(
            {
                "jti": refresh_jti,
                "account_uuid": account.uuid,
            },
        )

        session = UserSession(
            uuid=str(uuid.uuid4()),
            account_id=account.id,
            token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            refresh_family_id=refresh_family_id,
            session_type="web",
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location_city=location_city,
            location_country=location_country,
            started_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            auth_method=auth_method,
            mfa_used=mfa_used,
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
            "refresh_family_id": refresh_family_id,
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
        if not session:
            # A rotated token remains in the database as inactive. Finding it is
            # the durable replay signal; invalidate the complete family rather
            # than only rejecting the attacker request.
            rotated_session = await self._find_refresh_session_any_state(refresh_jti)
            if rotated_session and getattr(rotated_session, "termination_reason", None) == "refresh_rotation":
                family_id = getattr(rotated_session, "refresh_family_id", None)
                if family_id:
                    terminate_family = getattr(self.session_repo, "terminate_all_for_refresh_family", None)
                    if terminate_family is not None:
                        await terminate_family(family_id, "refresh_reuse_detected")
                blacklist_token(refresh_jti, self._remaining_token_seconds(rotated_session))
                await self._audit_event(
                    "session_reuse_detected",
                    actor_id=str(getattr(rotated_session, "account_id", "")),
                    target_id=str(getattr(rotated_session, "uuid", "")),
                    metadata={"refresh_family_id": family_id},
                    outcome="denied",
                )
            return None

        now = datetime.now(UTC)
        if not session.is_active or not session_is_usable(
            now=now,
            expires_at=getattr(session, "expires_at", None),
            last_activity_at=getattr(session, "last_activity_at", None) or now,
        ):
            await self._terminate_expired_session(session)
            return None

        account = await self.account_repo.get_by_id(session.account_id)
        if not self._account_can_authenticate(account):
            return None

        new_refresh_jti = str(uuid.uuid4())
        session.refresh_replaced_by_jti = new_refresh_jti
        session.termination_reason = "refresh_rotation"
        remaining_seconds = self._remaining_token_seconds(session)
        blacklist_token(refresh_jti, remaining_seconds)
        await self.session_repo.soft_delete(session.id)
        result = await self._create_session(
            account=account,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_id=session.device_id,
            refresh_family_id=getattr(session, "refresh_family_id", None),
            auth_method=getattr(session, "auth_method", None) or "password",
            mfa_used=bool(getattr(session, "mfa_used", False)),
            refresh_jti=new_refresh_jti,
        )
        await self._audit_event(
            "session_refreshed",
            actor_id=str(getattr(account, "id", getattr(account, "uuid", ""))),
            target_id=str(getattr(session, "uuid", getattr(session, "id", ""))),
            metadata={"refresh_family_id": getattr(session, "refresh_family_id", None)},
        )
        return result

    async def logout(self, session_uuid: str, *, account_id: str | None = None) -> bool:
        session = await self.session_repo.get_by_uuid(session_uuid)
        if not session or (account_id is not None and str(session.account_id) != str(account_id)):
            return False
        self._blacklist_session_tokens(session)
        await self.session_repo.terminate_session(
            session_id=session.id,
            reason="user_logout",
            terminated_by=str(account_id or "user"),
        )
        await self._audit_event(
            "logout",
            actor_id=str(account_id or session.account_id),
            target_id=str(getattr(session, "uuid", getattr(session, "id", ""))),
            metadata={"scope": "current_session"},
        )
        return True

    async def logout_all_sessions(self, account_id: str) -> int:
        sessions = await self.session_repo.find_by_account_id(account_id)
        for session in sessions:
            self._blacklist_session_tokens(session)
        await self.session_repo.terminate_all_for_account(
            account_id=account_id,
            reason="user_logout_all",
        )
        await self._audit_event(
            "logout",
            actor_id=str(account_id),
            target_id=str(account_id),
            metadata={"scope": "all_sessions", "count": len(sessions)},
        )
        return len(sessions)

    async def _find_refresh_session_any_state(self, refresh_jti: str) -> UserSession | None:
        finder = self.session_repo.find_by_refresh_token_jti
        try:
            return await finder(refresh_jti, active_only=False)
        except TypeError:
            # Keeps the service compatible with narrow unit-test repositories
            # and older adapters while production uses the durable query.
            return await finder(refresh_jti)

    async def _terminate_expired_session(self, session: UserSession) -> None:
        self._blacklist_session_tokens(session)
        await self.session_repo.terminate_session(
            session_id=session.id,
            reason="session_expired_or_idle",
            terminated_by="system",
        )
        await self._audit_event(
            "session_terminated",
            actor_id=str(session.account_id),
            target_id=str(getattr(session, "uuid", getattr(session, "id", ""))),
            metadata={"reason": "session_expired_or_idle"},
            outcome="denied",
        )

    def _account_can_authenticate(self, account: Account | None) -> bool:
        if account is None or not getattr(account, "is_active", False):
            return False
        if getattr(account, "is_locked", False):
            return False
        status = getattr(account, "status", AccountStatus.active.value)
        return status == AccountStatus.active.value

    def _blacklist_session_tokens(self, session: UserSession) -> None:
        from app.security.auth import blacklist_token

        blacklist_token(
            session.token_jti,
            max(1, self._remaining_token_seconds(session)),
        )
        if session.refresh_token_jti:
            blacklist_token(
                session.refresh_token_jti,
                max(1, self._remaining_token_seconds(session)),
            )

    @staticmethod
    def _remaining_token_seconds(session: UserSession) -> int:
        expires_at = getattr(session, "expires_at", None)
        if expires_at is None:
            return REFRESH_TOKEN_EXPIRE_DAYS * 86400
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return max(1, int((expires_at - datetime.now(UTC)).total_seconds()))

    @staticmethod
    def _decode_jti(token: str | None) -> str | None:
        if not token:
            return None
        try:
            from app.security.auth import decode_refresh_token

            return decode_refresh_token(token).get("jti")
        except Exception:
            return None

    async def _audit_login_failure(self, login: str) -> None:
        await self._audit_event(
            "login_failure",
            metadata={"identifier_present": bool(login)},
            outcome="denied",
        )

    async def _audit_event(
        self,
        action: str,
        *,
        actor_id: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
        outcome: str = "success",
    ) -> None:
        # Unit doubles intentionally provide no database API. Production
        # AsyncSession instances do, and the canonical hash-chained audit log is
        # written there without ever receiving a password, OTP, or token value.
        from sqlalchemy.ext.asyncio import AsyncSession

        if not isinstance(self.session, AsyncSession):
            return
        from app.identity.services.audit_service import AuditService

        await AuditService(self.session).record_event(
            action=action,
            actor_id=actor_id,
            target_type="session",
            target_id=target_id,
            metadata=metadata,
            outcome=outcome,
        )
