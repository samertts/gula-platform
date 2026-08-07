from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.national.services.citizen_service import CitizenService
from app.national.services.identity_service import IdentityService


@pytest.mark.asyncio
async def test_newborn_to_citizen_flow(sample_newborn_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    mock_citizen_service = CitizenService(mock_repo)
    identity_service = IdentityService(mock_citizen_service, mock_repo)
    result = await identity_service.register_newborn(sample_newborn_data)
    assert result["health_number"].startswith("NB")


@pytest.mark.asyncio
async def test_foreigner_registration_flow(sample_foreigner_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    mock_citizen_service = CitizenService(mock_repo)
    identity_service = IdentityService(mock_citizen_service, mock_repo)
    result = await identity_service.register_foreigner(sample_foreigner_data)
    assert result["health_number"].startswith("FR")
