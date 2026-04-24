"""Shared fixtures for nhop-platform tests.

Each test gets a fresh in-memory SQLite DB so the suite can run in any order
without state leaking between modules.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make the nhop-platform package importable when pytest is invoked from the
# repo root with `pytest nhop-platform/tests`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    db_path = tmp_path / "nhop_test.db"
    monkeypatch.setenv("NHOP_DATABASE_URL", f"sqlite:///{db_path}")

    # Force a re-import so the app binds to the test DB URL.
    for mod in list(sys.modules):
        if mod.startswith("app.") or mod == "app":
            sys.modules.pop(mod)

    from app.core.database import Base, engine  # noqa: WPS433
    from app import models  # noqa: F401, WPS433  (populate metadata)
    from app.main import app  # noqa: WPS433

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

        defaults = dict(
            health_id=health_id,
            full_name="مريض اختبار",
            gender="M",
            province="Baghdad",
            chronic_diseases=[],
            allergies=[],
        )
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

        defaults = dict(
            id=uuid.uuid4(),
            name="مختبر اختبار",
            license_number=f"LIC-{uuid.uuid4().hex[:8]}",
            lab_type=LabType.private,
            province="Baghdad",
            is_active=True,
        )
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

        defaults = dict(
            id=uuid.uuid4(),
            citizen_id=citizen_id,
            lab_id=lab_id,
            sample_barcode=uuid.uuid4().hex[:12].upper(),
            test_code=test_code,
            test_name=test_code,
            category=ResultCategory.other,
            value_numeric=14.0,
            unit="g/dL",
            is_abnormal=False,
            is_critical=False,
            status=ResultStatus.final,
        )
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
