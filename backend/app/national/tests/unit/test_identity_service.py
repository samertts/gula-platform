from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.national.exceptions import ForeignerRegistrationError, NewbornRegistrationError
from app.national.services.identity_service import IdentityService


@pytest.mark.asyncio
async def test_register_newborn_rejects_legacy_parent_identifiers(sample_newborn_data):
    """The endpoint now requires raw request-only NIDs, not stored parent IDs."""
    service = IdentityService(Mock(), Mock())
    with pytest.raises(NewbornRegistrationError):
        await service.register_newborn(sample_newborn_data)


@pytest.mark.asyncio
async def test_register_newborn_missing_mother():
    service = IdentityService(Mock(), Mock())
    with pytest.raises(NewbornRegistrationError):
        await service.register_newborn({})


@pytest.mark.asyncio
async def test_register_foreigner_success(sample_foreigner_data):
    mock_citizen_service = Mock()
    mock_citizen_service.register_citizen = AsyncMock()
    service = IdentityService(mock_citizen_service, Mock())
    result = await service.register_foreigner(sample_foreigner_data)
    assert "citizen" in result
    assert result["health_number"].startswith("FR")


@pytest.mark.asyncio
async def test_register_foreigner_missing_passport():
    service = IdentityService(Mock(), Mock())
    with pytest.raises(ForeignerRegistrationError):
        await service.register_foreigner({})


@pytest.mark.asyncio
async def test_register_visitor():
    mock_citizen_service = Mock()
    mock_citizen_service.register_citizen = AsyncMock()
    service = IdentityService(mock_citizen_service, Mock())
    data = {"passport_number": "PASS123", "first_name": "Test", "nationality": "UK"}
    result = await service.register_visitor(data)
    assert result.get("is_temporary") is True


@pytest.mark.asyncio
async def test_register_unknown_patient():
    mock_citizen_service = Mock()
    mock_citizen_service.register_citizen = AsyncMock()
    service = IdentityService(mock_citizen_service, Mock())
    data = {"description": "Found near market", "gender": "male"}
    result = await service.register_unknown_patient(data)
    assert result.get("requires_merge") is True
    assert result.get("is_temporary") is True
