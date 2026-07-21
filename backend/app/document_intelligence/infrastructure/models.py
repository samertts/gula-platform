from __future__ import annotations

from datetime import datetime
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
    DigitalPreservationRecord,
    DocumentAnnotation,
    DocumentEvent,
    DocumentLifecycleRecord,
    DocumentReview,
    GovernmentDocument,
    GovernanceEvent,
    GovernancePolicy,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    KnowledgeGraphEdge,
    OcrResult,
    PipelineHealth,
    ProcessingPipelineResult,
    ScannedDocument,
)
from ..domain.enums import (
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
    OcrLanguage,
    ProcessingPhase,
    ProcessingPriority,
    ReviewDecision,
    RetentionPolicy,
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


class DocumentVersionModel(DocIntelBase):
    __tablename__ = "docint_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    version_number = Column(Integer, nullable=False)
    storage_path = Column(String(1024), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    created_by = Column(String(128), nullable=False)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel")


class GovernmentDocumentModel(DocIntelBase):
    __tablename__ = "docint_government_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, unique=True, index=True
    )
    reference_number = Column(String(128), nullable=False, index=True)
    issuing_authority = Column(String(256), nullable=False)
    recipient_authority = Column(String(256), nullable=True)
    subject = Column(String(512), nullable=True)
    classification = Column(Enum(ConfidentialityLevel), nullable=False, default=ConfidentialityLevel.internal)
    decision_number = Column(String(128), nullable=True)
    committee_name = Column(String(256), nullable=True)
    contract_number = Column(String(128), nullable=True)
    procurement_number = Column(String(128), nullable=True)
    legal_basis = Column(String(512), nullable=True)
    signatory_name = Column(String(256), nullable=True)
    signatory_title = Column(String(256), nullable=True)
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> GovernmentDocument:
        return GovernmentDocument(
            id=self.id,
            document_id=self.document_id,
            reference_number=self.reference_number,
            issuing_authority=self.issuing_authority,
            recipient_authority=self.recipient_authority or "",
            subject=self.subject or "",
            classification=self.classification,
            decision_number=self.decision_number or "",
            committee_name=self.committee_name or "",
            contract_number=self.contract_number or "",
            procurement_number=self.procurement_number or "",
            legal_basis=self.legal_basis or "",
            signatory_name=self.signatory_name or "",
            signatory_title=self.signatory_title or "",
            effective_date=self.effective_date,
            expiry_date=self.expiry_date,
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, gov: GovernmentDocument) -> GovernmentDocumentModel:
        return cls(
            id=gov.id,
            document_id=gov.document_id,
            reference_number=gov.reference_number,
            issuing_authority=gov.issuing_authority,
            recipient_authority=gov.recipient_authority or None,
            subject=gov.subject or None,
            classification=gov.classification,
            decision_number=gov.decision_number or None,
            committee_name=gov.committee_name or None,
            contract_number=gov.contract_number or None,
            procurement_number=gov.procurement_number or None,
            legal_basis=gov.legal_basis or None,
            signatory_name=gov.signatory_name or None,
            signatory_title=gov.signatory_title or None,
            effective_date=gov.effective_date,
            expiry_date=gov.expiry_date,
            metadata_json=gov.metadata,
        )


class DocumentReviewModel(DocIntelBase):
    __tablename__ = "docint_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    reviewer_id = Column(String(128), nullable=False)
    reviewer_name = Column(String(256), nullable=False)
    role = Column(Enum(CollaborationRole), nullable=False, default=CollaborationRole.reviewer)
    decision = Column(Enum(ReviewDecision), nullable=True)
    comments = Column(Text, nullable=True)
    suggested_changes = Column(JSON, nullable=True, default=list)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> DocumentReview:
        return DocumentReview(
            id=self.id,
            document_id=self.document_id,
            reviewer_id=self.reviewer_id,
            reviewer_name=self.reviewer_name,
            role=self.role,
            decision=self.decision,
            comments=self.comments or "",
            suggested_changes=self.suggested_changes or [],
            assigned_at=self.assigned_at,
            completed_at=self.completed_at,
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, review: DocumentReview, document_id: UUID) -> DocumentReviewModel:
        return cls(
            document_id=document_id,
            reviewer_id=review.reviewer_id,
            reviewer_name=review.reviewer_name,
            role=review.role,
            decision=review.decision,
            comments=review.comments,
            suggested_changes=review.suggested_changes,
            assigned_at=review.assigned_at,
            metadata_json=review.metadata,
        )


class DocumentAnnotationModel(DocIntelBase):
    __tablename__ = "docint_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    page_number = Column(Integer, nullable=False, default=0)
    author_id = Column(String(128), nullable=False)
    author_name = Column(String(256), nullable=True)
    content = Column(Text, nullable=False)
    annotation_type = Column(String(64), nullable=False, default="comment")
    resolved = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON, nullable=True, default=dict)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> DocumentAnnotation:
        return DocumentAnnotation(
            id=self.id,
            document_id=self.document_id,
            page_number=self.page_number,
            author_id=self.author_id,
            author_name=self.author_name or "",
            content=self.content,
            annotation_type=self.annotation_type,
            resolved=bool(self.resolved),
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, ann: DocumentAnnotation) -> DocumentAnnotationModel:
        return cls(
            id=ann.id,
            document_id=ann.document_id,
            page_number=ann.page_number,
            author_id=ann.author_id,
            author_name=ann.author_name,
            content=ann.content,
            annotation_type=ann.annotation_type,
            resolved=1 if ann.resolved else 0,
            metadata_json=ann.metadata,
        )


class DigitalPreservationRecordModel(DocIntelBase):
    __tablename__ = "docint_preservation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, unique=True, index=True
    )
    standard = Column(Enum(DigitalPreservationStandard), nullable=False, default=DigitalPreservationStandard.oais)
    preservation_level = Column(String(64), nullable=False, default="full")
    original_format = Column(String(64), nullable=False)
    preservation_format = Column(String(64), nullable=False)
    original_checksum = Column(String(128), nullable=False)
    preservation_checksum = Column(String(128), nullable=False)
    checksum_method = Column(Enum(IntegrityCheckMethod), nullable=False, default=IntegrityCheckMethod.sha256)
    preservation_location = Column(String(1024), nullable=False)
    cold_storage_location = Column(String(1024), nullable=True)
    integrity_log = Column(JSON, nullable=True, default=list)
    preservation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    next_integrity_check = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> DigitalPreservationRecord:
        return DigitalPreservationRecord(
            id=self.id,
            document_id=self.document_id,
            standard=self.standard,
            preservation_level=self.preservation_level,
            original_format=self.original_format,
            preservation_format=self.preservation_format,
            original_checksum=self.original_checksum,
            preservation_checksum=self.preservation_checksum,
            checksum_method=self.checksum_method,
            preservation_location=self.preservation_location,
            cold_storage_location=self.cold_storage_location or "",
            integrity_log=self.integrity_log or [],
            preservation_date=self.preservation_date,
            next_integrity_check=self.next_integrity_check,
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, record: DigitalPreservationRecord) -> DigitalPreservationRecordModel:
        return cls(
            id=record.id,
            document_id=record.document_id,
            standard=record.standard,
            preservation_level=record.preservation_level,
            original_format=record.original_format,
            preservation_format=record.preservation_format,
            original_checksum=record.original_checksum,
            preservation_checksum=record.preservation_checksum,
            checksum_method=record.checksum_method,
            preservation_location=record.preservation_location,
            cold_storage_location=record.cold_storage_location or None,
            integrity_log=record.integrity_log,
            preservation_date=record.preservation_date,
            next_integrity_check=record.next_integrity_check,
            metadata_json=record.metadata,
        )


class GovernancePolicyModel(DocIntelBase):
    __tablename__ = "docint_governance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(256), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    domain = Column(Enum(GovernanceDomain), nullable=False)
    severity = Column(Enum(GovernanceRuleSeverity), nullable=False, default=GovernanceRuleSeverity.warning)
    action = Column(Enum(GovernancePolicyAction), nullable=False, default=GovernancePolicyAction.flag)
    conditions = Column(JSON, nullable=False, default=dict)
    enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> GovernancePolicy:
        return GovernancePolicy(
            id=self.id,
            name=self.name,
            description=self.description or "",
            domain=self.domain,
            severity=self.severity,
            action=self.action,
            conditions=self.conditions or {},
            enabled=bool(self.enabled),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, policy: GovernancePolicy) -> GovernancePolicyModel:
        return cls(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            domain=policy.domain,
            severity=policy.severity,
            action=policy.action,
            conditions=policy.conditions,
            enabled=1 if policy.enabled else 0,
        )


class GovernanceEventModel(DocIntelBase):
    __tablename__ = "docint_governance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=True, index=True
    )
    policy_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_governance_policies.id"), nullable=True
    )
    domain = Column(Enum(GovernanceDomain), nullable=False)
    severity = Column(Enum(GovernanceRuleSeverity), nullable=False, default=GovernanceRuleSeverity.info)
    message = Column(Text, nullable=False)
    action_taken = Column(Enum(GovernancePolicyAction), nullable=False, default=GovernancePolicyAction.notify)
    details = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_domain(self) -> GovernanceEvent:
        return GovernanceEvent(
            id=self.id,
            document_id=self.document_id,
            policy_id=self.policy_id,
            domain=self.domain,
            severity=self.severity,
            message=self.message,
            action_taken=self.action_taken,
            details=self.details or {},
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, event: GovernanceEvent) -> GovernanceEventModel:
        return cls(
            id=event.id,
            document_id=event.document_id,
            policy_id=event.policy_id,
            domain=event.domain,
            severity=event.severity,
            message=event.message,
            action_taken=event.action_taken,
            details=event.details,
        )


class DocumentEventModel(DocIntelBase):
    __tablename__ = "docint_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    channel = Column(Enum(EventChannel), nullable=False)
    actor_id = Column(String(128), nullable=False)
    actor_name = Column(String(256), nullable=True)
    payload = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> DocumentEvent:
        return DocumentEvent(
            id=self.id,
            document_id=self.document_id,
            channel=self.channel,
            actor_id=self.actor_id,
            actor_name=self.actor_name or "",
            payload=self.payload or {},
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, event: DocumentEvent) -> DocumentEventModel:
        return cls(
            document_id=event.document_id,
            channel=event.channel,
            actor_id=event.actor_id,
            actor_name=event.actor_name,
            payload=event.payload,
        )


class DocumentLifecycleModel(DocIntelBase):
    __tablename__ = "docint_lifecycle"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    event_type = Column(String(64), nullable=False)
    previous_status = Column(Enum(DocumentStatus), nullable=True)
    new_status = Column(Enum(DocumentStatus), nullable=True)
    actor = Column(String(256), nullable=False)
    reason = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("ScannedDocumentModel")

    def to_domain(self) -> DocumentLifecycleRecord:
        return DocumentLifecycleRecord(
            id=self.id,
            document_id=self.document_id,
            event_type=self.event_type,
            previous_status=self.previous_status,
            new_status=self.new_status,
            actor=self.actor,
            reason=self.reason or "",
            created_at=self.created_at,
            metadata=self.metadata_json or {},
        )


class WebhookRegistrationModel(DocIntelBase):
    __tablename__ = "docint_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String(2048), nullable=False)
    events = Column(JSON, nullable=False, default=list)
    secret = Column(String(256), nullable=True)
    active = Column(Integer, nullable=False, default=1)
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    failure_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeGraphEdgeModel(DocIntelBase):
    __tablename__ = "docint_knowledge_graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=True, index=True
    )
    target_document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=True, index=True
    )
    source_entity = Column(String(256), nullable=False)
    target_entity = Column(String(256), nullable=False)
    relation = Column(Enum(KnowledgeGraphRelation), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    weight = Column(Float, nullable=False, default=1.0)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_domain(self) -> KnowledgeGraphEdge:
        return KnowledgeGraphEdge(
            source_document_id=self.source_document_id,
            target_document_id=self.target_document_id,
            source_entity=self.source_entity,
            target_entity=self.target_entity,
            relation=self.relation,
            confidence=self.confidence,
            weight=self.weight,
            metadata=self.metadata_json or {},
        )

    @classmethod
    def from_domain(cls, edge: KnowledgeGraphEdge) -> KnowledgeGraphEdgeModel:
        return cls(
            source_document_id=edge.source_document_id,
            target_document_id=edge.target_document_id,
            source_entity=edge.source_entity,
            target_entity=edge.target_entity,
            relation=edge.relation,
            confidence=edge.confidence,
            weight=edge.weight,
            metadata_json=edge.metadata,
        )


class PipelineHealthModel(DocIntelBase):
    __tablename__ = "docint_pipeline_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pipeline_name = Column(String(128), nullable=False, index=True)
    phase = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="healthy")
    documents_processed = Column(Integer, nullable=False, default=0)
    documents_failed = Column(Integer, nullable=False, default=0)
    avg_processing_time_ms = Column(Float, nullable=False, default=0.0)
    p95_processing_time_ms = Column(Float, nullable=False, default=0.0)
    error_rate = Column(Float, nullable=False, default=0.0)
    throughput_per_minute = Column(Float, nullable=False, default=0.0)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> PipelineHealth:
        return PipelineHealth(
            pipeline_name=self.pipeline_name,
            phase=self.phase,
            status=self.status,
            documents_processed=self.documents_processed,
            documents_failed=self.documents_failed,
            avg_processing_time_ms=self.avg_processing_time_ms,
            p95_processing_time_ms=self.p95_processing_time_ms,
            error_rate=self.error_rate,
            throughput_per_minute=self.throughput_per_minute,
            last_error=self.last_error or "",
            last_error_at=self.last_error_at,
        )


class AccessControlModel(DocIntelBase):
    __tablename__ = "docint_access_control"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, index=True
    )
    user_id = Column(String(128), nullable=False, index=True)
    role = Column(Enum(CollaborationRole), nullable=False, default=CollaborationRole.viewer)
    delegated_from = Column(String(128), nullable=True)
    delegated_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("ScannedDocumentModel")


class DocumentRetentionModel(DocIntelBase):
    __tablename__ = "docint_retention"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("docint_documents.id"), nullable=False, unique=True, index=True
    )
    policy = Column(Enum(RetentionPolicy), nullable=False, default=RetentionPolicy.standard_7y)
    archive_status = Column(Enum(ArchiveStatus), nullable=False, default=ArchiveStatus.active)
    retention_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    retention_end = Column(DateTime, nullable=True)
    legal_hold = Column(Integer, nullable=False, default=0)
    legal_hold_reason = Column(Text, nullable=True)
    purge_scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("ScannedDocumentModel")
