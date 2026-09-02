from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.security.dependencies import get_current_user


def test_reservation_http_route_requires_idempotency_key() -> None:
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7001, lab_id=991004, role="blood_bank_technician", perm_version=1, is_active=True, is_verified=True
    )
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/blood-bank/reservations",
                json={"unit_id": "synthetic-unit", "order_id": "synthetic-order", "patient_id": "synthetic-patient", "facility_id": "FACILITY-A"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "idempotency_key_required"
