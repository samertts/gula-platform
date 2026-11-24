"""CanonicalPatient unification service.

Bridges LIMS Patient records and national Citizen records into a single
canonical identity. Provides find-or-create, merge, and link operations.
"""

import contextlib
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError
from app.models.canonical_patient import CanonicalPatient, CitizenLink, PatientLink
from app.models.patient import Patient
from app.services.mpi.models import Citizen
from app.services.mpi.reliability import acquire_canonical_link_lock, atomic_increment_version


def find_or_create_canonical(
    db: Session,
    patient_or_citizen: Patient | Citizen,
) -> CanonicalPatient:
    """Find an existing canonical for the given patient or citizen, or create one.

    For Patients: checks PatientLink table first, then falls back to creating
    a new CanonicalPatient from the Patient's data.
    For Citizens: checks CitizenLink table first, then falls back to creating
    a new CanonicalPatient from the Citizen's data.
    """
    if isinstance(patient_or_citizen, Patient):
        existing = get_canonical_by_patient(db, patient_or_citizen.id)
        if existing is not None:
            return existing
        canonical = CanonicalPatient(
            lab_id=patient_or_citizen.lab_id,
            national_id_hash=patient_or_citizen.national_id_hash,
            health_id=patient_or_citizen.health_id,
            full_name=patient_or_citizen.full_name,
            full_name_ar=None,
            date_of_birth=(
                datetime.combine(patient_or_citizen.birth_date, datetime.min.time())
                if patient_or_citizen.birth_date
                else None
            ),
            gender=patient_or_citizen.gender,
            phone=patient_or_citizen.phone,
            email=patient_or_citizen.email,
            source_system="lims",
            source_id=str(patient_or_citizen.id),
        )
        db.add(canonical)
        db.flush()
        link = PatientLink(
            patient_id=patient_or_citizen.id,
            canonical_id=canonical.id,
            linkage_method="auto_create",
            confidence=1.0,
        )
        db.add(link)
        return canonical

    if isinstance(patient_or_citizen, Citizen):
        existing = get_canonical_by_citizen(db, patient_or_citizen.id)
        if existing is not None:
            return existing
        by = patient_or_citizen.birth_year
        bm = patient_or_citizen.birth_month
        bd = patient_or_citizen.birth_day
        dob = None
        if by is not None and bm is not None and bd is not None:
            with contextlib.suppress(ValueError, OverflowError):
                dob = datetime(by, bm, bd, tzinfo=UTC)
        canonical = CanonicalPatient(
            national_id_hash=patient_or_citizen.nid_hash,
            full_name=patient_or_citizen.name_canonical,
            date_of_birth=dob,
            gender=patient_or_citizen.gender,
            source_system="mpi",
            source_id=str(patient_or_citizen.id),
        )
        db.add(canonical)
        db.flush()
        link = CitizenLink(
            citizen_id=patient_or_citizen.id,
            canonical_id=canonical.id,
            linkage_method="auto_create",
            confidence=1.0,
        )
        db.add(link)
        return canonical

    raise TypeError(f"Expected Patient or Citizen, got {type(patient_or_citizen).__name__}")


def merge_canonicals(
    db: Session,
    target_id: int,
    source_id: int,
) -> CanonicalPatient:
    """Merge two canonical records into one.

    The source canonical's links are reassigned to the target.
    The source record is NOT deleted — it remains orphaned for audit trail.

    MPI-02/03: the two rows are locked in a single ascending-id statement so
    concurrent merges cannot deadlock on opposite acquisition order, and both
    version counters are incremented by the database rather than by a blind
    read-modify-write. The caller owns the outer commit.
    """
    if target_id == source_id:
        raise ConflictError("cannot merge a canonical into itself")

    rows = (
        db.query(CanonicalPatient)
        .filter(CanonicalPatient.id.in_((target_id, source_id)))
        .order_by(CanonicalPatient.id.asc())
        .with_for_update()
        .all()
    )
    by_id = {r.id: r for r in rows}
    target = by_id.get(target_id)
    if target is None:
        raise NotFoundError("target canonical not found")
    source = by_id.get(source_id)
    if source is None:
        raise NotFoundError("source canonical not found")

    db.query(PatientLink).filter(PatientLink.canonical_id == source_id).update(
        {"canonical_id": target_id},
    )
    db.query(CitizenLink).filter(CitizenLink.canonical_id == source_id).update(
        {"canonical_id": target_id},
    )

    source.lab_id = None
    source.national_id_hash = None
    source.health_id = None
    source.full_name = f"{source.full_name} (merged into {target_id})"
    source.is_verified = False
    atomic_increment_version(db, source, CanonicalPatient)

    atomic_increment_version(db, target, CanonicalPatient)
    target.updated_at = datetime.now(UTC)

    return target


def get_canonical_by_patient(db: Session, patient_id: int) -> CanonicalPatient | None:
    """Return the canonical record linked to the given patient ID."""
    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient_id)
        .first()
    )
    if link is None:
        return None
    return db.query(CanonicalPatient).filter(CanonicalPatient.id == link.canonical_id).first()


def get_canonical_by_citizen(db: Session, citizen_id: int) -> CanonicalPatient | None:
    """Return the canonical record linked to the given citizen ID."""
    link = (
        db.query(CitizenLink)
        .filter(CitizenLink.citizen_id == citizen_id)
        .first()
    )
    if link is None:
        return None
    return db.query(CanonicalPatient).filter(CanonicalPatient.id == link.canonical_id).first()


def link_patient(
    db: Session,
    patient_id: int,
    canonical_id: int,
    method: str = "manual",
    confidence: float | None = None,
) -> PatientLink:
    """Create a PatientLink between a LIMS patient and a canonical record.

    AUD-02 (conflict-safe, no DDL): the check-then-insert is serialised by a
    transaction-scoped advisory lock because the tables currently have only
    non-unique indexes.  A patient may be linked to at most ONE canonical: a
    request to point an already-linked patient at a *different* canonical is a
    conflict (HTTP 409 at the route), not a silent second row that would strand
    one canonical behind ``get_canonical_by_patient().first()``.  The database
    UNIQUE(patient_id) constraint is proposed (not executed) in the AUD-02
    Migration Proposal as defence in depth.
    """
    acquire_canonical_link_lock(db)

    by_patient = (
        db.query(PatientLink).filter(PatientLink.patient_id == patient_id).first()
    )
    if by_patient is not None and by_patient.canonical_id != canonical_id:
        raise ConflictError("patient is already linked to a different canonical")

    existing = (
        db.query(PatientLink)
        .filter(
            PatientLink.patient_id == patient_id,
            PatientLink.canonical_id == canonical_id,
        )
        .first()
    )
    if existing is not None:
        existing.linkage_method = method
        if confidence is not None:
            existing.confidence = confidence
        db.flush()
        return existing

    link = PatientLink(
        patient_id=patient_id,
        canonical_id=canonical_id,
        linkage_method=method,
        confidence=confidence,
    )
    db.add(link)
    db.flush()  # surface integrity errors inside the lock, before route commit
    return link


def link_citizen(
    db: Session,
    citizen_id: int,
    canonical_id: int,
    method: str = "manual",
    confidence: float | None = None,
) -> CitizenLink:
    """Create a CitizenLink between a national citizen and a canonical record.

    AUD-02: same conflict-safe semantics as :func:`link_patient`; one canonical
    per citizen, no silent duplicate rows.
    """
    acquire_canonical_link_lock(db)

    by_citizen = (
        db.query(CitizenLink).filter(CitizenLink.citizen_id == citizen_id).first()
    )
    if by_citizen is not None and by_citizen.canonical_id != canonical_id:
        raise ConflictError("citizen is already linked to a different canonical")

    existing = (
        db.query(CitizenLink)
        .filter(
            CitizenLink.citizen_id == citizen_id,
            CitizenLink.canonical_id == canonical_id,
        )
        .first()
    )
    if existing is not None:
        existing.linkage_method = method
        if confidence is not None:
            existing.confidence = confidence
        db.flush()
        return existing

    link = CitizenLink(
        citizen_id=citizen_id,
        canonical_id=canonical_id,
        linkage_method=method,
        confidence=confidence,
    )
    db.add(link)
    db.flush()
    return link
