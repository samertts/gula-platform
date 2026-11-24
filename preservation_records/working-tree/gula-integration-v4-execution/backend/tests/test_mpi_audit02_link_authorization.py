"""AUD-02 — canonical link authorization / conflict safety (synthetic only).

Pins: role + institutional-account + lab ownership on every link endpoint; no
conflicting / duplicate / unauthorized links; cross-lab and cross-org denial;
and chained audit on each successful link.  No schema change is executed — the
DB-level UNIQUE proposal is an owner decision (see AUD-02 Migration Proposal).
"""

from __future__ import annotations

import pytest
from app.main import app
from app.models.audit_log import AuditLog
from app.models.canonical_patient import CanonicalPatient, CitizenLink, PatientLink
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.mpi.models import Citizen
from fastapi import HTTPException

LINK_URL = "/api/v1/canonical-patients/link-patient"
CITIZEN_URL = "/api/v1/canonical-patients/link-citizen"


def _lab(db, lab_id: int, name: str) -> Lab:
    lab = Lab(id=lab_id, name=name, license_number=f"SYN-AUD02-{lab_id}")
    db.add(lab)
    db.flush()
    return lab


def _actor(db, *, user_id: int, lab_id: int, role: str) -> LabUser:
    actor = LabUser(
        id=user_id,
        lab_id=lab_id,
        name=f"Synthetic {role}",
        email=f"synthetic-aud02-{user_id}@example.invalid",
        password_hash="synthetic-not-a-real-hash",
        role=role,
        is_active=True,
    )
    db.add(actor)
    db.flush()
    return actor


def _citizen_actor(db, user_id: int) -> User:
    return User(
        id=user_id,
        email=f"synthetic-citizen-{user_id}@example.invalid",
        full_name="Synthetic Citizen Account",
        role="citizen",
        lab_id=None,
        is_active=True,
    )


def _patient(db, lab_id: int, patient_id: int) -> Patient:
    p = Patient(
        id=patient_id,
        lab_id=lab_id,
        full_name="Synthetic AUD02 Patient",
        phone="+964700000222",
    )
    db.add(p)
    db.flush()
    return p


def _canonical(db, canonical_id: int, lab_id: int | None) -> CanonicalPatient:
    c = CanonicalPatient(
        id=canonical_id,
        lab_id=lab_id,
        full_name="Synthetic AUD02 Canonical",
    )
    db.add(c)
    db.flush()
    return c


def _citizen(db, citizen_id: int) -> Citizen:
    c = Citizen(
        id=citizen_id,
        citizen_ulid=f"01SYNTHAUD02{citizen_id}"[:26],
        name_canonical="synthetic aud02 citizen",
        name_blocking_key="synaud02cit",
        status="active",
        version=1,
    )
    db.add(c)
    db.flush()
    return c


def _override(user):
    app.dependency_overrides[get_current_user] = lambda: user


def _clear_override():
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture()
def _world(db):
    lab_a = _lab(db, 909200, "Synthetic Lab A")
    lab_b = _lab(db, 909201, "Synthetic Lab B")
    admin_a = _actor(db, user_id=909210, lab_id=lab_a.id, role="lab_admin")
    admin_b = _actor(db, user_id=909211, lab_id=lab_b.id, role="lab_admin")
    staff_a = _actor(db, user_id=909212, lab_id=lab_a.id, role="staff")
    citizen = _citizen_actor(db, 909213)
    patient_a = _patient(db, lab_a.id, 909220)
    patient_b = _patient(db, lab_b.id, 909221)
    canonical_a = _canonical(db, 909230, lab_a.id)
    canonical_b = _canonical(db, 909231, lab_b.id)
    national_canonical = _canonical(db, 909232, None)
    national_citizen = _citizen(db, 909240)
    return locals()


def test_staff_role_cannot_link(client, db, _world):
    _override(_world["staff_a"])
    try:
        r = client.post(
            LINK_URL,
            json={"patient_id": _world["patient_a"].id, "canonical_id": _world["canonical_a"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 403


def test_citizen_account_cannot_link(client, db, _world):
    _override(_world["citizen"])
    try:
        r = client.post(
            LINK_URL,
            json={"patient_id": _world["patient_a"].id, "canonical_id": _world["canonical_a"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 403


def test_citizen_account_cannot_link_citizen(client, db, _world):
    _override(_world["citizen"])
    try:
        r = client.post(
            CITIZEN_URL,
            json={"citizen_id": _world["national_citizen"].id, "canonical_id": _world["national_canonical"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 403


def test_cross_lab_patient_link_denied(client, db, _world):
    _override(_world["admin_a"])
    try:
        r = client.post(
            LINK_URL,
            json={"patient_id": _world["patient_b"].id, "canonical_id": _world["canonical_a"].id},
        )
    finally:
        _clear_override()
    # The global error middleware intentionally sanitises structured details to
    # a generic message; the security property under test is the 403 denial.
    assert r.status_code == 403


def test_cross_lab_canonical_link_denied(client, db, _world):
    _override(_world["admin_a"])
    try:
        r = client.post(
            LINK_URL,
            json={"patient_id": _world["patient_a"].id, "canonical_id": _world["canonical_b"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 403


def test_cross_org_citizen_link_denied(client, db, _world):
    """Lab A admin may not attach a national citizen to Lab B's canonical."""
    _override(_world["admin_a"])
    try:
        r = client.post(
            CITIZEN_URL,
            json={"citizen_id": _world["national_citizen"].id, "canonical_id": _world["canonical_b"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 403


def test_missing_patient_is_404(client, db, _world):
    _override(_world["admin_a"])
    try:
        r = client.post(
            LINK_URL,
            json={"patient_id": 999991, "canonical_id": _world["canonical_a"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 404


def test_authorized_link_creates_one_link_and_chained_audit(client, db, _world):
    _override(_world["admin_a"])
    try:
        r = client.post(
            LINK_URL,
            json={"patient_id": _world["patient_a"].id, "canonical_id": _world["canonical_a"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 200, r.text
    links = db.query(PatientLink).filter(
        PatientLink.patient_id == _world["patient_a"].id
    ).all()
    assert len(links) == 1
    assert links[0].canonical_id == _world["canonical_a"].id

    audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "canonical_link_patient")
        .one()
    )
    assert audit.user_id == _world["admin_a"].id
    assert audit.lab_id == _world["lab_a"].id
    assert audit.chain_hash is not None


def test_conflicting_second_canonical_is_409_without_duplicate(db, _world):
    from unittest.mock import patch

    from app.routes.canonical_patient import LinkPatientRequest, create_patient_link

    db.add(
        PatientLink(
            patient_id=_world["patient_a"].id,
            canonical_id=_world["canonical_a"].id,
            linkage_method="manual",
        )
    )
    db.flush()
    # The conflict is raised before any write.  Suppress the route's rollback
    # only so the fixture's seeded (uncommitted) prior link survives — in
    # production that prior link is already committed by the earlier request.
    with patch.object(db, "rollback", lambda: None), pytest.raises(HTTPException) as exc:
        create_patient_link(
            data=LinkPatientRequest(
                patient_id=_world["patient_a"].id,
                canonical_id=_world["national_canonical"].id,
            ),
            current_user=_world["admin_a"],
            db=db,
        )
    assert exc.value.status_code == 409
    links = db.query(PatientLink).filter(
        PatientLink.patient_id == _world["patient_a"].id
    ).all()
    assert len(links) == 1  # no duplicate / no silent re-point
    assert links[0].canonical_id == _world["canonical_a"].id
    assert (
        db.query(AuditLog).filter(AuditLog.action == "canonical_link_patient").count() == 0
    )


def test_idempotent_replay_does_not_create_second_link(db, _world):
    from unittest.mock import patch

    from app.routes.canonical_patient import LinkPatientRequest, create_patient_link

    db.add(
        PatientLink(
            patient_id=_world["patient_a"].id,
            canonical_id=_world["canonical_a"].id,
            linkage_method="manual",
        )
    )
    db.flush()
    with patch.object(db, "commit", lambda: None):
        response = create_patient_link(
            data=LinkPatientRequest(
                patient_id=_world["patient_a"].id,
                canonical_id=_world["canonical_a"].id,
            ),
            current_user=_world["admin_a"],
            db=db,
        )
    assert response.canonical_id == _world["canonical_a"].id
    assert db.query(PatientLink).filter(
        PatientLink.patient_id == _world["patient_a"].id
    ).count() == 1


def test_citizen_link_conflict_is_409(db, _world):
    from unittest.mock import patch

    from app.routes.canonical_patient import LinkCitizenRequest, create_citizen_link

    db.add(
        CitizenLink(
            citizen_id=_world["national_citizen"].id,
            canonical_id=_world["national_canonical"].id,
            linkage_method="manual",
        )
    )
    db.flush()
    with patch.object(db, "rollback", lambda: None), pytest.raises(HTTPException) as exc:
        create_citizen_link(
            data=LinkCitizenRequest(
                citizen_id=_world["national_citizen"].id,
                canonical_id=_world["canonical_a"].id,
            ),
            current_user=_world["admin_a"],
            db=db,
        )
    assert exc.value.status_code == 409
    assert db.query(CitizenLink).filter(
        CitizenLink.citizen_id == _world["national_citizen"].id
    ).count() == 1


def test_authorized_citizen_link_writes_chained_audit(client, db, _world):
    _override(_world["admin_a"])
    try:
        r = client.post(
            CITIZEN_URL,
            json={"citizen_id": _world["national_citizen"].id, "canonical_id": _world["national_canonical"].id},
        )
    finally:
        _clear_override()
    assert r.status_code == 200, r.text
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "canonical_link_citizen")
        .one()
    )
    assert audit.chain_hash is not None
