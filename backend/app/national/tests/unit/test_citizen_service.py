from __future__ import annotations

import re
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.national.domain.health_number import HealthNumberSequence
from app.national.exceptions import CitizenNotFoundError
from app.national.services.citizen_service import CitizenService


def _sequence_db(existing: HealthNumberSequence | None = None) -> Mock:
    """Deterministic sequence-aware DB double; no real or invented national IDs."""
    db = Mock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = existing
    return db


@pytest.mark.asyncio
async def test_register_citizen_success(sample_citizen_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    service = CitizenService(mock_repo, db=_sequence_db())
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
    service = CitizenService(mock_repo, db=_sequence_db())
    hn = await service._generate_health_number()
    # Canonical ADR-012 format: IQ + UTC year + six-digit sequence.
    assert re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", hn)


@pytest.mark.asyncio
async def test_generate_health_number_uses_existing_sequence_row():
    year = datetime.now().year
    entry = HealthNumberSequence(prefix="IQ", year=year, sequence_number=41)
    db = _sequence_db(entry)
    service = CitizenService(Mock(), db=db)
    hn = await service._generate_health_number()
    assert hn == f"IQ{year}000042"
    assert entry.sequence_number == 42
    db.add.assert_not_called()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_generate_health_number_creates_missing_sequence_row():
    year = datetime.now().year
    db = _sequence_db()
    service = CitizenService(Mock(), db=db)
    hn = await service._generate_health_number()
    assert hn == f"IQ{year}000001"
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_register_citizen_persists_generated_health_number(sample_citizen_data):
    repo = Mock()
    repo.get_by_health_number = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    service = CitizenService(repo, db=_sequence_db())
    await service.register_citizen(sample_citizen_data)
    created = repo.create.call_args.args[0]
    assert re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", created.health_number)
