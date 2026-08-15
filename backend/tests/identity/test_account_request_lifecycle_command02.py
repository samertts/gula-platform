from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.api import account_requests as account_requests_api
from app.identity.api.account_requests import (
    AccountActivationRequest,
    AccountRequestAction,
    AccountRequestVerificationConfirm,
)
from app.identity.api.router import router
from app.identity.models.account import AccountStatus
from app.identity.models.account_request import AccountRequestStatus
from app.identity.services.account_lifecycle_service import (
    AccountLifecycleService,
    InvalidAccountTransition,
)
from app.identity.services.account_request_service import (
    REQUEST_TRANSITIONS,
    AccountRequestService,
)
from fastapi.routing import APIRoute
from pydantic import ValidationError


def _account(status: str):
    return SimpleNamespace(
        status=status,
        is_active=True,
        is_locked=False,
        locked_until=None,
    )


def _iter_api_routes(router_routes, prefix: str = ""):
    for route in router_routes:
        if isinstance(route, APIRoute):
            yield route, f"{prefix.rstrip('/')}{route.path or '/'}"
            continue
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            include_context = getattr(route, "include_context", None)
            included_prefix = getattr(include_context, "prefix", None) or prefix
            yield from _iter_api_routes(original_router.routes, included_prefix)


def test_account_state_machine_requires_verification_and_approval():
    with pytest.raises(InvalidAccountTransition):
        AccountLifecycleService.activate(_account(AccountStatus.pending_verification.value))

    item = _account(AccountStatus.pending_verification.value)
    AccountLifecycleService.mark_verified(item)
    AccountLifecycleService.request_approval(item)
    AccountLifecycleService.approve(item)
    AccountLifecycleService.activate(item)
    assert item.status == AccountStatus.active.value


def test_account_state_machine_denies_terminal_reactivation():
    for terminal in (AccountStatus.rejected.value, AccountStatus.expired.value, AccountStatus.deactivated.value):
        with pytest.raises(InvalidAccountTransition):
            AccountLifecycleService.activate(_account(terminal))


def test_request_transition_matrix_has_no_direct_approval_from_review():
    assert AccountRequestService.can_transition(
        AccountRequestStatus.verified.value,
        AccountRequestStatus.pending_approval.value,
    )
    assert not AccountRequestService.can_transition(
        AccountRequestStatus.pending_review.value,
        AccountRequestStatus.approved.value,
    )
    assert not AccountRequestService.can_transition(
        AccountRequestStatus.pending_verification.value,
        AccountRequestStatus.approved.value,
    )
    assert REQUEST_TRANSITIONS[AccountRequestStatus.rejected.value] == frozenset()


def test_mutation_contracts_forbid_client_authority_and_secrets():
    for model in (AccountRequestAction, AccountRequestVerificationConfirm, AccountActivationRequest):
        with pytest.raises(ValidationError):
            model.model_validate({"actor_id": "attacker", "status": "active"})

    assert "actor_id" not in AccountRequestAction.model_fields
    assert "account_id" not in AccountRequestAction.model_fields
    assert "status" not in AccountRequestAction.model_fields


def test_request_serializer_contains_no_contact_or_token_material():
    request = SimpleNamespace(
        request_uuid="request-1",
        status=AccountRequestStatus.pending_review.value,
        requested_account_type="human",
        account_id=None,
        reviewed_at=None,
        verified_at=None,
        expires_at=None,
        is_active=True,
        contact_email_encrypted="private",
        activation_token_hash="private",
    )
    serialized = AccountRequestService.serialize_request(request)
    assert serialized == {
        "request_id": "request-1",
        "status": "pending_review",
        "requested_account_type": "human",
        "account_id": None,
        "reviewed_at": None,
        "verified_at": None,
        "expires_at": None,
        "is_active": True,
    }
    assert not {"email", "phone", "token", "token_hash", "password"}.intersection(serialized)


def test_account_request_routes_are_included_and_governed():
    assert any(
        getattr(route, "original_router", None) is account_requests_api.router
        for route in router.routes
    )
    routes = {
        (method, path)
        for route, path in _iter_api_routes(router.routes)
        if path.startswith(("/niam/account-requests", "/account-requests"))
        for method in route.methods or set()
    }
    expected = {
        ("GET", "/niam/account-requests/"),
        ("POST", "/niam/account-requests/{request_uuid}/review"),
        ("POST", "/niam/account-requests/{request_uuid}/verification/start"),
        ("POST", "/niam/account-requests/{request_uuid}/verification/confirm"),
        ("POST", "/niam/account-requests/{request_uuid}/approve"),
        ("POST", "/niam/account-requests/{request_uuid}/activation-token"),
        ("POST", "/niam/account-requests/{request_uuid}/activate"),
        ("POST", "/niam/account-requests/{request_uuid}/reject"),
        ("POST", "/niam/account-requests/{request_uuid}/expire"),
        ("POST", "/niam/account-requests/accounts/{account_uuid}/{action}"),
    }
    assert expected.issubset(routes)
