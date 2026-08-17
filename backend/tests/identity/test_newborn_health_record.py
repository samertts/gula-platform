from __future__ import annotations

from datetime import date

import pytest

from app.national.domain.citizen import Citizen
from app.national.enums import Gender
from app.national.exceptions import DuplicateNewbornRegistrationError
from app.national.repositories.citizen_repository import CitizenRepository
from app.national.services.citizen_service import CitizenService
from app.national.services.identity_service import IdentityService
from shared.identity.service import hash_national_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_newborn_record_uses_hashed_parent_lookup_and_rejects_duplicate_certificate(db, monkeypatch):
    """Only parent hashes and parent record IDs persist; raw NIDs do not."""
    hmac_key = "unit-test-nid-hmac-key"
    monkeypatch.setattr("app.national.services.identity_service.NID_HMAC_KEY", hmac_key)
    mother_nid = "123456789012"
    father_nid = "987654321098"
    mother = Citizen(
        national_id_hash=hash_national_id(mother_nid, hmac_key),
        health_number="IQPARENT000001",
        first_name="أم",
        last_name="الطفل",
        date_of_birth=date(1994, 1, 1),
        gender=Gender.FEMALE,
    )
    father = Citizen(
        national_id_hash=hash_national_id(father_nid, hmac_key),
        health_number="IQPARENT000002",
        first_name="أب",
        last_name="الطفل",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
    )
    db.add_all([mother, father])
    db.commit()

    repo = CitizenRepository(db)
    service = IdentityService(CitizenService(repo, db), repo, db)
    request_data = {
        "birth_certificate_number": "BC-2026-00001",
        "mother_national_id": mother_nid,
        "father_national_id": father_nid,
        "first_name": "طفل",
        "last_name": "الطفل",
        "date_of_birth": date(2026, 8, 1),
        "gender": "male",
        "birth_weight_grams": 3200,
        "lab_id": 1,
        "actor_id": 7,
    }

    result = await service.register_newborn(request_data)

    assert result["is_temporary"] is True
    assert result["health_number"].startswith("THN-")
    assert result["citizen"].national_id_hash is None
    assert result["citizen"].health_number == result["health_number"]

    with pytest.raises(DuplicateNewbornRegistrationError):
        await service.register_newborn(request_data)
