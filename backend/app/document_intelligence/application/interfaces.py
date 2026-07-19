from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator
from uuid import UUID

from ..domain.entities import (
    ClassificationResult,
    DocumentPage,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    OcrResult,
    ScannedDocument,
)
from ..domain.enums import (
    DocumentCategory,
    EntityType,
    OcrEngine,
    OcrEngineStatus,
    OcrLanguage,
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
    async def detect_signatures(self, image_data: bytes) -> list[dict[str, Any]]:
        ...
