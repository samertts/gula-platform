"""Unit tests for ehr_service — clinical records CRUD, care plans, patient timeline."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from app.domain.exceptions import NotFoundError
from app.ehr.enums import AllergyStatus, ClinicalNoteType, TimelineEventType
from app.ehr.models import (
    AllergyIntolerance,
    CarePlan,
    CarePlanActivity,
    CarePlanGoal,
    ClinicalNote,
    DiagnosisRecord,
    ImmunizationRecord,
    MedicationStatement,
    PatientTimelineEvent,
)
from app.national.domain.patient import Patient as NationalPatient
from app.national.enums import Gender
from app.services import ehr_service
from sqlalchemy.orm import Session


@pytest.fixture()
def national_patient(db: Session) -> NationalPatient:
    p = NationalPatient(
        lab_id=1,
        health_number="IQ-100000",
        first_name="Ali",
        last_name="Ahmed",
        full_name="Ali Ahmed",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
    )
    db.add(p)
    db.flush()
    return p


def _note_data(patient_id: str, title: str = "Progress note") -> dict:
    return {
        "patient_id": patient_id,
        "note_type": ClinicalNoteType.PROGRESS,
        "title": title,
        "title_ar": "ملاحظة تقدم",
        "content": "Patient stable",
    }


def _allergy_data(patient_id: str) -> dict:
    return {
        "patient_id": patient_id,
        "code_display": "Penicillin allergy",
        "code_display_ar": "حساسية البنسلين",
        "status": AllergyStatus.ACTIVE,
        "severity": "severe",
    }


def _medication_data(patient_id: str) -> dict:
    return {
        "patient_id": patient_id,
        "medication_name": "Amoxicillin",
        "medication_name_ar": "أموكسيسيلين",
        "status": "active",
        "date_recorded": datetime.now(UTC),
    }


class TestNationalPatientLookup:
    def test_found(self, db: Session, national_patient):
        patient = ehr_service.get_national_patient_or_404(db, national_patient.id, 1)
        assert patient.id == national_patient.id

    def test_wrong_lab_raises(self, db: Session, national_patient):
        with pytest.raises(NotFoundError):
            ehr_service.get_national_patient_or_404(db, national_patient.id, 999)

    def test_missing_raises(self, db: Session):
        with pytest.raises(NotFoundError):
            ehr_service.get_national_patient_or_404(db, "NOPE", 1)

    def test_deleted_raises(self, db: Session, national_patient):
        national_patient.soft_delete()
        db.flush()
        with pytest.raises(NotFoundError):
            ehr_service.get_national_patient_or_404(db, national_patient.id, 1)


class TestClinicalNote:
    def test_create_get(self, db: Session, national_patient):
        note = ehr_service.create_clinical_note(db, _note_data(national_patient.id))
        assert note.id and note.version == 1
        fetched = ehr_service.get_clinical_note(db, note.id)
        assert fetched and fetched.title == "Progress note"

    def test_get_missing_returns_none(self, db: Session):
        assert ehr_service.get_clinical_note(db, "missing") is None

    def test_update_increments_version(self, db: Session, national_patient):
        note = ehr_service.create_clinical_note(db, _note_data(national_patient.id))
        updated = ehr_service.update_clinical_note(db, note.id, {"content": "Updated"})
        assert updated.content == "Updated"
        assert updated.version == 2

    def test_update_missing_returns_none(self, db: Session):
        assert ehr_service.update_clinical_note(db, "missing", {"title": "x"}) is None

    def test_soft_delete(self, db: Session, national_patient):
        note = ehr_service.create_clinical_note(db, _note_data(national_patient.id))
        assert ehr_service.soft_delete_clinical_note(db, note.id) is True
        assert ehr_service.get_clinical_note(db, note.id) is None
        assert ehr_service.soft_delete_clinical_note(db, "missing") is False

    def test_list_by_patient_excludes_deleted(self, db: Session, national_patient):
        note = ehr_service.create_clinical_note(db, _note_data(national_patient.id))
        other = ehr_service.create_clinical_note(db, _note_data(national_patient.id, "Second"))
        ehr_service.soft_delete_clinical_note(db, note.id)
        listing = ehr_service.list_clinical_notes_by_patient(db, national_patient.id)
        assert [n.id for n in listing] == [other.id]

    def test_list_by_encounter(self, db: Session, national_patient):
        data = _note_data(national_patient.id)
        data["encounter_id"] = "ENC-1"
        ehr_service.create_clinical_note(db, data)
        others = ehr_service.list_clinical_notes_by_encounter(db, "ENC-1")
        assert len(others) == 1
        assert ehr_service.list_clinical_notes_by_encounter(db, "ENC-2") == []


class TestAllergy:
    def test_create_update_delete(self, db: Session, national_patient):
        allergy = ehr_service.create_allergy(db, _allergy_data(national_patient.id))
        assert allergy.id and allergy.status == AllergyStatus.ACTIVE
        updated = ehr_service.update_allergy(db, allergy.id, {"severity": "moderate"})
        assert updated.severity == "moderate"
        assert ehr_service.soft_delete_allergy(db, allergy.id) is True
        assert ehr_service.get_allergy(db, allergy.id) is None

    def test_update_missing(self, db: Session):
        assert ehr_service.update_allergy(db, "missing", {}) is None

    def test_list_by_patient(self, db: Session, national_patient):
        a = ehr_service.create_allergy(db, _allergy_data(national_patient.id))
        ehr_service.soft_delete_allergy(db, a.id)
        assert ehr_service.list_allergies_by_patient(db, national_patient.id) == []


class TestMedication:
    def test_create_get_delete(self, db: Session, national_patient):
        med = ehr_service.create_medication_statement(db, _medication_data(national_patient.id))
        assert med.id and med.medication_name == "Amoxicillin"
        assert ehr_service.get_medication_statement(db, med.id).id == med.id
        assert ehr_service.soft_delete_medication_statement(db, med.id) is True
        assert ehr_service.get_medication_statement(db, med.id) is None

    def test_list_by_patient(self, db: Session, national_patient):
        med = ehr_service.create_medication_statement(db, _medication_data(national_patient.id))
        listing = ehr_service.list_medication_statements_by_patient(db, national_patient.id)
        assert [m.id for m in listing] == [med.id]

    def test_medication_request_and_dispense(self, db: Session, national_patient):
        req = ehr_service.create_medication_request(
            db, {"patient_id": national_patient.id, "medication_name": "Ibuprofen"}
        )
        assert req.id
        disp = ehr_service.create_medication_dispense(
            db,
            {
                "patient_id": national_patient.id,
                "medication_name": "Ibuprofen",
                "quantity": 10,
            },
        )
        assert disp.id
        assert ehr_service.get_medication_request(db, req.id).id == req.id
        assert ehr_service.get_medication_dispense(db, disp.id).id == disp.id
        assert ehr_service.soft_delete_medication_dispense(db, disp.id) is True

    def test_medication_administration(self, db: Session, national_patient):
        admin = ehr_service.create_medication_administration(
            db,
            {
                "patient_id": national_patient.id,
                "medication_name": "Paracetamol",
                "status": "completed",
                "administration_time": datetime.now(UTC),
            },
        )
        assert admin.id
        assert ehr_service.get_medication_administration(db, admin.id).id == admin.id
        assert ehr_service.soft_delete_medication_administration(db, admin.id) is True


class TestCarePlan:
    def test_create_plan_goals_activities(self, db: Session, national_patient):
        plan = ehr_service.create_care_plan(
            db,
            {
                "patient_id": national_patient.id,
                "title": "Diabetes care",
                "title_ar": "رعاية السكري",
                "status": "active",
            },
        )
        assert plan.id
        goal = ehr_service.create_care_plan_goal(
            db,
            {"care_plan_id": plan.id, "description": "HbA1c < 7%"},
        )
        assert goal.id
        activity = ehr_service.create_care_plan_activity(
            db,
            {"care_plan_id": plan.id, "goal_id": goal.id, "description": "Diet review"},
        )
        assert activity.id

        assert [g.id for g in ehr_service.get_care_plan_goals(db, plan.id)] == [goal.id]
        assert [a.id for a in ehr_service.get_care_plan_activities(db, plan_id=plan.id)] == [activity.id]
        assert [a.id for a in ehr_service.get_care_plan_activities(db, goal_id=goal.id)] == [activity.id]
        assert ehr_service.get_care_plan_activities(db, plan_id="other") == []

    def test_plan_update_and_delete(self, db: Session, national_patient):
        plan = ehr_service.create_care_plan(
            db,
            {"patient_id": national_patient.id, "title": "Plan", "status": "draft"},
        )
        updated = ehr_service.update_care_plan(db, plan.id, {"title": "Plan v2"})
        assert updated.title == "Plan v2"
        assert ehr_service.soft_delete_care_plan(db, plan.id) is True
        assert ehr_service.get_care_plan(db, plan.id) is None


class TestTimeline:
    def _event(self, patient_id: str, event_type: TimelineEventType, when: datetime) -> PatientTimelineEvent:
        return PatientTimelineEvent(
            patient_id=patient_id,
            event_type=event_type,
            event_date=when,
            source_type="test",
            source_id="src-1",
            title="Event",
        )

    def test_get_patient_timeline_ordered_and_filtered(self, db: Session, national_patient):
        old = self._event(national_patient.id, TimelineEventType.VISIT, datetime.now(UTC) - timedelta(days=2))
        new = self._event(national_patient.id, TimelineEventType.VISIT, datetime.now(UTC))
        db.add_all([old, new])
        db.flush()
        events = ehr_service.get_patient_timeline(db, national_patient.id)
        assert [e.id for e in events] == [new.id, old.id]
        visits = ehr_service.get_patient_timeline(db, national_patient.id, event_type="visit")
        assert len(visits) == 2
        labs = ehr_service.get_patient_timeline(db, national_patient.id, event_type="lab_result")
        assert labs == []

    def test_timeline_excludes_deleted(self, db: Session, national_patient):
        ev = self._event(national_patient.id, TimelineEventType.VISIT, datetime.now(UTC))
        db.add(ev)
        db.flush()
        ev.soft_delete()
        db.flush()
        assert ehr_service.get_patient_timeline(db, national_patient.id) == []

    def test_build_live_timeline_aggregates_and_orders(self, db: Session, national_patient):
        pid = national_patient.id
        now = datetime.now(UTC)
        note = ehr_service.create_clinical_note(db, _note_data(pid, "Old note"))
        note.authored_at = now - timedelta(days=5)
        allergy = ehr_service.create_allergy(db, _allergy_data(pid))
        allergy.recorded_date = now
        med = ehr_service.create_medication_statement(db, _medication_data(pid))
        med.date_recorded = now - timedelta(days=1)
        db.flush()

        events = ehr_service.build_live_timeline(db, pid)
        types = [e["event_type"] for e in events]
        assert "allergy" in types and "clinical_note" in types and "medication" in types
        assert types[0] == "allergy"
        assert types[-1] == "clinical_note"
        allergy_event = next(e for e in events if e["event_type"] == "allergy")
        assert allergy_event["severity"] == "severe"
        assert allergy_event["source_type"] == "ehr_allergies"

    def test_build_live_timeline_excludes_deleted(self, db: Session, national_patient):
        pid = national_patient.id
        allergy = ehr_service.create_allergy(db, _allergy_data(pid))
        allergy.soft_delete()
        note = ehr_service.create_clinical_note(db, _note_data(pid))
        db.flush()
        events = ehr_service.build_live_timeline(db, pid)
        assert [e["event_type"] for e in events] == ["clinical_note"]

    def test_build_live_timeline_max_per_type(self, db: Session, national_patient):
        pid = national_patient.id
        for i in range(5):
            note = ehr_service.create_clinical_note(db, _note_data(pid, f"Note {i}"))
            note.authored_at = datetime.now(UTC) + timedelta(minutes=i)
        db.flush()
        events = ehr_service.build_live_timeline(db, pid, max_per_type=2)
        notes = [e for e in events if e["event_type"] == "clinical_note"]
        assert len(notes) == 2

    def test_build_live_timeline_empty(self, db: Session, national_patient):
        assert ehr_service.build_live_timeline(db, national_patient.id) == []


class TestOtherRecordTypes:
    def test_condition_diagnosis_immunization(self, db: Session, national_patient):
        pid = national_patient.id
        cond = ehr_service.create_condition(
            db, {"patient_id": pid, "code_display": "Hypertension", "severity": "moderate"}
        )
        assert cond.id
        diag = ehr_service.create_diagnosis(
            db, {"patient_id": pid, "diagnosis_text": "DM Type 2", "diagnosis_text_ar": "سكري"}
        )
        assert diag.id
        imm = ehr_service.create_immunization_record(
            db,
            {
                "patient_id": pid,
                "vaccine_code": "COV-1",
                "vaccine_name": "COVID-19",
                "administration_date": datetime.now(UTC),
            },
        )
        assert imm.id

        assert ehr_service.get_condition(db, cond.id).id == cond.id
        assert ehr_service.get_diagnosis(db, diag.id).id == diag.id
        assert ehr_service.get_immunization_record(db, imm.id).id == imm.id

        assert ehr_service.soft_delete_condition(db, cond.id) is True
        assert ehr_service.soft_delete_diagnosis(db, diag.id) is True
        assert ehr_service.soft_delete_immunization_record(db, imm.id) is True
        assert ehr_service.get_condition(db, cond.id) is None

    def test_social_family_risk(self, db: Session, national_patient):
        pid = national_patient.id
        social = ehr_service.create_social_history_record(
            db, {"patient_id": pid, "smoking_status": "never", "occupation": "Engineer"}
        )
        family = ehr_service.create_family_history_record(
            db,
            {
                "patient_id": pid,
                "relationship": "father",
                "condition_display": "Diabetes",
            },
        )
        risk = ehr_service.create_risk_factor_record(
            db,
            {
                "patient_id": pid,
                "risk_type": "obesity",
                "risk_level": "high",
                "assessment_date": datetime.now(UTC),
            },
        )
        assert social.id and family.id and risk.id
        assert ehr_service.soft_delete_social_history_record(db, social.id) is True
        assert ehr_service.soft_delete_family_history_record(db, family.id) is True
        assert ehr_service.soft_delete_risk_factor_record(db, risk.id) is True

    def test_attachment_crud(self, db: Session, national_patient):
        att = ehr_service.create_clinical_attachment(
            db,
            {
                "patient_id": national_patient.id,
                "source_type": "clinical_note",
                "source_id": "SRC-1",
                "file_name": "scan.pdf",
                "file_type": "application/pdf",
            },
        )
        assert att.id
        assert ehr_service.get_clinical_attachment(db, att.id).id == att.id
        assert len(ehr_service.list_attachments_by_patient(db, national_patient.id)) == 1
        assert ehr_service.soft_delete_clinical_attachment(db, att.id) is True
        assert ehr_service.list_attachments_by_patient(db, national_patient.id) == []
