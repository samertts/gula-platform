"""IHE PIXm and MHD pilot endpoints.

This module intentionally implements a constrained, read-safe pilot surface:
- PIXm exposes identifiers for a patient belonging to the caller's lab only.
- MHD stores inbound document Bundles in the existing integration inbox for
  review; it never writes clinical records directly.
- MHD DocumentReference search/read is tenant-scoped to the caller's lab.

Cross-organization production exchange requires an organisation-bound service
account, active consent policy, and a reviewed national MPI mapping. Those
controls are represented here rather than bypassed with global lookups.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.lims.models import LabReport
from app.models.lab_order import LabOrder
from app.models.canonical_patient import CanonicalPatient, PatientLink
from app.models.integration_inbox import IntegrationInboxEvent
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.service_account import ServiceAccount
from app.security.dependencies import get_current_user, require_service_account
from app.services.audit_service import log_action

router = APIRouter(prefix="/interop", tags=["IHE PIXm/MHD"])

_ALLOWED_MHD_RESOURCE_TYPES = {
    "Bundle",
    "Composition",
    "DiagnosticReport",
    "DocumentReference",
    "Observation",
    "Patient",
    "Practitioner",
    "Specimen",
}
_FINAL_REPORT_STATUSES = {"final", "amended", "corrected"}


def _lab_id_for_actor(actor: Any) -> int:
    """Return a mandatory organisation scope for human or machine actors."""
    lab_id = getattr(actor, "lab_id", None)
    if lab_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An organisation-bound actor is required for interoperability.",
        )
    return int(lab_id)


def _actor_id(actor: Any) -> str:
    if isinstance(actor, ServiceAccount):
        return f"svc:{actor.id}"
    return f"user:{actor.id}"


def _identifier(system: str, value: str) -> dict[str, str]:
    return {"system": system, "value": value}


def _parse_identifier(value: str) -> tuple[str | None, str]:
    if "|" in value:
        system, raw = value.split("|", 1)
        return system or None, raw
    return None, value


def _find_local_patient(db: Session, lab_id: int, identifier: str) -> Patient | None:
    """Resolve only local patient identifiers; raw national IDs are not accepted."""
    if identifier.startswith("Patient/"):
        raw_id = identifier.removeprefix("Patient/")
        if not raw_id.isdigit():
            return None
        return (
            db.query(Patient)
            .filter(Patient.id == int(raw_id), Patient.lab_id == lab_id)
            .first()
        )

    system, value = _parse_identifier(identifier)
    query = db.query(Patient).filter(Patient.lab_id == lab_id)
    if system and "health-id" not in system and "patient-id" not in system:
        return None
    if system and "patient-id" in system and value.isdigit():
        return query.filter(Patient.id == int(value)).first()
    return query.filter(Patient.health_id == value).first()


def _canonical_for_patient(db: Session, patient: Patient) -> CanonicalPatient | None:
    return (
        db.query(CanonicalPatient)
        .join(PatientLink, PatientLink.canonical_id == CanonicalPatient.id)
        .filter(PatientLink.patient_id == patient.id)
        .order_by(PatientLink.confidence.desc().nullslast(), PatientLink.id.desc())
        .first()
    )


def _patient_reference(patient: Patient, canonical: CanonicalPatient | None) -> dict[str, Any]:
    identifiers = [
        _identifier(f"urn:gula:patient-id:{patient.lab_id}", str(patient.id)),
    ]
    if patient.health_id:
        identifiers.append(_identifier("urn:gula:health-id", patient.health_id))
    if canonical and canonical.health_id and canonical.health_id not in {
        item["value"] for item in identifiers
    }:
        identifiers.append(_identifier("urn:gula:health-id", canonical.health_id))
    return {
        "reference": f"Patient/{patient.id}",
        "identifier": identifiers[-1],
        "display": "Patient record",
    }


def _document_reference(
    report: LabReport,
    order: LabOrder,
    patient: Patient,
    canonical: CanonicalPatient | None = None,
) -> dict[str, Any]:
    report_id = report.fhir_id or f"gula-report-{report.id}"
    status_value = report.status if report.status in _FINAL_REPORT_STATUSES else "current"
    content: list[dict[str, Any]] = []
    for attachment in getattr(report, "attachments", []) or []:
        attachment_data: dict[str, Any] = {
            "contentType": attachment.file_type or "application/pdf",
            "title": attachment.file_name,
        }
        if attachment.storage_path:
            attachment_data["url"] = f"/national/interop/Binary/{attachment.id}"
        content.append({"attachment": attachment_data})
    if not content:
        content = [{"attachment": {"contentType": "application/pdf", "title": report.title or report.report_number}}]

    return {
        "resourceType": "DocumentReference",
        "id": str(report_id),
        "status": status_value,
        "docStatus": "final" if report.status in _FINAL_REPORT_STATUSES else "preliminary",
        "type": {
            "coding": [{"system": "urn:gula:document-type", "code": "laboratory-report", "display": "Laboratory report"}],
            "text": report.title_ar or report.title or "Laboratory report",
        },
        "subject": _patient_reference(patient, canonical),
        "date": (report.finalized_at or report.generated_at or report.created_at).isoformat()
        if (report.finalized_at or report.generated_at or report.created_at)
        else None,
        "author": [{"reference": f"Organization/lab-{report.lab_id}"}],
        "custodian": {"reference": f"Organization/lab-{report.lab_id}"},
        "content": content,
        "context": {"related": [{"reference": f"ServiceRequest/order-{order.id}"}]},
        "meta": {"profile": ["https://gula-platform.org/fhir/StructureDefinition/gula-lab-document-reference"]},
    }


@router.get("/Patient/$ihe-pix", response_class=None)
def pix_query(
    sourceIdentifier: str = Query(..., min_length=1),
    targetSystem: str | None = Query(default=None),
    targetIdentifier: str | None = Query(default=None),
    actor: LabUser | ServiceAccount = Depends(require_service_account),
    db: Session = Depends(get_db),
):
    """Constrained PIXm ITI-83 query returning identifiers for the local subject."""
    lab_id = _lab_id_for_actor(actor)
    patient = _find_local_patient(db, lab_id, sourceIdentifier)
    parameters: list[dict[str, Any]] = []
    if patient:
        canonical = _canonical_for_patient(db, patient)
        identifiers = [_identifier(f"urn:gula:patient-id:{lab_id}", str(patient.id))]
        if patient.health_id:
            identifiers.append(_identifier("urn:gula:health-id", patient.health_id))
        if canonical and canonical.health_id and canonical.health_id not in {i["value"] for i in identifiers}:
            identifiers.append(_identifier("urn:gula:health-id", canonical.health_id))
        if targetSystem:
            identifiers = [i for i in identifiers if i["system"] == targetSystem]
        if targetIdentifier:
            identifiers = [i for i in identifiers if i["value"] == targetIdentifier]
        parameters = [{"name": "targetIdentifier", "valueIdentifier": item} for item in identifiers]

    log_action(
        db,
        action="interop.pixm.query",
        resource_type="Patient",
        resource_id=patient.id if patient else None,
        user_id=getattr(actor, "id", None),
        user_role=getattr(actor, "role", "service_account"),
        lab_id=lab_id,
        details={"matched": bool(patient), "identifier_system_only": "system|value" in sourceIdentifier},
        ip_address=None,
    )
    db.commit()
    return {"resourceType": "Parameters", "parameter": parameters}


@router.get("/DocumentReference")
def mhd_search_documents(
    patient: str | None = Query(default=None),
    subject: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    actor: LabUser | ServiceAccount = Depends(require_service_account),
    db: Session = Depends(get_db),
):
    """MHD ITI-67 search over final local laboratory reports."""
    lab_id = _lab_id_for_actor(actor)
    patient_identifier = patient or subject
    query = (
        db.query(LabReport, LabOrder, Patient)
        .join(LabOrder, LabOrder.id == LabReport.order_id)
        .join(Patient, Patient.id == LabOrder.patient_id)
        .filter(
            LabReport.lab_id == lab_id,
            LabOrder.lab_id == lab_id,
            Patient.lab_id == lab_id,
            LabReport.is_deleted.is_(False),
            LabReport.status.in_(_FINAL_REPORT_STATUSES),
        )
    )
    if patient_identifier:
        resolved = _find_local_patient(db, lab_id, patient_identifier)
        if not resolved:
            rows: list[tuple[LabReport, LabOrder, Patient]] = []
        else:
            rows = query.filter(LabOrder.patient_id == resolved.id).all()
    else:
        rows = query.all()
    if status_filter:
        rows = [row for row in rows if row[0].status == status_filter]
    entries = [
        {
            "fullUrl": f"DocumentReference/{report.fhir_id or f'gula-report-{report.id}'}",
            "resource": _document_reference(
                report,
                order,
                local_patient,
                _canonical_for_patient(db, local_patient),
            ),
        }
        for report, order, local_patient in rows
    ]
    return {"resourceType": "Bundle", "type": "searchset", "total": len(entries), "entry": entries}


@router.get("/DocumentReference/{report_id}")
def mhd_read_document(
    report_id: str,
    actor: LabUser | ServiceAccount = Depends(require_service_account),
    db: Session = Depends(get_db),
):
    """MHD ITI-68 read, restricted to the owning laboratory."""
    lab_id = _lab_id_for_actor(actor)
    report_id_filters = [LabReport.fhir_id == report_id]
    if report_id.isdigit():
        report_id_filters.append(LabReport.id == int(report_id))
    elif report_id.startswith("gula-report-") and report_id.removeprefix("gula-report-").isdigit():
        report_id_filters.append(LabReport.id == int(report_id.removeprefix("gula-report-")))
    row = (
        db.query(LabReport, LabOrder, Patient)
        .join(LabOrder, LabOrder.id == LabReport.order_id)
        .join(Patient, Patient.id == LabOrder.patient_id)
        .filter(
            or_(*report_id_filters),
            LabReport.lab_id == lab_id,
            LabOrder.lab_id == lab_id,
            Patient.lab_id == lab_id,
            LabReport.is_deleted.is_(False),
            LabReport.status.in_(_FINAL_REPORT_STATUSES),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="DocumentReference not found")
    report, order, patient = row
    return _document_reference(report, order, patient, _canonical_for_patient(db, patient))


@router.post("/Bundle", status_code=status.HTTP_202_ACCEPTED)
@router.post("/Document", status_code=status.HTTP_202_ACCEPTED)
def mhd_provide_document(
    payload: dict[str, Any] = Body(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    source_system: str | None = Header(default=None, alias="X-Source-System"),
    actor: LabUser | ServiceAccount = Depends(require_service_account),
    db: Session = Depends(get_db),
):
    """MHD ITI-65 intake into the review inbox; never writes clinical data directly."""
    if not idempotency_key or len(idempotency_key) > 200:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required and must be <= 200 characters")
    if payload.get("resourceType") != "Bundle":
        raise HTTPException(status_code=422, detail="ITI-65 payload must be a FHIR Bundle")
    entries = payload.get("entry") or []
    if not isinstance(entries, list) or len(entries) > 500:
        raise HTTPException(status_code=422, detail="Bundle entry count is invalid")
    unsupported = {
        (entry.get("resource") or {}).get("resourceType")
        for entry in entries
        if (entry.get("resource") or {}).get("resourceType") not in _ALLOWED_MHD_RESOURCE_TYPES
    }
    if unsupported:
        raise HTTPException(status_code=422, detail={"unsupported_resource_types": sorted(unsupported)})

    recipient_lab_id = _lab_id_for_actor(actor)
    existing = (
        db.query(IntegrationInboxEvent)
        .filter(
            IntegrationInboxEvent.idempotency_key == idempotency_key,
            IntegrationInboxEvent.tenant_id == str(recipient_lab_id),
        )
        .first()
    )
    if existing:
        return {"status": "already_accepted", "eventId": existing.event_id, "inboxId": existing.id}

    bundle_id = str(payload.get("id") or idempotency_key)
    event = IntegrationInboxEvent(
        event_id=f"mhd:{recipient_lab_id}:{bundle_id}",
        event_type="ihe.mhd.iti-65.document",
        schema_version=1,
        source_service=(source_system or "unknown")[:80],
        tenant_id=str(recipient_lab_id),
        entity_id=str(payload.get("id") or "bundle"),
        correlation_id=str(payload.get("id") or idempotency_key),
        idempotency_key=idempotency_key,
        actor_id=_actor_id(actor),
        payload=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        status="pending_review",
    )
    db.add(event)
    db.flush()
    log_action(
        db,
        action="interop.mhd.iti-65.accepted",
        resource_type="IntegrationInboxEvent",
        resource_id=event.id,
        user_id=getattr(actor, "id", None),
        user_role=getattr(actor, "role", "service_account"),
        lab_id=recipient_lab_id,
        details={"source_system": (source_system or "unknown")[:80], "resource_count": len(entries), "status": "pending_review"},
    )
    db.commit()
    return {"status": "accepted", "eventId": event.event_id, "inboxId": event.id, "reviewStatus": event.status}
