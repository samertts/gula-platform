from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.documentation_service import ClinicalDocumentService
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.models.clinical_document import ClinicalDocument

router = APIRouter(prefix="/api/v1/clinical/documents", tags=["Canonical Clinical Documentation"])


class ClinicalDocumentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str = Field(min_length=1, max_length=80)
    encounter_id: str | None = Field(default=None, max_length=80)
    document_type: str = Field(min_length=1, max_length=64)
    content: dict[str, Any]
    content_format: str = Field(default="structured", min_length=1, max_length=20)


class ClinicalDocumentAmendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: dict[str, Any]
    reason: str = Field(min_length=1, max_length=500)


class ClinicalDocumentSignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signature_reference: str = Field(min_length=1, max_length=128)


def _access(db: Session, actor: NiamActor, *, purpose: str, permissions: frozenset[str] = frozenset()) -> ClinicalAccessContext:
    gateway = ClinicalGatewayContextResolver(db).resolve(actor)
    return ClinicalAccessContext.from_gateway(gateway, purpose=purpose, permissions=permissions)


def _scope_query(db: Session, access: ClinicalAccessContext) -> Any:
    return db.query(ClinicalDocument).filter(
        ClinicalDocument.is_deleted.is_(False),
        ClinicalDocument.tenant_id == access.tenant_id,
        ClinicalDocument.organization_id == access.organization_id,
        ClinicalDocument.facility_id == access.facility_id,
        ClinicalDocument.workspace_id == access.workspace_id,
    )


def _safe(document: ClinicalDocument) -> dict[str, Any]:
    return cast(dict[str, Any], ClinicalDocumentService.to_safe_dict(document))


@router.get("")
def list_documents(
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_documentation.read", permissions=frozenset({"read"}))
        documents = _scope_query(db, access).order_by(ClinicalDocument.updated_at.desc()).limit(100).all()
        return {"items": [_safe(item) for item in documents], "total": len(documents), "workspace_id": access.workspace_id}
    except ClinicalGatewayBlocked as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical documentation is not available for this context") from exc


@router.get("/{document_id}")
def get_document(
    document_id: str,
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_documentation.read", permissions=frozenset({"read"}))
        document = _scope_query(db, access).filter(ClinicalDocument.id == document_id).one_or_none()
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return _safe(document)
    except ClinicalGatewayBlocked as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical documentation is not available for this context") from exc


@router.post("", status_code=status.HTTP_201_CREATED)
def create_document(
    payload: ClinicalDocumentCreateRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_documentation.create", permissions=frozenset({"create"}))
        document = ClinicalDocumentService(db).create(access=access, **payload.model_dump())
        db.commit()
        return _safe(document)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical document creation is not authorized") from exc


@router.post("/{document_id}/sign")
def sign_document(
    document_id: str,
    payload: ClinicalDocumentSignRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_documentation.sign", permissions=frozenset({"sign"}))
        document = ClinicalDocumentService(db).sign(access=access, document_id=document_id, signature_reference=payload.signature_reference)
        db.commit()
        return _safe(document)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical document signing is not authorized") from exc


@router.post("/{document_id}/amend", status_code=status.HTTP_201_CREATED)
def amend_document(
    document_id: str,
    payload: ClinicalDocumentAmendRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_documentation.amend", permissions=frozenset({"update"}))
        document = ClinicalDocumentService(db).amend(access=access, document_id=document_id, **payload.model_dump())
        db.commit()
        return _safe(document)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical document amendment is not authorized") from exc
