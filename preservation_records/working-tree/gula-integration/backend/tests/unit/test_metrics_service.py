from __future__ import annotations

import os
import time

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from datetime import date, datetime, timedelta

import pytest
from app.database import Base
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.patient import Patient
from app.services import metrics_service
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
    lab = Lab(name="Metrics Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


class TestGetUptimeS:
    def test_uptime_positive(self):
        uptime = metrics_service.get_uptime_s()
        assert uptime >= 0
        assert isinstance(uptime, int)

    def test_uptime_increases(self):
        u1 = metrics_service.get_uptime_s()
        time.sleep(0.01)
        u2 = metrics_service.get_uptime_s()
        assert u2 >= u1


class TestGetRssMb:
    def test_returns_float(self):
        rss = metrics_service.get_rss_mb()
        assert isinstance(rss, float)
        assert rss >= 0


class TestPingDb:
    def test_ping_success(self, db_session):
        ok, ms = metrics_service.ping_db(db_session)
        assert ok is True
        assert ms >= 0

    def test_ping_returns_ms(self, db_session):
        ok, ms = metrics_service.ping_db(db_session)
        assert ok is True
        assert isinstance(ms, float)


class TestGetOrderStats:
    def test_empty_stats(self, db_session):
        stats = metrics_service.get_order_stats(db_session, None)
        assert stats["orders_total"] == 0
        assert stats["orders_today"] == 0
        assert stats["validated_total"] == 0
        assert stats["validated_today"] == 0
        assert stats["pending"] == 0

    def test_stats_with_orders(self, db_session, lab):
        patient = Patient(lab_id=lab.id, full_name="P1", phone="07700000000", gender="M")
        db_session.add(patient)
        db_session.commit()

        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db_session.add(order)
        db_session.commit()

        stats = metrics_service.get_order_stats(db_session, None)
        assert stats["orders_total"] == 1
        assert stats["pending"] == 1

    def test_lab_filtered_stats(self, db_session, lab):
        other_lab = Lab(name="Other", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()

        patient = Patient(lab_id=lab.id, full_name="P1", phone="07700000000", gender="M")
        db_session.add(patient)
        db_session.commit()

        order1 = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        order2 = LabOrder(lab_id=other_lab.id, patient_id=patient.id, status="pending")
        db_session.add_all([order1, order2])
        db_session.commit()

        stats_lab = metrics_service.get_order_stats(db_session, lab.id)
        stats_all = metrics_service.get_order_stats(db_session, None)
        assert stats_lab["orders_total"] == 1
        assert stats_all["orders_total"] == 2

    def test_validated_counts(self, db_session, lab):
        patient = Patient(lab_id=lab.id, full_name="P1", phone="07700000000", gender="M")
        db_session.add(patient)
        db_session.commit()

        validated = LabOrder(
            lab_id=lab.id, patient_id=patient.id, status="validated", validated_at=datetime.now(),
            created_at=datetime.now(),
        )
        pending = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db_session.add_all([validated, pending])
        db_session.commit()

        stats = metrics_service.get_order_stats(db_session, lab.id)
        assert stats["validated_total"] == 1
        assert stats["validated_today"] == 1
        assert stats["pending"] == 1


class TestGetJsonMetrics:
    def test_returns_dict(self, db_session):
        metrics = metrics_service.get_json_metrics(db_session, lab_id=None, is_wide=True)
        assert isinstance(metrics, dict)
        assert "uptime_s" in metrics
        assert "uptime_h" in metrics
        assert "memory_mb" in metrics
        assert "db" in metrics
        assert "redis" in metrics
        assert "stats" in metrics
        assert "scope" in metrics
        assert "timestamp" in metrics

    def test_platform_scope(self, db_session):
        metrics = metrics_service.get_json_metrics(db_session, lab_id=None, is_wide=True)
        assert metrics["scope"] == "platform"

    def test_lab_scope(self, db_session, lab):
        metrics = metrics_service.get_json_metrics(db_session, lab_id=lab.id, is_wide=False)
        assert metrics["scope"] == "lab"

    def test_db_status(self, db_session):
        metrics = metrics_service.get_json_metrics(db_session, lab_id=None, is_wide=True)
        assert "status" in metrics["db"]
        assert "ok" in metrics["db"]
        assert "ping_ms" in metrics["db"]

    def test_redis_available_in_test_mode(self, db_session):
        metrics = metrics_service.get_json_metrics(db_session, lab_id=None, is_wide=True)
        assert "ok" in metrics["redis"]
        assert "ping_ms" in metrics["redis"]


class TestBuildHealthStatus:
    def test_ready_false_while_startup_guard_not_ready(self):
        from app.core import startup_guard
        from app.services.metrics_service import build_health_status

        saved = startup_guard.system_ready
        startup_guard.system_ready = False
        try:
            payload = build_health_status()
            assert payload["system_ready"] is False
        finally:
            startup_guard.system_ready = saved

    def test_ready_reflects_startup_guard(self):
        from app.core import startup_guard
        from app.services.metrics_service import build_health_status

        saved = startup_guard.system_ready
        startup_guard.system_ready = True
        try:
            payload = build_health_status()
            assert payload["system_ready"] is True
        finally:
            startup_guard.system_ready = saved
