from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.national.document_platform.application.interfaces import (
    PDFGenerator,
    QRCodeGenerator,
    SignatureVerifier,
    StorageAdapter,
)
from app.national.document_platform.domain.entities import (
    Document,
    DocumentAttachment,
    DocumentQRCode,
    DocumentVersion,
    ElectronicSignature,
)
from app.national.document_platform.domain.enums import (
    DocumentCategory,
    DocumentFormat,
    DocumentStatus,
    RetentionPolicy,
    SignatureStatus,
)
from app.national.document_platform.domain.events import (
    DocumentArchivedEvent,
    DocumentCreatedEvent,
    DocumentDeletedEvent,
    DocumentExpiredEvent,
    DocumentRetentionTriggeredEvent,
    DocumentSignedEvent,
    DocumentUpdatedEvent,
    DocumentVerifiedEvent,
    DocumentVersionedEvent,
)
from app.national.document_platform.domain.repository import (
    DocumentAttachmentRepository,
    DocumentQRCodeRepository,
    DocumentRepository,
    DocumentVersionRepository,
    ElectronicSignatureRepository,
    RetentionRuleRepository,
)
from app.national.document_platform.exceptions import (
    DocumentNotFoundError,
    DocumentStateTransitionError,
    DocumentValidationError,
    SignatureNotFoundError,
    SignatureVerificationError,
)

logger = logging.getLogger("gula.national.document_platform")


class DocumentPlatformService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        version_repository: DocumentVersionRepository,
        signature_repository: ElectronicSignatureRepository,
        qr_code_repository: DocumentQRCodeRepository,
        attachment_repository: DocumentAttachmentRepository,
        retention_rule_repository: RetentionRuleRepository,
        event_bus: EventBus,
        storage_adapter: StorageAdapter | None = None,
        signature_verifier: SignatureVerifier | None = None,
        qr_generator: QRCodeGenerator | None = None,
        pdf_generator: PDFGenerator | None = None,
    ) -> None:
        self.document_repository = document_repository
        self.version_repository = version_repository
        self.signature_repository = signature_repository
        self.qr_code_repository = qr_code_repository
        self.attachment_repository = attachment_repository
        self.retention_rule_repository = retention_rule_repository
        self.event_bus = event_bus
        self.storage_adapter = storage_adapter
        self.signature_verifier = signature_verifier
        self.qr_generator = qr_generator
        self.pdf_generator = pdf_generator

    async def create_document(
        self,
        filename: str,
        original_name: str,
        mime_type: str,
        format: DocumentFormat = DocumentFormat.OTHER,
        size_bytes: int = 0,
        hash_sha256: str = "",
        category: DocumentCategory = DocumentCategory.OTHER,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        retention_policy: RetentionPolicy = RetentionPolicy.STANDARD_1Y,
        expires_at: datetime | None = None,
        created_by: str = "",
    ) -> Document:
        document = Document(
            id=str(uuid.uuid4()),
            filename=filename,
            original_name=original_name,
            mime_type=mime_type,
            format=format,
            size_bytes=size_bytes,
            hash_sha256=hash_sha256 or self._compute_hash(filename.encode()),
            version=1,
            category=category,
            status=DocumentStatus.DRAFT,
            tags=tags or [],
            metadata=metadata or {},
            retention_policy=retention_policy,
            expires_at=expires_at,
            created_by=created_by,
        )

        errors = self._validate_document(document)
        if errors:
            raise DocumentValidationError(document.id, "; ".join(errors))

        if expires_at and expires_at < datetime.now(UTC):
            raise DocumentValidationError(document.id, "expires_at must be in the future")

        saved = await self.document_repository.save(document)

        self._publish_event(
            DocumentCreatedEvent(
                document_id=saved.id,
                filename=saved.filename,
                category=saved.category,
                format=saved.format,
                aggregate_id=saved.id,
                payload={
                    "filename": saved.filename,
                    "category": saved.category.value,
                    "format": saved.format.value,
                    "size_bytes": saved.size_bytes,
                },
            ),
        )

        return saved

    async def get_document(self, document_id: str) -> Document:
        document = await self.document_repository.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        return document

    async def update_document(
        self,
        document_id: str,
        updates: dict[str, Any],
    ) -> Document:
        document = await self.get_document(document_id)
        if document.status in (DocumentStatus.DELETED, DocumentStatus.ARCHIVED):
            raise DocumentStateTransitionError(
                document_id,
                document.status.value,
                "update",
            )

        changes: dict[str, Any] = {}
        for key, value in updates.items():
            if hasattr(document, key) and key not in (
                "id",
                "created_at",
                "version",
                "is_deleted",
                "deleted_at",
            ):
                old_val = getattr(document, key)
                if key == "category" and isinstance(value, str):
                    value = DocumentCategory(value)
                elif key == "format" and isinstance(value, str):
                    value = DocumentFormat(value)
                elif key == "status" and isinstance(value, str):
                    value = DocumentStatus(value)
                elif key == "retention_policy" and isinstance(value, str):
                    value = RetentionPolicy(value)
                setattr(document, key, value)
                if old_val != value:
                    changes[key] = {
                        "from": str(old_val) if not isinstance(old_val, (list, dict)) else old_val,
                        "to": str(value) if not isinstance(value, (list, dict)) else value,
                    }

        document.version += 1
        document.updated_at = datetime.now(UTC)
        saved = await self.document_repository.save(document)

        self._publish_event(
            DocumentUpdatedEvent(
                document_id=saved.id,
                changes=changes,
                aggregate_id=saved.id,
                payload={"changes": changes},
            ),
        )

        return saved

    async def create_version(
        self,
        document_id: str,
        filename: str,
        size_bytes: int = 0,
        hash_sha256: str = "",
        created_by: str = "",
        change_summary: str = "",
    ) -> DocumentVersion:
        document = await self.get_document(document_id)
        if document.status in (DocumentStatus.DELETED, DocumentStatus.ARCHIVED):
            raise DocumentStateTransitionError(
                document_id,
                document.status.value,
                "create_version",
            )

        existing_versions = await self.version_repository.list(document_id, limit=1000)
        next_version = max((v.version_number for v in existing_versions), default=0) + 1

        version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=document_id,
            version_number=next_version,
            filename=filename,
            size_bytes=size_bytes,
            hash_sha256=hash_sha256,
            created_by=created_by,
            change_summary=change_summary,
        )

        saved = await self.version_repository.save(version)

        document.version = next_version
        document.updated_at = datetime.now(UTC)
        document.hash_sha256 = hash_sha256 or document.hash_sha256
        await self.document_repository.save(document)

        self._publish_event(
            DocumentVersionedEvent(
                document_id=document_id,
                version_id=saved.id,
                version_number=saved.version_number,
                aggregate_id=document_id,
                payload={
                    "version_id": saved.id,
                    "version_number": saved.version_number,
                    "change_summary": saved.change_summary,
                },
            ),
        )

        return saved

    async def sign_document(
        self,
        document_id: str,
        signer_id: str,
        signer_name: str,
        signer_role: str = "",
        signature_type: str = "electronic",
        certificate_id: str = "",
        verification_url: str = "",
    ) -> ElectronicSignature:
        document = await self.get_document(document_id)
        if document.status in (DocumentStatus.DELETED, DocumentStatus.ARCHIVED):
            raise DocumentStateTransitionError(
                document_id,
                document.status.value,
                "sign",
            )

        existing_signatures = await self.signature_repository.list(document_id, limit=1000)
        previous_hash = (
            existing_signatures[-1].hash_chain_current
            if existing_signatures
            else document.hash_sha256
        )

        hash_input = f"{previous_hash}:{signer_id}:{document_id}:{datetime.now(UTC).isoformat()}"
        current_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        signature = ElectronicSignature(
            id=str(uuid.uuid4()),
            document_id=document_id,
            signer_id=signer_id,
            signer_name=signer_name,
            signer_role=signer_role,
            signature_type=signature_type,
            certificate_id=certificate_id,
            signed_at=datetime.now(UTC),
            verification_url=verification_url,
            signature_value=current_hash,
            status=SignatureStatus.SIGNED,
            hash_chain_previous=previous_hash,
            hash_chain_current=current_hash,
        )

        saved = await self.signature_repository.save(signature)

        document.status = DocumentStatus.FINAL
        document.updated_at = datetime.now(UTC)
        await self.document_repository.save(document)

        self._publish_event(
            DocumentSignedEvent(
                document_id=document_id,
                signature_id=saved.id,
                signer_id=saved.signer_id,
                signer_name=saved.signer_name,
                aggregate_id=document_id,
                payload={
                    "signature_id": saved.id,
                    "signer_id": saved.signer_id,
                    "signer_name": saved.signer_name,
                    "hash_chain_current": saved.hash_chain_current,
                },
            ),
        )

        return saved

    async def verify_signature(
        self,
        document_id: str,
        signature_id: str,
    ) -> dict[str, Any]:
        document = await self.get_document(document_id)
        signature = await self.signature_repository.get(signature_id)
        if not signature:
            raise SignatureNotFoundError(signature_id)
        if signature.document_id != document_id:
            raise SignatureVerificationError(
                signature_id, "Signature does not belong to this document",
            )

        if signature.status == SignatureStatus.EXPIRED:
            return {"valid": False, "reason": "Signature has expired", "signature_id": signature_id}

        if signature.status == SignatureStatus.REVOKED:
            return {
                "valid": False,
                "reason": "Signature has been revoked",
                "signature_id": signature_id,
            }

        hash_input = (
            f"{signature.hash_chain_previous}:{signature.signer_id}:{document_id}:{signature.signed_at.isoformat()}"
            if signature.signed_at
            else ""
        )
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest() if hash_input else ""
        hash_valid = signature.signature_value == expected_hash

        external_valid = True
        if self.signature_verifier and signature.certificate_id:
            try:
                result = await self.signature_verifier.verify(
                    document.hash_sha256,
                    signature.signature_value,
                    signature.certificate_id,
                )
                external_valid = result.get("valid", True)
            except Exception as exc:
                logger.error("External signature verification failed: %s", exc)
                external_valid = False

        valid = hash_valid and external_valid

        if valid and signature.status == SignatureStatus.SIGNED:
            signature.status = SignatureStatus.VERIFIED
            await self.signature_repository.save(signature)

        self._publish_event(
            DocumentVerifiedEvent(
                document_id=document_id,
                signature_id=signature_id,
                valid=valid,
                aggregate_id=document_id,
                payload={
                    "signature_id": signature_id,
                    "valid": valid,
                    "hash_valid": hash_valid,
                    "external_valid": external_valid,
                },
            ),
        )

        return {
            "valid": valid,
            "hash_valid": hash_valid,
            "external_valid": external_valid,
            "signature_id": signature_id,
            "signature_status": signature.status.value,
        }

    async def generate_qr(
        self,
        document_id: str,
        expires_in_days: int = 365,
    ) -> DocumentQRCode:
        document = await self.get_document(document_id)

        existing = await self.qr_code_repository.get_by_document(document_id)
        if existing:
            return existing

        verification_url = f"/national/documents/{document_id}/verify"
        qr_data = f"gula:doc:{document_id}:{document.hash_sha256}:{datetime.now(UTC).isoformat()}"

        qr_encoded = qr_data
        if self.qr_generator:
            try:
                qr_encoded = await self.qr_generator.generate(qr_data)
            except Exception as exc:
                logger.error("QR generation failed, using raw data: %s", exc)

        qr_code = DocumentQRCode(
            id=str(uuid.uuid4()),
            document_id=document_id,
            qr_data=qr_encoded,
            verification_url=verification_url,
            generated_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
            scanned_count=0,
        )

        return await self.qr_code_repository.save(qr_code)

    async def verify_qr(
        self,
        qr_data: str,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"valid": False, "document_id": None}

        if self.qr_generator:
            try:
                verified = await self.qr_generator.verify(qr_data)
                if verified.get("valid"):
                    result["valid"] = True
                    result["document_id"] = verified.get("document_id")
                    return result
            except Exception as exc:
                logger.error("QR verification via generator failed: %s", exc)

        if qr_data.startswith("gula:doc:"):
            parts = qr_data.split(":")
            if len(parts) >= 3:
                doc_id = parts[2]
                document = await self.document_repository.get(doc_id)
                if document:
                    result["valid"] = True
                    result["document_id"] = doc_id
                    result["filename"] = document.filename
                    result["hash_sha256"] = document.hash_sha256
                    result["status"] = document.status.value

        return result

    async def export_pdf(
        self,
        document_id: str,
        template: str = "",
    ) -> bytes:
        document = await self.get_document(document_id)

        if not self.pdf_generator:
            raise DocumentValidationError(document_id, "PDF generator not configured")

        content = {
            "id": document.id,
            "filename": document.filename,
            "original_name": document.original_name,
            "category": document.category.value,
            "status": document.status.value,
            "version": document.version,
            "tags": document.tags,
            "metadata": document.metadata,
            "created_by": document.created_by,
            "created_at": document.created_at.isoformat() if document.created_at else "",
        }

        try:
            return await self.pdf_generator.generate(content, template=template)
        except Exception as exc:
            raise DocumentValidationError(document_id, f"PDF generation failed: {exc}") from exc

    async def add_attachment(
        self,
        document_id: str,
        filename: str,
        size_bytes: int,
        mime_type: str,
        storage_path: str = "",
    ) -> DocumentAttachment:
        document = await self.get_document(document_id)
        if document.status in (DocumentStatus.DELETED, DocumentStatus.ARCHIVED):
            raise DocumentStateTransitionError(
                document_id,
                document.status.value,
                "add_attachment",
            )

        attachment = DocumentAttachment(
            id=str(uuid.uuid4()),
            document_id=document_id,
            filename=filename,
            size_bytes=size_bytes,
            mime_type=mime_type,
            storage_path=storage_path,
        )

        return await self.attachment_repository.save(attachment)

    async def get_attachments(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentAttachment]:
        await self.get_document(document_id)
        return await self.attachment_repository.list(document_id, skip=skip, limit=limit)

    async def archive_document(
        self,
        document_id: str,
        reason: str = "",
    ) -> Document:
        document = await self.get_document(document_id)
        if document.status == DocumentStatus.ARCHIVED:
            raise DocumentStateTransitionError(
                document_id,
                document.status.value,
                DocumentStatus.ARCHIVED.value,
            )

        document.status = DocumentStatus.ARCHIVED
        document.updated_at = datetime.now(UTC)
        saved = await self.document_repository.save(document)

        self._publish_event(
            DocumentArchivedEvent(
                document_id=document_id,
                reason=reason,
                aggregate_id=document_id,
                payload={"reason": reason},
            ),
        )

        return saved

    async def delete_document(
        self,
        document_id: str,
        reason: str = "",
    ) -> None:
        document = await self.get_document(document_id)
        if document.status == DocumentStatus.DELETED:
            raise DocumentStateTransitionError(
                document_id,
                document.status.value,
                DocumentStatus.DELETED.value,
            )

        document.status = DocumentStatus.DELETED
        document.is_deleted = True
        document.deleted_at = datetime.now(UTC)
        document.updated_at = datetime.now(UTC)
        await self.document_repository.save(document)

        self._publish_event(
            DocumentDeletedEvent(
                document_id=document_id,
                reason=reason,
                aggregate_id=document_id,
                payload={"reason": reason},
            ),
        )

    async def apply_retention_policy(
        self,
        document_id: str,
    ) -> dict[str, Any]:
        document = await self.get_document(document_id)

        rule = await self.retention_rule_repository.find_by_category(document.category)

        result: dict[str, Any] = {
            "document_id": document_id,
            "current_policy": document.retention_policy.value,
            "action": "none",
        }

        if not rule:
            return result

        if rule.policy == RetentionPolicy.LEGAL_HOLD:
            result["action"] = "legal_hold_applied"
            result["note"] = "Document placed on legal hold"
            return result

        if rule.policy == RetentionPolicy.INDEFINITE:
            result["action"] = "indefinite_retention"
            return result

        age_days = (datetime.now(UTC) - document.created_at).days if document.created_at else 0
        if age_days >= rule.retention_days:
            if rule.archive_required:
                document.status = DocumentStatus.ARCHIVED
                result["action"] = "archived"
            else:
                document.status = DocumentStatus.DELETED
                document.is_deleted = True
                document.deleted_at = datetime.now(UTC)
                result["action"] = "deleted"

            document.updated_at = datetime.now(UTC)
            await self.document_repository.save(document)

            self._publish_event(
                DocumentRetentionTriggeredEvent(
                    document_id=document_id,
                    rule_id=rule.id,
                    policy=rule.policy,
                    aggregate_id=document_id,
                    payload={
                        "rule_id": rule.id,
                        "policy": rule.policy.value,
                        "action": result["action"],
                        "retention_days": rule.retention_days,
                        "age_days": age_days,
                    },
                ),
            )

        return result

    async def get_document_history(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        document = await self.get_document(document_id)
        versions = await self.version_repository.list(document_id, skip=skip, limit=limit)
        signatures = await self.signature_repository.list(document_id)

        history: list[dict[str, Any]] = [
            {
                "type": "created",
                "timestamp": document.created_at.isoformat() if document.created_at else "",
                "by": document.created_by,
                "details": {"filename": document.filename, "category": document.category.value},
            },
        ]

        for v in versions:
            history.append(
                {
                    "type": "versioned",
                    "timestamp": v.created_at.isoformat() if v.created_at else "",
                    "by": v.created_by,
                    "details": {
                        "version_number": v.version_number,
                        "change_summary": v.change_summary,
                        "filename": v.filename,
                    },
                },
            )

        for s in signatures:
            history.append(
                {
                    "type": "signature",
                    "timestamp": s.signed_at.isoformat() if s.signed_at else "",
                    "by": s.signer_name,
                    "details": {
                        "signer_id": s.signer_id,
                        "signer_role": s.signer_role,
                        "signature_type": s.signature_type,
                        "status": s.status.value,
                    },
                },
            )

        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "document_id": document_id,
            "current_version": document.version,
            "current_status": document.status.value,
            "total_versions": len(versions),
            "total_signatures": len(signatures),
            "history": history,
        }

    async def search_documents(
        self,
        query: str | None = None,
        status: str | None = None,
        category: str | None = None,
        format: str | None = None,
        tags: list[str] | None = None,
        created_by: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = DocumentStatus(status)
        if category:
            filters["category"] = DocumentCategory(category)
        if format:
            filters["format"] = DocumentFormat(format)
        if created_by:
            filters["created_by"] = created_by

        if query:
            return await self.document_repository.search(query, skip=skip, limit=limit)

        documents = await self.document_repository.list(skip=skip, limit=limit, **filters)

        if tags:
            documents = [d for d in documents if any(t in d.tags for t in tags)]

        return documents

    async def get_expired_documents(self) -> list[Document]:
        datetime.now(UTC)
        return await self.document_repository.list(
            skip=0,
            limit=1000,
            status=DocumentStatus.FINAL,
        )

    async def process_expired_documents(self) -> list[str]:
        expired: list[str] = []
        documents = await self.document_repository.list(skip=0, limit=1000)
        now = datetime.now(UTC)

        for doc in documents:
            if (
                doc.expires_at
                and doc.expires_at <= now
                and doc.status not in (DocumentStatus.DELETED, DocumentStatus.ARCHIVED)
            ):
                doc.status = DocumentStatus.ARCHIVED
                doc.updated_at = now
                await self.document_repository.save(doc)

                self._publish_event(
                    DocumentExpiredEvent(
                        document_id=doc.id,
                        filename=doc.filename,
                        aggregate_id=doc.id,
                        payload={
                            "expires_at": doc.expires_at.isoformat() if doc.expires_at else "",
                        },
                    ),
                )
                expired.append(doc.id)

        return expired

    def _validate_document(self, document: Document) -> list[str]:
        errors: list[str] = []
        if not document.filename or not document.filename.strip():
            errors.append("Filename is required")
        if not document.original_name or not document.original_name.strip():
            errors.append("Original name is required")
        if document.size_bytes < 0:
            errors.append("size_bytes must be >= 0")
        if document.version < 1:
            errors.append("version must be >= 1")
        return errors

    def _compute_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _publish_event(self, domain_event: Any) -> None:
        try:
            event = Event(
                name=domain_event.event_type,
                data=domain_event.payload if hasattr(domain_event, "payload") else {},
                correlation_id=getattr(domain_event, "correlation_id", ""),
                tenant_id=getattr(domain_event, "tenant_id", ""),
            )
            self.event_bus.publish(event)
        except Exception as exc:
            logger.error(
                "Failed to publish event %s: %s",
                getattr(domain_event, "event_type", "unknown"),
                exc,
            )
