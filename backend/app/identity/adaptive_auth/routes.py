from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from .models import ImpossibleTravelEvent, RiskPolicy, SessionPolicy
from .services import AdaptiveAuthService, SessionGovernanceService

router = APIRouter(prefix="/niam/adaptive-auth", tags=["NIAM Adaptive Auth"])


@router.post("/evaluate")
async def evaluate_risk(
    account_id: str,
    ip_address: str,
    user_agent: str = "",
    location: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AdaptiveAuthService(db)
    result = await service.evaluate_risk(
        account_id=account_id,
        ip_address=ip_address,
        user_agent=user_agent,
        location=location,
    )
    mitigation = await service.apply_mitigation(result["risk_score"], account_id)
    return {"risk_assessment": result, "mitigation": mitigation}


@router.get("/risk-history/{account_id}")
async def get_risk_history(
    account_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = AdaptiveAuthService(db)
    events = await service.get_risk_history(account_id, limit=limit)
    return [e.to_dict() for e in events]


@router.post("/mfa/challenge")
async def create_mfa_challenge(
    account_id: str,
    mfa_type: str = "totp",
    db: AsyncSession = Depends(get_db),
):
    service = AdaptiveAuthService(db)
    mfa = await service.create_mfa_challenge(account_id=account_id, mfa_type=mfa_type)
    return {
        "mfa_id": mfa.mfa_id,
        "mfa_type": mfa.mfa_type,
        "expires_at": mfa.challenge_expires_at.isoformat(),
    }


@router.post("/mfa/verify")
async def verify_mfa_challenge(
    mfa_id: str,
    challenge_response: str,
    db: AsyncSession = Depends(get_db),
):
    service = AdaptiveAuthService(db)
    result = await service.verify_mfa(mfa_id=mfa_id, challenge_response=challenge_response)
    return result


@router.get("/policies")
async def list_risk_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

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
    db: AsyncSession = Depends(get_db),
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
    return entity.to_dict()


@router.post("/policies/{policy_id}")
async def update_risk_policy(
    policy_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

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
    return entity.to_dict()


@router.get("/session-policies")
async def list_session_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

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
    db: AsyncSession = Depends(get_db),
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
    return entity.to_dict()


@router.put("/session-policies/{policy_id}")
async def update_session_policy(
    policy_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    service = SessionGovernanceService(db)
    entity = await service.update_session_policy(policy_id, **body)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.get("/travel-events/{account_id}")
async def list_travel_events(
    account_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

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
    db: AsyncSession = Depends(get_db),
):
    service = SessionGovernanceService(db)
    count = await service.get_active_session_count(account_id)
    return {"account_id": account_id, "active_sessions": count}


@router.post("/detect-new-device")
async def detect_new_device(
    account_id: str,
    device_fingerprint: str,
    db: AsyncSession = Depends(get_db),
):
    service = AdaptiveAuthService(db)
    is_new = await service.detect_new_device(account_id, device_fingerprint)
    return {"is_new_device": is_new}


@router.post("/enforce-session-policy")
async def enforce_session_policy(
    account_id: str,
    account_type: str,
    db: AsyncSession = Depends(get_db),
):
    service = SessionGovernanceService(db)
    result = await service.enforce_session_policy(
        account_id=account_id,
        account_type=account_type,
    )
    return result


@router.post("/check-session-expiry")
async def check_session_expiry(
    db: AsyncSession = Depends(get_db),
):
    service = SessionGovernanceService(db)
    expired_count = await service.check_session_expiry()
    return {"expired_sessions": expired_count}


@router.get("/session-valid/{session_id}")
async def is_session_valid(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = SessionGovernanceService(db)
    valid = await service.is_session_valid(session_id)
    return {"valid": valid}
