from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol
from uuid import UUID

from .entities import (
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
from .enums import (
    CollaborationRole,
    DocumentCategory,
    DocumentStatus,
    EventChannel,
    GovernanceDomain,
    GovernanceRuleSeverity,
    ProcessingPriority,
    RetentionPolicy,
)


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


class GovernmentDocumentRepository(ABC):
    @abstractmethod
    async def save(self, gov: GovernmentDocument) -> GovernmentDocument:
        ...

    @abstractmethod
    async def get(self, document_id: UUID) -> GovernmentDocument | None:
        ...

    @abstractmethod
    async def search(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 50
    ) -> list[GovernmentDocument]:
        ...


class ReviewRepository(ABC):
    @abstractmethod
    async def save(self, review: DocumentReview) -> DocumentReview:
        ...

    @abstractmethod
    async def get(self, review_id: UUID) -> DocumentReview | None:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[DocumentReview]:
        ...

    @abstractmethod
    async def update(self, review: DocumentReview) -> DocumentReview:
        ...


class AnnotationRepository(ABC):
    @abstractmethod
    async def save(self, annotation: DocumentAnnotation) -> DocumentAnnotation:
        ...

    @abstractmethod
    async def get(self, annotation_id: UUID) -> DocumentAnnotation | None:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[DocumentAnnotation]:
        ...

    @abstractmethod
    async def update(self, annotation: DocumentAnnotation) -> DocumentAnnotation:
        ...


class PreservationRepository(ABC):
    @abstractmethod
    async def save(self, record: DigitalPreservationRecord) -> DigitalPreservationRecord:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> DigitalPreservationRecord | None:
        ...

    @abstractmethod
    async def update(self, record: DigitalPreservationRecord) -> DigitalPreservationRecord:
        ...

    @abstractmethod
    async def list_due_for_integrity_check(self) -> list[DigitalPreservationRecord]:
        ...


class GovernancePolicyRepository(ABC):
    @abstractmethod
    async def save(self, policy: GovernancePolicy) -> GovernancePolicy:
        ...

    @abstractmethod
    async def get(self, policy_id: UUID) -> GovernancePolicy | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> GovernancePolicy | None:
        ...

    @abstractmethod
    async def list(self, domain: GovernanceDomain | None = None) -> list[GovernancePolicy]:
        ...

    @abstractmethod
    async def delete(self, policy_id: UUID) -> None:
        ...


class GovernanceEventRepository(ABC):
    @abstractmethod
    async def save(self, event: GovernanceEvent) -> GovernanceEvent:
        ...

    @abstractmethod
    async def list(
        self, document_id: UUID | None = None, severity: GovernanceRuleSeverity | None = None
    ) -> list[GovernanceEvent]:
        ...


class DocumentEventRepository(ABC):
    @abstractmethod
    async def save(self, event: DocumentEvent) -> DocumentEvent:
        ...

    @abstractmethod
    async def list(
        self, document_id: UUID | None = None, channel: EventChannel | None = None
    ) -> list[DocumentEvent]:
        ...


class LifecycleRepository(ABC):
    @abstractmethod
    async def save(self, record: DocumentLifecycleRecord) -> DocumentLifecycleRecord:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[DocumentLifecycleRecord]:
        ...


class GraphEdgeRepository(ABC):
    @abstractmethod
    async def save(self, edge: KnowledgeGraphEdge) -> KnowledgeGraphEdge:
        ...

    @abstractmethod
    async def get_by_document(self, document_id: UUID) -> list[KnowledgeGraphEdge]:
        ...

    @abstractmethod
    async def find_related(
        self, document_id: UUID, max_depth: int = 3
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_entity_network(self, entity_name: str) -> list[dict[str, Any]]:
        ...


class AccessControlRepository(ABC):
    @abstractmethod
    async def grant(self, document_id: UUID, user_id: str, role: CollaborationRole) -> None:
        ...

    @abstractmethod
    async def revoke(self, document_id: UUID, user_id: str) -> None:
        ...

    @abstractmethod
    async def check(self, document_id: UUID, user_id: str) -> CollaborationRole | None:
        ...

    @abstractmethod
    async def get_by_user(self, user_id: str) -> list[UUID]:
        ...


class WebhookRepository(ABC):
    @abstractmethod
    async def register(
        self, url: str, events: list[EventChannel], secret: str | None = None
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def unregister(self, webhook_id: UUID) -> None:
        ...

    @abstractmethod
    async def get_by_event(self, channel: EventChannel) -> list[dict[str, Any]]:
        ...


class RetentionRepository(ABC):
    @abstractmethod
    async def save(self, document_id: UUID, policy: RetentionPolicy) -> None:
        ...

    @abstractmethod
    async def get(self, document_id: UUID) -> RetentionPolicy | None:
        ...

    @abstractmethod
    async def list_expiring(self, days: int = 30) -> list[UUID]:
        ...

    @abstractmethod
    async def list_active(self) -> list[UUID]:
        ...


class DocumentVersionRepository(ABC):
    @abstractmethod
    async def save_version(
        self, document_id: UUID, version: int, storage_path: str, checksum: str, created_by: str
    ) -> None:
        ...

    @abstractmethod
    async def get_latest_version(self, document_id: UUID) -> int:
        ...

    @abstractmethod
    async def list_versions(self, document_id: UUID) -> list[dict[str, Any]]:
        ...


class PipelineHealthRepository(ABC):
    @abstractmethod
    async def save(self, health: PipelineHealth) -> PipelineHealth:
        ...

    @abstractmethod
    async def get_latest(self, pipeline_name: str, phase: str) -> PipelineHealth | None:
        ...

    @abstractmethod
    async def get_all_pipelines(self) -> list[PipelineHealth]:
        ...
