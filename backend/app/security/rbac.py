"""Role-based access control for GULA platform.

Hierarchy (higher level = more authority):
  master_admin   100  — Platform owner, full control
  ministry_admin  90  — Ministry of Health, national oversight
  province_admin  80  — Province health authority
  admin           50  — Lab manager (own lab only)
  lab_admin       50  — alias for admin
  doctor          40  — Physician (read-only clinical)
  staff           20  — Lab staff
  lab_staff       20  — alias for staff
  technician      20  — Lab technician
  citizen         10  — Patient / public user

Rule: a user can only create, modify, or deactivate users whose role_level
is STRICTLY LESS than their own.  Master admin may not be modified by anyone
except themselves (see can_manage_user).
"""

# ── Role levels (authoritative) ───────────────────────────────────────────────
ROLE_LEVELS: dict[str, int] = {
    "master_admin":   100,
    "ministry_admin":  90,
    "province_admin":  80,
    "admin":           50,
    "lab_admin":       50,   # legacy alias
    "doctor":          40,
    "staff":           20,
    "lab_staff":       20,   # legacy alias
    "technician":      20,
    "citizen":         10,
}

# ── Granular permission catalogue ────────────────────────────────────────────
ALL_PERMISSIONS: list[str] = [
    # Patients
    "patients:read",
    "patients:write",
    "patients:delete",
    # Orders
    "orders:read",
    "orders:write",
    # Results
    "results:read",
    "results:write",
    # Staff management (within a lab)
    "staff:manage",
    # Lab settings
    "lab:read",
    "lab:manage",
    # Dashboard
    "dashboard:read",
    # Audit logs
    "audit:read",
    # Platform-level management (ministry/province admins)
    "platform:manage_labs",    # create/activate/deactivate labs
    "platform:manage_users",   # create/modify users below own level
    "platform:view_stats",     # national/province statistics
    # System-level (master_admin only)
    "system:admin",
]

# ── Role → permissions mapping ────────────────────────────────────────────────
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "master_admin": ALL_PERMISSIONS,

    "ministry_admin": [
        "patients:read",
        "orders:read",
        "results:read",
        "lab:read",
        "dashboard:read",
        "audit:read",
        "platform:manage_labs",
        "platform:manage_users",
        "platform:view_stats",
    ],

    "province_admin": [
        "patients:read",
        "orders:read",
        "results:read",
        "lab:read",
        "dashboard:read",
        "audit:read",
        "platform:manage_labs",
        "platform:manage_users",
        "platform:view_stats",
    ],

    # Lab-level administrator (lab manager)
    "admin": [
        "patients:read", "patients:write", "patients:delete",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "staff:manage",
        "lab:read", "lab:manage",
        "dashboard:read",
        "audit:read",
        "platform:manage_users",
    ],
    "lab_admin": [  # legacy alias → same as admin
        "patients:read", "patients:write", "patients:delete",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "staff:manage",
        "lab:read", "lab:manage",
        "dashboard:read",
        "audit:read",
        "platform:manage_users",
    ],

    "doctor": [
        "patients:read",
        "orders:read",
        "results:read",
        "dashboard:read",
    ],

    "staff": [
        "patients:read", "patients:write",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "lab:read",
        "dashboard:read",
    ],
    "lab_staff": [  # legacy alias → same as staff
        "patients:read", "patients:write",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "lab:read",
        "dashboard:read",
    ],

    "technician": [
        "orders:read", "orders:write",
        "results:read", "results:write",
        "lab:read",
        "dashboard:read",
    ],

    "citizen": [],
}

VALID_ROLES: set[str] = set(ROLE_PERMISSIONS.keys())


def get_role_level(role: str) -> int:
    """Return numeric level for a role (0 if unknown)."""
    return ROLE_LEVELS.get(role, 0)


def get_permissions_for_role(role: str) -> list[str]:
    """Return the permission list for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: str, permission: str) -> bool:
    """Return True if *role* has *permission*."""
    return permission in get_permissions_for_role(role)


def can_manage_role(actor_role: str, target_role: str) -> bool:
    """Return True if actor can create/modify a user with target_role.

    Rules:
    - Actor level must be STRICTLY GREATER than target level.
    - master_admin cannot be created or modified by anyone except another
      master_admin (and there is only one — enforced in ensure_master_admin).
    """
    if target_role == "master_admin":
        return actor_role == "master_admin"
    actor_level = get_role_level(actor_role)
    target_level = get_role_level(target_role)
    return actor_level > target_level and actor_level > 0


def can_manage_user(actor, target_user) -> bool:
    """Return True if actor LabUser can manage target LabUser.

    Extra rule: province_admin can only manage users in their own province.
    """
    if not can_manage_role(actor.role, target_user.role):
        return False
    if actor.role == "province_admin":
        return actor.province_id == target_user.province_id
    return True


# ── Legacy helpers (kept for backward compatibility) ──────────────────────────
ROLES = ROLE_PERMISSIONS  # alias


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
    """
    Enforce lab isolation: a user can only access resources in their own lab,
    unless they are a platform-level admin (master_admin, ministry_admin, province_admin).

    Usage in routes:
        require_own_lab(current_user, patient.lab_id)
    """
    from fastapi import HTTPException

    platform_roles = {"master_admin", "ministry_admin", "province_admin"}
    if current_user.role in platform_roles:
        # Province admins: additional province check handled separately
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
    """
    Combined ABAC + tier check.
    Raises 403 if lab does not have access to feature.
    Wraps feature_flags.require_feature for convenience.

    Usage:
        require_feature_for_lab("ai_interpretation", current_user.lab_id, db)
    """
    from ..core.feature_flags import require_feature
    require_feature(feature, lab_id, db)


def assert_lab_within_limit(limit_field: str, current_count: int, lab_id: int, db) -> None:
    """
    Check resource limits defined in the lab's subscription.
    Raises 402 (Payment Required) if limit is exceeded.

    limit_field: 'max_patients' | 'max_staff' | 'max_orders_per_day' etc.
    """
    from fastapi import HTTPException
    from ..models.subscription import LabSubscription

    sub = db.query(LabSubscription).filter(
        LabSubscription.lab_id == lab_id,
        LabSubscription.is_active == True,
    ).first()

    if sub is None:
        # No subscription row → default starter limits
        from ..core.feature_flags import get_tier_limits
        limits = get_tier_limits("starter")
    else:
        limits = {
            "max_patients":        sub.max_patients,
            "max_staff":           sub.max_staff,
            "max_branches":        sub.max_branches,
            "max_orders_per_day":  sub.max_orders_per_day,
            "max_ai_calls_per_day":sub.max_ai_calls_per_day,
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
