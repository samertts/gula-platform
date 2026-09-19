"""Bind a legacy login to the canonical NIAM session it belongs to (NR-135).

WHY THIS EXISTS
---------------
NIAM is the canonical identity authority. The clinical read gateway, and every
other NIAM-protected surface, authenticates through get_current_niam_actor_sync,
which requires a token carrying ``account_uuid`` and a ``jti`` that matches a
live ``niam_sessions`` row joined to an active ``niam_accounts`` row.

POST /login is the legacy authenticator. It minted a token carrying only legacy
claims -- act, exp, iat, jti, lab_id, perm_ver, role, type, user_id -- and
created no NIAM session. So it failed the gateway on two independent counts:
``account_uuid`` was absent from the claims, and no ``niam_sessions`` row
existed for the token's jti. No session the platform could mint reached the
platform's own clinical surface.

This module closes that without creating a second authority. Legacy
authentication remains the credential check; the canonical SESSION it produces
is a NIAM session, and the legacy token becomes a representation of that
session rather than an authority of its own.

WHAT IS SERVER-DERIVED, AND WHAT THE CLIENT MAY NEVER CHOOSE
------------------------------------------------------------
The canonical account is resolved from the ALREADY-AUTHENTICATED legacy row --
its table and its primary key -- through ``niam_legacy_account_links``. The
client supplies a credential and nothing else. It cannot name an
``account_uuid``, an ``identity_id``, a ``person_id``, a ``lab_id`` or a role
and have that become a security fact: none of those are read from the request
anywhere in this path.

FAIL-CLOSED BY CONSTRUCTION
---------------------------
When no canonical account is linked, or the linked account is not active, this
returns None and the caller mints exactly the legacy token it minted before.
The NIAM-protected surface then refuses that token with 401, as it already did.
Nothing is widened by the absence of a link: the only reachable outcomes are
"canonical session established" and "no worse than before".

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not create canonical accounts. ``LegacyMappingService`` states that it
"never creates canonical accounts ... those actions require separate approved
waves and an explicit feature-flagged cohort", and the direct account-creation
route is fail-closed at 410 behind a review-gated intake. Auto-provisioning an
account at login would walk through both of those boundaries, so provisioning
is left to the governed path and recorded as NR-137. This module binds what
already exists.
"""
from __future__ import annotations

import logging
import uuid as _uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
)
from app.identity.models.session import UserSession

logger = logging.getLogger("gula.identity.legacy_bridge")

#: Legacy `act` claim -> the source_kind recorded on a legacy account link.
#: These are the only two legacy account tables, and the mapping is fixed.
_ACCOUNT_KIND_TO_SOURCE = {
    "lab": LegacyAccountLinkSource.lab_user,
    "user": LegacyAccountLinkSource.user,
}


def resolve_canonical_account(
    db: Session,
    *,
    legacy_account_id: int,
    account_kind: str,
) -> Account | None:
    """The canonical NIAM account for an already-authenticated legacy row.

    Both arguments come from the authenticated legacy user, never from the
    request. Returns None when no link exists or the linked account is not in a
    state that may hold a session -- both of which leave the caller exactly
    where it was before this module existed.

    The link is read directly rather than through LegacyMappingService because
    that service requires a mapping HMAC key to construct, and a key is needed
    only to WRITE a fingerprint. Reading by (source_kind, legacy_account_id) is
    the same predicate the service's own get_link() uses.
    """
    source = _ACCOUNT_KIND_TO_SOURCE.get(account_kind)
    if source is None or not isinstance(legacy_account_id, int) or legacy_account_id <= 0:
        return None

    # A database error here must WITHHOLD authority, never break authentication.
    # Reading the link is an enrichment of a login that has already succeeded:
    # if the identity tables cannot be read -- a deployment mid-migration, a
    # schema that predates NIAM -- the right outcome is the one that already
    # applies when no link exists. The caller mints the legacy token, and the
    # NIAM-protected surface refuses it. Failing the login instead would turn a
    # missing table into an outage, and an error can never GRANT anything here:
    # every path out of this block returns None.
    #
    # The read runs inside a SAVEPOINT because PostgreSQL aborts the whole
    # transaction on a failed statement, and the caller still has an audit row
    # to write and a commit to make.
    try:
        with db.begin_nested():
            link = db.execute(
                select(LegacyAccountLink).where(
                    LegacyAccountLink.source_kind == source.value,
                    LegacyAccountLink.legacy_account_id == legacy_account_id,
                )
            ).scalar_one_or_none()
            if link is None or not link.canonical_account_id:
                return None

            return db.execute(
                select(Account).where(
                    Account.id == link.canonical_account_id,
                    Account.status == AccountStatus.active.value,
                    Account.is_active.is_(True),
                    Account.is_locked.is_(False),
                )
            ).scalar_one_or_none()
    except SQLAlchemyError:
        logger.warning(
            "canonical account lookup unavailable for %s#%s — issuing a legacy-only "
            "session; the NIAM-protected surface will refuse it",
            source.value,
            legacy_account_id,
            exc_info=True,
        )
        return None


def establish_canonical_session(
    db: Session,
    *,
    account: Account,
    access_jti: str,
    refresh_jti: str | None,
    expires_at: datetime,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> UserSession:
    """Record the NIAM session this login produced.

    The jti values are the ones already minted into the tokens being returned,
    so the session and the token identify the same login rather than two
    parallel ones. A login that reaches here has passed the legacy credential
    check, so auth_method records how the session was established.
    """
    session = UserSession(
        uuid=str(_uuid.uuid4()),
        account_id=account.id,
        token_jti=access_jti,
        refresh_token_jti=refresh_jti,
        session_type="web",
        is_active=True,
        ip_address=ip_address,
        user_agent=user_agent,
        started_at=datetime.now(UTC),
        last_activity_at=datetime.now(UTC),
        expires_at=expires_at,
        auth_method="legacy_password",
        mfa_used=False,
    )
    db.add(session)
    db.flush()
    bind_workspace_context(db, account=account, session=session)
    return session


def bind_workspace_context(db: Session, *, account: Account, session: UserSession) -> None:
    """NR-137: give the session the workspace it is unambiguously entitled to.

    NR-135 produced a canonical NIAM session and stopped there, so the clinical
    gateway's first link -- WorkspaceSessionContext -- was never created and
    every clinical read blocked at reason_code=missing_workspace. The identity
    was canonical; the organizational context behind it was absent.

    The selection is delegated to WorkspaceService.bind_unambiguous_context,
    which grants nothing: it chooses only among workspaces `list_eligible`
    already allows, requires an active membership to stand behind the choice,
    and binds nothing at all when the answer is not unique. A legacy record's
    lab_id and role do not make a workspace on their own.

    FAILS OPEN ON NOTHING, AND BREAKS LOGIN ON NOTHING. A database that has no
    workspace tables -- or any other error here -- must not take authentication
    down with it, which is the lesson NR-135 learned the hard way when wiring
    the account lookup in naively turned 30 passing auth tests into 24 errors.
    The SAVEPOINT keeps a failed statement from poisoning the transaction the
    caller still has to commit, and a failure simply leaves the session without
    a workspace, which the gateway already refuses correctly.
    """
    from app.identity.services.workspace_service import WorkspaceService

    try:
        with db.begin_nested():
            WorkspaceService(db).bind_unambiguous_context(account, session.id)
    except SQLAlchemyError:
        logger.warning(
            "workspace context unavailable for account %s -- the session stands "
            "without one and the clinical gateway will refuse it",
            account.id, exc_info=True,
        )
    except Exception:
        logger.warning(
            "workspace selection failed for account %s; session left unbound",
            account.id, exc_info=True,
        )


def terminate_canonical_session(db: Session, *, access_jti: str, reason: str) -> int:
    """Close the NIAM session a legacy token represents. Returns rows closed.

    Logout has to reach the canonical session too, or a token revoked on the
    legacy side would keep opening the NIAM-protected surface for as long as
    the session row stayed active.
    """
    sessions = db.execute(
        select(UserSession).where(
            UserSession.token_jti == access_jti,
            UserSession.is_active.is_(True),
        )
    ).scalars().all()
    for session in sessions:
        session.is_active = False
        session.terminated_at = datetime.now(UTC)
        session.termination_reason = reason
    if sessions:
        db.flush()
    return len(sessions)


def session_expiry(refresh_token_expire_days: int) -> datetime:
    """The session outlives the access token but not the refresh token."""
    return datetime.now(UTC) + timedelta(days=refresh_token_expire_days)
