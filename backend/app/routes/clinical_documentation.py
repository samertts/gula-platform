from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.security.legacy_clinical import block_legacy_clinical_route

logger = logging.getLogger("gula.routes.clinical_documentation")

router = APIRouter(
    prefix="/clinical/documentation",
    tags=["clinical documentation"],
    dependencies=[Depends(block_legacy_clinical_route)],
)

_DOCUMENT_TYPES = frozenset({
    "soap_note", "progress_note", "nursing_note", "consultation_note",
    "operation_note", "emergency_note",
})


class SoapNoteCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    department: str | None = None
    diagnosis_codes: list[dict[str, str]] = []
    is_confidential: bool = False


class ProgressNoteCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    note_type: str = "progress"
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    department: str | None = None


class NursingNoteCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    assessment: str | None = None
    interventions: str | None = None
    response: str | None = None
    plan: str | None = None
    department: str | None = None


class ConsultationNoteCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    referring_provider_id: str | None = None
    consulting_provider_id: str | None = None
    specialty: str | None = None
    reason_for_consultation: str | None = None
    clinical_findings: str | None = None
    assessment: str | None = None
    recommendations: str | None = None
    department: str | None = None


class OperationNoteCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    procedure_name: str
    procedure_code: str | None = None
    surgeon_id: str | None = None
    assistant_id: str | None = None
    anesthesiologist_id: str | None = None
    preoperative_diagnosis: str | None = None
    postoperative_diagnosis: str | None = None
    procedure_description: str | None = None
    findings: str | None = None
    complications: str | None = None
    estimated_blood_loss: str | None = None
    specimens_removed: str | None = None
    anesthesia_type: str | None = None
    department: str | None = None


class EmergencyNoteCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    arrival_time: str | None = None
    triage_category: str | None = None
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    vital_signs: str | None = None
    examination_findings: str | None = None
    assessment: str | None = None
    plan: str | None = None
    disposition: str | None = None
    department: str | None = None


class StructuredTemplateCreate(BaseModel):
    name: str = Field(..., max_length=256)
    document_type: str
    template_content: dict[str, Any]
    description: str | None = None
    department: str | None = None
    is_active: bool = True


class SignDocumentRequest(BaseModel):
    document_id: str
    signature_type: str = "electronic"
    role: str | None = None


_DOCUMENTS: dict[str, dict[str, Any]] = {}
_DOC_COUNTER: int = 0
_TEMPLATES: dict[str, dict[str, Any]] = {}
_VERSION_HISTORY: dict[str, list[dict[str, Any]]] = {}


def _next_doc_id() -> str:
    global _DOC_COUNTER
    _DOC_COUNTER += 1
    return f"CLN-DOC-{_DOC_COUNTER:06d}"


def _store_document(doc_type: str, data: dict) -> dict:
    doc_id = _next_doc_id()
    now = datetime.now(UTC).isoformat()
    doc = {
        "id": doc_id,
        "document_type": doc_type,
        **{k: v for k, v in data.items() if v is not None},
        "created_by": data.get("created_by"),
        "created_at": now,
        "updated_at": now,
        "is_signed": False,
        "version": 1,
    }
    _DOCUMENTS[doc_id] = doc
    _VERSION_HISTORY[doc_id] = [
        {"version": 1, "timestamp": now, "action": "created", "content": doc},
    ]
    return doc


# ==============================================================================
# SOAP Notes
# ==============================================================================


@router.post("/soap-notes", status_code=201)
def create_soap_note(
    data: SoapNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _store_document("soap_note", {**data.model_dump(exclude_none=True), "created_by": current_user.id})


# ==============================================================================
# Progress Notes
# ==============================================================================


@router.post("/progress-notes", status_code=201)
def create_progress_note(
    data: ProgressNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _store_document("progress_note", {**data.model_dump(exclude_none=True), "created_by": current_user.id})


# ==============================================================================
# Nursing Notes
# ==============================================================================


@router.post("/nursing-notes", status_code=201)
def create_nursing_note(
    data: NursingNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _store_document("nursing_note", {**data.model_dump(exclude_none=True), "created_by": current_user.id})


# ==============================================================================
# Consultation Notes
# ==============================================================================


@router.post("/consultation-notes", status_code=201)
def create_consultation_note(
    data: ConsultationNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _store_document("consultation_note", {**data.model_dump(exclude_none=True), "created_by": current_user.id})


# ==============================================================================
# Operation Notes
# ==============================================================================


@router.post("/operation-notes", status_code=201)
def create_operation_note(
    data: OperationNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _store_document("operation_note", {**data.model_dump(exclude_none=True), "created_by": current_user.id})


# ==============================================================================
# Emergency Notes
# ==============================================================================


@router.post("/emergency-notes", status_code=201)
def create_emergency_note(
    data: EmergencyNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _store_document("emergency_note", {**data.model_dump(exclude_none=True), "created_by": current_user.id})


# ==============================================================================
# List / Get Documents
# ==============================================================================


@router.get("")
def list_documents(
    patient_id: str | None = None,
    document_type: str | None = None,
    department: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = list(_DOCUMENTS.values())
    if patient_id:
        items = [d for d in items if d.get("patient_id") == patient_id]
    if document_type:
        items = [d for d in items if d.get("document_type") == document_type]
    if department:
        items = [d for d in items if d.get("department") == department]
    total = len(items)
    items.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return {"items": items[skip:skip + limit], "total": total, "skip": skip, "limit": limit}


@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# ==============================================================================
# Structured Templates
# ==============================================================================


@router.get("/templates")
def list_structured_templates(
    document_type: str | None = None,
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = list(_TEMPLATES.values())
    if document_type:
        items = [t for t in items if t.get("document_type") == document_type]
    if department:
        items = [t for t in items if t.get("department") == department]
    return {"items": items, "total": len(items)}


@router.post("/templates", status_code=201)
def create_structured_template(
    data: StructuredTemplateCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.document_type not in _DOCUMENT_TYPES and data.document_type != "general":
        raise HTTPException(
            status_code=422,
            detail=f"Invalid document_type. Must be one of: {', '.join(sorted(_DOCUMENT_TYPES))} or 'general'",
        )
    template_id = _next_doc_id()
    template = {
        "id": template_id,
        **data.model_dump(exclude_none=True),
        "lab_id": current_user.lab_id,
        "created_by": current_user.id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _TEMPLATES[template_id] = template
    return template


# ==============================================================================
# Electronic Signature & Sign Document
# ==============================================================================


@router.post("/sign")
def sign_document(
    data: SignDocumentRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _DOCUMENTS.get(data.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("is_signed"):
        raise HTTPException(status_code=422, detail="Document is already signed")

    now = datetime.now(UTC).isoformat()
    doc["is_signed"] = True
    doc["signed_by"] = current_user.id
    doc["signed_at"] = now
    doc["signature_type"] = data.signature_type
    doc["updated_at"] = now

    if data.document_id in _VERSION_HISTORY:
        _VERSION_HISTORY[data.document_id].append({
            "version": doc["version"] + 1,
            "timestamp": now,
            "action": "signed",
            "signed_by": current_user.id,
        })
        doc["version"] += 1

    return doc


# ==============================================================================
# Version History
# ==============================================================================


@router.get("/{document_id}/versions")
def get_document_version_history(
    document_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if document_id not in _DOCUMENTS:
        raise HTTPException(status_code=404, detail="Document not found")
    history = _VERSION_HISTORY.get(document_id, [])
    return {"document_id": document_id, "versions": history, "total": len(history)}
