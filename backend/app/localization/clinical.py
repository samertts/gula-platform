"""Medical terminology localization registry and approval enforcement."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping

from .language_registry import LanguageDefinition
from .pack_schema import ApprovalRecord, TerminologyEntry
from .runtime import StableMessage


class ClinicalApprovalError(ValueError):
    """Raised when high-risk clinical localization lacks documented approval."""


class ClinicalInvariantError(ValueError):
    """Raised when a translation would alter a clinical value, unit, or identifier."""


class PackGovernanceError(ValueError):
    """Raised when a language or clinical catalog is not approved for publication."""


def validate_pack_governance(
    definition: LanguageDefinition,
    *,
    catalogs: Iterable[str],
    files: Mapping[str, bytes],
    approval_status: str,
    allow_synthetic: bool,
) -> None:
    """Enforce registry and clinical approval gates for a pack.

    Synthetic packs are accepted only when explicitly enabled. Approved packs
    require a publishable, linguistically approved registry entry. Clinical
    catalogs and L3/L4 terminology are rejected unless the registry records
    documented clinical approval.
    """
    if not definition.is_active or definition.locale_tag is None:
        raise PackGovernanceError(f"language standard is not approved: {definition.language_id}")

    if approval_status == "synthetic_test_only":
        if not allow_synthetic:
            raise PackGovernanceError("synthetic test packs are disabled in this environment")
    elif approval_status != "approved":
        raise PackGovernanceError("pack approval status is not publishable")
    elif not definition.is_publishable or definition.approval_status != "approved":
        raise PackGovernanceError(f"language pack is not publishable: {definition.language_id}")
    elif definition.linguistic_approval_status != "approved":
        raise PackGovernanceError(f"linguistic approval is missing: {definition.language_id}")

    if "clinical" in set(catalogs) and definition.clinical_approval_status != "approved":
        raise PackGovernanceError(f"clinical catalog is not approved for {definition.language_id}")

    for path, content in files.items():
        if not path.startswith("terminology/"):
            continue
        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, ValueError) as exc:
            raise PackGovernanceError(f"invalid terminology file: {path}") from exc
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            content_class = entry.get("approval_class") or entry.get("content_class")
            if content_class not in {"L3", "L4"}:
                continue
            if definition.clinical_approval_status != "approved":
                raise PackGovernanceError(f"clinical terminology is not approved for {definition.language_id}")
            if content_class == "L4" and not entry.get("clinical_reviewer"):
                raise PackGovernanceError("L4 terminology requires documented human clinical approval")


class ClinicalTerminologyRegistry:
    """Stores translated display strings separately from source clinical data."""

    def __init__(self, entries: Iterable[TerminologyEntry] = ()) -> None:
        self._entries = {entry.concept_id: entry for entry in entries}
        if len(self._entries) != len(list(entries)):
            raise ClinicalInvariantError("duplicate terminology concept_id")

    @staticmethod
    def validate_approval(record: ApprovalRecord) -> None:
        if record.content_class == "L4" and not record.clinical_reviewer:
            raise ClinicalApprovalError("L4 content requires documented human clinical approval")
        if record.content_class not in {"L1", "L2", "L3", "L4"}:
            raise ClinicalApprovalError("unknown content classification")

    def add(self, entry: TerminologyEntry, record: ApprovalRecord) -> None:
        self.validate_approval(record)
        if record.translation_key != entry.concept_id:
            raise ClinicalInvariantError("approval record does not match terminology concept")
        if record.content_class != entry.approval_class:
            raise ClinicalInvariantError("approval class does not match terminology entry")
        if entry.approval_class == "L4" and record.clinical_reviewer is None:
            raise ClinicalApprovalError("unapproved L4 translation cannot be published")
        self._entries[entry.concept_id] = entry

    def get(self, concept_id: str) -> TerminologyEntry | None:
        return self._entries.get(concept_id)

    def display(self, concept_id: str) -> str:
        entry = self._entries.get(concept_id)
        if entry is None:
            return ""
        return entry.translated_display

    @staticmethod
    def assert_unchanged(before: Mapping[str, object], after: Mapping[str, object]) -> None:
        protected = ("original_value", "original_unit", "loinc", "ucum", "code_system", "code", "result_status")
        for key in protected:
            if before.get(key) != after.get(key):
                raise ClinicalInvariantError(f"clinical field changed by localization: {key}")

    def stable_message(self, code: str, parameters: Mapping[str, object], correlation_id: str | None = None) -> StableMessage:
        return StableMessage(code=code, parameters=dict(parameters), correlation_id=correlation_id)
