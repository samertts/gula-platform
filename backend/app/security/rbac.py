"""Role-based access control for GULA platform."""

# ── Granular permission catalogue ────────────────────────────────────────────
# Each key is the canonical permission string used in require_permission().
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
    # System-level (master_admin only)
    "system:admin",
]

# ── Role → permissions mapping ────────────────────────────────────────────────
# master_admin receives ALL permissions automatically (see get_permissions_for_role).
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "master_admin": ALL_PERMISSIONS,
    # Lab-level administrator
    "admin": [
        "patients:read", "patients:write", "patients:delete",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "staff:manage",
        "lab:read", "lab:manage",
        "dashboard:read",
        "audit:read",
    ],
    "lab_admin": [  # legacy alias → same as admin
        "patients:read", "patients:write", "patients:delete",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "staff:manage",
        "lab:read", "lab:manage",
        "dashboard:read",
        "audit:read",
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
    "doctor": [
        "patients:read",
        "orders:read",
        "results:read",
    ],
    "citizen": [],
}

VALID_ROLES: set[str] = set(ROLE_PERMISSIONS.keys())


def get_permissions_for_role(role: str) -> list[str]:
    """Return the permission list for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: str, permission: str) -> bool:
    """Return True if *role* has *permission*."""
    return permission in get_permissions_for_role(role)


# ── Legacy helpers (kept for backward compatibility) ──────────────────────────
# Old code used ROLES["master_admin"] == ["all"]; map that to the new structure.
ROLES = ROLE_PERMISSIONS  # alias


def require_role(*allowed_roles):
    """FastAPI dependency: require the user to have one of the listed roles.

    Prefer require_permission() for new code.
    """
    from fastapi import Depends, HTTPException
    from .dependencies import get_current_user

    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return checker
