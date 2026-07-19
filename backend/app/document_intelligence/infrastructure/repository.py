from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import and_, create_engine, desc, func, or_, text
from sqlalchemy.orm import Session, sessionmaker

from ..domain.entities import (
    ClassificationResult,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    OcrResult,
    ProcessingPipelineResult,
    ScannedDocument,
)
from ..domain.enums import DocumentCategory, DocumentStatus, ProcessingPriority
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
from ..exceptions import DocumentNotFoundError
from .models import (
    ClassificationResultModel,
    ExtractedEntityModel,
    ExtractedFieldModel,
    ExtractedTableModel,
    OcrResultModel,
    PipelineResultModel,
    ScannedDocumentModel,
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
        self, document_id: UUID, status: DocumentStatus, error: str = ""
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
        self, tenant_id: UUID | None = None
    ) -> dict[DocumentStatus, int]:
        with self._session() as session:
            query = session.query(
                ScannedDocumentModel.status, func.count(ScannedDocumentModel.id)
            )
            if tenant_id:
                query = query.filter(ScannedDocumentModel.tenant_id == tenant_id)
            query = query.group_by(ScannedDocumentModel.status)
            return {row[0]: row[1] for row in query.all()}

    async def find_duplicates(
        self, checksum: str, tenant_id: UUID | None = None
    ) -> list[ScannedDocument]:
        with self._session() as session:
            query = session.query(ScannedDocumentModel).filter(
                ScannedDocumentModel.checksum_sha256 == checksum
            )
            if tenant_id:
                query = query.filter(ScannedDocumentModel.tenant_id == tenant_id)
            return [m.to_domain() for m in query.all()]

    async def get_pending_processing(
        self, limit: int = 50, priority: ProcessingPriority | None = None
    ) -> list[ScannedDocument]:
        with self._session() as session:
            query = session.query(ScannedDocumentModel).filter(
                ScannedDocumentModel.status.in_([
                    DocumentStatus.pending_ingestion,
                    DocumentStatus.ocr_pending,
                    DocumentStatus.classification_pending,
                    DocumentStatus.entity_extraction_pending,
                    DocumentStatus.fhir_mapping_pending,
                ])
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
                OcrResultModel.document_id == document_id
            ).delete()
            session.commit()


class SqlEntityRepository(EntityRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save_many(
        self, document_id: UUID, entities: list[ExtractedEntity]
    ) -> list[ExtractedEntity]:
        with self._session_factory() as session:
            session.query(ExtractedEntityModel).filter(
                ExtractedEntityModel.document_id == document_id
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
        self, value: str, tenant_id: UUID | None = None, limit: int = 50
    ) -> list[ExtractedEntity]:
        with self._session_factory() as session:
            query = session.query(ExtractedEntityModel).filter(
                ExtractedEntityModel.value.ilike(f"%{value}%")
            )
            models = query.limit(limit).all()
            return [m.to_domain() for m in models]


class SqlFieldRepository(FieldRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save_many(
        self, document_id: UUID, fields: list[ExtractedField]
    ) -> list[ExtractedField]:
        with self._session_factory() as session:
            session.query(ExtractedFieldModel).filter(
                ExtractedFieldModel.document_id == document_id
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
        self, document_id: UUID, tables: list[ExtractedTable]
    ) -> list[ExtractedTable]:
        with self._session_factory() as session:
            session.query(ExtractedTableModel).filter(
                ExtractedTableModel.document_id == document_id
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
