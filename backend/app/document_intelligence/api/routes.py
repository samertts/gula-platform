from __future__ import annotations

import contextlib
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from ..application.service import DocumentIntelligenceOrchestrator
from ..domain.entities import (
    DocumentAnnotation,
    GovernancePolicy,
    GovernmentDocument,
    SemanticQuery,
)
from ..domain.enums import (
    CollaborationRole,
    ConfidentialityLevel,
    DigitalPreservationStandard,
    DocumentCategory,
    EventChannel,
    GovernanceDomain,
    GovernancePolicyAction,
    GovernanceRuleSeverity,
    OcrLanguage,
    ProcessingPriority,
    RetentionPolicy,
    ReviewDecision,
)
from ..domain.repository import DocumentRepository
from ..exceptions import (
    DocumentNotFoundError,
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

        with contextlib.suppress(json.JSONDecodeError):
            meta = json.loads(metadata)
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
        inputs.append(
            (data, file.filename or "untitled", file.content_type or "application/octet-stream"),
        )

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
            "phases_completed": [
                str(p) for p in (result.pipeline.phases_completed if result.pipeline else [])
            ],
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
        raise HTTPException(status_code=404, detail="Document not found") from None


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
        providers.append(
            {
                "engine": str(engine),
                "name": provider.display_name,
                "version": provider.version,
                "status": str(status),
                "requires_gpu": provider.requires_gpu,
            },
        )
    return {
        "providers": providers,
        "default": str(manager.default_engine),
        "available": [str(e) for e in manager.available_engines],
    }


@router.post("/ocr/benchmark", summary="Benchmark OCR providers")
async def benchmark_ocr_providers():
    from app.document_intelligence import get_provider_manager

    manager = get_provider_manager()
    return await manager.benchmark_all()


@router.post("/classify", summary="Classify document text")
async def classify_text(
    text: str = Form(...),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    result = await orchestrator.classify_text(text)
    return {
        "category": str(result.category),
        "confidence": result.confidence_score,
        "alternatives": [(str(c), s) for c, s in result.alternatives],
    }


@router.get("/statistics", summary="Document intelligence statistics")
async def get_statistics(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_statistics()


@router.post("/remediate", summary="Run automatic remediation")
async def auto_remediate(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.auto_remediate()


@router.get("/status", summary="Platform health status")
async def platform_status():
    from app.document_intelligence import get_provider_manager

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
        "version": "2.0.0",
        "mode": "offline",
        "features": [
            "ocr",
            "classification",
            "entity_extraction",
            "fhir_mapping",
            "knowledge_graph",
            "semantic_search",
            "government_records",
            "digital_preservation",
            "governance",
            "collaboration",
            "webhooks",
            "observability",
            "lifecycle_management",
            "access_control",
            "retention_management",
        ],
    }


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Government Records & National Archive
# ═══════════════════════════════════════════════════════════════════

gov_router = APIRouter(
    prefix="/document-intelligence/government",
    tags=["Government Records"],
)


@gov_router.post("/register", summary="Register a government document")
async def register_government_document(
    document_id: UUID = Form(...),
    reference_number: str = Form(...),
    issuing_authority: str = Form(...),
    subject: str = Form(None),
    classification: ConfidentialityLevel = Form(ConfidentialityLevel.internal),
    decision_number: str = Form(None),
    contract_number: str = Form(None),
    procurement_number: str = Form(None),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    gov = GovernmentDocument(
        document_id=document_id,
        reference_number=reference_number,
        issuing_authority=issuing_authority,
        subject=subject or "",
        classification=classification,
        decision_number=decision_number or "",
        contract_number=contract_number or "",
        procurement_number=procurement_number or "",
    )
    result = await orchestrator.register_government_document(gov)
    return {"message": "Government document registered", "government_document_id": str(result.id)}


@gov_router.get("/search", summary="Search government documents")
async def search_government_documents(
    query: str = Query(...),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    results = await orchestrator.search_government_documents(query)
    return {"total": len(results), "results": results}


@gov_router.get("/{document_id}", summary="Get government document details")
async def get_government_document(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    result = await orchestrator.get_government_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Government document not found")
    return result


@gov_router.post("/{document_id}/track", summary="Track order lifecycle")
async def track_order_lifecycle(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.track_order_lifecycle(document_id)


router.include_router(gov_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Collaboration
# ═══════════════════════════════════════════════════════════════════

collab_router = APIRouter(
    prefix="/document-intelligence/collaboration",
    tags=["Collaboration"],
)


@collab_router.post("/review/assign", summary="Assign a reviewer")
async def assign_reviewer(
    document_id: UUID = Form(...),
    reviewer_id: str = Form(...),
    role: CollaborationRole = Form(CollaborationRole.reviewer),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    review = await orchestrator.assign_reviewer(document_id, reviewer_id, role)
    return {"message": "Reviewer assigned", "review_id": str(review.id)}


@collab_router.post("/review/{review_id}/submit", summary="Submit a review decision")
async def submit_review(
    review_id: UUID,
    decision: ReviewDecision = Form(...),
    comments: str = Form(""),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    review = await orchestrator.submit_review(review_id, decision, comments)
    return {"message": "Review submitted", "decision": str(review.decision)}


@collab_router.get("/review/{document_id}", summary="Get reviews for a document")
async def get_reviews(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_reviews(document_id)


@collab_router.post("/annotate", summary="Add annotation to document")
async def add_annotation(
    document_id: UUID = Form(...),
    content: str = Form(...),
    page_number: int = Form(0),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    annotation = DocumentAnnotation(
        document_id=document_id,
        page_number=page_number,
        content=content,
    )
    result = await orchestrator.add_annotation(annotation)
    return {"message": "Annotation added", "annotation_id": str(result.id)}


@collab_router.get("/annotations/{document_id}", summary="Get annotations")
async def get_annotations(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_annotations(document_id)


@collab_router.post("/session", summary="Create collaboration session")
async def create_session(
    document_id: UUID = Form(...),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    session = await orchestrator.create_session(document_id)
    return {"message": "Session created", "session_id": str(session.id)}


router.include_router(collab_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Governance
# ═══════════════════════════════════════════════════════════════════

gov_router2 = APIRouter(
    prefix="/document-intelligence/governance",
    tags=["Governance"],
)


@gov_router2.post("/policies", summary="Create a governance policy")
async def create_policy(
    name: str = Form(...),
    description: str = Form(""),
    domain: GovernanceDomain = Form(...),
    severity: GovernanceRuleSeverity = Form(GovernanceRuleSeverity.warning),
    action: GovernancePolicyAction = Form(GovernancePolicyAction.flag),
    conditions: str = Form("{}"),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    import json

    policy = GovernancePolicy(
        name=name,
        description=description,
        domain=domain,
        severity=severity,
        action=action,
        conditions=json.loads(conditions),
    )
    result = await orchestrator.create_policy(policy)
    return {"message": "Policy created", "policy_id": str(result.id)}


@gov_router2.get("/policies", summary="List governance policies")
async def list_policies(
    domain: GovernanceDomain | None = Query(None),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.list_policies(domain)


@gov_router2.delete("/policies/{policy_id}", summary="Delete a policy")
async def delete_policy(
    policy_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    await orchestrator.delete_policy(policy_id)
    return {"message": "Policy deleted"}


@gov_router2.post(
    "/evaluate/{document_id}", summary="Evaluate document against governance policies",
)
async def evaluate_document(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    events = await orchestrator.evaluate_document(document_id)
    return {"total_events": len(events), "events": [str(e.id) for e in events]}


@gov_router2.get("/events", summary="Get governance events")
async def get_governance_events(
    document_id: UUID | None = Query(None),
    severity: GovernanceRuleSeverity | None = Query(None),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_governance_events(document_id, severity)


router.include_router(gov_router2)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Digital Archive & Preservation
# ═══════════════════════════════════════════════════════════════════

archive_router = APIRouter(
    prefix="/document-intelligence/archive",
    tags=["Digital Archive"],
)


@archive_router.post("/preserve/{document_id}", summary="Preserve a document")
async def preserve_document(
    document_id: UUID,
    standard: DigitalPreservationStandard = Form(DigitalPreservationStandard.oais),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    record = await orchestrator.preserve_document(document_id, standard)
    return {"message": "Document preserved", "preservation_id": str(record.id)}


@archive_router.get("/preservation/{document_id}", summary="Get preservation record")
async def get_preservation_record(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    record = await orchestrator.get_preservation_record(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="No preservation record found")
    return {
        "id": str(record.id),
        "standard": str(record.standard),
        "preservation_format": record.preservation_format,
        "checksum_method": str(record.checksum_method),
        "next_integrity_check": record.next_integrity_check.isoformat()
        if record.next_integrity_check
        else None,
    }


@archive_router.post("/check-integrity/{document_id}", summary="Check document integrity")
async def check_integrity(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.check_integrity(document_id)


@archive_router.post("/retention/{document_id}", summary="Apply retention policy")
async def apply_retention(
    document_id: UUID,
    policy: RetentionPolicy = Form(RetentionPolicy.standard_7y),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    await orchestrator.apply_retention(document_id, policy)
    return {"message": f"Retention policy {policy.value} applied"}


@archive_router.post("/purge-expired", summary="Purge expired documents")
async def purge_expired(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    purged = await orchestrator.purge_expired()
    return {"message": f"{len(purged)} documents purged", "purged_ids": [str(d) for d in purged]}


router.include_router(archive_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Knowledge Graph
# ═══════════════════════════════════════════════════════════════════

kg_router = APIRouter(
    prefix="/document-intelligence/knowledge-graph",
    tags=["Knowledge Graph"],
)


@kg_router.get("/related/{document_id}", summary="Find related documents")
async def find_related(
    document_id: UUID,
    max_depth: int = Query(3, le=10),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.find_related_documents(document_id, max_depth)


@kg_router.get("/entity/{entity_name}", summary="Get entity network")
async def get_entity_network(
    entity_name: str,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_entity_network(entity_name)


@kg_router.get("/subgraph/{document_id}", summary="Get document subgraph")
async def get_document_subgraph(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_document_subgraph(document_id)


@kg_router.post("/rebuild", summary="Rebuild knowledge graph")
async def rebuild_knowledge_graph(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    await orchestrator.rebuild_graph()
    return {"message": "Knowledge graph rebuild initiated"}


router.include_router(kg_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Webhooks & Events
# ═══════════════════════════════════════════════════════════════════

webhook_router = APIRouter(
    prefix="/document-intelligence/webhooks",
    tags=["Webhooks"],
)


@webhook_router.post("/register", summary="Register a webhook")
async def register_webhook(
    url: str = Form(...),
    events: str = Form("document_ingested"),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    event_list = [EventChannel(e.strip()) for e in events.split(",")]
    result = await orchestrator.register_webhook(url, event_list)
    return {"message": "Webhook registered", "webhook_id": result.get("id")}


@webhook_router.delete("/{webhook_id}", summary="Unregister a webhook")
async def unregister_webhook(
    webhook_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    await orchestrator.unregister_webhook(webhook_id)
    return {"message": "Webhook unregistered"}


router.include_router(webhook_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Observability
# ═══════════════════════════════════════════════════════════════════

obs_router = APIRouter(
    prefix="/document-intelligence/observability",
    tags=["Observability"],
)


@obs_router.get("/dashboard", summary="Full observability dashboard data")
async def get_dashboard(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_dashboard_data()


@obs_router.get("/pipeline-health", summary="Pipeline health status")
async def get_pipeline_health(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_pipeline_health()


@obs_router.get("/statistics", summary="Detailed document statistics")
async def get_document_statistics(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_document_statistics()


@obs_router.get("/throughput", summary="Pipeline throughput metrics")
async def get_throughput(
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_throughput_metrics()


router.include_router(obs_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Access Control
# ═══════════════════════════════════════════════════════════════════

access_router = APIRouter(
    prefix="/document-intelligence/access",
    tags=["Access Control"],
)


@access_router.post("/grant", summary="Grant document access")
async def grant_access(
    document_id: UUID = Form(...),
    user_id: str = Form(...),
    role: CollaborationRole = Form(CollaborationRole.viewer),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    await orchestrator.grant_access(document_id, user_id, role)
    return {"message": f"Access granted to {user_id}"}


@access_router.post("/revoke", summary="Revoke document access")
async def revoke_access(
    document_id: UUID = Form(...),
    user_id: str = Form(...),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    await orchestrator.revoke_access(document_id, user_id)
    return {"message": f"Access revoked from {user_id}"}


@access_router.get("/check/{document_id}/{user_id}", summary="Check document access")
async def check_access(
    document_id: UUID,
    user_id: str,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    has_access = await orchestrator.check_access(document_id, user_id, "viewer")
    return {"document_id": str(document_id), "user_id": user_id, "has_access": has_access}


router.include_router(access_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Semantic Search
# ═══════════════════════════════════════════════════════════════════

semantic_router = APIRouter(
    prefix="/document-intelligence/semantic-search",
    tags=["Semantic Search"],
)


@semantic_router.post("/query", summary="Semantic search query")
async def semantic_search(
    query_text: str = Form(...),
    limit: int = Form(20),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    query = SemanticQuery(query_text=query_text, limit=limit)
    results = await orchestrator.semantic_search(query)
    return {"query": query_text, "total": len(results), "results": results}


@semantic_router.get("/similar/{document_id}", summary="Find similar documents")
async def find_similar(
    document_id: UUID,
    limit: int = Query(10, le=50),
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    results = await orchestrator.similar_documents(document_id, limit)
    return {"document_id": str(document_id), "total": len(results), "results": results}


@semantic_router.get("/suggest/{partial_query}", summary="Query suggestions")
async def suggest_queries(
    partial_query: str,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    suggestions = await orchestrator.suggest_queries(partial_query)
    return {"suggestions": suggestions}


router.include_router(semantic_router)


# ═══════════════════════════════════════════════════════════════════
# DOCINT-002: Lifecycle Management
# ═══════════════════════════════════════════════════════════════════

lifecycle_router = APIRouter(
    prefix="/document-intelligence/lifecycle",
    tags=["Document Lifecycle"],
)


@lifecycle_router.get("/{document_id}", summary="Get document lifecycle")
async def get_lifecycle(
    document_id: UUID,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_lifecycle(document_id)


@lifecycle_router.get("/expiring/{days}", summary="Get documents expiring soon")
async def get_expiring(
    days: int = 30,
    orchestrator: DocumentIntelligenceOrchestrator = Depends(_get_orchestrator),
):
    return await orchestrator.get_expiring_documents(days)


router.include_router(lifecycle_router)
