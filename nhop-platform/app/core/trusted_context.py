"""The single source of caller identity for NHOP.

Every authority decision in this service must come from here. Nothing may read
identity, role or tenancy off the wire.

WHY THIS FAILS CLOSED (NR-127)
------------------------------
NHOP has no authentication stack. Until this commit its entire authority model
was client-supplied headers: ``X-Role`` chose your role, ``X-Actor-Id`` chose
who you were, and both were persisted as the recorded actor. Any caller could
send ``X-Role: MINISTRY``. The production identity surface (JWT-backed) lives
in the GULA platform and is not federated here yet, which is exactly what
``rbac.py`` said when it introduced the header shortcut:

    "Until NHOP shares that identity surface, routes that need authorisation
     read the caller's role from the X-Role request header."

So there is no trusted context to derive, and inventing a second identity
system in this service is not the answer. This module therefore refuses to
produce a context at all. A service that cannot say who is calling must not
act on their behalf -- an unavailable endpoint is recoverable, a clinical
record forged under a real laboratory's name is not.

WHEN FEDERATION LANDS
---------------------
Replace the body of :func:`require_trusted_context` with one that validates a
GULA-issued token and maps its claims onto :class:`TrustedContext`. Nothing
else in the service needs to change: every call site already reads from the
context this dependency puts on ``request.state``.

Tests that need a caller override the dependency through FastAPI's own
``app.dependency_overrides``. That is deliberate -- there is no environment
variable or header that can switch this on, because anything switchable from
outside the process is the defect this module exists to remove.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request, status

#: Attribute name under which the resolved context is published on the request.
REQUEST_STATE_ATTR = "trusted_context"

_UNAVAILABLE_DETAIL = (
    "NHOP cannot establish a trusted caller identity: no identity provider is "
    "federated with this service. Endpoints that act on behalf of a caller are "
    "unavailable until one is. See NR-127."
)


@dataclass(frozen=True)
class TrustedContext:
    """Who the caller is, as established by the server. Never by the client."""

    actor_id: str
    role: str
    lab_id: str | None = None


def require_trusted_context(request: Request) -> TrustedContext:
    """FastAPI dependency: the only way to obtain a caller identity.

    Fails closed. See the module docstring for why, and for what replaces this
    body when GULA identity is federated.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_UNAVAILABLE_DETAIL,
    )


def current_context(request: Request) -> TrustedContext:
    """The context for this request, as published by the dependency.

    Handlers and helpers use this instead of reading headers. If it is missing,
    the route was reached without the dependency -- which is a wiring mistake,
    not an anonymous caller, so it fails closed too rather than defaulting.
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
