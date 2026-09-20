"""Platform Authority bootstrap -- the first legitimate assignment.

Implements the mechanism designed in
docs/security/NIAM_PLATFORM_AUTHORITY_BOOTSTRAP.md, resolving its one
BLOCKED prerequisite (no async DB engine existed) now that
app/identity/niam_async_db.py provides one. Mirrors the existing,
evidenced `app/core/bootstrap/master_admin.py::ensure_master_admin`
pattern exactly: never exposed via any HTTP route, deployment/environment
-controlled, fail-closed on missing or malformed configuration, and
self-disabling by construction (idempotent per (identity, capability)
pair, including historical/revoked rows -- never re-grants a capability
that was ever bootstrap-issued, even if later revoked).

Environment variables (both must be set; absence of either is a
deliberate, silent no-op -- "absence of configuration means absence of
bootstrap", matching GULA_ADMIN_PASSWORD's own doctrine):

  PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL
      An email address that must resolve to an existing, active
      niam_accounts row (mirrors GULA_ADMIN_EMAIL -- the operator already
      has a real account, created through the ordinary NIAM signup flow,
      before bootstrap can point at it).

  PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES
      Comma-separated list of PlatformCapability values, e.g.
      "platform.federation.manage,platform.trust.manage". Any entry that
      is not one of the four known capabilities is rejected individually
      (logged, skipped) -- a typo in one capability never blocks the
      others, and never grants anything unlisted.

Not wired into any code path that runs automatically against a real
deployment beyond the same non-fatal seeding list `ensure_master_admin`
already uses -- both env vars are unset on every current deployment, so
this remains a complete no-op until an operator deliberately configures
it, exactly like the existing precedent.
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.account import Account, AccountStatus
from app.identity.platform_authority.models import (
    PlatformAuthorityAssignment,
    PlatformCapability,
)
from app.identity.platform_authority.services import (
    PlatformAuthorityService,
    UnknownPlatformCapability,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService

logger = logging.getLogger("gula.identity.platform_authority.bootstrap")

_ACCOUNT_EMAIL_VAR = "PLATFORM_AUTHORITY_BOOTSTRAP_ACCOUNT_EMAIL"
_CAPABILITIES_VAR = "PLATFORM_AUTHORITY_BOOTSTRAP_CAPABILITIES"


async def _resolve_bootstrap_account(session: AsyncSession, email: str) -> Account | None:
    stmt = select(Account).where(
        Account.email == email,
        Account.status == AccountStatus.active.value,
        Account.is_active.is_(True),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _already_handled(session: AsyncSession, identity_id: str, capability: str) -> bool:
    """True if ANY assignment (active or historical/revoked) already
    exists for this (identity, capability) pair -- the self-disabling
    check from the design doc's Section 7/8/10: a capability that was
    ever bootstrap-granted is never re-granted, even after revocation,
    and a crash between capabilities correctly resumes only the ones
    still missing on the next restart."""
    stmt = select(PlatformAuthorityAssignment.id).where(
        PlatformAuthorityAssignment.identity_id == identity_id,
        PlatformAuthorityAssignment.capability == capability,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def ensure_platform_authority_bootstrap(session: AsyncSession) -> list[str]:
    """Idempotent, fail-closed bootstrap. Returns the list of capabilities
    actually granted this call (empty on a no-op run, including when
    unconfigured -- never raises for ordinary "not configured" absence;
    only genuine unexpected errors propagate, matching every other
    non-fatal startup_guard seeding step's contract)."""
    email = os.getenv(_ACCOUNT_EMAIL_VAR, "").strip()
    capabilities_raw = os.getenv(_CAPABILITIES_VAR, "").strip()
    if not email or not capabilities_raw:
        return []

    account = await _resolve_bootstrap_account(session, email)
    if account is None:
        logger.error(
            "[PLATFORM AUTHORITY BOOTSTRAP] %s=%r does not resolve to an active account -- "
            "no capability granted.",
            _ACCOUNT_EMAIL_VAR, email,
        )
        return []

    audit = CanonicalAuditService(session)
    service = PlatformAuthorityService(session)
    granted: list[str] = []

    requested = [c.strip() for c in capabilities_raw.split(",") if c.strip()]
    known = {c.value for c in PlatformCapability}

    await audit.record(
        AuditEventInput(
            event_type="bootstrap_started",
            category="PLATFORM_AUTHORITY",
            action="platform_authority.bootstrap.started",
            actor_id=None,
            actor_type="system",
            target_type="niam_identity",
            target_id=account.identity_id,
            decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_BOOTSTRAP",
            data_classification="INTERNAL",
            metadata={"requested_capabilities": requested},
        ),
    )

    for capability in requested:
        if capability not in known:
            logger.error(
                "[PLATFORM AUTHORITY BOOTSTRAP] %r is not a known PlatformCapability -- skipped.",
                capability,
            )
            continue
        if await _already_handled(session, account.identity_id, capability):
            logger.info(
                "[PLATFORM AUTHORITY BOOTSTRAP] %s already has an assignment for %s "
                "(active or historical) -- skipped, not re-granted.",
                account.identity_id, capability,
            )
            continue
        try:
            await service.grant(
                identity_id=account.identity_id,
                capability=capability,
                granted_by_account_id=None,
            )
        except UnknownPlatformCapability:
            # unreachable given the `known` filter above, but never let a
            # single bad entry silently short-circuit the loop either way
            logger.error(
                "[PLATFORM AUTHORITY BOOTSTRAP] grant() rejected %r unexpectedly.", capability,
            )
            continue
        granted.append(capability)
        logger.info(
            "[PLATFORM AUTHORITY BOOTSTRAP] granted %s to identity %s.",
            capability, account.identity_id,
        )

    await audit.record(
        AuditEventInput(
            event_type="bootstrap_completed",
            category="PLATFORM_AUTHORITY",
            action="platform_authority.bootstrap.completed",
            actor_id=None,
            actor_type="system",
            target_type="niam_identity",
            target_id=account.identity_id,
            decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_BOOTSTRAP",
            data_classification="INTERNAL",
            metadata={"granted_capabilities": granted},
        ),
    )
    return granted
