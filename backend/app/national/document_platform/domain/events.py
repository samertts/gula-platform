from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.national.document_platform.domain.enums import (
    DocumentCategory,
    DocumentFormat,
    RetentionPolicy,
)
from app.national.events.base import NationalDomainEvent


@dataclass
class DocumentCreatedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.created"
    aggregate_type: str = "Document"
    document_id: str = ""
    filename: str = ""
    category: DocumentCategory | None = None
    format: DocumentFormat | None = None


@dataclass
class DocumentUpdatedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.updated"
    aggregate_type: str = "Document"
    document_id: str = ""
    changes: dict[str, Any] | None = None


@dataclass
class DocumentVersionedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.versioned"
    aggregate_type: str = "DocumentVersion"
    document_id: str = ""
    version_id: str = ""
    version_number: int = 0


@dataclass
class DocumentSignedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.signed"
    aggregate_type: str = "ElectronicSignature"
    document_id: str = ""
    signature_id: str = ""
    signer_id: str = ""
    signer_name: str = ""


@dataclass
class DocumentVerifiedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.verified"
    aggregate_type: str = "ElectronicSignature"
    document_id: str = ""
    signature_id: str = ""
    valid: bool = False


@dataclass
class DocumentArchivedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.archived"
    aggregate_type: str = "Document"
    document_id: str = ""
    reason: str = ""


@dataclass
class DocumentDeletedEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.deleted"
    aggregate_type: str = "Document"
    document_id: str = ""
    reason: str = ""


@dataclass
class DocumentExpiredEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.expired"
    aggregate_type: str = "Document"
    document_id: str = ""
    filename: str = ""


@dataclass
class DocumentRetentionTriggeredEvent(NationalDomainEvent):
    event_type: str = "national.document_platform.document.retention_triggered"
    aggregate_type: str = "RetentionRule"
    document_id: str = ""
    rule_id: str = ""
    policy: RetentionPolicy | None = None
