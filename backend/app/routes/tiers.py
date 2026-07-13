"""
GULA Platform — Subscription Tier Management API
=================================================
Endpoints:
  GET  /tiers                       — list all available tiers and features
  GET  /tiers/my                    — current lab's subscription info
  POST /tiers/upgrade               — request an upgrade (admin initiates)
  GET  /tiers/upgrade-requests      — list upgrade requests for my lab
  POST /tiers/upgrade-demand        — citizen requests lab upgrade (demand signal)
  GET  /admin/tiers/demands         — platform admin: top upgrade demand labs
  PUT  /admin/tiers/{lab_id}        — platform admin: manually set tier
  POST /admin/tiers/flags/{lab_id}  — platform admin: set/remove feature flag
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..core.feature_flags import (
    _VALID_DEPLOYMENTS,
    _VALID_SECURITY,
    _VALID_TIERS,
    get_lab_subscription_info,
    get_tier_features,
    get_tier_limits,
    is_upgrade_valid,
)
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.subscription import FeatureFlag, LabSubscription, UpgradeDemandScore, UpgradeRequest
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip
from ..services.audit_service import log_action

logger = logging.getLogger("gula.tiers")
router = APIRouter(tags=["subscription"])


# ─── Tier Catalog (public) ────────────────────────────────────────────────────


@router.get("/tiers", summary="List available tiers and feature matrix")
def list_tiers():
    """
    Public endpoint — returns the full tier matrix so the frontend can render
    the pricing/feature comparison table without an auth token.
    """
    tiers = []
    for tier in ("starter", "growth", "enterprise"):
        limits = get_tier_limits(tier)
        features = sorted(get_tier_features(tier))
        tiers.append(
            {
                "id": tier,
                "name": {
                    "starter": "Starter",
                    "growth": "Growth",
                    "enterprise": "Enterprise",
                }[tier],
                "name_ar": {
                    "starter": "البداية",
                    "growth": "النمو",
                    "enterprise": "المؤسسات",
                }[tier],
                "monthly_price_usd": {"starter": 0, "growth": 49, "enterprise": 199}[tier],
                "limits": limits,
                "features": features,
            }
        )
    return {"tiers": tiers}


# ─── My Subscription ─────────────────────────────────────────────────────────


@router.get("/tiers/my", summary="Current lab subscription info")
def my_subscription(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the calling lab's full subscription state, feature set, and limits."""
    if not current_user.lab_id:
        raise HTTPException(status_code=400, detail="No lab associated with this account")
    return get_lab_subscription_info(current_user.lab_id, db)


# ─── Upgrade Request (lab admin) ─────────────────────────────────────────────


class UpgradeRequestBody(BaseModel):
    target_tier: str
    target_deployment_mode: str | None = None
    target_security_level: str | None = None
    reason: str | None = None

    @field_validator("target_tier")
    @classmethod
    def validate_tier(cls, v):
        if v not in _VALID_TIERS:
            raise ValueError(f"Invalid tier. Must be one of: {', '.join(sorted(_VALID_TIERS))}")
        return v

    @field_validator("target_deployment_mode")
    @classmethod
    def validate_deployment(cls, v):
        if v and v not in _VALID_DEPLOYMENTS:
            raise ValueError(
                f"Invalid deployment_mode. Must be one of: {', '.join(sorted(_VALID_DEPLOYMENTS))}"
            )
        return v

    @field_validator("target_security_level")
    @classmethod
    def validate_security(cls, v):
        if v and v not in _VALID_SECURITY:
            raise ValueError(
                f"Invalid security_level. Must be one of: {', '.join(sorted(_VALID_SECURITY))}"
            )
        return v


@router.post("/tiers/upgrade", status_code=201, summary="Lab admin requests tier upgrade")
def request_upgrade(
    body: UpgradeRequestBody,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lab admin submits an upgrade request.
    The request is queued for platform admin approval.
    """
    if current_user.role not in ("admin", "lab_admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Only lab admins can request upgrades")

    if not current_user.lab_id:
        raise HTTPException(status_code=400, detail="No lab associated with this account")

    # Check current tier — validate it's actually an upgrade
    sub = db.query(LabSubscription).filter(LabSubscription.lab_id == current_user.lab_id).first()
    current_tier = sub.tier if sub else "starter"

    if body.target_tier == current_tier:
        raise HTTPException(status_code=400, detail="Lab is already on this tier")
    if not is_upgrade_valid(current_tier, body.target_tier):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upgrade from '{current_tier}' to '{body.target_tier}'. Contact support for downgrade requests.",
        )

    upgrade_req = UpgradeRequest(
        lab_id=current_user.lab_id,
        requester_id=None,  # lab admin, not citizen
        target_tier=body.target_tier,
        target_deployment_mode=body.target_deployment_mode,
        target_security_level=body.target_security_level,
        reason=body.reason or "",
        status="pending",
        weight=2.0,  # lab-admin requests carry higher weight than citizen requests
    )
    db.add(upgrade_req)

    _update_demand_score(current_user.lab_id, db)

    log_action(
        db,
        action="upgrade_request",
        resource_type="subscription",
        resource_id=current_user.lab_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Upgrade request: {current_tier}→{body.target_tier}",
        ip_address=get_client_ip(request),
    )
    db.commit()
    db.refresh(upgrade_req)

    return {
        "message": "Upgrade request submitted successfully. A platform admin will review it.",
        "message_ar": "تم تقديم طلب الترقية بنجاح. سيتم مراجعته من قبل مسؤول المنصة.",
        "request_id": upgrade_req.id,
        "status": "pending",
    }


# ─── Citizen Demand Signal ───────────────────────────────────────────────────


class DemandSignalBody(BaseModel):
    lab_id: int
    target_tier: str
    reason: str | None = None

    @field_validator("target_tier")
    @classmethod
    def validate_tier(cls, v):
        if v not in _VALID_TIERS:
            raise ValueError(f"Invalid tier: {v}")
        return v


@router.post(
    "/tiers/upgrade-demand", status_code=201, summary="Citizen signals demand for lab upgrade"
)
def submit_upgrade_demand(
    body: DemandSignalBody,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verified citizens can signal demand for a lab to upgrade.
    Weight = 1.0 for verified citizens (is_verified=True), 0.3 for unverified.
    Rate-limited: 1 request per lab per user per 30 days.
    """
    # Verify the lab exists
    lab = db.query(Lab).filter(Lab.id == body.lab_id, Lab.is_active).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    # Rate limit: has this user already requested this lab in the last 30 days?
    recent = (
        db.query(UpgradeRequest)
        .filter(
            UpgradeRequest.lab_id == body.lab_id,
            UpgradeRequest.requester_id == current_user.id,
            UpgradeRequest.created_at >= datetime.now(UTC).replace(day=1),
        )
        .first()
    )
    if recent:
        raise HTTPException(
            status_code=429,
            detail="You have already submitted a demand request for this lab this month.",
        )

    # Weight: verified citizen = 1.0, unverified = 0.3, lab staff = 0
    weight = 0.0
    if hasattr(current_user, "is_verified"):
        weight = 1.0 if current_user.is_verified else 0.3
    elif hasattr(current_user, "role") and current_user.role == "citizen":
        weight = 0.5
    else:
        # Lab staff cannot submit citizen demand signals
        raise HTTPException(status_code=403, detail="Only citizens can submit demand signals")

    demand = UpgradeRequest(
        lab_id=body.lab_id,
        requester_id=current_user.id,
        target_tier=body.target_tier,
        reason=body.reason or "",
        status="pending",
        weight=weight,
    )
    db.add(demand)
    _update_demand_score(body.lab_id, db)

    log_action(
        db,
        action="upgrade_demand",
        resource_type="subscription",
        resource_id=body.lab_id,
        user_id=current_user.id,
        user_role=getattr(current_user, "role", "citizen"),
        details=f"Citizen demand for {body.target_tier} (weight={weight})",
        ip_address=get_client_ip(request),
    )
    db.commit()

    return {
        "message": "Your request has been recorded. Thank you for helping improve lab services.",
        "message_ar": "تم تسجيل طلبك. شكراً لمساهمتك في تحسين خدمات المختبرات.",
        "weight": weight,
    }


# ─── Platform Admin: View Demands ────────────────────────────────────────────


@router.get("/admin/tiers/demands", summary="Platform admin: top upgrade demand labs")
def list_upgrade_demands(
    limit: int = 20,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns labs sorted by weighted upgrade demand score (highest first)."""
    if current_user.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Platform admin access required")

    scores = (
        db.query(UpgradeDemandScore)
        .order_by(UpgradeDemandScore.weighted_score.desc())
        .limit(limit)
        .all()
    )
    result = []
    for s in scores:
        lab = db.query(Lab).filter(Lab.id == s.lab_id).first()
        sub = db.query(LabSubscription).filter(LabSubscription.lab_id == s.lab_id).first()
        result.append(
            {
                "lab_id": s.lab_id,
                "lab_name": lab.name if lab else "Unknown",
                "current_tier": sub.tier if sub else "starter",
                "weighted_score": round(s.weighted_score, 2),
                "unique_requesters": s.unique_requesters,
                "last_request_at": s.last_request_at.isoformat() if s.last_request_at else None,
            }
        )
    return {"demands": result}


# ─── Platform Admin: Set Tier ────────────────────────────────────────────────


class SetTierBody(BaseModel):
    tier: str
    deployment_mode: str = "single"
    security_level: str = "standard"
    billing_cycle: str = "monthly"
    notes: str | None = None

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v):
        if v not in _VALID_TIERS:
            raise ValueError(f"Invalid tier: {v}")
        return v

    @field_validator("deployment_mode")
    @classmethod
    def validate_deployment(cls, v):
        if v not in _VALID_DEPLOYMENTS:
            raise ValueError(f"Invalid deployment_mode: {v}")
        return v

    @field_validator("security_level")
    @classmethod
    def validate_security(cls, v):
        if v not in _VALID_SECURITY:
            raise ValueError(f"Invalid security_level: {v}")
        return v


@router.put("/admin/tiers/{lab_id}", summary="Platform admin: set lab tier")
def set_lab_tier(
    lab_id: int,
    body: SetTierBody,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Platform admin manually sets the tier for a lab."""
    if current_user.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Platform admin access required")

    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    sub = db.query(LabSubscription).filter(LabSubscription.lab_id == lab_id).first()
    limits = get_tier_limits(body.tier)

    if sub:
        sub.tier = body.tier
        sub.deployment_mode = body.deployment_mode
        sub.security_level = body.security_level
        sub.billing_cycle = body.billing_cycle
        sub.notes = body.notes
        sub.max_patients = limits["max_patients"]
        sub.max_staff = limits["max_staff"]
        sub.max_branches = limits["max_branches"]
        sub.max_orders_per_day = limits["max_orders_per_day"]
        sub.max_ai_calls_per_day = limits["max_ai_calls_per_day"]
        sub.updated_at = datetime.now(UTC)
    else:
        sub = LabSubscription(
            lab_id=lab_id,
            tier=body.tier,
            deployment_mode=body.deployment_mode,
            security_level=body.security_level,
            billing_cycle=body.billing_cycle,
            notes=body.notes,
            **limits,
        )
        db.add(sub)

    # Mark any pending upgrade requests for this lab as fulfilled
    db.query(UpgradeRequest).filter(
        UpgradeRequest.lab_id == lab_id,
        UpgradeRequest.status == "pending",
    ).update(
        {
            "status": "fulfilled",
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.now(UTC),
            "review_note": f"Tier set to {body.tier} by platform admin",
        }
    )

    log_action(
        db,
        action="set_tier",
        resource_type="subscription",
        resource_id=lab_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Tier set: {body.tier} / {body.deployment_mode} / {body.security_level}",
        ip_address=get_client_ip(request),
    )
    db.commit()

    return {
        "message": f"Lab {lab_id} tier updated to {body.tier}",
        "tier": body.tier,
        "deployment_mode": body.deployment_mode,
        "security_level": body.security_level,
        "limits": limits,
    }


# ─── Platform Admin: Feature Flag Override ───────────────────────────────────


class FeatureFlagBody(BaseModel):
    feature_key: str
    is_enabled: bool
    reason: str | None = None
    expires_at: str | None = None  # ISO datetime string or None


@router.post("/admin/tiers/flags/{lab_id}", status_code=201, summary="Set feature flag for a lab")
def set_feature_flag(
    lab_id: int,
    body: FeatureFlagBody,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Platform admin: enable or disable a specific feature for a lab,
    overriding tier defaults. Optionally set an expiry date for trials.
    """
    if current_user.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Platform admin access required")

    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    expires = None
    if body.expires_at:
        try:
            expires = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format (use ISO 8601)")

    # Upsert feature flag
    flag = (
        db.query(FeatureFlag)
        .filter(
            FeatureFlag.lab_id == lab_id,
            FeatureFlag.feature_key == body.feature_key,
        )
        .first()
    )

    if flag:
        flag.is_enabled = body.is_enabled
        flag.reason = body.reason
        flag.set_by = current_user.id
        flag.expires_at = expires
    else:
        flag = FeatureFlag(
            lab_id=lab_id,
            feature_key=body.feature_key,
            is_enabled=body.is_enabled,
            reason=body.reason,
            set_by=current_user.id,
            expires_at=expires,
        )
        db.add(flag)

    log_action(
        db,
        action="set_feature_flag",
        resource_type="subscription",
        resource_id=lab_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Feature flag '{body.feature_key}' = {body.is_enabled} (expires={expires})",
        ip_address=get_client_ip(request),
    )
    db.commit()

    return {
        "message": f"Feature flag '{body.feature_key}' set to {body.is_enabled} for lab {lab_id}",
        "feature_key": body.feature_key,
        "is_enabled": body.is_enabled,
        "expires_at": expires.isoformat() if expires else None,
    }


@router.get("/admin/tiers/flags/{lab_id}", summary="List feature flags for a lab")
def list_feature_flags(
    lab_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("master_admin", "ministry_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if current_user.role == "admin" and current_user.lab_id != lab_id:
        raise HTTPException(status_code=403, detail="Can only view flags for your own lab")

    flags = db.query(FeatureFlag).filter(FeatureFlag.lab_id == lab_id).all()
    return {
        "lab_id": lab_id,
        "flags": [
            {
                "feature_key": f.feature_key,
                "is_enabled": f.is_enabled,
                "reason": f.reason,
                "expires_at": f.expires_at.isoformat() if f.expires_at else None,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in flags
        ],
    }


# ─── Internal helper ─────────────────────────────────────────────────────────


def _update_demand_score(lab_id: int, db: Session) -> None:
    """
    Recalculate UpgradeDemandScore after a new request.
    Formula: weighted_score = raw_score × log2(unique_requesters + 2)
    This rewards breadth (many different users) over depth (same user spamming).
    """
    import math

    result = (
        db.query(
            func.sum(UpgradeRequest.weight).label("raw_score"),
            func.count(UpgradeRequest.requester_id.distinct()).label("unique_requesters"),
            func.max(UpgradeRequest.created_at).label("last_request_at"),
        )
        .filter(
            UpgradeRequest.lab_id == lab_id,
            UpgradeRequest.status.in_(["pending", "approved"]),
        )
        .one()
    )

    raw_score = float(result.raw_score or 0)
    unique = int(result.unique_requesters or 0)
    weighted_score = raw_score * math.log2(unique + 2)

    score = db.query(UpgradeDemandScore).filter(UpgradeDemandScore.lab_id == lab_id).first()
    if score:
        score.raw_score = raw_score
        score.unique_requesters = unique
        score.weighted_score = weighted_score
        score.last_request_at = result.last_request_at
        score.updated_at = datetime.now(UTC)
    else:
        score = UpgradeDemandScore(
            lab_id=lab_id,
            raw_score=raw_score,
            unique_requesters=unique,
            weighted_score=weighted_score,
            last_request_at=result.last_request_at,
        )
        db.add(score)


# ─── Seed default subscriptions ──────────────────────────────────────────────


def seed_default_subscriptions(db: Session) -> None:
    """
    Ensure every active lab has a LabSubscription row.
    Called during startup seeding — safe to run multiple times.
    """
    labs_without_sub = (
        db.query(Lab)
        .outerjoin(LabSubscription, Lab.id == LabSubscription.lab_id)
        .filter(LabSubscription.id is None, Lab.is_active)
        .all()
    )
    for lab in labs_without_sub:
        sub = LabSubscription(
            lab_id=lab.id,
            tier="starter",
            deployment_mode="single",
            security_level="standard",
            **get_tier_limits("starter"),
        )
        db.add(sub)

    if labs_without_sub:
        db.commit()
        logger.info("[TIERS] Seeded default subscriptions for %d labs", len(labs_without_sub))
