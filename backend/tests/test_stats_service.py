from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("REDIS_URL", "")

from datetime import datetime

import pytest
from app._compat import UTC
from app.database import Base
from app.services.stats_service import _cache_key
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_cache_key_deterministic():
    k1 = _cache_key(1, "daily_trends", days=30)
    k2 = _cache_key(1, "daily_trends", days=30)
    assert k1 == k2
    assert k1.startswith("stats:1:daily_trends:")


def test_cache_key_differs_for_different_params():
    k1 = _cache_key(1, "daily_trends", days=30)
    k2 = _cache_key(1, "daily_trends", days=7)
    assert k1 != k2


def test_cache_key_differs_for_different_labs():
    k1 = _cache_key(1, "daily_trends", days=30)
    k2 = _cache_key(2, "daily_trends", days=30)
    assert k1 != k2


def test_cache_key_differs_for_different_endpoints():
    k1 = _cache_key(1, "daily_trends", days=30)
    k2 = _cache_key(1, "test_frequency", days=30)
    assert k1 != k2


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def test_stats_summary_empty(db):
    from app.services.stats_service import stats_summary
    result = stats_summary(1, db)
    assert result["totals"]["patients"] == 0
    assert result["totals"]["orders"] == 0
    assert result["totals"]["tests"] == 0
    assert result["totals"]["critical_results"] == 0
    assert result["totals"]["critical_rate_pct"] == 0
    assert result["today"]["orders"] == 0
    assert result["this_week"]["orders"] == 0
    assert result["this_month"]["orders"] == 0


def test_stats_summary_with_data(db):
    from app.models.lab import Lab
    from app.models.lab_order import LabOrder
    from app.models.patient import Patient
    from app.services.stats_service import stats_summary

    lab = Lab(id=1, name="Test Lab", is_active=True)
    db.add(lab)
    db.flush()

    patient = Patient(id=1, health_id="HD-001", full_name="P1", phone="0000000000",
                       lab_id=1, created_at=datetime.now(UTC))
    db.add(patient)
    db.flush()

    order = LabOrder(id=1, lab_id=1, patient_id=1, status="pending",
                     created_at=datetime.now(UTC))
    db.add(order)
    db.commit()

    result = stats_summary(1, db)
    assert result["totals"]["patients"] == 1
    assert result["totals"]["orders"] >= 1


def test_stats_summary_different_lab_isolation(db):
    from app.models.lab import Lab
    from app.models.patient import Patient
    from app.services.stats_service import stats_summary

    lab1 = Lab(id=10, name="Lab 1", is_active=True)
    lab2 = Lab(id=20, name="Lab 2", is_active=True)
    db.add_all([lab1, lab2])
    db.flush()

    patient = Patient(id=10, health_id="HD-010", full_name="P1", phone="0000000000",
                       lab_id=10, created_at=datetime.now(UTC))
    db.add(patient)
    db.commit()

    r1 = stats_summary(10, db)
    r2 = stats_summary(20, db)
    assert r1["totals"]["patients"] == 1
    assert r2["totals"]["patients"] == 0
