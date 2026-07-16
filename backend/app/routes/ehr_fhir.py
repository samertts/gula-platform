from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..ehr.models import (
    AllergyIntolerance,
    CarePlan,
    ClinicalAttachment,
    ClinicalNote,
    ConditionRecord,
    DiagnosisRecord,
    ImmunizationRecord,
    MedicationRequest,
    MedicationStatement,
)
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..national.domain.encounter import Encounter
from ..security.dependencies import get_current_user
from ..services import ehr_service

router = APIRouter(prefix="/fhir", tags=["fhir"])


def _fmt_fhir_datetime(val: datetime | None) -> str | None:
    return val.isoformat() if val else None


def _fmt_fhir_date(val: date | None) -> str | None:
    return val.isoformat() if val else None


def _patient_ref(patient_id: str) -> dict:
    return {"reference": f"Patient/{patient_id}", "type": "Patient"}


def _practitioner_ref(practitioner_id: str | None) -> dict | None:
    if not practitioner_id:
        return None
    return {"reference": f"Practitioner/{practitioner_id}", "type": "Practitioner"}


def _encounter_ref(encounter_id: str | None) -> dict | None:
    if not encounter_id:
        return None
    return {"reference": f"Encounter/{encounter_id}", "type": "Encounter"}


def _codeable_concept(
    code: str | None, display: str | None, system: str | None = None
) -> dict | None:
    if not code and not display:
        return None
    coding: list[dict] = []
    if code:
        c: dict[str, Any] = {"code": code}
        if system:
            c["system"] = system
        if display:
            c["display"] = display
        coding.append(c)
    result: dict[str, Any] = {}
    if coding:
        result["coding"] = coding
    if display and not code:
        result["text"] = display
    return result


# ── Patient (proxy) ───────────────────────────────────────────────────────


@router.get("/Patient/{patient_id}", summary="FHIR Patient resource")
def fhir_read_patient(
    patient_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = ehr_service.get_national_patient_or_404(db, patient_id, current_user.lab_id)
    name_parts = [
        p
        for p in [
            patient.first_name,
            patient.father_name,
            patient.grandfather_name,
            patient.last_name,
        ]
        if p
    ]
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [
            {"system": "urn:gula:health-number", "value": patient.health_number},
        ],
        "name": [{"family": patient.last_name, "given": [patient.first_name], "text": " ".join(name_parts)}],
        "gender": patient.gender.value if patient.gender else None,
        "birthDate": _fmt_fhir_date(patient.date_of_birth),
        "telecom": (
            [{"system": "phone", "value": patient.phone}] if patient.phone else []
        ),
        "address": (
            [
                {
                    "line": [patient.address_line] if patient.address_line else [],
                    "city": patient.district or "",
                    "state": patient.governorate or "",
                }
            ]
            if any([patient.address_line, patient.governorate])
            else []
        ),
        "meta": {
            "versionId": str(patient.version),
            "lastUpdated": _fmt_fhir_datetime(patient.updated_at),
        },
    }


# ── Encounter (proxy) ────────────────────────────────────────────────────


@router.get("/Encounter/{encounter_id}", summary="FHIR Encounter resource")
def fhir_read_encounter(
    encounter_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    encounter = (
        db.query(Encounter)
        .filter(Encounter.id == encounter_id, Encounter.is_deleted.is_(False))
        .first()
    )
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    ehr_service.get_national_patient_or_404(
        db, encounter.patient_id, current_user.lab_id
    )
    return {
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": encounter.status.value if encounter.status else "unknown",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": encounter.encounter_type.value if encounter.encounter_type else "OTHER",
        },
        "subject": _patient_ref(encounter.patient_id),
        "participant": (
            [
                {
                    "individual": _practitioner_ref(encounter.practitioner_id),
                }
            ]
            if encounter.practitioner_id
            else []
        ),
        "period": {
            "start": _fmt_fhir_datetime(encounter.period_start),
            "end": _fmt_fhir_datetime(encounter.period_end),
        },
        "reasonCode": (
            [_codeable_concept(encounter.reason_code, encounter.reason_description)]
            if encounter.reason_code or encounter.reason_description
            else []
        ),
        "diagnosis": (
            [
                {
                    "condition": {
                        "reference": f"Condition?encounter={encounter_id}",
                        "display": encounter.diagnosis_description,
                    }
                }
            ]
            if encounter.diagnosis_description
            else []
        ),
        "meta": {
            "versionId": str(encounter.version),
            "lastUpdated": _fmt_fhir_datetime(encounter.updated_at),
        },
    }


# ── Condition ────────────────────────────────────────────────────────────


@router.get("/Condition/{condition_id}", summary="FHIR Condition resource")
def fhir_read_condition(
    condition_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(ConditionRecord)
        .filter(ConditionRecord.id == condition_id, ConditionRecord.is_deleted.is_(False))
        .first()
    )
    if not record:
        record = (
            db.query(DiagnosisRecord)
            .filter(DiagnosisRecord.id == condition_id, DiagnosisRecord.is_deleted.is_(False))
            .first()
        )
    if not record:
        raise HTTPException(status_code=404, detail="Condition not found")
    patient_id = record.patient_id
    ehr_service.get_national_patient_or_404(db, patient_id, current_user.lab_id)

    if isinstance(record, DiagnosisRecord):
        return _diagnosis_to_fhir_condition(record)
    return _condition_to_fhir_condition(record)


def _condition_to_fhir_condition(rec: ConditionRecord) -> dict:
    return {
        "resourceType": "Condition",
        "id": rec.id,
        "clinicalStatus": _codeable_concept(
            rec.clinical_status, rec.clinical_status, "http://terminology.hl7.org/CodeSystem/condition-clinical"
        ),
        "verificationStatus": _codeable_concept(
            rec.verification_status,
            rec.verification_status,
            "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        ),
        "category": [_codeable_concept(rec.category, rec.category)] if rec.category else [],
        "code": _codeable_concept(rec.code, rec.code_display, rec.code_system),
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "onsetDateTime": _fmt_fhir_date(rec.onset_date),
        "abatementDateTime": _fmt_fhir_date(rec.abatement_date),
        "recordedDate": _fmt_fhir_datetime(rec.recorded_date),
        "bodySite": [_codeable_concept(rec.body_site, rec.body_site)] if rec.body_site else [],
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


def _diagnosis_to_fhir_condition(rec: DiagnosisRecord) -> dict:
    return {
        "resourceType": "Condition",
        "id": rec.id,
        "clinicalStatus": _codeable_concept(
            "active" if rec.is_active else "resolved",
            "Active" if rec.is_active else "Resolved",
            "http://terminology.hl7.org/CodeSystem/condition-clinical",
        ),
        "code": _codeable_concept(rec.icd10_code, rec.icd10_description, "http://hl7.org/fhir/sid/icd-10"),
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "onsetDateTime": _fmt_fhir_date(rec.diagnosis_date),
        "abatementDateTime": _fmt_fhir_date(rec.resolution_date),
        "recordedDate": _fmt_fhir_datetime(rec.created_at),
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


@router.get("/Condition", summary="FHIR Condition search")
def fhir_search_condition(
    patient: str | None = Query(None, alias="patient"),
    encounter: str | None = Query(None, alias="encounter"),
    clinical_status: str | None = Query(None, alias="clinical-status"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [],
        "total": 0,
    }
    conditions = db.query(ConditionRecord).filter(ConditionRecord.is_deleted.is_(False))
    diagnoses = db.query(DiagnosisRecord).filter(DiagnosisRecord.is_deleted.is_(False))
    if patient:
        conditions = conditions.filter(ConditionRecord.patient_id == patient)
        diagnoses = diagnoses.filter(DiagnosisRecord.patient_id == patient)
    if clinical_status:
        conditions = conditions.filter(ConditionRecord.clinical_status == clinical_status)
    if encounter:
        conditions = conditions.filter(ConditionRecord.encounter_id == encounter)
        diagnoses = diagnoses.filter(DiagnosisRecord.encounter_id == encounter)
    conditions = conditions.all()
    diagnoses = diagnoses.all()
    entries = [_condition_to_fhir_condition(c) for c in conditions]
    entries.extend(_diagnosis_to_fhir_condition(d) for d in diagnoses)
    bundle["entry"] = [{"resource": e, "fullUrl": f"Condition/{e['id']}"} for e in entries]
    bundle["total"] = len(entries)
    return bundle


# ── Observation (lab results) ────────────────────────────────────────────


@router.get("/Observation/{observation_id}", summary="FHIR Observation for a lab result")
def fhir_read_observation(
    observation_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = (
        db.query(LabResult)
        .join(LabOrder)
        .filter(LabResult.id == observation_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Observation not found")
    order = (
        db.query(LabOrder)
        .filter(LabOrder.id == result.order_id, LabOrder.lab_id == current_user.lab_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=403,
            detail="Access denied: observation does not belong to your laboratory",
        )
    return _lab_result_to_observation(result, order)


def _lab_result_to_observation(result: LabResult, order: LabOrder) -> dict:
    obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": str(result.id),
        "status": "final",
        "code": _codeable_concept(result.test_name, result.test_name) or {"text": result.test_name},
        "subject": {"reference": f"Patient/{order.patient_id}", "type": "Patient"},
        "effectiveDateTime": _fmt_fhir_datetime(order.created_at),
        "issued": _fmt_fhir_datetime(result.created_at),
    }
    if result.value is not None:
        obs["valueQuantity"] = {
            "value": result.value,
            "unit": result.unit or "",
        }
    elif result.value_text:
        obs["valueString"] = result.value_text
    if result.normal_range_low is not None or result.normal_range_high is not None:
        ref: dict[str, Any] = {}
        if result.normal_range_low is not None:
            ref["low"] = {"value": result.normal_range_low}
        if result.normal_range_high is not None:
            ref["high"] = {"value": result.normal_range_high}
        obs["referenceRange"] = [ref]
    if result.flag:
        obs["interpretation"] = [
            _codeable_concept(result.flag, result.flag, "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation")
        ]
    obs["meta"] = {
        "versionId": "1",
        "lastUpdated": _fmt_fhir_datetime(result.created_at),
    }
    return obs


@router.get("/Observation", summary="FHIR Observation search")
def fhir_search_observation(
    patient: str | None = Query(None, alias="patient"),
    code: str | None = Query(None, alias="code"),
    category: str | None = Query(None, alias="category"),
    date: str | None = Query(None, alias="date"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [],
        "total": 0,
    }
    q = (
        db.query(LabResult)
        .join(LabOrder)
        .filter(LabOrder.lab_id == current_user.lab_id)
    )
    if patient:
        q = q.filter(LabOrder.patient_id == patient)
    if code:
        q = q.filter(LabResult.test_name.ilike(f"%{code}%"))
    results = q.order_by(LabResult.created_at.desc()).limit(100).all()
    entries = []
    for r in results:
        order = (
            db.query(LabOrder).filter(LabOrder.id == r.order_id).first()
        )
        if order:
            entries.append(
                {
                    "resource": _lab_result_to_observation(r, order),
                    "fullUrl": f"Observation/{r.id}",
                }
            )
    bundle["entry"] = entries
    bundle["total"] = len(entries)
    return bundle


# ── MedicationRequest ────────────────────────────────────────────────────


@router.get("/MedicationRequest/{request_id}", summary="FHIR MedicationRequest")
def fhir_read_medication_request(
    request_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_request(db, request_id)
    if not record:
        raise HTTPException(status_code=404, detail="MedicationRequest not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _medication_request_to_fhir(record)


def _medication_request_to_fhir(rec: MedicationRequest) -> dict:
    return {
        "resourceType": "MedicationRequest",
        "id": rec.id,
        "status": rec.status.value if hasattr(rec.status, "value") else rec.status,
        "intent": rec.intent,
        "medicationCodeableConcept": _codeable_concept(
            rec.medication_code, rec.medication_name, rec.medication_code_system
        )
        or {"text": rec.medication_name},
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "requester": _practitioner_ref(rec.prescriber_id),
        "dosageInstruction": (
            [
                {
                    "text": rec.dosage_instruction,
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                    "route": _codeable_concept(rec.route, rec.route),
                    "doseAndRate": (
                        [
                            {
                                "doseQuantity": {
                                    "value": rec.quantity,
                                    "unit": rec.quantity_unit or "",
                                }
                            }
                        ]
                        if rec.quantity
                        else []
                    ),
                }
            ]
            if rec.dosage_instruction
            else []
        ),
        "dispenseRequest": {
            "numberOfRepeatsAllowed": rec.refills or 0,
            "quantity": (
                {"value": rec.quantity, "unit": rec.quantity_unit or ""} if rec.quantity else None
            ),
            "validityPeriod": {
                "start": _fmt_fhir_date(rec.valid_from),
                "end": _fmt_fhir_date(rec.valid_to),
            },
        },
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


@router.get("/MedicationRequest", summary="FHIR MedicationRequest search")
def fhir_search_medication_request(
    patient: str | None = Query(None, alias="patient"),
    status: str | None = Query(None, alias="status"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    q = db.query(MedicationRequest).filter(MedicationRequest.is_deleted.is_(False))
    if patient:
        q = q.filter(MedicationRequest.patient_id == patient)
    if status:
        q = q.filter(MedicationRequest.status == status)
    records = q.order_by(MedicationRequest.authored_on.desc()).limit(100).all()
    entries = [
        {"resource": _medication_request_to_fhir(r), "fullUrl": f"MedicationRequest/{r.id}"}
        for r in records
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": entries,
        "total": len(entries),
    }


# ── MedicationStatement ──────────────────────────────────────────────────


@router.get("/MedicationStatement/{statement_id}", summary="FHIR MedicationStatement")
def fhir_read_medication_statement(
    statement_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_medication_statement(db, statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="MedicationStatement not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _medication_statement_to_fhir(record)


def _medication_statement_to_fhir(rec: MedicationStatement) -> dict:
    return {
        "resourceType": "MedicationStatement",
        "id": rec.id,
        "status": rec.status or "unknown",
        "medicationCodeableConcept": _codeable_concept(
            rec.medication_code, rec.medication_name, rec.medication_code_system
        )
        or {"text": rec.medication_name},
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "informationSource": _practitioner_ref(rec.practitioner_id),
        "effectiveDateTime": _fmt_fhir_date(rec.date_started),
        "dateAsserted": _fmt_fhir_datetime(rec.date_recorded),
        "dosage": (
            [
                {
                    "text": rec.dosage_text,
                    "route": _codeable_concept(rec.route, rec.route),
                    "doseAndRate": (
                        [
                            {
                                "doseQuantity": {
                                    "value": rec.strength_value,
                                    "unit": rec.strength_unit or "",
                                }
                            }
                        ]
                        if rec.strength_value
                        else []
                    ),
                }
            ]
            if rec.dosage_text
            else []
        ),
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


# ── CarePlan ─────────────────────────────────────────────────────────────


@router.get("/CarePlan/{plan_id}", summary="FHIR CarePlan resource")
def fhir_read_care_plan(
    plan_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_care_plan(db, plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="CarePlan not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _care_plan_to_fhir(db, record)


def _care_plan_to_fhir(db: Session, rec: CarePlan) -> dict:
    goals = ehr_service.get_care_plan_goals(db, rec.id)
    return {
        "resourceType": "CarePlan",
        "id": rec.id,
        "status": rec.status.value if hasattr(rec.status, "value") else rec.status,
        "intent": rec.intent,
        "category": [_codeable_concept(rec.category, rec.category)] if rec.category else [],
        "title": rec.title,
        "description": rec.description,
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "period": {
            "start": _fmt_fhir_date(rec.period_start),
            "end": _fmt_fhir_date(rec.period_end),
        },
        "goal": [
            {
                "reference": f"Goal/{g.id}",
                "display": g.description,
            }
            for g in goals
        ],
        "activity": [
            {
                "detail": {
                    "code": _codeable_concept(a.activity_code, a.description, a.activity_code_system),
                    "status": a.status,
                    "scheduledPeriod": {
                        "start": _fmt_fhir_date(a.scheduled_start),
                        "end": _fmt_fhir_date(a.scheduled_end),
                    },
                }
            }
            for a in ehr_service.get_care_plan_activities(db, plan_id=rec.id)
        ],
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


# ── Procedure (placeholder) ──────────────────────────────────────────────


@router.get("/Procedure/{procedure_id}", summary="FHIR Procedure resource")
def fhir_read_procedure(
    procedure_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raise HTTPException(status_code=501, detail="Procedure FHIR resource not yet implemented")


# ── AllergyIntolerance ───────────────────────────────────────────────────


@router.get("/AllergyIntolerance/{allergy_id}", summary="FHIR AllergyIntolerance")
def fhir_read_allergy(
    allergy_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_allergy(db, allergy_id)
    if not record:
        raise HTTPException(status_code=404, detail="AllergyIntolerance not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _allergy_to_fhir(record)


def _allergy_to_fhir(rec: AllergyIntolerance) -> dict:
    return {
        "resourceType": "AllergyIntolerance",
        "id": rec.id,
        "clinicalStatus": _codeable_concept(
            rec.status.value if hasattr(rec.status, "value") else rec.status,
            rec.status.value if hasattr(rec.status, "value") else rec.status,
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
        ),
        "verificationStatus": _codeable_concept(
            rec.verification_status,
            rec.verification_status,
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
        ),
        "type": rec.allergy_type.upper() if rec.allergy_type else None,
        "category": [rec.category] if rec.category else [],
        "criticality": rec.criticality,
        "code": _codeable_concept(rec.code, rec.code_display, rec.code_system)
        or {"text": rec.code_display},
        "patient": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "onsetDateTime": _fmt_fhir_date(rec.onset_date),
        "recordedDate": _fmt_fhir_datetime(rec.recorded_date),
        "reaction": (
            [
                {
                    "manifestation": [{"text": rec.reaction}],
                    "severity": rec.severity.value if hasattr(rec.severity, "value") else rec.severity,
                }
            ]
            if rec.reaction
            else []
        ),
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


@router.get("/AllergyIntolerance", summary="FHIR AllergyIntolerance search")
def fhir_search_allergy(
    patient: str | None = Query(None, alias="patient"),
    clinical_status: str | None = Query(None, alias="clinical-status"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    q = db.query(AllergyIntolerance).filter(AllergyIntolerance.is_deleted.is_(False))
    if patient:
        q = q.filter(AllergyIntolerance.patient_id == patient)
    if clinical_status:
        q = q.filter(AllergyIntolerance.status == clinical_status)
    records = q.order_by(AllergyIntolerance.created_at.desc()).limit(100).all()
    entries = [
        {"resource": _allergy_to_fhir(r), "fullUrl": f"AllergyIntolerance/{r.id}"}
        for r in records
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": entries,
        "total": len(entries),
    }


# ── Immunization ─────────────────────────────────────────────────────────


@router.get("/Immunization/{immunization_id}", summary="FHIR Immunization")
def fhir_read_immunization(
    immunization_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_immunization_record(db, immunization_id)
    if not record:
        raise HTTPException(status_code=404, detail="Immunization not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _immunization_to_fhir(record)


def _immunization_to_fhir(rec: ImmunizationRecord) -> dict:
    return {
        "resourceType": "Immunization",
        "id": rec.id,
        "status": rec.status or "completed",
        "vaccineCode": _codeable_concept(
            rec.vaccine_code, rec.vaccine_name, rec.vaccine_code_system
        )
        or {"text": rec.vaccine_name},
        "patient": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "occurrenceDateTime": _fmt_fhir_datetime(rec.administration_date),
        "recorded": _fmt_fhir_datetime(rec.recorded_date),
        "manufacturer": _codeable_concept(None, rec.manufacturer) if rec.manufacturer else None,
        "lotNumber": rec.lot_number,
        "expirationDate": _fmt_fhir_date(rec.expiry_date),
        "doseQuantity": (
            {
                "value": float(rec.dose_quantity) if rec.dose_quantity else None,
                "unit": rec.dose_unit or "",
            }
            if rec.dose_quantity
            else None
        ),
        "site": _codeable_concept(rec.site, rec.site) if rec.site else None,
        "route": _codeable_concept(rec.route, rec.route) if rec.route else None,
        "performer": (
            [
                {
                    "function": _codeable_concept("AP", "Administering Provider"),
                    "actor": _practitioner_ref(rec.administrator_id),
                }
            ]
            if rec.administrator_id
            else []
        ),
        "protocolApplied": (
            [
                {
                    "doseNumberPositiveInt": rec.dose_number,
                    "seriesDosesPositiveInt": rec.total_doses,
                }
            ]
            if rec.dose_number
            else []
        ),
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


@router.get("/Immunization", summary="FHIR Immunization search")
def fhir_search_immunization(
    patient: str | None = Query(None, alias="patient"),
    status: str | None = Query(None, alias="status"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    q = db.query(ImmunizationRecord).filter(ImmunizationRecord.is_deleted.is_(False))
    if patient:
        q = q.filter(ImmunizationRecord.patient_id == patient)
    if status:
        q = q.filter(ImmunizationRecord.status == status)
    records = q.order_by(ImmunizationRecord.administration_date.desc()).limit(100).all()
    entries = [
        {"resource": _immunization_to_fhir(r), "fullUrl": f"Immunization/{r.id}"}
        for r in records
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": entries,
        "total": len(entries),
    }


# ── DocumentReference (clinical attachments) ─────────────────────────────


@router.get("/DocumentReference/{doc_id}", summary="FHIR DocumentReference")
def fhir_read_document_reference(
    doc_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_attachment(db, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="DocumentReference not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _attachment_to_document_reference(record)


def _attachment_to_document_reference(rec: ClinicalAttachment) -> dict:
    return {
        "resourceType": "DocumentReference",
        "id": rec.id,
        "status": "current",
        "type": _codeable_concept(rec.file_type, rec.file_type),
        "category": [_codeable_concept(rec.category, rec.category)] if rec.category else [],
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "author": [_practitioner_ref(rec.uploaded_by)] if rec.uploaded_by else [],
        "description": rec.description or rec.caption or "",
        "content": [
            {
                "attachment": {
                    "contentType": rec.mime_type or "application/octet-stream",
                    "url": rec.storage_path or "",
                    "size": rec.file_size_bytes,
                    "hash": rec.content_hash,
                    "title": rec.file_name,
                }
            }
        ],
        "context": {
            "period": {
                "start": _fmt_fhir_datetime(rec.uploaded_at),
            },
            "encounter": [_encounter_ref(rec.encounter_id)] if rec.encounter_id else [],
        },
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


@router.get("/DocumentReference", summary="FHIR DocumentReference search")
def fhir_search_document_reference(
    patient: str | None = Query(None, alias="patient"),
    category: str | None = Query(None, alias="category"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    q = db.query(ClinicalAttachment).filter(ClinicalAttachment.is_deleted.is_(False))
    if patient:
        q = q.filter(ClinicalAttachment.patient_id == patient)
    if category:
        q = q.filter(ClinicalAttachment.category == category)
    records = q.order_by(ClinicalAttachment.uploaded_at.desc()).limit(100).all()
    entries = [
        {
            "resource": _attachment_to_document_reference(r),
            "fullUrl": f"DocumentReference/{r.id}",
        }
        for r in records
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": entries,
        "total": len(entries),
    }


# ── Composition (clinical notes) ─────────────────────────────────────────


@router.get("/Composition/{composition_id}", summary="FHIR Composition for a clinical note")
def fhir_read_composition(
    composition_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_note(db, composition_id)
    if not record:
        raise HTTPException(status_code=404, detail="Composition not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)
    return _clinical_note_to_composition(record)


def _clinical_note_to_composition(rec: ClinicalNote) -> dict:
    section_text = rec.content or ""
    return {
        "resourceType": "Composition",
        "id": rec.id,
        "status": "final" if rec.is_final else "preliminary",
        "type": _codeable_concept(
            rec.note_type.value if hasattr(rec.note_type, "value") else rec.note_type,
            rec.title,
        ),
        "subject": _patient_ref(rec.patient_id),
        "encounter": _encounter_ref(rec.encounter_id),
        "date": _fmt_fhir_datetime(rec.authored_at),
        "author": [_practitioner_ref(rec.author_id)] if rec.author_id else [],
        "title": rec.title or rec.title_ar or "",
        "confidentiality": "N",
        "attester": (
            [
                {
                    "mode": "legal",
                    "time": _fmt_fhir_datetime(rec.signed_at),
                    "party": _practitioner_ref(rec.signed_by),
                }
            ]
            if rec.is_signed
            else []
        ),
        "section": [
            {
                "title": rec.title,
                "code": _codeable_concept(
                    rec.note_type.value if hasattr(rec.note_type, "value") else rec.note_type,
                    rec.title,
                ),
                "text": {
                    "status": "additional",
                    "div": f'<div xmlns="http://www.w3.org/1999/xhtml">{section_text}</div>',
                },
            }
        ],
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


@router.get("/Composition", summary="FHIR Composition search")
def fhir_search_composition(
    patient: str | None = Query(None, alias="patient"),
    status: str | None = Query(None, alias="status"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    q = db.query(ClinicalNote).filter(ClinicalNote.is_deleted.is_(False))
    if patient:
        q = q.filter(ClinicalNote.patient_id == patient)
    if status:
        if status == "final":
            q = q.filter(ClinicalNote.is_final.is_(True))
        elif status == "preliminary":
            q = q.filter(ClinicalNote.is_final.is_(False))
    records = q.order_by(ClinicalNote.authored_at.desc()).limit(100).all()
    entries = [
        {
            "resource": _clinical_note_to_composition(r),
            "fullUrl": f"Composition/{r.id}",
        }
        for r in records
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": entries,
        "total": len(entries),
    }


# ── Bundle (generic search results) ──────────────────────────────────────


@router.get("/Bundle/{bundle_id}", summary="FHIR Bundle read")
def fhir_read_bundle(
    bundle_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raise HTTPException(status_code=501, detail="Bundle read not implemented; use search endpoints")
