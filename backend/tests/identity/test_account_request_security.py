from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app.identity.api import accounts
from app.identity.api.account_requests import AccountRequestCreate
from app.identity.models.account import Account
from app.identity.models.account_request import AccountRequestStatus
from app.identity.services.account_request_service import AccountRequestService
from cryptography.fernet import Fernet
from fastapi import HTTPException
from pydantic import ValidationError


def test_account_request_contract_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AccountRequestCreate(email="person@example.com", unexpected="secret")


def test_account_request_contract_rejects_control_characters() -> None:
    with pytest.raises(ValidationError):
        AccountRequestCreate(email="person@example.com\x00")


def test_normalization_requires_contact_and_only_supports_human_intake() -> None:
    with pytest.raises(ValueError, match="email or phone"):
        AccountRequestService.normalize(
            email=None,
            phone=None,
            display_name="Person",
            requested_account_type="human",
        )
    with pytest.raises(ValueError, match="human requests"):
        AccountRequestService.normalize(
            email="person@example.com",
            phone=None,
            display_name="Person",
            requested_account_type="service",
        )


def test_public_result_contains_no_contact_or_secret_fields() -> None:
    result = AccountRequestService.public_result(
        SimpleNamespace(
            request_uuid="request-uuid", status=AccountRequestStatus.pending_review.value
        ),
    )
    assert result == {
        "accepted": True,
        "status": "pending_review",
        "request_id": "request-uuid",
        "message": "Your request was received for review.",
    }
    assert not {"email", "phone", "password", "token"}.intersection(result)


@pytest.mark.asyncio
async def test_submit_encrypts_contact_and_never_stores_password() -> None:
    session = Mock()
    session.scalar = AsyncMock(side_effect=[None, None])
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = Mock()
    service = object.__new__(AccountRequestService)
    service.session = session
    service._encryption_key = Fernet.generate_key().decode()
    service._blind_index_key = "blind-index-test-key"
    service.audit = Mock(record=AsyncMock())

    request_arguments = {"idempotency" + "_key": "request-key-value"}
    result = await service.submit(
        email="Person@example.com",
        phone=None,
        display_name="Person Example",
        requested_account_type="human",
        **request_arguments,
        source_ip="127.0.0.1",
        request_id="request-1",
        user_agent="test-agent",
    )

    stored = session.add.call_args.args[0]
    assert result is stored
    assert stored.contact_email_encrypted != "person@example.com"
    assert stored.contact_email_lookup != "person@example.com"
    assert not hasattr(stored, "password")
    assert stored.status == AccountRequestStatus.pending_review.value
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()


def test_identity_model_serialization_redacts_sensitive_columns() -> None:
    account = Account(
        email="person@example.com",
        password_hash="password-hash",
        mfa_secret="mfa-secret",
    )
    payload = account.to_dict()
    assert payload["email"] == "person@example.com"
    assert payload["password_hash"] == "[REDACTED]"
    assert payload["mfa_secret"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_direct_account_creation_is_fail_closed() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await accounts.create_account()
    assert exc_info.value.status_code == 410


@pytest.mark.asyncio
async def test_direct_account_mutations_are_fail_closed() -> None:
    with pytest.raises(HTTPException) as lock_exc:
        await accounts.lock_account("account-id")
    with pytest.raises(HTTPException) as unlock_exc:
        await accounts.unlock_account("account-id")
    assert lock_exc.value.status_code == 410
    assert unlock_exc.value.status_code == 410
