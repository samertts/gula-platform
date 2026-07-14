from __future__ import annotations

from app._compat import UTC
from app.national.base import BaseEntity, _ulid
from app.national.document_platform.domain.enums import (
    DocumentCategory,
    DocumentFormat,
    DocumentStatus,
    RetentionPolicy,
    SignatureStatus,
)
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)


class NationalDocumentModel(BaseEntity):
    __tablename__ = "national_documents"

    id = Column(String(26), primary_key=True, default=_ulid)
    filename = Column(String(512), nullable=False, index=True)
    original_name = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    format = Column(SAEnum(DocumentFormat), nullable=False, default=DocumentFormat.OTHER, index=True)
    size_bytes = Column(Integer, nullable=False, default=0)
    hash_sha256 = Column(String(64), nullable=False, default="", index=True)
    version = Column(Integer, nullable=False, default=1)
    category = Column(SAEnum(DocumentCategory), nullable=False, default=DocumentCategory.OTHER, index=True)
    status = Column(SAEnum(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT, index=True)
    tags = Column(JSON, nullable=True, default=list)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    retention_policy = Column(SAEnum(RetentionPolicy), nullable=False, default=RetentionPolicy.STANDARD_1Y)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_nat_docs_status_category", "status", "category"),
        Index("ix_nat_docs_category_format", "category", "format"),
        Index("ix_nat_docs_created_by_status", "created_by", "status"),
        Index("ix_nat_docs_expires_at", "expires_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.document_platform.domain.entities import Document

        return Document(
            id=self.id,
            filename=self.filename,
            original_name=self.original_name,
            mime_type=self.mime_type,
            format=self.format,
            size_bytes=self.size_bytes,
            hash_sha256=self.hash_sha256 or "",
            version=self.version,
            category=self.category,
            status=self.status,
            tags=self.tags or [],
            metadata=self.metadata_ or {},
            retention_policy=self.retention_policy,
            expires_at=self.expires_at,
            created_by=self.created_by or "",
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
            deleted_at=self.deleted_at,
        )


class NationalDocumentVersionModel(BaseEntity):
    __tablename__ = "national_document_versions"

    id = Column(String(26), primary_key=True, default=_ulid)
    document_id = Column(String(26), ForeignKey("national_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    filename = Column(String(512), nullable=False, default="")
    size_bytes = Column(Integer, nullable=False, default=0)
    hash_sha256 = Column(String(64), nullable=False, default="")
    created_by = Column(String(100), nullable=True)
    change_summary = Column(Text, nullable=True, default="")

    __table_args__ = (
        Index("ix_nat_doc_ver_doc_version", "document_id", "version_number", unique=True),
        Index("ix_nat_doc_ver_doc_created", "document_id", "created_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.document_platform.domain.entities import DocumentVersion

        return DocumentVersion(
            id=self.id,
            document_id=self.document_id,
            version_number=self.version_number,
            filename=self.filename,
            size_bytes=self.size_bytes,
            hash_sha256=self.hash_sha256 or "",
            created_by=self.created_by or "",
            created_at=self.created_at,
            change_summary=self.change_summary or "",
        )


class NationalElectronicSignatureModel(BaseEntity):
    __tablename__ = "national_electronic_signatures"

    id = Column(String(26), primary_key=True, default=_ulid)
    document_id = Column(String(26), ForeignKey("national_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    signer_id = Column(String(100), nullable=False, index=True)
    signer_name = Column(String(255), nullable=False, default="")
    signer_role = Column(String(100), nullable=True, default="")
    signature_type = Column(String(50), nullable=False, default="electronic")
    certificate_id = Column(String(255), nullable=True, default="")
    signed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    verification_url = Column(String(512), nullable=True, default="")
    signature_value = Column(Text, nullable=True, default="")
    status = Column(SAEnum(SignatureStatus), nullable=False, default=SignatureStatus.PENDING)
    hash_chain_previous = Column(String(64), nullable=False, default="")
    hash_chain_current = Column(String(64), nullable=False, default="")

    __table_args__ = (
        Index("ix_nat_sig_doc_signer", "document_id", "signer_id"),
        Index("ix_nat_sig_signer_status", "signer_id", "status"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.document_platform.domain.entities import ElectronicSignature

        return ElectronicSignature(
            id=self.id,
            document_id=self.document_id,
            signer_id=self.signer_id,
            signer_name=self.signer_name,
            signer_role=self.signer_role or "",
            signature_type=self.signature_type,
            certificate_id=self.certificate_id or "",
            signed_at=self.signed_at,
            expires_at=self.expires_at,
            verification_url=self.verification_url or "",
            signature_value=self.signature_value or "",
            status=self.status,
            hash_chain_previous=self.hash_chain_previous,
            hash_chain_current=self.hash_chain_current,
        )


class NationalDocumentQRCodeModel(BaseEntity):
    __tablename__ = "national_document_qr_codes"

    id = Column(String(26), primary_key=True, default=_ulid)
    document_id = Column(String(26), ForeignKey("national_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    qr_data = Column(Text, nullable=False, default="")
    verification_url = Column(String(512), nullable=True, default="")
    generated_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scanned_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_nat_qr_doc_id", "document_id", unique=True),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.document_platform.domain.entities import DocumentQRCode

        return DocumentQRCode(
            id=self.id,
            document_id=self.document_id,
            qr_data=self.qr_data,
            verification_url=self.verification_url or "",
            generated_at=self.generated_at,
            expires_at=self.expires_at,
            scanned_count=self.scanned_count,
        )


class NationalDocumentAttachmentModel(BaseEntity):
    __tablename__ = "national_document_attachments"

    id = Column(String(26), primary_key=True, default=_ulid)
    document_id = Column(String(26), ForeignKey("national_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(512), nullable=False, default="")
    size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(128), nullable=False, default="")
    storage_path = Column(String(1024), nullable=False, default="")

    __table_args__ = (
        Index("ix_nat_att_doc_id", "document_id"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.document_platform.domain.entities import DocumentAttachment

        return DocumentAttachment(
            id=self.id,
            document_id=self.document_id,
            filename=self.filename,
            size_bytes=self.size_bytes,
            mime_type=self.mime_type,
            storage_path=self.storage_path,
            created_at=self.created_at,
        )


class NationalRetentionRuleModel(BaseEntity):
    __tablename__ = "national_retention_rules"

    id = Column(String(26), primary_key=True, default=_ulid)
    category = Column(SAEnum(DocumentCategory), nullable=False, unique=True, index=True)
    policy = Column(SAEnum(RetentionPolicy), nullable=False, default=RetentionPolicy.STANDARD_1Y)
    retention_days = Column(Integer, nullable=False, default=365)
    action_at = Column(DateTime(timezone=True), nullable=True)
    archive_required = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_nat_ret_cat_policy", "category", "policy"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.document_platform.domain.entities import RetentionRule

        return RetentionRule(
            id=self.id,
            category=self.category,
            policy=self.policy,
            retention_days=self.retention_days,
            action_at=self.action_at,
            archive_required=self.archive_required,
            created_at=self.created_at,
        )
