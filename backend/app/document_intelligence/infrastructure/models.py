from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

from ..domain.entities import (
    ClassificationResult,
    DocumentPage,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    OcrResult,
    ProcessingPipelineResult,
    ScannedDocument,
)
from ..domain.enums import (
    ClassificationConfidence,
    DocumentCategory,
    DocumentStatus,
    EntityType,
    ExtractedFieldType,
    OcrEngine,
    OcrLanguage,
    ProcessingPhase,
    ProcessingPriority,
    StorageBackend,
)

DocIntelBase = declarative_base()


class ScannedDocumentModel(DocIntelBase):
    __tablename__ = "docint_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    lab_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    filename = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)
    source = Column(String(128), nullable=False, default="api")
    source_reference = Column(String(256), nullable=True)
    storage_backend = Column(
        Enum(StorageBackend), nullable=False, default=StorageBackend.encrypted_local
    )
    storage_path = Column(String(1024), nullable=False)
    storage_uri = Column(String(2048), nullable=True)
    checksum_sha256 = Column(String(64), nullable=False)
    status = Column(
        Enum(DocumentStatus), nullable=False, default=DocumentStatus.pending_ingestion
    )
    priority = Column(
        Enum(ProcessingPriority), nullable=False, default=ProcessingPriority.normal
    )
    language = Column(
        Enum(OcrLanguage), nullable=False, default=OcrLanguage.arabic_english
    )
    error_message = Column(Text, nullable=True, default="")
    retry_count = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSON, nullable=True, default=dict)
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    ocr_results = relationship("OcrResultModel", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("ExtractedEntityModel", back_populates="document", cascade="all, delete-orphan")
    fields = relationship("ExtractedFieldModel", back_populates="document", cascade="all, delete-orphan")
    tables = relationship("ExtractedTableModel", back_populates="document", cascade="all, delete-orphan")
    pipeline_result = relationship("PipelineResultModel", back_populates="document", uselist=False, cascade="all, delete-orphan")

    def to_domain(self) -> ScannedDocument:
        return ScannedDocument(
            id=self.id,
            tenant_id=self.tenant_id,
            patient_id=self.patient_id,
            encounter_id=self.encounter_id,
            lab_id=self.lab_id,
            filename=self.filename,
            mime_type=self.mime_type,
            size_bytes=self.size_bytes,
            page_count=self.page_count,
            source=self.source,
            source_reference=self.source_reference or "",
            storage_backend=self.storage_backend,
            storage_path=self.storage_path,
            storage_uri=self.storage_uri or "",
            checksum_sha256=self.checksum_sha256,
            status=self.status,
            priority=self.priority,
            language=self.language,
            error_message=self.error_message or "",
            retry_count=self.retry_count,
            metadata=self.metadata_json or {},
            tags=self.tags or [],
            created_at=self.created_at,
            updated_at=self.updated_at,
            processed_at=self.processed_at,
        )

    @classmethod
    def from_domain(cls, doc: ScannedDocument) -> ScannedDocumentModel:
        return cls(
            id=doc.id,
            tenant_id=doc.tenant_id,
            patient_id=doc.patient_id,
            encounter_id=doc.encounter_id,
            lab_id=doc.lab_id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            size_bytes=doc.size_bytes,
            page_count=doc.page_count,
            source=doc.source,
            source_reference=doc.source_reference,
            storage_backend=doc.storage_backend,
            storage_path=doc.storage_path,
            storage_uri=doc.storage_uri,
            checksum_sha256=doc.checksum_sha256,
            status=doc.status,
            priority=doc.priority,
            language=doc.language,
            error_message=doc.error_message,
            retry_count=doc.retry_count,
            metadata_json=doc.metadata,
            tags=doc.tags,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            processed_at=doc.processed_at,
        )


class OcrResultModel(DocIntelBase):
    __tablename__ = "docint_ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    full_text = Column(Text, nullable=True, default="")
    ocr_engine = Column(Enum(OcrEngine), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    processing_time_ms = Column(Float, nullable=False, default=0.0)
    language = Column(Enum(OcrLanguage), nullable=False, default=OcrLanguage.arabic_english)
    page_count = Column(Integer, nullable=False, default=0)
    success = Column(Integer, nullable=False, default=1)
    error_message = Column(Text, nullable=True, default="")
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel", back_populates="ocr_results")

    def to_domain(self) -> OcrResult:
        return OcrResult(
            document_id=self.document_id,
            full_text=self.full_text or "",
            ocr_engine=self.ocr_engine,
            confidence=self.confidence,
            processing_time_ms=self.processing_time_ms,
            language=self.language,
            page_count=self.page_count,
            success=bool(self.success),
            error_message=self.error_message or "",
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, result: OcrResult) -> OcrResultModel:
        return cls(
            document_id=result.document_id,
            full_text=result.full_text,
            ocr_engine=result.ocr_engine,
            confidence=result.confidence,
            processing_time_ms=result.processing_time_ms,
            language=result.language,
            page_count=result.page_count,
            success=1 if result.success else 0,
            error_message=result.error_message,
            metadata_json=result.metadata,
        )


class ExtractedEntityModel(DocIntelBase):
    __tablename__ = "docint_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    entity_type = Column(Enum(EntityType), nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    normalized_value = Column(Text, nullable=True)
    source_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=False, default=0)
    field_name = Column(String(256), nullable=True)
    loinc_code = Column(String(16), nullable=True)
    snomed_code = Column(String(32), nullable=True)
    icd_code = Column(String(16), nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel", back_populates="entities")

    def to_domain(self) -> ExtractedEntity:
        return ExtractedEntity(
            entity_type=self.entity_type,
            value=self.value,
            confidence=self.confidence,
            normalized_value=self.normalized_value or "",
            source_text=self.source_text or "",
            page_number=self.page_number,
            field_name=self.field_name or "",
            loinc_code=self.loinc_code or "",
            snomed_code=self.snomed_code or "",
            icd_code=self.icd_code or "",
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, entity: ExtractedEntity, document_id: UUID) -> ExtractedEntityModel:
        return cls(
            document_id=document_id,
            entity_type=entity.entity_type,
            value=entity.value,
            confidence=entity.confidence,
            normalized_value=entity.normalized_value,
            source_text=entity.source_text,
            page_number=entity.page_number,
            field_name=entity.field_name,
            loinc_code=entity.loinc_code,
            snomed_code=entity.snomed_code,
            icd_code=entity.icd_code,
            metadata_json=entity.metadata,
        )


class ExtractedFieldModel(DocIntelBase):
    __tablename__ = "docint_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    name = Column(String(256), nullable=False)
    value = Column(Text, nullable=True)
    field_type = Column(Enum(ExtractedFieldType), nullable=False, default=ExtractedFieldType.text)
    confidence = Column(Float, nullable=False, default=0.0)
    page_number = Column(Integer, nullable=False, default=0)
    normalized_value = Column(Text, nullable=True)
    original_text = Column(Text, nullable=True)
    language = Column(String(16), nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel", back_populates="fields")

    def to_domain(self) -> ExtractedField:
        return ExtractedField(
            name=self.name,
            value=self.value or "",
            field_type=self.field_type,
            confidence=self.confidence,
            page_number=self.page_number,
            normalized_value=self.normalized_value or "",
            original_text=self.original_text or "",
            language=self.language or "",
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, field: ExtractedField, document_id: UUID) -> ExtractedFieldModel:
        return cls(
            document_id=document_id,
            name=field.name,
            value=field.value,
            field_type=field.field_type,
            confidence=field.confidence,
            page_number=field.page_number,
            normalized_value=field.normalized_value,
            original_text=field.original_text,
            language=field.language,
            metadata_json=field.metadata,
        )


class ExtractedTableModel(DocIntelBase):
    __tablename__ = "docint_tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    page_number = Column(Integer, nullable=False, default=0)
    headers = Column(JSON, nullable=True, default=list)
    rows = Column(JSON, nullable=True, default=list)
    confidence = Column(Float, nullable=False, default=0.0)
    caption = Column(String(512), nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel", back_populates="tables")

    def to_domain(self) -> ExtractedTable:
        return ExtractedTable(
            page_number=self.page_number,
            headers=self.headers or [],
            rows=self.rows or [],
            confidence=self.confidence,
            caption=self.caption or "",
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, table: ExtractedTable, document_id: UUID) -> ExtractedTableModel:
        return cls(
            document_id=document_id,
            page_number=table.page_number,
            headers=table.headers,
            rows=table.rows,
            confidence=table.confidence,
            caption=table.caption,
            metadata_json=table.metadata,
        )


class ClassificationResultModel(DocIntelBase):
    __tablename__ = "docint_classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    category = Column(Enum(DocumentCategory), nullable=False)
    confidence = Column(Enum(ClassificationConfidence), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    subcategory = Column(String(256), nullable=True)
    alternatives = Column(JSON, nullable=True, default=list)
    method = Column(String(128), nullable=False, default="")
    features = Column(JSON, nullable=True, default=dict)
    processing_time_ms = Column(Float, nullable=False, default=0.0)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> ClassificationResult:
        return ClassificationResult(
            category=self.category,
            confidence=self.confidence,
            confidence_score=self.confidence_score,
            subcategory=self.subcategory or "",
            alternatives=[(DocumentCategory(a[0]), a[1]) for a in (self.alternatives or [])],
            method=self.method,
            features=self.features or {},
            processing_time_ms=self.processing_time_ms,
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, result: ClassificationResult) -> ClassificationResultModel:
        return cls(
            category=result.category,
            confidence=result.confidence,
            confidence_score=result.confidence_score,
            subcategory=result.subcategory,
            alternatives=[(str(c), s) for c, s in result.alternatives],
            method=result.method,
            features=result.features,
            processing_time_ms=result.processing_time_ms,
            metadata_json=result.metadata,
        )


class PipelineResultModel(DocIntelBase):
    __tablename__ = "docint_pipeline_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, unique=True, index=True
    )
    phases_completed = Column(JSON, nullable=True, default=list)
    fhir_resources = Column(JSON, nullable=True, default=list)
    knowledge_graph_entries = Column(JSON, nullable=True, default=list)
    vector_embeddings = Column(JSON, nullable=True, default=list)
    search_index_entries = Column(JSON, nullable=True, default=list)
    total_processing_time_ms = Column(Float, nullable=False, default=0.0)
    success = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True, default="")
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("ScannedDocumentModel", back_populates="pipeline_result")

    def to_domain(self) -> ProcessingPipelineResult:
        phases = [ProcessingPhase(p) for p in (self.phases_completed or []) if p in [e.value for e in ProcessingPhase]]
        return ProcessingPipelineResult(
            document_id=self.document_id,
            phases_completed=phases,
            fhir_resources=self.fhir_resources or [],
            knowledge_graph_entries=self.knowledge_graph_entries or [],
            vector_embeddings=self.vector_embeddings or [],
            search_index_entries=self.search_index_entries or [],
            total_processing_time_ms=self.total_processing_time_ms,
            success=bool(self.success),
            error_message=self.error_message or "",
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, result: ProcessingPipelineResult) -> PipelineResultModel:
        return cls(
            document_id=result.document_id,
            phases_completed=[str(p) for p in result.phases_completed],
            fhir_resources=result.fhir_resources,
            knowledge_graph_entries=result.knowledge_graph_entries,
            vector_embeddings=result.vector_embeddings,
            search_index_entries=result.search_index_entries,
            total_processing_time_ms=result.total_processing_time_ms,
            success=1 if result.success else 0,
            error_message=result.error_message,
            metadata_json=result.metadata,
        )
