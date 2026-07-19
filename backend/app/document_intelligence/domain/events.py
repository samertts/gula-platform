from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from .enums import DocumentCategory, OcrEngine, ProcessingPhase


@dataclass
class DocumentIntelligenceEvent:
    document_id: UUID
    tenant_id: UUID | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentIngested(DocumentIntelligenceEvent):
    filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    page_count: int = 0
    source: str = ""
    storage_path: str = ""
    checksum: str = ""


@dataclass
class DocumentOcrCompleted(DocumentIntelligenceEvent):
    ocr_engine: OcrEngine = OcrEngine.tesseract
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    page_count: int = 0
    text_length: int = 0


@dataclass
class DocumentOcrFailed(DocumentIntelligenceEvent):
    ocr_engine: OcrEngine = OcrEngine.tesseract
    error_message: str = ""
    processing_time_ms: float = 0.0
    retry_count: int = 0


@dataclass
class DocumentClassified(DocumentIntelligenceEvent):
    category: DocumentCategory = DocumentCategory.unknown
    confidence: float = 0.0
    method: str = ""


@dataclass
class DocumentClassificationFailed(DocumentIntelligenceEvent):
    error_message: str = ""
    method: str = ""


@dataclass
class DocumentProcessed(DocumentIntelligenceEvent):
    phases_completed: list[ProcessingPhase] = field(default_factory=list)
    total_processing_time_ms: float = 0.0
    entity_count: int = 0
    fhir_resource_count: int = 0


@dataclass
class DocumentProcessingFailed(DocumentIntelligenceEvent):
    phase: ProcessingPhase = ProcessingPhase.ingestion
    error_message: str = ""
    processing_time_ms: float = 0.0
