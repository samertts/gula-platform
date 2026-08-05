"""Unit tests for patient_service — direct service layer tests.

Covers: patient_to_dict, PatientDict.to_dict, list_patients, get_patient_by_id,
create_patient (duplicates, guardian validation, force_create), update_patient,
get_family_members, get_patient_children, _check_duplicates, _resolve_mpi.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from datetime import date

import pytest
from app.database import Base
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.patient import Patient
from app.services import patient_service
from app.services.identity import hash_family_id, hash_national_id
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def lab(db_session):
    lab = Lab(name="Test Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


@pytest.fixture
def patient(lab, db_session):
    p = Patient(
        lab_id=lab.id,
        full_name="Ahmed Ali",
        phone="07701112222",
        birth_date=date(1990, 5, 15),
        gender="male",
        email="ahmed@test.com",
        health_id="GULA-TEST123",
        national_id_hash=hash_national_id("1000100010001"),
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


class _Citizen:
    def __init__(self, ulid):
        self.citizen_ulid = ulid


class _Outcome:
    def __init__(self, ulid, method):
        self.citizen = _Citizen(ulid)
        self.match_method = method


# ─── Serialization ────────────────────────────────────────────────────────────


def test_patient_to_dict_maps_fields(patient):
    d = patient_service.patient_to_dict(patient)
    assert d["id"] == patient.id
    assert d["full_name"] == "Ahmed Ali"
    assert d["phone"] == "07701112222"
    assert d["birth_date"] == "1990-05-15"
    assert d["has_national_id"] is True
    assert d["has_family_id"] is False
    assert d["created_at"] is not None


def test_patient_to_dict_without_hashes(db_session, lab):
    p = Patient(
        lab_id=lab.id,
        full_name="No Hashes",
        phone="07700000000",
        birth_date=None,
    )
    db_session.add(p)
    db_session.flush()
    d = patient_service.patient_to_dict(p)
    assert d["has_national_id"] is False
    assert d["has_family_id"] is False
    assert d["birth_date"] is None


def test_patient_dict_dto_roundtrip():
    dto = patient_service.PatientDict(
        id=1,
        full_name="A",
        phone="1",
        birth_date=None,
        gender=None,
        email=None,
        health_id=None,
        is_minor=None,
        guardian_id=None,
        has_national_id=False,
        has_family_id=False,
        created_at=None,
    )
    d = dto.to_dict()
    assert d["id"] == 1
    assert d["full_name"] == "A"
    assert "guardian_id" in d
    assert "created_at" in d


# ─── list_patients ────────────────────────────────────────────────────────────


def test_list_patients_empty(db_session, lab):
    res = patient_service.list_patients(db_session, lab.id)
    assert res == {"total": 0, "patients": []}


def test_list_patients_filters_by_lab(db_session, lab, patient):
    other = Lab(name="Other", city="Basra", lab_type="public", is_active=True)
    db_session.add(other)
    db_session.commit()
    Patient(
        lab_id=other.id,
        full_name="Other Patient",
        phone="07801112222",
    )
    db_session.commit()

    res = patient_service.list_patients(db_session, lab.id)
    assert res["total"] == 1
    assert res["patients"][0]["full_name"] == "Ahmed Ali"


def test_list_patients_search_by_phone(db_session, lab, patient):
    res = patient_service.list_patients(db_session, lab.id, search="0770111")
    assert res["total"] == 1


def test_list_patients_search_by_name(db_session, lab, patient):
    res = patient_service.list_patients(db_session, lab.id, search="ahmed")
    assert res["total"] == 1


def test_list_patients_search_no_match(db_session, lab, patient):
    res = patient_service.list_patients(db_session, lab.id, search="zzz")
    assert res["total"] == 0


def test_list_patients_pagination(db_session, lab):
    for i in range(5):
        db_session.add(
            Patient(lab_id=lab.id, full_name=f"Patient {i}", phone=f"0770000000{i}"),
        )
    db_session.commit()

    res = patient_service.list_patients(db_session, lab.id, skip=1, limit=2)
    assert res["total"] == 5
    assert len(res["patients"]) == 2


# ─── get_patient_by_id ────────────────────────────────────────────────────────


def test_get_patient_by_id_found(db_session, lab, patient):
    d = patient_service.get_patient_by_id(db_session, patient.id, lab.id)
    assert d is not None
    assert d["full_name"] == "Ahmed Ali"


def test_get_patient_by_id_missing(db_session, lab, patient):
    assert patient_service.get_patient_by_id(db_session, 9999, lab.id) is None


def test_get_patient_by_id_lab_isolation(db_session, lab, patient):
    other = Lab(name="Other", city="Basra", lab_type="public", is_active=True)
    db_session.add(other)
    db_session.commit()
    assert patient_service.get_patient_by_id(db_session, patient.id, other.id) is None


# ─── create_patient ───────────────────────────────────────────────────────────


def test_create_patient_success(db_session, lab):
    with patch("app.services.patient_service.log_action"), patch(
        "app.services.patient_service.mpi_resolver"
    ) as mpi:
        mpi.resolve_identity.return_value = _Outcome("ULID123", "new")
        res = patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Zahra Hassan",
            phone="07703334444",
            birth_date=date(1985, 1, 1),
            gender="female",
        )

    assert res["message"] == "Patient created"
    assert res["patient"]["full_name"] == "Zahra Hassan"
    assert res["patient"]["citizen_ulid"] == "ULID123"
    assert res["patient"]["mpi_match_method"] == "new"
    assert res["patient"]["health_id"].startswith("GULA-")


def test_create_patient_hashes_identifiers(db_session, lab):
    with patch("app.services.patient_service.log_action"), patch(
        "app.services.patient_service.mpi_resolver"
    ) as mpi:
        mpi.resolve_identity.return_value = _Outcome("U1", "new")
        patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Test Person",
            phone="07700001111",
            national_id="1000100020002",
            family_id="123456789",
        )

    saved = db_session.query(Patient).filter(Patient.full_name == "Test Person").first()
    assert saved.national_id_hash == hash_national_id("1000100020002")
    assert saved.family_id_hash == hash_family_id("123456789")


def test_create_patient_duplicate_national_id(db_session, lab, patient):
    with patch("app.services.patient_service.log_action"):
        res = patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Ahmed Ali",
            phone="07999999999",
            national_id="1000100010001",
        )

    assert res["status_code"] == 409
    assert res["error"]["duplicate"] is True
    assert "national ID" in res["error"]["message"]


def test_create_patient_duplicate_name_phone(db_session, lab, patient):
    with patch("app.services.patient_service.log_action"):
        res = patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Ahmed Ali",
            phone="07701112222",
            birth_date=date(1990, 5, 15),
        )

    assert res["status_code"] == 409
    assert res["error"]["duplicate"] is True
    assert res["error"]["matches"][0]["score"] >= 0.65


def test_create_patient_force_create_bypasses_duplicates(db_session, lab, patient):
    with patch("app.services.patient_service.log_action"), patch(
        "app.services.patient_service.mpi_resolver"
    ) as mpi:
        mpi.resolve_identity.return_value = _Outcome("U2", "new")
        res = patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Ahmed Ali",
            phone="07701112222",
            birth_date=date(1990, 5, 15),
            force_create=True,
        )

    assert res["message"] == "Patient created"
    count = db_session.query(Patient).filter(Patient.full_name == "Ahmed Ali").count()
    assert count == 2


def test_create_patient_guardian_not_found(db_session, lab):
    with patch("app.services.patient_service.log_action"):
        res = patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Minor Child",
            phone="07702223333",
            guardian_id=9999,
        )

    assert res["status_code"] == 404
    assert "Guardian" in res["error"]


def test_create_patient_valid_guardian(db_session, lab, patient):
    with patch("app.services.patient_service.log_action"), patch(
        "app.services.patient_service.mpi_resolver"
    ) as mpi:
        mpi.resolve_identity.return_value = _Outcome("U3", "new")
        res = patient_service.create_patient(
            db_session,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Minor Child",
            phone="07702223333",
            guardian_id=patient.id,
        )

    assert res["message"] == "Patient created"
    assert res["patient"]["guardian_id"] == patient.id


# ─── update_patient ───────────────────────────────────────────────────────────


def test_update_patient_not_found(db_session, lab):
    with patch("app.services.patient_service.log_action"):
        res = patient_service.update_patient(
            db_session, 9999, lab.id, user_id=1, user_role="admin", full_name="X"
        )
    assert res["status_code"] == 404


def test_update_patient_fields(db_session, lab, patient):
    with patch("app.services.patient_service.log_action") as log:
        res = patient_service.update_patient(
            db_session,
            patient.id,
            lab.id,
            user_id=1,
            user_role="admin",
            full_name="Updated Name",
            phone="07709999999",
        )

    assert res["message"] == "Patient updated"
    assert res["patient"]["full_name"] == "Updated Name"
    log.assert_called_once()
    assert "Updated fields: full_name, phone" in log.call_args.kwargs["details"]


def test_update_patient_family_id_hash(db_session, lab, patient):
    with patch("app.services.patient_service.log_action"):
        res = patient_service.update_patient(
            db_session,
            patient.id,
            lab.id,
            user_id=1,
            user_role="admin",
            family_id="555444333",
        )

    db_session.refresh(patient)
    assert patient.family_id_hash == hash_family_id("555444333")
    assert res["patient"]["has_family_id"] is True


# ─── get_family_members ───────────────────────────────────────────────────────


def test_get_family_members_invalid_id(db_session, lab):
    res = patient_service.get_family_members(db_session, "abc!def", lab.id)
    assert res["status_code"] == 400


def test_get_family_members_no_members(db_session, lab):
    res = patient_service.get_family_members(db_session, "123456789", lab.id)
    assert res["status_code"] == 404


def test_get_family_members_lists_members_with_order_stats(db_session, lab):
    db_session.add(Patient(
        lab_id=lab.id, full_name="Member One", phone="07700000001",
        family_id_hash=hash_family_id("123456789"), birth_date=date(1980, 1, 1),
    ))
    db_session.add(Patient(
        lab_id=lab.id, full_name="Member Two", phone="07700000002",
        family_id_hash=hash_family_id("123456789"), birth_date=date(1990, 1, 1),
    ))
    db_session.flush()

    members = (
        db_session.query(Patient)
        .filter(Patient.family_id_hash == hash_family_id("123456789"))
        .all()
    )
    m = members[0]
    order = LabOrder(patient_id=m.id, lab_id=lab.id, status="completed")
    db_session.add(order)
    db_session.commit()

    res = patient_service.get_family_members(db_session, "123456789", lab.id)
    assert res["family_member_count"] == 2
    by_name = {x["full_name"]: x for x in res["members"]}
    assert by_name["Member One"]["order_count"] == 1
    assert by_name["Member Two"]["order_count"] == 0


# ─── get_patient_children ─────────────────────────────────────────────────────


def test_get_patient_children_guardian_not_found(db_session, lab):
    res = patient_service.get_patient_children(db_session, 9999, lab.id)
    assert res["status_code"] == 404


def test_get_patient_children_returns_minors(db_session, lab, patient):
    db_session.add(Patient(
        lab_id=lab.id, full_name="Child One", phone="07700000003",
        guardian_id=patient.id, birth_date=date(2015, 1, 1),
    ))
    db_session.add(Patient(
        lab_id=lab.id, full_name="Child Two", phone="07700000004",
        guardian_id=patient.id, birth_date=date(2018, 1, 1),
    ))
    db_session.commit()

    res = patient_service.get_patient_children(db_session, patient.id, lab.id)
    assert res["guardian"]["full_name"] == "Ahmed Ali"
    assert res["children_count"] == 2
    assert len(res["children"]) == 2


def test_get_patient_children_excludes_other_guardians(db_session, lab, patient):
    other = Patient(
        lab_id=lab.id, full_name="Other Guardian", phone="07700000005",
    )
    db_session.add(other)
    db_session.flush()
    db_session.add(Patient(
        lab_id=lab.id, full_name="Not My Child", phone="07700000006",
        guardian_id=other.id,
    ))
    db_session.commit()

    res = patient_service.get_patient_children(db_session, patient.id, lab.id)
    assert res["children_count"] == 0


# ─── _check_duplicates ────────────────────────────────────────────────────────


def test_check_duplicates_none(db_session, lab):
    result = patient_service._check_duplicates(
        db_session, lab.id, "New Person", "07705556666", "2000-01-01", None
    )
    assert result is None


def test_check_duplicates_matches_by_national_id(db_session, lab, patient):
    result = patient_service._check_duplicates(
        db_session, lab.id, "Whoever", "07707777777", "2001-01-01",
        hash_national_id("1000100010001"),
    )
    assert result is not None
    assert result["status_code"] == 409


def test_check_duplicates_low_score_not_reported(db_session, lab):
    db_session.add(Patient(
        lab_id=lab.id, full_name="Different Person", phone="07701118888",
        birth_date=date(1970, 1, 1),
    ))
    db_session.commit()
    result = patient_service._check_duplicates(
        db_session, lab.id, "Different Person", "07702223333", "2000-01-01", None
    )
    assert result is None


# ─── _resolve_mpi ─────────────────────────────────────────────────────────────


def test_resolve_mpi_success(db_session, lab, patient):
    fake = Mock()
    fake.resolve_identity.return_value = _Outcome("ULID-FAM", "nid_exact")

    with patch("app.services.patient_service.mpi_resolver", fake), patch(
        "app.services.patient_service.log_action"
    ):
        ulid, method = patient_service._resolve_mpi(
            db_session, patient, "1000100010001", None, 1, lab.id,
        )

    assert ulid == "ULID-FAM"
    assert method == "nid_exact"
    fake.resolve_identity.assert_called_once()


def test_resolve_mpi_failure_logs_and_returns_none(db_session, lab, patient):
    fake = Mock()
    fake.resolve_identity.side_effect = RuntimeError("mpi down")

    with patch("app.services.patient_service.mpi_resolver", fake), patch(
        "app.services.patient_service.log_action"
    ) as log:
        ulid, method = patient_service._resolve_mpi(
            db_session, patient, None, None, 1, lab.id,
        )

    assert ulid is None
    assert method is None
    log.assert_called_once()
    assert log.call_args.kwargs["action"] == "mpi_resolve_failed"
