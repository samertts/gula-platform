"""Lightweight role-based access control for the NHOP API.

The production auth stack (JWT-backed) lives in the GULA platform. Until
NHOP shares that identity surface, routes that need authorisation read the
caller's role from :mod:`app.core.trusted_context`, which fails closed
(503) until a real identity provider is federated. This module previously
read the role straight from a client-supplied ``X-Role`` header with no
verification at all — any caller could send ``X-Role: MINISTRY`` and pass —
that gap is closed by sourcing the role from the trusted context instead.

Exposed:
    :class:`Role`           - enum of known roles
    :func:`require_roles`   - FastAPI dependency factory
"""
from __future__ import annotations

import enum

from fastapi import HTTPException, Request, status

from .trusted_context import current_context


class Role(enum.StrEnum):
    CITIZEN   = "CITIZEN"
    LAB       = "LAB"
    DOCTOR    = "DOCTOR"
    PHARMACY  = "PHARMACY"
    ADMIN     = "ADMIN"
    MINISTRY  = "MINISTRY"


def require_roles(*allowed: Role | str):
    """Return a FastAPI dependency that 403s unless the trusted context's
    role is one of ``allowed``."""
    allowed_values = {r.value if isinstance(r, Role) else str(r) for r in allowed}

    def _dep(request: Request) -> str:
        normalized = (current_context(request).role or "").strip().upper()
        if normalized not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{normalized}' is not permitted here",
            )
        return normalized

    _dep.__doc__ = f"Require one of roles: {sorted(allowed_values)}"
    return _dep
