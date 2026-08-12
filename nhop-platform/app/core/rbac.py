"""Lightweight role-based access control for the NHOP API.

The production auth stack (JWT-backed) lives in the GULA platform. Until
NHOP shares that identity surface, routes that need authorisation read the
caller's role from the ``X-Role`` request header — the same pattern the
citizens API already uses for ``X-Actor-Id``. This keeps restricted
endpoints testable without booting the full auth stack.

Exposed:
    :class:`Role`           - enum of known roles
    :func:`require_roles`   - FastAPI dependency factory
"""
from __future__ import annotations

import enum

from fastapi import Header, HTTPException, status


class Role(enum.StrEnum):
    CITIZEN   = "CITIZEN"
    LAB       = "LAB"
    DOCTOR    = "DOCTOR"
    PHARMACY  = "PHARMACY"
    ADMIN     = "ADMIN"
    MINISTRY  = "MINISTRY"


def require_roles(*allowed: Role | str):
    """Return a FastAPI dependency that 403s unless ``X-Role`` is one of ``allowed``."""
    allowed_values = {r.value if isinstance(r, Role) else str(r) for r in allowed}

    def _dep(x_role: str | None = Header(default=None, alias="X-Role")) -> str:
        if x_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing X-Role header",
            )
        normalized = x_role.strip().upper()
        if normalized not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{normalized}' is not permitted here",
            )
        return normalized

    _dep.__doc__ = f"Require one of roles: {sorted(allowed_values)}"
    return _dep
