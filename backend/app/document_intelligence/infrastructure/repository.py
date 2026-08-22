from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, sessionmaker

from ..domain.entities import (
    ClassificationResult,
    DigitalPreservationRecord,
    DocumentAnnotation,
    DocumentEvent,
    DocumentLifecycleRecord,
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
)
from ..domain.enums import (
    CollaborationRole,
    DocumentCategory,
    DocumentStatus,
    EventChannel,
    GovernanceDomain,
    GovernanceRuleSeverity,
    ProcessingPriority,
    RetentionPolicy,
)
from ..domain.repository import (
    AccessControlRepository,
    AnnotationRepository,
    ClassificationResultRepository,
    DocumentEventRepository,
    DocumentRepository,
    DocumentVersionRepository,
    EntityRepository,
    FieldRepository,
    GovernanceEventRepository,
    GovernancePolicyRepository,
    GovernmentDocumentRepository,
    GraphEdgeRepository,
    LifecycleRepository,
    OcrResultRepository,
    PipelineHealthRepository,
    PipelineResultRepository,
    PreservationRepository,
    RetentionRepository,
    ReviewRepository,
    StorageRepository,
    TableRepository,
    WebhookRepository,
)
from ..exceptions import DocumentNotFoundError
from .models import (
    AccessControlModel,
    ClassificationResultModel,
    DigitalPreservationRecordModel,
    DocumentAnnotationModel,
    DocumentEventModel,
    DocumentLifecycleModel,
    DocumentRetentionModel,
    DocumentReviewModel,
    DocumentVersionModel,
    ExtractedEntityModel,
    ExtractedFieldModel,
    ExtractedTableModel,
    GovernanceEventModel,
    GovernancePolicyModel,
    GovernmentDocumentModel,
    KnowledgeGraphEdgeModel,
    OcrResultModel,
    PipelineHealthModel,
    PipelineResultModel,
    ScannedDocumentModel,
    WebhookRegistrationModel,
)

logger = logging.getLogger("gula.document_intelligence.repository")


class SqlDocumentRepository(DocumentRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def _session(self) -> Session:
        return self._session_factory()

    async def save(self, document: ScannedDocument) -> ScannedDocument:
        with self._session() as session:
            existing = session.get(ScannedDocumentModel, document.id)
            if existing:
                for key, value in ScannedDocumentModel.from_domain(document).__dict__.items():
                    if key != "_sa_instance_state":
                        setattr(existing, key, value)
                session.flush()
                saved = existing
            else:
                model = ScannedDocumentModel.from_domain(document)
                session.add(model)
                session.flush()
                saved = model
            session.commit()
            return saved.to_domain()

    async def get(self, document_id: UUID) -> ScannedDocument | None:
        with self._session() as session:
            model = session.get(ScannedDocumentModel, document_id)
            return model.to_domain() if model else None

    async def delete(self, document_id: UUID) -> None:
        with self._session() as session:
            model = session.get(ScannedDocumentModel, document_id)
            if model:
                session.delete(model)
                session.commit()

    async def list(
        self,
        status: DocumentStatus | None = None,
        category: DocumentCategory | None = None,
        patient_id: UUID | None = None,
        lab_id: UUID | None = None,
        tenant_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ScannedDocument], int]:
        with self._session() as session:
            query = session.query(ScannedDocumentModel)
            filters = []
            if status:
                filters.append(ScannedDocumentModel.status == status)
            if patient_id:
                filters.append(ScannedDocumentModel.patient_id == patient_id)
            if lab_id:
                filters.append(ScannedDocumentModel.lab_id == lab_id)
            if tenant_id:
                filters.append(ScannedDocumentModel.tenant_id == tenant_id)
            if filters:
                query = query.filter(and_(*filters))

            total = query.count()
            models = (
                query.order_by(desc(ScannedDocumentModel.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [m.to_domain() for m in models], total

    async def search(
        self,
        query: str,
        tenant_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ScannedDocument], int]:
        with self._session() as session:
            q = session.query(ScannedDocumentModel)
            filters = [ScannedDocumentModel.filename.ilike(f"%{query}%")]
            if tenant_id:
                filters.append(ScannedDocumentModel.tenant_id == tenant_id)
            q = q.filter(and_(*filters))

            total = q.count()
            models = (
                q.order_by(desc(ScannedDocumentModel.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [m.to_domain() for m in models], total

    async def update_status(
        self, document_id: UUID, status: DocumentStatus, error: str = "",
    ) -> None:
        with self._session() as session:
            model = session.get(ScannedDocumentModel, document_id)
            if not model:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            model.status = status
            if error:
                model.error_message = error
            session.commit()

    async def count_by_status(
        self, tenant_id: UUID | None = None,
    ) -> dict[DocumentStatus, int]:
        with self._session() as session:
            query = session.query(
                ScannedDocumentModel.status, func.count(ScannedDocumentModel.id),
            )
            if tenant_id:
                query = query.filter(ScannedDocumentModel.tenant_id == tenant_id)
            query = query.group_by(ScannedDocumentModel.status)
            return {row[0]: row[1] for row in query.all()}

    async def find_duplicates(
        self, checksum: str, tenant_id: UUID | None = None,
    ) -> list[ScannedDocument]:
        with self._session() as session:
            query = session.query(ScannedDocumentModel).filter(
                ScannedDocumentModel.checksum_sha256 == checksum,
            )
            if tenant_id:
                query = query.filter(ScannedDocumentModel.tenant_id == tenant_id)
            return [m.to_domain() for m in query.all()]

    async def get_pending_processing(
        self, limit: int = 50, priority: ProcessingPriority | None = None,
    ) -> list[ScannedDocument]:
        with self._session() as session:
            query = session.query(ScannedDocumentModel).filter(
                ScannedDocumentModel.status.in_([
                    DocumentStatus.pending_ingestion,
                    DocumentStatus.ocr_pending,
                    DocumentStatus.classification_pending,
                    DocumentStatus.entity_extraction_pending,
                    DocumentStatus.fhir_mapping_pending,
                ]),
            )
            if priority:
                query = query.filter(ScannedDocumentModel.priority == priority)
            models = (
                query.order_by(
                    desc(ScannedDocumentModel.priority),
                    ScannedDocumentModel.created_at,
                )
                .limit(limit)
                .all()
            )
            return [m.to_domain() for m in models]


class SqlOcrResultRepository(OcrResultRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, result: OcrResult) -> OcrResult:
        with self._session_factory() as session:
            existing = None
            if result.document_id:
                existing = (
                    session.query(OcrResultModel)
                    .filter(OcrResultModel.document_id == result.document_id)
                    .first()
                )
            if existing:
                existing.full_text = result.full_text
                existing.ocr_engine = result.ocr_engine
                existing.confidence = result.confidence
                existing.processing_time_ms = result.processing_time_ms
                existing.page_count = result.page_count
                existing.success = 1 if result.success else 0
                existing.error_message = result.error_message
            else:
                model = OcrResultModel.from_domain(result)
                session.add(model)
            session.commit()
            return result

    async def get(self, document_id: UUID) -> OcrResult | None:
        with self._session_factory() as session:
            model = (
                session.query(OcrResultModel)
                .filter(OcrResultModel.document_id == document_id)
                .first()
            )
            return model.to_domain() if model else None

    async def delete(self, document_id: UUID) -> None:
        with self._session_factory() as session:
            session.query(OcrResultModel).filter(
                OcrResultModel.document_id == document_id,
            ).delete()
            session.commit()


class SqlEntityRepository(EntityRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save_many(
        self, document_id: UUID, entities: list[ExtractedEntity],
    ) -> list[ExtractedEntity]:
        with self._session_factory() as session:
            session.query(ExtractedEntityModel).filter(
                ExtractedEntityModel.document_id == document_id,
            ).delete()
            for entity in entities:
                session.add(ExtractedEntityModel.from_domain(entity, document_id))
            session.commit()
        return entities

    async def get_by_document(self, document_id: UUID) -> list[ExtractedEntity]:
        with self._session_factory() as session:
            models = (
                session.query(ExtractedEntityModel)
                .filter(ExtractedEntityModel.document_id == document_id)
                .all()
            )
            return [m.to_domain() for m in models]

    async def search_by_value(
        self, value: str, tenant_id: UUID | None = None, limit: int = 50,
    ) -> list[ExtractedEntity]:
        with self._session_factory() as session:
            query = session.query(ExtractedEntityModel).filter(
                ExtractedEntityModel.value.ilike(f"%{value}%"),
            )
            models = query.limit(limit).all()
            return [m.to_domain() for m in models]


class SqlFieldRepository(FieldRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save_many(
        self, document_id: UUID, fields: list[ExtractedField],
    ) -> list[ExtractedField]:
        with self._session_factory() as session:
            session.query(ExtractedFieldModel).filter(
                ExtractedFieldModel.document_id == document_id,
            ).delete()
            for field in fields:
                session.add(ExtractedFieldModel.from_domain(field, document_id))
            session.commit()
        return fields

    async def get_by_document(self, document_id: UUID) -> list[ExtractedField]:
        with self._session_factory() as session:
            models = (
                session.query(ExtractedFieldModel)
                .filter(ExtractedFieldModel.document_id == document_id)
                .all()
            )
            return [m.to_domain() for m in models]


class SqlTableRepository(TableRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save_many(
        self, document_id: UUID, tables: list[ExtractedTable],
    ) -> list[ExtractedTable]:
        with self._session_factory() as session:
            session.query(ExtractedTableModel).filter(
                ExtractedTableModel.document_id == document_id,
            ).delete()
            for table in tables:
                session.add(ExtractedTableModel.from_domain(table, document_id))
            session.commit()
        return tables

    async def get_by_document(self, document_id: UUID) -> list[ExtractedTable]:
        with self._session_factory() as session:
            models = (
                session.query(ExtractedTableModel)
                .filter(ExtractedTableModel.document_id == document_id)
                .all()
            )
            return [m.to_domain() for m in models]


class SqlClassificationResultRepository(ClassificationResultRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, result: ClassificationResult) -> ClassificationResult:
        with self._session_factory() as session:
            model = ClassificationResultModel.from_domain(result)
            session.add(model)
            session.commit()
        return result

    async def get(self, document_id: UUID) -> ClassificationResult | None:
        with self._session_factory() as session:
            model = (
                session.query(ClassificationResultModel)
                .filter(ClassificationResultModel.document_id == document_id)
                .first()
            )
            return model.to_domain() if model else None


class SqlPipelineResultRepository(PipelineResultRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, result: ProcessingPipelineResult) -> ProcessingPipelineResult:
        with self._session_factory() as session:
            existing = None
            if result.document_id:
                existing = (
                    session.query(PipelineResultModel)
                    .filter(PipelineResultModel.document_id == result.document_id)
                    .first()
                )
            if existing:
                existing.phases_completed = [str(p) for p in result.phases_completed]
                existing.fhir_resources = result.fhir_resources
                existing.knowledge_graph_entries = result.knowledge_graph_entries
                existing.vector_embeddings = result.vector_embeddings
                existing.search_index_entries = result.search_index_entries
                existing.total_processing_time_ms = result.total_processing_time_ms
                existing.success = 1 if result.success else 0
                existing.error_message = result.error_message
            else:
                model = PipelineResultModel.from_domain(result)
                session.add(model)
            session.commit()
        return result

    async def get(self, document_id: UUID) -> ProcessingPipelineResult | None:
        with self._session_factory() as session:
            model = (
                session.query(PipelineResultModel)
                .filter(PipelineResultModel.document_id == document_id)
                .first()
            )
            return model.to_domain() if model else None


class LocalStorageRepository(StorageRepository):
    def __init__(self, base_path: str | Path = "/data/documents") -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, path: str, encrypt: bool = True) -> str:
        full_path = self._base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        return str(full_path)

    async def read(self, path: str, decrypt: bool = True) -> bytes:
        full_path = self._base_path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Storage path not found: {path}")
        return full_path.read_bytes()

    async def delete(self, path: str) -> None:
        full_path = self._base_path / path
        if full_path.exists():
            full_path.unlink()

    async def exists(self, path: str) -> bool:
        return (self._base_path / path).exists()

    async def get_size(self, path: str) -> int:
        full_path = self._base_path / path
        return full_path.stat().st_size if full_path.exists() else 0


class SqlGovernmentDocumentRepository(GovernmentDocumentRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, gov: GovernmentDocument) -> GovernmentDocument:
        with self._session_factory() as s:
            existing = s.query(GovernmentDocumentModel).filter_by(document_id=gov.document_id).first()
            if existing:
                for k, v in GovernmentDocumentModel.from_domain(gov).__dict__.items():
                    if k != "_sa_instance_state":
                        setattr(existing, k, v)
                s.commit()
                return existing.to_domain()
            model = GovernmentDocumentModel.from_domain(gov)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get(self, document_id: UUID) -> GovernmentDocument | None:
        with self._session_factory() as s:
            m = s.query(GovernmentDocumentModel).filter_by(document_id=document_id).first()
            return m.to_domain() if m else None

    async def search(self, query: str, filters: dict[str, Any] | None = None, limit: int = 50) -> list[GovernmentDocument]:
        with self._session_factory() as s:
            q = s.query(GovernmentDocumentModel)
            q = q.filter(
                GovernmentDocumentModel.reference_number.ilike(f"%{query}%")
                | GovernmentDocumentModel.subject.ilike(f"%{query}%")
                | GovernmentDocumentModel.issuing_authority.ilike(f"%{query}%"),
            )
            return [m.to_domain() for m in q.limit(limit).all()]


class SqlReviewRepository(ReviewRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, review: DocumentReview) -> DocumentReview:
        with self._session_factory() as s:
            model = DocumentReviewModel.from_domain(review, review.document_id)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get(self, review_id: UUID) -> DocumentReview | None:
        with self._session_factory() as s:
            m = s.query(DocumentReviewModel).filter_by(id=review_id).first()
            return m.to_domain() if m else None

    async def get_by_document(self, document_id: UUID) -> list[DocumentReview]:
        with self._session_factory() as s:
            return [m.to_domain() for m in s.query(DocumentReviewModel).filter_by(document_id=document_id).all()]

    async def update(self, review: DocumentReview) -> DocumentReview:
        with self._session_factory() as s:
            m = s.query(DocumentReviewModel).filter_by(id=review.id).first()
            if m:
                m.decision = review.decision
                m.comments = review.comments
                m.suggested_changes = review.suggested_changes
                m.completed_at = review.completed_at
                s.commit()
            return review


class SqlAnnotationRepository(AnnotationRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, annotation: DocumentAnnotation) -> DocumentAnnotation:
        with self._session_factory() as s:
            model = DocumentAnnotationModel.from_domain(annotation)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get(self, annotation_id: UUID) -> DocumentAnnotation | None:
        with self._session_factory() as s:
            m = s.query(DocumentAnnotationModel).filter_by(id=annotation_id).first()
            return m.to_domain() if m else None

    async def get_by_document(self, document_id: UUID) -> list[DocumentAnnotation]:
        with self._session_factory() as s:
            return [m.to_domain() for m in s.query(DocumentAnnotationModel).filter_by(document_id=document_id).all()]

    async def update(self, annotation: DocumentAnnotation) -> DocumentAnnotation:
        with self._session_factory() as s:
            m = s.query(DocumentAnnotationModel).filter_by(id=annotation.id).first()
            if m:
                m.resolved = 1 if annotation.resolved else 0
                m.content = annotation.content
                s.commit()
            return annotation


class SqlPreservationRepository(PreservationRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, record: DigitalPreservationRecord) -> DigitalPreservationRecord:
        with self._session_factory() as s:
            existing = s.query(DigitalPreservationRecordModel).filter_by(document_id=record.document_id).first()
            if existing:
                for k, v in DigitalPreservationRecordModel.from_domain(record).__dict__.items():
                    if k != "_sa_instance_state":
                        setattr(existing, k, v)
                s.commit()
                return existing.to_domain()
            model = DigitalPreservationRecordModel.from_domain(record)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get_by_document(self, document_id: UUID) -> DigitalPreservationRecord | None:
        with self._session_factory() as s:
            m = s.query(DigitalPreservationRecordModel).filter_by(document_id=document_id).first()
            return m.to_domain() if m else None

    async def update(self, record: DigitalPreservationRecord) -> DigitalPreservationRecord:
        return await self.save(record)

    async def list_due_for_integrity_check(self) -> list[DigitalPreservationRecord]:
        from datetime import UTC, datetime
        with self._session_factory() as s:
            ms = s.query(DigitalPreservationRecordModel).filter(
                DigitalPreservationRecordModel.next_integrity_check <= datetime.now(UTC),
            ).all()
            return [m.to_domain() for m in ms]


class SqlGovernancePolicyRepository(GovernancePolicyRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, policy: GovernancePolicy) -> GovernancePolicy:
        with self._session_factory() as s:
            existing = s.query(GovernancePolicyModel).filter_by(name=policy.name).first()
            if existing:
                for k, v in GovernancePolicyModel.from_domain(policy).__dict__.items():
                    if k != "_sa_instance_state":
                        setattr(existing, k, v)
                s.commit()
                return existing.to_domain()
            model = GovernancePolicyModel.from_domain(policy)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get(self, policy_id: UUID) -> GovernancePolicy | None:
        with self._session_factory() as s:
            m = s.query(GovernancePolicyModel).filter_by(id=policy_id).first()
            return m.to_domain() if m else None

    async def get_by_name(self, name: str) -> GovernancePolicy | None:
        with self._session_factory() as s:
            m = s.query(GovernancePolicyModel).filter_by(name=name).first()
            return m.to_domain() if m else None

    async def list(self, domain: GovernanceDomain | None = None) -> list[GovernancePolicy]:
        with self._session_factory() as s:
            q = s.query(GovernancePolicyModel)
            if domain:
                q = q.filter_by(domain=domain)
            return [m.to_domain() for m in q.all()]

    async def delete(self, policy_id: UUID) -> None:
        with self._session_factory() as s:
            s.query(GovernancePolicyModel).filter_by(id=policy_id).delete()
            s.commit()


class SqlGovernanceEventRepository(GovernanceEventRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, event: GovernanceEvent) -> GovernanceEvent:
        with self._session_factory() as s:
            model = GovernanceEventModel.from_domain(event)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def list(self, document_id: UUID | None = None, severity: GovernanceRuleSeverity | None = None) -> list[GovernanceEvent]:
        with self._session_factory() as s:
            q = s.query(GovernanceEventModel)
            if document_id:
                q = q.filter_by(document_id=document_id)
            if severity:
                q = q.filter_by(severity=severity)
            return [m.to_domain() for m in q.order_by(GovernanceEventModel.created_at.desc()).all()]


class SqlDocumentEventRepository(DocumentEventRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, event: DocumentEvent) -> DocumentEvent:
        with self._session_factory() as s:
            model = DocumentEventModel.from_domain(event)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def list(self, document_id: UUID | None = None, channel: EventChannel | None = None) -> list[DocumentEvent]:
        with self._session_factory() as s:
            q = s.query(DocumentEventModel)
            if document_id:
                q = q.filter_by(document_id=document_id)
            if channel:
                q = q.filter_by(channel=channel)
            return [m.to_domain() for m in q.order_by(DocumentEventModel.created_at.desc()).all()]


class SqlLifecycleRepository(LifecycleRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, record: DocumentLifecycleRecord) -> DocumentLifecycleRecord:
        with self._session_factory() as s:
            model = DocumentLifecycleModel(
                id=record.id or None,
                document_id=record.document_id,
                event_type=record.event_type,
                previous_status=record.previous_status,
                new_status=record.new_status,
                actor=record.actor,
                reason=record.reason,
                metadata_json=record.metadata,
            )
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get_by_document(self, document_id: UUID) -> list[DocumentLifecycleRecord]:
        with self._session_factory() as s:
            return [m.to_domain() for m in s.query(DocumentLifecycleModel).filter_by(document_id=document_id)
                    .order_by(DocumentLifecycleModel.created_at.desc()).all()]


class SqlGraphEdgeRepository(GraphEdgeRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, edge: KnowledgeGraphEdge) -> KnowledgeGraphEdge:
        with self._session_factory() as s:
            model = KnowledgeGraphEdgeModel.from_domain(edge)
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get_by_document(self, document_id: UUID) -> list[KnowledgeGraphEdge]:
        with self._session_factory() as s:
            return [m.to_domain() for m in s.query(KnowledgeGraphEdgeModel)
                    .filter((KnowledgeGraphEdgeModel.source_document_id == document_id)
                            | (KnowledgeGraphEdgeModel.target_document_id == document_id)).all()]

    async def find_related(self, document_id: UUID, max_depth: int = 3) -> list[dict[str, Any]]:
        with self._session_factory() as s:
            edges = s.query(KnowledgeGraphEdgeModel).filter(
                (KnowledgeGraphEdgeModel.source_document_id == document_id)
                | (KnowledgeGraphEdgeModel.target_document_id == document_id),
            ).limit(50).all()
            seen: set[UUID] = set()
            related: list[dict[str, Any]] = []
            for e in edges:
                other = e.target_document_id if e.source_document_id == document_id else e.source_document_id
                if other and other not in seen:
                    seen.add(other)
                    related.append({
                        "document_id": str(other),
                        "relation": str(e.relation),
                        "confidence": e.confidence,
                    })
            return related

    async def get_entity_network(self, entity_name: str) -> list[dict[str, Any]]:
        with self._session_factory() as s:
            edges = s.query(KnowledgeGraphEdgeModel).filter(
                KnowledgeGraphEdgeModel.source_entity.ilike(f"%{entity_name}%")
                | KnowledgeGraphEdgeModel.target_entity.ilike(f"%{entity_name}%"),
            ).limit(100).all()
            return [e.to_domain() for e in edges]


class SqlAccessControlRepository(AccessControlRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def grant(self, document_id: UUID, user_id: str, role: CollaborationRole) -> None:
        with self._session_factory() as s:
            existing = s.query(AccessControlModel).filter_by(document_id=document_id, user_id=user_id).first()
            if existing:
                existing.role = role
            else:
                s.add(AccessControlModel(document_id=document_id, user_id=user_id, role=role))
            s.commit()

    async def revoke(self, document_id: UUID, user_id: str) -> None:
        with self._session_factory() as s:
            s.query(AccessControlModel).filter_by(document_id=document_id, user_id=user_id).delete()
            s.commit()

    async def check(self, document_id: UUID, user_id: str) -> CollaborationRole | None:
        with self._session_factory() as s:
            m = s.query(AccessControlModel).filter_by(document_id=document_id, user_id=user_id).first()
            return m.role if m else None

    async def get_by_user(self, user_id: str) -> list[UUID]:
        with self._session_factory() as s:
            return [m.document_id for m in s.query(AccessControlModel).filter_by(user_id=user_id).all()]


class SqlWebhookRepository(WebhookRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def register(self, url: str, events: list[EventChannel], secret: str | None = None) -> dict[str, Any]:
        with self._session_factory() as s:
            model = WebhookRegistrationModel(
                url=url,
                events=[str(e) for e in events],
                secret=secret,
            )
            s.add(model)
            s.commit()
            return {"id": str(model.id), "url": model.url, "events": model.events}

    async def unregister(self, webhook_id: UUID) -> None:
        with self._session_factory() as s:
            s.query(WebhookRegistrationModel).filter_by(id=webhook_id).delete()
            s.commit()

    async def get_by_event(self, channel: EventChannel) -> list[dict[str, Any]]:
        with self._session_factory() as s:
            results = []
            for m in s.query(WebhookRegistrationModel).filter_by(active=1).all():
                if str(channel) in (m.events or []):
                    results.append({"id": str(m.id), "url": m.url})
            return results


class SqlRetentionRepository(RetentionRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, document_id: UUID, policy: RetentionPolicy) -> None:
        with self._session_factory() as s:
            existing = s.query(DocumentRetentionModel).filter_by(document_id=document_id).first()
            if existing:
                existing.policy = policy
            else:
                s.add(DocumentRetentionModel(document_id=document_id, policy=policy))
            s.commit()

    async def get(self, document_id: UUID) -> RetentionPolicy | None:
        with self._session_factory() as s:
            m = s.query(DocumentRetentionModel).filter_by(document_id=document_id).first()
            return m.policy if m else None

    async def list_expiring(self, days: int = 30) -> list[UUID]:
        from datetime import UTC, datetime, timedelta

        with self._session_factory() as s:
            cutoff = datetime.now(UTC) + timedelta(days=days)
            return [m.document_id for m in s.query(DocumentRetentionModel)
                    .filter(DocumentRetentionModel.retention_end <= cutoff).all()]

    async def list_active(self) -> list[UUID]:
        with self._session_factory() as s:
            return [m.document_id for m in s.query(DocumentRetentionModel).all()]


class SqlVersionRepository(DocumentVersionRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save_version(self, document_id: UUID, version: int, storage_path: str, checksum: str, created_by: str) -> None:
        with self._session_factory() as s:
            s.add(DocumentVersionModel(
                document_id=document_id, version_number=version,
                storage_path=storage_path, checksum_sha256=checksum, created_by=created_by,
            ))
            s.commit()

    async def get_latest_version(self, document_id: UUID) -> int:
        with self._session_factory() as s:
            m = s.query(DocumentVersionModel).filter_by(document_id=document_id)\
                .order_by(DocumentVersionModel.version_number.desc()).first()
            return m.version_number if m else 0

    async def list_versions(self, document_id: UUID) -> list[dict[str, Any]]:
        with self._session_factory() as s:
            return [
                {
                    "version_number": m.version_number,
                    "storage_path": m.storage_path,
                    "checksum": m.checksum_sha256,
                    "size_bytes": m.size_bytes,
                    "created_by": m.created_by,
                    "created_at": m.created_at.isoformat(),
                }
                for m in s.query(DocumentVersionModel).filter_by(document_id=document_id)
                .order_by(DocumentVersionModel.version_number.desc()).all()
            ]


class SqlPipelineHealthRepository(PipelineHealthRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, health: PipelineHealth) -> PipelineHealth:
        with self._session_factory() as s:
            existing = s.query(PipelineHealthModel).filter_by(
                pipeline_name=health.pipeline_name, phase=health.phase,
            ).first()
            if existing:
                existing.status = health.status
                existing.documents_processed = health.documents_processed
                existing.documents_failed = health.documents_failed
                existing.avg_processing_time_ms = health.avg_processing_time_ms
                existing.p95_processing_time_ms = health.p95_processing_time_ms
                existing.error_rate = health.error_rate
                existing.throughput_per_minute = health.throughput_per_minute
                s.commit()
                return existing.to_domain()
            model = PipelineHealthModel(
                pipeline_name=health.pipeline_name, phase=health.phase,
                status=health.status, documents_processed=health.documents_processed,
                documents_failed=health.documents_failed,
                avg_processing_time_ms=health.avg_processing_time_ms,
                p95_processing_time_ms=health.p95_processing_time_ms,
                error_rate=health.error_rate,
                throughput_per_minute=health.throughput_per_minute,
            )
            s.add(model)
            s.commit()
            return model.to_domain()

    async def get_latest(self, pipeline_name: str, phase: str) -> PipelineHealth | None:
        with self._session_factory() as s:
            m = s.query(PipelineHealthModel).filter_by(
                pipeline_name=pipeline_name, phase=phase,
            ).order_by(PipelineHealthModel.updated_at.desc()).first()
            return m.to_domain() if m else None

    async def get_all_pipelines(self) -> list[PipelineHealth]:
        with self._session_factory() as s:
            return [m.to_domain() for m in s.query(PipelineHealthModel).all()]
