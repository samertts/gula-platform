from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from .enums import (
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
    OcrLanguage,
    ProcessingPhase,
    ProcessingPriority,
    ReviewDecision,
    StorageBackend,
)


@dataclass
class ScannedDocument:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID | None = None
    patient_id: UUID | None = None
    encounter_id: UUID | None = None
    lab_id: UUID | None = None
    filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    page_count: int = 0
    source: str = ""
    source_reference: str = ""
    storage_backend: StorageBackend = StorageBackend.encrypted_local
    storage_path: str = ""
    storage_uri: str = ""
    checksum_sha256: str = ""
    status: DocumentStatus = DocumentStatus.pending_ingestion
    priority: ProcessingPriority = ProcessingPriority.normal
    language: OcrLanguage = OcrLanguage.arabic_english
    error_message: str = ""
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None

    def mark_ingested(self, storage_path: str, checksum: str) -> None:
        self.storage_path = storage_path
        self.checksum_sha256 = checksum
        self.status = DocumentStatus.ingested
        self.updated_at = datetime.now(UTC)

    def mark_ocr_completed(self) -> None:
        self.status = DocumentStatus.ocr_completed
        self.updated_at = datetime.now(UTC)

    def mark_ocr_failed(self, error: str) -> None:
        self.status = DocumentStatus.ocr_failed
        self.error_message = error
        self.retry_count += 1
        self.updated_at = datetime.now(UTC)

    def mark_processed(self) -> None:
        self.status = DocumentStatus.knowledge_indexed
        self.processed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    @property
    def extension(self) -> str:
        return self.filename.rsplit(".", 1)[-1].lower() if "." in self.filename else ""

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")

    @property
    def is_pdf(self) -> bool:
        return self.mime_type == "application/pdf"

    @property
    def is_document(self) -> bool:
        return self.mime_type in {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }


@dataclass
class DocumentPage:
    page_number: int = 0
    width: int = 0
    height: int = 0
    dpi: int = 300
    text: str = ""
    confidence: float = 0.0
    ocr_engine: OcrEngine = OcrEngine.tesseract
    processed_image_path: str = ""
    preprocessed: bool = False
    language: OcrLanguage = OcrLanguage.arabic_english
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedField:
    name: str = ""
    value: str = ""
    field_type: ExtractedFieldType = ExtractedFieldType.text
    confidence: float = 0.0
    page_number: int = 0
    bounding_box: tuple[float, float, float, float] | None = None
    normalized_value: str = ""
    original_text: str = ""
    language: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedEntity:
    entity_type: EntityType = EntityType.custom
    value: str = ""
    confidence: float = 0.0
    normalized_value: str = ""
    source_text: str = ""
    page_number: int = 0
    field_name: str = ""
    loinc_code: str = ""
    snomed_code: str = ""
    icd_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedTable:
    page_number: int = 0
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    confidence: float = 0.0
    bounding_box: tuple[float, float, float, float] | None = None
    caption: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OcrResult:
    document_id: UUID | None = None
    pages: list[DocumentPage] = field(default_factory=list)
    full_text: str = ""
    ocr_engine: OcrEngine = OcrEngine.tesseract
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    language: OcrLanguage = OcrLanguage.arabic_english
    page_count: int = 0
    success: bool = False
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    category: DocumentCategory = DocumentCategory.unknown
    confidence: ClassificationConfidence = ClassificationConfidence.low
    confidence_score: float = 0.0
    subcategory: str = ""
    alternatives: list[tuple[DocumentCategory, float]] = field(default_factory=list)
    method: str = ""
    features: dict[str, float] = field(default_factory=dict)
    ocr_engine: OcrEngine = OcrEngine.tesseract
    page_count: int = 0
    processing_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingPipelineResult:
    document_id: UUID | None = None
    phases_completed: list[ProcessingPhase] = field(default_factory=list)
    ocr_result: OcrResult | None = None
    classification: ClassificationResult | None = None
    entities: list[ExtractedEntity] = field(default_factory=list)
    fields: list[ExtractedField] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    fhir_resources: list[dict[str, Any]] = field(default_factory=list)
    knowledge_graph_entries: list[dict[str, Any]] = field(default_factory=list)
    vector_embeddings: list[float] = field(default_factory=list)
    search_index_entries: list[dict[str, Any]] = field(default_factory=list)
    total_processing_time_ms: float = 0.0
    success: bool = False
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentIntelligenceResult:
    document: ScannedDocument | None = None
    pipeline: ProcessingPipelineResult | None = None
    ocr_text: str = ""
    classification: DocumentCategory | None = None
    entities: list[ExtractedEntity] = field(default_factory=list)
    fields: list[ExtractedField] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    fhir: dict[str, Any] = field(default_factory=dict)
    knowledge_graph: dict[str, Any] = field(default_factory=dict)
    embeddings: list[float] = field(default_factory=list)
    search_entries: list[dict[str, Any]] = field(default_factory=list)
    processing_summary: dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error: str = ""


@dataclass
class GovernmentDocument:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    reference_number: str = ""
    issuing_authority: str = ""
    recipient_authority: str = ""
    subject: str = ""
    classification: ConfidentialityLevel = ConfidentialityLevel.internal
    decision_number: str = ""
    committee_name: str = ""
    contract_number: str = ""
    procurement_number: str = ""
    legal_basis: str = ""
    signatory_name: str = ""
    signatory_title: str = ""
    effective_date: datetime | None = None
    expiry_date: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentReview:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    reviewer_id: str = ""
    reviewer_name: str = ""
    role: CollaborationRole = CollaborationRole.reviewer
    decision: ReviewDecision | None = None
    comments: str = ""
    suggested_changes: list[str] = field(default_factory=list)
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentAnnotation:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    page_number: int = 0
    author_id: str = ""
    author_name: str = ""
    content: str = ""
    annotation_type: str = "comment"
    bounding_box: tuple[float, float, float, float] | None = None
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DigitalPreservationRecord:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    standard: DigitalPreservationStandard = DigitalPreservationStandard.oais
    preservation_level: str = "full"
    original_format: str = ""
    preservation_format: str = ""
    original_checksum: str = ""
    preservation_checksum: str = ""
    checksum_method: IntegrityCheckMethod = IntegrityCheckMethod.sha256
    preservation_location: str = ""
    cold_storage_location: str = ""
    integrity_log: list[dict[str, Any]] = field(default_factory=list)
    preservation_date: datetime = field(default_factory=datetime.utcnow)
    next_integrity_check: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraphEdge:
    source_document_id: UUID | None = None
    target_document_id: UUID | None = None
    source_entity: str = ""
    target_entity: str = ""
    relation: KnowledgeGraphRelation = KnowledgeGraphRelation.associated_with
    confidence: float = 0.0
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticQuery:
    query_text: str = ""
    query_vector: list[float] = field(default_factory=list)
    category_filter: list[DocumentCategory] = field(default_factory=list)
    entity_filter: dict[str, str] = field(default_factory=dict)
    date_range: tuple[datetime | None, datetime | None] = (None, None)
    confidentiality_filter: list[ConfidentialityLevel] = field(default_factory=list)
    limit: int = 20
    offset: int = 0
    hybrid_search: bool = True
    arabic_boost: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticSearchResult:
    document_id: UUID | None = None
    score: float = 0.0
    text_snippet: str = ""
    category: DocumentCategory | None = None
    entities: list[ExtractedEntity] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernancePolicy:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    domain: GovernanceDomain = GovernanceDomain.document_classification
    severity: GovernanceRuleSeverity = GovernanceRuleSeverity.warning
    action: GovernancePolicyAction = GovernancePolicyAction.flag
    conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GovernanceEvent:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    policy_id: UUID | None = None
    domain: GovernanceDomain = GovernanceDomain.document_classification
    severity: GovernanceRuleSeverity = GovernanceRuleSeverity.info
    message: str = ""
    action_taken: GovernancePolicyAction = GovernancePolicyAction.notify
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DocumentEvent:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    channel: EventChannel = EventChannel.document_ingested
    actor_id: str = ""
    actor_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineHealth:
    pipeline_name: str = ""
    phase: str = ""
    status: str = "healthy"
    documents_processed: int = 0
    documents_failed: int = 0
    avg_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    error_rate: float = 0.0
    throughput_per_minute: float = 0.0
    last_error: str = ""
    last_error_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentLifecycleRecord:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    event_type: str = ""
    previous_status: DocumentStatus | None = None
    new_status: DocumentStatus | None = None
    actor: str = ""
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    id: UUID = field(default_factory=uuid4)
    document_id: UUID | None = None
    participants: list[dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
