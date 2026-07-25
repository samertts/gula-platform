from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ehr.models import (
    AllergyIntolerance,
    CarePlan,
    CarePlanActivity,
    CarePlanGoal,
    ClinicalAttachment,
    ClinicalNote,
    ConditionRecord,
    DiagnosisRecord,
    FamilyHistoryRecord,
    ImmunizationRecord,
    MedicationAdministration,
    MedicationDispense,
    MedicationRequest,
    MedicationStatement,
    PatientTimelineEvent,
    ProblemListItem,
    RiskFactorRecord,
    SocialHistoryRecord,
)
from app.national.domain.patient import Patient as NationalPatient


def get_national_patient_or_404(
    db: Session,
    patient_id: str,
    lab_id: int,
) -> NationalPatient:
    patient = (
        db.query(NationalPatient)
        .filter(
            NationalPatient.id == patient_id,
            NationalPatient.lab_id == lab_id,
            NationalPatient.is_deleted.is_(False),
        )
        .first()
    )
    if not patient:
        from app.domain.exceptions import NotFoundError

        raise NotFoundError("Patient not found in your laboratory")
    return patient


def _fmt_ts(val: datetime | None) -> str | None:
    return val.isoformat() if val else None


def _fmt_date(val: date | None) -> str | None:
    return val.isoformat() if val else None


def _to_dict(record: Any) -> dict[str, Any]:
    return record.to_dict() if hasattr(record, "to_dict") else {}


def get_care_plan_goals(db: Session, plan_id: str) -> list[CarePlanGoal]:
    return (
        db.query(CarePlanGoal)
        .filter(
            CarePlanGoal.care_plan_id == plan_id,
            CarePlanGoal.is_deleted.is_(False),
        )
        .all()
    )


def get_care_plan_activities(
    db: Session,
    plan_id: str | None = None,
    goal_id: str | None = None,
) -> list[CarePlanActivity]:
    q = db.query(CarePlanActivity).filter(CarePlanActivity.is_deleted.is_(False))
    if plan_id:
        q = q.filter(CarePlanActivity.care_plan_id == plan_id)
    if goal_id:
        q = q.filter(CarePlanActivity.goal_id == goal_id)
    return q.all()


# ── Clinical Notes ────────────────────────────────────────────────────────


def create_clinical_note(db: Session, data: dict[str, Any]) -> ClinicalNote:
    note = ClinicalNote(**data)
    db.add(note)
    db.flush()
    return note


def get_clinical_note(db: Session, note_id: str) -> ClinicalNote | None:
    return (
        db.query(ClinicalNote)
        .filter(ClinicalNote.id == note_id, ClinicalNote.is_deleted.is_(False))
        .first()
    )


def update_clinical_note(
    db: Session,
    note_id: str,
    data: dict[str, Any],
) -> ClinicalNote | None:
    note = get_clinical_note(db, note_id)
    if not note:
        return None
    for key, value in data.items():
        setattr(note, key, value)
    note.version += 1
    db.flush()
    return note


def soft_delete_clinical_note(db: Session, note_id: str) -> bool:
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        return False
    note.soft_delete()
    db.flush()
    return True


def list_clinical_notes_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[ClinicalNote]:
    return (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.patient_id == patient_id,
            ClinicalNote.is_deleted.is_(False),
        )
        .order_by(ClinicalNote.authored_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_clinical_notes_by_encounter(
    db: Session,
    encounter_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[ClinicalNote]:
    return (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.encounter_id == encounter_id,
            ClinicalNote.is_deleted.is_(False),
        )
        .order_by(ClinicalNote.authored_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Allergies ─────────────────────────────────────────────────────────────


def create_allergy(db: Session, data: dict[str, Any]) -> AllergyIntolerance:
    record = AllergyIntolerance(**data)
    db.add(record)
    db.flush()
    return record


def get_allergy(db: Session, allergy_id: str) -> AllergyIntolerance | None:
    return (
        db.query(AllergyIntolerance)
        .filter(AllergyIntolerance.id == allergy_id, AllergyIntolerance.is_deleted.is_(False))
        .first()
    )


def update_allergy(
    db: Session,
    allergy_id: str,
    data: dict[str, Any],
) -> AllergyIntolerance | None:
    record = get_allergy(db, allergy_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_allergy(db: Session, allergy_id: str) -> bool:
    record = db.query(AllergyIntolerance).filter(AllergyIntolerance.id == allergy_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_allergies_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[AllergyIntolerance]:
    return (
        db.query(AllergyIntolerance)
        .filter(
            AllergyIntolerance.patient_id == patient_id,
            AllergyIntolerance.is_deleted.is_(False),
        )
        .order_by(AllergyIntolerance.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Medication Statements ─────────────────────────────────────────────────


def create_medication_statement(
    db: Session,
    data: dict[str, Any],
) -> MedicationStatement:
    record = MedicationStatement(**data)
    db.add(record)
    db.flush()
    return record


def get_medication_statement(
    db: Session,
    statement_id: str,
) -> MedicationStatement | None:
    return (
        db.query(MedicationStatement)
        .filter(
            MedicationStatement.id == statement_id,
            MedicationStatement.is_deleted.is_(False),
        )
        .first()
    )


def update_medication_statement(
    db: Session,
    statement_id: str,
    data: dict[str, Any],
) -> MedicationStatement | None:
    record = get_medication_statement(db, statement_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_medication_statement(db: Session, statement_id: str) -> bool:
    record = db.query(MedicationStatement).filter(MedicationStatement.id == statement_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_medication_statements_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[MedicationStatement]:
    return (
        db.query(MedicationStatement)
        .filter(
            MedicationStatement.patient_id == patient_id,
            MedicationStatement.is_deleted.is_(False),
        )
        .order_by(MedicationStatement.date_recorded.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Medication Requests ───────────────────────────────────────────────────


def create_medication_request(
    db: Session,
    data: dict[str, Any],
) -> MedicationRequest:
    record = MedicationRequest(**data)
    db.add(record)
    db.flush()
    return record


def get_medication_request(
    db: Session,
    request_id: str,
) -> MedicationRequest | None:
    return (
        db.query(MedicationRequest)
        .filter(
            MedicationRequest.id == request_id,
            MedicationRequest.is_deleted.is_(False),
        )
        .first()
    )


def update_medication_request(
    db: Session,
    request_id: str,
    data: dict[str, Any],
) -> MedicationRequest | None:
    record = get_medication_request(db, request_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_medication_request(db: Session, request_id: str) -> bool:
    record = db.query(MedicationRequest).filter(MedicationRequest.id == request_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_medication_requests_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[MedicationRequest]:
    return (
        db.query(MedicationRequest)
        .filter(
            MedicationRequest.patient_id == patient_id,
            MedicationRequest.is_deleted.is_(False),
        )
        .order_by(MedicationRequest.authored_on.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Medication Dispenses ──────────────────────────────────────────────────


def create_medication_dispense(
    db: Session,
    data: dict[str, Any],
) -> MedicationDispense:
    record = MedicationDispense(**data)
    db.add(record)
    db.flush()
    return record


def get_medication_dispense(
    db: Session,
    dispense_id: str,
) -> MedicationDispense | None:
    return (
        db.query(MedicationDispense)
        .filter(
            MedicationDispense.id == dispense_id,
            MedicationDispense.is_deleted.is_(False),
        )
        .first()
    )


def update_medication_dispense(
    db: Session,
    dispense_id: str,
    data: dict[str, Any],
) -> MedicationDispense | None:
    record = get_medication_dispense(db, dispense_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_medication_dispense(db: Session, dispense_id: str) -> bool:
    record = db.query(MedicationDispense).filter(MedicationDispense.id == dispense_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_medication_dispenses_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[MedicationDispense]:
    return (
        db.query(MedicationDispense)
        .filter(
            MedicationDispense.patient_id == patient_id,
            MedicationDispense.is_deleted.is_(False),
        )
        .order_by(MedicationDispense.dispensed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Medication Administrations ────────────────────────────────────────────


def create_medication_administration(
    db: Session,
    data: dict[str, Any],
) -> MedicationAdministration:
    record = MedicationAdministration(**data)
    db.add(record)
    db.flush()
    return record


def get_medication_administration(
    db: Session,
    admin_id: str,
) -> MedicationAdministration | None:
    return (
        db.query(MedicationAdministration)
        .filter(
            MedicationAdministration.id == admin_id,
            MedicationAdministration.is_deleted.is_(False),
        )
        .first()
    )


def update_medication_administration(
    db: Session,
    admin_id: str,
    data: dict[str, Any],
) -> MedicationAdministration | None:
    record = get_medication_administration(db, admin_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_medication_administration(
    db: Session,
    admin_id: str,
) -> bool:
    record = (
        db.query(MedicationAdministration).filter(MedicationAdministration.id == admin_id).first()
    )
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_medication_administrations_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[MedicationAdministration]:
    return (
        db.query(MedicationAdministration)
        .filter(
            MedicationAdministration.patient_id == patient_id,
            MedicationAdministration.is_deleted.is_(False),
        )
        .order_by(MedicationAdministration.administration_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Care Plans ────────────────────────────────────────────────────────────


def create_care_plan(db: Session, data: dict[str, Any]) -> CarePlan:
    plan = CarePlan(**data)
    db.add(plan)
    db.flush()
    return plan


def get_care_plan(db: Session, plan_id: str) -> CarePlan | None:
    return db.query(CarePlan).filter(CarePlan.id == plan_id, CarePlan.is_deleted.is_(False)).first()


def update_care_plan(
    db: Session,
    plan_id: str,
    data: dict[str, Any],
) -> CarePlan | None:
    plan = get_care_plan(db, plan_id)
    if not plan:
        return None
    for key, value in data.items():
        setattr(plan, key, value)
    db.flush()
    return plan


def soft_delete_care_plan(db: Session, plan_id: str) -> bool:
    plan = db.query(CarePlan).filter(CarePlan.id == plan_id).first()
    if not plan:
        return False
    plan.soft_delete()
    db.flush()
    return True


def list_care_plans_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[CarePlan]:
    return (
        db.query(CarePlan)
        .filter(
            CarePlan.patient_id == patient_id,
            CarePlan.is_deleted.is_(False),
        )
        .order_by(CarePlan.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Care Plan Goals ───────────────────────────────────────────────────────


def create_care_plan_goal(db: Session, data: dict[str, Any]) -> CarePlanGoal:
    goal = CarePlanGoal(**data)
    db.add(goal)
    db.flush()
    return goal


def get_care_plan_goal(db: Session, goal_id: str) -> CarePlanGoal | None:
    return (
        db.query(CarePlanGoal)
        .filter(CarePlanGoal.id == goal_id, CarePlanGoal.is_deleted.is_(False))
        .first()
    )


def update_care_plan_goal(
    db: Session,
    goal_id: str,
    data: dict[str, Any],
) -> CarePlanGoal | None:
    goal = get_care_plan_goal(db, goal_id)
    if not goal:
        return None
    for key, value in data.items():
        setattr(goal, key, value)
    db.flush()
    return goal


def soft_delete_care_plan_goal(db: Session, goal_id: str) -> bool:
    goal = db.query(CarePlanGoal).filter(CarePlanGoal.id == goal_id).first()
    if not goal:
        return False
    goal.soft_delete()
    db.flush()
    return True


# ── Care Plan Activities ──────────────────────────────────────────────────


def create_care_plan_activity(
    db: Session,
    data: dict[str, Any],
) -> CarePlanActivity:
    activity = CarePlanActivity(**data)
    db.add(activity)
    db.flush()
    return activity


def get_care_plan_activity(
    db: Session,
    activity_id: str,
) -> CarePlanActivity | None:
    return (
        db.query(CarePlanActivity)
        .filter(
            CarePlanActivity.id == activity_id,
            CarePlanActivity.is_deleted.is_(False),
        )
        .first()
    )


def update_care_plan_activity(
    db: Session,
    activity_id: str,
    data: dict[str, Any],
) -> CarePlanActivity | None:
    activity = get_care_plan_activity(db, activity_id)
    if not activity:
        return None
    for key, value in data.items():
        setattr(activity, key, value)
    db.flush()
    return activity


def soft_delete_care_plan_activity(db: Session, activity_id: str) -> bool:
    activity = db.query(CarePlanActivity).filter(CarePlanActivity.id == activity_id).first()
    if not activity:
        return False
    activity.soft_delete()
    db.flush()
    return True


# ── Problem List ──────────────────────────────────────────────────────────


def create_problem_list_item(db: Session, data: dict[str, Any]) -> ProblemListItem:
    record = ProblemListItem(**data)
    db.add(record)
    db.flush()
    return record


def get_problem_list_item(
    db: Session,
    item_id: str,
) -> ProblemListItem | None:
    return (
        db.query(ProblemListItem)
        .filter(
            ProblemListItem.id == item_id,
            ProblemListItem.is_deleted.is_(False),
        )
        .first()
    )


def update_problem_list_item(
    db: Session,
    item_id: str,
    data: dict[str, Any],
) -> ProblemListItem | None:
    record = get_problem_list_item(db, item_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_problem_list_item(db: Session, item_id: str) -> bool:
    record = db.query(ProblemListItem).filter(ProblemListItem.id == item_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_problem_list_items_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[ProblemListItem]:
    return (
        db.query(ProblemListItem)
        .filter(
            ProblemListItem.patient_id == patient_id,
            ProblemListItem.is_deleted.is_(False),
        )
        .order_by(ProblemListItem.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Conditions ────────────────────────────────────────────────────────────


def create_condition(db: Session, data: dict[str, Any]) -> ConditionRecord:
    record = ConditionRecord(**data)
    db.add(record)
    db.flush()
    return record


def get_condition(db: Session, condition_id: str) -> ConditionRecord | None:
    return (
        db.query(ConditionRecord)
        .filter(
            ConditionRecord.id == condition_id,
            ConditionRecord.is_deleted.is_(False),
        )
        .first()
    )


def update_condition(
    db: Session,
    condition_id: str,
    data: dict[str, Any],
) -> ConditionRecord | None:
    record = get_condition(db, condition_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_condition(db: Session, condition_id: str) -> bool:
    record = db.query(ConditionRecord).filter(ConditionRecord.id == condition_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_conditions_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[ConditionRecord]:
    return (
        db.query(ConditionRecord)
        .filter(
            ConditionRecord.patient_id == patient_id,
            ConditionRecord.is_deleted.is_(False),
        )
        .order_by(ConditionRecord.recorded_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Diagnoses ─────────────────────────────────────────────────────────────


def create_diagnosis(db: Session, data: dict[str, Any]) -> DiagnosisRecord:
    record = DiagnosisRecord(**data)
    db.add(record)
    db.flush()
    return record


def get_diagnosis(db: Session, diagnosis_id: str) -> DiagnosisRecord | None:
    return (
        db.query(DiagnosisRecord)
        .filter(
            DiagnosisRecord.id == diagnosis_id,
            DiagnosisRecord.is_deleted.is_(False),
        )
        .first()
    )


def update_diagnosis(
    db: Session,
    diagnosis_id: str,
    data: dict[str, Any],
) -> DiagnosisRecord | None:
    record = get_diagnosis(db, diagnosis_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_diagnosis(db: Session, diagnosis_id: str) -> bool:
    record = db.query(DiagnosisRecord).filter(DiagnosisRecord.id == diagnosis_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_diagnoses_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[DiagnosisRecord]:
    return (
        db.query(DiagnosisRecord)
        .filter(
            DiagnosisRecord.patient_id == patient_id,
            DiagnosisRecord.is_deleted.is_(False),
        )
        .order_by(DiagnosisRecord.diagnosis_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Family History ────────────────────────────────────────────────────────


def create_family_history_record(
    db: Session,
    data: dict[str, Any],
) -> FamilyHistoryRecord:
    record = FamilyHistoryRecord(**data)
    db.add(record)
    db.flush()
    return record


def get_family_history_record(
    db: Session,
    record_id: str,
) -> FamilyHistoryRecord | None:
    return (
        db.query(FamilyHistoryRecord)
        .filter(
            FamilyHistoryRecord.id == record_id,
            FamilyHistoryRecord.is_deleted.is_(False),
        )
        .first()
    )


def update_family_history_record(
    db: Session,
    record_id: str,
    data: dict[str, Any],
) -> FamilyHistoryRecord | None:
    record = get_family_history_record(db, record_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_family_history_record(db: Session, record_id: str) -> bool:
    record = db.query(FamilyHistoryRecord).filter(FamilyHistoryRecord.id == record_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_family_history_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[FamilyHistoryRecord]:
    return (
        db.query(FamilyHistoryRecord)
        .filter(
            FamilyHistoryRecord.patient_id == patient_id,
            FamilyHistoryRecord.is_deleted.is_(False),
        )
        .order_by(FamilyHistoryRecord.recorded_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Social History ────────────────────────────────────────────────────────


def create_social_history_record(
    db: Session,
    data: dict[str, Any],
) -> SocialHistoryRecord:
    record = SocialHistoryRecord(**data)
    db.add(record)
    db.flush()
    return record


def get_social_history_record(
    db: Session,
    record_id: str,
) -> SocialHistoryRecord | None:
    return (
        db.query(SocialHistoryRecord)
        .filter(
            SocialHistoryRecord.id == record_id,
            SocialHistoryRecord.is_deleted.is_(False),
        )
        .first()
    )


def update_social_history_record(
    db: Session,
    record_id: str,
    data: dict[str, Any],
) -> SocialHistoryRecord | None:
    record = get_social_history_record(db, record_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_social_history_record(db: Session, record_id: str) -> bool:
    record = db.query(SocialHistoryRecord).filter(SocialHistoryRecord.id == record_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_social_history_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[SocialHistoryRecord]:
    return (
        db.query(SocialHistoryRecord)
        .filter(
            SocialHistoryRecord.patient_id == patient_id,
            SocialHistoryRecord.is_deleted.is_(False),
        )
        .order_by(SocialHistoryRecord.recorded_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Risk Factors ──────────────────────────────────────────────────────────


def create_risk_factor_record(
    db: Session,
    data: dict[str, Any],
) -> RiskFactorRecord:
    record = RiskFactorRecord(**data)
    db.add(record)
    db.flush()
    return record


def get_risk_factor_record(
    db: Session,
    record_id: str,
) -> RiskFactorRecord | None:
    return (
        db.query(RiskFactorRecord)
        .filter(
            RiskFactorRecord.id == record_id,
            RiskFactorRecord.is_deleted.is_(False),
        )
        .first()
    )


def update_risk_factor_record(
    db: Session,
    record_id: str,
    data: dict[str, Any],
) -> RiskFactorRecord | None:
    record = get_risk_factor_record(db, record_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_risk_factor_record(db: Session, record_id: str) -> bool:
    record = db.query(RiskFactorRecord).filter(RiskFactorRecord.id == record_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_risk_factors_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[RiskFactorRecord]:
    return (
        db.query(RiskFactorRecord)
        .filter(
            RiskFactorRecord.patient_id == patient_id,
            RiskFactorRecord.is_deleted.is_(False),
        )
        .order_by(RiskFactorRecord.assessment_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Immunizations ─────────────────────────────────────────────────────────


def create_immunization_record(
    db: Session,
    data: dict[str, Any],
) -> ImmunizationRecord:
    record = ImmunizationRecord(**data)
    db.add(record)
    db.flush()
    return record


def get_immunization_record(
    db: Session,
    record_id: str,
) -> ImmunizationRecord | None:
    return (
        db.query(ImmunizationRecord)
        .filter(
            ImmunizationRecord.id == record_id,
            ImmunizationRecord.is_deleted.is_(False),
        )
        .first()
    )


def update_immunization_record(
    db: Session,
    record_id: str,
    data: dict[str, Any],
) -> ImmunizationRecord | None:
    record = get_immunization_record(db, record_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_immunization_record(db: Session, record_id: str) -> bool:
    record = db.query(ImmunizationRecord).filter(ImmunizationRecord.id == record_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_immunizations_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[ImmunizationRecord]:
    return (
        db.query(ImmunizationRecord)
        .filter(
            ImmunizationRecord.patient_id == patient_id,
            ImmunizationRecord.is_deleted.is_(False),
        )
        .order_by(ImmunizationRecord.administration_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Clinical Attachments ──────────────────────────────────────────────────


def create_clinical_attachment(
    db: Session,
    data: dict[str, Any],
) -> ClinicalAttachment:
    record = ClinicalAttachment(**data)
    db.add(record)
    db.flush()
    return record


def get_clinical_attachment(
    db: Session,
    attachment_id: str,
) -> ClinicalAttachment | None:
    return (
        db.query(ClinicalAttachment)
        .filter(
            ClinicalAttachment.id == attachment_id,
            ClinicalAttachment.is_deleted.is_(False),
        )
        .first()
    )


def update_clinical_attachment(
    db: Session,
    attachment_id: str,
    data: dict[str, Any],
) -> ClinicalAttachment | None:
    record = get_clinical_attachment(db, attachment_id)
    if not record:
        return None
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def soft_delete_clinical_attachment(db: Session, attachment_id: str) -> bool:
    record = db.query(ClinicalAttachment).filter(ClinicalAttachment.id == attachment_id).first()
    if not record:
        return False
    record.soft_delete()
    db.flush()
    return True


def list_attachments_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[ClinicalAttachment]:
    return (
        db.query(ClinicalAttachment)
        .filter(
            ClinicalAttachment.patient_id == patient_id,
            ClinicalAttachment.is_deleted.is_(False),
        )
        .order_by(ClinicalAttachment.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_attachments_by_source(
    db: Session,
    source_type: str,
    source_id: str,
) -> list[ClinicalAttachment]:
    return (
        db.query(ClinicalAttachment)
        .filter(
            ClinicalAttachment.source_type == source_type,
            ClinicalAttachment.source_id == source_id,
            ClinicalAttachment.is_deleted.is_(False),
        )
        .order_by(ClinicalAttachment.sort_order, ClinicalAttachment.uploaded_at.desc())
        .all()
    )


# ── Patient Timeline ─────────────────────────────────────────────────────


def get_patient_timeline(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 100,
    event_type: str | None = None,
) -> list[PatientTimelineEvent]:
    q = db.query(PatientTimelineEvent).filter(
        PatientTimelineEvent.patient_id == patient_id,
        PatientTimelineEvent.is_deleted.is_(False),
    )
    if event_type:
        q = q.filter(PatientTimelineEvent.event_type == event_type)
    return q.order_by(PatientTimelineEvent.event_date.desc()).offset(skip).limit(limit).all()


def build_live_timeline(
    db: Session,
    patient_id: str,
    max_per_type: int = 10,
) -> list[dict[str, Any]]:
    """Aggregate events from multiple EHR tables into a unified timeline."""
    events: list[dict[str, Any]] = []

    for allergy in (
        db.query(AllergyIntolerance)
        .filter(
            AllergyIntolerance.patient_id == patient_id,
            AllergyIntolerance.is_deleted.is_(False),
        )
        .order_by(AllergyIntolerance.recorded_date.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "allergy",
                "event_date": _fmt_ts(allergy.recorded_date or allergy.created_at),
                "title": allergy.code_display,
                "title_ar": allergy.code_display_ar,
                "severity": allergy.severity,
                "source_id": allergy.id,
                "source_type": "ehr_allergies",
            }
        )

    for condition in (
        db.query(ConditionRecord)
        .filter(
            ConditionRecord.patient_id == patient_id,
            ConditionRecord.is_deleted.is_(False),
        )
        .order_by(ConditionRecord.recorded_date.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "condition",
                "event_date": _fmt_ts(condition.recorded_date or condition.created_at),
                "title": condition.code_display,
                "title_ar": condition.code_display_ar,
                "severity": condition.severity,
                "source_id": condition.id,
                "source_type": "ehr_conditions",
            }
        )

    for diagnosis in (
        db.query(DiagnosisRecord)
        .filter(
            DiagnosisRecord.patient_id == patient_id,
            DiagnosisRecord.is_deleted.is_(False),
        )
        .order_by(DiagnosisRecord.created_at.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "diagnosis",
                "event_date": _fmt_ts(diagnosis.created_at),
                "title": diagnosis.diagnosis_text,
                "title_ar": diagnosis.diagnosis_text_ar,
                "source_id": diagnosis.id,
                "source_type": "ehr_diagnoses",
            }
        )

    for med in (
        db.query(MedicationStatement)
        .filter(
            MedicationStatement.patient_id == patient_id,
            MedicationStatement.is_deleted.is_(False),
        )
        .order_by(MedicationStatement.date_recorded.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "medication",
                "event_date": _fmt_ts(med.date_recorded or med.created_at),
                "title": med.medication_name,
                "title_ar": med.medication_name_ar,
                "source_id": med.id,
                "source_type": "ehr_medication_statements",
            }
        )

    for note in (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.patient_id == patient_id,
            ClinicalNote.is_deleted.is_(False),
        )
        .order_by(ClinicalNote.authored_at.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "clinical_note",
                "event_date": _fmt_ts(note.authored_at),
                "title": note.title,
                "title_ar": note.title_ar,
                "note_type": note.note_type,
                "source_id": note.id,
                "source_type": "ehr_clinical_notes",
            }
        )

    for immun in (
        db.query(ImmunizationRecord)
        .filter(
            ImmunizationRecord.patient_id == patient_id,
            ImmunizationRecord.is_deleted.is_(False),
        )
        .order_by(ImmunizationRecord.administration_date.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "immunization",
                "event_date": _fmt_ts(immun.administration_date),
                "title": immun.vaccine_name,
                "title_ar": immun.vaccine_name_ar,
                "source_id": immun.id,
                "source_type": "ehr_immunizations",
            }
        )

    for cp in (
        db.query(CarePlan)
        .filter(
            CarePlan.patient_id == patient_id,
            CarePlan.is_deleted.is_(False),
        )
        .order_by(CarePlan.created_at.desc())
        .limit(max_per_type)
        .all()
    ):
        events.append(
            {
                "event_type": "care_plan",
                "event_date": _fmt_ts(cp.created_at),
                "title": cp.title,
                "title_ar": cp.title_ar,
                "status": cp.status,
                "source_id": cp.id,
                "source_type": "ehr_care_plans",
            }
        )

    events.sort(key=lambda e: e.get("event_date") or "", reverse=True)
    return events
