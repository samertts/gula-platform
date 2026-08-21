from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.models.clinical_document import ClinicalDocument


class ClinicalDocumentService:
    """Durable document commands behind the canonical clinical access context."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        access: ClinicalAccessContext,
        patient_id: str,
        encounter_id: str | None,
        document_type: str,
        content: dict[str, Any],
        content_format: str = "structured",
    ) -> ClinicalDocument:
        access.require_operation("create")
        if not patient_id.strip() or not document_type.strip():
            raise ClinicalGatewayBlocked("invalid_document_input")
        document = ClinicalDocument(
            patient_id=patient_id,
            encounter_id=encounter_id,
            author_practitioner_id=str(access.legacy_user_id),
            author_account_id=access.account_id,
            organization_id=access.organization_id,
            facility_id=access.facility_id,
            department_id=access.department_id,
            workspace_id=access.workspace_id,
            tenant_id=access.tenant_id,
            legacy_lab_id=access.legacy_lab_id,
            document_type=document_type,
            status="DRAFT",
            content=content,
            content_format=content_format,
            correlation_id=str(access.correlation_id),
            created_by=access.account_id,
            updated_by=access.account_id,
        )
        self.db.add(document)
        self.db.flush()
        return document

    def sign(self, *, access: ClinicalAccessContext, document_id: str, signature_reference: str) -> ClinicalDocument:
        access.require_operation("sign")
        document = self.db.get(ClinicalDocument, document_id)
        if document is None or document.is_deleted:
            raise ClinicalGatewayBlocked("document_not_found")
        if (
            document.tenant_id != access.tenant_id
            or document.organization_id != access.organization_id
            or document.facility_id != access.facility_id
            or document.workspace_id != access.workspace_id
            or document.author_account_id != access.account_id
        ):
            raise ClinicalGatewayBlocked("document_scope_denied")
        if not signature_reference.strip():
            raise ClinicalGatewayBlocked("missing_signature_reference")
        document.sign(practitioner_id=str(access.legacy_user_id), signature_reference=signature_reference)
        document.updated_by = access.account_id
        self.db.flush()
        return document

    def amend(
        self,
        *,
        access: ClinicalAccessContext,
        document_id: str,
        content: dict[str, Any],
        reason: str,
    ) -> ClinicalDocument:
        access.require_operation("update")
        original = self.db.get(ClinicalDocument, document_id)
        if original is None or original.is_deleted:
            raise ClinicalGatewayBlocked("document_not_found")
        if (
            original.tenant_id != access.tenant_id
            or original.organization_id != access.organization_id
            or original.facility_id != access.facility_id
            or original.workspace_id != access.workspace_id
        ):
            raise ClinicalGatewayBlocked("document_scope_denied")
        amendment = original.create_amendment(
            content=content,
            reason=reason,
            author_practitioner_id=str(access.legacy_user_id),
        )
        amendment.author_account_id = access.account_id
        amendment.updated_by = access.account_id
        self.db.add(amendment)
        original.status = "AMENDED"
        original.updated_by = access.account_id
        self.db.flush()
        return amendment

    @staticmethod
    def to_safe_dict(document: ClinicalDocument) -> dict[str, Any]:
        return {
            "id": document.id,
            "patient_id": document.patient_id,
            "encounter_id": document.encounter_id,
            "document_type": document.document_type,
            "status": document.status,
            "version": document.version,
            "content": document.content,
            "content_format": document.content_format,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "signed_at": document.signed_at,
            "amendment_of": document.amendment_of,
            "correlation_id": document.correlation_id,
        }
