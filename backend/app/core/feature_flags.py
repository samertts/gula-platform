"""GULA Platform — Feature Flags & Tier Enforcement
=================================================
Server-side only. Never rely on frontend feature visibility.

Tier Matrix (source of truth):
┌─────────────────────────┬─────────┬────────┬────────────┐
│ Feature                 │ starter │ growth │ enterprise │
├─────────────────────────┼─────────┼────────┼────────────┤
│ patient_management      │   ✓     │   ✓    │     ✓      │
│ basic_results           │   ✓     │   ✓    │     ✓      │
│ sample_tracking         │   ✓     │   ✓    │     ✓      │
│ pdf_reports             │   ✓     │   ✓    │     ✓      │
│ qr_codes                │   ✓     │   ✓    │     ✓      │
│ quality_control         │         │   ✓    │     ✓      │
│ batch_import            │         │   ✓    │     ✓      │
│ ehr_integration         │         │   ✓    │     ✓      │
│ advanced_analytics      │         │   ✓    │     ✓      │
│ multi_branch            │         │        │     ✓      │
│ government_reporting    │         │        │     ✓      │
│ ai_interpretation       │         │        │     ✓      │
│ ai_anomaly_detection    │         │        │     ✓      │
│ custom_branding         │         │        │     ✓      │
│ api_access              │         │        │     ✓      │
│ sla_guarantee           │         │        │     ✓      │
├─────────────────────────┴─────────┴────────┴────────────┤
│ Deployment Mode Overrides:                               │
│   government → government_reporting always enabled       │
│   multi_branch → multi_branch always enabled             │
│ Security Level Overrides:                                │
│   high_security → audit_chain, 2FA required             │
│   air_gapped    → all external APIs disabled            │
└─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC

logger = logging.getLogger("gula.features")

# ── Tier definitions ─────────────────────────────────────────────────────────

_TIER_FEATURES: dict[str, frozenset[str]] = {
    "starter": frozenset(
        {
            "patient_management",
            "basic_results",
            "sample_tracking",
            "pdf_reports",
            "qr_codes",
            "notifications",
            "audit_log",
            "mobile_access",
        },
    ),
    "growth": frozenset(
        {
            "patient_management",
            "basic_results",
            "sample_tracking",
            "pdf_reports",
            "qr_codes",
            "notifications",
            "audit_log",
            "mobile_access",
            # growth additions
            "quality_control",
            "batch_import",
            "batch_export",
            "ehr_integration",
            "advanced_analytics",
            "critical_alerts",
            "insurance_integration",
            "national_id_lookup",
            "device_results",
        },
    ),
    "enterprise": frozenset(
        {
            "patient_management",
            "basic_results",
            "sample_tracking",
            "pdf_reports",
            "qr_codes",
            "notifications",
            "audit_log",
            "mobile_access",
            "quality_control",
            "batch_import",
            "batch_export",
            "ehr_integration",
            "advanced_analytics",
            "critical_alerts",
            "insurance_integration",
            "national_id_lookup",
            "device_results",
            # enterprise additions
            "multi_branch",
            "government_reporting",
            "ai_interpretation",
            "ai_anomaly_detection",
            "ai_epidemiology",
            "custom_branding",
            "api_access",
            "sla_guarantee",
            "white_label",
            "priority_support",
        },
    ),
}

# ── Deployment mode overrides ────────────────────────────────────────────────
_DEPLOYMENT_EXTRAS: dict[str, frozenset[str]] = {
    "single": frozenset(),
    "multi_branch": frozenset({"multi_branch", "cross_branch_reports"}),
    "government": frozenset(
        {"government_reporting", "compliance_dashboard", "ministry_integration"},
    ),
}

# ── Security level overrides ─────────────────────────────────────────────────
_SECURITY_EXTRAS: dict[str, frozenset[str]] = {
    "standard": frozenset(),
    "high_security": frozenset({"two_factor_required", "audit_chain", "session_timeout_short"}),
    "air_gapped": frozenset(
        {"two_factor_required", "audit_chain", "session_timeout_short", "air_gapped_mode"},
    ),
}

# Features blocked in air-gapped mode (no external calls)
_AIR_GAPPED_BLOCKED: frozenset[str] = frozenset(
    {
        "ai_interpretation",
        "ai_anomaly_detection",
        "ai_epidemiology",
        "ehr_integration",
        "insurance_integration",
        "national_id_lookup",
        "ministry_integration",
        "notifications",  # external push notifications
    },
)

# Tier ordering for upgrade validation
_TIER_ORDER = {"starter": 0, "growth": 1, "enterprise": 2}
_VALID_TIERS = frozenset(_TIER_ORDER.keys())
_VALID_DEPLOYMENTS = frozenset({"single", "multi_branch", "government"})
_VALID_SECURITY = frozenset({"standard", "high_security", "air_gapped"})


def get_tier_features(
    tier: str, deployment_mode: str = "single", security_level: str = "standard",
) -> frozenset[str]:
    """Return the full feature set for a given (tier, deployment_mode, security_level) combo.
    Applies deployment and security overrides on top of tier base.
    Air-gapped mode blocks external-API features regardless of tier.
    """
    base = _TIER_FEATURES.get(tier, _TIER_FEATURES["starter"])
    deployment_bonus = _DEPLOYMENT_EXTRAS.get(deployment_mode, frozenset())
    security_bonus = _SECURITY_EXTRAS.get(security_level, frozenset())

    features = base | deployment_bonus | security_bonus

    # Air-gapped: remove all external-dependency features
    if security_level == "air_gapped":
        features = features - _AIR_GAPPED_BLOCKED

    return features


def resolve_lab_features(lab_id: int, db: Session) -> frozenset[str]:
    """Load a lab's effective feature set from DB, applying:
      1. Tier base features
      2. Deployment / security overrides
      3. Per-lab FeatureFlag overrides (can add OR remove features)
      4. Expiry check on per-lab flags

    This is the authoritative check — call this in every route that gates features.
    Result is NOT cached here; cache in Redis at the route level if needed.
    """
    from ..models.subscription import FeatureFlag, LabSubscription

    sub = (
        db.query(LabSubscription)
        .filter(
            LabSubscription.lab_id == lab_id,
            LabSubscription.is_active,
        )
        .first()
    )

    if sub is None:
        # No subscription → default to starter/single/standard
        tier, deployment, security = "starter", "single", "standard"
    else:
        tier = sub.tier or "starter"
        deployment = sub.deployment_mode or "single"
        security = sub.security_level or "standard"

    features = set(get_tier_features(tier, deployment, security))

    # Apply per-lab FeatureFlag overrides
    now = datetime.now(UTC)
    flags = db.query(FeatureFlag).filter(FeatureFlag.lab_id == lab_id).all()
    for flag in flags:
        # Skip expired flags
        if flag.expires_at and flag.expires_at < now:
            continue
        if flag.is_enabled:
            features.add(flag.feature_key)
        else:
            features.discard(flag.feature_key)

    return frozenset(features)


def require_feature(feature: str, lab_id: int, db: Session) -> None:
    """Raise HTTP 403 if the lab does not have access to `feature`.
    Import this in route handlers for server-side enforcement.

    Usage:
        require_feature("ai_interpretation", current_user.lab_id, db)
    """
    from fastapi import HTTPException

    features = resolve_lab_features(lab_id, db)
    if feature not in features:
        logger.warning(
            "[FEATURE GATE] lab_id=%s blocked from feature '%s' (not in tier)",
            lab_id,
            feature,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_not_available",
                "feature": feature,
                "message": f"This feature ({feature}) is not available in your current plan.",
                "message_ar": f"هذه الميزة ({feature}) غير متاحة في خطتك الحالية.",
                "upgrade_hint": "Please upgrade your subscription to access this feature.",
                "upgrade_hint_ar": "يرجى ترقية اشتراكك للوصول إلى هذه الميزة.",
            },
        )


def can_lab_access(feature: str, lab_id: int, db: Session) -> bool:
    """Non-raising version — returns True/False. Use in conditional logic."""
    return feature in resolve_lab_features(lab_id, db)


def get_lab_subscription_info(lab_id: int, db: Session) -> dict[str, object]:
    """Return subscription summary for a lab — used in dashboard and API responses.
    """
    from ..models.subscription import LabSubscription

    sub = (
        db.query(LabSubscription)
        .filter(
            LabSubscription.lab_id == lab_id,
            LabSubscription.is_active,
        )
        .first()
    )

    if sub is None:
        return {
            "tier": "starter",
            "deployment_mode": "single",
            "security_level": "standard",
            "is_trial": False,
            "features": sorted(get_tier_features("starter")),
        }

    features = resolve_lab_features(lab_id, db)
    now = datetime.now(UTC)
    is_trial = bool(sub.trial_ends_at and sub.trial_ends_at > now)

    return {
        "tier": sub.tier,
        "deployment_mode": sub.deployment_mode,
        "security_level": sub.security_level,
        "is_trial": is_trial,
        "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
        "billing_cycle": sub.billing_cycle,
        "max_patients": sub.max_patients,
        "max_staff": sub.max_staff,
        "max_branches": sub.max_branches,
        "max_orders_per_day": sub.max_orders_per_day,
        "max_ai_calls_per_day": sub.max_ai_calls_per_day,
        "features": sorted(features),
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    }


def is_upgrade_valid(current_tier: str, target_tier: str) -> bool:
    """Return True only if target_tier is strictly higher than current_tier.
    Downgrades must go through admin approval flow (data implications).
    """
    return (
        current_tier in _TIER_ORDER
        and target_tier in _TIER_ORDER
        and _TIER_ORDER[target_tier] > _TIER_ORDER[current_tier]
    )


def get_tier_limits(tier: str) -> dict[str, int]:
    """Return the default resource limits for a tier."""
    limits = {
        "starter": {
            "max_patients": 500,
            "max_staff": 5,
            "max_branches": 1,
            "max_orders_per_day": 100,
            "max_ai_calls_per_day": 0,
        },
        "growth": {
            "max_patients": 5000,
            "max_staff": 20,
            "max_branches": 1,
            "max_orders_per_day": 1000,
            "max_ai_calls_per_day": 0,
        },
        "enterprise": {
            "max_patients": 99999,
            "max_staff": 999,
            "max_branches": 50,
            "max_orders_per_day": 99999,
            "max_ai_calls_per_day": 500,
        },
    }
    return limits.get(tier, limits["starter"])
