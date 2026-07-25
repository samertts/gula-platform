"""End-to-end tests for the outbreak API endpoints (RBAC + happy paths)."""
from datetime import datetime, timedelta, timezone

import pytest
from app.api.v1.outbreak import router as outbreak_router
from app.core.database import Base, get_db
from app.models.antibiotic_sensitivity import AntibioticSensitivity
from app.models.audit_log import AuditLog
from app.models.citizen import Citizen
from app.models.disease_case import DiseaseCase
from app.models.lab_test import LabTest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from datetime import UTC


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    app = FastAPI()
    app.include_router(outbreak_router, prefix="/v1")

    def _override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db

    # Seed one critical-level outbreak.
    now = datetime.now(UTC)
    with Session() as seed:
        for i in range(60):
            seed.add(DiseaseCase(
                disease_code="CHOLERA",
                province="Basra",
                is_positive=True,
                reported_at=now - timedelta(days=1) - timedelta(hours=i * 4),
            ))
        for i in range(25):
            seed.add(DiseaseCase(
                disease_code="CHOLERA",
                province="Basra",
                is_positive=True,
                reported_at=now - timedelta(minutes=i * 30),
            ))
        seed.commit()

    try:
        yield TestClient(app)
    finally:
        engine.dispose()


def test_alerts_requires_role(client):
    res = client.get("/v1/outbreak/alerts")
    assert res.status_code == 401


def test_alerts_rejects_wrong_role(client):
    res = client.get("/v1/outbreak/alerts", headers={"X-Role": "CITIZEN"})
    assert res.status_code == 403


def test_alerts_ministry_ok(client):
    res = client.get("/v1/outbreak/alerts", headers={"X-Role": "MINISTRY"})
    assert res.status_code == 200
    body = res.json()
    assert "alerts" in body
    assert len(body["alerts"]) >= 1
    assert body["alerts"][0]["disease_code"] == "CHOLERA"
    assert body["alerts"][0]["severity"] in {"warning", "critical"}


def test_heatmap_admin_ok(client):
    res = client.get(
        "/v1/outbreak/heatmap/CHOLERA?days=7",
        headers={"X-Role": "ADMIN"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["disease_code"] == "CHOLERA"
    assert body["days"] == 7
    assert body["total"] >= 1


def test_resistance_empty_dataset(client):
    res = client.get("/v1/outbreak/resistance", headers={"X-Role": "MINISTRY"})
    assert res.status_code == 200
    body = res.json()
    assert body["total_pairs"] == 0
    assert body["pairs"] == []
