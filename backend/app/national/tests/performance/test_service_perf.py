from __future__ import annotations

import time
from unittest.mock import AsyncMock, Mock

import pytest

from app.national.services.citizen_service import CitizenService


@pytest.mark.asyncio
async def test_register_citizen_performance(sample_citizen_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    service = CitizenService(mock_repo)
    start = time.time()
    for _ in range(100):
        await service.register_citizen(sample_citizen_data)
    elapsed = time.time() - start
    assert elapsed < 5.0
