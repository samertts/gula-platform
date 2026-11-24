"""AUD-CLIN-001 regression — critical-result alerts must be durable and honest.

The previous workflow returned ``status="alerted"`` while emitting nothing.
These tests prove the fail-closed replacement:

* a critical result produces a durable ``CriticalResultDetected`` outbox row;
* the response NEVER claims a clinician was notified;
* non-critical / missing results produce no outbox row.

All identifiers are synthetic. No database beyond the per-test SQLite
savepoint is used; no notification is actually delivered.
"""

from __future__ import annotations

import json

import pytest
from app.lims import models as lims_models
from app.lims.workflows import process_critical_result
from app.models.lab_order import LabOrder
from app.models.outbox import OutboxEvent
from app.models.patient import Patient

RESULT_EVENT_TYPE = "lims.result.critical"


@pytest.fixture()
def critical_result(db, make_lab):
    lab = make_lab("Critical Alert Lab")
    patient = Patient(lab_id=lab.id, full_name="Synthetic Critical Patient", phone="07700000001")
    db.add(patient)
    db.flush()
    order = LabOrder(patient_id=patient.id, lab_id=lab.id, status="pending")
    db.add(order)
    db.flush()
    lims_order = lims_models.Order(
        order_id=order.id, lab_id=lab.id, accession_number="ACC-CRIT-001"
    )
    db.add(lims_order)
    db.flush()
    specimen = lims_models.Specimen(
        lab_id=lab.id, order_id=order.id, barcode="SP-CRIT-001", specimen_type="blood"
    )
    db.add(specimen)
    db.flush()
    result = lims_models.Result(
        lab_id=lab.id,
        specimen_id=specimen.id,
        order_id=order.id,
        test_code="K",
        test_name="Potassium",
        value_numeric=7.2,
        unit="mmol/L",
        is_critical=True,
        is_panic=True,
    )
    db.add(result)
    db.flush()
    return lab, result


def test_critical_result_writes_durable_outbox_and_never_claims_alerted(db, critical_result):
    lab, result = critical_result

    outcome = process_critical_result(db, result.id, lab.id, user_id=4242)

    assert outcome["status"] == "notification_pending"
    assert outcome["clinician_notified"] is False
    assert outcome["delivery_status"] == "pending_dispatch"
    assert outcome["acknowledgement_status"] == "NOT_CONFIGURED"
    assert outcome["is_panic"] is True
    assert outcome["notification_window"] == "15 minutes"
    assert outcome["outbox_event_id"] is not None

    event = db.query(OutboxEvent).filter(OutboxEvent.id == outcome["outbox_event_id"]).one()
    assert event.event_type == RESULT_EVENT_TYPE
    assert event.aggregate_type == "result"
    assert event.aggregate_id == result.id
    assert event.status == "pending"
    payload = json.loads(event.payload)
    assert payload["event_type"] == RESULT_EVENT_TYPE
    assert payload["payload"]["result_id"] == result.id
    assert payload["payload"]["lab_id"] == lab.id
    assert payload["payload"]["delivery_status"] == "pending_dispatch"
    assert payload["payload"]["requested_action"] == "notify_ordering_physician"
    assert payload["payload"]["acknowledgement_status"] == "NOT_CONFIGURED"


def test_non_critical_result_emits_no_outbox_row(db, critical_result):
    lab, result = critical_result
    result.is_critical = False
    db.flush()

    outcome = process_critical_result(db, result.id, lab.id, user_id=4242)

    assert outcome["status"] == "skipped"
    assert db.query(OutboxEvent).filter(OutboxEvent.event_type == RESULT_EVENT_TYPE).count() == 0


def test_missing_result_returns_error_without_outbox(db, critical_result):
    lab, _ = critical_result

    outcome = process_critical_result(db, 999999, lab.id, user_id=4242)

    assert outcome["status"] == "error"
    assert db.query(OutboxEvent).filter(OutboxEvent.event_type == RESULT_EVENT_TYPE).count() == 0


def test_non_panic_result_uses_60_minute_window(db, critical_result):
    lab, result = critical_result
    result.is_panic = False
    db.flush()

    outcome = process_critical_result(db, result.id, lab.id, user_id=4242)

    assert outcome["status"] == "notification_pending"
    assert outcome["is_panic"] is False
    assert outcome["notification_window"] == "60 minutes"
