"""Shared fixtures for nhop-platform tests.

Each test gets a fresh SQLite database, so the suite can run in any order
without state leaking between modules.

Run tests from the nhop-platform directory:
    cd nhop-platform && python -m pytest tests/

NR-130. These fixtures did not work. `app_client` read `sys.modules` without
importing sys, so all ten tests that used it errored at setup, and `db_session`
was never written at all, so the eleven tests that asked for it errored too --
21 errors, two causes, and no coverage from either file since they were added.

The repair is not `import sys`. The line that would have enabled purged every
`app.*` entry from sys.modules mid-suite to rebind the app to a test database.
That is the NR-126 state-leak class: modules imported earlier keep stale
references while later imports get fresh ones, and the suite becomes
order-dependent. FastAPI already has the mechanism for this -- override the
`get_db` dependency -- so the database is swapped without touching the import
system at all.
"""
from __future__ import annotations

import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# app.core.database reads this at import time and app.main opens the database
# while being imported, so it has to be set before either is imported -- which
# is here, since conftest is imported before any test module. Without it the
# import writes ./nhop.db into whatever directory the suite was started from.
os.environ.setdefault(
    "NHOP_DATABASE_URL",
    "sqlite:///" + tempfile.mkdtemp(prefix="nhop-conftest-") + "/import-time.db",
)


@pytest.fixture()
def test_engine(tmp_path):
    """A database of this test's own, with the full schema on it."""
    import app.models
    from app.core.database import Base

    engine = create_engine(
        f"sqlite:///{tmp_path / 'nhop_test.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def session_factory(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db_session(session_factory):
    """A plain session for service-level tests that never go through HTTP."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def app_client(test_engine, session_factory):
    """The real application, with only its database redirected.

    Nothing else is substituted: the middleware, the router wiring and the
    dependencies are the ones production serves, so a test cannot pass against
    a shape the deployed app does not have.
    """
    from app.core.database import get_db
    from app.main import app

    def _override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    try:
        yield TestClient(app), session_factory
    finally:
        app.dependency_overrides.pop(get_db, None)


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

