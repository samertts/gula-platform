"""Regression tests for P0 pharmacy and radiology safety workflows."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.pharmacy.enums import DispenseStatus
from app.pharmacy.services import PharmacyService, PharmacyWorkflowError
from app.radiology.enums import ExamStatus, ModalityType, ReportStatus
from app.radiology.models import RadiologyExam, RadiologyReport
from app.radiology.services import RadiologyService, RadiologyWorkflowError


class _FakeSession:
    def flush(self) -> None:
        return None


def _queue_entry() -> SimpleNamespace:
    return SimpleNamespace(
        id="QUEUE-WORKFLOW-001",
        status=DispenseStatus.PENDING,
        version=1,
        assigned_to=None,
        ready_time=None,
        completion_time=None,
    )


def test_dispense_workflow_requires_legal_order_and_independent_verifier():
    entry = _queue_entry()
    preparer_service = PharmacyService(_FakeSession(), user_id=101, lab_id=1)
    verifier_service = PharmacyService(_FakeSession(), user_id=202, lab_id=1)
    for service in (preparer_service, verifier_service):
        service.get_dispense_queue_entry = lambda _queue_id, *, for_update: entry  # type: ignore[method-assign]
        service._audit = lambda *args, **kwargs: None  # type: ignore[method-assign]

    with pytest.raises(PharmacyWorkflowError, match="illegal dispense transition"):
        preparer_service.complete_dispense(entry.id, expected_version=entry.version)

    prepared = preparer_service.prepare_dispense(entry.id, expected_version=entry.version)
    assert prepared is not None
    assert prepared.status == DispenseStatus.PREPARED
    assert prepared.assigned_to == "101"
    assert prepared.version == 2

    with pytest.raises(PharmacyWorkflowError, match="cannot verify their own"):
        preparer_service.verify_dispense(entry.id, expected_version=prepared.version)

    verified = verifier_service.verify_dispense(entry.id, expected_version=prepared.version)
    assert verified is not None
    assert verified.status == DispenseStatus.VERIFIED
    assert verified.version == 3


def _exam(db, *, status: ExamStatus = ExamStatus.SCHEDULED) -> RadiologyExam:
    exam = RadiologyExam(
        patient_id="RAD-PATIENT-001",
        accession_number="ACC-WORKFLOW-001",
        modality=ModalityType.CT,
        status=status,
    )
    db.add(exam)
    db.flush()
    return exam


def test_exam_workflow_rejects_skipped_state_transition(db):
    exam = _exam(db)
    service = RadiologyService(db)

    with pytest.raises(RadiologyWorkflowError, match="illegal examination transition"):
        service.update_exam_status(
            exam.id,
            ExamStatus.COMPLETED,
            expected_version=exam.version,
        )

    checked_in = service.update_exam_status(
        exam.id,
        ExamStatus.CHECKED_IN,
        expected_version=exam.version,
    )
    assert checked_in is not None
    assert checked_in.status == ExamStatus.CHECKED_IN
    assert checked_in.version == 2


def test_report_verification_requires_second_reviewer_and_critical_acknowledgement_is_sequenced(db):
    exam = _exam(db, status=ExamStatus.COMPLETED)
    report = RadiologyReport(
        exam_id=exam.id,
        accession_number=exam.accession_number,
        patient_id=exam.patient_id,
        status=ReportStatus.DRAFT,
        findings="Acute finding",
        impression="Urgent review required",
    )
    db.add(report)
    db.flush()
    service = RadiologyService(db)

    finalized = service.finalize_report(
        report.id,
        expected_version=report.version,
        radiologist_id="reader-1",
    )
    assert finalized is not None
    assert finalized.status == ReportStatus.FINAL

    with pytest.raises(RadiologyWorkflowError, match="second qualified reviewer"):
        service.verify_report(
            report.id,
            expected_version=finalized.version,
            verified_by="reader-1",
        )

    verified = service.verify_report(
        report.id,
        expected_version=finalized.version,
        verified_by="reader-2",
    )
    assert verified is not None
    assert verified.verified_at is not None

    finding = service.create_critical_finding(
        exam.id,
        "critical_red",
        "Immediate escalation required",
        report_id=report.id,
    )
    with pytest.raises(RadiologyWorkflowError, match="only a notified"):
        service.acknowledge_critical_finding(
            finding.id,
            expected_version=finding.version,
            acknowledged_by="recipient-1",
        )

    notified = service.notify_critical_finding(
        finding.id,
        expected_version=finding.version,
        notified_by="reader-1",
        notified_to="recipient-1",
    )
    assert notified is not None
    acknowledged = service.acknowledge_critical_finding(
        finding.id,
        expected_version=notified.version,
        acknowledged_by="recipient-1",
    )
    assert acknowledged is not None
    assert acknowledged.status.value == "acknowledged"
    assert acknowledged.acknowledgement_time is not None
