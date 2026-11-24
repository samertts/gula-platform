from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.national.domain.encounter import Encounter
from app.national.enums import EncounterStatus, EncounterType
from app.national.exceptions import EncounterNotFoundError
from app.national.services.encounter_service import (
    cancel_encounter,
    complete_encounter,
    create_encounter,
    delete_encounter,
    get_encounter,
    update_encounter,
)


def _db(encounter: Encounter | None = None) -> Mock:
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = encounter
    return db


def _encounter() -> Encounter:
    return Encounter(
        patient_id="synthetic-patient",
        encounter_type=EncounterType.OUTPATIENT,
        status=EncounterStatus.PLANNED,
        facility_id="synthetic-facility",
        practitioner_id="synthetic-practitioner",
        organization_id="synthetic-organization",
        period_start=datetime.now(timezone.utc),
        reason_description="synthetic presenting complaint",
        lab_id="synthetic-lab",
    )


def test_create_encounter(sample_encounter_data):
    db = _db()
    data = dict(sample_encounter_data)
    data["lab_id"] = "synthetic-lab"
    data["status"] = EncounterStatus.PLANNED
    data["encounter_type"] = EncounterType.OUTPATIENT
    data["period_start"] = datetime.now(timezone.utc)
    encounter = create_encounter(db, data)
    assert encounter is not None
    assert isinstance(encounter, Encounter)
    assert encounter.patient_id == data["patient_id"]
    assert encounter.facility_id == data["facility_id"]
    assert encounter.practitioner_id == data["practitioner_id"]
    db.add.assert_called_once()
    db.flush.assert_called_once()


def test_get_encounter_returns_existing_record():
    encounter = _encounter()
    assert get_encounter(_db(encounter), encounter.id) is encounter


def test_update_encounter_applies_known_fields_only():
    encounter = _encounter()
    db = _db(encounter)
    result = update_encounter(
        db,
        encounter.id,
        {"reason_description": "synthetic updated complaint", "unknown_field": "ignored"},
    )
    assert result is encounter
    assert encounter.reason_description == "synthetic updated complaint"
    assert not hasattr(encounter, "unknown_field")
    db.flush.assert_called_once()


def test_complete_encounter_sets_terminal_status():
    encounter = _encounter()
    db = _db(encounter)
    assert complete_encounter(db, encounter.id, "synthetic-user") is encounter
    assert encounter.status == EncounterStatus.COMPLETED
    assert encounter.period_end is not None


def test_cancel_encounter_sets_cancelled_status():
    encounter = _encounter()
    db = _db(encounter)
    assert cancel_encounter(db, encounter.id, "synthetic-user") is encounter
    assert encounter.status == EncounterStatus.CANCELLED


def test_delete_encounter_soft_deletes():
    encounter = _encounter()
    db = _db(encounter)
    delete_encounter(db, encounter.id)
    assert encounter.is_deleted is True
    db.flush.assert_called_once()


def test_unknown_encounter_raises_not_found():
    with pytest.raises(EncounterNotFoundError):
        update_encounter(_db(), "synthetic-missing", {"status": EncounterStatus.COMPLETED})
