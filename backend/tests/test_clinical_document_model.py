from __future__ import annotations

import pytest

from app.models.clinical_document import ClinicalDocument


def _document(status: str = "DRAFT") -> ClinicalDocument:
    return ClinicalDocument(
        patient_id="patient-1",
        author_practitioner_id="practitioner-1",
        author_account_id=1,
        organization_id="org-1",
        facility_id="facility-1",
        workspace_id="workspace-1",
        tenant_id=1,
        document_type="soap_note",
        status=status,
        content={"assessment": "draft"},
        correlation_id="corr-1",
    )


def test_document_state_machine_allows_review_then_sign():
    document = _document()
    assert document.can_transition_to("IN_REVIEW")
    document.status = "IN_REVIEW"
    assert document.can_transition_to("SIGNED")


def test_signed_document_cannot_be_overwritten_or_signed_twice():
    document = _document("IN_REVIEW")
    document.sign(practitioner_id="practitioner-1", signature_reference="sig-1")
    assert document.status == "SIGNED"
    assert document.is_signed is True
    assert not document.can_transition_to("DRAFT")
    with pytest.raises(ValueError, match="Invalid clinical document transition"):
        document.sign(practitioner_id="practitioner-1", signature_reference="sig-2")


def test_amendment_creates_new_draft_and_preserves_original_reference():
    original = _document("SIGNED")
    amendment = original.create_amendment(
        content={"assessment": "corrected"},
        reason="تصحيح سريري موثق",
        author_practitioner_id="practitioner-2",
    )
    assert amendment.status == "DRAFT"
    assert amendment.amendment_of == original.id
    assert amendment.version == int(original.version or 1) + 1
    assert amendment.is_signed is False


def test_amendment_requires_reason_and_signed_source():
    with pytest.raises(ValueError, match="Only signed"):
        _document("DRAFT").create_amendment(content={}, reason="x", author_practitioner_id="p")
    with pytest.raises(ValueError, match="Amendment reason"):
        _document("SIGNED").create_amendment(content={}, reason=" ", author_practitioner_id="p")
