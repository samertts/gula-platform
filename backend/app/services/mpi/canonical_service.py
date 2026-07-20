"""CanonicalPatient unification service.

Bridges LIMS Patient records and national Citizen records into a single
canonical identity. Provides find-or-create, merge, and link operations.
"""

import contextlib
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC
from app.models.canonical_patient import CanonicalPatient, CitizenLink, PatientLink
from app.models.patient import Patient
from app.services.mpi.models import Citizen


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
    """
    if target_id == source_id:
        from app.domain.exceptions import ConflictError, NotFoundError
        raise ConflictError("cannot merge a canonical into itself")

    target = db.query(CanonicalPatient).filter(CanonicalPatient.id == target_id).first()
    if target is None:
        raise NotFoundError("target canonical not found")

    source = db.query(CanonicalPatient).filter(CanonicalPatient.id == source_id).first()
    if source is None:
        raise NotFoundError("source canonical not found")

    db.query(PatientLink).filter(PatientLink.canonical_id == source_id).update(
        {"canonical_id": target_id}
    )
    db.query(CitizenLink).filter(CitizenLink.canonical_id == source_id).update(
        {"canonical_id": target_id}
    )

    source.lab_id = None
    source.national_id_hash = None
    source.health_id = None
    source.full_name = f"{source.full_name} (merged into {target_id})"
    source.is_verified = False
    source.version = source.version + 1

    target.version = target.version + 1
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
    """Create a PatientLink between a LIMS patient and a canonical record."""
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
        return existing

    link = PatientLink(
        patient_id=patient_id,
        canonical_id=canonical_id,
        linkage_method=method,
        confidence=confidence,
    )
    db.add(link)
    return link


def link_citizen(
    db: Session,
    citizen_id: int,
    canonical_id: int,
    method: str = "manual",
    confidence: float | None = None,
) -> CitizenLink:
    """Create a CitizenLink between a national citizen and a canonical record."""
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
        return existing

    link = CitizenLink(
        citizen_id=citizen_id,
        canonical_id=canonical_id,
        linkage_method=method,
        confidence=confidence,
    )
    db.add(link)
    return link
