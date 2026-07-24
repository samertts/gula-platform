from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from app.document_intelligence.application.service import (
    DefaultClassifierService,
    DefaultEntityExtractionService,
    DefaultFhirMappingService,
    DefaultIngestionService,
    DefaultKnowledgePipelineService,
    DefaultOcrPipelineService,
    DefaultSearchService,
    DocumentIntelligenceOrchestrator,
)
from app.document_intelligence.application.wiring import DefaultDocumentClassifier
from app.document_intelligence.domain.entities import (
    ClassificationResult,
    CollaborationSession,
    DigitalPreservationRecord,
    DocumentAnnotation,
    DocumentEvent,
    DocumentLifecycleRecord,
    DocumentPage,
    DocumentReview,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    GovernanceEvent,
    GovernancePolicy,
    GovernmentDocument,
    KnowledgeGraphEdge,
    OcrResult,
    PipelineHealth,
    ProcessingPipelineResult,
    ScannedDocument,
    SemanticQuery,
    SemanticSearchResult,
)
from app.document_intelligence.domain.enums import (
    ArchiveStatus,
    ClassificationConfidence,
    CollaborationRole,
    ConfidentialityLevel,
    DigitalPreservationStandard,
    DocumentCategory,
    DocumentStatus,
    EntityType,
    EventChannel,
    ExtractedFieldType,
    GovernanceDomain,
    GovernancePolicyAction,
    GovernanceRuleSeverity,
    IntegrityCheckMethod,
    KnowledgeGraphRelation,
    OcrEngine,
    OcrEngineStatus,
    OcrLanguage,
    ProcessingPhase,
    ProcessingPriority,
    RetentionPolicy,
    ReviewDecision,
    StorageBackend,
)
from app.document_intelligence.domain.repository import (
    AccessControlRepository,
    AnnotationRepository,
    DocumentEventRepository,
    DocumentRepository,
    DocumentVersionRepository,
    GovernanceEventRepository,
    GovernancePolicyRepository,
    GovernmentDocumentRepository,
    GraphEdgeRepository,
    LifecycleRepository,
    PipelineHealthRepository,
    PreservationRepository,
    RetentionRepository,
    ReviewRepository,
    WebhookRepository,
)
from app.document_intelligence.exceptions import (
    DocumentIntelligenceError,
    DocumentNotFoundError,
    IngestionError,
    OcrProviderError,
)
from app.document_intelligence.infrastructure.repository import (
    LocalStorageRepository,
    SqlDocumentRepository,
)
from app.document_intelligence.infrastructure.services import (
    InfrastructureAccessControlService,
    InfrastructureCollaborationService,
    InfrastructureDocumentLifecycleManager,
    InfrastructureDocumentLifecycleService,
    InfrastructureEventBusService,
    InfrastructureGovernanceService,
    InfrastructureGovernmentRecordsService,
    InfrastructureKnowledgeGraphService,
    InfrastructureNationalArchiveService,
    InfrastructureObservabilityService,
    InfrastructureSemanticSearchService,
    InfrastructureVersioningService,
    InfrastructureWebhookService,
)
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ═══════════════════════════════════════════════════════════════════
# DOMAIN ENTITY TESTS
# ═══════════════════════════════════════════════════════════════════

class TestScannedDocument:
    def test_create(self):
        doc = ScannedDocument(filename="test.pdf", mime_type="application/pdf")
        assert doc.id is not None
        assert isinstance(doc.id, UUID)
        assert doc.status == DocumentStatus.pending_ingestion

    def test_mark_ingested(self):
        doc = ScannedDocument()
        doc.mark_ingested("/path/to/file", "abc123")
        assert doc.status == DocumentStatus.ingested
        assert doc.checksum_sha256 == "abc123"
        assert doc.storage_path == "/path/to/file"

    def test_mark_ocr_completed(self):
        doc = ScannedDocument()
        doc.mark_ocr_completed()
        assert doc.status == DocumentStatus.ocr_completed

    def test_mark_ocr_failed(self):
        doc = ScannedDocument()
        doc.mark_ocr_failed("No text found")
        assert doc.status == DocumentStatus.ocr_failed
        assert doc.error_message == "No text found"
        assert doc.retry_count == 1

    def test_mark_processed(self):
        doc = ScannedDocument()
        doc.mark_processed()
        assert doc.status == DocumentStatus.knowledge_indexed
        assert doc.processed_at is not None

    def test_extension(self):
        assert ScannedDocument(filename="report.pdf").extension == "pdf"
        assert ScannedDocument(filename="image.PNG").extension == "png"
        assert ScannedDocument(filename="noext").extension == ""

    def test_is_image(self):
        assert ScannedDocument(mime_type="image/jpeg").is_image is True
        assert ScannedDocument(mime_type="image/png").is_image is True
        assert ScannedDocument(mime_type="application/pdf").is_image is False

    def test_is_pdf(self):
        assert ScannedDocument(mime_type="application/pdf").is_pdf is True
        assert ScannedDocument(mime_type="image/jpeg").is_pdf is False


class TestGovernmentDocument:
    def test_create(self):
        doc = GovernmentDocument(
            reference_number="MOH-001-2026",
            issuing_authority="Ministry of Health",
            subject="New Laboratory Guidelines",
        )
        assert doc.reference_number == "MOH-001-2026"
        assert doc.issuing_authority == "Ministry of Health"
        assert doc.classification == ConfidentialityLevel.internal


class TestDocumentReview:
    def test_create(self):
        review = DocumentReview(reviewer_id="user1", reviewer_name="Dr. Ali")
        assert review.role == CollaborationRole.reviewer
        assert review.decision is None


class TestDigitalPreservationRecord:
    def test_create(self):
        record = DigitalPreservationRecord(
            original_format="application/pdf",
            preservation_format="application/pdf",
            original_checksum="abc",
            preservation_checksum="abc",
            preservation_location="/archive/123",
        )
        assert record.standard == DigitalPreservationStandard.oais


class TestGovernancePolicy:
    def test_create(self):
        policy = GovernancePolicy(
            name="Auto-Archive-7Y",
            domain=GovernanceDomain.data_retention,
            severity=GovernanceRuleSeverity.warning,
            conditions={"policy": "7_year_retention"},
        )
        assert policy.enabled is True


class TestKnowledgeGraphEdge:
    def test_create(self):
        edge = KnowledgeGraphEdge(
            source_entity="Patient-123",
            target_entity="Diagnosis-DM",
            relation=KnowledgeGraphRelation.associated_with,
        )
        assert edge.confidence == 0.0
        assert edge.weight == 1.0


class TestSemanticQuery:
    def test_create(self):
        query = SemanticQuery(query_text="diabetes test results", limit=10)
        assert query.hybrid_search is True
        assert query.arabic_boost is True


# ═══════════════════════════════════════════════════════════════════
# ENUM TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEnums:
    def test_document_categories(self):
        cats = [e.value for e in DocumentCategory]
        assert "laboratory_report" in cats
        assert "radiology_report" in cats
        assert "prescription" in cats
        assert "official_government_letter" in cats
        assert "administrative_order" in cats

    def test_confidentiality_levels(self):
        assert ConfidentialityLevel.unrestricted.value == "unrestricted"
        assert ConfidentialityLevel.top_secret.value == "top_secret"

    def test_collaboration_roles(self):
        assert CollaborationRole.viewer.value == "viewer"
        assert CollaborationRole.owner.value == "owner"

    def test_governance_domains(self):
        domains = [e.value for e in GovernanceDomain]
        assert "document_classification" in domains
        assert "data_retention" in domains
        assert "access_control" in domains

    def test_event_channels(self):
        channels = [e.value for e in EventChannel]
        assert "document_ingested" in channels
        assert "governance_breach" in channels

    def test_retention_policies(self):
        assert RetentionPolicy.standard_7y.value == "7Y"
        assert RetentionPolicy.permanent.value == "permanent"
        assert RetentionPolicy.legal_hold.value == "legal_hold"


# ═══════════════════════════════════════════════════════════════════
# CLASSIFIER TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDefaultClassifier:
    @pytest.fixture
    def classifier(self):
        return DefaultDocumentClassifier()

    @pytest.mark.parametrize("text,expected_cat", [
        ("Hemoglobin: 14.2 g/dL, WBC: 7500, Glucose: 110 mg/dL", DocumentCategory.laboratory_report),
        ("X-ray chest PA view shows clear lung fields", DocumentCategory.radiology_report),
        ("Take Amoxicillin 500mg three times daily for 7 days", DocumentCategory.prescription),
        ("National ID Number: 123456789012", DocumentCategory.national_id),
        ("شهادة طبية تفيد بأن المريض بحاجة إلى راحة", DocumentCategory.medical_certificate),
    ])
    @pytest.mark.asyncio
    async def test_classify(self, classifier, text, expected_cat):
        result = await classifier.classify(text)
        assert result.category == expected_cat
        assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_classify_unknown(self, classifier):
        result = await classifier.classify("This is completely random text with no medical content")
        assert result.category == DocumentCategory.unknown

    @pytest.mark.asyncio
    async def test_batch_classify(self, classifier):
        texts = [("Lab result: Glucose 95", None), ("Chest X-ray normal", None)]
        results = await classifier.classify_batch(texts)
        assert len(results) == 2


# ═══════════════════════════════════════════════════════════════════
# ENTITY EXTRACTOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDefaultEntityExtractor:
    @pytest.fixture
    def extractor(self):
        from app.document_intelligence.application.wiring import DefaultEntityExtractor
        return DefaultEntityExtractor()

    @pytest.mark.asyncio
    async def test_extract_health_id(self, extractor):
        entities, fields, tables = await extractor.extract("Patient HN-2024123")
        health_ids = [e for e in entities if e.entity_type == EntityType.health_id]
        assert len(health_ids) > 0
        assert "HN-2024123" in health_ids[0].value

    @pytest.mark.asyncio
    async def test_extract_lab_values(self, extractor):
        entities, fields, tables = await extractor.extract("Hemoglobin: 14.5 g/dL")
        assert len(fields) > 0
        assert fields[0].name == "Hemoglobin"

    @pytest.mark.asyncio
    async def test_extract_icd_code(self, extractor):
        entities, fields, tables = await extractor.extract("Diagnosis: E11.9")
        icd_codes = [e for e in entities if e.entity_type == EntityType.icd_code]
        assert len(icd_codes) > 0

    @pytest.mark.asyncio
    async def test_extract_entities_of_type(self, extractor):
        result = await extractor.extract_entities_of_type("Call 07712345678", [EntityType.phone_number])
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════════
# FHIR MAPPER TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDefaultFhirMapper:
    @pytest.fixture
    def mapper(self):
        from app.document_intelligence.application.wiring import DefaultFhirMapper
        return DefaultFhirMapper()

    @pytest.mark.asyncio
    async def test_document_reference(self, mapper):
        doc = ScannedDocument(id=uuid4(), mime_type="application/pdf", filename="test.pdf")
        result = await mapper.to_document_reference(doc, OcrResult())
        assert result["resourceType"] == "DocumentReference"
        assert result["id"] == str(doc.id)

    @pytest.mark.asyncio
    async def test_patient_resource(self, mapper):
        entities = [ExtractedEntity(entity_type=EntityType.patient_name, value="John Doe")]
        result = await mapper.to_patient(entities)
        assert result is not None
        assert result["resourceType"] == "Patient"

    @pytest.mark.asyncio
    async def test_practitioner_resource(self, mapper):
        entities = [ExtractedEntity(entity_type=EntityType.doctor_name, value="Dr. Smith")]
        result = await mapper.to_practitioner(entities)
        assert result is not None
        assert result["resourceType"] == "Practitioner"

    @pytest.mark.asyncio
    async def test_observation_resources(self, mapper):
        fields = [ExtractedField(name="Hemoglobin", value="14.5", normalized_value="14.5")]
        result = await mapper.to_observation([], fields)
        assert len(result) > 0
        assert result[0]["resourceType"] == "Observation"

    @pytest.mark.asyncio
    async def test_map_all(self, mapper):
        entities = [ExtractedEntity(entity_type=EntityType.patient_name, value="John")]
        fields = [ExtractedField(name="Hb", value="14.5", normalized_value="14.5")]
        result = await mapper.map_all(entities, fields)
        assert "Patient" in result
        assert "Observations" in result


# ═══════════════════════════════════════════════════════════════════
# KNOWLEDGE EXTRACTOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDefaultKnowledgeExtractor:
    @pytest.fixture
    def extractor(self):
        from app.document_intelligence.application.wiring import DefaultKnowledgeExtractor
        return DefaultKnowledgeExtractor()

    @pytest.mark.asyncio
    async def test_extract_concepts(self, extractor):
        entities = [ExtractedEntity(entity_type=EntityType.diagnosis, value="Diabetes")]
        concepts = await extractor.extract_concepts("Patient has Diabetes", entities)
        assert len(concepts) > 0
        assert concepts[0]["name"] == "Diabetes"

    @pytest.mark.asyncio
    async def test_build_knowledge_graph(self, extractor):
        concepts = [{"name": "Diabetes", "type": "diagnosis"}]
        kg = await extractor.build_knowledge_graph(concepts)
        assert "nodes" in kg
        assert "edges" in kg

    @pytest.mark.asyncio
    async def test_generate_embeddings(self, extractor):
        embeddings = await extractor.generate_embeddings("test text")
        assert len(embeddings) == 32


# ═══════════════════════════════════════════════════════════════════
# ORCHESTRATOR TESTS (UNIT)
# ═══════════════════════════════════════════════════════════════════

class MockRepo:
    def __init__(self):
        self._store: dict[str, Any] = {}

    async def save(self, *args, **kwargs):
        obj = args[0] if args else kwargs.get("obj")
        if obj and hasattr(obj, "id") and obj.id:
            key = f"{type(obj).__name__}:{obj.id}"
            self._store[key] = obj
        return obj

    async def get(self, *args, **kwargs):
        doc_id = args[0] if args else kwargs.get("document_id")
        if doc_id:
            # Check if it was stored
            for key, val in self._store.items():
                if hasattr(val, "id") and val.id == doc_id:
                    return val
            # Return a default ScannedDocument for lookups
            return ScannedDocument(
                id=doc_id,
                mime_type="application/pdf",
                storage_path="/tmp/test",
                checksum_sha256="abc123",
            )
        return None

    async def delete(self, *_, **__):
        pass

    async def list(self, *_, **__):
        return []

    async def search(self, *_, **__):
        return [], 0

    async def update_status(self, *_, **__):
        pass

    async def count_by_status(self, *_, **__):
        return {}

    async def find_duplicates(self, *_, **__):
        return []

    async def get_pending_processing(self, *_, **__):
        return []

    async def save_many(self, *_, **__):
        return []

    async def save_version(self, *_, **__):
        pass

    async def get_latest_version(self, *_, **__):
        return 0

    async def list_versions(self, *_, **__):
        return []

    async def grant(self, *_, **__):
        pass

    async def revoke(self, *_, **__):
        pass

    async def check(self, *_, **__):
        return CollaborationRole.viewer

    async def get_by_user(self, *_, **__):
        return []

    async def register(self, *_, **__):
        return {"id": "webhook-1"}

    async def unregister(self, *_, **__):
        pass

    async def get_by_event(self, *_, **__):
        return []

    async def get_by_document(self, *_, **__):
        return []

    async def update(self, obj, *_, **__):
        return obj

    async def list_due_for_integrity_check(self, *_, **__):
        return []

    async def list_expiring(self, *_, **__):
        return []

    async def list_active(self, *_, **__):
        return []

    async def get_by_name(self, *_, **__):
        return None

    async def get_all_pipelines(self, *_, **__):
        return []

    async def get_latest(self, *_, **__):
        return None

    async def find_related(self, *_, **__):
        return []

    async def get_entity_network(self, *_, **__):
        return []

    async def read(self, *_, **__):
        return b"test data"

    async def exists(self, *_, **__):
        return True

    async def get_size(self, *_, **__):
        return 100


class MockClassifier:
    async def classify(self, text, pages=None):
        return ClassificationResult(
            category=DocumentCategory.laboratory_report,
            confidence=ClassificationConfidence.high,
            confidence_score=0.85,
            method="keyword_match",
        )

    async def classify_batch(self, docs):
        return [await self.classify(t) for t, _ in docs]

    async def get_custom_classes(self):
        return []

    async def add_custom_class(self, name, examples):
        pass

    async def classify_text(self, text):
        return await self.classify(text)


class MockClassifierService:
    def __init__(self):
        self._classifier = MockClassifier()

    @property
    def classifier(self):
        return self._classifier

    async def classify_document(self, doc, ocr_result):
        return await self._classifier.classify(ocr_result.full_text)

    async def classify_text(self, text):
        return await self._classifier.classify(text)


class MockExtractor:
    async def extract(self, text, category=None):
        return (
            [ExtractedEntity(entity_type=EntityType.patient_name, value="John Doe")],
            [ExtractedField(name="Hemoglobin", value="14.5")],
            [ExtractedTable(headers=["Test", "Value"], rows=[["Hb", "14.5"]])],
        )

    async def extract_from_pages(self, pages, category=None):
        return await self.extract(" ".join(p.text for p in pages))

    async def extract_entities_of_type(self, text, types):
        all_e, _, _ = await self.extract(text)
        return [e for e in all_e if e.entity_type in types]


@pytest.fixture
def orchestrator():
    mock_repo = MockRepo()
    svc = InfrastructureGovernmentRecordsService(mock_repo, mock_repo)
    collab = InfrastructureCollaborationService(mock_repo, mock_repo)
    gov = InfrastructureGovernanceService(mock_repo, mock_repo, mock_repo)
    archive = InfrastructureNationalArchiveService(mock_repo, mock_repo, mock_repo)
    kg = InfrastructureKnowledgeGraphService(mock_repo)
    webhook = InfrastructureWebhookService(mock_repo, mock_repo)
    obs = InfrastructureObservabilityService(mock_repo)
    access = InfrastructureAccessControlService(mock_repo)
    semantic = InfrastructureSemanticSearchService(mock_repo)
    lifecycle = InfrastructureDocumentLifecycleService(mock_repo)
    event_bus = InfrastructureEventBusService(mock_repo)

    return DocumentIntelligenceOrchestrator(
        ingestion=MockRepo(),
        ocr_pipeline=MockRepo(),
        classifier=MockClassifierService(),
        entity_extractor=MockRepo(),
        fhir_mapper=MockRepo(),
        knowledge_pipeline=MockRepo(),
        search=MockRepo(),
        lifecycle=MockRepo(),
        remediation=MockRepo(),
        doc_repo=mock_repo,
        pipeline_repo=mock_repo,
        event_publisher=MockRepo(),
        audit=MockRepo(),
        gov_service=svc,
        collab_service=collab,
        gov_service_=gov,
        archive_service=archive,
        kg_service=kg,
        webhook_service=webhook,
        obs_service=obs,
        access_service=access,
        semantic_service=semantic,
        lifecycle_service=lifecycle,
        event_bus=event_bus,
    )


class TestDocumentIntelligenceOrchestrator:
    @pytest.mark.asyncio
    async def test_classify_text(self, orchestrator):
        result = await orchestrator.classify_text("Hemoglobin 14.2 g/dL")
        assert result.category == DocumentCategory.laboratory_report

    @pytest.mark.asyncio
    async def test_government_record_lifecycle(self, orchestrator):
        gov = GovernmentDocument(
            reference_number="MOH-001",
            issuing_authority="Ministry of Health",
        )
        result = await orchestrator.register_government_document(gov)
        assert result is not None

    @pytest.mark.asyncio
    async def test_assign_reviewer(self, orchestrator):
        review = await orchestrator.assign_reviewer(uuid4(), "user1")
        assert review.reviewer_id == "user1"

    @pytest.mark.asyncio
    async def test_create_policy(self, orchestrator):
        policy = GovernancePolicy(
            name="Test Policy",
            domain=GovernanceDomain.data_retention,
        )
        result = await orchestrator.create_policy(policy)
        assert result is not None

    @pytest.mark.asyncio
    async def test_preserve_document(self, orchestrator):
        record = await orchestrator.preserve_document(uuid4())
        assert record is not None

    @pytest.mark.asyncio
    async def test_knowledge_graph(self, orchestrator):
        related = await orchestrator.find_related_documents(uuid4())
        assert related == []

    @pytest.mark.asyncio
    async def test_check_access(self, orchestrator):
        result = await orchestrator.check_access(uuid4(), "user1")
        assert result is True

    @pytest.mark.asyncio
    async def test_semantic_search(self, orchestrator):
        query = SemanticQuery(query_text="diabetes")
        results = await orchestrator.semantic_search(query)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_register_webhook(self, orchestrator):
        result = await orchestrator.register_webhook("http://example.com/hook", [EventChannel.document_ingested])
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_lifecycle(self, orchestrator):
        result = await orchestrator.get_lifecycle(uuid4())
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_pipeline_health(self, orchestrator):
        result = await orchestrator.get_pipeline_health()
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════
# GOVERNMENT RECORDS SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestGovernmentRecordsService:
    @pytest.fixture
    def service(self):
        return InfrastructureGovernmentRecordsService(MockRepo(), MockRepo())

    @pytest.mark.asyncio
    async def test_register(self, service):
        gov = GovernmentDocument(issuing_authority="MOH")
        result = await service.register_government_document(uuid4(), gov)
        assert result.reference_number is not None

    @pytest.mark.asyncio
    async def test_generate_reference_number(self, service):
        ref = await service.generate_reference_number("Ministry of Health", "GOV")
        assert ref.startswith("MOH")


# ═══════════════════════════════════════════════════════════════════
# COLLABORATION SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestCollaborationService:
    @pytest.fixture
    def service(self):
        return InfrastructureCollaborationService(MockRepo(), MockRepo())

    @pytest.mark.asyncio
    async def test_create_session(self, service):
        session = await service.create_session(uuid4())
        assert isinstance(session, CollaborationSession)

    @pytest.mark.asyncio
    async def test_submit_review(self, service):
        review = DocumentReview(reviewer_id="user1")
        saved = await service.assign_reviewer(uuid4(), "user1")
        result = await service.submit_review(saved.id, ReviewDecision.approved, "Looks good")
        assert result.decision == ReviewDecision.approved


# ═══════════════════════════════════════════════════════════════════
# GOVERNANCE SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestGovernanceService:
    @pytest.fixture
    def service(self):
        return InfrastructureGovernanceService(MockRepo(), MockRepo(), MockRepo())

    @pytest.mark.asyncio
    async def test_evaluate_document(self, service):
        events = await service.evaluate_document(uuid4())
        assert isinstance(events, list)


# ═══════════════════════════════════════════════════════════════════
# NATIONAL ARCHIVE SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestNationalArchiveService:
    @pytest.fixture
    def service(self):
        return InfrastructureNationalArchiveService(MockRepo(), MockRepo(), MockRepo())

    @pytest.mark.asyncio
    async def test_preserve(self, service):
        record = await service.archive_document(uuid4())
        assert isinstance(record, DigitalPreservationRecord)

    @pytest.mark.asyncio
    async def test_check_integrity(self, service):
        # Will raise error because no document exists
        with pytest.raises(DocumentIntelligenceError):
            await service.check_integrity(uuid4())


# ═══════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestKnowledgeGraphService:
    @pytest.fixture
    def service(self):
        return InfrastructureKnowledgeGraphService(MockRepo())

    @pytest.mark.asyncio
    async def test_find_related(self, service):
        result = await service.find_related_documents(uuid4())
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════
# WEBHOOK SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestWebhookService:
    @pytest.fixture
    def service(self):
        return InfrastructureWebhookService(MockRepo(), MockRepo())

    @pytest.mark.asyncio
    async def test_register(self, service):
        result = await service.register_webhook(
            "http://example.com/hook",
            [EventChannel.document_ingested],
        )
        assert "id" in result


# ═══════════════════════════════════════════════════════════════════
# OBSERVABILITY SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestObservabilityService:
    @pytest.fixture
    def service(self):
        return InfrastructureObservabilityService(MockRepo())

    @pytest.mark.asyncio
    async def test_get_pipeline_health(self, service):
        result = await service.get_pipeline_health()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, service):
        result = await service.get_dashboard_data()
        assert "pipelines" in result


# ═══════════════════════════════════════════════════════════════════
# ACCESS CONTROL SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAccessControlService:
    @pytest.fixture
    def service(self):
        return InfrastructureAccessControlService(MockRepo())

    @pytest.mark.asyncio
    async def test_check_access(self, service):
        result = await service.check_access(uuid4(), "user1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delegate_access(self, service):
        await service.delegate_access(uuid4(), "user1", "user2")
        # Should not raise


# ═══════════════════════════════════════════════════════════════════
# EVENT BUS SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEventBusService:
    @pytest.fixture
    def service(self):
        return InfrastructureEventBusService(MockRepo())

    @pytest.mark.asyncio
    async def test_publish_subscribe(self, service):
        received = []
        async def handler(event):
            received.append(event)
        await service.subscribe(EventChannel.document_ingested, handler)
        event = DocumentEvent(document_id=uuid4(), channel=EventChannel.document_ingested, actor_id="system")
        await service.publish(event)
        assert len(received) == 1


# ═══════════════════════════════════════════════════════════════════
# VERSIONING & LIFECYCLE MANAGER TESTS
# ═══════════════════════════════════════════════════════════════════

class TestInfrastructureDocumentLifecycleManager:
    @pytest.fixture
    def manager(self):
        return InfrastructureDocumentLifecycleManager(MockRepo(), MockRepo(), MockRepo(), MockRepo())

    @pytest.mark.asyncio
    async def test_apply_retention(self, manager):
        await manager.apply_retention_policy(uuid4())

    @pytest.mark.asyncio
    async def test_archive(self, manager):
        await manager.archive_document(uuid4())
