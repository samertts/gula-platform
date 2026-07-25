from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.document_platform.application.service import DocumentPlatformService
from app.national.document_platform.domain.entities import Document
from app.national.document_platform.domain.enums import (
    DocumentCategory,
    DocumentFormat,
    RetentionPolicy,
)
from app.national.document_platform.exceptions import (
    DocumentNotFoundError,
    DocumentStateTransitionError,
    DocumentValidationError,
    QRCodeNotFoundError,
    SignatureNotFoundError,
    SignatureVerificationError,
)
from app.national.document_platform.infrastructure.repository import (
    SQLAlchemyDocumentAttachmentRepository,
    SQLAlchemyDocumentQRCodeRepository,
    SQLAlchemyDocumentRepository,
    SQLAlchemyDocumentVersionRepository,
    SQLAlchemyElectronicSignatureRepository,
    SQLAlchemyRetentionRuleRepository,
)

router = APIRouter(prefix="/national/documents", tags=["National Document Platform"])


def _get_service(db: Session = Depends(get_db)) -> DocumentPlatformService:
    from app.kernel import Kernel
    from app.kernel.event_bus.bus import EventBus

    kernel = Kernel.get_instance()
    event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
    doc_repo = SQLAlchemyDocumentRepository(db)
    ver_repo = SQLAlchemyDocumentVersionRepository(db)
    sig_repo = SQLAlchemyElectronicSignatureRepository(db)
    qr_repo = SQLAlchemyDocumentQRCodeRepository(db)
    att_repo = SQLAlchemyDocumentAttachmentRepository(db)
    ret_repo = SQLAlchemyRetentionRuleRepository(db)
    return DocumentPlatformService(
        document_repository=doc_repo,
        version_repository=ver_repo,
        signature_repository=sig_repo,
        qr_code_repository=qr_repo,
        attachment_repository=att_repo,
        retention_rule_repository=ret_repo,
        event_bus=event_bus,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document(
    body: dict[str, Any],
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        document = await service.create_document(
            filename=body.get("filename", ""),
            original_name=body.get("original_name", ""),
            mime_type=body.get("mime_type", "application/octet-stream"),
            format=DocumentFormat(body.get("format", "other"))
            if body.get("format")
            else DocumentFormat.OTHER,
            size_bytes=body.get("size_bytes", 0),
            hash_sha256=body.get("hash_sha256", ""),
            category=DocumentCategory(body.get("category", "other"))
            if body.get("category")
            else DocumentCategory.OTHER,
            tags=body.get("tags", []),
            metadata=body.get("metadata", {}),
            retention_policy=RetentionPolicy(body.get("retention_policy", "standard_1y"))
            if body.get("retention_policy")
            else RetentionPolicy.STANDARD_1Y,
            expires_at=datetime.fromisoformat(body["expires_at"])
            if body.get("expires_at")
            else None,
            created_by=body.get("created_by", ""),
        )
        return _document_to_response(document)
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.get("/")
async def list_documents(
    status: str | None = Query(None),
    category: str | None = Query(None),
    format: str | None = Query(None),
    tags: str | None = Query(None),
    created_by: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DocumentPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    tag_list = tags.split(",") if tags else None
    documents = await service.search_documents(
        query=search,
        status=status,
        category=category,
        format=format,
        tags=tag_list,
        created_by=created_by,
        skip=skip,
        limit=limit,
    )
    return [_document_to_response(d) for d in documents]


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        document = await service.get_document(document_id)
        versions = await service.version_repository.list(document_id)
        signatures = await service.signature_repository.list(document_id)
        attachments = await service.attachment_repository.list(document_id)
        qr = await service.qr_code_repository.get_by_document(document_id)

        result = _document_to_response(document)
        result["versions"] = [
            {
                "id": v.id,
                "version_number": v.version_number,
                "filename": v.filename,
                "size_bytes": v.size_bytes,
                "hash_sha256": v.hash_sha256,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "change_summary": v.change_summary,
            }
            for v in versions
        ]
        result["signatures"] = [
            {
                "id": s.id,
                "signer_id": s.signer_id,
                "signer_name": s.signer_name,
                "signer_role": s.signer_role,
                "signature_type": s.signature_type,
                "status": s.status.value,
                "signed_at": s.signed_at.isoformat() if s.signed_at else None,
            }
            for s in signatures
        ]
        result["attachments"] = [
            {
                "id": a.id,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "mime_type": a.mime_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attachments
        ]
        result["qr_code"] = (
            {
                "id": qr.id,
                "verification_url": qr.verification_url,
                "generated_at": qr.generated_at.isoformat() if qr.generated_at else None,
                "expires_at": qr.expires_at.isoformat() if qr.expires_at else None,
                "scanned_count": qr.scanned_count,
            }
            if qr
            else None
        )

        return result
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.put("/{document_id}")
async def update_document(
    document_id: str,
    body: dict[str, Any],
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        document = await service.update_document(document_id, body)
        return _document_to_response(document)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    body: dict[str, Any] | None = None,
    service: DocumentPlatformService = Depends(_get_service),
) -> None:
    if body is None:
        body = {}
    try:
        await service.delete_document(document_id, reason=body.get("reason", ""))
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/{document_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_version(
    document_id: str,
    body: dict[str, Any],
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        version = await service.create_version(
            document_id=document_id,
            filename=body.get("filename", ""),
            size_bytes=body.get("size_bytes", 0),
            hash_sha256=body.get("hash_sha256", ""),
            created_by=body.get("created_by", ""),
            change_summary=body.get("change_summary", ""),
        )
        return {
            "id": version.id,
            "document_id": version.document_id,
            "version_number": version.version_number,
            "filename": version.filename,
            "size_bytes": version.size_bytes,
            "hash_sha256": version.hash_sha256,
            "created_by": version.created_by,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "change_summary": version.change_summary,
        }
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.get("/{document_id}/versions")
async def list_versions(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DocumentPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        versions = await service.version_repository.list(document_id, skip=skip, limit=limit)
        return [
            {
                "id": v.id,
                "document_id": v.document_id,
                "version_number": v.version_number,
                "filename": v.filename,
                "size_bytes": v.size_bytes,
                "hash_sha256": v.hash_sha256,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "change_summary": v.change_summary,
            }
            for v in versions
        ]
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/{document_id}/sign", status_code=status.HTTP_201_CREATED)
async def sign_document(
    document_id: str,
    body: dict[str, Any],
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        signature = await service.sign_document(
            document_id=document_id,
            signer_id=body.get("signer_id", ""),
            signer_name=body.get("signer_name", ""),
            signer_role=body.get("signer_role", ""),
            signature_type=body.get("signature_type", "electronic"),
            certificate_id=body.get("certificate_id", ""),
            verification_url=body.get("verification_url", ""),
        )
        return {
            "id": signature.id,
            "document_id": signature.document_id,
            "signer_id": signature.signer_id,
            "signer_name": signature.signer_name,
            "signer_role": signature.signer_role,
            "signature_type": signature.signature_type,
            "status": signature.status.value,
            "signed_at": signature.signed_at.isoformat() if signature.signed_at else None,
            "hash_chain_current": signature.hash_chain_current,
        }
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.get("/{document_id}/signatures")
async def list_signatures(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DocumentPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        signatures = await service.signature_repository.list(document_id, skip=skip, limit=limit)
        return [
            {
                "id": s.id,
                "document_id": s.document_id,
                "signer_id": s.signer_id,
                "signer_name": s.signer_name,
                "signer_role": s.signer_role,
                "signature_type": s.signature_type,
                "status": s.status.value,
                "signed_at": s.signed_at.isoformat() if s.signed_at else None,
                "certificate_id": s.certificate_id,
                "hash_chain_previous": s.hash_chain_previous,
                "hash_chain_current": s.hash_chain_current,
            }
            for s in signatures
        ]
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/{document_id}/verify")
async def verify_document(
    document_id: str,
    body: dict[str, Any],
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    signature_id = body.get("signature_id", "")
    if not signature_id:
        try:
            await service.get_document(document_id)
            signatures = await service.signature_repository.list(document_id)
            if not signatures:
                return {"valid": False, "reason": "No signatures found for this document"}
            signature_id = signatures[-1].id
        except DocumentNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
            ) from e

    try:
        return await service.verify_signature(document_id, signature_id)
    except (SignatureNotFoundError, DocumentNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request",
        ) from e


@router.post("/{document_id}/qrcode", status_code=status.HTTP_201_CREATED)
async def generate_qr_code(
    document_id: str,
    body: dict[str, Any] | None = None,
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    if body is None:
        body = {}
    try:
        qr = await service.generate_qr(
            document_id=document_id,
            expires_in_days=body.get("expires_in_days", 365),
        )
        return {
            "id": qr.id,
            "document_id": qr.document_id,
            "verification_url": qr.verification_url,
            "generated_at": qr.generated_at.isoformat() if qr.generated_at else None,
            "expires_at": qr.expires_at.isoformat() if qr.expires_at else None,
            "scanned_count": qr.scanned_count,
        }
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/{document_id}/qrcode")
async def get_qr_code(
    document_id: str,
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        qr = await service.qr_code_repository.get_by_document(document_id)
        if not qr:
            raise QRCodeNotFoundError(document_id)
        return {
            "id": qr.id,
            "document_id": qr.document_id,
            "qr_data": qr.qr_data,
            "verification_url": qr.verification_url,
            "generated_at": qr.generated_at.isoformat() if qr.generated_at else None,
            "expires_at": qr.expires_at.isoformat() if qr.expires_at else None,
            "scanned_count": qr.scanned_count,
        }
    except (DocumentNotFoundError, QRCodeNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/{document_id}/attachments")
async def list_attachments(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DocumentPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        attachments = await service.get_attachments(document_id, skip=skip, limit=limit)
        return [
            {
                "id": a.id,
                "document_id": a.document_id,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "mime_type": a.mime_type,
                "storage_path": a.storage_path,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attachments
        ]
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/{document_id}/attachments", status_code=status.HTTP_201_CREATED)
async def add_attachment(
    document_id: str,
    body: dict[str, Any],
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        attachment = await service.add_attachment(
            document_id=document_id,
            filename=body.get("filename", ""),
            size_bytes=body.get("size_bytes", 0),
            mime_type=body.get("mime_type", "application/octet-stream"),
            storage_path=body.get("storage_path", ""),
        )
        return {
            "id": attachment.id,
            "document_id": attachment.document_id,
            "filename": attachment.filename,
            "size_bytes": attachment.size_bytes,
            "mime_type": attachment.mime_type,
            "storage_path": attachment.storage_path,
            "created_at": attachment.created_at.isoformat() if attachment.created_at else None,
        }
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/{document_id}/archive")
async def archive_document(
    document_id: str,
    body: dict[str, Any] | None = None,
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    if body is None:
        body = {}
    try:
        document = await service.archive_document(document_id, reason=body.get("reason", ""))
        return {"id": document.id, "status": document.status.value, "archived": True}
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/{document_id}/generate-pdf")
async def generate_pdf(
    document_id: str,
    body: dict[str, Any] | None = None,
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    if body is None:
        body = {}
    try:
        pdf_bytes = await service.generate_pdf(document_id, template=body.get("template", ""))
        return {"document_id": document_id, "pdf_size_bytes": len(pdf_bytes), "generated": True}
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.post("/{document_id}/retention")
async def apply_retention(
    document_id: str,
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return await service.apply_retention_policy(document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/{document_id}/history")
async def get_document_history(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DocumentPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return await service.get_document_history(document_id, skip=skip, limit=limit)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/categories")
async def list_categories() -> list[dict[str, str]]:
    return [{"value": c.value, "name": c.name} for c in DocumentCategory]


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_document_platform", "version": "1.0.0"}


def _document_to_response(document: Document) -> dict[str, Any]:
    return {
        "id": document.id,
        "filename": document.filename,
        "original_name": document.original_name,
        "mime_type": document.mime_type,
        "format": document.format.value,
        "size_bytes": document.size_bytes,
        "hash_sha256": document.hash_sha256,
        "version": document.version,
        "category": document.category.value,
        "status": document.status.value,
        "tags": document.tags,
        "metadata": document.metadata,
        "retention_policy": document.retention_policy.value,
        "expires_at": document.expires_at.isoformat() if document.expires_at else None,
        "created_by": document.created_by,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
    }
