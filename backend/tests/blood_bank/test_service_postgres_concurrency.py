"""Service-level Blood Bank concurrency proof.

Requires BLOOD_BANK_POSTGRES_URL and a database migrated through 20260901_0002.
This test calls the canonical BloodBankService, not a simplified probe service.
"""
from __future__ import annotations

import os
import threading
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.blood_bank.application.service import BloodBankService
from app.blood_bank.domain.enums import ComponentStatus, CrossmatchStatus
from app.blood_bank.infrastructure.models import (
    BloodReservationModel,
    BloodUnitModel,
    CrossmatchModel,
    InventoryMovementModel,
)

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")


def test_canonical_reservation_service_race() -> None:
    engine = create_engine(POSTGRES_URL, future=True, pool_size=4, max_overflow=0)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    lab_id, facility_id, unit_id, patient_id = 991001, "FACILITY-SVC-A", "svc-race-unit", "synthetic-patient-svc"
    now = datetime.now(UTC)
    setup = Session()
    try:
        setup.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == lab_id).delete(synchronize_session=False)
        setup.query(BloodReservationModel).filter(BloodReservationModel.lab_id == lab_id).delete(synchronize_session=False)
        setup.query(CrossmatchModel).filter(CrossmatchModel.lab_id == lab_id).delete(synchronize_session=False)
        setup.query(BloodUnitModel).filter(BloodUnitModel.lab_id == lab_id).delete(synchronize_session=False)
        unit = BloodUnitModel(id=unit_id, lab_id=lab_id, facility_id=facility_id, blood_group="O", rh_factor="positive", component="packed_rbc", status=ComponentStatus.AVAILABLE.value, screening_complete=True, processing_complete=True, storage_location="cold-room-1", expiry_date=now + timedelta(days=10))
        match = CrossmatchModel(lab_id=lab_id, patient_id=patient_id, unit_id=unit_id, status=CrossmatchStatus.COMPATIBLE.value, verified_at=now, expires_at=now + timedelta(hours=8), performed_by="fixture")
        setup.add_all([unit, match])
        setup.commit()
    finally:
        setup.close()

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    errors: list[str] = []
    lock = threading.Lock()

    def attempt(actor: str) -> None:
        session = Session()
        try:
            barrier.wait(timeout=10)
            BloodBankService(session).reserve_unit({"lab_id": lab_id, "facility_id": facility_id, "unit_id": unit_id, "patient_id": patient_id, "order_id": f"order-{actor}", "requested_by": actor})
            session.commit()
            result = "success"
        except Exception as exc:
            session.rollback()
            result = "conflict" if type(exc).__name__ in {"BloodBankWorkflowError", "IntegrityError", "HTTPException"} or "unique" in str(exc).lower() else f"error:{type(exc).__name__}"
            errors.append(str(exc))
        finally:
            session.close()
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=attempt, args=("actor-a",)), threading.Thread(target=attempt, args=("actor-b",))]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=30)

    verify = Session()
    try:
        assert sorted(outcomes) == ["conflict", "success"], errors
        assert verify.query(BloodReservationModel).filter(BloodReservationModel.lab_id == lab_id, BloodReservationModel.unit_id == unit_id, BloodReservationModel.status == "reserved").count() == 1
        assert verify.query(BloodUnitModel).filter(BloodUnitModel.id == unit_id).one().status == ComponentStatus.RESERVED.value
        assert verify.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == lab_id, InventoryMovementModel.unit_id == unit_id, InventoryMovementModel.movement_type == "reserved").count() == 1
    finally:
        verify.close()
        cleanup = Session()
        cleanup.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.query(BloodReservationModel).filter(BloodReservationModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.query(CrossmatchModel).filter(CrossmatchModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.query(BloodUnitModel).filter(BloodUnitModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.commit(); cleanup.close(); engine.dispose()
