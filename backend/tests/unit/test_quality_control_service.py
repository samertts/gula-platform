from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.database import Base
from app.models.lab import Lab
from app.models.quality_control import QualityControl
from app.services import quality_control_service
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
    lab = Lab(name="QC Lab", city="Baghdad", lab_type="private", is_active=True)
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)
    return lab


class TestEvaluateWestgard:
    def test_pass_when_no_sd_and_small_deviation(self):
        result = quality_control_service.evaluate_westgard(100, 100, 0)
        assert result["status"] == "pass"
        assert result["violation"] is None

    def test_warning_when_no_sd_and_10_to_15_deviation(self):
        result = quality_control_service.evaluate_westgard(112, 100, 0)
        assert result["status"] == "warning"
        assert result["violation"] == "deviation>10%"

    def test_fail_when_no_sd_and_over_15_deviation(self):
        result = quality_control_service.evaluate_westgard(120, 100, 0)
        assert result["status"] == "fail"
        assert result["violation"] == "deviation>15%"

    def test_pass_when_z_under_2(self):
        result = quality_control_service.evaluate_westgard(100, 100, 10)
        assert result["status"] == "pass"
        assert result["violation"] is None

    def test_warning_when_z_between_2_and_3(self):
        result = quality_control_service.evaluate_westgard(125, 100, 10)
        assert result["status"] == "warning"
        assert result["violation"] == "1-2s"

    def test_fail_when_z_over_3(self):
        result = quality_control_service.evaluate_westgard(135, 100, 10)
        assert result["status"] == "fail"
        assert result["violation"] == "1-3s"

    def test_negative_z_scores(self):
        result = quality_control_service.evaluate_westgard(60, 100, 10)
        assert result["status"] == "fail"
        assert result["violation"] == "1-3s"

    def test_edge_sd_zero(self):
        result = quality_control_service.evaluate_westgard(111, 100, 0)
        assert result["status"] == "warning"

    def test_edge_sd_none(self):
        result = quality_control_service.evaluate_westgard(111, 100, None)
        assert result["status"] == "warning"

    def test_exactly_at_2_sd(self):
        result = quality_control_service.evaluate_westgard(120, 100, 10)
        assert result["status"] == "warning"

    def test_exactly_at_3_sd(self):
        result = quality_control_service.evaluate_westgard(130, 100, 10)
        assert result["status"] == "fail"


class TestQcToDict:
    def test_serializes_all_fields(self, db_session, lab):
        qc = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=102.0,
            sd=5.0,
            unit="mg/dL",
            instrument_name="Cobas-6000",
            lot_number="LOT-123",
            status="pass",
            violation=None,
            notes="ok",
            performed_by="tech1",
        )
        db_session.add(qc)
        db_session.commit()
        db_session.refresh(qc)

        d = quality_control_service.qc_to_dict(qc)
        assert d["test_code"] == "GLU"
        assert d["level"] == "normal"
        assert d["expected_value"] == 100.0
        assert d["measured_value"] == 102.0
        assert d["sd"] == 5.0
        assert d["unit"] == "mg/dL"
        assert d["instrument_name"] == "Cobas-6000"
        assert d["lot_number"] == "LOT-123"
        assert d["status"] == "pass"
        assert d["violation"] is None
        assert d["notes"] == "ok"
        assert d["performed_by"] == "tech1"
        assert "created_at" in d

    def test_created_at_isoformat(self, db_session, lab):
        qc = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=102.0,
            sd=5.0,
            performed_by="tech1",
        )
        db_session.add(qc)
        db_session.commit()
        d = quality_control_service.qc_to_dict(qc)
        assert isinstance(d["created_at"], str)
        assert "T" in d["created_at"]


class TestEvaluateWestgardFull:
    def test_passes_when_all_normal(self, db_session, lab):
        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 100, 100, 5
        )
        assert result["status"] == "pass"

    def test_fails_1_3s(self, db_session, lab):
        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 120, 100, 5
        )
        assert result["status"] == "fail"
        assert "1-3s" in result["violation"]

    def test_warning_1_2s(self, db_session, lab):
        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 111, 100, 5
        )
        assert result["status"] == "warning"
        assert "1-2s" in result["violation"]

    def test_fails_2_2s_consecutive(self, db_session, lab):
        cutoff = datetime.now(UTC) - timedelta(hours=2)
        qc = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=111.0,
            sd=5.0,
            status="pass",
            performed_by="tech1",
            created_at=cutoff,
        )
        db_session.add(qc)
        db_session.commit()

        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 112, 100, 5
        )
        assert result["status"] == "fail"
        assert "2-2s" in result["violation"]

    def test_fails_r_4s(self, db_session, lab):
        qc = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=130.0,
            sd=5.0,
            status="pass",
            performed_by="tech1",
            created_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(qc)
        db_session.commit()

        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 100, 100, 5
        )
        assert result["status"] == "fail"
        assert "R-4s" in result["violation"]

    def test_fails_4_1s(self, db_session, lab):
        for i in range(3):
            qc = QualityControl(
                lab_id=lab.id,
                test_code="GLU",
                level="normal",
                expected_value=100.0,
                measured_value=106.0,
                sd=5.0,
                status="pass",
                performed_by="tech1",
                created_at=datetime.now(UTC) - timedelta(hours=i + 1),
            )
            db_session.add(qc)
        db_session.commit()

        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 107, 100, 5
        )
        assert result["status"] == "fail"
        assert "4-1s" in result["violation"]

    def test_fails_10_x(self, db_session, lab):
        for i in range(9):
            qc = QualityControl(
                lab_id=lab.id,
                test_code="GLU",
                level="normal",
                expected_value=100.0,
                measured_value=101.0,
                sd=5.0,
                status="pass",
                performed_by="tech1",
                created_at=datetime.now(UTC) - timedelta(hours=i + 1),
            )
            db_session.add(qc)
        db_session.commit()

        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 102, 100, 5
        )
        assert result["status"] == "fail"
        assert "10-x" in result["violation"]

    def test_no_sd_fallback(self, db_session, lab):
        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 200, 100, None
        )
        assert result["status"] == "fail"

    def test_instrument_filter(self, db_session, lab):
        other = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=130.0,
            sd=5.0,
            status="pass",
            performed_by="tech1",
            instrument_name="Instrument-X",
            created_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(other)
        db_session.commit()

        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 105, 100, 5, instrument_name="Instrument-Y"
        )
        assert result["status"] == "pass"

    def test_lot_number_filter(self, db_session, lab):
        other = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=130.0,
            sd=5.0,
            status="pass",
            performed_by="tech1",
            lot_number="LOT-A",
            created_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(other)
        db_session.commit()

        result = quality_control_service.evaluate_westgard_full(
            db_session, lab.id, "GLU", "normal", 105, 100, 5, lot_number="LOT-B"
        )
        assert result["status"] == "pass"


class TestGetQcSummary:
    def test_empty_summary(self, db_session, lab):
        summary = quality_control_service.get_qc_summary(lab.id, db_session, days=7)
        assert summary["period_days"] == 7
        assert summary["tests"] == []
        assert summary["overall_pass_rate"] == 100

    def test_summary_with_data(self, db_session, lab):
        for _ in range(5):
            qc = QualityControl(
                lab_id=lab.id,
                test_code="GLU",
                level="normal",
                expected_value=100.0,
                measured_value=100.0,
                sd=5.0,
                status="pass",
                performed_by="tech1",
            )
            db_session.add(qc)

        qc_fail = QualityControl(
            lab_id=lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=120.0,
            sd=5.0,
            status="fail",
            performed_by="tech1",
        )
        db_session.add(qc_fail)
        db_session.commit()

        summary = quality_control_service.get_qc_summary(lab.id, db_session, days=7)
        assert len(summary["tests"]) == 1
        glm = summary["tests"][0]
        assert glm["test_code"] == "GLU"
        assert glm["total"] == 6
        assert glm["issues"] == 1
        assert glm["pass_rate"] == pytest.approx(83.3, rel=0.1)

    def test_lab_isolation(self, db_session, lab):
        other_lab = Lab(name="Other", city="Basra", lab_type="private", is_active=True)
        db_session.add(other_lab)
        db_session.commit()

        qc_other = QualityControl(
            lab_id=other_lab.id,
            test_code="GLU",
            level="normal",
            expected_value=100.0,
            measured_value=120.0,
            sd=5.0,
            status="fail",
            performed_by="tech1",
        )
        db_session.add(qc_other)
        db_session.commit()

        summary = quality_control_service.get_qc_summary(lab.id, db_session, days=7)
        assert summary["tests"] == []
