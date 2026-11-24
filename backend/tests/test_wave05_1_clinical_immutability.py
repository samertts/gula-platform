"""Wave 05.1 — canonical clinical note immutability characterization.

Synthetic records only. These tests exercise the existing SQLAlchemy-backed
``app.services.ehr_service``. They do not add a clinical store, route, policy,
DDL, trigger, signature implementation or generated artifact.

Known owner-gated gaps are characterized as current behavior, not approved:
no CAS/lock protects concurrent amendments, no append-only audit event is
emitted, and signature invalidation after amendment is undefined.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy.sql.elements import False_, True_

from app._compat import UTC
from app.ehr.enums import ClinicalNoteType
from app.ehr.models.clinical_note import ClinicalNote
from app.services import ehr_service


def _matches(note, expression) -> bool:
    left = getattr(expression, "left", None)
    key = getattr(left, "key", None)
    if key is None or not hasattr(note, key):
        return True
    right = getattr(expression, "right", None)
    if isinstance(right, False_):
        expected = False
    elif isinstance(right, True_):
        expected = True
    else:
        expected = getattr(right, "value", right)
    return getattr(note, key) == expected


class _NoteQuery:
    def __init__(self, notes):
        self._notes = notes
        self._expressions = []

    def filter(self, *expressions):
        self._expressions.extend(expressions)
        return self

    def first(self):
        for note in self._notes:
            if all(_matches(note, expression) for expression in self._expressions):
                return note
        return None


class _NoteSession:
    """Minimal in-memory Session surface used by canonical note functions."""

    def __init__(self):
        self.notes = []
        self.flushes = 0

    def query(self, _model):
        return _NoteQuery(self.notes)

    def add(self, note):
        if not getattr(note, "id", None):
            note.id = f"NOTE-SYN-{uuid.uuid4().hex[:12]}"
        self.notes.append(note)

    def flush(self):
        self.flushes += 1


def _note(session, **overrides):
    values = dict(
        id=f"NOTE-SYN-{uuid.uuid4().hex[:12]}",
        patient_id="PATIENT-SYN-W05-1",
        citizen_id="CITIZEN-SYN-W05-1",
        encounter_id="ENCOUNTER-SYN-W05-1",
        practitioner_id="PRACTITIONER-SYN-W05-1",
        author_id="AUTHOR-SYN-W05-1",
        facility_id="FACILITY-SYN-W05-1",
        note_type=ClinicalNoteType.PROGRESS,
        title="Synthetic progress note",
        content="Original synthetic content",
        content_format="text",
        version=1,
        is_final=False,
        is_signed=False,
        is_deleted=False,
        authored_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    values.update(overrides)
    note = ClinicalNote(**values)
    session.notes.append(note)
    return note


def _amend(session, note, content="Amended synthetic content", reason="Synthetic correction"):
    return ehr_service.amend_clinical_note(
        session, note.id, content=content, amendment_reason=reason,
    )


def test_draft_note_update_is_allowed_and_increments_version():
    session = _NoteSession()
    note = _note(session)
    updated = ehr_service.update_clinical_note(
        session, note.id, {"content": "Revised synthetic content"},
    )
    assert updated is note
    assert note.content == "Revised synthetic content"
    assert note.version == 2
    assert session.flushes == 1


def test_draft_note_finalization_is_allowed_but_unfinalization_is_rejected():
    session = _NoteSession()
    note = _note(session)
    finalized = ehr_service.update_clinical_note(session, note.id, {"is_final": True})
    assert finalized.is_final is True
    assert finalized.version == 2

    with pytest.raises(ehr_service.ClinicalRecordImmutableError):
        ehr_service.update_clinical_note(session, note.id, {"is_final": False})
    assert note.is_final is True
    assert note.version == 2


@pytest.mark.parametrize(
    "field_name",
    [
        "version",
        "fhir_id",
        "prior_version_id",
        "superseded_by_id",
        "is_amended",
        "amendment_reason",
        "is_signed",
        "signed_by",
        "signed_at",
        "electronic_signature",
        "signature_hash",
        "authored_at",
    ],
)
def test_version_signature_and_provenance_fields_cannot_be_edited_in_place(field_name):
    session = _NoteSession()
    note = _note(session)
    original_authored_at = note.authored_at
    with pytest.raises(ValueError, match=field_name):
        ehr_service.update_clinical_note(session, note.id, {field_name: "tampered"})
    assert note.version == 1
    assert note.authored_at == original_authored_at
    assert not hasattr(note, "bogus_field")


@pytest.mark.parametrize("final,signed", [(True, False), (True, True), (False, True)])
def test_final_or_signed_note_cannot_be_changed_in_place(final, signed):
    session = _NoteSession()
    note = _note(
        session,
        is_final=final,
        is_signed=signed,
        signed_by="SYN-PRACTITIONER" if signed else None,
        signature_hash="SYN-HASH" if signed else None,
    )
    original_content = note.content
    original_version = note.version
    with pytest.raises(ehr_service.ClinicalRecordImmutableError):
        ehr_service.update_clinical_note(session, note.id, {"content": "tampered"})
    assert note.content == original_content
    assert note.version == original_version


@pytest.mark.parametrize("final,signed", [(True, False), (True, True), (False, True)])
def test_final_or_signed_note_cannot_be_soft_deleted(final, signed):
    session = _NoteSession()
    note = _note(session, is_final=final, is_signed=signed)
    with pytest.raises(ehr_service.ClinicalRecordImmutableError):
        ehr_service.soft_delete_clinical_note(session, note.id)
    assert note.is_deleted is False
    assert ehr_service.get_clinical_note(session, note.id) is note


def test_draft_soft_delete_is_terminal_for_service_reads_and_writes():
    session = _NoteSession()
    note = _note(session)
    assert ehr_service.soft_delete_clinical_note(session, note.id) is True
    assert note.is_deleted is True
    assert note.deleted_at is not None
    assert ehr_service.get_clinical_note(session, note.id) is None
    assert ehr_service.update_clinical_note(session, note.id, {"content": "x"}) is None
    assert ehr_service.soft_delete_clinical_note(session, note.id) is False
    assert _amend(session, note) is None


@pytest.mark.parametrize("content,reason", [("", "reason"), ("   ", "reason"), ("content", ""), ("content", "   ")])
def test_amendment_requires_non_blank_content_and_reason(content, reason):
    session = _NoteSession()
    note = _note(session, is_final=True)
    with pytest.raises(ValueError):
        ehr_service.amend_clinical_note(
            session, note.id, content=content, amendment_reason=reason,
        )
    assert session.notes == [note]


def test_signed_note_amendment_preserves_original_signature_and_provenance():
    session = _NoteSession()
    note = _note(
        session,
        is_final=True,
        is_signed=True,
        signed_by="SYN-PRACTITIONER",
        signature_hash="SYN-HASH",
    )
    original = SimpleNamespace(
        content=note.content, version=note.version, signature=note.signature_hash,
        authored_at=note.authored_at,
    )
    amendment = _amend(session, note, reason="Synthetic signed correction")
    assert amendment is not None
    assert amendment.id != note.id
    assert amendment.prior_version_id == note.id
    assert note.superseded_by_id == amendment.id
    assert amendment.version == original.version + 1
    assert amendment.is_amended is True
    assert amendment.is_final is True
    assert amendment.is_signed is False
    assert amendment.amendment_reason == "Synthetic signed correction"
    assert amendment.authored_at != original.authored_at
    assert amendment.patient_id == note.patient_id
    assert amendment.facility_id == note.facility_id
    assert note.content == original.content
    assert note.version == original.version
    assert note.signature_hash == original.signature
    assert note.authored_at == original.authored_at


def test_amendment_chain_extends_the_current_tail_not_the_original():
    session = _NoteSession()
    original = _note(session, is_final=True)
    first = _amend(session, original, content="First synthetic amendment")
    second = _amend(session, original, content="Second synthetic amendment")
    assert original.superseded_by_id == first.id
    assert first.superseded_by_id == second.id
    assert second.prior_version_id == first.id
    assert second.version == first.version + 1
    assert ehr_service.get_clinical_note(session, second.id) is second


def test_deleted_successor_is_characterized_as_a_silent_chain_break():
    session = _NoteSession()
    original = _note(session, is_final=True)
    first = _amend(session, original, content="First synthetic amendment")
    first.is_deleted = True  # direct state injection; no production bypass is added
    second = _amend(session, original, content="Second synthetic amendment")
    # Current service behavior: the deleted successor is skipped, so the new
    # amendment attaches to the earlier live note and creates a sibling. This
    # is recorded as a gap, not approved as a safe clinical workflow.
    assert second.prior_version_id == original.id
    assert first.superseded_by_id is None
    assert ehr_service.get_clinical_note(session, first.id) is None


def test_cycle_is_characterized_as_a_silent_break_not_a_rejection():
    session = _NoteSession()
    original = _note(session, is_final=True)
    original.superseded_by_id = original.id
    amendment = _amend(session, original)
    assert amendment.prior_version_id == original.id
    assert original.superseded_by_id == amendment.id
    assert amendment.superseded_by_id is None


def test_two_isolated_amendments_characterize_missing_cas_protection():
    first_session = _NoteSession()
    second_session = _NoteSession()
    first_original = _note(first_session, id="NOTE-SYN-CONCURRENT", is_final=True)
    second_original = _note(second_session, id="NOTE-SYN-CONCURRENT", is_final=True)
    first = _amend(first_session, first_original)
    second = _amend(second_session, second_original)
    assert first.id != second.id
    assert first.version == second.version == 2
    assert first.prior_version_id == second.prior_version_id == "NOTE-SYN-CONCURRENT"


def test_draft_reparenting_via_generic_update_is_characterized_as_a_gap():
    session = _NoteSession()
    note = _note(session)
    updated = ehr_service.update_clinical_note(
        session, note.id, {"patient_id": "PATIENT-SYN-OTHER"},
    )
    assert updated.patient_id == "PATIENT-SYN-OTHER"
    assert note.version == 2
