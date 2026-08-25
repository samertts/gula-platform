from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab_user import LabUser
from app.models.service_account import ServiceAccount
from app.security.dependencies import require_permission, require_service_account
from app.security.service_accounts import has_service_account_scope

from .models import ExternalSource
from .schemas import (
    ChunkResponse,
    ExternalSourceCreate,
    ImportBatchResponse,
    ImportManifest,
    MatchDecisionInput,
    ProfessionalRecordChunk,
    SourceActivationInput,
)
from .service import (
    IngestionConflictError,
    IngestionDisabledError,
    activate_source,
    create_batch,
    decide_match,
    register_source,
    stage_professional_chunk,
)

router = APIRouter(prefix="/integration/external-ingestion", tags=["external-ingestion"])


def require_ingestion_writer(
    actor: ServiceAccount | LabUser = Depends(require_service_account),
) -> ServiceAccount | LabUser:
    """Allow only a scoped machine identity or the platform admin for staging.

    A lab role alone cannot write external national/professional batches. The
    route remains a control-plane endpoint; raw files are never accepted here.
    """
    if isinstance(actor, ServiceAccount):
        if not has_service_account_scope(actor, "integration:identity:write"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="integration scope required")
        return actor
    if actor.role not in {"master_admin", "ministry_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="platform ingestion admin required")
    return actor


def _actor_id(actor: ServiceAccount | LabUser) -> int:
    return actor.id


def _actor_role(actor: ServiceAccount | LabUser) -> str:
    return "service_account" if isinstance(actor, ServiceAccount) else actor.role


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


def _disabled(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/sources", status_code=status.HTTP_201_CREATED)
def register_external_source(
    payload: ExternalSourceCreate,
    db: Session = Depends(get_db),
    actor: LabUser = Depends(require_permission("system:admin")),
) -> dict[str, Any]:
    try:
        source = register_source(
            db,
            source_key=payload.source_key,
            source_kind=payload.source_kind,
            display_name=payload.display_name,
            schema_version=payload.schema_version,
            allowed_fields=payload.allowed_fields,
            service_account_id=payload.service_account_id,
            contract_expires_at=payload.contract_expires_at,
            actor_id=actor.id,
            actor_role=actor.role,
        )
        db.commit()
        return {
            "id": source.id,
            "source_key": source.source_key,
            "source_kind": source.source_kind,
            "contract_status": source.contract_status,
            "is_enabled": source.is_enabled,
            "version": source.version,
        }
    except IngestionDisabledError as exc:
        db.rollback()
        raise _disabled(exc) from exc
    except IngestionConflictError as exc:
        db.rollback()
        raise _conflict(exc) from exc


@router.post("/sources/{source_id}/activate")
def activate_external_source(
    payload: SourceActivationInput,
    source_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    actor: LabUser = Depends(require_permission("system:admin")),
) -> dict[str, Any]:
    try:
        source = activate_source(
            db,
            source_id=source_id,
            expected_version=payload.expected_version,
            legal_approval_ref=payload.legal_approval_ref,
            security_review_ref=payload.security_review_ref,
            second_reviewer_id=payload.second_reviewer_id,
            actor_id=actor.id,
            actor_role=actor.role,
        )
        db.commit()
        return {
            "id": source.id,
            "source_key": source.source_key,
            "contract_status": source.contract_status,
            "is_enabled": source.is_enabled,
            "version": source.version,
        }
    except IngestionDisabledError as exc:
        db.rollback()
        raise _disabled(exc) from exc
    except IngestionConflictError as exc:
        db.rollback()
        raise _conflict(exc) from exc


@router.post("/batches", response_model=ImportBatchResponse, status_code=status.HTTP_201_CREATED)
def receive_manifest(
    payload: ImportManifest,
    db: Session = Depends(get_db),
    actor: ServiceAccount | LabUser = Depends(require_ingestion_writer),
) -> ImportBatchResponse:
    try:
        batch = create_batch(
            db,
            manifest=payload,
            actor_id=_actor_id(actor),
            actor_role=_actor_role(actor),
            actor_is_service_account=isinstance(actor, ServiceAccount),
        )
        db.commit()
        source = db.get(ExternalSource, batch.source_id)
        return ImportBatchResponse(
            id=batch.id,
            status=batch.status,
            source_key=source.source_key if source else payload.source_key,
            export_id=batch.export_id,
            expires_at=batch.expires_at,
        )
    except IngestionDisabledError as exc:
        db.rollback()
        raise _disabled(exc) from exc
    except IngestionConflictError as exc:
        db.rollback()
        raise _conflict(exc) from exc


@router.post("/batches/{batch_id}/professional-records", response_model=ChunkResponse)
def stage_professional_records(
    payload: ProfessionalRecordChunk,
    batch_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    actor: ServiceAccount | LabUser = Depends(require_ingestion_writer),
) -> ChunkResponse:
    try:
        result = stage_professional_chunk(
            db,
            batch_id=batch_id,
            records=payload.records,
            actor_id=_actor_id(actor),
            actor_role=_actor_role(actor),
            actor_is_service_account=isinstance(actor, ServiceAccount),
        )
        db.commit()
        return ChunkResponse(**result)
    except IngestionDisabledError as exc:
        db.rollback()
        raise _disabled(exc) from exc
    except IngestionConflictError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid professional record") from exc


@router.post("/professional-records/{record_id}/decision")
def decide_professional_match(
    payload: MatchDecisionInput,
    record_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    actor: LabUser = Depends(require_permission("system:admin")),
) -> dict[str, Any]:
    try:
        record = decide_match(
            db,
            record_id=record_id,
            decision=payload,
            actor_id=actor.id,
            actor_role=actor.role,
        )
        db.commit()
        return {
            "record_id": record.id,
            "resolution_status": record.resolution_status,
            "canonical_entity_id": record.canonical_entity_id,
            "version": record.version,
        }
    except IngestionDisabledError as exc:
        db.rollback()
        raise _disabled(exc) from exc
    except IngestionConflictError as exc:
        db.rollback()
        raise _conflict(exc) from exc
