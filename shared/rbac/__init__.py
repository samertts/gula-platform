from .permissions import (
    RBACMatrix,
    Role,
    Permission,
    has_permission,
    require_permission,
    # Extended string-based API (backend-compatible)
    EXTENDED_ROLE_LEVELS,
    EXTENDED_ALL_PERMISSIONS,
    EXTENDED_ROLE_PERMISSIONS,
    EXTENDED_VALID_ROLES,
    get_role_level,
    get_permissions_for_role,
    has_permission_str,
    can_manage_role,
)

__all__ = [
    "RBACMatrix",
    "Role",
    "Permission",
    "has_permission",
    "require_permission",
    "EXTENDED_ROLE_LEVELS",
    "EXTENDED_ALL_PERMISSIONS",
    "EXTENDED_ROLE_PERMISSIONS",
    "EXTENDED_VALID_ROLES",
    "get_role_level",
    "get_permissions_for_role",
    "has_permission_str",
    "can_manage_role",
]
