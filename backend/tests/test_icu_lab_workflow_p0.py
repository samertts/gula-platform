from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.blood_bank.application.service import BloodBankService
from app.blood_bank.exceptions import BloodBankValidationError, BloodBankWorkflowError
from app.blood_bank.infrastructure.models import (
    BloodRequestModel,
    BloodUnitModel,
    CrossmatchModel,
)
from app.critical_care.application.service import CriticalCareService
from app.critical_care.exceptions import (
    ICUAdmissionNotFoundError,
    ICUValidationError,
    ICUWorkflowError,
)
from app.critical_care.infrastructure.models import (
    ContinuousInfusionModel,
    ICUAdmissionModel,
    ICUBedModel,
)
from app.lims import models as lims_models
from app.lims.services import ReportService

LAB_ID = 71


def _admit_icu_patient(db, *, patient_id: str = "patient-1") -> tuple[CriticalCareService, ICUAdmissionModel]:
    bed = ICUBedModel(
        lab_id=LAB_ID,
        bed_label="ICU-01",
        icu_type="adult_icu",
        is_active=True,
        is_occupied=False,
        has_ventilator=True,
        has_infusion_pump=True,
    )
    db.add(bed)
    db.flush()
    service = CriticalCareService(db)
    admission = service.admit_patient_safely(
        {
            "lab_id": LAB_ID,
            "patient_id": patient_id,
            "bed_id": bed.id,
            "icu_type": "adult_icu",
            "admission_type": "emergency",
        }
    )
    return service, admission


def test_icu_admission_binds_the_bed_and_rejects_a_second_active_admission(db):
    service, admission = _admit_icu_patient(db)

    bed = db.query(ICUBedModel).filter_by(id=admission.bed_id).one()
    assert bed.is_occupied is True
    assert bed.current_patient_id == "patient-1"
    assert bed.current_admission_id == admission.id

    with pytest.raises(ICUWorkflowError):
        service.admit_patient_safely(
            {
                "lab_id": LAB_ID,
                "patient_id": "patient-1",
                "bed_id": admission.bed_id,
                "icu_type": "adult_icu",
            }
        )


def test_icu_vitals_require_a_live_admission_and_strict_chronology(db):
    service, admission = _admit_icu_patient(db)
    recorded_at = datetime.now(UTC)
    service.record_vitals_safely(
        {
            "lab_id": LAB_ID,
            "patient_id": admission.patient_id,
            "admission_id": admission.id,
            "recorded_at": recorded_at,
            "heart_rate": 90,
            "respiratory_rate": 18,
            "systolic_bp": 120,
            "diastolic_bp": 75,
            "temperature": 37.0,
            "oxygen_saturation": 97.0,
            "gcs_total": 15,
        }
    )

    with pytest.raises(ICUWorkflowError):
        service.record_vitals_safely(
            {
                "lab_id": LAB_ID,
                "patient_id": admission.patient_id,
                "admission_id": admission.id,
                "recorded_at": recorded_at,
                "heart_rate": 90,
            }
        )


def test_high_alert_infusion_requires_independent_verification_and_cannot_stop_twice(db):
    service, admission = _admit_icu_patient(db)
    infusion = service.start_infusion_safely(
        {
            "lab_id": LAB_ID,
            "patient_id": admission.patient_id,
            "admission_id": admission.id,
            "medication": "insulin",
            "rate": "2 ml/hr",
            "initiated_by": "nurse-1",
            "start_time": datetime.now(UTC),
        }
    )
    assert infusion.status == "awaiting_verification"

    with pytest.raises(ICUValidationError):
        service.verify_infusion_safely(infusion.id, LAB_ID, "nurse-1")

    verified = service.verify_infusion_safely(infusion.id, LAB_ID, "nurse-2")
    assert verified.status == "active"
    assert verified.verified_by == "nurse-2"

    stopped = service.stop_infusion_safely(infusion.id, LAB_ID)
    assert stopped.status == "stopped"
    with pytest.raises(ICUWorkflowError):
        service.stop_infusion_safely(infusion.id, LAB_ID)


def _blood_request_and_unit(db) -> tuple[BloodBankService, BloodRequestModel, BloodUnitModel]:
    request = BloodRequestModel(
        lab_id=LAB_ID,
        patient_id="patient-blood-1",
        facility_id="facility-1",
        blood_group="A",
        rh_factor="+",
        component="packed_rbc",
        units_requested=1,
        fulfilled_units=0,
        status="pending",
    )
    unit = BloodUnitModel(
        lab_id=LAB_ID,
        facility_id="facility-1",
        blood_group="A",
        rh_factor="+",
        component="packed_rbc",
        bag_identifier="UNIT-001",
        status="available",
        screening_complete=True,
        processing_complete=True,
        recalled=False,
        expiry_date=datetime.now(UTC) + timedelta(days=7),
    )
    db.add_all([request, unit])
    db.flush()
    return BloodBankService(db), request, unit


def test_blood_issue_requires_a_bound_request_and_only_eligible_units(db):
    service, request, unit = _blood_request_and_unit(db)

    issued = service.issue_units_safely(
        request_id=request.id,
        lab_id=LAB_ID,
        quantity=1,
        issued_by="blood-bank-tech-1",
    )
    assert [item.id for item in issued] == [unit.id]
    assert unit.status == "issued"
    assert unit.issued_to == request.patient_id
    assert request.status == "fulfilled"

    with pytest.raises(BloodBankWorkflowError):
        service.issue_units_safely(
            request_id=request.id,
            lab_id=LAB_ID,
            quantity=1,
            issued_by="blood-bank-tech-1",
        )


def test_transfusion_requires_independent_crossmatch_and_bedside_verification(db):
    service, request, unit = _blood_request_and_unit(db)
    service.issue_units_safely(
        request_id=request.id,
        lab_id=LAB_ID,
        quantity=1,
        issued_by="blood-bank-tech-1",
    )
    crossmatch = service.perform_crossmatch_safely(
        {
            "lab_id": LAB_ID,
            "patient_id": request.patient_id,
            "patient_blood_group": "A",
            "patient_rh_factor": "+",
            "unit_id": unit.id,
            "performed_by": "tech-1",
            "expires_at": datetime.now(UTC) + timedelta(hours=24),
        }
    )
    with pytest.raises(BloodBankValidationError):
        service.verify_crossmatch_safely(crossmatch.id, LAB_ID, "tech-1")
    service.verify_crossmatch_safely(crossmatch.id, LAB_ID, "tech-2")

    transfusion = service.record_transfusion_safely(
        {
            "lab_id": LAB_ID,
            "patient_id": request.patient_id,
            "unit_id": unit.id,
            "crossmatch_id": crossmatch.id,
            "ordered_by": "physician-1",
        }
    )
    with pytest.raises(BloodBankValidationError):
        service.verify_transfusion_safely(
            transfusion.id,
            LAB_ID,
            {"verified_by": "nurse-1", "patient_verified": True},
        )
    verified = service.verify_transfusion_safely(
        transfusion.id,
        LAB_ID,
        {
            "verified_by": "nurse-1",
            "patient_verified": True,
            "unit_verified": True,
            "consent_verified": True,
            "bedside_verification_complete": True,
            "pre_vitals": {"temperature": 37.0, "blood_pressure": "120/80"},
        },
    )
    assert verified.status == "verified"
    started = service.start_transfusion_safely(transfusion.id, LAB_ID, "nurse-2")
    assert started.status == "in_progress"
    completed = service.complete_transfusion_safely(
        transfusion.id,
        LAB_ID,
        {"post_vitals": {"temperature": 37.1, "blood_pressure": "118/78"}},
    )
    assert completed.status == "completed"
    assert unit.status == "transfused"


def test_lims_reports_require_released_results_and_a_valid_correction_transition(db):
    report = lims_models.LabReport(
        lab_id=LAB_ID,
        order_id=1001,
        report_number="RPT-SAFETY-1",
        status="draft",
        locale="ar",
        generated_by=1,
        created_by=1,
    )
    result = lims_models.Result(
        lab_id=LAB_ID,
        specimen_id=1001,
        order_id=1001,
        test_code="K",
        test_name="Potassium",
        validation_status="pending",
        created_by=1,
    )
    db.add_all([report, result])
    db.flush()

    with pytest.raises(ValueError, match="released"):
        ReportService.finalize(db, report, user_id=2)

    result.validation_status = "released"
    finalized = ReportService.finalize(db, report, user_id=2)
    assert finalized.status == "final"
    assert finalized.version == 2

    with pytest.raises(ValueError, match="reason"):
        ReportService.correct(db, report, "", user_id=2)
    corrected = ReportService.correct(db, report, "Incorrect patient identifier", user_id=2)
    assert corrected.status == "corrected"
    assert corrected.correction_reason == "Incorrect patient identifier"
    assert corrected.version == 3


def test_icu_reads_are_scoped_to_the_callers_institution(db):
    service, admission = _admit_icu_patient(db, patient_id="patient-isolated")
    other_bed = ICUBedModel(
        lab_id=LAB_ID + 1,
        bed_label="OTHER-ICU-01",
        icu_type="adult_icu",
        is_active=True,
        is_occupied=False,
    )
    other_admission = ICUAdmissionModel(
        lab_id=LAB_ID + 1,
        patient_id="patient-isolated",
        bed_id="other-bed",
        status="stable",
        icu_type="adult_icu",
    )
    db.add_all([other_bed, other_admission])
    db.flush()

    assert service.get_admission(admission.id, LAB_ID).id == admission.id
    with pytest.raises(ICUAdmissionNotFoundError):
        service.get_admission(other_admission.id, LAB_ID)
    assert service.list_admissions(LAB_ID, limit=10)[0].id == admission.id
    availability = service.get_bed_availability(LAB_ID)
    assert availability[0]["total"] == 1
