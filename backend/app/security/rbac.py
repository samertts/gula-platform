"""Role-based access control — canonical shared.rbac with backend extensions.

All role/permission data is defined in shared.rbac. This module re-exports
the extended string-based API for backward compatibility.

See shared/rbac/permissions.py for the canonical role hierarchy.
"""

from __future__ import annotations

from shared.rbac import (
    EXTENDED_ALL_PERMISSIONS as ALL_PERMISSIONS,
)
from shared.rbac import (
    EXTENDED_ROLE_LEVELS as ROLE_LEVELS,
)
from shared.rbac import (
    EXTENDED_ROLE_PERMISSIONS as ROLE_PERMISSIONS,
)
from shared.rbac import (
    EXTENDED_VALID_ROLES as VALID_ROLES,
)
from shared.rbac import (
    can_manage_role as _shared_can_manage_role,
)
from shared.rbac import (
    get_permissions_for_role as _shared_get_permissions,
)
from shared.rbac import (
    get_role_level as _shared_get_role_level,
)
from shared.rbac import (
    has_permission_str,
)

# ── Re-exports ─────────────────────────────────────────────────────────────────
ROLE_LEVELS = ROLE_LEVELS
ALL_PERMISSIONS = ALL_PERMISSIONS
ROLE_PERMISSIONS = ROLE_PERMISSIONS
VALID_ROLES = VALID_ROLES
ROLES = ROLE_PERMISSIONS  # legacy alias


def get_role_level(role: str) -> int:
    return _shared_get_role_level(role)


def get_permissions_for_role(role: str) -> list[str]:
    return _shared_get_permissions(role)


def has_permission(role: str, permission: str) -> bool:
    return has_permission_str(role, permission)


def can_manage_role(actor_role: str, target_role: str) -> bool:
    return _shared_can_manage_role(actor_role, target_role)


def can_manage_user(actor, target_user) -> bool:
    if not can_manage_role(actor.role, target_user.role):
        return False
    if actor.role == "province_admin":
        return actor.province_id == target_user.province_id
    if actor.role in {"master_admin", "ministry_admin"}:
        return True
    # Every other role that can reach this check (e.g. admin/lab_admin) is
    # lab-scoped: it may only manage users within its own lab. Mirrors the
    # platform_roles bypass + lab_id equality already enforced by
    # require_own_lab() below, so tenant scoping stays defined in one place.
    return getattr(actor, "lab_id", None) is not None and actor.lab_id == getattr(
        target_user, "lab_id", None
    )


def require_role(*allowed_roles):
    """FastAPI dependency: require the user to have one of the listed roles."""
    from fastapi import Depends, HTTPException

    from .dependencies import get_current_user

    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return checker


# ── ABAC: Attribute-Based Access Control ──────────────────────────────────────


def require_own_lab(current_user, resource_lab_id: int) -> None:
    from fastapi import HTTPException

    platform_roles = {"master_admin", "ministry_admin", "province_admin"}
    if current_user.role in platform_roles:
        return

    if getattr(current_user, "lab_id", None) != resource_lab_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "cross_lab_access_denied",
                "message": "You do not have permission to access resources in another laboratory.",
                "message_ar": "لا تملك صلاحية الوصول إلى موارد مختبر آخر.",
            },
        )


def require_feature_for_lab(feature: str, lab_id: int, db) -> None:
    from ..core.feature_flags import require_feature

    require_feature(feature, lab_id, db)


def assert_lab_within_limit(limit_field: str, current_count: int, lab_id: int, db) -> None:
    from fastapi import HTTPException

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
        from ..core.feature_flags import get_tier_limits

        limits = get_tier_limits("starter")
    else:
        limits = {
            "max_patients": sub.max_patients,
            "max_staff": sub.max_staff,
            "max_branches": sub.max_branches,
            "max_orders_per_day": sub.max_orders_per_day,
            "max_ai_calls_per_day": sub.max_ai_calls_per_day,
        }

    limit_value = limits.get(limit_field, 0)
    if limit_value > 0 and current_count >= limit_value:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "subscription_limit_reached",
                "limit_field": limit_field,
                "limit_value": limit_value,
                "current_count": current_count,
                "message": f"You have reached the limit of {limit_value} for {limit_field}.",
                "message_ar": f"لقد وصلت إلى الحد الأقصى ({limit_value}) لـ {limit_field}.",
                "upgrade_hint": "Upgrade your subscription to increase limits.",
                "upgrade_hint_ar": "قم بترقية اشتراكك لرفع الحدود.",
            },
        )
