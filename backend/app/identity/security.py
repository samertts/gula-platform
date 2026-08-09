from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db, get_niam_db
from app.identity.models.account import Account, AccountStatus
from app.security.auth import decode_token, is_token_blacklisted
from app.security.dependencies import _extract_token, get_current_user, security

if TYPE_CHECKING:
    from app.models.lab_user import LabUser

logger = logging.getLogger("gula.identity.security")

# NIAM routes accept two token families:
#   - identity-domain tokens  -> payload carries ``account_uuid``
#   - lab tokens (legacy UI)  -> payload carries ``user_id``
NIAMPrincipal = Union[Account, "LabUser"]


async def get_current_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_niam_db),
    sync_db: Session = Depends(get_db),
) -> NIAMPrincipal:
    """Authenticate the caller of an NIAM route.

    Rejects anonymous and revoked/expired tokens with 401. Accepts either an
    identity-domain access token (``account_uuid`` claim, validated against the
    active ``Account``) or a laboratory access token (``user_id`` claim,
    validated through the canonical ``get_current_user``), which the current
    admin frontend sends when it calls NIAM endpoints.
    """
    raw_token = _extract_token(credentials, request)
    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(raw_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        logger.warning("NIAM token revoked jti=%s", jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    account_uuid = payload.get("account_uuid")
    if account_uuid:
        result = await db.execute(select(Account).where(Account.uuid == account_uuid))
        account = result.scalar_one_or_none()
        if account is None or not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not found or inactive",
            )
        if account.status in (
            AccountStatus.suspended.value,
            AccountStatus.deactivated.value,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active",
            )
        if account.is_locked and account.locked_until:
            locked_until = account.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=UTC)
            if locked_until > datetime.now(UTC):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is locked",
                )
        return account

    if payload.get("user_id") is not None:
        return get_current_user(request, credentials, sync_db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token payload",
    )


async def get_actor_identity_id(
    principal: NIAMPrincipal = Depends(get_current_identity),
) -> str:
    """Return the authenticated actor's NIAM identity id.

    The actor is always derived from the verified token principal — never from
    a client-supplied parameter. Only identity-domain accounts map to a NIAM
    identity; legacy lab tokens cannot act as an NIAM workspace, professional
    registry, or governance actor.
    """
    if isinstance(principal, Account):
        return principal.identity_id
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Lab tokens cannot perform NIAM actor operations",
    )
