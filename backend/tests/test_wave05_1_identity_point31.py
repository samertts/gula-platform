"""Wave 05.1 point 31 — canonical health-number sequence regressions.

Synthetic fixtures only. These tests pin the existing ADR-012 sequence
authority without inventing an Iraqi national identifier or changing the
registration API contract.
"""

from __future__ import annotations

import re
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.national.domain.health_number import HealthNumberSequence
from app.national.services.citizen_service import CitizenService
from app.national.services.identity_service import IdentityService


def _db(existing: HealthNumberSequence | None = None) -> Mock:
    db = Mock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = existing
    return db


def _repo() -> Mock:
    repo = Mock()
    repo.get_by_health_number = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_point31_generated_number_uses_canonical_format() -> None:
    hn = await CitizenService(_repo(), db=_db())._generate_health_number()
    assert re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", hn)


@pytest.mark.asyncio
async def test_point31_existing_sequence_row_is_incremented_once() -> None:
    year = datetime.now().year
    row = HealthNumberSequence(prefix="IQ", year=year, sequence_number=7)
    db = _db(row)
    hn = await CitizenService(_repo(), db=db)._generate_health_number()
    assert hn == f"IQ{year}000008"
    assert row.sequence_number == 8
    db.add.assert_not_called()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_point31_missing_sequence_row_is_created_without_invented_id() -> None:
    year = datetime.now().year
    db = _db()
    hn = await CitizenService(_repo(), db=db)._generate_health_number()
    assert hn == f"IQ{year}000001"
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_point31_registration_persists_generated_number() -> None:
    repo = _repo()
    await CitizenService(repo, db=_db()).register_citizen(
        {
            "first_name": "Synthetic",
            "last_name": "Patient",
            "date_of_birth": "2000-01-01",
            "gender": "female",
            "phone": "SYNTHETIC",
        }
    )
    created = repo.create.call_args.args[0]
    assert re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", created.health_number)


@pytest.mark.asyncio
async def test_point31_provisional_numbers_are_not_persisted_as_canonical() -> None:
    repo = _repo()
    service = IdentityService(CitizenService(repo, db=_db()), repo)
    newborn = await service.register_newborn(
        {
            "mother_id": "synthetic-mother",
            "birth_certificate_number": "SYN-BC-001",
            "first_name": "Synthetic",
            "last_name": "Newborn",
            "date_of_birth": "2026-01-01",
            "gender": "female",
        }
    )
    foreigner = await service.register_foreigner(
        {
            "passport_number": "SYN-PASS-001",
            "passport_country": "SYNTHETIC",
            "first_name": "Synthetic",
            "last_name": "Foreigner",
            "date_of_birth": "1990-01-01",
            "gender": "male",
        }
    )
    assert newborn["health_number"].startswith("NB")
    assert foreigner["health_number"].startswith("FR")
    persisted = [call.args[0].health_number for call in repo.create.call_args_list]
    assert all(re.fullmatch(rf"IQ{datetime.now().year}\d{{6}}", value) for value in persisted)
