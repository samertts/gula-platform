"""Trust platform REST API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.rbac import require_role
from app.trust.enums import (
    ConsentPurpose,
    DataCategory,
)
from app.trust.services import ComplianceService, ConsentService, SovereigntyService, TrustService

router = APIRouter(prefix="/api/v1/trust", tags=["Trust Platform"])


# ── Schemas ──

class ConsentCreateRequest(BaseModel):
    patient_id: int
    purpose: str
    data_categories: list[str]
    guardian_id: int | None = None
    expires_in_days: int | None = None


class ConsentResponse(BaseModel):
    id: int
    patient_id: int
    lab_id: int
    purpose: str
    status: str
    granted_at: str | None = None
    expires_at: str | None = None
    data_categories: str | None = None


class ConsentVerifyRequest(BaseModel):
    patient_id: int
    purpose: str
    data_category: str | None = None


class SignDocumentRequest(BaseModel):
    document_hash: str
    metadata: dict[str, Any] | None = None


class ComplianceCheckRequest(BaseModel):
    check_type: str
    check_name: str
    target_id: str | None = None
    target_type: str | None = None


# ── Consent Routes ──

@router.post("/consent", response_model=ConsentResponse)
def create_consent(
    request: ConsentCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = ConsentService(db)
    try:
        purpose = ConsentPurpose(request.purpose)
        categories = [DataCategory(c) for c in request.data_categories]
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e

    record = service.create_consent(
        patient_id=request.patient_id,
        lab_id=current_user.get("lab_id", 0),
        purpose=purpose,
        data_categories=categories,
        guardian_id=request.guardian_id,
        expires_in_days=request.expires_in_days,
    )
    return ConsentResponse(
        id=record.id,
        patient_id=record.patient_id,
        lab_id=record.lab_id,
        purpose=record.purpose.value,
        status=record.status.value,
        granted_at=record.granted_at.isoformat() if record.granted_at else None,
        expires_at=record.expires_at.isoformat() if record.expires_at else None,
        data_categories=record.data_categories,
    )


@router.get("/consent/verify")
def verify_consent(
    patient_id: int = Query(...),
    purpose: str = Query(...),
    data_category: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ConsentService(db)
    try:
        purpose_enum = ConsentPurpose(purpose)
        category_enum = DataCategory(data_category) if data_category else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e

    lab_id = current_user.get("lab_id", 0)
    granted = service.verify_consent(patient_id, lab_id, purpose_enum, category_enum)
    return {"granted": granted, "patient_id": patient_id, "purpose": purpose}


@router.get("/consent/patient/{patient_id}")
def get_patient_consents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = ConsentService(db)
    records = service.get_patient_consents(patient_id)
    return {
        "patient_id": patient_id,
        "consents": [
            {
                "id": r.id,
                "purpose": r.purpose.value,
                "status": r.status.value,
                "granted_at": r.granted_at.isoformat() if r.granted_at else None,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            }
            for r in records
        ],
    }


@router.post("/consent/{consent_id}/withdraw")
def withdraw_consent(
    consent_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = ConsentService(db)
    record = service.withdraw_consent(consent_id, current_user.get("user_id", 0))
    if not record:
        raise HTTPException(status_code=404, detail="Consent record not found")
    return {"status": "withdrawn", "consent_id": consent_id}


@router.get("/consent/access-history/{patient_id}")
def get_access_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = ConsentService(db)
    history = service.get_access_history(patient_id)
    return {"patient_id": patient_id, "access_history": history}


# ── Sovereignty Routes ──

@router.get("/sovereignty/rules")
def get_sovereignty_rules(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = SovereigntyService(db)
    rules = service.get_all_rules()
    return {
        "rules": [
            {
                "id": r.id,
                "data_category": r.data_category.value,
                "sovereignty_level": r.sovereignty_level.value,
                "allows_cross_border": bool(r.allows_cross_border),
                "requires_encryption": bool(r.requires_encryption),
                "data_residency": r.data_residency,
            }
            for r in rules
        ],
    }


@router.get("/sovereignty/validate-cross-border")
def validate_cross_border(
    data_category: str = Query(...),
    destination: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = SovereigntyService(db)
    try:
        category = DataCategory(data_category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e
    allowed = service.validate_cross_border(category, destination)
    return {"allowed": allowed, "data_category": data_category, "destination": destination}


# ── Trust Service Routes ──

@router.post("/sign")
def sign_document(
    request: SignDocumentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = TrustService(db)
    log = service.sign_document(
        document_hash=request.document_hash,
        user_id=current_user.get("user_id", 0),
        lab_id=current_user.get("lab_id", 0),
        metadata=request.metadata,
    )
    return {
        "id": log.id,
        "document_hash": log.document_hash,
        "signature": log.signature_value[:32] + "...",
        "timestamp": log.created_at.isoformat(),
        "request_id": log.request_id,
    }


@router.post("/timestamp")
def timestamp_document(
    request: SignDocumentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = TrustService(db)
    log = service.timestamp_document(
        document_hash=request.document_hash,
        user_id=current_user.get("user_id", 0),
        lab_id=current_user.get("lab_id", 0),
    )
    return {
        "id": log.id,
        "document_hash": log.document_hash,
        "timestamp_token": log.timestamp_token[:48] + "...",
        "timestamp": log.created_at.isoformat(),
        "request_id": log.request_id,
    }


@router.get("/verify/{document_hash}")
def verify_document(
    document_hash: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = TrustService(db)
    return service.verify_document_integrity(document_hash)


# ── Compliance Routes ──

@router.post("/compliance/check")
def run_compliance_check(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = ComplianceService(db)
    check = service.run_compliance_check(
        check_type=request.check_type,
        check_name=request.check_name,
        target_id=request.target_id,
        target_type=request.target_type,
    )
    return {
        "id": check.id,
        "check_type": check.check_type,
        "check_name": check.check_name,
        "result": check.result.value,
        "score": check.score,
        "checked_at": check.checked_at.isoformat(),
        "next_check_at": check.next_check_at.isoformat() if check.next_check_at else None,
    }


@router.get("/compliance/dashboard")
def get_compliance_dashboard(
    lab_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = ComplianceService(db)
    return service.get_compliance_dashboard(lab_id)


@router.post("/compliance/evidence")
def add_compliance_evidence(
    evidence_type: str = Query(...),
    source: str = Query(...),
    evidence_data: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = ComplianceService(db)
    evidence = service.add_evidence(
        evidence_type=evidence_type,
        source=source,
        evidence_data=evidence_data,
        collected_by=current_user.get("user_id"),
    )
    return {
        "evidence_id": evidence.evidence_id,
        "evidence_type": evidence.evidence_type,
        "source": evidence.source,
        "status": evidence.status.value,
        "collected_at": evidence.collected_at.isoformat(),
    }
