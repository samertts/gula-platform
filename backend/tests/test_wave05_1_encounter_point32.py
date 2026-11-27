"""Wave 05.1 point 32 — canonical function-based encounter service.

The historical ``EncounterService`` class was intentionally replaced by
module-level functions. These regressions exercise the canonical service
directly; they do not create a second encounter service or new route.
"""

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
    update_encounter,
)


def _db(encounter: Encounter | None = None) -> Mock:
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = encounter
    return db


def _synthetic_encounter() -> Encounter:
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


def test_point32_creation_persists_all_required_references() -> None:
    db = _db()
    encounter = create_encounter(
        db,
        {
            "patient_id": "synthetic-patient",
            "encounter_type": EncounterType.OUTPATIENT,
            "status": EncounterStatus.PLANNED,
            "facility_id": "synthetic-facility",
            "practitioner_id": "synthetic-practitioner",
            "organization_id": "synthetic-organization",
            "period_start": datetime.now(timezone.utc),
            "reason_description": "synthetic presenting complaint",
            "lab_id": "synthetic-lab",
        },
    )
    assert isinstance(encounter, Encounter)
    assert encounter.patient_id == "synthetic-patient"
    assert encounter.facility_id == "synthetic-facility"
    assert encounter.practitioner_id == "synthetic-practitioner"
    assert encounter.organization_id == "synthetic-organization"
    db.add.assert_called_once()
    db.flush.assert_called_once()


def test_point32_update_ignores_unknown_fields() -> None:
    encounter = _synthetic_encounter()
    update_encounter(_db(encounter), encounter.id, {"reason_description": "synthetic revised", "bogus": 1})
    assert encounter.reason_description == "synthetic revised"
    assert not hasattr(encounter, "bogus")


def test_point32_completion_and_cancellation_are_terminal() -> None:
    completed = _synthetic_encounter()
    complete_encounter(_db(completed), completed.id, "synthetic-user")
    assert completed.status == EncounterStatus.COMPLETED
    assert completed.period_end is not None

    cancelled = _synthetic_encounter()
    cancel_encounter(_db(cancelled), cancelled.id, "synthetic-user")
    assert cancelled.status == EncounterStatus.CANCELLED


def test_point32_delete_is_soft_delete_only() -> None:
    encounter = _synthetic_encounter()
    delete_encounter(_db(encounter), encounter.id)
    assert encounter.is_deleted is True


def test_point32_unknown_encounter_is_not_silently_created() -> None:
    with pytest.raises(EncounterNotFoundError):
        complete_encounter(_db(), "synthetic-missing", "synthetic-user")
