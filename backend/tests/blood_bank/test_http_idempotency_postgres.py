from __future__ import annotations

import os
import threading
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.blood_bank.domain.enums import ComponentStatus, CrossmatchStatus
from app.clinical.command_guard import ClinicalCommandGuard
from app.blood_bank.infrastructure.models import (
    BloodReservationModel,
    BloodUnitModel,
    BloodRequestModel,
    CrossmatchModel,
    InventoryMovementModel,
)
from app.database import get_db
from app.models.clinical_command import ClinicalCommandReceipt
from app.main import app
from app.security.dependencies import get_current_user

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")

LAB_ID = 991010
ACTOR_ID = 7010
FACILITY_ID = "FACILITY-HTTP-A"
UNIT_ID = "http-replay-unit"
PATIENT_ID = "synthetic-http-patient"


def _session_factory():
    return sessionmaker(bind=create_engine(POSTGRES_URL, future=True, pool_size=8, max_overflow=0), expire_on_commit=False)


def _prepare_issue(Session) -> tuple[str, str]:
    request_id = "http-issue-request"
    issue_unit_id = "http-issue-unit"
    now = datetime.now(UTC)
    with Session() as session:
        session.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(BloodRequestModel).filter(BloodRequestModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(BloodUnitModel).filter(BloodUnitModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.commit()
    engine = Session.kw["bind"]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"), {"id": LAB_ID, "name": "Synthetic HTTP Blood Bank Lab"})
        conn.execute(text("INSERT INTO lab_users (id, lab_id, name, email, password_hash, role, is_active, perm_version) VALUES (:id, :lab_id, :name, :email, :password_hash, :role, true, 1) ON CONFLICT (id) DO NOTHING"), {"id": ACTOR_ID, "lab_id": LAB_ID, "name": "Synthetic HTTP Verifier", "email": "http-verifier@example.invalid", "password_hash": "!synthetic-only", "role": "master_admin"})
    with Session() as session:
        session.add(BloodRequestModel(id=request_id, lab_id=LAB_ID, patient_id=PATIENT_ID, patient_name="Synthetic Patient", facility_id=FACILITY_ID, blood_group="O", rh_factor="positive", component="packed_rbc", units_requested=1, fulfilled_units=0, status="pending", requested_by=str(ACTOR_ID)))
        session.add(BloodUnitModel(id=issue_unit_id, lab_id=LAB_ID, facility_id=FACILITY_ID, blood_group="O", rh_factor="positive", component="packed_rbc", status=ComponentStatus.AVAILABLE.value, screening_complete=True, processing_complete=True, storage_location="cold-room-http", expiry_date=now + timedelta(days=10)))
        session.commit()
    return request_id, issue_unit_id


def _prepare_issued(Session) -> str:
    issued_unit_id = "http-issued-id-or-unit"
    now = datetime.now(UTC)
    with Session() as session:
        session.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(BloodUnitModel).filter(BloodUnitModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.commit()
    engine = Session.kw["bind"]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"), {"id": LAB_ID, "name": "Synthetic HTTP Blood Bank Lab"})
        conn.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"), {"id": LAB_ID + 1, "name": "Synthetic Other Facility"})
        conn.execute(text("INSERT INTO lab_users (id, lab_id, name, email, password_hash, role, is_active, perm_version) VALUES (:id, :lab_id, :name, :email, :password_hash, :role, true, 1) ON CONFLICT (id) DO NOTHING"), {"id": ACTOR_ID, "lab_id": LAB_ID, "name": "Synthetic HTTP Verifier", "email": "http-verifier@example.invalid", "password_hash": "!synthetic-only", "role": "master_admin"})
    with Session() as session:
        session.add(BloodUnitModel(id=issued_unit_id, lab_id=LAB_ID, facility_id=FACILITY_ID, blood_group="O", rh_factor="positive", component="packed_rbc", status=ComponentStatus.ISSUED.value, issued_to=PATIENT_ID, issued_at=now, screening_complete=True, processing_complete=True, storage_location="issued", expiry_date=now + timedelta(days=10)))
        session.commit()
    return issued_unit_id


def _prepare(Session) -> None:
    now = datetime.now(UTC)
    with Session() as session:
        session.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(BloodReservationModel).filter(BloodReservationModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(CrossmatchModel).filter(CrossmatchModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.query(BloodUnitModel).filter(BloodUnitModel.lab_id == LAB_ID).delete(synchronize_session=False)
        session.commit()
    engine = Session.kw["bind"]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"), {"id": LAB_ID, "name": "Synthetic HTTP Blood Bank Lab"})
        conn.execute(text("INSERT INTO lab_users (id, lab_id, name, email, password_hash, role, is_active, perm_version) VALUES (:id, :lab_id, :name, :email, :password_hash, :role, true, 1) ON CONFLICT (id) DO NOTHING"), {"id": ACTOR_ID, "lab_id": LAB_ID, "name": "Synthetic HTTP Verifier", "email": "http-verifier@example.invalid", "password_hash": "!synthetic-only", "role": "master_admin"})
    with Session() as session:
        session.add(BloodUnitModel(id=UNIT_ID, lab_id=LAB_ID, facility_id=FACILITY_ID, blood_group="O", rh_factor="positive", component="packed_rbc", status=ComponentStatus.AVAILABLE.value, screening_complete=True, processing_complete=True, storage_location="cold-room-http", expiry_date=now + timedelta(days=10)))
        session.add(CrossmatchModel(lab_id=LAB_ID, patient_id=PATIENT_ID, unit_id=UNIT_ID, status=CrossmatchStatus.COMPATIBLE.value, verified_at=now, expires_at=now + timedelta(hours=8), performed_by="http-fixture"))
        session.commit()


def _client(Session, actor_lab_id: int = LAB_ID, actor_id: int = ACTOR_ID):
    def db_override():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=actor_id, lab_id=actor_lab_id, role="master_admin", perm_version=1, is_active=True, is_verified=True)
    return TestClient(app, raise_server_exceptions=False)


def _payload(order_id: str = "http-order-1") -> dict[str, str]:
    return {"unit_id": UNIT_ID, "order_id": order_id, "patient_id": PATIENT_ID, "facility_id": FACILITY_ID}


def _issue_counts(Session, request_id: str, unit_id: str):
    with Session() as session:
        request = session.query(BloodRequestModel).filter(BloodRequestModel.id == request_id).one()
        return {
            "fulfilled_units": request.fulfilled_units,
            "unit_status": session.query(BloodUnitModel).filter(BloodUnitModel.id == unit_id).one().status,
            "movements": session.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == LAB_ID, InventoryMovementModel.unit_id == unit_id, InventoryMovementModel.movement_type == "issued").count(),
        }


def _counts(Session):
    with Session() as session:
        return {
            "reservations": session.query(BloodReservationModel).filter(BloodReservationModel.lab_id == LAB_ID, BloodReservationModel.unit_id == UNIT_ID, BloodReservationModel.status == "reserved").count(),
            "movements": session.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == LAB_ID, InventoryMovementModel.unit_id == UNIT_ID, InventoryMovementModel.movement_type == "reserved").count(),
            "unit_status": session.query(BloodUnitModel).filter(BloodUnitModel.id == UNIT_ID).one().status,
        }


def _claims(Session, operation: str, key: str) -> list[tuple[str, str]]:
    """Return the durable idempotency claims for one actor/operation/key."""
    with Session() as session:
        receipts = (
            session.query(ClinicalCommandReceipt)
            .filter(
                ClinicalCommandReceipt.lab_id == LAB_ID,
                ClinicalCommandReceipt.actor_user_id == ACTOR_ID,
                ClinicalCommandReceipt.operation == operation,
                ClinicalCommandReceipt.idempotency_key == key,
            )
            .all()
        )
        return [(receipt.status, receipt.request_fingerprint) for receipt in receipts]


def _conflict_code(response) -> str:
    """The canonical safe error envelope exposes a stable code and no internals."""
    return response.json().get("code")


def test_http_reservation_replay_has_one_side_effect() -> None:
    Session = _session_factory()
    _prepare(Session)
    key = "HTTP-RESERVATION-REPLAY-001"
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload())
            second = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload())
        assert first.status_code == 201
        assert second.status_code == 409
        assert _conflict_code(second) == "CONFLICT"
        assert _counts(Session) == {"reservations": 1, "movements": 1, "unit_status": ComponentStatus.RESERVED.value}
        claims = _claims(Session, "blood.reservation.create", key)
        assert len(claims) == 1
        assert claims[0][0] == "completed"
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_reservation_same_key_concurrency_has_one_side_effect() -> None:
    Session = _session_factory()
    _prepare(Session)
    key = "HTTP-RESERVATION-CONCURRENT-001"
    barrier = threading.Barrier(2)
    responses = []
    errors = []

    def send() -> None:
        try:
            with _client(Session) as client:
                barrier.wait(timeout=10)
                responses.append(client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload()).status_code)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=send) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=45)
    try:
        assert not errors
        assert sorted(responses) == [201, 409]
        assert _counts(Session) == {"reservations": 1, "movements": 1, "unit_status": ComponentStatus.RESERVED.value}
        claims = _claims(Session, "blood.reservation.create", key)
        assert len(claims) == 1
        assert claims[0][0] == "completed"
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_reservation_concurrent_payload_collision_has_one_side_effect() -> None:
    Session = _session_factory()
    _prepare(Session)
    key = "HTTP-RESERVATION-CONCURRENT-COLLISION-001"
    barrier = threading.Barrier(2)
    responses = []
    errors = []

    def send(order_id: str) -> None:
        try:
            with _client(Session) as client:
                barrier.wait(timeout=10)
                responses.append(client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload(order_id)).status_code)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=send, args=("http-order-a",)), threading.Thread(target=send, args=("http-order-b",))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=45)
    try:
        assert not errors
        assert sorted(responses) == [201, 409]
        assert _counts(Session) == {"reservations": 1, "movements": 1, "unit_status": ComponentStatus.RESERVED.value}
        claims = _claims(Session, "blood.reservation.create", key)
        assert len(claims) == 1
        assert claims[0][0] == "completed"
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_issue_replay_has_one_side_effect() -> None:
    Session = _session_factory()
    request_id, unit_id = _prepare_issue(Session)
    key = "HTTP-ISSUE-REPLAY-001"
    body = {"request_id": request_id, "quantity": 1}
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
            second = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body)
        assert first.status_code == 200
        assert second.status_code == 409
        assert _conflict_code(second) == "CONFLICT"
        assert _issue_counts(Session, request_id, unit_id) == {"fulfilled_units": 1, "unit_status": ComponentStatus.ISSUED.value, "movements": 1}
        claims = _claims(Session, "blood.issue", key)
        assert len(claims) == 1
        assert claims[0][0] == "completed"
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_issue_same_key_concurrency_has_one_side_effect() -> None:
    """Two concurrent HTTP issues under one Idempotency-Key commit exactly one effect."""
    Session = _session_factory()
    request_id, unit_id = _prepare_issue(Session)
    key = "HTTP-ISSUE-CONCURRENT-001"
    body = {"request_id": request_id, "quantity": 1}
    barrier = threading.Barrier(2)
    responses = []
    errors = []

    def send() -> None:
        try:
            with _client(Session) as client:
                barrier.wait(timeout=10)
                responses.append(client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json=body).status_code)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=send) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=45)
    try:
        assert not errors
        assert sorted(responses) == [200, 409]
        assert _issue_counts(Session, request_id, unit_id) == {"fulfilled_units": 1, "unit_status": ComponentStatus.ISSUED.value, "movements": 1}
        claims = _claims(Session, "blood.issue", key)
        assert len(claims) == 1
        assert claims[0][0] == "completed"
        # The stored fingerprint is the canonical one for this exact command.
        assert claims[0][1] == ClinicalCommandGuard._fingerprint("blood.issue", "blood_request", request_id, body)
        # No partially committed state: one issued unit and one claim for the whole lab.
        with Session() as session:
            assert session.query(BloodUnitModel).filter(BloodUnitModel.lab_id == LAB_ID, BloodUnitModel.status == ComponentStatus.ISSUED.value).count() == 1
            assert session.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == LAB_ID, ClinicalCommandReceipt.operation == "blood.issue").count() == 1
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_cross_facility_traceability_is_denied() -> None:
    Session = _session_factory()
    _prepare(Session)
    try:
        with Session.kw["bind"].begin() as conn:
            conn.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"), {"id": LAB_ID + 1, "name": "Synthetic Other Facility"})
        with _client(Session, actor_lab_id=LAB_ID + 1) as client:
            response = client.get(f"/blood-bank/units/{UNIT_ID}/traceability")
        assert response.status_code == 404
        assert _counts(Session) == {"reservations": 0, "movements": 0, "unit_status": ComponentStatus.AVAILABLE.value}
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_idor_reservation_return_and_discard_are_facility_scoped() -> None:
    Session = _session_factory()
    _prepare(Session)
    issued_unit_id = _prepare_issued(Session)
    try:
        with _client(Session, actor_lab_id=LAB_ID + 1) as client:
            reservation = client.post("/blood-bank/reservations", headers={"Idempotency-Key": "HTTP-IDOR-RES-001"}, json=_payload())
            returned = client.post("/blood-bank/returns", headers={"Idempotency-Key": "HTTP-IDOR-RETURN-001"}, json={"unit_id": issued_unit_id, "facility_id": FACILITY_ID, "reason": "unauthorized return", "integrity": "intact", "outcome": "available"})
            discarded = client.post("/blood-bank/discards", headers={"Idempotency-Key": "HTTP-IDOR-DISCARD-001"}, json={"unit_id": issued_unit_id, "facility_id": FACILITY_ID, "reason": "unauthorized discard", "category": "other"})
        assert reservation.status_code == 422
        assert returned.status_code == 422
        assert discarded.status_code == 422
        with Session() as session:
            assert session.query(BloodUnitModel).filter(BloodUnitModel.id == issued_unit_id).one().status == ComponentStatus.ISSUED.value
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_idempotency_key_namespace_is_operation_scoped() -> None:
    Session = _session_factory()
    _prepare(Session)
    key = "HTTP-NAMESPACE-SAME-KEY-001"
    try:
        with _client(Session) as client:
            reservation = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload("namespace-order"))
        assert reservation.status_code == 201
        request_id, unit_id = _prepare_issue(Session)
        with _client(Session) as client:
            issue = client.post("/blood-bank/inventory/issue", headers={"Idempotency-Key": key, "If-Match": "1"}, json={"request_id": request_id, "quantity": 1})
        assert issue.status_code == 200
        assert _issue_counts(Session, request_id, unit_id) == {"fulfilled_units": 1, "unit_status": ComponentStatus.ISSUED.value, "movements": 1}
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()


def test_http_reservation_payload_collision_has_no_second_side_effect() -> None:
    Session = _session_factory()
    _prepare(Session)
    key = "HTTP-RESERVATION-COLLISION-001"
    try:
        with _client(Session) as client:
            first = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload("http-order-a"))
            first_fingerprint = _claims(Session, "blood.reservation.create", key)[0][1]
            second = client.post("/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload("http-order-b"))
        assert first.status_code == 201
        assert second.status_code == 409
        assert _conflict_code(second) == "CONFLICT"
        assert _counts(Session) == {"reservations": 1, "movements": 1, "unit_status": ComponentStatus.RESERVED.value}
        claims = _claims(Session, "blood.reservation.create", key)
        assert len(claims) == 1
        assert claims[0][0] == "completed"
        assert claims[0][1] == first_fingerprint
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()
