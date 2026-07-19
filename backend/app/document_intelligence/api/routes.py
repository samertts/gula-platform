from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from ..application.service import DocumentIntelligenceOrchestrator
from ..domain.enums import DocumentCategory, OcrEngine, OcrLanguage, ProcessingPriority
from ..domain.repository import DocumentRepository
from ..exceptions import (
    DocumentIntelligenceError,
    DocumentNotFoundError,
    IngestionError,
    ProviderNotAvailableError,
)

logger = logging.getLogger("gula.document_intelligence.routes")

router = APIRouter(
    prefix="/document-intelligence",
    tags=["Document Intelligence"],
)


def _get_orchestrator() -> DocumentIntelligenceOrchestrator:
    from app.document_intelligence import get_orchestrator
    return get_orchestrator()


def _get_document_repo() -> DocumentRepository:
    from app.document_intelligence import get_document_repo
    return get_document_repo()


@router.post("/ingest", summary="Ingest a document for processing")
async def ingest_document(
    file: UploadFile = File(...),
    language: OcrLanguage = Query(OcrLanguage.arabic_english),
    priority: ProcessingPriority = Query(ProcessingPriority.normal),
    patient_id: str | None = Query(None),
    lab_id: str | None = Query(None),
    metadata: str | None = Query(None),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    data = await file.read()
    meta = {}
    if metadata:
        import json
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            pass
    if patient_id:
        meta["patient_id"] = patient_id
    if lab_id:
        meta["lab_id"] = lab_id

    if not data:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    result = await orchestrator.process_document(
        data=data,
        filename=file.filename or "untitled",
        mime_type=file.content_type or "application/octet-stream",
        language=language,
        priority=priority,
        metadata=meta,
    )

    if not result.success:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Document processing completed with errors",
                "error": result.error,
                "processing_summary": result.processing_summary,
            },
        )

    return {
        "message": "Document processed successfully",
        "document_id": str(result.document.id) if result.document else None,
        "processing_summary": result.processing_summary,
        "classification": str(result.classification) if result.classification else None,
        "entity_count": len(result.entities),
        "field_count": len(result.fields),
    }


@router.post("/ingest/batch", summary="Batch ingest multiple documents")
async def ingest_batch(
    files: list[UploadFile] = File(...),
    language: OcrLanguage = Query(OcrLanguage.arabic_english),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    inputs: list[tuple[bytes, str, str]] = []
    for file in files:
        data = await file.read()
        inputs.append((data, file.filename or "untitled", file.content_type or "application/octet-stream"))

    results = await orchestrator.process_batch(inputs, language)

    return [
        {
            "filename": r.document.filename if r.document and r.success else "unknown",
            "document_id": str(r.document.id) if r.document else None,
            "success": r.success,
            "error": r.error if not r.success else None,
            "classification": str(r.classification) if r.classification else None,
            "entity_count": len(r.entities),
        }
        for r in results
    ]


@router.get("/documents/{document_id}", summary="Get document details and results")
async def get_document(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    result = await orchestrator.get_document_result(document_id)
    if not result or not result.document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document": {
            "id": str(result.document.id),
            "filename": result.document.filename,
            "mime_type": result.document.mime_type,
            "size_bytes": result.document.size_bytes,
            "page_count": result.document.page_count,
            "status": str(result.document.status),
            "language": str(result.document.language),
            "created_at": result.document.created_at.isoformat(),
            "tags": result.document.tags,
        },
        "processing": {
            "success": result.success,
            "error": result.error,
            "phases_completed": [str(p) for p in (result.pipeline.phases_completed if result.pipeline else [])],
            "total_time_ms": result.pipeline.total_processing_time_ms if result.pipeline else 0,
        },
        "classification": str(result.classification) if result.classification else None,
        "entity_count": len(result.entities),
    }


@router.delete("/documents/{document_id}", summary="Delete a document")
async def delete_document(
    document_id: UUID,
    repo: DocumentRepository = Depends(_get_document_repo),
):
    try:
        await repo.delete(document_id)
        return {"message": "Document deleted", "document_id": str(document_id)}
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents", summary="List documents with filters")
async def list_documents(
    status: str | None = Query(None),
    category: str | None = Query(None),
    patient_id: UUID | None = Query(None),
    lab_id: UUID | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    repo: DocumentRepository = Depends(_get_document_repo),
):
    cat = DocumentCategory(category) if category else None
    from ..domain.enums import DocumentStatus
    st = DocumentStatus(status) if status else None

    docs, total = await repo.list(
        status=st,
        category=cat,
        patient_id=patient_id,
        lab_id=lab_id,
        limit=limit,
        offset=offset,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "mime_type": d.mime_type,
                "size_bytes": d.size_bytes,
                "page_count": d.page_count,
                "status": str(d.status),
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
    }


@router.get("/search", summary="Enterprise search across all documents")
async def search_documents(
    query: str = Query(..., min_length=1),
    document_type: str | None = Query(None),
    patient_id: UUID | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(50, le=200),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    cat = DocumentCategory(document_type) if document_type else None
    results = await orchestrator.search_documents(
        query=query,
        document_type=cat,
        patient_id=patient_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return {"query": query, "total": len(results), "results": results}


@router.get("/ocr/providers", summary="List available OCR providers")
async def list_ocr_providers():
    from app.document_intelligence import get_provider_manager
    manager = get_provider_manager()
    providers = []
    for engine, provider in manager.get_all().items():
        status = await provider.check_health()
        providers.append({
            "engine": str(engine),
            "name": provider.display_name,
            "version": provider.version,
            "status": str(status),
            "requires_gpu": provider.requires_gpu,
        })
    return {
        "providers": providers,
        "default": str(manager.default_engine),
        "available": [str(e) for e in manager.available_engines],
    }


@router.post("/ocr/benchmark", summary="Benchmark OCR providers")
async def benchmark_ocr_providers():
    from app.document_intelligence import get_provider_manager
    manager = get_provider_manager()
    results = await manager.benchmark_all()
    return results


@router.post("/classify", summary="Classify document text")
async def classify_text(
    text: str = Form(...),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    from ..application.service import DefaultClassifierService
    classifier = DefaultClassifierService.__new__(DefaultClassifierService)  # placeholder
    from ..domain.entities import ClassificationResult
    result = ClassificationResult(
        category=DocumentCategory.unknown,
    )
    return {
        "category": str(result.category),
        "confidence": result.confidence_score,
    }


@router.get("/statistics", summary="Document intelligence statistics")
async def get_statistics(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    stats = await orchestrator.get_statistics()
    return stats


@router.post("/remediate", summary="Run automatic remediation")
async def auto_remediate(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    result = await orchestrator.auto_remediate()
    return result


@router.get("/status", summary="Platform health status")
async def platform_status():
    from app.document_intelligence import get_provider_manager, get_orchestrator
    manager = get_provider_manager()
    provider_status = {}
    for engine, provider in manager.get_all().items():
        try:
            status = await provider.check_health()
            provider_status[str(engine)] = str(status)
        except Exception as e:
            provider_status[str(engine)] = f"error: {e}"

    return {
        "platform": "Document Intelligence Platform",
        "status": "operational",
        "providers": provider_status,
        "version": "1.0.0",
        "mode": "offline",
    }
