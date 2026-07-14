from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.national.exceptions import CitizenNotFoundError
from app.national.services.citizen_service import CitizenService


@pytest.mark.asyncio
async def test_register_citizen_success(sample_citizen_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    service = CitizenService(mock_repo)
    result = await service.register_citizen(sample_citizen_data)
    assert result is not None
    mock_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_citizen_not_found():
    mock_repo = Mock()
    mock_repo.get = AsyncMock(return_value=None)
    service = CitizenService(mock_repo)
    with pytest.raises(CitizenNotFoundError):
        await service.get_citizen("NONEXISTENT")


@pytest.mark.asyncio
async def test_generate_health_number():
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    service = CitizenService(mock_repo)
    hn = await service._generate_health_number()
    assert hn.startswith("IQ")
    assert len(hn) == 10
