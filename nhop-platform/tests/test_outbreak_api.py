"""End-to-end tests for the outbreak API endpoints (RBAC + happy paths)."""
from datetime import datetime, timedelta, timezone

import pytest
from app.api.v1.outbreak import router as outbreak_router
from app.core.database import Base, get_db
from app.core.trusted_context import (
    TrustedContext,
    publish,
    require_trusted_context,
)
from app.models.antibiotic_sensitivity import AntibioticSensitivity
from app.models.audit_log import AuditLog
from app.models.citizen import Citizen
from app.models.disease_case import DiseaseCase
from app.models.lab_test import LabTest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app._compat import UTC


def _as(client, role: str, actor_id: str = "operator-1") -> None:
    """Give requests a SERVER-ESTABLISHED context with this role.

    Overriding the dependency is the only way in. There is deliberately no
    header, query parameter or environment variable that does this, because
    anything reachable from outside the process is the defect being removed.
    """
    def _provider(request: Request) -> TrustedContext:
        return publish(request, TrustedContext(actor_id=actor_id, role=role))

    client.app.dependency_overrides[require_trusted_context] = _provider


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
    # Mirror production wiring: the trusted-context dependency is applied at the
    # router, not per handler. Without it a route could be reached with no
    # caller at all, which is the defect NR-127 removed.
    app.include_router(
        outbreak_router, prefix="/v1",
        dependencies=[Depends(require_trusted_context)],
    )

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


def test_no_trusted_context_is_refused(client):
    """NR-127. With no identity provider federated, the service must not act."""
    res = client.get("/v1/outbreak/alerts")
    assert res.status_code == 503
    assert "trusted caller identity" in res.json()["detail"]


def test_a_forged_role_header_confers_nothing(client):
    """The exact attack the old contract allowed: X-Role: MINISTRY."""
    res = client.get("/v1/outbreak/alerts", headers={"X-Role": "MINISTRY"})
    assert res.status_code == 503, (
        "X-Role still reaches the authorization decision; it must be inert"
    )


def test_a_forged_actor_header_confers_nothing(client):
    res = client.get(
        "/v1/outbreak/alerts",
        headers={"X-Actor-Id": "1", "X-Actor-Role": "MINISTRY", "X-Role": "ADMIN"},
    )
    assert res.status_code == 503


def test_the_wrong_role_is_refused(client):
    """Positive control for the role check itself: a real context, wrong role."""
    _as(client, "CITIZEN")
    res = client.get("/v1/outbreak/alerts")
    assert res.status_code == 403


def test_alerts_ministry_ok(client):
    _as(client, "MINISTRY")
    res = client.get("/v1/outbreak/alerts")
    assert res.status_code == 200
    body = res.json()
    assert "alerts" in body
    assert len(body["alerts"]) >= 1
    assert body["alerts"][0]["disease_code"] == "CHOLERA"
    assert body["alerts"][0]["severity"] in {"warning", "critical"}


def test_heatmap_admin_ok(client):
    _as(client, "ADMIN")
    res = client.get("/v1/outbreak/heatmap/CHOLERA?days=7")
    assert res.status_code == 200
    body = res.json()
    assert body["disease_code"] == "CHOLERA"
    assert body["days"] == 7
    assert body["total"] >= 1


def test_resistance_empty_dataset(client):
    _as(client, "MINISTRY")
    res = client.get("/v1/outbreak/resistance")
    assert res.status_code == 200
    body = res.json()
    assert body["total_pairs"] == 0
    assert body["pairs"] == []
