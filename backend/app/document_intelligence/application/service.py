from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from ..domain.entities import (
    ClassificationResult,
    CollaborationSession,
    DigitalPreservationRecord,
    DocumentAnnotation,
    DocumentIntelligenceResult,
    DocumentLifecycleRecord,
    DocumentPage,
    DocumentReview,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    GovernanceEvent,
    GovernancePolicy,
    GovernmentDocument,
    OcrResult,
    PipelineHealth,
    ProcessingPipelineResult,
    ScannedDocument,
    SemanticQuery,
    SemanticSearchResult,
)
from ..domain.enums import (
    CollaborationRole,
    DigitalPreservationStandard,
    DocumentCategory,
    DocumentStatus,
    EventChannel,
    GovernanceDomain,
    GovernanceRuleSeverity,
    OcrEngine,
    OcrLanguage,
    ProcessingPhase,
    ProcessingPriority,
    RetentionPolicy,
    ReviewDecision,
)
from ..domain.events import (
    DocumentClassificationFailed,
    DocumentClassified,
    DocumentIngested,
    DocumentOcrCompleted,
    DocumentProcessed,
    DocumentProcessingFailed,
)
from ..domain.repository import (
    ClassificationResultRepository,
    DocumentRepository,
    EntityRepository,
    FieldRepository,
    OcrResultRepository,
    PipelineResultRepository,
    StorageRepository,
    TableRepository,
)
from ..exceptions import (
    ClassificationError,
    EntityExtractionError,
    FhirMappingError,
    IndexingError,
    IngestionError,
    KnowledgeExtractionError,
    OcrProviderError,
    SearchError,
)
from .interfaces import (
    AccessControlService,
    AuditService,
    CollaborationService,
    DocumentClassifier,
    DocumentClassifierService,
    DocumentIngestionService,
    DocumentLifecycleManager,
    DocumentLifecycleService,
    DocumentParser,
    EncryptionService,
    EntityExtractionService,
    EntityExtractor,
    EventBusService,
    FhirMapper,
    FhirMappingService,
    GovernanceService,
    GovernmentRecordsService,
    ImagePreprocessor,
    KnowledgeExtractor,
    KnowledgeGraphService,
    KnowledgePipelineService,
    LayoutDetector,
    MedicalParser,
    NationalArchiveService,
    ObservabilityService,
    OcrPipelineService,
    OcrProvider,
    PipelineEventPublisher,
    ProviderBenchmark,
    RemediationService,
    SearchIndexer,
    SearchService,
    SemanticSearchService,
    WebhookService,
)

logger = logging.getLogger("gula.document_intelligence")


class DefaultIngestionService(DocumentIngestionService):
    def __init__(
        self,
        document_repo: DocumentRepository,
        storage_repo: StorageRepository,
        parser: DocumentParser,
        encryptor: EncryptionService,
        event_publisher: PipelineEventPublisher,
        audit: AuditService,
    ) -> None:
        self._doc_repo = document_repo
        self._storage = storage_repo
        self._parser = parser
        self._encryptor = encryptor
        self._events = event_publisher
        self._audit = audit

    async def ingest(
        self,
        data: bytes,
        filename: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> ScannedDocument:
        if not data:
            raise IngestionError("Empty data provided for ingestion")

        checksum = await self._encryptor.hash_document(data)

        filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        page_count = 0
        try:
            page_count = await self._parser.get_page_count(data, mime_type)
        except Exception as exc:
            logger.warning("Could not determine page count: %s", exc)

        doc = ScannedDocument(
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            page_count=page_count,
            source="api_upload",
            metadata=metadata or {},
        )

        storage_path = f"documents/{doc.id}/{filename}"
        encrypted_data = await self._encryptor.encrypt(data)
        storage_uri = await self._storage.save(encrypted_data, storage_path)

        doc.mark_ingested(storage_path=storage_path, checksum=checksum)
        doc.storage_uri = storage_uri

        saved = await self._doc_repo.save(doc)

        await self._events.publish(
            DocumentIngested(
                document_id=saved.id,
                filename=filename,
                mime_type=mime_type,
                size_bytes=len(data),
                page_count=page_count,
                storage_path=storage_path,
                checksum=checksum,
            )
        )

        await self._audit.log_event(
            "document.ingested",
            saved.id,
            {"filename": filename, "size": len(data), "mime_type": mime_type},
        )

        logger.info("Document ingested: %s (%s, %d bytes)", saved.id, filename, len(data))
        return saved

    async def ingest_batch(
        self, files: list[tuple[bytes, str, str]]
    ) -> list[ScannedDocument]:
        results = []
        for data, filename, mime_type in files:
            try:
                doc = await self.ingest(data, filename, mime_type)
                results.append(doc)
            except IngestionError as exc:
                logger.error("Batch ingest failed for %s: %s", filename, exc)
        return results

    async def ingest_from_uri(
        self, uri: str, metadata: dict[str, Any] | None = None
    ) -> ScannedDocument:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(uri)
            response.raise_for_status()
            data = response.content

        filename = uri.rsplit("/", 1)[-1] if "/" in uri else "remote_document"
        content_type = response.headers.get("content-type", "application/octet-stream")
        return await self.ingest(data, filename, content_type, metadata)

    async def ingest_from_fhir(
        self, document_reference: dict[str, Any]
    ) -> ScannedDocument:
        attachment = document_reference.get("content", [{}])[0].get("attachment", {})
        url = attachment.get("url", "")
        if url:
            return await self.ingest_from_uri(url)

        data_encoded = attachment.get("data", "")
        if data_encoded:
            import base64

            data = base64.b64decode(data_encoded)
            content_type = attachment.get("contentType", "application/octet-stream")
            filename = document_reference.get("id", "fhir_document") + "." + content_type.split("/")[-1]
            return await self.ingest(data, filename, content_type)

        raise IngestionError("FHIR DocumentReference has no downloadable content")


class DefaultOcrPipelineService(OcrPipelineService):
    def __init__(
        self,
        providers: dict[OcrEngine, OcrProvider],
        parser: DocumentParser,
        preprocessor: ImagePreprocessor,
        layout_detector: LayoutDetector,
        benchmark: ProviderBenchmark,
        ocr_repo: OcrResultRepository,
        doc_repo: DocumentRepository,
        event_publisher: PipelineEventPublisher,
        audit: AuditService,
        default_provider: OcrEngine = OcrEngine.tesseract,
    ) -> None:
        self._providers = providers
        self._parser = parser
        self._preprocessor = preprocessor
        self._layout = layout_detector
        self._benchmark = benchmark
        self._ocr_repo = ocr_repo
        self._doc_repo = doc_repo
        self._events = event_publisher
        self._audit = audit
        self._default_provider = default_provider

    async def _get_provider(self, provider: OcrEngine | None) -> OcrProvider:
        engine = provider or self._default_provider
        if engine not in self._providers:
            best = await self._benchmark.get_best_provider(OcrLanguage.arabic_english)
            engine = best
        if engine not in self._providers:
            engines = list(self._providers.keys())
            if not engines:
                raise OcrProviderError("No OCR providers available")
            engine = engines[0]
        return self._providers[engine]

    async def process_document(
        self,
        document: ScannedDocument,
        provider: OcrEngine | None = None,
        language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> OcrResult:
        t0 = time.perf_counter()

        ocr_provider = await self._get_provider(provider)

        raw_data = await self._parser._read_storage(document)

        if document.is_image:
            pages_data = [raw_data]
        elif document.is_pdf:
            pages_data = await self._parser.parse_pdf(raw_data)
        elif document.mime_type == "image/tiff":
            pages_data = await self._parser.parse_tiff(raw_data)
        else:
            pages_data = [raw_data]

        pages: list[DocumentPage] = []
        for i, page_data in enumerate(pages_data):
            processed = await self._preprocessor.auto_preprocess(page_data)
            page = await ocr_provider.ocr_image(processed, language)
            page.page_number = i + 1
            pages.append(page)

        full_text = "\n\n".join(p.text for p in pages if p.text)
        avg_conf = sum(p.confidence for p in pages) / max(len(pages), 1)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        result = OcrResult(
            document_id=document.id,
            pages=pages,
            full_text=full_text,
            ocr_engine=ocr_provider.engine_type,
            confidence=avg_conf,
            processing_time_ms=elapsed_ms,
            language=language,
            page_count=len(pages),
            success=True,
        )

        await self._ocr_repo.save(result)
        document.mark_ocr_completed()
        await self._doc_repo.save(document)

        await self._events.publish(
            DocumentOcrCompleted(
                document_id=document.id,
                ocr_engine=ocr_provider.engine_type,
                confidence=avg_conf,
                processing_time_ms=elapsed_ms,
                page_count=len(pages),
                text_length=len(full_text),
            )
        )

        await self._audit.log_event(
            "document.ocr.completed",
            document.id,
            {
                "engine": str(ocr_provider.engine_type),
                "pages": len(pages),
                "confidence": round(avg_conf, 2),
                "time_ms": round(elapsed_ms, 0),
            },
        )

        logger.info(
            "OCR completed: %s (%s, %d pages, %.1fms, confidence=%.2f)",
            document.id,
            ocr_provider.engine_type,
            len(pages),
            elapsed_ms,
            avg_conf,
        )
        return result

    async def process_batch(
        self,
        documents: list[ScannedDocument],
        provider: OcrEngine | None = None,
    ) -> list[OcrResult]:
        import asyncio

        results = await asyncio.gather(
            *[self.process_document(d, provider) for d in documents],
            return_exceptions=True,
        )
        final: list[OcrResult] = []
        for r in results:
            if isinstance(r, Exception):
                logger.error("Batch OCR failed: %s", r)
            else:
                final.append(r)
        return final

    async def process_stream(
        self,
        document: ScannedDocument,
        provider: OcrEngine | None = None,
    ):
        ocr_provider = await self._get_provider(provider)
        raw_data = await self._parser._read_storage(document)
        pages_data = await self._parser.parse_pdf(raw_data)

        for i, page_data in enumerate(pages_data):
            processed = await self._preprocessor.auto_preprocess(page_data)
            page = await ocr_provider.ocr_image(processed)
            page.page_number = i + 1
            yield page


class DefaultClassifierService(DocumentClassifierService):
    def __init__(
        self,
        classifier: DocumentClassifier,
        classifier_repo: ClassificationResultRepository,
        doc_repo: DocumentRepository,
        event_publisher: PipelineEventPublisher,
        audit: AuditService,
    ) -> None:
        self._classifier = classifier
        self._classifier_repo = classifier_repo
        self._doc_repo = doc_repo
        self._events = event_publisher
        self._audit = audit

    async def classify_document(
        self, document: ScannedDocument, ocr_result: OcrResult
    ) -> ClassificationResult:
        try:
            result = await self._classifier.classify(
                ocr_result.full_text, ocr_result.pages
            )
        except Exception as exc:
            await self._events.publish(
                DocumentClassificationFailed(
                    document_id=document.id, error_message=str(exc)
                )
            )
            raise ClassificationError(f"Classification failed: {exc}") from exc

        await self._classifier_repo.save(result)

        await self._events.publish(
            DocumentClassified(
                document_id=document.id,
                category=result.category,
                confidence=result.confidence_score,
                method=result.method,
            )
        )

        await self._audit.log_event(
            "document.classified",
            document.id,
            {
                "category": str(result.category),
                "confidence": result.confidence_score,
                "method": result.method,
            },
        )

        logger.info(
            "Document classified: %s → %s (%.2f)",
            document.id,
            result.category,
            result.confidence_score,
        )
        return result

    async def classify_text(self, text: str) -> ClassificationResult:
        return await self._classifier.classify(text)


class DefaultEntityExtractionService(EntityExtractionService):
    def __init__(
        self,
        extractor: EntityExtractor,
        entity_repo: EntityRepository,
        field_repo: FieldRepository,
        table_repo: TableRepository,
        medical_parser: MedicalParser | None = None,
        event_publisher: PipelineEventPublisher | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._extractor = extractor
        self._entity_repo = entity_repo
        self._field_repo = field_repo
        self._table_repo = table_repo
        self._medical = medical_parser
        self._events = event_publisher
        self._audit = audit

    async def extract_from_document(
        self, document: ScannedDocument, ocr_result: OcrResult
    ) -> tuple[list[ExtractedEntity], list[ExtractedField], list[ExtractedTable]]:
        try:
            entities, fields, tables = await self._extractor.extract(
                ocr_result.full_text
            )
        except Exception as exc:
            raise EntityExtractionError(f"Entity extraction failed: {exc}") from exc

        if self._medical and ocr_result.full_text:
            try:
                if any("glucose" in e.value.lower() for e in entities):
                    parsed = await self._medical.parse_lab_report(ocr_result.full_text)
                    for key, value in parsed.items():
                        if isinstance(value, str):
                            fields.append(
                                ExtractedField(
                                    name=key, value=value, confidence=0.8
                                )
                            )
            except Exception:
                pass

        await self._entity_repo.save_many(document.id, entities)
        await self._field_repo.save_many(document.id, fields)
        await self._table_repo.save_many(document.id, tables)

        if self._audit:
            await self._audit.log_event(
                "document.entities.extracted",
                document.id,
                {
                    "entity_count": len(entities),
                    "field_count": len(fields),
                    "table_count": len(tables),
                },
            )

        return entities, fields, tables

    async def extract_from_text(
        self, text: str, category: DocumentCategory | None = None
    ) -> tuple[list[ExtractedEntity], list[ExtractedField], list[ExtractedTable]]:
        return await self._extractor.extract(text, category)


class DefaultFhirMappingService(FhirMappingService):
    def __init__(
        self,
        mapper: FhirMapper,
        event_publisher: PipelineEventPublisher | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._mapper = mapper
        self._events = event_publisher
        self._audit = audit

    async def map_document(
        self,
        document: ScannedDocument,
        ocr_result: OcrResult,
        entities: list[ExtractedEntity],
        fields: list[ExtractedField],
    ) -> dict[str, Any]:
        try:
            result = await self._mapper.map_all(
                entities, fields, document, ocr_result
            )
        except Exception as exc:
            raise FhirMappingError(f"FHIR mapping failed: {exc}") from exc

        if self._audit:
            await self._audit.log_event(
                "document.fhir.mapped",
                document.id,
                {
                    "resource_types": list(result.keys()),
                    "resource_count": sum(
                        len(v) if isinstance(v, list) else 1 for v in result.values()
                    ),
                },
            )

        return result

    async def map_to_bundle(self, resources: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": r} for r in resources],
            "total": len(resources),
        }


class DefaultKnowledgePipelineService(KnowledgePipelineService):
    def __init__(
        self,
        knowledge_extractor: KnowledgeExtractor,
        search_indexer: SearchIndexer,
        event_publisher: PipelineEventPublisher | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._extractor = knowledge_extractor
        self._indexer = search_indexer
        self._events = event_publisher
        self._audit = audit

    async def process(
        self,
        document: ScannedDocument,
        ocr_result: OcrResult,
        entities: list[ExtractedEntity],
    ) -> dict[str, Any]:
        try:
            concepts = await self._extractor.extract_concepts(
                ocr_result.full_text, entities
            )
            kg = await self._extractor.build_knowledge_graph(concepts)
            embeddings = await self._extractor.generate_embeddings(
                ocr_result.full_text
            )

            idx_entry = await self._indexer.index_document(
                document, ocr_result.full_text, entities
            )

            timeline = await self._extractor.extract_clinical_timeline(entities)

            result = {
                "concepts": concepts,
                "knowledge_graph": kg,
                "embeddings": embeddings,
                "search_index_id": idx_entry,
                "clinical_timeline": timeline,
            }

            if self._audit:
                await self._audit.log_event(
                    "document.knowledge.processed",
                    document.id,
                    {
                        "concept_count": len(concepts),
                        "kg_nodes": len(kg.get("nodes", [])),
                        "kg_edges": len(kg.get("edges", [])),
                    },
                )

            return result

        except Exception as exc:
            raise KnowledgeExtractionError(f"Knowledge extraction failed: {exc}") from exc

    async def query_knowledge_graph(self, query: str) -> list[dict[str, Any]]:
        return await self._indexer.search(query)

    async def get_patient_timeline(
        self, patient_id: UUID
    ) -> list[dict[str, Any]]:
        return await self._indexer.search(
            "", filters={"patient_id": str(patient_id)}
        )


class DefaultSearchService(SearchService):
    def __init__(self, indexer: SearchIndexer) -> None:
        self._indexer = indexer

    async def index_document(
        self, document: ScannedDocument, text: str, entities: list[ExtractedEntity]
    ) -> None:
        try:
            await self._indexer.index_document(document, text, entities)
        except Exception as exc:
            raise IndexingError(f"Search indexing failed: {exc}") from exc

    async def search(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        try:
            return await self._indexer.search(query, filters)
        except Exception as exc:
            raise SearchError(f"Search failed: {exc}") from exc

    async def advanced_search(
        self,
        query: str,
        document_type: DocumentCategory | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        patient_id: UUID | None = None,
        doctor_name: str | None = None,
        lab_name: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"limit": limit}
        if document_type:
            filters["category"] = str(document_type)
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if patient_id:
            filters["patient_id"] = str(patient_id)
        if doctor_name:
            filters["doctor_name"] = doctor_name
        if lab_name:
            filters["lab_name"] = lab_name
        try:
            return await self._indexer.search(query, filters)
        except Exception as exc:
            raise SearchError(f"Advanced search failed: {exc}") from exc


class DocumentIntelligenceOrchestrator:
    def __init__(
        self,
        ingestion: DocumentIngestionService,
        ocr_pipeline: OcrPipelineService,
        classifier: DocumentClassifierService,
        entity_extractor: EntityExtractionService,
        fhir_mapper: FhirMappingService,
        knowledge_pipeline: KnowledgePipelineService,
        search: SearchService,
        lifecycle: DocumentLifecycleManager,
        remediation: RemediationService,
        doc_repo: DocumentRepository,
        pipeline_repo: PipelineResultRepository,
        event_publisher: PipelineEventPublisher,
        audit: AuditService,
        gov_service: GovernmentRecordsService | None = None,
        collab_service: CollaborationService | None = None,
        gov_service_: GovernanceService | None = None,
        archive_service: NationalArchiveService | None = None,
        kg_service: KnowledgeGraphService | None = None,
        webhook_service: WebhookService | None = None,
        obs_service: ObservabilityService | None = None,
        access_service: AccessControlService | None = None,
        semantic_service: SemanticSearchService | None = None,
        lifecycle_service: DocumentLifecycleService | None = None,
        event_bus: EventBusService | None = None,
    ) -> None:
        self._ingestion = ingestion
        self._ocr = ocr_pipeline
        self._classifier = classifier
        self._entity_extractor = entity_extractor
        self._fhir = fhir_mapper
        self._knowledge = knowledge_pipeline
        self._search = search
        self._lifecycle = lifecycle
        self._remediation = remediation
        self._doc_repo = doc_repo
        self._pipeline_repo = pipeline_repo
        self._events = event_publisher
        self._audit = audit
        self._gov = gov_service
        self._collab = collab_service
        self._gov_ = gov_service_
        self._archive = archive_service
        self._kg = kg_service
        self._webhook = webhook_service
        self._obs = obs_service
        self._access = access_service
        self._semantic = semantic_service
        self._lifecycle_svc = lifecycle_service
        self._event_bus = event_bus

    async def process_document(
        self,
        data: bytes,
        filename: str,
        mime_type: str,
        language: OcrLanguage = OcrLanguage.arabic_english,
        priority: ProcessingPriority = ProcessingPriority.normal,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentIntelligenceResult:
        t_start = time.perf_counter()
        pipeline = ProcessingPipelineResult()
        result = DocumentIntelligenceResult()

        try:
            doc = await self._ingestion.ingest(data, filename, mime_type, metadata)
            result.document = doc
            pipeline.phases_completed.append(ProcessingPhase.ingestion)

            doc.priority = priority
            await self._doc_repo.save(doc)

            ocr_result = await self._ocr.process_document(doc, language=language)
            pipeline.ocr_result = ocr_result
            pipeline.phases_completed.append(ProcessingPhase.ocr)
            result.ocr_text = ocr_result.full_text

            classification = await self._classifier.classify_document(doc, ocr_result)
            pipeline.classification = classification
            pipeline.phases_completed.append(ProcessingPhase.classification)
            result.classification = classification.category

            entities, fields, tables = await self._entity_extractor.extract_from_document(
                doc, ocr_result
            )
            pipeline.entities = entities
            pipeline.fields = fields
            pipeline.tables = tables
            pipeline.phases_completed.append(ProcessingPhase.entity_extraction)
            result.entities = entities
            result.fields = fields
            result.tables = tables

            fhir = await self._fhir.map_document(doc, ocr_result, entities, fields)
            pipeline.fhir_resources = list(fhir.values()) if isinstance(fhir, dict) else [fhir]
            pipeline.phases_completed.append(ProcessingPhase.fhir_mapping)
            result.fhir = fhir

            kg_result = await self._knowledge.process(doc, ocr_result, entities)
            pipeline.knowledge_graph_entries = kg_result.get("knowledge_graph", {}).get(
                "nodes", []
            )
            pipeline.vector_embeddings = kg_result.get("embeddings", [])
            pipeline.phases_completed.append(ProcessingPhase.knowledge_extraction)
            result.knowledge_graph = kg_result
            result.embeddings = kg_result.get("embeddings", [])

            await self._search.index_document(
                doc, ocr_result.full_text, entities
            )
            pipeline.phases_completed.append(ProcessingPhase.search_indexing)

            doc.mark_processed()
            await self._doc_repo.save(doc)

            pipeline.success = True
            result.success = True

        except (IngestionError, OcrProviderError, ClassificationError,
                EntityExtractionError, FhirMappingError, KnowledgeExtractionError,
                IndexingError) as exc:
            pipeline.success = False
            pipeline.error_message = str(exc)
            result.success = False
            result.error = str(exc)
            logger.error("Document processing pipeline failed: %s", exc)

            if result.document:
                phase = ProcessingPhase.ingestion
                if ProcessingPhase.ocr in pipeline.phases_completed:
                    phase = ProcessingPhase.ocr
                if ProcessingPhase.classification in pipeline.phases_completed:
                    phase = ProcessingPhase.classification
                if ProcessingPhase.entity_extraction in pipeline.phases_completed:
                    phase = ProcessingPhase.entity_extraction
                if ProcessingPhase.fhir_mapping in pipeline.phases_completed:
                    phase = ProcessingPhase.fhir_mapping
                if ProcessingPhase.knowledge_extraction in pipeline.phases_completed:
                    phase = ProcessingPhase.knowledge_extraction

                await self._events.publish(
                    DocumentProcessingFailed(
                        document_id=result.document.id,
                        phase=phase,
                        error_message=str(exc),
                        processing_time_ms=(time.perf_counter() - t_start) * 1000,
                    )
                )

        except Exception as exc:
            pipeline.success = False
            pipeline.error_message = f"Unexpected error: {exc}"
            result.success = False
            result.error = f"Unexpected error: {exc}"
            logger.exception("Unexpected pipeline error: %s", exc)

        pipeline.total_processing_time_ms = (time.perf_counter() - t_start) * 1000
        result.pipeline = pipeline

        result.processing_summary = {
            "document_id": str(result.document.id) if result.document else "",
            "phases_completed": [str(p) for p in pipeline.phases_completed],
            "total_time_ms": round(pipeline.total_processing_time_ms, 2),
            "page_count": result.document.page_count if result.document else 0,
            "entity_count": len(pipeline.entities),
            "field_count": len(pipeline.fields),
            "table_count": len(pipeline.tables),
            "success": pipeline.success,
        }

        if result.document and pipeline.success:
            await self._events.publish(
                DocumentProcessed(
                    document_id=result.document.id,
                    phases_completed=pipeline.phases_completed,
                    total_processing_time_ms=pipeline.total_processing_time_ms,
                    entity_count=len(pipeline.entities),
                    fhir_resource_count=len(pipeline.fhir_resources),
                )
            )

        await self._pipeline_repo.save(pipeline)

        return result

    async def process_batch(
        self,
        files: list[tuple[bytes, str, str]],
        language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> list[DocumentIntelligenceResult]:
        import asyncio

        tasks = [
            self.process_document(data, filename, mime_type, language)
            for data, filename, mime_type in files
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def get_document(self, document_id: UUID) -> ScannedDocument | None:
        return await self._doc_repo.get(document_id)

    async def get_document_result(self, document_id: UUID) -> DocumentIntelligenceResult | None:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            return None
        pipeline = await self._pipeline_repo.get(document_id)
        return DocumentIntelligenceResult(
            document=doc,
            pipeline=pipeline or ProcessingPipelineResult(),
            success=(pipeline.success if pipeline else False),
        )

    async def search_documents(
        self,
        query: str,
        document_type: DocumentCategory | None = None,
        patient_id: UUID | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return await self._search.advanced_search(
            query=query,
            document_type=document_type,
            patient_id=patient_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    async def auto_remediate(self) -> dict[str, Any]:
        return await self._remediation.auto_remediate()

    async def get_statistics(self) -> dict[str, Any]:
        status_counts = await self._doc_repo.count_by_status()
        return {
            "total_documents": sum(status_counts.values()),
            "by_status": {str(k): v for k, v in status_counts.items()},
            "pending_processing": sum(
                v for k, v in status_counts.items()
                if k in (DocumentStatus.pending_ingestion, DocumentStatus.ocr_pending,
                         DocumentStatus.classification_pending, DocumentStatus.entity_extraction_pending,
                         DocumentStatus.fhir_mapping_pending)
            ),
            "failed": sum(
                v for k, v in status_counts.items()
                if k in (DocumentStatus.ocr_failed, DocumentStatus.classification_failed,
                         DocumentStatus.entity_extraction_failed, DocumentStatus.fhir_mapping_failed)
            ),
        }

    @property
    def classifier(self) -> DocumentClassifierService:
        return self._classifier

    async def classify_text(self, text: str) -> ClassificationResult:
        return await self._classifier.classify_text(text)

    # ── Government Records ──
    async def register_government_document(self, gov: GovernmentDocument) -> GovernmentDocument:
        if self._gov is None:
            raise RuntimeError("GovernmentRecordsService not configured")
        return await self._gov.register_government_document(gov.document_id, gov)

    async def get_government_document(self, document_id: UUID) -> GovernmentDocument | None:
        if self._gov is None:
            raise RuntimeError("GovernmentRecordsService not configured")
        return await self._gov.get_government_document(document_id)

    async def search_government_documents(self, query: str) -> list[GovernmentDocument]:
        if self._gov is None:
            raise RuntimeError("GovernmentRecordsService not configured")
        return await self._gov.search_government_documents(query)

    async def track_order_lifecycle(self, document_id: UUID) -> list[dict[str, Any]]:
        if self._gov is None:
            raise RuntimeError("GovernmentRecordsService not configured")
        return await self._gov.track_order_lifecycle(document_id)

    # ── Collaboration ──
    async def assign_reviewer(self, document_id: UUID, reviewer_id: str, role: CollaborationRole = CollaborationRole.reviewer) -> DocumentReview:
        if self._collab is None:
            raise RuntimeError("CollaborationService not configured")
        return await self._collab.assign_reviewer(document_id, reviewer_id, role)

    async def submit_review(self, review_id: UUID, decision: ReviewDecision, comments: str = "") -> DocumentReview:
        if self._collab is None:
            raise RuntimeError("CollaborationService not configured")
        return await self._collab.submit_review(review_id, decision, comments)

    async def get_reviews(self, document_id: UUID) -> list[DocumentReview]:
        if self._collab is None:
            raise RuntimeError("CollaborationService not configured")
        return await self._collab.get_reviews(document_id)

    async def add_annotation(self, annotation: DocumentAnnotation) -> DocumentAnnotation:
        if self._collab is None:
            raise RuntimeError("CollaborationService not configured")
        return await self._collab.add_annotation(annotation)

    async def get_annotations(self, document_id: UUID) -> list[DocumentAnnotation]:
        if self._collab is None:
            raise RuntimeError("CollaborationService not configured")
        return await self._collab.get_annotations(document_id)

    async def create_session(self, document_id: UUID) -> CollaborationSession:
        if self._collab is None:
            raise RuntimeError("CollaborationService not configured")
        return await self._collab.create_session(document_id)

    # ── Governance ──
    async def create_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        if self._gov_ is None:
            raise RuntimeError("GovernanceService not configured")
        return await self._gov_.create_policy(policy)

    async def list_policies(self, domain: GovernanceDomain | None = None) -> list[GovernancePolicy]:
        if self._gov_ is None:
            raise RuntimeError("GovernanceService not configured")
        return await self._gov_.list_policies(domain)

    async def delete_policy(self, policy_id: UUID) -> None:
        if self._gov_ is None:
            raise RuntimeError("GovernanceService not configured")
        await self._gov_.delete_policy(policy_id)

    async def evaluate_document(self, document_id: UUID) -> list[GovernanceEvent]:
        if self._gov_ is None:
            raise RuntimeError("GovernanceService not configured")
        return await self._gov_.evaluate_document(document_id)

    async def get_governance_events(self, document_id: UUID | None = None, severity: GovernanceRuleSeverity | None = None) -> list[GovernanceEvent]:
        if self._gov_ is None:
            raise RuntimeError("GovernanceService not configured")
        return await self._gov_.get_governance_events(document_id, severity)

    # ── Archive & Preservation ──
    async def preserve_document(self, document_id: UUID, standard: DigitalPreservationStandard = DigitalPreservationStandard.oais) -> DigitalPreservationRecord:
        if self._archive is None:
            raise RuntimeError("NationalArchiveService not configured")
        return await self._archive.preserve_document(document_id, standard)

    async def get_preservation_record(self, document_id: UUID) -> DigitalPreservationRecord | None:
        if self._archive is None:
            raise RuntimeError("NationalArchiveService not configured")
        return await self._archive.get_preservation_record(document_id)

    async def check_integrity(self, document_id: UUID) -> dict[str, Any]:
        if self._archive is None:
            raise RuntimeError("NationalArchiveService not configured")
        return await self._archive.check_integrity(document_id)

    async def apply_retention(self, document_id: UUID, policy: RetentionPolicy = RetentionPolicy.standard_7y) -> None:
        if self._lifecycle is None:
            raise RuntimeError("DocumentLifecycleManager not configured")
        await self._lifecycle.apply_retention_policy(document_id)

    async def purge_expired(self) -> list[UUID]:
        if self._archive is None:
            raise RuntimeError("NationalArchiveService not configured")
        return await self._archive.purge_expired()

    # ── Knowledge Graph ──
    async def find_related_documents(self, document_id: UUID, max_depth: int = 3) -> list[dict[str, Any]]:
        if self._kg is None:
            raise RuntimeError("KnowledgeGraphService not configured")
        return await self._kg.find_related_documents(document_id, max_depth)

    async def get_entity_network(self, entity_name: str) -> dict[str, Any]:
        if self._kg is None:
            raise RuntimeError("KnowledgeGraphService not configured")
        return await self._kg.get_entity_network(entity_name)

    async def get_document_subgraph(self, document_id: UUID) -> dict[str, Any]:
        if self._kg is None:
            raise RuntimeError("KnowledgeGraphService not configured")
        return await self._kg.get_document_subgraph(document_id)

    async def rebuild_graph(self) -> None:
        if self._kg is None:
            raise RuntimeError("KnowledgeGraphService not configured")
        await self._kg.rebuild_graph()

    # ── Webhooks ──
    async def register_webhook(self, url: str, events: list[EventChannel], secret: str | None = None) -> dict[str, Any]:
        if self._webhook is None:
            raise RuntimeError("WebhookService not configured")
        return await self._webhook.register_webhook(url, events, secret)

    async def unregister_webhook(self, webhook_id: UUID) -> None:
        if self._webhook is None:
            raise RuntimeError("WebhookService not configured")
        await self._webhook.unregister_webhook(webhook_id)

    # ── Observability ──
    async def get_pipeline_health(self) -> list[PipelineHealth]:
        if self._obs is None:
            raise RuntimeError("ObservabilityService not configured")
        return await self._obs.get_pipeline_health()

    async def get_dashboard_data(self) -> dict[str, Any]:
        if self._obs is None:
            raise RuntimeError("ObservabilityService not configured")
        return await self._obs.get_dashboard_data()

    async def get_document_statistics(self) -> dict[str, Any]:
        if self._obs is None:
            raise RuntimeError("ObservabilityService not configured")
        return await self._obs.get_document_statistics()

    async def get_throughput_metrics(self) -> dict[str, Any]:
        if self._obs is None:
            raise RuntimeError("ObservabilityService not configured")
        return await self._obs.get_throughput_metrics()

    # ── Access Control ──
    async def check_access(self, document_id: UUID, user_id: str, permission: str = "viewer") -> bool:
        if self._access is None:
            raise RuntimeError("AccessControlService not configured")
        return await self._access.check_access(document_id, user_id, permission)

    async def grant_access(self, document_id: UUID, user_id: str, role: CollaborationRole) -> None:
        if self._access is None:
            raise RuntimeError("AccessControlService not configured")
        await self._access.grant_access(document_id, user_id, role)

    async def revoke_access(self, document_id: UUID, user_id: str) -> None:
        if self._access is None:
            raise RuntimeError("AccessControlService not configured")
        await self._access.revoke_access(document_id, user_id)

    # ── Semantic Search ──
    async def semantic_search(self, query: SemanticQuery) -> list[SemanticSearchResult]:
        if self._semantic is None:
            raise RuntimeError("SemanticSearchService not configured")
        return await self._semantic.search(query)

    async def similar_documents(self, document_id: UUID, limit: int = 10) -> list[SemanticSearchResult]:
        if self._semantic is None:
            raise RuntimeError("SemanticSearchService not configured")
        return await self._semantic.similar_documents(document_id, limit)

    async def suggest_queries(self, partial: str) -> list[str]:
        if self._semantic is None:
            raise RuntimeError("SemanticSearchService not configured")
        return await self._semantic.suggest_queries(partial)

    # ── Lifecycle ──
    async def get_lifecycle(self, document_id: UUID) -> list[DocumentLifecycleRecord]:
        if self._lifecycle_svc is None:
            raise RuntimeError("DocumentLifecycleService not configured")
        return await self._lifecycle_svc.get_lifecycle(document_id)

    async def get_expiring_documents(self, days: int = 30) -> list[DocumentLifecycleRecord]:
        if self._lifecycle_svc is None:
            raise RuntimeError("DocumentLifecycleService not configured")
        return await self._lifecycle_svc.get_expiring_documents(days)
