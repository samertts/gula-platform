"""Foundation and account/identity hardening tests for IAM Phases 0 and 1."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.models.account import AccountStatus, AccountType
from app.identity.models.audit import AuditAction
from app.identity.services import account_service as account_service_module
from app.identity.services.account_lifecycle_service import (
    LEGAL_TRANSITIONS,
    AccountLifecycleService,
    InvalidAccountTransition,
)
from app.identity.services.account_service import AccountService, DuplicateAccountError
from sqlalchemy.exc import IntegrityError


class _AccountRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, account):
        return account


@pytest.mark.asyncio
async def test_account_creation_normalizes_identifiers_and_keeps_pending_status(monkeypatch):
    monkeypatch.setattr(account_service_module, "AccountRepository", _AccountRepository)

    result = await AccountService(SimpleNamespace()).create_account(
        identity_id="identity-1",
        account_type=AccountType.human,
        email="  PERSON@EXAMPLE.COM ",
        phone="+964 700 123 4567",
        username="  Person.One ",
        password="correct horse battery staple",
    )

    assert result.email == "person@example.com"
    assert result.phone == "+9647001234567"
    assert result.username == "person.one"
    assert result.account_type == AccountType.human.value
    assert result.status == AccountStatus.pending_verification.value
    assert result.password_hash
    assert result.password_hash != "correct horse battery staple"


@pytest.mark.asyncio
async def test_duplicate_account_creation_rolls_back_and_returns_domain_error(monkeypatch):
    class _DuplicateAccountRepository:
        def __init__(self, session):
            self.session = session

        async def create(self, account):
            raise IntegrityError("insert", {}, Exception("unique constraint"))

    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(account_service_module, "AccountRepository", _DuplicateAccountRepository)

    with pytest.raises(DuplicateAccountError, match="already registered"):
        await AccountService(session).create_account(
            identity_id="identity-1",
            email="person@example.com",
            password="correct horse battery staple",
        )

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_account_creation_rejects_missing_identifier_and_short_password(monkeypatch):
    monkeypatch.setattr(account_service_module, "AccountRepository", _AccountRepository)
    service = AccountService(SimpleNamespace())

    with pytest.raises(ValueError, match="identifier"):
        await service.create_account(identity_id="identity-1")

    with pytest.raises(ValueError, match="at least"):
        await service.create_account(
            identity_id="identity-1",
            email="person@example.com",
            password="too-short",
        )


def test_account_lifecycle_matrix_is_deny_by_default():
    assert LEGAL_TRANSITIONS[AccountStatus.pending_verification.value] == frozenset(
        {AccountStatus.active.value, AccountStatus.deactivated.value},
    )
    assert LEGAL_TRANSITIONS[AccountStatus.deactivated.value] == frozenset()
    assert not AccountLifecycleService.can_transition(
        AccountStatus.deactivated.value,
        AccountStatus.active.value,
    )

    item = SimpleNamespace(
        status=AccountStatus.deactivated.value,
        is_active=False,
        is_locked=False,
        locked_until=None,
    )
    with pytest.raises(InvalidAccountTransition):
        AccountLifecycleService.activate(item)
    assert item.status == AccountStatus.deactivated.value
    assert item.is_active is False


def test_phase0_audit_vocabulary_covers_foundation_security_events():
    required = {
        AuditAction.account_created,
        AuditAction.account_activated,
        AuditAction.account_locked,
        AuditAction.account_suspended,
        AuditAction.session_created,
        AuditAction.session_revoked,
        AuditAction.login_failure,
        AuditAction.policy_denied,
        AuditAction.audit_chain_verified,
        AuditAction.audit_tamper_detected,
    }
    assert required.issubset(set(AuditAction))
    values = [item.value for item in AuditAction]
    assert len(values) == len(set(values))
