from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.public_health.application.service import PublicHealthService
from app.public_health.domain.enums import ImmunizationStatus
from app.public_health.infrastructure.models import ImmunizationRecordModel
from shared.rbac.permissions import get_permissions_for_role


@pytest.mark.integration
def test_patient_schedule_is_generated_once_and_marks_overdue(db):
    service = PublicHealthService(db)
    definition = service.configure_immunization_schedule(
        {
            "schedule_version": "UNIT-EPI-1",
            "vaccine": "Unit Vaccine",
            "vaccine_code": "UNIT-001",
            "dose_number": 1,
            "total_doses": 1,
            "recommended_age_days": 0,
            "source_reference": "approved-unit-reference",
        },
        lab_id=1,
        approved_by="test-admin",
    )
    assert definition["schedule_version"] == "UNIT-EPI-1"

    first = service.generate_patient_immunization_schedule(
        patient_id="newborn-citizen-1",
        health_number="THN-UNIT0000001",
        date_of_birth=date.today() - timedelta(days=2),
        lab_id=1,
        schedule_version="UNIT-EPI-1",
        newborn_id="newborn-1",
    )
    second = service.generate_patient_immunization_schedule(
        patient_id="newborn-citizen-1",
        health_number="THN-UNIT0000001",
        date_of_birth=date.today() - timedelta(days=2),
        lab_id=1,
        schedule_version="UNIT-EPI-1",
        newborn_id="newborn-1",
    )

    assert len(first) == 1
    assert first[0].id == second[0].id
    overdue = service.get_overdue_vaccinations(lab_id=1, patient_id="newborn-citizen-1")
    assert [item.id for item in overdue] == [first[0].id]
    assert overdue[0].status == ImmunizationStatus.OVERDUE.value


@pytest.mark.integration
def test_administering_a_scheduled_dose_is_idempotent(db):
    service = PublicHealthService(db)
    service.configure_immunization_schedule(
        {
            "schedule_version": "UNIT-EPI-2",
            "vaccine": "Unit Vaccine 2",
            "vaccine_code": "UNIT-002",
            "dose_number": 1,
            "total_doses": 1,
            "recommended_age_days": 10,
        },
        lab_id=1,
        approved_by="test-admin",
    )
    schedule = service.generate_patient_immunization_schedule(
        patient_id="newborn-citizen-2",
        health_number="THN-UNIT0000002",
        date_of_birth=date.today(),
        lab_id=1,
        schedule_version="UNIT-EPI-2",
    )[0]

    first_record = service.mark_administered(
        schedule.id,
        {"administration_date": datetime.now(UTC), "lot_number": "LOT-UNIT"},
        lab_id=1,
        administered_by="nurse-1",
    )
    repeated_record = service.mark_administered(
        schedule.id,
        {"administration_date": datetime.now(UTC)},
        lab_id=1,
        administered_by="nurse-1",
    )

    assert first_record.id == repeated_record.id
    assert first_record.status == ImmunizationStatus.COMPLETE.value
    assert db.query(ImmunizationRecordModel).filter_by(schedule_id=schedule.id).count() == 1


@pytest.mark.unit
def test_newborn_and_immunization_permissions_follow_least_privilege():
    midwife_permissions = get_permissions_for_role("midwife")
    assert {"newborn:register", "immunization:administer"}.issubset(midwife_permissions)
    assert "immunization:schedule" not in midwife_permissions
    assert "newborn:register" not in get_permissions_for_role("doctor")


@pytest.mark.integration
def test_non_administration_creates_follow_up_task_without_deleting_schedule(db):
    service = PublicHealthService(db)
    service.configure_immunization_schedule(
        {
            "schedule_version": "UNIT-EPI-FOLLOWUP",
            "vaccine": "Unit Follow-up Vaccine",
            "vaccine_code": "UNIT-FU-001",
            "dose_number": 1,
            "total_doses": 2,
            "recommended_age_days": 0,
        },
        lab_id=1,
        approved_by="test-admin",
    )
    schedule = service.generate_patient_immunization_schedule(
        patient_id="newborn-followup-1",
        health_number="THN-FOLLOWUP0001",
        date_of_birth=date.today(),
        lab_id=1,
        schedule_version="UNIT-EPI-FOLLOWUP",
    )[0]

    updated = service.record_non_administration(
        schedule.id,
        {"reason": "stockout", "notes": "لا يوجد مخزون صالح حالياً", "priority": "high"},
        lab_id=1,
        recorded_by="vaccinator-1",
    )
    tasks = service.list_follow_up_tasks(lab_id=1, status="pending")

    assert updated.id == schedule.id
    assert updated.non_administration_reason == "stockout"
    assert updated.follow_up_status == "pending"
    assert len(tasks) == 1
    assert tasks[0].schedule_id == schedule.id

    completed = service.complete_follow_up_task(tasks[0].id, lab_id=1, completed_by="nurse-1")
    assert completed.status == "completed"


@pytest.mark.integration
def test_aefi_is_linked_to_administered_record_and_tenant(db):
    service = PublicHealthService(db)
    service.configure_immunization_schedule(
        {
            "schedule_version": "UNIT-EPI-AEFI",
            "vaccine": "Unit AEFI Vaccine",
            "vaccine_code": "UNIT-AEFI-001",
            "dose_number": 1,
            "total_doses": 1,
            "recommended_age_days": 0,
        },
        lab_id=1,
        approved_by="test-admin",
    )
    schedule = service.generate_patient_immunization_schedule(
        patient_id="newborn-aefi-1",
        health_number="THN-AEFI000001",
        date_of_birth=date.today(),
        lab_id=1,
        schedule_version="UNIT-EPI-AEFI",
    )[0]
    record = service.mark_administered(
        schedule.id,
        {"administration_date": datetime.now(UTC), "lot_number": "LOT-AEFI"},
        lab_id=1,
        administered_by="nurse-1",
    )

    event = service.report_adverse_event(
        record.id,
        {"severity": "moderate", "symptoms": ["حمى", "طفح"], "treatment": "مراقبة"},
        lab_id=1,
        reported_by="doctor-1",
    )

    assert event.record_id == record.id
    assert event.schedule_id == schedule.id
    assert event.patient_id == "newborn-aefi-1"
    assert event.investigation_status == "reported"


@pytest.mark.integration
def test_cold_chain_excursion_quarantines_attached_lots(db):
    service = PublicHealthService(db)
    catalog = service.register_vaccine_catalog(
        {"vaccine_code": "UNIT-STOCK-001", "name": "Unit Stock Vaccine", "storage_min_c": 2, "storage_max_c": 8},
        lab_id=1,
    )
    lot = service.receive_vaccine_lot(
        catalog.id,
        {"lot_number": "LOT-COLD-1", "quantity": 20, "expiry_date": datetime.now(UTC) + timedelta(days=180), "storage_equipment_id": "fridge-1"},
        lab_id=1,
        performed_by="stock-user",
    )

    reading = service.record_cold_chain_reading(
        {"equipment_id": "fridge-1", "temperature_c": 12, "minimum_allowed_c": 2, "maximum_allowed_c": 8},
        lab_id=1,
        recorded_by="stock-user",
    )
    inventory = service.list_vaccine_inventory(lab_id=1)

    assert reading.status == "out_of_range"
    assert inventory[0].id == lot.id
    assert inventory[0].quarantined is True
    assert inventory[0].available_quantity == 20


@pytest.mark.integration
def test_vaccine_consumption_is_idempotent_and_matches_administered_vaccine(db):
    service = PublicHealthService(db)
    catalog = service.register_vaccine_catalog(
        {"vaccine_code": "UNIT-STOCK-002", "name": "Unit Consume Vaccine"},
        lab_id=1,
    )
    lot = service.receive_vaccine_lot(
        catalog.id,
        {"lot_number": "LOT-CONSUME-1", "quantity": 2, "expiry_date": datetime.now(UTC) + timedelta(days=180)},
        lab_id=1,
        performed_by="stock-user",
    )
    service.configure_immunization_schedule(
        {
            "schedule_version": "UNIT-STOCK-SCHEDULE",
            "vaccine": "Unit Consume Vaccine",
            "vaccine_code": "UNIT-STOCK-002",
            "dose_number": 1,
            "total_doses": 1,
            "recommended_age_days": 0,
        },
        lab_id=1,
        approved_by="test-admin",
    )
    schedule = service.generate_patient_immunization_schedule(
        patient_id="stock-patient-1", health_number="THN-STOCK-001", date_of_birth=date.today(),
        lab_id=1, schedule_version="UNIT-STOCK-SCHEDULE",
    )[0]
    record = service.mark_administered(
        schedule.id, {"administration_date": datetime.now(UTC)}, lab_id=1, administered_by="vaccinator-1",
    )

    first = service.consume_vaccine_for_administration(record.id, lot.id, 1, 1, "stock-user", "consume-key-001")
    replay = service.consume_vaccine_for_administration(record.id, lot.id, 1, 1, "stock-user", "consume-key-001")
    inventory = service.list_vaccine_inventory(lab_id=1)

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert inventory[0].available_quantity == 1


@pytest.mark.integration
def test_vaccine_wastage_and_adjustment_are_auditable_and_non_negative(db):
    service = PublicHealthService(db)
    catalog = service.register_vaccine_catalog({"vaccine_code": "UNIT-STOCK-003", "name": "Unit Waste Vaccine"}, lab_id=1)
    lot = service.receive_vaccine_lot(
        catalog.id,
        {"lot_number": "LOT-WASTE-1", "quantity": 5, "expiry_date": datetime.now(UTC) + timedelta(days=180)},
        lab_id=1,
        performed_by="stock-user",
    )

    waste = service.record_vaccine_wastage(
        lot.id, {"quantity": 2, "reason": "broken vial", "idempotency_key": "waste-key-001"}, 1, "stock-user",
    )
    replay = service.record_vaccine_wastage(
        lot.id, {"quantity": 2, "reason": "broken vial", "idempotency_key": "waste-key-001"}, 1, "stock-user",
    )
    adjustment = service.adjust_vaccine_lot(
        lot.id, {"delta": -1, "reason": "physical count", "idempotency_key": "adjust-key-001"}, 1, "stock-user",
    )

    assert waste["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert adjustment["quantity"] == -1
    assert service.list_vaccine_inventory(1)[0].available_quantity == 2
    with pytest.raises(ValueError):
        service.adjust_vaccine_lot(lot.id, {"delta": -3, "reason": "invalid", "idempotency_key": "adjust-key-002"}, 1, "stock-user")
