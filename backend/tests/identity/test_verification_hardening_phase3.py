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
    VerificationPurpose,
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


def result(status: VerificationStatus, method: VerificationMethod, assurance: AssuranceLevel = AssuranceLevel.L3):
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
    assert AssuranceEngine.level_for([candidate], VerificationPurpose.professional) == AssuranceLevel.L0
    with pytest.raises(PermissionError, match="Required professional assurance"):
        AssuranceEngine.require([candidate], VerificationPurpose.professional, AssuranceLevel.L1)


@pytest.mark.parametrize(
    ("method", "purpose", "expected"),
    [
        (VerificationMethod.phone, VerificationPurpose.contact, AssuranceLevel.L1),
        (VerificationMethod.email, VerificationPurpose.contact, AssuranceLevel.L1),
        (VerificationMethod.official_identity, VerificationPurpose.identity, AssuranceLevel.L2),
        (VerificationMethod.professional_registry, VerificationPurpose.professional, AssuranceLevel.L2),
        (VerificationMethod.organization_registry, VerificationPurpose.organization, AssuranceLevel.L2),
        # Capture techniques read a document; they do not attest to it.
        (VerificationMethod.ocr, VerificationPurpose.identity, AssuranceLevel.L0),
        (VerificationMethod.nfc, VerificationPurpose.identity, AssuranceLevel.L0),
    ],
)
def test_verified_method_mapping_is_authoritative(method, purpose, expected):
    candidate = result(VerificationStatus.verified, method)
    assert VerificationPolicy.purpose_for(method) == purpose
    assert VerificationPolicy.assurance_for(candidate) == expected


def test_assurance_is_scoped_per_purpose_and_never_substituted():
    """AUTH-004. This test previously asserted the defect.

    It read: phone + organization_registry + an expired professional check
    collapse to a single ``L4``, and ``require(results, L4)`` passes. On one
    ladder ``organization_registry`` sat above ``official_identity``, so an
    account whose *employer* was verified out-ranked one whose *holder* was,
    and any caller asking for "at least L2 — we know who this person is" was
    satisfied by an organization check.

    Purposes are independent questions. They are answered separately now, and
    a caller must say which one it is asking.
    """
    results = [
        result(VerificationStatus.verified, VerificationMethod.phone),
        result(VerificationStatus.verified, VerificationMethod.organization_registry),
        result(VerificationStatus.expired, VerificationMethod.professional_registry),
    ]

    assert AssuranceEngine.level_for(results, VerificationPurpose.contact) == AssuranceLevel.L1
    assert AssuranceEngine.level_for(results, VerificationPurpose.organization) == AssuranceLevel.L2
    # Never proven, and never inferred from the other two:
    assert AssuranceEngine.level_for(results, VerificationPurpose.identity) == AssuranceLevel.L0
    # An expired check contributes nothing.
    assert AssuranceEngine.level_for(results, VerificationPurpose.professional) == AssuranceLevel.L0

    AssuranceEngine.require(results, VerificationPurpose.organization, AssuranceLevel.L2)
    with pytest.raises(PermissionError, match="Required identity assurance"):
        AssuranceEngine.require(results, VerificationPurpose.identity, AssuranceLevel.L2)


def test_a_caller_that_does_not_name_a_purpose_cannot_be_answered():
    """Fail closed at the call site rather than returning a wrong number.

    The old signature took results alone. Any call written against it now
    raises TypeError instead of silently answering a different question from
    the one the caller believed it was asking.
    """
    results = [result(VerificationStatus.verified, VerificationMethod.organization_registry)]

    with pytest.raises(TypeError):
        AssuranceEngine.level_for(results)
    with pytest.raises(TypeError):
        AssuranceEngine.require(results, AssuranceLevel.L2)


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
