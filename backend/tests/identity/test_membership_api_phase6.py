from __future__ import annotations

from app.identity.api.memberships import (
    MembershipApplicationRequest,
    MembershipInvitationRequest,
    serialize_invitation,
)
from app.identity.api.router import router
from app.identity.models.membership import MembershipInvitation
from fastapi.routing import APIRoute


def _membership_routes() -> dict[tuple[str, str], APIRoute]:
    routes: dict[tuple[str, str], APIRoute] = {}
    for route in router.routes:
        if isinstance(route, APIRoute) and route.path.startswith(("/niam/memberships", "/memberships")):
            path = route.path if route.path.startswith("/niam/") else f"/niam{route.path}"
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
