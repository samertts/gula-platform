"""Regression guard: Hospital facility-CRUD routes must durably commit.

Every route in app/routes/hospital.py except the five ClinicalCommandGuard-
based ones (assign/discharge/transfer_bed, update_ot_status,
complete_surgical_safety_checklist) never called db.commit() anywhere --
not in the route, not in HospitalService, not in log_action. get_db()
uses autocommit=False and only rolls back on exception; SQLAlchemy's
default Session.close() discards a pending (flushed-but-uncommitted)
transaction. So every create_hospital/update_hospital/deactivate_hospital/
create_campus/update_campus/create_building/create_floor/
create_department/update_department/create_clinic/create_room/
create_bed/create_unit/create_operation_theater/create_equipment/
update_equipment/create_cost_center/create_appointment call returned a
200/201 with what looked like a real created/updated record, but nothing
was durably persisted -- the very next request (a fresh SessionLocal(),
exactly matching real production per-request behavior) could not find it.

This repo's own shared-session TestClient fixture (tests/conftest.py's
`client`, which yields the SAME db object for every request in a test)
completely masks this bug, since a flush is visible to later queries on
the same open session/transaction regardless of whether it was ever
committed. This test deliberately does NOT use that fixture -- it drives
two genuinely independent sessions against a real file-backed SQLite DB,
matching how two separate production requests would actually behave.

Fixed with an explicit db.commit() in each affected route, right after
the service call, matching the exact pattern already used by
_run_hospital_command (the two ClinicalCommandGuard-based commits that
already existed in this file).
"""
from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.security.auth import create_token
from shared.auth.passwords import hash_password


@pytest.fixture()
def two_session_world(monkeypatch):
    """A real file-backed SQLite DB with the app wired to make a genuinely
    fresh SessionLocal() per request (unlike the shared `client` fixture),
    plus one independent verification session opened after the app is done.
    """
    import app.database as _database

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

        # Build the exact same combined DDL metadata tests/conftest.py uses,
        # reusing its already-imported model registrations and JSONB/BigInteger
        # SQLite compile shims (registered as tests.conftest's own import-time
        # side effect) rather than re-deriving them.
        import tests.conftest as _conftest  # noqa: F401
        from app.database import Base
        from app.care_continuum.base import CareContinuumBase
        from app.citizen_platform.base import CitizenPlatformBase
        from app.clinical.base import ClinicalBase
        from app.ehr.base import EHRBase
        from app.financial.models import FinBase
        from app.governance.base import GovernanceBase
        from app.health_data.base import HealthDataBase
        from app.hospital.base import HospitalBase
        from app.national.base import NationalBase
        from app.national_data.base import DataPlatformBase
        from app.nhdw.base import NHDWBase
        from app.nursing.base import NursingBase
        from app.pharmacy.base import PharmacyBase
        from app.radiology.base import RadiologyBase
        from app.trust.base import TrustBase
        from sqlalchemy import MetaData

        all_metas = [
            Base.metadata, NationalBase.metadata, EHRBase.metadata,
            CareContinuumBase.metadata, CitizenPlatformBase.metadata,
            ClinicalBase.metadata, GovernanceBase.metadata,
            HealthDataBase.metadata, HospitalBase.metadata,
            DataPlatformBase.metadata, NHDWBase.metadata,
            NursingBase.metadata, PharmacyBase.metadata,
            RadiologyBase.metadata, TrustBase.metadata, FinBase.metadata,
        ]
        ddl_meta = MetaData()
        for meta in all_metas:
            for tname, tbl in list(meta.tables.items()):
                if tname not in ddl_meta.tables:
                    tbl.to_metadata(ddl_meta)
        for tbl in list(ddl_meta.tables.values()):
            seen = {}
            for idx in list(tbl.indexes):
                if idx.name in seen:
                    tbl.indexes.discard(idx)
                else:
                    seen[idx.name] = idx
        ddl_meta.create_all(engine)

        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        monkeypatch.setattr(_database, "SessionLocal", session_factory, raising=True)
        monkeypatch.setattr(_database, "engine", engine, raising=True)

        # Seed a lab + admin user via a short-lived, committed session.
        from app.models.lab import Lab
        from app.models.lab_user import LabUser

        seed = session_factory()
        lab = Lab(name="Durable Commit Lab", license_number="LIC-DC-1", lab_type="private",
                  city="Baghdad", is_active=True)
        seed.add(lab)
        seed.commit()
        admin = LabUser(lab_id=lab.id, email="admin@durablecommit.gula", name="Admin",
                         password_hash=hash_password("password123"), role="admin", is_active=True)
        seed.add(admin)
        seed.commit()
        lab_id, admin_id = lab.id, admin.id
        seed.close()

        token = create_token({"user_id": admin_id, "lab_id": lab_id, "role": "admin"})

        from app.main import app

        with TestClient(app, raise_server_exceptions=True) as http:
            yield {"client": http, "token": token, "engine": engine}
    finally:
        os.unlink(db_path)


def _verify_row_exists(engine, model, row_id) -> bool:
    """Open a brand new session/connection -- not the one the app used."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        return session.query(model).filter(model.id == row_id).first() is not None
    finally:
        session.close()


def test_create_hospital_is_durably_committed(two_session_world):
    from app.hospital.models import HospitalMaster

    client, token, engine = (
        two_session_world["client"], two_session_world["token"], two_session_world["engine"],
    )
    resp = client.post(
        "/hospital/",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "DC1", "name": "Durable Commit Hospital", "hospital_type": "general"},
    )
    assert resp.status_code == 201, resp.text
    hospital_id = resp.json()["id"]

    assert _verify_row_exists(engine, HospitalMaster, hospital_id), (
        "create_hospital returned 201 but the row was not durably committed -- "
        "a second, independent session cannot see it"
    )


def test_create_department_is_visible_to_the_next_independent_request(two_session_world):
    """The real-world shape of the bug: request 1 creates a hospital,
    request 2 (a genuinely separate SessionLocal(), matching production)
    must be able to see it -- not just the same in-memory Python object."""
    client, token = two_session_world["client"], two_session_world["token"]

    create_resp = client.post(
        "/hospital/",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "DC2", "name": "Durable Commit Hospital 2", "hospital_type": "general"},
    )
    assert create_resp.status_code == 201, create_resp.text
    hospital_id = create_resp.json()["id"]

    dept_resp = client.post(
        f"/hospital/{hospital_id}/departments",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "DCD1", "name": "Durable Commit Department"},
    )
    assert dept_resp.status_code == 201, (
        f"expected the hospital created in the prior request to be visible; got {dept_resp.text}"
    )


def test_update_campus_is_durably_committed(two_session_world):
    from app.hospital.models import Campus

    client, token, engine = (
        two_session_world["client"], two_session_world["token"], two_session_world["engine"],
    )
    h = client.post(
        "/hospital/", headers={"Authorization": f"Bearer {token}"},
        json={"code": "DC3", "name": "H3", "hospital_type": "general"},
    ).json()
    campus = client.post(
        f"/hospital/{h['id']}/campuses", headers={"Authorization": f"Bearer {token}"},
        json={"code": "CDC3", "name": "Campus DC3"},
    ).json()

    resp = client.put(
        f"/hospital/campuses/{campus['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "CDC3", "name": "Renamed Campus"},
    )
    assert resp.status_code == 200, resp.text

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    verify = Session()
    try:
        row = verify.query(Campus).filter(Campus.id == campus["id"]).first()
        assert row is not None
        assert row.name == "Renamed Campus"
    finally:
        verify.close()
