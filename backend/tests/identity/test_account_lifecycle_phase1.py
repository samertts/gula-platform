from types import SimpleNamespace

import pytest
from app.identity.models.account import AccountStatus
from app.identity.services.account_lifecycle_service import (
    AccountLifecycleService,
    InvalidAccountTransition,
)
from app.identity.services.verification_service import (
    AssuranceLevel,
    NotConnectedProvider,
    VerificationMethod,
    VerificationPolicy,
    VerificationRequest,
    VerificationStatus,
)


def account(status: str):
    return SimpleNamespace(
        status=status,
        is_active=True,
        is_locked=False,
        locked_until=None,
    )


def test_pending_account_can_activate():
    result = AccountLifecycleService.activate(account(AccountStatus.pending_verification.value))
    assert result.status == AccountStatus.active.value
    assert result.is_active is True


def test_active_account_can_be_suspended_but_not_reactivated_from_deactivated():
    result = AccountLifecycleService.suspend(account(AccountStatus.active.value))
    assert result.status == AccountStatus.suspended.value

    with pytest.raises(InvalidAccountTransition):
        AccountLifecycleService.activate(account(AccountStatus.deactivated.value))


def test_disabled_account_cannot_be_reactivated():
    with pytest.raises(InvalidAccountTransition):
        AccountLifecycleService.activate(account(AccountStatus.disabled.value))


@pytest.mark.asyncio
async def test_unconnected_provider_never_claims_verification():
    provider = NotConnectedProvider(VerificationMethod.official_identity)
    result = await provider.verify(
        VerificationRequest(
            account_id="account-1",
            identity_id="identity-1",
            method=VerificationMethod.official_identity,
        ),
    )
    assert result.status == VerificationStatus.not_connected
    assert result.assurance == AssuranceLevel.L0
    assert VerificationPolicy.assurance_for(result) == AssuranceLevel.L0


def test_verification_policy_is_centralized():
    from app.identity.services.verification_service import VerificationResult

    result = VerificationResult(
        status=VerificationStatus.verified,
        assurance=AssuranceLevel.L3,  # a provider claiming the top; the policy overrides
        provider="phone:test",
        method=VerificationMethod.phone,
    )
    assert VerificationPolicy.assurance_for(result) == AssuranceLevel.L1
