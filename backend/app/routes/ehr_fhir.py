from __future__ import annotations

from datetime import date, datetime
from html import escape
import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app._compat import UTC

from ..audit import audit_log
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
from ..fhir.terminology import (
    interpretation_concept,
    observation_code,
    observation_status,
    test_matches_code,
)
from ..models.audit_log import AuditLog
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..national.domain.encounter import Encounter
from ..security.dependencies import get_current_user
from ..services import ehr_service

logger = logging.getLogger("gula.fhir")

class FHIRJSONResponse(JSONResponse):
    """FHIR R4 JSON representation for successful external exchange requests."""

    media_type = "application/fhir+json"


router = APIRouter(
    prefix="/fhir",
    tags=["fhir"],
    default_response_class=FHIRJSONResponse,
)

_SUPPORTED_CREATE = frozenset({
    "AllergyIntolerance", "CarePlan", "Composition", "Condition",
    "DocumentReference", "Encounter", "Immunization", "MedicationRequest",
    "MedicationStatement", "Observation", "Patient", "Procedure",
})
_SUPPORTED_UPDATE = frozenset({
    "AllergyIntolerance", "CarePlan", "Composition", "Condition",
    "DocumentReference", "Encounter", "Immunization", "MedicationRequest",
    "MedicationStatement", "Observation", "Patient", "Procedure",
})
_SUPPORTED_DELETE = frozenset({
    "AllergyIntolerance", "CarePlan", "Composition", "Condition",
    "DocumentReference", "Encounter", "Immunization", "MedicationRequest",
    "MedicationStatement", "Observation", "Procedure",
})


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
    code: str | None, display: str | None, system: str | None = None,
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


@router.get("/metadata", summary="FHIR CapabilityStatement")
def fhir_metadata(
    current_user: LabUser = Depends(get_current_user),
):
    """Expose the standard FHIR discovery resource to authenticated partners."""
    # The dependency intentionally enforces the same tenant-aware authentication
    # policy as every clinical exchange endpoint.
    del current_user
    from app.fhir._capabilities import get_capability_statement

    return get_capability_statement()


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
                },
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
        db, encounter.patient_id, current_user.lab_id,
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
                },
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
                    },
                },
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
            rec.clinical_status, rec.clinical_status, "http://terminology.hl7.org/CodeSystem/condition-clinical",
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
        # 404, not 403. A 403 here distinguished "this id does not exist" from
        # "it exists but belongs to another laboratory", which is a cross-tenant
        # existence oracle: iterating ids reveals another lab's result count and
        # id range. Every sibling FHIR read route in this module already answers
        # 404 for both cases; Observation was the only one that did not.
        raise HTTPException(status_code=404, detail="Observation not found")
    return _lab_result_to_observation(result, order)


def _lab_result_to_observation(result: LabResult, order: LabOrder) -> dict:
    obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": str(result.id),
        # Verification lives on the order: a doctor or admin verifying a result
        # sets lab_orders.status = "validated" and locks the row. Reporting every
        # result as "final" told a consumer that an unverified result — and a
        # result whose order had been *cancelled* — was clinician-validated.
        "status": observation_status(order.status),
        "code": observation_code(result.test_name),
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
    # GULA's flag vocabulary is not v3-ObservationInterpretation's: "critical",
    # "normal" and "unknown" are not codes in that system, and publishing them
    # under its URI asserted codes that do not exist. The internal value is kept
    # as `text` so nothing is lost. See fhir/terminology.interpretation_concept.
    interpretation = interpretation_concept(
        result.flag,
        result.value,
        result.normal_range_low,
        result.normal_range_high,
    )
    if interpretation is not None:
        obs["interpretation"] = [interpretation]
    obs["meta"] = {
        # lab_results.version is the optimistic-lock counter, incremented on
        # every mutation, so an amended result is no longer published as v1.
        "versionId": str(result.version if result.version is not None else 1),
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
    results = q.order_by(LabResult.created_at.desc()).limit(100).all()
    if code:
        results = [result for result in results if test_matches_code(result.test_name, code)]
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
                },
            )
    bundle["entry"] = entries
    bundle["total"] = len(entries)
    return bundle


# ── Provenance (tamper-evident audit projection) ──────────────────────────


def _audit_details(entry: AuditLog) -> dict[str, Any]:
    """Read structured audit details safely; legacy text is deliberately ignored."""
    if not entry.details:
        return {}
    try:
        parsed = json.loads(entry.details)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _audit_log_to_provenance(entry: AuditLog, target: str) -> dict[str, Any]:
    """Project a scoped, hash-chained audit event into a FHIR R4 Provenance."""
    resource: dict[str, Any] = {
        "resourceType": "Provenance",
        "id": str(entry.id),
        "target": [{"reference": target}],
        "recorded": _fmt_fhir_datetime(entry.created_at),
        "activity": {
            "coding": [{
                "system": "urn:gula:audit-action",
                "code": entry.action,
                "display": entry.action.replace(".", " ").title(),
            }],
        },
        "agent": [{
            "type": {"text": "authenticated user"},
            "who": {"identifier": {"system": "urn:gula:user-id", "value": str(entry.user_id)}},
        }],
    }
    if entry.chain_hash:
        resource["extension"] = [{
            "url": "https://gula.health/fhir/StructureDefinition/audit-chain-hash",
            "valueString": entry.chain_hash,
        }]
    return resource


@router.get("/Provenance", summary="FHIR Provenance search from tenant-scoped audit records")
def fhir_search_provenance(
    target: str = Query(..., description="FHIR target reference, for example Observation/123"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return audit lineage for one target without exposing another tenant's events."""
    if "/" not in target or target.startswith("/") or target.endswith("/"):
        raise HTTPException(status_code=422, detail="target must be a FHIR ResourceType/id reference")

    resource_type, resource_id = target.split("/", 1)
    if not resource_type or not resource_id or "/" in resource_id:
        raise HTTPException(status_code=422, detail="target must be a FHIR ResourceType/id reference")

    events = (
        db.query(AuditLog)
        .filter(AuditLog.lab_id == current_user.lab_id, AuditLog.resource_type == "FHIR")
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(500)
        .all()
    )
    matching_events = [
        event
        for event in events
        if _audit_details(event).get("fhir_resource_type") == resource_type
        and _audit_details(event).get("fhir_resource_id") == resource_id
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(matching_events),
        "entry": [
            {"fullUrl": f"Provenance/{event.id}", "resource": _audit_log_to_provenance(event, target)}
            for event in matching_events
        ],
    }


# ── Aggregate population health analytics (no patient identifiers) ─────────


@router.get("/analytics/population-summary", summary="Aggregate laboratory population summary")
def fhir_population_summary(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Provide a tenant-local aggregate only; no patient or result values are returned."""
    rows = (
        db.query(LabResult.flag, func.count(LabResult.id))
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .filter(LabOrder.lab_id == current_user.lab_id)
        .group_by(LabResult.flag)
        .all()
    )
    distribution = {str(flag or "unflagged"): int(count) for flag, count in rows}
    total = sum(distribution.values())
    critical_count = sum(
        count
        for flag, count in distribution.items()
        if flag.strip().casefold() in {"critical", "crit", "c"}
    )
    result_distribution = [
        {
            "name": "resultDistribution",
            "part": [
                {"name": "flag", "valueString": flag},
                {"name": "count", "valueInteger": count},
            ],
        }
        for flag, count in sorted(distribution.items())
    ]
    return {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "testVolume", "valueInteger": total},
            {"name": "criticalValueCount", "valueInteger": critical_count},
            {
                "name": "criticalValueRate",
                "valueDecimal": round(critical_count / total, 6) if total else 0,
            },
            *result_distribution,
        ],
    }


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
            rec.medication_code, rec.medication_name, rec.medication_code_system,
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
                                },
                            },
                        ]
                        if rec.quantity
                        else []
                    ),
                },
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
            rec.medication_code, rec.medication_name, rec.medication_code_system,
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
                                },
                            },
                        ]
                        if rec.strength_value
                        else []
                    ),
                },
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
                },
            }
            for a in ehr_service.get_care_plan_activities(db, plan_id=rec.id)
        ],
        "meta": {
            "versionId": str(rec.version),
            "lastUpdated": _fmt_fhir_datetime(rec.updated_at),
        },
    }


# ── Procedure (from clinical notes with procedure type) ──────────────────


@router.get("/Procedure/{procedure_id}", summary="FHIR Procedure resource")
def fhir_read_procedure(
    procedure_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ehr_service.get_clinical_note(db, procedure_id)
    if not record:
        raise HTTPException(status_code=404, detail="Procedure not found")
    ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)

    from app.national.fhir.procedure import FHIRProcedureMapper

    data = {
        "id": record.id,
        "status": "completed" if record.is_final else "in-progress",
        "code": record.note_type.value if hasattr(record.note_type, "value") else str(record.note_type or ""),
        "display": record.title or "",
        "display_ar": record.title_ar or "",
        "performed_start": _fmt_fhir_datetime(record.authored_at),
        "practitioner_id": record.author_id,
        "notes": record.content[:500] if record.content else "",
    }
    return FHIRProcedureMapper.from_dict(data, patient_id=record.patient_id, encounter_id=record.encounter_id)


@router.get("/Procedure", summary="FHIR Procedure search")
def fhir_search_procedure(
    patient: str | None = Query(None, alias="patient"),
    status: str | None = Query(None, alias="status"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if patient:
        ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)
    from app.ehr.models.clinical_note import ClinicalNote
    q = db.query(ClinicalNote).filter(ClinicalNote.is_deleted.is_(False))
    if patient:
        q = q.filter(ClinicalNote.patient_id == patient)
    if status:
        if status == "completed":
            q = q.filter(ClinicalNote.is_final.is_(True))
        elif status == "in-progress":
            q = q.filter(ClinicalNote.is_final.is_(False))
    records = q.order_by(ClinicalNote.authored_at.desc()).limit(100).all()

    from app.national.fhir.procedure import FHIRProcedureMapper
    entries = []
    for r in records:
        data = {
            "id": r.id,
            "status": "completed" if r.is_final else "in-progress",
            "code": r.note_type.value if hasattr(r.note_type, "value") else str(r.note_type or ""),
            "display": r.title or "",
            "performed_start": _fmt_fhir_datetime(r.authored_at),
            "practitioner_id": r.author_id,
            "notes": (r.content or "")[:300],
        }
        resource = FHIRProcedureMapper.from_dict(data, patient_id=r.patient_id, encounter_id=r.encounter_id)
        entries.append({"resource": resource, "fullUrl": f"Procedure/{r.id}"})
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": entries,
        "total": len(entries),
    }


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
                },
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
            rec.vaccine_code, rec.vaccine_name, rec.vaccine_code_system,
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
                },
            ]
            if rec.administrator_id
            else []
        ),
        "protocolApplied": (
            [
                {
                    "doseNumberPositiveInt": rec.dose_number,
                    "seriesDosesPositiveInt": rec.total_doses,
                },
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
                },
            },
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
    # Clinical notes are user-authored. Escape them before embedding in a FHIR
    # Narrative XHTML div so downstream renderers never execute supplied markup.
    section_text = escape(rec.content or "")
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
                },
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
            },
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


# ── Bundle / Patient-everything ──────────────────────────────────────────


@router.get("/Patient/{patient_id}/$everything", summary="FHIR Patient $everything operation")
def fhir_patient_everything(
    patient_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the tenant-scoped FHIR R4 record collection for one patient."""
    return fhir_read_bundle(patient_id, current_user, db)


@router.get("/Bundle/{bundle_id}", summary="FHIR Bundle read - returns patient-everything")
def fhir_read_bundle(
    bundle_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ehr_service.get_national_patient_or_404(db, bundle_id, current_user.lab_id)
    patient_resource = fhir_read_patient(bundle_id, current_user, db)
    entries = [{"resource": patient_resource, "fullUrl": f"Patient/{bundle_id}"}]

    encounters = (
        db.query(Encounter)
        .filter(Encounter.patient_id == bundle_id, Encounter.is_deleted.is_(False))
        .limit(50)
        .all()
    )
    for enc in encounters:
        entries.append({
            "resource": {
                "resourceType": "Encounter",
                "id": enc.id,
                "status": enc.status.value if enc.status else "unknown",
                "subject": {"reference": f"Patient/{bundle_id}"},
                "period": {
                    "start": _fmt_fhir_datetime(enc.period_start),
                    "end": _fmt_fhir_datetime(enc.period_end),
                },
            },
            "fullUrl": f"Encounter/{enc.id}",
        })

    from app.ehr.models.clinical_note import ClinicalNote
    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.patient_id == bundle_id, ClinicalNote.is_deleted.is_(False))
        .limit(50)
        .all()
    )
    for note in notes:
        entries.append({
            "resource": {
                "resourceType": "Composition",
                "id": note.id,
                "status": "final" if note.is_final else "preliminary",
                "subject": {"reference": f"Patient/{bundle_id}"},
                "title": note.title or "",
                "date": _fmt_fhir_datetime(note.authored_at),
            },
            "fullUrl": f"Composition/{note.id}",
        })

    from app.ehr.models import ConditionRecord
    conditions = (
        db.query(ConditionRecord)
        .filter(ConditionRecord.patient_id == bundle_id, ConditionRecord.is_deleted.is_(False))
        .limit(50)
        .all()
    )
    for cond in conditions:
        entries.append({
            "resource": {
                "resourceType": "Condition",
                "id": cond.id,
                "subject": {"reference": f"Patient/{bundle_id}"},
                "code": {"text": cond.code_display or ""},
                "clinicalStatus": {"coding": [{"code": cond.clinical_status or "active"}]},
            },
            "fullUrl": f"Condition/{cond.id}",
        })

    from ..models.lab_order import LabOrder
    from ..models.lab_result import LabResult
    orders = (
        db.query(LabOrder)
        .filter(LabOrder.patient_id == bundle_id, LabOrder.lab_id == current_user.lab_id)
        .limit(50)
        .all()
    )
    for order in orders:
        entries.append({
            "resource": {
                "resourceType": "ServiceRequest",
                "id": str(order.id),
                "status": order.status or "unknown",
                "intent": "order",
                "subject": {"reference": f"Patient/{bundle_id}"},
                "code": {"text": order.test_name or ""},
                "authoredOn": _fmt_fhir_datetime(order.created_at),
            },
            "fullUrl": f"ServiceRequest/{order.id}",
        })
        results = (
            db.query(LabResult)
            .filter(LabResult.order_id == order.id)
            .limit(50)
            .all()
        )
        for r in results:
            entries.append({
                "resource": {
                    "resourceType": "Observation",
                    "id": str(r.id),
                    "status": "final",
                    "code": {"text": r.test_name or ""},
                    "subject": {"reference": f"Patient/{bundle_id}"},
                    "valueQuantity": {"value": r.value, "unit": r.unit or ""} if r.value is not None else None,
                    "effectiveDateTime": _fmt_fhir_datetime(order.created_at),
                },
                "fullUrl": f"Observation/{r.id}",
            })

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "entry": entries,
        "total": len(entries),
    }


# ── Generic Create ──────────────────────────────────────────────────────


@router.post("/{resource_type}", summary="FHIR Create resource", status_code=201)
@audit_log(action="fhir.create")
def fhir_create_resource(
    resource_type: str,
    body: dict[str, Any],
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if resource_type not in _SUPPORTED_CREATE:
        raise HTTPException(status_code=422, detail=f"Create not supported for {resource_type}")
    resource_id = str(uuid4())
    now = datetime.now(UTC)
    patient_id = _extract_patient_ref(body)
    encounter_id = _extract_encounter_ref(body)
    if patient_id and resource_type != "Patient":
        ehr_service.get_national_patient_or_404(db, patient_id, current_user.lab_id)
    _create_fhir_resource(db, resource_type, resource_id, body, patient_id, encounter_id, current_user, now)
    return {"resourceType": resource_type, "id": resource_id}


# ── Generic Update ──────────────────────────────────────────────────────


@router.put("/{resource_type}/{resource_id}", summary="FHIR Update resource")
@audit_log(action="fhir.update")
def fhir_update_resource(
    resource_type: str,
    resource_id: str,
    body: dict[str, Any],
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if resource_type not in _SUPPORTED_UPDATE:
        raise HTTPException(status_code=422, detail=f"Update not supported for {resource_type}")
    _get_fhir_resource_or_404(db, resource_type, resource_id, current_user)
    now = datetime.now(UTC)
    patient_id = _extract_patient_ref(body)
    encounter_id = _extract_encounter_ref(body)
    _update_fhir_resource(db, resource_type, resource_id, body, patient_id, encounter_id, current_user, now)
    return {"resourceType": resource_type, "id": resource_id}


# ── Generic Delete (soft-delete) ────────────────────────────────────────


@router.delete("/{resource_type}/{resource_id}", summary="FHIR Delete resource")
@audit_log(action="fhir.delete")
def fhir_delete_resource(
    resource_type: str,
    resource_id: str,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if resource_type not in _SUPPORTED_DELETE:
        raise HTTPException(status_code=422, detail=f"Delete not supported for {resource_type}")
    record = _get_fhir_resource_or_404(db, resource_type, resource_id, current_user)
    if hasattr(record, "is_deleted"):
        record.is_deleted = True
    if hasattr(record, "deleted_at"):
        record.deleted_at = datetime.now(UTC)
    if hasattr(record, "deleted_by"):
        record.deleted_by = current_user.id
    return {"resourceType": resource_type, "id": resource_id, "status": "deleted"}


# ── Batch / Transaction support ─────────────────────────────────────────


@router.post("", summary="FHIR Batch or Transaction")
@audit_log(action="fhir.batch")
def fhir_batch(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bundle_type = body.get("type", "batch")
    if bundle_type not in ("batch", "transaction"):
        raise HTTPException(status_code=422, detail=f"Unsupported bundle type: {bundle_type}")
    entries = body.get("entry", [])
    results: list[dict[str, Any]] = []
    any_entry_failed = False
    for entry in entries:
        resource = entry.get("resource", {})
        rt = resource.get("resourceType", "")
        req = entry.get("request", {})
        method = req.get("method", "POST").upper()
        url = req.get("url", "")
        resource_id = url.split("/")[-1] if "/" in url else str(uuid4())
        status_code = 200
        try:
            if method == "POST":
                if rt in _SUPPORTED_CREATE:
                    now = datetime.now(UTC)
                    pid = _extract_patient_ref(resource)
                    eid = _extract_encounter_ref(resource)
                    _create_fhir_resource(db, rt, resource_id, resource, pid, eid, current_user, now)
                    status_code = 201
                else:
                    status_code = 422
            elif method == "PUT":
                if rt in _SUPPORTED_UPDATE:
                    rec = db.query(_fhir_model_class(rt)).filter_by(id=resource_id).first()
                    if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:
                        status_code = 403
                    elif rec:
                        now = datetime.now(UTC)
                        pid = _extract_patient_ref(resource)
                        eid = _extract_encounter_ref(resource)
                        _update_fhir_resource(db, rt, resource_id, resource, pid, eid, current_user, now)
                    else:
                        status_code = 404
                else:
                    status_code = 422
            elif method == "DELETE":
                if rt in _SUPPORTED_DELETE:
                    rec = db.query(_fhir_model_class(rt)).filter_by(id=resource_id).first()
                    if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:
                        status_code = 403
                    elif rec:
                        if hasattr(rec, "is_deleted"):
                            rec.is_deleted = True
                        if hasattr(rec, "deleted_at"):
                            rec.deleted_at = datetime.now(UTC)
                        if hasattr(rec, "deleted_by"):
                            rec.deleted_by = current_user.id
                    else:
                        status_code = 404
                else:
                    status_code = 422
            else:
                status_code = 405
        except HTTPException as exc:
            status_code = exc.status_code
        if bundle_type == "batch":
            # A batch bundle's entries are independent interactions, so a 2xx
            # here has to mean this entry is durable whatever the others did.
            # Without this the endpoint reported 201 and discarded the write:
            # get_db never commits, and closing the session rolls it back.
            if 200 <= status_code < 300:
                try:
                    db.commit()
                except SQLAlchemyError:
                    # The store rejected the row this entry claimed to create.
                    # Not trying is what let the old code answer 201 anyway.
                    logger.exception("FHIR batch entry could not be persisted: %s/%s", rt, resource_id)
                    db.rollback()
                    status_code = 500
            else:
                db.rollback()
        if not 200 <= status_code < 300:
            any_entry_failed = True
        results.append({
            "resourceType": "Bundle",
            "type": bundle_type,
            "entry": [{"response": {"status": str(status_code), "location": f"{rt}/{resource_id}"}}],
        })
    if bundle_type == "transaction":
        # A transaction bundle is all-or-nothing, so one failed entry must not
        # leave the others persisted. It previously committed regardless.
        statuses = [
            e["entry"][0]["response"]["status"] for e in results
        ]
        if any_entry_failed:
            db.rollback()
            # And the caller must not be handed a bundle of 201s for writes that
            # were just discarded -- that is the same false success as the batch
            # path, one level up.
            raise HTTPException(
                status_code=422,
                detail=f"transaction bundle rolled back; no entry was applied: {statuses}",
            )
        try:
            db.commit()
        except SQLAlchemyError:
            logger.exception("FHIR transaction bundle could not be committed")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="transaction bundle could not be committed; no entry was applied",
            ) from None
    return {"resourceType": "Bundle", "type": f"{bundle_type}-response", "entry": results}


# ── Generic helpers ─────────────────────────────────────────────────────


def _extract_patient_ref(body: dict) -> str | None:
    subj = body.get("subject") or body.get("patient") or {}
    if isinstance(subj, dict):
        ref = subj.get("reference", "")
        if ref.startswith("Patient/"):
            return ref.split("/", 1)[1]
    return None


def _extract_encounter_ref(body: dict) -> str | None:
    enc = body.get("encounter") or {}
    if isinstance(enc, dict):
        ref = enc.get("reference", "")
        if ref.startswith("Encounter/"):
            return ref.split("/", 1)[1]
    return None


def _fhir_model_class(resource_type: str):
    from ..ehr.models import (
        AllergyIntolerance as AI,
    )
    from ..ehr.models import (
        CarePlan as CP,
    )
    from ..ehr.models import (
        ClinicalAttachment as CA,
    )
    from ..ehr.models import (
        ClinicalNote as CN,
    )
    from ..ehr.models import (
        ConditionRecord as CR,
    )
    from ..ehr.models import (
        DiagnosisRecord as DR,
    )
    from ..ehr.models import (
        ImmunizationRecord as IR,
    )
    from ..ehr.models import (
        MedicationRequest as MR,
    )
    from ..ehr.models import (
        MedicationStatement as MS,
    )
    from ..national.domain.encounter import Encounter as EncModel
    _map: dict[str, Any] = {
        "AllergyIntolerance": AI, "CarePlan": CP, "Composition": CN,
        "Condition": CR, "DiagnosisRecord": DR, "DocumentReference": CA,
        "Encounter": EncModel, "Immunization": IR, "MedicationRequest": MR,
        "MedicationStatement": MS,
    }
    return _map.get(resource_type)


def _get_fhir_resource_or_404(db: Session, resource_type: str, resource_id: str, user: LabUser):
    model = _fhir_model_class(resource_type)
    if not model:
        raise HTTPException(status_code=422, detail=f"Unknown resource type: {resource_type}")
    record = db.query(model).filter(model.id == resource_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{resource_type} not found")
    if hasattr(record, "is_deleted") and record.is_deleted:
        raise HTTPException(status_code=410, detail=f"{resource_type} has been deleted")
    if hasattr(record, "lab_id") and getattr(record, "lab_id", None) and record.lab_id != user.lab_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if hasattr(record, "patient_id") and getattr(record, "patient_id", None):
        ehr_service.get_national_patient_or_404(db, record.patient_id, user.lab_id)
    return record


def _create_fhir_resource(
    db: Session, resource_type: str, resource_id: str, body: dict[str, Any],
    patient_id: str | None, encounter_id: str | None,
    user: LabUser, now: datetime,
):
    model = _fhir_model_class(resource_type)
    if not model:
        raise HTTPException(status_code=422, detail=f"Unknown resource type: {resource_type}")
    record = model(id=resource_id)
    if hasattr(record, "lab_id"):
        record.lab_id = user.lab_id
    if hasattr(record, "patient_id") and patient_id:
        record.patient_id = patient_id
    if hasattr(record, "encounter_id") and encounter_id:
        record.encounter_id = encounter_id
    if hasattr(record, "created_at"):
        record.created_at = now
    if hasattr(record, "updated_at"):
        record.updated_at = now
    if hasattr(record, "created_by"):
        record.created_by = user.id
    if hasattr(record, "version"):
        record.version = 1
    if hasattr(record, "status"):
        record.status = body.get("status", "active")
    if hasattr(record, "is_deleted"):
        record.is_deleted = False
    db.add(record)
    return record


def _update_fhir_resource(
    db: Session, resource_type: str, resource_id: str, body: dict[str, Any],
    patient_id: str | None, encounter_id: str | None,
    user: LabUser, now: datetime,
):
    record = _get_fhir_resource_or_404(db, resource_type, resource_id, user)
    if hasattr(record, "updated_at"):
        record.updated_at = now
    if hasattr(record, "updated_by"):
        record.updated_by = user.id
    if hasattr(record, "version"):
        version = getattr(record, "version", 0) or 0
        record.version = version + 1
    if patient_id and hasattr(record, "patient_id"):
        record.patient_id = patient_id
    if encounter_id and hasattr(record, "encounter_id"):
        record.encounter_id = encounter_id
    return record
