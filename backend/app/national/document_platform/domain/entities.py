from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.document_platform.domain.enums import (
    DocumentCategory,
    DocumentFormat,
    DocumentStatus,
    RetentionPolicy,
    SignatureStatus,
)


@dataclass
class Document:
    id: str
    filename: str
    original_name: str
    mime_type: str
    format: DocumentFormat = DocumentFormat.OTHER
    size_bytes: int = 0
    hash_sha256: str = ""
    version: int = 1
    category: DocumentCategory = DocumentCategory.OTHER
    status: DocumentStatus = DocumentStatus.DRAFT
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    retention_policy: RetentionPolicy = RetentionPolicy.STANDARD_1Y
    expires_at: datetime | None = None
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    is_deleted: bool = False
    deleted_at: datetime | None = None

    @property
    def is_draft(self) -> bool:
        return self.status == DocumentStatus.DRAFT

    @property
    def is_final(self) -> bool:
        return self.status == DocumentStatus.FINAL

    @property
    def is_archived(self) -> bool:
        return self.status == DocumentStatus.ARCHIVED

    @property
    def is_deleted_status(self) -> bool:
        return self.status == DocumentStatus.DELETED

    @property
    def is_active(self) -> bool:
        return not self.is_deleted and self.status not in (
            DocumentStatus.DELETED,
            DocumentStatus.ARCHIVED,
        )


@dataclass
class DocumentVersion:
    id: str
    document_id: str
    version_number: int = 1
    filename: str = ""
    size_bytes: int = 0
    hash_sha256: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    change_summary: str = ""


@dataclass
class ElectronicSignature:
    id: str
    document_id: str
    signer_id: str = ""
    signer_name: str = ""
    signer_role: str = ""
    signature_type: str = "electronic"
    certificate_id: str = ""
    signed_at: datetime | None = None
    expires_at: datetime | None = None
    verification_url: str = ""
    signature_value: str = ""
    status: SignatureStatus = SignatureStatus.PENDING
    hash_chain_previous: str = ""
    hash_chain_current: str = ""


@dataclass
class DocumentQRCode:
    id: str
    document_id: str
    qr_data: str = ""
    verification_url: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    scanned_count: int = 0


@dataclass
class DocumentAttachment:
    id: str
    document_id: str
    filename: str = ""
    size_bytes: int = 0
    mime_type: str = ""
    storage_path: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RetentionRule:
    id: str
    category: DocumentCategory = DocumentCategory.OTHER
    policy: RetentionPolicy = RetentionPolicy.STANDARD_1Y
    retention_days: int = 365
    action_at: datetime | None = None
    archive_required: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
