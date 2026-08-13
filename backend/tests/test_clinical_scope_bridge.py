from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.clinical_scope import ClinicalLabFacilityBinding, ClinicalLabFacilityBindingStatus
from app.services.clinical_scope_bridge_service import (
    ClinicalFacilityScopeAmbiguous,
    ClinicalFacilityScopeUnavailable,
    ClinicalScopeBridgeService,
)


def _binding(*, lab_id: int = 41, facility_id: int = 7) -> ClinicalLabFacilityBinding:
    return ClinicalLabFacilityBinding(
        id="01CLINICALSCOPEBINDING001",
        legacy_lab_id=lab_id,
        facility_resource_id=facility_id,
        status=ClinicalLabFacilityBindingStatus.pending.value,
        mapping_version=1,
    )


def test_binding_requires_reviewed_transitions_and_reason_for_revocation():
    binding = _binding()
    with pytest.raises(ValueError, match="Invalid clinical lab-facility binding transition"):
        binding.transition(ClinicalLabFacilityBindingStatus.active)

    binding.transition(ClinicalLabFacilityBindingStatus.validated)
    binding.transition(ClinicalLabFacilityBindingStatus.active)
    assert binding.status == ClinicalLabFacilityBindingStatus.active.value
    assert binding.activated_at is not None

    with pytest.raises(ValueError, match="reason is required"):
        binding.transition(ClinicalLabFacilityBindingStatus.revoked)
    binding.transition(ClinicalLabFacilityBindingStatus.revoked, reason="facility reassignment reviewed")
    assert binding.status == ClinicalLabFacilityBindingStatus.revoked.value
    assert binding.mapping_version == 4


@pytest.mark.asyncio
async def test_scope_resolution_rejects_missing_or_ambiguous_active_binding():
    session = MagicMock()
    service = ClinicalScopeBridgeService(session)

    missing_result = MagicMock()
    missing_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=missing_result)
    with pytest.raises(ClinicalFacilityScopeUnavailable, match="No active reviewed"):
        await service.resolve_active_binding(41)

    ambiguous_result = MagicMock()
    ambiguous_result.scalars.return_value.all.return_value = [_binding(), _binding(facility_id=8)]
    session.execute = AsyncMock(return_value=ambiguous_result)
    with pytest.raises(ClinicalFacilityScopeAmbiguous, match="More than one"):
        await service.resolve_active_binding(41)


@pytest.mark.asyncio
async def test_scope_resolution_accepts_exactly_one_reviewed_binding():
    session = MagicMock()
    binding = _binding()
    binding.status = ClinicalLabFacilityBindingStatus.active.value
    result = MagicMock()
    result.scalars.return_value.all.return_value = [binding]
    session.execute = AsyncMock(return_value=result)

    resolved = await ClinicalScopeBridgeService(session).resolve_active_binding(41)
    assert resolved is binding
    assert resolved.legacy_lab_id == 41
    assert resolved.facility_resource_id == 7


def test_scope_migration_is_additive_and_reversible():
    from pathlib import Path

    migration = (
        Path(__file__).parents[1] / "migrations/versions/20260813_0002_clinical_scope_bridge.py"
    ).read_text()
    assert 'down_revision = "20260813_0001"' in migration
    assert "clinical_lab_facility_bindings" in migration
    assert 'ForeignKey("labs.id"' in migration
    assert 'ForeignKey("facilities.id"' in migration
    assert "def downgrade" in migration
