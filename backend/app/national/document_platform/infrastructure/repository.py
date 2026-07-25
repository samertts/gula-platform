from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.document_platform.domain.entities import (
    Document,
    DocumentAttachment,
    DocumentQRCode,
    DocumentVersion,
    ElectronicSignature,
    RetentionRule,
)
from app.national.document_platform.domain.enums import DocumentCategory, DocumentStatus
from app.national.document_platform.domain.repository import (
    DocumentAttachmentRepository,
    DocumentQRCodeRepository,
    DocumentRepository,
    DocumentVersionRepository,
    ElectronicSignatureRepository,
    RetentionRuleRepository,
)
from app.national.document_platform.infrastructure.models import (
    NationalDocumentAttachmentModel,
    NationalDocumentModel,
    NationalDocumentQRCodeModel,
    NationalDocumentVersionModel,
    NationalElectronicSignatureModel,
    NationalRetentionRuleModel,
)


class SQLAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, document: Document) -> Document:
        model = (
            self.db.query(NationalDocumentModel)
            .filter(NationalDocumentModel.id == document.id)
            .first()
        )
        if model:
            model.filename = document.filename
            model.original_name = document.original_name
            model.mime_type = document.mime_type
            model.format = document.format
            model.size_bytes = document.size_bytes
            model.hash_sha256 = document.hash_sha256
            model.version = document.version
            model.category = document.category
            model.status = document.status
            model.tags = document.tags
            model.metadata_ = document.metadata
            model.retention_policy = document.retention_policy
            model.expires_at = document.expires_at
            model.created_by = document.created_by
            model.is_deleted = document.is_deleted
            model.deleted_at = document.deleted_at
        else:
            model = NationalDocumentModel(
                id=document.id,
                filename=document.filename,
                original_name=document.original_name,
                mime_type=document.mime_type,
                format=document.format,
                size_bytes=document.size_bytes,
                hash_sha256=document.hash_sha256,
                version=document.version,
                category=document.category,
                status=document.status,
                tags=document.tags,
                metadata_=document.metadata,
                retention_policy=document.retention_policy,
                expires_at=document.expires_at,
                created_by=document.created_by,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, document_id: str) -> Document | None:
        model = (
            self.db.query(NationalDocumentModel)
            .filter(
                NationalDocumentModel.id == document_id,
                ~NationalDocumentModel.is_deleted,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Document]:
        query = self.db.query(NationalDocumentModel).filter(~~NationalDocumentModel.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalDocumentModel, key) and value is not None:
                query = query.filter(getattr(NationalDocumentModel, key) == value)
        models = (
            query.order_by(NationalDocumentModel.created_at.desc()).offset(skip).limit(limit).all()
        )
        return [m.to_domain() for m in models]

    async def delete(self, document_id: str, soft: bool = True) -> None:
        model = (
            self.db.query(NationalDocumentModel)
            .filter(
                NationalDocumentModel.id == document_id,
                ~NationalDocumentModel.is_deleted,
            )
            .first()
        )
        if model:
            if soft:
                model.is_deleted = True
                model.deleted_at = datetime.now(UTC)
            else:
                self.db.delete(model)
            self.db.commit()

    async def find_by_status(
        self,
        status: DocumentStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        models = (
            self.db.query(NationalDocumentModel)
            .filter(
                NationalDocumentModel.status == status,
                ~NationalDocumentModel.is_deleted,
            )
            .order_by(NationalDocumentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def find_by_category(
        self,
        category: DocumentCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        models = (
            self.db.query(NationalDocumentModel)
            .filter(
                NationalDocumentModel.category == category,
                ~NationalDocumentModel.is_deleted,
            )
            .order_by(NationalDocumentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        search_term = f"%{query}%"
        models = (
            self.db.query(NationalDocumentModel)
            .filter(
                ~~NationalDocumentModel.is_deleted,
                or_(
                    NationalDocumentModel.filename.ilike(search_term),
                    NationalDocumentModel.original_name.ilike(search_term),
                ),
            )
            .order_by(NationalDocumentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def count(self, **filters: Any) -> int:
        query = self.db.query(NationalDocumentModel).filter(~~NationalDocumentModel.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalDocumentModel, key) and value is not None:
                query = query.filter(getattr(NationalDocumentModel, key) == value)
        return query.count()


class SQLAlchemyDocumentVersionRepository(DocumentVersionRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, version: DocumentVersion) -> DocumentVersion:
        model = (
            self.db.query(NationalDocumentVersionModel)
            .filter(NationalDocumentVersionModel.id == version.id)
            .first()
        )
        if model:
            model.document_id = version.document_id
            model.version_number = version.version_number
            model.filename = version.filename
            model.size_bytes = version.size_bytes
            model.hash_sha256 = version.hash_sha256
            model.created_by = version.created_by
            model.change_summary = version.change_summary
        else:
            model = NationalDocumentVersionModel(
                id=version.id,
                document_id=version.document_id,
                version_number=version.version_number,
                filename=version.filename,
                size_bytes=version.size_bytes,
                hash_sha256=version.hash_sha256,
                created_by=version.created_by,
                change_summary=version.change_summary,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, version_id: str) -> DocumentVersion | None:
        model = (
            self.db.query(NationalDocumentVersionModel)
            .filter(
                NationalDocumentVersionModel.id == version_id,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentVersion]:
        models = (
            self.db.query(NationalDocumentVersionModel)
            .filter(
                NationalDocumentVersionModel.document_id == document_id,
            )
            .order_by(NationalDocumentVersionModel.version_number.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def delete(self, version_id: str) -> None:
        model = (
            self.db.query(NationalDocumentVersionModel)
            .filter(
                NationalDocumentVersionModel.id == version_id,
            )
            .first()
        )
        if model:
            self.db.delete(model)
            self.db.commit()


class SQLAlchemyElectronicSignatureRepository(ElectronicSignatureRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, signature: ElectronicSignature) -> ElectronicSignature:
        model = (
            self.db.query(NationalElectronicSignatureModel)
            .filter(NationalElectronicSignatureModel.id == signature.id)
            .first()
        )
        if model:
            model.document_id = signature.document_id
            model.signer_id = signature.signer_id
            model.signer_name = signature.signer_name
            model.signer_role = signature.signer_role
            model.signature_type = signature.signature_type
            model.certificate_id = signature.certificate_id
            model.signed_at = signature.signed_at
            model.expires_at = signature.expires_at
            model.verification_url = signature.verification_url
            model.signature_value = signature.signature_value
            model.status = signature.status
            model.hash_chain_previous = signature.hash_chain_previous
            model.hash_chain_current = signature.hash_chain_current
        else:
            model = NationalElectronicSignatureModel(
                id=signature.id,
                document_id=signature.document_id,
                signer_id=signature.signer_id,
                signer_name=signature.signer_name,
                signer_role=signature.signer_role,
                signature_type=signature.signature_type,
                certificate_id=signature.certificate_id,
                signed_at=signature.signed_at,
                expires_at=signature.expires_at,
                verification_url=signature.verification_url,
                signature_value=signature.signature_value,
                status=signature.status,
                hash_chain_previous=signature.hash_chain_previous,
                hash_chain_current=signature.hash_chain_current,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, signature_id: str) -> ElectronicSignature | None:
        model = (
            self.db.query(NationalElectronicSignatureModel)
            .filter(
                NationalElectronicSignatureModel.id == signature_id,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ElectronicSignature]:
        models = (
            self.db.query(NationalElectronicSignatureModel)
            .filter(
                NationalElectronicSignatureModel.document_id == document_id,
            )
            .order_by(NationalElectronicSignatureModel.signed_at.desc().nullslast())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def find_by_signer(
        self,
        signer_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ElectronicSignature]:
        models = (
            self.db.query(NationalElectronicSignatureModel)
            .filter(
                NationalElectronicSignatureModel.signer_id == signer_id,
            )
            .order_by(NationalElectronicSignatureModel.signed_at.desc().nullslast())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]


class SQLAlchemyDocumentQRCodeRepository(DocumentQRCodeRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, qr_code: DocumentQRCode) -> DocumentQRCode:
        model = (
            self.db.query(NationalDocumentQRCodeModel)
            .filter(NationalDocumentQRCodeModel.id == qr_code.id)
            .first()
        )
        if model:
            model.document_id = qr_code.document_id
            model.qr_data = qr_code.qr_data
            model.verification_url = qr_code.verification_url
            model.generated_at = qr_code.generated_at
            model.expires_at = qr_code.expires_at
            model.scanned_count = qr_code.scanned_count
        else:
            model = NationalDocumentQRCodeModel(
                id=qr_code.id,
                document_id=qr_code.document_id,
                qr_data=qr_code.qr_data,
                verification_url=qr_code.verification_url,
                generated_at=qr_code.generated_at,
                expires_at=qr_code.expires_at,
                scanned_count=qr_code.scanned_count,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, qr_code_id: str) -> DocumentQRCode | None:
        model = (
            self.db.query(NationalDocumentQRCodeModel)
            .filter(
                NationalDocumentQRCodeModel.id == qr_code_id,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def get_by_document(self, document_id: str) -> DocumentQRCode | None:
        model = (
            self.db.query(NationalDocumentQRCodeModel)
            .filter(
                NationalDocumentQRCodeModel.document_id == document_id,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def increment_scanned(self, qr_code_id: str) -> None:
        model = (
            self.db.query(NationalDocumentQRCodeModel)
            .filter(
                NationalDocumentQRCodeModel.id == qr_code_id,
            )
            .first()
        )
        if model:
            model.scanned_count = (model.scanned_count or 0) + 1
            self.db.commit()


class SQLAlchemyDocumentAttachmentRepository(DocumentAttachmentRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, attachment: DocumentAttachment) -> DocumentAttachment:
        model = (
            self.db.query(NationalDocumentAttachmentModel)
            .filter(NationalDocumentAttachmentModel.id == attachment.id)
            .first()
        )
        if model:
            model.document_id = attachment.document_id
            model.filename = attachment.filename
            model.size_bytes = attachment.size_bytes
            model.mime_type = attachment.mime_type
            model.storage_path = attachment.storage_path
        else:
            model = NationalDocumentAttachmentModel(
                id=attachment.id,
                document_id=attachment.document_id,
                filename=attachment.filename,
                size_bytes=attachment.size_bytes,
                mime_type=attachment.mime_type,
                storage_path=attachment.storage_path,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, attachment_id: str) -> DocumentAttachment | None:
        model = (
            self.db.query(NationalDocumentAttachmentModel)
            .filter(
                NationalDocumentAttachmentModel.id == attachment_id,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentAttachment]:
        models = (
            self.db.query(NationalDocumentAttachmentModel)
            .filter(
                NationalDocumentAttachmentModel.document_id == document_id,
            )
            .order_by(NationalDocumentAttachmentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def delete(self, attachment_id: str) -> None:
        model = (
            self.db.query(NationalDocumentAttachmentModel)
            .filter(
                NationalDocumentAttachmentModel.id == attachment_id,
            )
            .first()
        )
        if model:
            self.db.delete(model)
            self.db.commit()


class SQLAlchemyRetentionRuleRepository(RetentionRuleRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, rule: RetentionRule) -> RetentionRule:
        model = (
            self.db.query(NationalRetentionRuleModel)
            .filter(NationalRetentionRuleModel.id == rule.id)
            .first()
        )
        if model:
            model.category = rule.category
            model.policy = rule.policy
            model.retention_days = rule.retention_days
            model.action_at = rule.action_at
            model.archive_required = rule.archive_required
        else:
            model = NationalRetentionRuleModel(
                id=rule.id,
                category=rule.category,
                policy=rule.policy,
                retention_days=rule.retention_days,
                action_at=rule.action_at,
                archive_required=rule.archive_required,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, rule_id: str) -> RetentionRule | None:
        model = (
            self.db.query(NationalRetentionRuleModel)
            .filter(
                NationalRetentionRuleModel.id == rule_id,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def find_by_category(self, category: DocumentCategory) -> RetentionRule | None:
        model = (
            self.db.query(NationalRetentionRuleModel)
            .filter(
                NationalRetentionRuleModel.category == category,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RetentionRule]:
        models = (
            self.db.query(NationalRetentionRuleModel)
            .order_by(
                NationalRetentionRuleModel.category,
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def delete(self, rule_id: str) -> None:
        model = (
            self.db.query(NationalRetentionRuleModel)
            .filter(
                NationalRetentionRuleModel.id == rule_id,
            )
            .first()
        )
        if model:
            self.db.delete(model)
            self.db.commit()
