from __future__ import annotations

import re
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.national.services.citizen_service import CitizenService
from app.national.services.identity_service import IdentityService


def _sequence_db() -> Mock:
    """Deterministic sequence-aware DB double; no real or invented national IDs."""
    db = Mock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
    return db


@pytest.mark.asyncio
async def test_newborn_to_citizen_flow(sample_newborn_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    mock_citizen_service = CitizenService(mock_repo, db=_sequence_db())
    identity_service = IdentityService(mock_citizen_service, mock_repo)
    result = await identity_service.register_newborn(sample_newborn_data)
    assert result["health_number"].startswith("NB")


@pytest.mark.asyncio
async def test_foreigner_registration_flow(sample_foreigner_data):
    mock_repo = Mock()
    mock_repo.get_by_health_number = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()
    mock_citizen_service = CitizenService(mock_repo, db=_sequence_db())
    identity_service = IdentityService(mock_citizen_service, mock_repo)
    result = await identity_service.register_foreigner(sample_foreigner_data)
    assert result["health_number"].startswith("FR")


@pytest.mark.asyncio
async def test_newborn_flow_documents_provisional_number_overwrite(sample_newborn_data):
    """Known defect: returned NB number is not the persisted canonical IQ number.

    This characterization does not approve the behavior. Owner decision
    D-IDENTITY-02 is required to unify the response and persisted identifier.
    """
    repo = Mock()
    repo.get_by_health_number = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    identity_service = IdentityService(CitizenService(repo, db=_sequence_db()), repo)
    result = await identity_service.register_newborn(sample_newborn_data)
    persisted = repo.create.call_args.args[0].health_number
    assert result["health_number"].startswith("NB")
    assert re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", persisted)
    assert result["health_number"] != persisted


@pytest.mark.asyncio
async def test_foreigner_flow_documents_provisional_number_overwrite(sample_foreigner_data):
    """Known defect: returned FR number is not the persisted canonical IQ number.

    Owner decision D-IDENTITY-02 remains required; this test only records the
    current behavior and does not invent a national identifier.
    """
    repo = Mock()
    repo.get_by_health_number = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    identity_service = IdentityService(CitizenService(repo, db=_sequence_db()), repo)
    result = await identity_service.register_foreigner(sample_foreigner_data)
    persisted = repo.create.call_args.args[0].health_number
    assert result["health_number"].startswith("FR")
    assert re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", persisted)
    assert result["health_number"] != persisted
