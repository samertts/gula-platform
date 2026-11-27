"""Wave 05 — canonical PHI fail-closed and clinical note immutability.

Every fixture is synthetic. No PHI, PII, credential or production data is used.
These tests exercise existing canonical components only; no new authorization,
identity, audit, record store, schema or route is introduced.

The note tests use a deterministic in-memory session. The shared SQLite fixture
cannot materialize EHR notes because the repository declares cross-metadata
foreign keys from EHRBase tables to NationalBase tables; that is a pre-existing
test-harness limitation, not a property of the service logic under test.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.sql.elements import False_, True_

from app._compat import UTC
from app.ehr.enums import ClinicalNoteType
from app.ehr.models.clinical_note import ClinicalNote
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.national.domain.encounter import Encounter as NationalEncounter
from app.national.domain.observation import Observation as NationalObservation
from app.radiology.models import RadiologyReport
from app.services import ehr_service


# ── Canonical authorization harness (mirrors the Phase 8 / Wave 04 harness) ──


class _Result:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class _ScriptedSession:
    def __init__(self, *, identity=None, employments=None, memberships=None, assignments=None, permissions=None):
        self.identity = identity
        self.employments = employments or []
        self.memberships = memberships or []
        self.assignments = assignments or []
        self.permissions = permissions or []

    async def execute(self, statement):
        sql = str(statement)
        if "niam_identities" in sql:
            return _Result([self.identity] if self.identity is not None else [])
        if "niam_employments" in sql:
            return _Result(list(self.employments))
        if "niam_memberships" in sql:
            matches = list(self.memberships)
            if "revoked_at IS NULL" in sql:
                matches = [item for item in matches if getattr(item, "revoked_at", None) is None]
            return _Result(matches)
        if "niam_assignments" in sql:
            return _Result(list(self.assignments))
        if "niam_role_assignments" in sql:
            return _Result(list(self.permissions))
        if "niam_policies" in sql:
            return _Result([])
        return _Result([])

    async def scalar(self, _statement):
        return "permission-id"

    def add(self, _entry):
        return None

    async def flush(self):
        return None


def _now():
    return datetime.now(UTC)


def _actor():
    return AuthorizationActor(
        account=SimpleNamespace(
            id="ACCOUNT-W05",
            identity_id="IDENTITY-W05",
            status="active",
            is_active=True,
            is_locked=False,
        ),
        session=SimpleNamespace(
            id="SESSION-W05",
            account_id="ACCOUNT-W05",
            is_active=True,
            expires_at=_now() + timedelta(hours=1),
            mfa_used=False,
        ),
    )


def _identity():
    return SimpleNamespace(id="IDENTITY-W05", person_id="PERSON-W05")


def _employment():
    return SimpleNamespace(
        id="EMPLOYMENT-W05",
        person_id="PERSON-W05",
        organization_id="ORG-W05",
        status="active",
        is_active=True,
        start_date=date.today() - timedelta(days=30),
        end_date=None,
        termination_date=None,
    )


def _membership():
    return SimpleNamespace(
        id="MEMBERSHIP-W05",
        account_id="ACCOUNT-W05",
        organization_id="ORG-W05",
        facility_id="FACILITY-W05",
        department_id=None,
        unit_id=None,
        workspace_id=None,
        status="active",
        is_active=True,
        expires_at=None,
        revoked_at=None,
    )


def _request(**overrides):
    values = dict(
        subject_account_id="ACCOUNT-W05",
        action="read",
        resource_type="patient_record",
        resource_id="PATIENT-SYN-W05",
        permission_key="patient_record.read",
        organization_id="ORG-W05",
        facility_id="FACILITY-W05",
        department_id=None,
        unit_id=None,
        workspace_id=None,
        resource_context={
            "exists": True,
            "organization_id": "ORG-W05",
            "facility_id": "FACILITY-W05",
        },
    )
    values.update(overrides)
    return AuthorizationRequest(**values)


def _service():
    return AuthorizationDecisionService(
        _ScriptedSession(
            identity=_identity(),
            employments=[_employment()],
            memberships=[_membership()],
            permissions=["patient_record.read", "patient_record.read_everything"],
        ),
    )


@pytest.mark.asyncio
async def test_wave05_mapped_phi_action_remains_allowed():
    decision = await _service().authorize(_actor(), _request())
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_wave05_unmapped_phi_action_fails_closed_despite_broad_key():
    decision = await _service().authorize(
        _actor(),
        _request(action="teleport", permission_key="patient_record.read_everything"),
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.permission_unknown


@pytest.mark.asyncio
async def test_wave05_conflicting_phi_key_still_denied():
    decision = await _service().authorize(
        _actor(),
        _request(action="read", permission_key="lab_result.read"),
    )
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.phi_permission_conflict


# ── Clinical note immutability and amendment ───────────────────────────────


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
    """In-memory Session surface used by the note service functions."""

    def __init__(self):
        self.notes = []

    def query(self, _model):
        return _NoteQuery(self.notes)

    def add(self, note):
        if not getattr(note, "id", None):
            note.id = f"NOTE-{uuid.uuid4().hex[:12]}"
        self.notes.append(note)

    def flush(self):
        return None


def _note(session, **overrides):
    values = dict(
        id=f"NOTE-{uuid.uuid4().hex[:12]}",
        patient_id="PATIENT-SYN-W05",
        note_type=ClinicalNoteType.PROGRESS,
        title="Synthetic progress note",
        content="Original synthetic content",
        content_format="text",
        version=1,
        is_final=False,
        is_signed=False,
        is_deleted=False,
    )
    values.update(overrides)
    note = ClinicalNote(**values)
    session.notes.append(note)
    return note


def test_wave05_final_note_cannot_be_changed_in_place():
    session = _NoteSession()
    note = _note(session, is_final=True)
    original_content = note.content
    original_version = note.version

    with pytest.raises(ehr_service.ClinicalRecordImmutableError):
        ehr_service.update_clinical_note(session, note.id, {"content": "tampered"})

    assert note.content == original_content
    assert note.version == original_version


def test_wave05_signed_note_cannot_be_soft_deleted():
    session = _NoteSession()
    note = _note(session, is_signed=True, signed_by="SYN-PRACTITIONER")

    with pytest.raises(ehr_service.ClinicalRecordImmutableError):
        ehr_service.soft_delete_clinical_note(session, note.id)

    assert note.is_deleted is False


def test_wave05_draft_note_can_be_finalized_but_not_unfinalized():
    session = _NoteSession()
    note = _note(session)

    finalized = ehr_service.update_clinical_note(session, note.id, {"is_final": True})
    assert finalized.is_final is True
    assert finalized.version == 2

    with pytest.raises(ehr_service.ClinicalRecordImmutableError):
        ehr_service.update_clinical_note(session, note.id, {"is_final": False})


def test_wave05_amendment_preserves_history_and_links_supersession():
    session = _NoteSession()
    note = _note(
        session,
        is_final=True,
        is_signed=True,
        signed_by="SYN-PRACTITIONER",
        signature_hash="SYN-HASH",
    )
    original_content = note.content
    original_signature = note.signature_hash
    original_version = note.version

    amendment = ehr_service.amend_clinical_note(
        session,
        note.id,
        content="Amended synthetic content",
        amendment_reason="Synthetic correction for validation",
    )

    assert amendment is not None
    assert amendment.id != note.id
    assert amendment.patient_id == note.patient_id
    assert amendment.prior_version_id == note.id
    assert amendment.version == original_version + 1
    assert amendment.is_amended is True
    assert amendment.is_final is True
    assert amendment.is_signed is False
    assert amendment.amendment_reason == "Synthetic correction for validation"

    assert note.superseded_by_id == amendment.id
    assert note.content == original_content
    assert note.signature_hash == original_signature
    assert note.version == original_version

    stored_amendment = ehr_service.get_clinical_note(session, amendment.id)
    assert stored_amendment is amendment
    assert stored_amendment.prior_version_id == note.id


def test_wave05_amendment_chain_always_extends_current_version():
    session = _NoteSession()
    note = _note(session, is_final=True)
    first = ehr_service.amend_clinical_note(
        session, note.id, content="First amendment", amendment_reason="Synthetic reason 1",
    )
    second = ehr_service.amend_clinical_note(
        session, note.id, content="Second amendment", amendment_reason="Synthetic reason 2",
    )

    assert first.superseded_by_id == second.id
    assert second.prior_version_id == first.id
    assert note.superseded_by_id == first.id
    assert second.version == first.version + 1


def test_wave05_amendment_requires_reason():
    session = _NoteSession()
    note = _note(session, is_final=True)

    with pytest.raises(ValueError, match="Amendment reason is required"):
        ehr_service.amend_clinical_note(session, note.id, content="Amended", amendment_reason="  ")


# ── Longitudinal history projection ───────────────────────────────────────


class _RecordQuery:
    def __init__(self, records):
        self._records = records
        self._expressions = []

    def filter(self, *expressions):
        self._expressions.extend(expressions)
        return self

    def order_by(self, *_expressions):
        return self

    def limit(self, _count):
        return self

    def all(self):
        return [
            record
            for record in self._records
            if all(_matches(record, expression) for expression in self._expressions)
        ]


class _RecordSession:
    """Read-only session surface for the longitudinal projection."""

    def __init__(self, records_by_model):
        self._records_by_model = records_by_model

    def query(self, model):
        return _RecordQuery(self._records_by_model.get(model, []))


def test_wave05_longitudinal_bundle_dedupes_and_sorts_by_event_date():
    events = [
        {
            "event_type": "encounter",
            "event_date": "2026-01-02T00:00:00+00:00",
            "source_type": "national_encounters",
            "source_id": "ENC-1",
        },
        {
            "event_type": "clinical_note",
            "event_date": "2026-01-03T00:00:00+00:00",
            "source_type": "ehr_clinical_notes",
            "source_id": "NOTE-1",
        },
        {
            "event_type": "clinical_note",
            "event_date": "2026-01-04T00:00:00+00:00",
            "source_type": "ehr_clinical_notes",
            "source_id": "NOTE-1",
        },
    ]

    bundle = ehr_service.build_longitudinal_history_bundle(
        events, patient_id="PATIENT-SYN-W05", generated_at=datetime(2026, 2, 1, tzinfo=UTC),
    )

    assert bundle["patient_id"] == "PATIENT-SYN-W05"
    assert bundle["event_count"] == 2
    assert bundle["source_types"] == ["ehr_clinical_notes", "national_encounters"]
    assert [event["event_type"] for event in bundle["events"]] == ["clinical_note", "encounter"]
    assert bundle["events"][0]["event_date"] == "2026-01-03T00:00:00+00:00"


def test_wave05_longitudinal_history_includes_existing_non_ehr_domains(monkeypatch):
    monkeypatch.setattr(
        ehr_service,
        "build_live_timeline",
        lambda _db, _patient_id, max_per_type=10: [{
            "event_type": "clinical_note",
            "event_date": "2026-01-03T00:00:00+00:00",
            "source_type": "ehr_clinical_notes",
            "source_id": "NOTE-1",
        }],
    )
    session = _RecordSession(
        {
            NationalEncounter: [
                SimpleNamespace(
                    id="ENC-1", patient_id="PATIENT-SYN-W05", is_deleted=False,
                    period_start=datetime(2026, 1, 1, tzinfo=UTC),
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    encounter_type="outpatient", status="completed",
                    reason_description="Synthetic follow-up", diagnosis_description=None,
                    facility_id="FACILITY-SYN",
                ),
            ],
            NationalObservation: [
                SimpleNamespace(
                    id="OBS-1", patient_id="PATIENT-SYN-W05", is_deleted=False,
                    effective_datetime=datetime(2026, 1, 2, tzinfo=UTC),
                    issued_at=None, created_at=datetime(2026, 1, 2, tzinfo=UTC),
                    code="8867-4", code_display="Heart rate",
                    value_text=None, value_quantity="72", value_integer=72,
                    value_boolean=False, unit="bpm", status="final",
                ),
            ],
            RadiologyReport: [
                SimpleNamespace(
                    id="RAD-1", patient_id="PATIENT-SYN-W05", is_deleted=False,
                    completed_at=datetime(2026, 1, 4, tzinfo=UTC),
                    verified_at=None, amended_at=None,
                    created_at=datetime(2026, 1, 4, tzinfo=UTC),
                    impression="Synthetic normal study", conclusion=None,
                    accession_number="ACC-SYN-1", status="final",
                    version=2, prior_report_id="RAD-SYN-0",
                ),
            ],
        },
    )

    bundle = ehr_service.build_longitudinal_history(session, "PATIENT-SYN-W05")

    assert bundle["patient_id"] == "PATIENT-SYN-W05"
    assert bundle["event_count"] == 4
    assert bundle["source_types"] == [
        "ehr_clinical_notes",
        "national_encounters",
        "national_observations",
        "radiology_reports",
    ]
    radiology = next(event for event in bundle["events"] if event["source_type"] == "radiology_reports")
    assert radiology["event_type"] == "radiology_report"
    assert radiology["version"] == 2
    assert radiology["prior_report_id"] == "RAD-SYN-0"
