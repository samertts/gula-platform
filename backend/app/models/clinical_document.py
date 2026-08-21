from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Index, Integer, String

from app._compat import UTC
from app.models.base import AuditMixin, Base, OptimisticLockMixin, SoftDeleteMixin

CLINICAL_DOCUMENT_STATES = frozenset({"DRAFT", "IN_REVIEW", "SIGNED", "AMENDED", "VOIDED", "CANCELLED"})


def _document_id() -> str:
    return str(uuid.uuid4())


class ClinicalDocument(AuditMixin, SoftDeleteMixin, OptimisticLockMixin, Base):
    """Durable clinical document authority for the doctor workflow.

    The model deliberately stores opaque/string resource identifiers because the
    repository currently has legacy integer patient records and national string
    resources. Resolution and authorization happen in the service layer; the
    client never supplies actor or context as authority.
    """

    __tablename__ = "clinical_documents"

    id = Column(String(36), primary_key=True, default=_document_id)
    patient_id = Column(String(80), nullable=False, index=True)
    encounter_id = Column(String(80), nullable=True, index=True)
    author_practitioner_id = Column(String(80), nullable=False, index=True)
    author_account_id = Column(Integer, nullable=False, index=True)
    organization_id = Column(String(80), nullable=False, index=True)
    facility_id = Column(String(80), nullable=False, index=True)
    department_id = Column(String(80), nullable=True, index=True)
    workspace_id = Column(String(80), nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    legacy_lab_id = Column(Integer, nullable=True, index=True)

    document_type = Column(String(64), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    content = Column(JSON, nullable=False, default=dict)
    content_format = Column(String(20), nullable=False, default="structured")

    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_by = Column(String(80), nullable=True, index=True)
    signature_reference = Column(String(128), nullable=True)
    amendment_of = Column(String(36), nullable=True, index=True)
    amendment_reason = Column(String(500), nullable=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    is_signed = Column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        Index("ix_clinical_document_scope_patient", "tenant_id", "organization_id", "facility_id", "workspace_id", "patient_id"),
        Index("ix_clinical_document_state", "status", "is_signed", "is_deleted"),
        Index("ix_clinical_document_encounter", "encounter_id", "version"),
    )

    def is_terminal(self) -> bool:
        return self.status in {"SIGNED", "VOIDED", "CANCELLED"}

    def can_transition_to(self, new_status: str) -> bool:
        allowed = {
            "DRAFT": {"IN_REVIEW", "CANCELLED"},
            "IN_REVIEW": {"SIGNED", "DRAFT", "CANCELLED"},
            "SIGNED": {"AMENDED", "VOIDED"},
            "AMENDED": {"SIGNED", "VOIDED"},
            "VOIDED": set(),
            "CANCELLED": set(),
        }
        return new_status in allowed.get(self.status, set())

    def sign(self, *, practitioner_id: str, signature_reference: str) -> None:
        if not self.can_transition_to("SIGNED"):
            raise ValueError(f"Invalid clinical document transition: {self.status} -> SIGNED")
        now = datetime.now(UTC)
        self.status = "SIGNED"
        self.is_signed = True
        self.version = int(self.version or 1) + 1
        self.signed_by = practitioner_id
        self.signed_at = now
        self.signature_reference = signature_reference
        self.updated_at = now

    def create_amendment(self, *, content: dict, reason: str, author_practitioner_id: str) -> "ClinicalDocument":
        if self.status not in {"SIGNED", "AMENDED"}:
            raise ValueError("Only signed clinical documents can be amended")
        if not reason.strip():
            raise ValueError("Amendment reason is required")
        return ClinicalDocument(
            patient_id=self.patient_id,
            encounter_id=self.encounter_id,
            author_practitioner_id=author_practitioner_id,
            author_account_id=self.author_account_id,
            organization_id=self.organization_id,
            facility_id=self.facility_id,
            department_id=self.department_id,
            workspace_id=self.workspace_id,
            tenant_id=self.tenant_id,
            legacy_lab_id=self.legacy_lab_id,
            document_type=self.document_type,
            status="DRAFT",
            is_signed=False,
            content=content,
            content_format=self.content_format,
            version=int(self.version or 1) + 1,
            amendment_of=self.id,
            amendment_reason=reason.strip(),
            correlation_id=str(uuid.uuid4()),
        )
