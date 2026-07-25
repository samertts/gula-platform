from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.national.document_platform.domain.entities import (
    Document,
    DocumentAttachment,
    DocumentQRCode,
    DocumentVersion,
    ElectronicSignature,
    RetentionRule,
)
from app.national.document_platform.domain.enums import DocumentCategory, DocumentStatus


class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> Document: ...

    @abstractmethod
    async def get(self, document_id: str) -> Document | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Document]: ...

    @abstractmethod
    async def delete(self, document_id: str, soft: bool = True) -> None: ...

    @abstractmethod
    async def find_by_status(
        self,
        status: DocumentStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]: ...

    @abstractmethod
    async def find_by_category(
        self,
        category: DocumentCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]: ...

    @abstractmethod
    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]: ...

    @abstractmethod
    async def count(self, **filters: Any) -> int: ...


class DocumentVersionRepository(ABC):
    @abstractmethod
    async def save(self, version: DocumentVersion) -> DocumentVersion: ...

    @abstractmethod
    async def get(self, version_id: str) -> DocumentVersion | None: ...

    @abstractmethod
    async def list(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentVersion]: ...

    @abstractmethod
    async def delete(self, version_id: str) -> None: ...


class ElectronicSignatureRepository(ABC):
    @abstractmethod
    async def save(self, signature: ElectronicSignature) -> ElectronicSignature: ...

    @abstractmethod
    async def get(self, signature_id: str) -> ElectronicSignature | None: ...

    @abstractmethod
    async def list(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ElectronicSignature]: ...

    @abstractmethod
    async def find_by_signer(
        self,
        signer_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ElectronicSignature]: ...


class DocumentQRCodeRepository(ABC):
    @abstractmethod
    async def save(self, qr_code: DocumentQRCode) -> DocumentQRCode: ...

    @abstractmethod
    async def get(self, qr_code_id: str) -> DocumentQRCode | None: ...

    @abstractmethod
    async def get_by_document(
        self,
        document_id: str,
    ) -> DocumentQRCode | None: ...

    @abstractmethod
    async def increment_scanned(self, qr_code_id: str) -> None: ...


class DocumentAttachmentRepository(ABC):
    @abstractmethod
    async def save(self, attachment: DocumentAttachment) -> DocumentAttachment: ...

    @abstractmethod
    async def get(self, attachment_id: str) -> DocumentAttachment | None: ...

    @abstractmethod
    async def list(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentAttachment]: ...

    @abstractmethod
    async def delete(self, attachment_id: str) -> None: ...


class RetentionRuleRepository(ABC):
    @abstractmethod
    async def save(self, rule: RetentionRule) -> RetentionRule: ...

    @abstractmethod
    async def get(self, rule_id: str) -> RetentionRule | None: ...

    @abstractmethod
    async def find_by_category(
        self,
        category: DocumentCategory,
    ) -> RetentionRule | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RetentionRule]: ...

    @abstractmethod
    async def delete(self, rule_id: str) -> None: ...
