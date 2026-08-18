from __future__ import annotations

from app.identity.api import memberships as memberships_api
from app.identity.api.memberships import (
    MembershipApplicationRequest,
    MembershipInvitationRequest,
    serialize_invitation,
)
from app.identity.api.router import router
from app.identity.models.membership import MembershipInvitation
from fastapi.routing import APIRoute


def _iter_api_routes(router_routes, prefix: str = ""):
    """Flatten FastAPI routes and the platform's lazy included-router wrappers."""
    for route in router_routes:
        if isinstance(route, APIRoute):
            route_path = route.path or "/"
            full_path = f"{prefix.rstrip('/')}{route_path}"
            yield route, full_path
            continue
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            include_context = getattr(route, "include_context", None)
            included_prefix = getattr(include_context, "prefix", None) or prefix
            yield from _iter_api_routes(original_router.routes, included_prefix)


def _membership_routes() -> dict[tuple[str, str], APIRoute]:
    """Return membership routes after verifying they are included by the NIAM router.

    FastAPI represents nested routers differently across supported versions:
    either as lazy ``_IncludedRouter`` wrappers or as materialized ``APIRoute``
    instances.  Both forms must still expose the same protected lifecycle routes.
    """
    has_lazy_membership_router = any(
        getattr(route, "original_router", None) is memberships_api.router for route in router.routes
    )
    has_materialized_membership_route = any(
        isinstance(route, APIRoute) and (route.path or "").startswith("/niam/memberships")
        for route in router.routes
    )
    assert has_lazy_membership_router or has_materialized_membership_route

    routes: dict[tuple[str, str], APIRoute] = {}
    for route, path in _iter_api_routes(router.routes):
        if path.startswith(("/niam/memberships", "/memberships")):
            path = path if path.startswith("/niam/") else f"/niam{path}"
            for method in route.methods or set():
                routes[(method, path)] = route
    return routes


def test_membership_api_exposes_real_lifecycle_routes() -> None:
    routes = _membership_routes()
    expected = {
        ("GET", "/niam/memberships/me"),
        ("POST", "/niam/memberships/applications"),
        ("POST", "/niam/memberships/applications/{application_id}/approve"),
        ("POST", "/niam/memberships/invitations"),
        ("POST", "/niam/memberships/invitations/{invitation_id}/accept"),
        ("POST", "/niam/memberships/invitations/{invitation_id}/revoke"),
        ("POST", "/niam/memberships/{membership_id}/revoke"),
        ("POST", "/niam/memberships/{membership_id}/suspend"),
        ("POST", "/niam/memberships/{membership_id}/reactivate"),
    }
    assert expected.issubset(routes)


def test_mutation_bodies_do_not_accept_server_authoritative_status_or_account() -> None:
    application_fields = set(MembershipApplicationRequest.model_fields)
    invitation_fields = set(MembershipInvitationRequest.model_fields)
    assert "status" not in application_fields | invitation_fields
    assert "account_id" not in application_fields | invitation_fields
    assert "actor_id" not in application_fields | invitation_fields


def test_invitation_serializer_does_not_leak_hash_or_secret_without_explicit_acceptance() -> None:
    invitation = MembershipInvitation(
        id="invitation",
        uuid="uuid",
        invitation_key="key",
        token_hash="private-hash",
        organization_id="organization",
        relationship_type="employee",
        scope_type="organization",
        status="pending",
        expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        version=1,
    )
    serialized = serialize_invitation(invitation)
    assert "token" not in serialized
    assert "token_hash" not in serialized
