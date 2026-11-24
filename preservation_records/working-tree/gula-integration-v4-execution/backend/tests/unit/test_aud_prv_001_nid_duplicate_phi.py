"""AUD-PRV-001 — national-ID duplicate lookup must not disclose cross-facility PHI.

The auditor found ``_check_duplicates`` looked up a national-ID hash GLOBALLY and
returned ``patient_to_dict(existing)`` of the matched record. A user at facility A
who knew (or brute-forced) a national ID could obtain facility B's patient PHI:
full name, phone, birth date, gender, email, health id, guardian link.

Falsification axes:
1. A national-ID match at a DIFFERENT facility is not detected and leaks nothing.
2. A same-facility match returns ONLY a non-identifying conflict marker — no PHI,
   no internal id, no facility identity, no ``existing_patient``.
3. The query selects only ``Patient.id`` (never loads full PHI entities).
4. ``lab_id is None`` skips the national-ID lookup (fail-closed).
5. Legitimate same-facility phone duplicates still work (no functional regression).
"""
from __future__ import annotations

import inspect
from datetime import UTC, date, datetime, timedelta

import pytest
from app.models.patient import Patient
from app.services import patient_service
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

NID_HASH = "nid:hash-for-victim-123"
PHI_KEYS = {
    "id", "lab_id", "health_id", "national_id_hash", "family_id_hash", "guardian_id",
    "full_name", "phone", "birth_date", "gender", "email", "is_minor", "created_at",
    "existing_patient", "matches", "facility", "facility_id",
}


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Patient.__table__.create(engine)
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            Patient.__table__.insert().values(
                id=1,
                lab_id=2,  # victim lives at a DIFFERENT facility
                full_name="Victim Other Facility",
                phone="+964700000999",
                national_id_hash=NID_HASH,
                birth_date=date(1980, 1, 1),
                gender="F",
                email="victim@other.invalid",
                health_id="GULA-OTHER-1",
                created_at=now - timedelta(days=400),
            )
        )
    with Session(engine) as session:
        yield session


def _call(session, *, lab_id, nid_hash=NID_HASH, full_name="Caller Input",
          phone="+964711111000", birth_date="1990-01-01"):
    return patient_service._check_duplicates(
        session, lab_id, full_name, phone, birth_date, nid_hash,
    )


class TestNationalIdDuplicatePhi:
    def test_cross_facility_nid_match_leaks_nothing(self, db):
        """The exact auditor falsification: lab 1 must not see lab 2's patient."""
        result = _call(db, lab_id=1)  # caller at facility 1, victim at facility 2
        # Distinct phone/name -> no same-facility duplicate either.
        assert result is None, f"cross-facility NID match leaked a duplicate: {result}"

    def test_same_facility_match_returns_only_non_identifying_marker(self, db):
        """A real same-facility NID match returns a conflict marker, never PHI."""
        # Insert a patient that belongs to the CALLER's facility with the same NID.
        db.execute(
            Patient.__table__.insert().values(
                id=2, lab_id=1, full_name="Same Facility Patient",
                phone="+964711111000", national_id_hash=NID_HASH,
                created_at=datetime.now(UTC),
            )
        )
        db.commit()
        result = _call(db, lab_id=1)
        assert result is not None
        assert result["status_code"] == 409
        error = result["error"]
        assert error["duplicate"] is True
        assert error["conflict"] == {"scope": "national_id", "facility_scoped": True}
        # No PHI or internal identity anywhere in the response.
        assert not (set(error) & PHI_KEYS), f"PHI leaked in error body: {set(error) & PHI_KEYS}"
        assert not (set(error.get("conflict", {})) & PHI_KEYS)

    def test_no_existing_patient_or_phi_fields_in_response(self, db):
        """Explicitly assert the removed ``existing_patient`` field never returns."""
        db.execute(
            Patient.__table__.insert().values(
                id=3, lab_id=1, full_name="Another", phone="+964711111000",
                national_id_hash=NID_HASH, created_at=datetime.now(UTC),
            )
        )
        db.commit()
        result = _call(db, lab_id=1)
        blob = repr(result)
        assert "existing_patient" not in blob
        assert "Victim Other Facility" not in blob
        assert "victim@other.invalid" not in blob
        assert "GULA-OTHER-1" not in blob

    def test_none_lab_id_skips_nid_lookup(self, db):
        """Fail-closed: no lab scope means no national-ID lookup at all."""
        assert _call(db, lab_id=None) is None

    def test_nid_query_selects_only_id_and_is_lab_scoped(self):
        """Static guard: the NID branch selects Patient.id and filters by lab_id."""
        src = inspect.getsource(patient_service._check_duplicates)
        assert "db.query(Patient.id)" in src, "NID lookup must select only Patient.id"
        assert "Patient.lab_id == lab_id, Patient.national_id_hash == nid_hash" in src, (
            "NID lookup must be partitioned by the caller's lab_id"
        )

    def test_same_facility_phone_duplicate_still_detected(self, db):
        """Functional regression guard: legitimate same-facility duplicates still work."""
        db.execute(
            Patient.__table__.insert().values(
                id=4, lab_id=1, full_name="Caller Input", phone="+964711111000",
                birth_date=date(1990, 1, 1), created_at=datetime.now(UTC),
            )
        )
        db.commit()
        # No NID match at this facility -> falls through to phone/name detection.
        result = _call(db, lab_id=1, nid_hash="nid:no-match-here")
        assert result is not None
        assert result["status_code"] == 409
        assert result["error"]["matches"], "same-facility phone duplicate should still be reported"
