from __future__ import annotations

from datetime import UTC, datetime, timezone

import pytest
from app.localization.clinical import (
    ClinicalApprovalError,
    ClinicalInvariantError,
    ClinicalTerminologyRegistry,
)
from app.localization.pack_schema import ApprovalRecord, TerminologyEntry
from app.localization.runtime import is_valid_translation_key
from pydantic import ValidationError


def _record(content_class: str, clinical_reviewer: str | None) -> ApprovalRecord:
    return ApprovalRecord(
        translation_key="clinical.allergy",
        content_class=content_class,  # type: ignore[arg-type]
        source_text="Synthetic allergy warning",
        translated_text="Synthetic translated warning",
        translator="translator-a",
        linguistic_reviewer="reviewer-b",
        clinical_reviewer=clinical_reviewer,
        approved_at=datetime.now(UTC),
        package_version="1.0.0",
        change_reason="synthetic test",
    )


def _entry(content_class: str) -> TerminologyEntry:
    return TerminologyEntry(
        concept_id="clinical.allergy",
        source_language="en",
        loinc="SYNTHETIC-LOINC",
        ucum="mg",
        code_system="SYNTHETIC",
        code="ALLERGY-1",
        original_value="10",
        original_unit="mg",
        translated_display="Synthetic translated warning",
        translated_display_language="fa",
        approval_class=content_class,  # type: ignore[arg-type]
        approval_record_id="approval-1",
    )


def test_l4_without_clinical_approval_cannot_be_published():
    with pytest.raises(ValidationError):
        _record("L4", None)


def test_l4_with_documented_clinical_approval_is_publishable():
    registry = ClinicalTerminologyRegistry()
    registry.add(_entry("L4"), _record("L4", "clinician-c"))
    assert registry.display("clinical.allergy") == "Synthetic translated warning"


def test_role_separation_enforced():
    with pytest.raises(ValidationError):
        ApprovalRecord(
            translation_key="clinical.allergy",
            content_class="L4",
            source_text="source",
            translated_text="target",
            translator="same-person",
            linguistic_reviewer="same-person",
            clinical_reviewer="same-person",
            approved_at=datetime.now(UTC),
            package_version="1.0.0",
            change_reason="initial",
        )


def test_clinical_values_units_and_identifiers_never_change():
    before = {"original_value": "10", "original_unit": "mg", "loinc": "SYNTHETIC-LOINC", "ucum": "mg"}
    after = dict(before)
    ClinicalTerminologyRegistry.assert_unchanged(before, after)
    after["original_unit"] = "g"
    with pytest.raises(ClinicalInvariantError):
        ClinicalTerminologyRegistry.assert_unchanged(before, after)


def test_stable_clinical_error_contract():
    registry = ClinicalTerminologyRegistry()
    message = registry.stable_message("CRITICAL_RESULT_NOT_AVAILABLE", {"result_id": "SYNTHETIC"}, "corr-1")
    assert message.to_dict() == {
        "code": "CRITICAL_RESULT_NOT_AVAILABLE",
        "parameters": {"result_id": "SYNTHETIC"},
        "correlation_id": "corr-1",
    }


def test_translation_keys_are_not_clinical_identifiers():
    assert is_valid_translation_key("clinical.allergy_warning")
    assert not is_valid_translation_key("LOINC:1234-5")
