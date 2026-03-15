"""Role-based access control for GULA platform."""

# Role permissions matrix
ROLES = {
    "master_admin": ["all"],
    "lab_admin": ["lab:manage", "lab:read", "patient:read", "patient:write", "order:read", "order:write", "result:read", "result:write", "staff:manage", "dashboard:read"],
    "lab_staff": ["patient:read", "patient:write", "order:read", "order:write", "result:read", "result:write", "dashboard:read"],
    "doctor": ["patient:read", "order:read", "result:read", "history:read"],
    "citizen": ["self:read", "self:results"],
}

VALID_ROLES = set(ROLES.keys())


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    role_perms = ROLES.get(role, [])
    if "all" in role_perms:
        return True
    return permission in role_perms


def require_role(*allowed_roles):
    """FastAPI dependency to require specific roles."""
    from fastapi import Depends, HTTPException
    from .dependencies import get_current_user

    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return checker
