from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.national.base import NationalBase
from app.national.enums import EncounterType
from app.national.services.encounter_service import (
    create_encounter,
    get_encounter,
    get_encounters_by_patient,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    NationalBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def encounter_data(sample_encounter_data):
    data = dict(sample_encounter_data)
    data["period_start"] = datetime.fromisoformat(data["period_start"])
    data["encounter_type"] = EncounterType(data["encounter_type"])
    data.setdefault("lab_id", "LAB001")
    return data


def test_create_encounter(db_session, encounter_data):
    encounter = create_encounter(db_session, encounter_data)
    assert encounter is not None
    assert encounter.id
    assert encounter.patient_id == "PAT001"
    assert encounter.encounter_type.value == "outpatient"


def test_get_encounter(db_session, encounter_data):
    created = create_encounter(db_session, encounter_data)
    fetched = get_encounter(db_session, created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_encounters_by_patient(db_session, encounter_data):
    create_encounter(db_session, encounter_data)
    rows = get_encounters_by_patient(db_session, "PAT001")
    assert len(rows) == 1
    assert rows[0].patient_id == "PAT001"
