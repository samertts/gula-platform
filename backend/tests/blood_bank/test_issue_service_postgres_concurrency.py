"""Real PostgreSQL Issue service concurrency proof.

Requires a disposable database migrated through the Blood Bank migrations.
"""
from __future__ import annotations

import os
import threading
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.blood_bank.application.service import BloodBankService
from app.blood_bank.domain.enums import ComponentStatus
from app.blood_bank.infrastructure.models import BloodRequestModel, BloodUnitModel, InventoryMovementModel

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")


def test_canonical_issue_service_race() -> None:
    engine = create_engine(POSTGRES_URL, future=True, pool_size=4, max_overflow=0)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    lab_id, facility_id, request_id, unit_id = 991002, "FACILITY-ISSUE-A", "svc-issue-request", "svc-issue-unit"
    patient_id = "synthetic-patient-issue"
    now = datetime.now(UTC)
    setup = Session()
    try:
        setup.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == lab_id).delete(synchronize_session=False)
        setup.query(BloodRequestModel).filter(BloodRequestModel.lab_id == lab_id).delete(synchronize_session=False)
        setup.query(BloodUnitModel).filter(BloodUnitModel.lab_id == lab_id).delete(synchronize_session=False)
        setup.add(BloodRequestModel(id=request_id, lab_id=lab_id, patient_id=patient_id, facility_id=facility_id, blood_group="O", rh_factor="positive", component="packed_rbc", units_requested=1, fulfilled_units=0, status="approved", requested_by="synthetic-doctor"))
        setup.add(BloodUnitModel(id=unit_id, lab_id=lab_id, facility_id=facility_id, blood_group="O", rh_factor="positive", component="packed_rbc", status=ComponentStatus.AVAILABLE.value, screening_complete=True, processing_complete=True, storage_location="cold-room-1", expiry_date=now + timedelta(days=10)))
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
            BloodBankService(session).issue_units_safely(request_id=request_id, lab_id=lab_id, quantity=1, issued_by=actor)
            session.commit()
            result = "success"
        except Exception as exc:
            session.rollback()
            result = "conflict" if type(exc).__name__ in {"BloodBankWorkflowError", "InsufficientStockError", "IntegrityError"} else f"error:{type(exc).__name__}"
            errors.append(str(exc))
        finally:
            session.close()
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=attempt, args=("issuer-a",)), threading.Thread(target=attempt, args=("issuer-b",))]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=30)

    verify = Session()
    try:
        assert sorted(outcomes) == ["conflict", "success"], errors
        unit = verify.query(BloodUnitModel).filter(BloodUnitModel.id == unit_id).one()
        assert unit.status == ComponentStatus.ISSUED.value
        assert verify.query(BloodUnitModel).filter(BloodUnitModel.id == unit_id, BloodUnitModel.status == ComponentStatus.ISSUED.value).count() == 1
        assert verify.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == lab_id, InventoryMovementModel.unit_id == unit_id, InventoryMovementModel.movement_type == "issued").count() == 1
        assert verify.query(BloodRequestModel).filter(BloodRequestModel.id == request_id, BloodRequestModel.fulfilled_units == 1).count() == 1
    finally:
        verify.close()
        cleanup = Session()
        cleanup.query(InventoryMovementModel).filter(InventoryMovementModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.query(BloodRequestModel).filter(BloodRequestModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.query(BloodUnitModel).filter(BloodUnitModel.lab_id == lab_id).delete(synchronize_session=False)
        cleanup.commit(); cleanup.close(); engine.dispose()
