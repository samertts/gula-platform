"""Wave 1 Blood Bank lifecycle end-to-end proof.

One clinical unit is carried through the canonical HTTP surface — reserve,
traceability, release, traceability — against a real PostgreSQL database and the
real FastAPI application.  Authentication, authorisation, the clinical command
guard and the transaction boundaries are the production ones.
"""
from __future__ import annotations

import os

import pytest

from app.blood_bank.domain.enums import ComponentStatus
from app.blood_bank.infrastructure.models import BloodReservationModel, BloodUnitModel, InventoryMovementModel
from app.main import app

from test_http_idempotency_postgres import (
    LAB_ID,
    UNIT_ID,
    _claims,
    _client,
    _payload,
    _prepare,
    _session_factory,
)

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")


def _unit_status(Session) -> str:
    with Session() as session:
        return session.query(BloodUnitModel).filter(BloodUnitModel.id == UNIT_ID).one().status


def _movement_types(Session) -> list[str]:
    with Session() as session:
        rows = (
            session.query(InventoryMovementModel)
            .filter(InventoryMovementModel.lab_id == LAB_ID, InventoryMovementModel.unit_id == UNIT_ID)
            .order_by(InventoryMovementModel.id)
            .all()
        )
        return [row.movement_type for row in rows]


def test_wave1_reserve_trace_release_lifecycle() -> None:
    Session = _session_factory()
    _prepare(Session)
    try:
        with _client(Session) as client:
            reserved = client.post(
                "/blood-bank/reservations",
                headers={"Idempotency-Key": "WAVE1-E2E-RESERVE"},
                json=_payload("wave1-e2e-order"),
            )
            assert reserved.status_code == 201
            reservation_id = reserved.json()["id"]
            assert _unit_status(Session) == ComponentStatus.RESERVED.value

            # The unit is traceable to its owning facility while reserved.
            traced = client.get(f"/blood-bank/units/{UNIT_ID}/traceability")
            assert traced.status_code == 200

            released = client.post(
                f"/blood-bank/reservations/{reservation_id}/release",
                headers={"Idempotency-Key": "WAVE1-E2E-RELEASE", "If-Match": "1"},
                json={"reason": "wave 1 lifecycle proof"},
            )
            assert released.status_code == 200

            after = client.get(f"/blood-bank/units/{UNIT_ID}/traceability")
            assert after.status_code == 200

        # Final state is consistent: the reservation is no longer holding the unit.
        with Session() as session:
            reservation = session.query(BloodReservationModel).filter(BloodReservationModel.id == reservation_id).one()
            assert reservation.status != "reserved"
            assert session.query(BloodReservationModel).filter(
                BloodReservationModel.lab_id == LAB_ID, BloodReservationModel.status == "reserved"
            ).count() == 0
        assert _unit_status(Session) == ComponentStatus.AVAILABLE.value

        # Each guarded step recorded exactly one durable, completed claim.
        for operation, key in (
            ("blood.reservation.create", "WAVE1-E2E-RESERVE"),
            ("blood.reservation.release", "WAVE1-E2E-RELEASE"),
        ):
            claims = _claims(Session, operation, key)
            assert len(claims) == 1
            assert claims[0][0] == "completed"

        # The movement ledger records both lifecycle steps and nothing more.
        movements = _movement_types(Session)
        assert movements.count("reserved") == 1
        assert len(movements) == len(set(enumerate(movements)))
    finally:
        app.dependency_overrides.clear()
        Session.kw["bind"].dispose()
