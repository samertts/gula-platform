"""Regression guard for the biomedical work-order/device concurrency fix.

complete_work_order and update_device_status previously read a row with a
plain, unlocked SELECT before mutating it -- the same TOCTOU shape already
fixed this session in payments (double cash capture / double refund) and
devices (double outbox dispatch). Proven separately against a real
disposable PostgreSQL 16 database that two concurrent complete_work_order
calls on the SAME work order both succeeded pre-fix, silently double-
applying the completion side effects (cost totals, device release).
SQLite (this suite's default) cannot reproduce the race itself
(single-writer locking masks it), so this test pins the two guarantees
that make the guard real: a locked query is issued, and a second
completion attempt is rejected rather than silently re-applied.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.biomedical.application.service import BiomedicalService
from app.biomedical.exceptions import WorkOrderAlreadyCompletedError
from app.biomedical.infrastructure.models import MedicalDeviceModel, WorkOrderModel
from app.national.base import NationalBase

LAB_ID = 7171


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    NationalBase.metadata.create_all(engine, tables=[MedicalDeviceModel.__table__, WorkOrderModel.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed(db) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    device = MedicalDeviceModel(lab_id=LAB_ID, device_name="Ventilator", status="under_maintenance")
    db.add(device)
    db.flush()
    wo = WorkOrderModel(
        lab_id=LAB_ID, device_id=device.id, device_name=device.device_name,
        work_order_number="WO-TEST-0001", status="in_progress", reported_date=now,
    )
    db.add(wo)
    db.commit()
    return device.id, wo.id


def test_complete_work_order_locks_and_increments_version(db):
    device_id, wo_id = _seed(db)
    service = BiomedicalService(db)
    completed = service.complete_work_order(wo_id, {"action_taken": "replaced valve", "cost_parts": 20.0, "cost_labor": 30.0})
    assert completed.id == wo_id

    refreshed_wo = db.query(WorkOrderModel).filter_by(id=wo_id).one()
    refreshed_device = db.query(MedicalDeviceModel).filter_by(id=device_id).one()
    assert refreshed_wo.status == "completed"
    assert refreshed_wo.cost_total == 50.0
    assert refreshed_wo.version == 2  # started at 1, incremented once by completion
    assert refreshed_device.status == "available"
    assert refreshed_device.version == 2


def test_second_completion_is_rejected_not_reapplied(db):
    _, wo_id = _seed(db)
    service = BiomedicalService(db)
    service.complete_work_order(wo_id, {"cost_parts": 20.0, "cost_labor": 30.0})

    with pytest.raises(WorkOrderAlreadyCompletedError):
        service.complete_work_order(wo_id, {"cost_parts": 999.0, "cost_labor": 999.0})

    # The second call's payload must never have been applied.
    refreshed = db.query(WorkOrderModel).filter_by(id=wo_id).one()
    assert refreshed.cost_total == 50.0
    assert refreshed.version == 2


def test_update_device_status_query_is_row_locked(db, monkeypatch):
    from sqlalchemy.orm import Query as SAQuery

    device_id, _ = _seed(db)
    calls = []
    original = SAQuery.with_for_update

    def spy(self, *args, **kwargs):
        calls.append(kwargs)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(SAQuery, "with_for_update", spy)

    service = BiomedicalService(db)
    updated = service.update_device_status(device_id, "available", "PM complete")

    assert calls, "update_device_status must call Query.with_for_update()"
    assert updated.id == device_id
    refreshed = db.query(MedicalDeviceModel).filter_by(id=device_id).one()
    assert refreshed.version == 2


def test_complete_work_order_query_is_row_locked(db, monkeypatch):
    from sqlalchemy.orm import Query as SAQuery

    _, wo_id = _seed(db)
    calls = []
    original = SAQuery.with_for_update

    def spy(self, *args, **kwargs):
        calls.append(kwargs)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(SAQuery, "with_for_update", spy)

    service = BiomedicalService(db)
    service.complete_work_order(wo_id, {"cost_parts": 1.0, "cost_labor": 1.0})

    # Two locked queries expected: the work order itself, then its device.
    assert len(calls) >= 2, "complete_work_order must lock both the work order and its linked device"
