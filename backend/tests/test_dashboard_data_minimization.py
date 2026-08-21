from __future__ import annotations

import os
import uuid

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import create_token, hash_password


@pytest.fixture()
def dashboard_db():
    # Import model modules with relationship targets before creating metadata.
    import app.models.audit_log  # noqa: F401
    import app.models.claim  # noqa: F401
    import app.models.consent  # noqa: F401
    import app.models.outbox  # noqa: F401
    import app.models.quality_control  # noqa: F401
    import app.models.sample  # noqa: F401
    import app.models.subscription  # noqa: F401
    import app.models.user  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def dashboard_client(dashboard_db):
    def override_db():
        yield dashboard_db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_dashboard_does_not_expose_public_result_token(dashboard_client, dashboard_db):
    lab = Lab(name="Minimization Test Lab", is_active=True)
    dashboard_db.add(lab)
    dashboard_db.flush()

    user = LabUser(
        lab_id=lab.id,
        name="Dashboard Admin",
        email=f"dashboard-{uuid.uuid4().hex[:10]}@example.test",
        password_hash=hash_password("Test1234"),
        role="admin",
        is_active=True,
    )
    patient = Patient(
        lab_id=lab.id,
        full_name="Synthetic Patient",
        phone="07700000000",
    )
    dashboard_db.add_all([user, patient])
    dashboard_db.flush()

    order = LabOrder(
        patient_id=patient.id,
        lab_id=lab.id,
        status="completed",
    )
    dashboard_db.add(order)
    dashboard_db.flush()

    public_token = "public-result-credential-that-must-not-leak"
    result = LabResult(
        order_id=order.id,
        test_name="Potassium",
        value=6.8,
        unit="mmol/L",
        flag="critical",
        token=public_token,
    )
    dashboard_db.add(result)
    dashboard_db.commit()

    token = create_token({"user_id": user.id, "lab_id": lab.id, "role": "admin", "account_kind": "lab"})
    response = dashboard_client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["abnormal_results"][0]["test_name"] == "Potassium"
    assert "token" not in body["abnormal_results"][0]
    assert public_token not in response.text
