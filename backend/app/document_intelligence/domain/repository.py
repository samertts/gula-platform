from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol
from uuid import UUID

from .entities import (
    ClassificationResult,
    ExtractedEntity,
    ExtractedField,
    ExtractedTable,
    OcrResult,
    ProcessingPipelineResult,
    ScannedDocument,
)
from .enums import DocumentCategory, DocumentStatus, ProcessingPriority


class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: ScannedDocument) -> ScannedDocument:
        ...

    @abstractmethod
    async def get(self, document_id: UUID) -> ScannedDocument | None:
        ...

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        tenant_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ScannedDocument], int]:
        ...

    @abstractmethod
    async def update_status(
        self, document_id: UUID, status: DocumentStatus, error: str = ""
    ) -> None:
        ...

    @abstractmethod
    async def count_by_status(self, tenant_id: UUID | None = None) -> dict[DocumentStatus, int]:
        ...

    @abstractmethod
    async def find_duplicates(
        self, checksum: str, tenant_id: UUID | None = None
    ) -> list[ScannedDocument]:
        ...

    @abstractmethod
    async def get_pending_processing(
        self, limit: int = 50, priority: ProcessingPriority | None = None
    ) -> list[ScannedDocument]:
        ...


class OcrResultRepository(ABC):
    @abstractmethod
    async def save(self, result: OcrResult) -> OcrResult:
        ...

    @abstractmethod
    async def get(self, document_id: UUID) -> OcrResult | None:
        ...

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        ...


class EntityRepository(ABC):
    @abstractmethod
    async def save_many(
        self, document_id: UUID, entities: list[ExtractedEntity]
    ) -> list[ExtractedEntity]:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[ExtractedEntity]:
        ...

    @abstractmethod
    async def search_by_value(
        self, value: str, tenant_id: UUID | None = None, limit: int = 50
    ) -> list[ExtractedEntity]:
        ...


class FieldRepository(ABC):
    @abstractmethod
    async def save_many(
        self, document_id: UUID, fields: list[ExtractedField]
    ) -> list[ExtractedField]:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[ExtractedField]:
        ...


class TableRepository(ABC):
    @abstractmethod
    async def save_many(
        self, document_id: UUID, tables: list[ExtractedTable]
    ) -> list[ExtractedTable]:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[ExtractedTable]:
        ...


class ClassificationResultRepository(ABC):
    @abstractmethod
    async def save(self, result: ClassificationResult) -> ClassificationResult:
        ...

    @abstractmethod
    async def get(self, document_id: UUID) -> ClassificationResult | None:
        ...


class PipelineResultRepository(ABC):
    @abstractmethod
    async def save(self, result: ProcessingPipelineResult) -> ProcessingPipelineResult:
        ...

    @abstractmethod
    async def get(self, document_id: UUID) -> ProcessingPipelineResult | None:
        ...


class StorageRepository(Protocol):
    async def save(self, data: bytes, path: str, encrypt: bool = True) -> str: ...

    async def read(self, path: str, decrypt: bool = True) -> bytes: ...

    async def delete(self, path: str) -> None: ...

    async def exists(self, path: str) -> bool: ...

    async def get_size(self, path: str) -> int: ...
