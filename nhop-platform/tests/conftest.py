"""Shared fixtures for nhop-platform tests.

Each test gets a fresh in-memory SQLite DB so the suite can run in any order
without state leaking between modules.

Run tests from the nhop-platform directory:
    cd nhop-platform && python -m pytest tests/
"""
from __future__ import annotations

import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    db_path = tmp_path / "nhop_test.db"
    monkeypatch.setenv("NHOP_DATABASE_URL", f"sqlite:///{db_path}")

    # Force a re-import so the app binds to the test DB URL.
    for mod in list(sys.modules):
        if mod.startswith("app.") or mod == "app":
            sys.modules.pop(mod)

    from app import models
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    client = TestClient(app)
    yield client, TestingSession

    Base.metadata.drop_all(engine)


@pytest.fixture()
def make_citizen():
    """Factory that registers a citizen directly via the session."""
    def _make(session, *, health_id="HID-TEST-001", **overrides):
        from app.models.citizen import Citizen

        defaults = {
            "health_id": health_id,
            "full_name": "مريض اختبار",
            "gender": "M",
            "province": "Baghdad",
            "chronic_diseases": [],
            "allergies": [],
        }
        defaults.update(overrides)
        citizen = Citizen(**defaults)
        session.add(citizen)
        session.commit()
        session.refresh(citizen)
        return citizen

    return _make


@pytest.fixture()
def make_lab():
    def _make(session, **overrides):
        from app.models.lab import Lab, LabType

        defaults = {
            "id": uuid.uuid4(),
            "name": "مختبر اختبار",
            "license_number": f"LIC-{uuid.uuid4().hex[:8]}",
            "lab_type": LabType.private,
            "province": "Baghdad",
            "is_active": True,
        }
        defaults.update(overrides)
        lab = Lab(**defaults)
        session.add(lab)
        session.commit()
        session.refresh(lab)
        return lab

    return _make


@pytest.fixture()
def make_result():
    def _make(session, *, citizen_id, lab_id, test_code="HGB", **overrides):
        from app.models.test_result import ResultCategory, ResultStatus, TestResult

        defaults = {
            "id": uuid.uuid4(),
            "citizen_id": citizen_id,
            "lab_id": lab_id,
            "sample_barcode": uuid.uuid4().hex[:12].upper(),
            "test_code": test_code,
            "test_name": test_code,
            "category": ResultCategory.other,
            "value_numeric": 14.0,
            "unit": "g/dL",
            "is_abnormal": False,
            "is_critical": False,
            "status": ResultStatus.final,
        }
        defaults.update(overrides)
        row = TestResult(**defaults)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    return _make


@pytest.fixture()
def doctor_headers():
    return {"X-Actor-Role": "DOCTOR", "X-Actor-Id": "dr-001"}


@pytest.fixture()
def admin_headers():
    """core.rbac.require_roles reads X-Role (distinct from doctor.py's own
    X-Actor-Role scheme) — ADMIN is accepted by every require_roles(...)
    gate in citizens.py and test_results.py."""
    return {"X-Role": "ADMIN"}


@pytest.fixture()
def db_session():
    """Bare SQLAlchemy session against a fresh in-memory SQLite DB.

    For service-layer unit tests that talk to the ORM directly, without
    going through the FastAPI app (see ``app_client`` for that).
    """
    from app.core.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app import models  # noqa: F401  (populate Base.metadata)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
