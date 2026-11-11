from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models import UserSession
from app.identity.niam_async_db import get_niam_db

from .models import AdaptiveMFASession, ImpossibleTravelEvent, RiskPolicy, SessionPolicy
from .services import AdaptiveAuthService, SessionGovernanceService

router = APIRouter(prefix="/niam/adaptive-auth", tags=["NIAM Adaptive Auth"])

_POLICY_AUTHORITY_UNAVAILABLE = (
    "Managing platform-wide risk/session policy requires an administrative "
    "authorization decision that does not yet exist in NIAM. "
    "app.identity.services.authorization_decision.AuthorizationDecisionService "
    "is organization-scoped (it denies by design whenever organization_id is "
    "absent and the resource type is not in its NON_ORGANIZATIONAL_READS "
    "allowlist, which RiskPolicy/SessionPolicy are not) — it is the wrong "
    "tool for a genuinely global resource, and widening that allowlist would "
    "be a change to canonical NIAM authorization semantics this branch is not "
    "authorized to make on its own. Until a real platform-admin concept is "
    "decided, this fails closed rather than granting every authenticated "
    "NIAM actor (this router's only existing gate) the ability to rewrite "
    "global security policy."
)


def _require_policy_admin() -> None:
    """Fails closed. See _POLICY_AUTHORITY_UNAVAILABLE.

    Before this, create_risk_policy/update_risk_policy/create_session_policy/
    update_session_policy required nothing beyond the router-level
    Depends(get_current_niam_actor) (any authenticated account, any role) —
    any logged-in user could rewrite platform-wide risk thresholds,
    mitigation actions, MFA requirements, and session limits for every
    tenant.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=_POLICY_AUTHORITY_UNAVAILABLE,
    )


_CROSS_ACCOUNT_AUTHORITY_UNAVAILABLE = (
    "This operation targets another account's security/session data. No "
    "existing NIAM Platform Authority capability or AuthorizationDecisionService "
    "permission is scoped to authorize one account acting on another "
    "account's adaptive-auth resources (risk history, MFA challenges, "
    "sessions, device/travel records) -- the four PlatformCapability values "
    "(federation_manage, trust_manage, certificates_manage, "
    "governance_manage) are platform-administrative concepts unrelated to "
    "this operation's actual semantics, and AuthorizationDecisionService is "
    "organization-scoped (see _POLICY_AUTHORITY_UNAVAILABLE above), which "
    "does not fit an account-to-account security check either. Rather than "
    "invent a new permission unilaterally, this fails closed to "
    "self-access-only until a real cross-account security-administration "
    "authority is designed and reviewed."
)


def _require_self(actor: NiamActor, account_id: str) -> None:
    """Object-level ownership check for adaptive-auth's account-scoped
    resources (risk evaluation/history, MFA challenges, sessions, device
    and travel records). These are NOT organization-scoped, so NIAM's
    AuthorizationDecisionService (Membership/Role/Permission ABAC) does not
    apply -- the only trustworthy authorization signal here is identity:
    the caller may only act on their own account. Never trust a
    client-supplied account_id as authorization by itself.
    """
    if account_id != actor.account.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_CROSS_ACCOUNT_AUTHORITY_UNAVAILABLE,
        )


@router.post("/evaluate")
async def evaluate_risk(
    account_id: str,
    ip_address: str,
    user_agent: str = "",
    location: dict[str, Any] | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    service = AdaptiveAuthService(db)
    result = await service.evaluate_risk(
        account_id=account_id,
        ip_address=ip_address,
        user_agent=user_agent,
        location=location,
    )
    mitigation = await service.apply_mitigation(result["risk_score"], account_id)
    await db.commit()
    return {"risk_assessment": result, "mitigation": mitigation}


@router.get("/risk-history/{account_id}")
async def get_risk_history(
    account_id: str,
    limit: int = Query(50, ge=1, le=500),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    service = AdaptiveAuthService(db)
    events = await service.get_risk_history(account_id, limit=limit)
    return [e.to_dict() for e in events]


@router.post("/mfa/challenge")
async def create_mfa_challenge(
    account_id: str,
    mfa_type: str = "totp",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    service = AdaptiveAuthService(db)
    mfa = await service.create_mfa_challenge(account_id=account_id, mfa_type=mfa_type)
    await db.commit()
    return {
        "mfa_id": mfa.mfa_id,
        "mfa_type": mfa.mfa_type,
        "expires_at": mfa.challenge_expires_at.isoformat(),
    }


@router.post("/mfa/verify")
async def verify_mfa_challenge(
    mfa_id: str,
    challenge_response: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    # verify_mfa takes no account_id -- resolve the target MFA session's
    # owning account first so a client can never probe or answer another
    # account's MFA challenge merely by guessing/obtaining its mfa_id.
    existing = (
        await db.execute(
            select(AdaptiveMFASession).where(
                AdaptiveMFASession.mfa_id == mfa_id,
                AdaptiveMFASession.is_active.is_(True),
            ),
        )
    ).scalar_one_or_none()
    if existing is not None:
        _require_self(actor, existing.account_id)
    service = AdaptiveAuthService(db)
    result = await service.verify_mfa(mfa_id=mfa_id, challenge_response=challenge_response)
    await db.commit()
    return result


@router.get("/policies")
async def list_risk_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_niam_db),
):
    stmt = (
        select(RiskPolicy)
        .where(RiskPolicy.is_active.is_(True))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    policies = list(result.scalars().all())
    return [p.to_dict() for p in policies]


@router.post("/policies")
async def create_risk_policy(
    policy_id: str,
    name: str,
    risk_threshold_low: int,
    risk_threshold_medium: int,
    risk_threshold_high: int,
    risk_threshold_critical: int,
    actions: dict[str, Any],
    description: str | None = None,
    scope: dict[str, Any] | None = None,
    enabled: bool = True,
    db: AsyncSession = Depends(get_niam_db),
    _: None = Depends(_require_policy_admin),
):
    entity = RiskPolicy(
        uuid=str(__import__("uuid").uuid4()),
        policy_id=policy_id,
        name=name,
        description=description,
        risk_threshold_low=risk_threshold_low,
        risk_threshold_medium=risk_threshold_medium,
        risk_threshold_high=risk_threshold_high,
        risk_threshold_critical=risk_threshold_critical,
        actions=actions,
        scope=scope,
        enabled=enabled,
        is_active=True,
    )
    db.add(entity)
    await db.flush()
    await db.commit()
    return entity.to_dict()


@router.post("/policies/{policy_id}")
async def update_risk_policy(
    policy_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_niam_db),
    _: None = Depends(_require_policy_admin),
):
    stmt = select(RiskPolicy).where(
        RiskPolicy.policy_id == policy_id,
        RiskPolicy.is_active.is_(True),
    )
    result = await db.execute(stmt)
    entity = result.scalar_one_or_none()
    if not entity:
        return {"error": "not_found"}
    for key, value in body.items():
        if hasattr(entity, key) and value is not None:
            setattr(entity, key, value)
    await db.flush()
    await db.commit()
    return entity.to_dict()


@router.get("/session-policies")
async def list_session_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_niam_db),
):
    stmt = (
        select(SessionPolicy)
        .where(SessionPolicy.is_active.is_(True))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    policies = list(result.scalars().all())
    return [p.to_dict() for p in policies]


@router.post("/session-policies")
async def create_session_policy(
    policy_id: str,
    name: str,
    applies_to: str,
    max_sessions: int = 1,
    allow_concurrent: bool = False,
    require_mfa: bool = False,
    session_timeout_minutes: int | None = None,
    inactivity_timeout_minutes: int | None = None,
    notify_previous_device: bool = True,
    terminate_previous_on_new_login: bool = True,
    enforce_geo_restriction: bool = False,
    allowed_geo: dict[str, Any] | None = None,
    enforce_ip_restriction: bool = False,
    allowed_ips: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_niam_db),
    _: None = Depends(_require_policy_admin),
):
    service = SessionGovernanceService(db)
    entity = await service.create_session_policy(
        policy_id=policy_id,
        name=name,
        applies_to=applies_to,
        max_sessions=max_sessions,
        allow_concurrent=allow_concurrent,
        require_mfa=require_mfa,
        session_timeout_minutes=session_timeout_minutes,
        inactivity_timeout_minutes=inactivity_timeout_minutes,
        notify_previous_device=notify_previous_device,
        terminate_previous_on_new_login=terminate_previous_on_new_login,
        enforce_geo_restriction=enforce_geo_restriction,
        allowed_geo=allowed_geo,
        enforce_ip_restriction=enforce_ip_restriction,
        allowed_ips=allowed_ips,
    )
    await db.commit()
    return entity.to_dict()


@router.put("/session-policies/{policy_id}")
async def update_session_policy(
    policy_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_niam_db),
    _: None = Depends(_require_policy_admin),
):
    service = SessionGovernanceService(db)
    entity = await service.update_session_policy(policy_id, **body)
    if not entity:
        return {"error": "not_found"}
    await db.commit()
    return entity.to_dict()


@router.get("/travel-events/{account_id}")
async def list_travel_events(
    account_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    stmt = (
        select(ImpossibleTravelEvent)
        .where(
            ImpossibleTravelEvent.account_id == account_id,
            ImpossibleTravelEvent.is_active.is_(True),
        )
        .offset(skip)
        .limit(limit)
        .order_by(ImpossibleTravelEvent.created_at.desc())
    )
    result = await db.execute(stmt)
    events = list(result.scalars().all())
    return [e.to_dict() for e in events]


@router.get("/active-sessions/{account_id}")
async def get_active_session_count(
    account_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    service = SessionGovernanceService(db)
    count = await service.get_active_session_count(account_id)
    return {"account_id": account_id, "active_sessions": count}


@router.post("/detect-new-device")
async def detect_new_device(
    account_id: str,
    device_fingerprint: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    service = AdaptiveAuthService(db)
    is_new = await service.detect_new_device(account_id, device_fingerprint)
    await db.commit()
    return {"is_new_device": is_new}


@router.post("/enforce-session-policy")
async def enforce_session_policy(
    account_id: str,
    account_type: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    _require_self(actor, account_id)
    service = SessionGovernanceService(db)
    result = await service.enforce_session_policy(
        account_id=account_id,
        account_type=account_type,
    )
    await db.commit()
    return result


@router.post("/check-session-expiry")
async def check_session_expiry(
    db: AsyncSession = Depends(get_niam_db),
):
    # Global maintenance sweep, not account-scoped -- out of this fix's
    # ownership-check scope (nothing to "own"), but any authenticated NIAM
    # actor can currently trigger it. Documented as a separate, pre-existing
    # finding in the batch report; not touched here per the same
    # no-invented-capability discipline as _POLICY_AUTHORITY_UNAVAILABLE.
    service = SessionGovernanceService(db)
    expired_count = await service.check_session_expiry()
    await db.commit()
    return {"expired_sessions": expired_count}


@router.get("/session-valid/{session_id}")
async def is_session_valid(
    session_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    # is_session_valid takes no account_id -- resolve the target session's
    # owning account first so a client can never probe another account's
    # session validity merely by guessing/obtaining its session_id.
    existing = (
        await db.execute(
            select(UserSession).where(UserSession.id == session_id),
        )
    ).scalar_one_or_none()
    if existing is not None:
        _require_self(actor, existing.account_id)
    service = SessionGovernanceService(db)
    valid = await service.is_session_valid(session_id)
    return {"valid": valid}
