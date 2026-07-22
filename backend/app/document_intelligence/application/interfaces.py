from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ..domain.entities import (
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
    ScannedDocument,
    SemanticQuery,
    SemanticSearchResult,
)
from ..domain.enums import (
    CollaborationRole,
    DigitalPreservationStandard,
    DocumentCategory,
    EntityType,
    EventChannel,
    GovernanceDomain,
    GovernanceRuleSeverity,
    OcrEngine,
    OcrEngineStatus,
    OcrLanguage,
    RetentionPolicy,
    ReviewDecision,
)


class OcrProvider(ABC):
    @property
    @abstractmethod
    def engine_type(self) -> OcrEngine:
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        ...

    @abstractmethod
    async def initialize(self) -> None:
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        ...

    @abstractmethod
    async def check_health(self) -> OcrEngineStatus:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    async def get_supported_languages(self) -> list[OcrLanguage]:
        ...

    @abstractmethod
    async def ocr_image(
        self, image_data: bytes, language: OcrLanguage = OcrLanguage.arabic_english
    ) -> DocumentPage:
        ...

    @abstractmethod
    async def ocr_image_path(
        self, image_path: Path, language: OcrLanguage = OcrLanguage.arabic_english
    ) -> DocumentPage:
        ...

    @abstractmethod
    async def ocr_batch(
        self, images: list[bytes | Path], language: OcrLanguage = OcrLanguage.arabic_english
    ) -> list[DocumentPage]:
        ...

    @abstractmethod
    async def get_benchmark_score(self) -> dict[str, float]:
        ...

    @property
    @abstractmethod
    def requires_gpu(self) -> bool:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...


class ImagePreprocessor(ABC):
    @abstractmethod
    async def deskew(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def denoise(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def correct_rotation(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def enhance_quality(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def crop(self, image_data: bytes, box: tuple[int, int, int, int]) -> bytes:
        ...

    @abstractmethod
    async def to_grayscale(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def resize(self, image_data: bytes, max_width: int = 2048) -> bytes:
        ...

    @abstractmethod
    async def binarize(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def remove_borders(self, image_data: bytes) -> bytes:
        ...

    @abstractmethod
    async def auto_preprocess(self, image_data: bytes) -> bytes:
        ...


class DocumentParser(ABC):
    @abstractmethod
    async def parse_pdf(self, data: bytes) -> list[bytes]:
        ...

    @abstractmethod
    async def parse_image(self, data: bytes) -> bytes:
        ...

    @abstractmethod
    async def parse_docx(self, data: bytes) -> str:
        ...

    @abstractmethod
    async def parse_tiff(self, data: bytes) -> list[bytes]:
        ...

    @abstractmethod
    async def get_page_count(self, data: bytes, mime_type: str) -> int:
        ...

    @abstractmethod
    async def extract_metadata(self, data: bytes, mime_type: str) -> dict[str, Any]:
        ...


class DocumentClassifier(ABC):
    @abstractmethod
    async def classify(
        self, text: str, pages: list[DocumentPage] | None = None
    ) -> ClassificationResult:
        ...

    @abstractmethod
    async def classify_batch(
        self, documents: list[tuple[str, list[DocumentPage] | None]]
    ) -> list[ClassificationResult]:
        ...

    @abstractmethod
    async def get_custom_classes(self) -> list[str]:
        ...

    @abstractmethod
    async def add_custom_class(self, name: str, examples: list[str]) -> None:
        ...


class EntityExtractor(ABC):
    @abstractmethod
    async def extract(
        self, text: str, category: DocumentCategory | None = None
    ) -> tuple[list[ExtractedEntity], list[ExtractedField], list[ExtractedTable]]:
        ...

    @abstractmethod
    async def extract_from_pages(
        self, pages: list[DocumentPage], category: DocumentCategory | None = None
    ) -> tuple[list[ExtractedEntity], list[ExtractedField], list[ExtractedTable]]:
        ...

    @abstractmethod
    async def extract_entities_of_type(
        self, text: str, entity_types: list[EntityType]
    ) -> list[ExtractedEntity]:
        ...


class FhirMapper(ABC):
    @abstractmethod
    async def to_document_reference(
        self, document: ScannedDocument, ocr_result: OcrResult
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def to_patient(self, entities: list[ExtractedEntity]) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def to_practitioner(self, entities: list[ExtractedEntity]) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def to_organization(self, entities: list[ExtractedEntity]) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def to_observation(
        self, entities: list[ExtractedEntity], fields: list[ExtractedField]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def to_diagnostic_report(
        self, entities: list[ExtractedEntity], fields: list[ExtractedField]
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def to_medication_request(
        self, entities: list[ExtractedEntity]
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def to_encounter(self, entities: list[ExtractedEntity]) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def to_condition(self, entities: list[ExtractedEntity]) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def to_procedure(self, entities: list[ExtractedEntity]) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def to_specimen(self, entities: list[ExtractedEntity]) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def map_all(
        self,
        entities: list[ExtractedEntity],
        fields: list[ExtractedField],
        document: ScannedDocument | None = None,
        ocr_result: OcrResult | None = None,
    ) -> dict[str, Any]:
        ...


class KnowledgeExtractor(ABC):
    @abstractmethod
    async def extract_concepts(
        self, text: str, entities: list[ExtractedEntity]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def build_knowledge_graph(
        self, concepts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def generate_embeddings(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def build_semantic_index(
        self, text: str, document_id: UUID
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def extract_clinical_timeline(
        self, entities: list[ExtractedEntity]
    ) -> list[dict[str, Any]]:
        ...


class SearchIndexer(ABC):
    @abstractmethod
    async def index_document(
        self, document: ScannedDocument, text: str, entities: list[ExtractedEntity]
    ) -> str:
        ...

    @abstractmethod
    async def search(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def hybrid_search(
        self, query: str, query_vector: list[float] | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def semantic_search(
        self, query: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def delete_index(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def rebuild_index(self) -> None:
        ...


class MedicalParser(ABC):
    @abstractmethod
    async def parse_lab_report(self, text: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def parse_radiology_report(self, text: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def parse_prescription(self, text: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def parse_referral(self, text: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def normalize_medication(self, medication_name: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def normalize_test_name(self, test_name: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def map_to_loinc(self, test_name: str) -> str:
        ...

    @abstractmethod
    async def map_to_snomed(self, concept: str) -> str:
        ...

    @abstractmethod
    async def map_to_icd(self, diagnosis: str) -> str:
        ...


class AuditService(ABC):
    @abstractmethod
    async def log_event(
        self, event_type: str, document_id: UUID, details: dict[str, Any]
    ) -> None:
        ...

    @abstractmethod
    async def get_document_history(
        self, document_id: UUID
    ) -> list[dict[str, Any]]:
        ...


class VersioningService(ABC):
    @abstractmethod
    async def create_version(self, document_id: UUID, data: bytes) -> int:
        ...

    @abstractmethod
    async def get_version(self, document_id: UUID, version: int) -> bytes | None:
        ...

    @abstractmethod
    async def list_versions(self, document_id: UUID) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def restore_version(self, document_id: UUID, version: int) -> ScannedDocument:
        ...


class EncryptionService(ABC):
    @abstractmethod
    async def encrypt(self, data: bytes, key_id: str = "default") -> bytes:
        ...

    @abstractmethod
    async def decrypt(self, data: bytes, key_id: str = "default") -> bytes:
        ...

    @abstractmethod
    async def hash_document(self, data: bytes) -> str:
        ...

    @abstractmethod
    async def verify_hash(self, data: bytes, expected_hash: str) -> bool:
        ...

    @abstractmethod
    async def generate_watermark(
        self, document_id: UUID, tenant_id: UUID
    ) -> bytes:
        ...

    @abstractmethod
    async def verify_digital_signature(
        self, data: bytes, signature: bytes, certificate: bytes | None = None
    ) -> bool:
        ...


class AiIntegrationService(ABC):
    @abstractmethod
    async def summarize(self, text: str, max_length: int = 500) -> str:
        ...

    @abstractmethod
    async def translate(self, text: str, target_language: str = "en") -> str:
        ...

    @abstractmethod
    async def answer_question(self, context: str, question: str) -> str:
        ...

    @abstractmethod
    async def detect_risks(self, text: str, entities: list[ExtractedEntity]) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def find_duplicates(
        self, text: str, document_id: UUID
    ) -> list[tuple[UUID, float]]:
        ...

    @abstractmethod
    async def generate_medical_insights(
        self, entities: list[ExtractedEntity], fields: list[ExtractedField]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def rag_query(
        self, query: str, document_ids: list[UUID] | None = None
    ) -> str:
        ...


class ProviderBenchmark(ABC):
    @abstractmethod
    async def benchmark_provider(self, provider: OcrProvider) -> dict[str, float]:
        ...

    @abstractmethod
    async def benchmark_all_providers(self) -> dict[OcrEngine, dict[str, float]]:
        ...

    @abstractmethod
    async def get_best_provider(self, language: OcrLanguage) -> OcrEngine:
        ...

    @abstractmethod
    async def record_result(
        self, engine: OcrEngine, metrics: dict[str, float]
    ) -> None:
        ...


class DocumentLifecycleManager(ABC):
    @abstractmethod
    async def apply_retention_policy(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def archive_document(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def restore_document(self, document_id: UUID) -> ScannedDocument:
        ...

    @abstractmethod
    async def apply_legal_hold(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def release_legal_hold(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def deduplicate(self, document_id: UUID) -> list[UUID]:
        ...

    @abstractmethod
    async def compress(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def schedule_deletion(self, document_id: UUID, days: int) -> None:
        ...


class PipelineEventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: Any) -> None:
        ...

    @abstractmethod
    async def subscribe(self, event_type: type, handler: Any) -> None:
        ...


class DocumentIngestionService(ABC):
    @abstractmethod
    async def ingest(
        self, data: bytes, filename: str, mime_type: str, metadata: dict[str, Any] | None = None
    ) -> ScannedDocument:
        ...

    @abstractmethod
    async def ingest_batch(
        self, files: list[tuple[bytes, str, str]]
    ) -> list[ScannedDocument]:
        ...

    @abstractmethod
    async def ingest_from_uri(self, uri: str, metadata: dict[str, Any] | None = None) -> ScannedDocument:
        ...

    @abstractmethod
    async def ingest_from_fhir(
        self, document_reference: dict[str, Any]
    ) -> ScannedDocument:
        ...


class OcrPipelineService(ABC):
    @abstractmethod
    async def process_document(
        self,
        document: ScannedDocument,
        provider: OcrEngine | None = None,
        language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> OcrResult:
        ...

    @abstractmethod
    async def process_batch(
        self,
        documents: list[ScannedDocument],
        provider: OcrEngine | None = None,
    ) -> list[OcrResult]:
        ...

    @abstractmethod
    async def process_stream(
        self,
        document: ScannedDocument,
        provider: OcrEngine | None = None,
    ) -> AsyncIterator[DocumentPage]:
        ...


class DocumentClassifierService(ABC):
    @abstractmethod
    async def classify_document(
        self, document: ScannedDocument, ocr_result: OcrResult
    ) -> ClassificationResult:
        ...

    @abstractmethod
    async def classify_text(self, text: str) -> ClassificationResult:
        ...


class EntityExtractionService(ABC):
    @abstractmethod
    async def extract_from_document(
        self, document: ScannedDocument, ocr_result: OcrResult
    ) -> tuple[list[ExtractedEntity], list[ExtractedField], list[ExtractedTable]]:
        ...

    @abstractmethod
    async def extract_from_text(
        self, text: str, category: DocumentCategory | None = None
    ) -> tuple[list[ExtractedEntity], list[ExtractedField], list[ExtractedTable]]:
        ...


class FhirMappingService(ABC):
    @abstractmethod
    async def map_document(
        self,
        document: ScannedDocument,
        ocr_result: OcrResult,
        entities: list[ExtractedEntity],
        fields: list[ExtractedField],
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def map_to_bundle(self, resources: list[dict[str, Any]]) -> dict[str, Any]:
        ...


class KnowledgePipelineService(ABC):
    @abstractmethod
    async def process(
        self,
        document: ScannedDocument,
        ocr_result: OcrResult,
        entities: list[ExtractedEntity],
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def query_knowledge_graph(self, query: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_patient_timeline(self, patient_id: UUID) -> list[dict[str, Any]]:
        ...


class SearchService(ABC):
    @abstractmethod
    async def index_document(
        self, document: ScannedDocument, text: str, entities: list[ExtractedEntity]
    ) -> None:
        ...

    @abstractmethod
    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
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
        ...


class RemediationService(ABC):
    @abstractmethod
    async def detect_and_fix_ocr_failures(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_and_fix_classification_failures(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_and_fix_extraction_failures(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_and_fix_fhir_mapping_failures(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_and_fix_indexing_failures(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def auto_remediate(self) -> dict[str, Any]:
        ...


class LayoutDetector(ABC):
    @abstractmethod
    async def detect_layout(self, image_data: bytes) -> dict[str, Any]:
        ...

    @abstractmethod
    async def detect_tables(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_forms(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_handwriting(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_qr_codes(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_barcodes(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_stamps(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_logos(self, image_data: bytes) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_handwritten_text(self, image_data: bytes) -> list[dict[str, Any]]:
        ...


class GovernmentRecordsService(ABC):
    @abstractmethod
    async def register_government_document(
        self, document_id: UUID, gov_record: GovernmentDocument
    ) -> GovernmentDocument:
        ...

    @abstractmethod
    async def get_government_document(self, document_id: UUID) -> GovernmentDocument | None:
        ...

    @abstractmethod
    async def search_government_documents(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[GovernmentDocument]:
        ...

    @abstractmethod
    async def track_order_lifecycle(self, document_id: UUID) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def validate_government_format(self, document: GovernmentDocument) -> dict[str, Any]:
        ...

    @abstractmethod
    async def generate_reference_number(self, authority: str, category: str) -> str:
        ...


class CollaborationService(ABC):
    @abstractmethod
    async def assign_reviewer(
        self, document_id: UUID, reviewer_id: str, role: CollaborationRole = CollaborationRole.reviewer
    ) -> DocumentReview:
        ...

    @abstractmethod
    async def submit_review(
        self, review_id: UUID, decision: ReviewDecision, comments: str, changes: list[str] | None = None
    ) -> DocumentReview:
        ...

    @abstractmethod
    async def get_reviews(self, document_id: UUID) -> list[DocumentReview]:
        ...

    @abstractmethod
    async def add_annotation(
        self, document_id: UUID, annotation: DocumentAnnotation
    ) -> DocumentAnnotation:
        ...

    @abstractmethod
    async def get_annotations(self, document_id: UUID) -> list[DocumentAnnotation]:
        ...

    @abstractmethod
    async def resolve_annotation(self, annotation_id: UUID) -> DocumentAnnotation:
        ...

    @abstractmethod
    async def create_session(self, document_id: UUID) -> CollaborationSession:
        ...

    @abstractmethod
    async def join_session(self, session_id: UUID, user_id: str) -> CollaborationSession:
        ...

    @abstractmethod
    async def get_session(self, session_id: UUID) -> CollaborationSession | None:
        ...


class GovernanceService(ABC):
    @abstractmethod
    async def create_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        ...

    @abstractmethod
    async def update_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        ...

    @abstractmethod
    async def delete_policy(self, policy_id: UUID) -> None:
        ...

    @abstractmethod
    async def get_policy(self, policy_id: UUID) -> GovernancePolicy | None:
        ...

    @abstractmethod
    async def list_policies(self, domain: GovernanceDomain | None = None) -> list[GovernancePolicy]:
        ...

    @abstractmethod
    async def evaluate_document(self, document_id: UUID) -> list[GovernanceEvent]:
        ...

    @abstractmethod
    async def evaluate_all(self) -> list[GovernanceEvent]:
        ...

    @abstractmethod
    async def get_governance_events(
        self, document_id: UUID | None = None, severity: GovernanceRuleSeverity | None = None
    ) -> list[GovernanceEvent]:
        ...

    @abstractmethod
    async def apply_policy_action(self, event: GovernanceEvent) -> None:
        ...


class NationalArchiveService(ABC):
    @abstractmethod
    async def archive_document(
        self, document_id: UUID, policy: RetentionPolicy = RetentionPolicy.standard_7y
    ) -> DigitalPreservationRecord:
        ...

    @abstractmethod
    async def preserve_document(
        self, document_id: UUID, standard: DigitalPreservationStandard = DigitalPreservationStandard.oais
    ) -> DigitalPreservationRecord:
        ...

    @abstractmethod
    async def check_integrity(self, record_id: UUID) -> dict[str, Any]:
        ...

    @abstractmethod
    async def restore_from_archive(self, document_id: UUID) -> ScannedDocument:
        ...

    @abstractmethod
    async def get_preservation_record(self, document_id: UUID) -> DigitalPreservationRecord | None:
        ...

    @abstractmethod
    async def schedule_integrity_checks(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def apply_retention(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def purge_expired(self) -> list[UUID]:
        ...


class KnowledgeGraphService(ABC):
    @abstractmethod
    async def add_edge(self, edge: KnowledgeGraphEdge) -> KnowledgeGraphEdge:
        ...

    @abstractmethod
    async def find_related_documents(
        self, document_id: UUID, max_depth: int = 3
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def discover_relations(self, document_id: UUID) -> list[KnowledgeGraphEdge]:
        ...

    @abstractmethod
    async def get_entity_network(self, entity_name: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_document_subgraph(self, document_id: UUID) -> dict[str, Any]:
        ...

    @abstractmethod
    async def query_graph(self, query: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def rebuild_graph(self) -> None:
        ...


class SemanticSearchService(ABC):
    @abstractmethod
    async def search(self, query: SemanticQuery) -> list[SemanticSearchResult]:
        ...

    @abstractmethod
    async def hybrid_search(
        self, query_text: str, query_vector: list[float] | None = None
    ) -> list[SemanticSearchResult]:
        ...

    @abstractmethod
    async def arabic_search(self, query: str) -> list[SemanticSearchResult]:
        ...

    @abstractmethod
    async def natural_language_query(self, query: str) -> list[SemanticSearchResult]:
        ...

    @abstractmethod
    async def similar_documents(self, document_id: UUID, limit: int = 10) -> list[SemanticSearchResult]:
        ...

    @abstractmethod
    async def search_by_entity(self, entity_type: EntityType, value: str) -> list[SemanticSearchResult]:
        ...

    @abstractmethod
    async def suggest_queries(self, partial: str) -> list[str]:
        ...


class WebhookService(ABC):
    @abstractmethod
    async def register_webhook(
        self, url: str, events: list[EventChannel], secret: str | None = None
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def unregister_webhook(self, webhook_id: UUID) -> None:
        ...

    @abstractmethod
    async def dispatch_event(self, event: DocumentEvent) -> None:
        ...

    @abstractmethod
    async def get_webhook_log(self, webhook_id: UUID) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def retry_failed(self, webhook_id: UUID) -> None:
        ...


class EventBusService(ABC):
    @abstractmethod
    async def publish(self, event: DocumentEvent) -> None:
        ...

    @abstractmethod
    async def subscribe(self, channel: EventChannel, handler: Any) -> None:
        ...

    @abstractmethod
    async def unsubscribe(self, channel: EventChannel, handler: Any) -> None:
        ...

    @abstractmethod
    async def get_event_history(
        self, document_id: UUID | None = None, channel: EventChannel | None = None
    ) -> list[DocumentEvent]:
        ...


class ObservabilityService(ABC):
    @abstractmethod
    async def get_pipeline_health(self) -> list[PipelineHealth]:
        ...

    @abstractmethod
    async def record_pipeline_metrics(self, health: PipelineHealth) -> None:
        ...

    @abstractmethod
    async def get_ocr_statistics(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_throughput_metrics(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_processing_times(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_error_rates(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_document_statistics(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_knowledge_graph_statistics(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_governance_summary(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_dashboard_data(self) -> dict[str, Any]:
        ...


class DocumentLifecycleService(ABC):
    @abstractmethod
    async def get_lifecycle(self, document_id: UUID) -> list[DocumentLifecycleRecord]:
        ...

    @abstractmethod
    async def record_event(
        self, document_id: UUID, event_type: str, actor: str, reason: str = "",
        metadata: dict[str, Any] | None = None
    ) -> DocumentLifecycleRecord:
        ...

    @abstractmethod
    async def get_active_documents(self) -> list[DocumentLifecycleRecord]:
        ...

    @abstractmethod
    async def get_expiring_documents(self, days: int = 30) -> list[DocumentLifecycleRecord]:
        ...


class AccessControlService(ABC):
    @abstractmethod
    async def check_access(
        self, document_id: UUID, user_id: str, permission: str
    ) -> bool:
        ...

    @abstractmethod
    async def grant_access(
        self, document_id: UUID, user_id: str, role: CollaborationRole
    ) -> None:
        ...

    @abstractmethod
    async def revoke_access(
        self, document_id: UUID, user_id: str
    ) -> None:
        ...

    @abstractmethod
    async def get_access_list(self, document_id: UUID) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_documents_for_user(
        self, user_id: str, permission: str = "viewer"
    ) -> list[UUID]:
        ...

    @abstractmethod
    async def delegate_access(
        self, document_id: UUID, from_user: str, to_user: str, expiry: datetime | None = None
    ) -> None:
        ...


class PatientIntelligenceService(ABC):
    @abstractmethod
    async def get_patient_dossier(
        self, patient_id: UUID
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_patient_timeline(
        self, patient_id: UUID
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_patient_diagnoses(
        self, patient_id: UUID
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_patient_medications(
        self, patient_id: UUID
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def detect_health_risks(
        self, patient_id: UUID
    ) -> list[dict[str, Any]]:
        ...


class ClinicalDecisionSupportService(ABC):
    @abstractmethod
    async def evaluate_guidelines(
        self, patient_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def check_drug_interactions(
        self, medications: list[str]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def suggest_diagnoses(
        self, symptoms: list[str], patient_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def alert_critical_values(
        self, lab_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        ...


class RagAiService(ABC):
    @abstractmethod
    async def ask_document(
        self, document_id: UUID, question: str
    ) -> str:
        ...

    @abstractmethod
    async def ask_corpus(
        self, query: str, category_filter: list[DocumentCategory] | None = None
    ) -> str:
        ...

    @abstractmethod
    async def generate_summary(
        self, document_id: UUID, max_length: int = 500
    ) -> str:
        ...

    @abstractmethod
    async def generate_patient_summary(
        self, patient_id: UUID
    ) -> str:
        ...

    @abstractmethod
    async def generate_report(
        self, template: str, data: dict[str, Any]
    ) -> str:
        ...

    @abstractmethod
    async def answer_question(
        self, context: str, question: str, domain: str = "medical"
    ) -> str:
        ...


class FhirApiService(ABC):
    @abstractmethod
    async def search_resource(
        self, resource_type: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_resource(
        self, resource_type: str, resource_id: str
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def create_resource(
        self, resource_type: str, resource: dict[str, Any]
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def update_resource(
        self, resource_type: str, resource_id: str, resource: dict[str, Any]
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def delete_resource(
        self, resource_type: str, resource_id: str
    ) -> None:
        ...

    @abstractmethod
    async def batch_operation(
        self, operations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        ...


class PolicyAssistantService(ABC):
    @abstractmethod
    async def answer_policy_question(self, question: str) -> str:
        ...

    @abstractmethod
    async def summarize_policy(self, policy_id: UUID) -> str:
        ...

    @abstractmethod
    async def check_compliance(self, document_id: UUID, policy_id: UUID) -> dict[str, Any]:
        ...

    @abstractmethod
    async def generate_compliance_report(self, document_id: UUID) -> dict[str, Any]:
        ...


class AutomationService(ABC):
    @abstractmethod
    async def auto_classify(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def auto_extract(self, document_id: UUID) -> None:
        ...

    @abstractmethod
    async def auto_route(self, document_id: UUID) -> str:
        ...

    @abstractmethod
    async def auto_apply_policy(self, document_id: UUID) -> list[GovernanceEvent]:
        ...

    @abstractmethod
    async def auto_remediate(self) -> dict[str, Any]:
        ...


class DocumentPrintService(ABC):
    @abstractmethod
    async def generate_pdf(self, document_id: UUID, template: str = "standard") -> bytes:
        ...

    @abstractmethod
    async def generate_qr_label(self, document_id: UUID) -> bytes:
        ...

    @abstractmethod
    async def print_barcode(self, document_id: UUID) -> bytes:
        ...


class ExportService(ABC):
    @abstractmethod
    async def export_json(self, document_id: UUID, include_ocr: bool = True) -> str:
        ...

    @abstractmethod
    async def export_csv(self, document_ids: list[UUID]) -> str:
        ...

    @abstractmethod
    async def export_fhir_bundle(self, document_id: UUID) -> dict[str, Any]:
        ...

    @abstractmethod
    async def export_pdf(self, document_id: UUID) -> bytes:
        ...


class AuditTrailService(ABC):
    @abstractmethod
    async def get_audit_trail(self, document_id: UUID) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def verify_chain(self, document_id: UUID) -> bool:
        ...

    @abstractmethod
    async def get_audit_summary(self, document_id: UUID) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_user_activity(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        ...


class DistributedProcessingService(ABC):
    @abstractmethod
    async def submit_job(self, document_id: UUID, pipeline: str) -> str:
        ...

    @abstractmethod
    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def cancel_job(self, job_id: str) -> None:
        ...

    @abstractmethod
    async def get_worker_status(self) -> list[dict[str, Any]]:
        ...
