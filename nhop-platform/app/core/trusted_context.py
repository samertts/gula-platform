"""The single source of caller identity for NHOP.

Every authority decision in this service must come from here. Nothing may
read identity, role, or tenancy off the wire.

WHY THIS FAILS CLOSED
---------------------
NHOP has no authentication stack of its own. Before this module, every
role/actor-scoped endpoint in this service trusted client-supplied headers —
``X-Role`` chose the caller's role, ``X-Actor-Id`` chose who they were — and
neither was checked against any session, token, or server-side identity. Any
caller could send ``X-Role: MINISTRY`` and pass every gate that used it (see
``nhop-platform/tests/test_rbac_is_not_a_trust_boundary.py``,
``test_notifications_actor_id_is_not_a_trust_boundary.py``, and the
now-superseded module docstrings in ``core/rbac.py`` and the v1 route files,
which documented this honestly rather than pretending the header check was
real access control).

The production identity surface (JWT-backed RBAC) lives in the GULA
platform (``backend/app/security/``) and is not federated into this service
yet. Rather than invent a second, parallel identity system here — which
would just be a differently-shaped guess at who the caller is — this module
refuses to produce a caller identity at all until real federation exists. A
service that cannot say who is calling must not act on their behalf: an
endpoint that is unavailable is recoverable; a clinical record or outbreak
report forged under a spoofed role is not.

WHEN FEDERATION LANDS
---------------------
Replace the body of :func:`require_trusted_context` with one that validates
a GULA-issued token and maps its claims onto :class:`TrustedContext`.
Nothing else in the service needs to change: every call site already reads
identity from the context this dependency publishes on ``request.state``,
not from headers.

Tests that need a caller override the dependency through FastAPI's own
``app.dependency_overrides``. There is no environment variable or header
that can switch this on, because anything switchable from outside the
process is the defect this module exists to remove.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request, status

#: Attribute name under which the resolved context is published on the request.
REQUEST_STATE_ATTR = "trusted_context"

_UNAVAILABLE_DETAIL = (
    "NHOP cannot establish a trusted caller identity: no identity provider is "
    "federated with this service. Endpoints that act on behalf of a caller are "
    "unavailable until one is."
)


@dataclass(frozen=True)
class TrustedContext:
    """Who the caller is, as established by the server. Never by the client."""

    actor_id: str
    role: str
    lab_id: str | None = None


def require_trusted_context(request: Request) -> TrustedContext:
    """FastAPI dependency: the only way to obtain a caller identity.

    Fails closed. See the module docstring for why, and for what replaces
    this body when GULA identity is federated into NHOP.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_UNAVAILABLE_DETAIL,
    )


def current_context(request: Request) -> TrustedContext:
    """The context for this request, as published by the dependency.

    Handlers and helpers use this instead of reading headers. If it is
    missing, the route was reached without the dependency — a wiring
    mistake, not an anonymous caller — so this fails closed too rather than
    defaulting to some placeholder identity.
    """
    context = getattr(request.state, REQUEST_STATE_ATTR, None)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_UNAVAILABLE_DETAIL,
        )
    return context


def publish(request: Request, context: TrustedContext) -> TrustedContext:
    """Put a resolved context on the request so helpers can read it."""
    setattr(request.state, REQUEST_STATE_ATTR, context)
    return context
