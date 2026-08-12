from __future__ import annotations

import pytest

from app.national.services.encounter_service import EncounterService


@pytest.mark.asyncio
async def test_create_encounter(sample_encounter_data):
    service = EncounterService()
    encounter = await service.create_encounter(sample_encounter_data)
    assert encounter is not None
