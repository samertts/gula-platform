"""Verification lifecycle and assurance hardening tests for IAM Phase 3."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.services.verification_service import (
    AssuranceEngine,
    AssuranceLevel,
    NotConnectedProvider,
    VerificationMethod,
    VerificationPolicy,
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


def result(status: VerificationStatus, method: VerificationMethod, assurance: AssuranceLevel = AssuranceLevel.L5):
    return VerificationResult(
        status=status,
        assurance=assurance,
        provider="test-provider",
        method=method,
        provider_reference="reference-1" if status == VerificationStatus.verified else None,
    )


@pytest.mark.parametrize(
    "status",
    [
        VerificationStatus.not_started,
        VerificationStatus.pending,
        VerificationStatus.in_progress,
        VerificationStatus.failed,
        VerificationStatus.expired,
        VerificationStatus.revoked,
        VerificationStatus.requires_review,
        VerificationStatus.not_connected,
    ],
)
def test_non_verified_statuses_always_have_zero_assurance(status):
    candidate = result(status, VerificationMethod.professional_registry)

    assert VerificationPolicy.assurance_for(candidate) == AssuranceLevel.L0
    assert AssuranceEngine.level_for([candidate]) == AssuranceLevel.L0
    with pytest.raises(PermissionError, match="Required assurance"):
        AssuranceEngine.require([candidate], AssuranceLevel.L1)


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        (VerificationMethod.phone, AssuranceLevel.L1),
        (VerificationMethod.email, AssuranceLevel.L1),
        (VerificationMethod.official_identity, AssuranceLevel.L2),
        (VerificationMethod.professional_registry, AssuranceLevel.L3),
        (VerificationMethod.organization_registry, AssuranceLevel.L4),
    ],
)
def test_verified_method_mapping_is_authoritative(method, expected):
    assert VerificationPolicy.assurance_for(result(VerificationStatus.verified, method)) == expected


def test_assurance_engine_selects_highest_verified_level_only():
    results = [
        result(VerificationStatus.verified, VerificationMethod.phone, AssuranceLevel.L5),
        result(VerificationStatus.verified, VerificationMethod.organization_registry, AssuranceLevel.L1),
        result(VerificationStatus.expired, VerificationMethod.professional_registry, AssuranceLevel.L5),
    ]

    assert AssuranceEngine.level_for(results) == AssuranceLevel.L4
    AssuranceEngine.require(results, AssuranceLevel.L4)
    with pytest.raises(PermissionError):
        AssuranceEngine.require(results, AssuranceLevel.L5)


@pytest.mark.asyncio
async def test_not_connected_provider_never_claims_success_or_assurance():
    provider = NotConnectedProvider(VerificationMethod.professional_registry)
    request = VerificationRequest(
        account_id="account-1",
        identity_id="identity-1",
        method=VerificationMethod.professional_registry,
    )

    started = await provider.start_verification(request)
    completed = await provider.complete_verification(SimpleNamespace(), evidence={"fake": True})

    assert started.status == VerificationStatus.not_connected
    assert started.assurance == AssuranceLevel.L0
    assert completed.status == VerificationStatus.failed
    assert completed.assurance == AssuranceLevel.L0
    assert provider.connected is False
