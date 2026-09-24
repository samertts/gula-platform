from types import SimpleNamespace

import pytest
from app.identity.models.verification_record import VerificationRecordStatus
from app.identity.services.verification_record_service import (
    InvalidVerificationTransition,
    VerificationRecordService,
)
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


def record(status: str = VerificationRecordStatus.not_started.value):
    return SimpleNamespace(
        status=status,
        assurance_level=AssuranceLevel.L0.value,
        started_at=None,
        completed_at=None,
        valid_from=None,
        revoked_at=None,
        provider_reference=None,
        verified_attributes=None,
        failure_reason_code=None,
        is_active=True,
    )


def test_verification_state_machine_requires_backend_progression():
    item = record()
    VerificationRecordService.transition(item, VerificationRecordStatus.pending)
    VerificationRecordService.transition(item, VerificationRecordStatus.in_progress)
    assert item.status == VerificationRecordStatus.in_progress.value

    with pytest.raises(InvalidVerificationTransition):
        VerificationRecordService.transition(item, VerificationRecordStatus.revoked)


def test_provider_result_can_establish_verified_only_after_in_progress():
    item = record(VerificationRecordStatus.in_progress.value)
    result = VerificationResult(
        status=VerificationStatus.verified,
        assurance=AssuranceLevel.L3,  # the provider grades itself; the policy overrides
        provider="official-test-provider",
        method=VerificationMethod.official_identity,
        provider_reference="opaque-reference",
        verified_attributes={"name": "verified-only"},
    )
    VerificationRecordService.apply_provider_result(item, result)
    assert item.status == VerificationRecordStatus.verified.value
    assert item.assurance_level == AssuranceLevel.L2.value
    assert item.verified_attributes == {"name": "verified-only"}


@pytest.mark.asyncio
async def test_not_connected_provider_cannot_grant_assurance():
    provider = NotConnectedProvider(VerificationMethod.official_identity)
    result = await provider.verify(VerificationRequest("a", "i", VerificationMethod.official_identity))
    assert result.status == VerificationStatus.not_connected
    assert VerificationPolicy.assurance_for(result) == AssuranceLevel.L0


def test_revocation_downgrades_assurance_and_deactivates_record():
    item = record(VerificationRecordStatus.verified.value)
    item.assurance_level = AssuranceLevel.L2.value
    VerificationRecordService.revoke(item)
    assert item.status == VerificationRecordStatus.revoked.value
    assert item.assurance_level == AssuranceLevel.L0.value
    assert item.is_active is False


def test_assurance_engine_is_centralized_and_deny_by_default():
    results = [
        VerificationResult(
            status=VerificationStatus.verified,
            assurance=AssuranceLevel.L3,  # the provider grades itself; the policy overrides
            provider="professional-test-provider",
            method=VerificationMethod.professional_registry,
        ),
    ]
    # A registry attests to a licence, so it answers the professional question
    # at L2 — not the provider's self-declared L3, and not the identity
    # question at any level.
    assert AssuranceEngine.level_for(results, VerificationPurpose.professional) == AssuranceLevel.L2
    AssuranceEngine.require(results, VerificationPurpose.professional, AssuranceLevel.L2)
    with pytest.raises(PermissionError):
        AssuranceEngine.require(results, VerificationPurpose.identity, AssuranceLevel.L1)
    with pytest.raises(PermissionError):
        AssuranceEngine.require([], VerificationPurpose.contact, AssuranceLevel.L1)
