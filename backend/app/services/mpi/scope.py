"""NR-148 — who may act inside the Master Patient Index, and over which records.

THE MPI IS DELIBERATELY CROSS-TENANT. THAT IS NOT THE DEFECT.
--------------------------------------------------------------
NR-022 decided it: Person/Identity is the canonical national subject, and
Patient and Citizen are contextual roles on top of it. A Master Patient Index
whose records stopped at a laboratory boundary could not do the one job it
exists for -- recognising that Lab A's patient and Lab B's patient are the same
person. `CanonicalPatient.lab_id` is therefore PROVENANCE ("which laboratory
first contributed this record"), not ownership, and the schema says so:

    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"),
                    nullable=True, index=True)

Nullable, and SET NULL on the lab's deletion -- the canonical record outlives
the laboratory. A tenant-owned row would be NOT NULL with CASCADE. There is no
(lab_id, ...) composite index either -- while `patients`, which IS tenant-owned,
carries ix_patients_lab_id and ix_patients_lab_phone -- and `PatientLink` / `CitizenLink` exist
precisely to bind per-tenant and national rows to one canonical person.

SO WHAT WAS THE DEFECT
----------------------
Two things, and neither is "the MPI crosses tenants":

  1. `CanonicalPatient(**data.model_dump())` let the REQUEST BODY set lab_id.
     Provenance that the client chooses is not provenance -- a laboratory could
     file a canonical record under another laboratory's name.

  2. Nothing distinguished the callers who may act nationally from the ones who
     may not. Every authenticated user -- a technician of a single private lab
     -- could search the entire national patient index by name or phone, read
     any canonical record, and MERGE two people's identities together.

A cross-tenant domain still needs a scope rule. It just needs a different one.

THE RULE, DERIVED FROM THE EXISTING MATRIX
------------------------------------------
No new permission is invented. `platform:view_stats` is already held by exactly
master_admin, ministry_admin and province_admin -- the roles the platform
already treats as seeing past a single laboratory -- and by no lab-scoped role.
That is the marker for national scope, so this module reads it rather than
adding a parallel vocabulary.

  * National scope  -> may search the index, merge identities, and link a
    national citizen to a canonical record.
  * Lab scope       -> may create canonical records (provenance = their own
    lab), and may read a canonical record they have a legitimate connection to:
    one linked to a patient of theirs, or one their own lab contributed.

Reaching for someone else's canonical record without that connection reads as
absent (404), not forbidden, so the index does not become an existence oracle
over the national population.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ...models.canonical_patient import CanonicalPatient
from ...security.rbac import get_permissions_for_role

#: The permission the platform already uses to mean "sees past one laboratory".
NATIONAL_SCOPE_PERMISSION = "platform:view_stats"

_NOT_FOUND = "canonical patient not found"


def has_national_scope(user) -> bool:
    """True when this caller may act across laboratories in the MPI."""
    role = getattr(user, "role", None)
    if not role:
        return False
    return NATIONAL_SCOPE_PERMISSION in get_permissions_for_role(role)


def require_national_scope(user, action: str) -> None:
    """Refuse a national MPI action to a laboratory-scoped caller.

    Used for the operations that are meaningless below the national level:
    searching the whole index, merging two identities, and binding a national
    citizen to a canonical record.
    """
    if not has_national_scope(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{action} requires national scope in the patient index",
        )


def provenance_lab_id(user) -> int | None:
    """The lab_id a record created by this caller is stamped with.

    Server-derived, always. A national caller has no lab, which is why the
    column is nullable -- their contributions carry no laboratory provenance
    rather than a borrowed one.
    """
    return getattr(user, "lab_id", None)


def visible_canonical(
    db: Session, canonical_id: int, user,
) -> CanonicalPatient | None:
    """The canonical record, if this caller may see it. Otherwise None.

    None rather than a 403: a laboratory must not be able to learn which
    canonical ids exist by probing for the difference.
    """
    canonical = (
        db.query(CanonicalPatient)
        .filter(CanonicalPatient.id == canonical_id)
        .first()
    )
    if canonical is None:
        return None
    if can_see_canonical(db, canonical, user):
        return canonical
    return None


def can_see_canonical(db: Session, canonical: CanonicalPatient, user) -> bool:
    """A national caller sees everything; a lab sees what it is connected to."""
    if has_national_scope(user):
        return True

    lab_id = getattr(user, "lab_id", None)
    if lab_id is None:
        return False

    # Provenance: this laboratory contributed the record.
    if canonical.lab_id is not None and canonical.lab_id == lab_id:
        return True

    # Linkage: the record is linked to one of this laboratory's own patients.
    return _linked_to_lab(db, canonical.id, lab_id)


def _linked_to_lab(db: Session, canonical_id: int, lab_id: int) -> bool:
    from ...models.canonical_patient import PatientLink
    from ...models.patient import Patient

    return (
        db.query(PatientLink.id)
        .join(Patient, Patient.id == PatientLink.patient_id)
        .filter(
            PatientLink.canonical_id == canonical_id,
            Patient.lab_id == lab_id,
        )
        .first()
        is not None
    )


def require_own_patient(db: Session, patient_id: int, user) -> None:
    """A laboratory may only link ITS OWN patient into the index.

    Without this, `POST /link-patient` would let one laboratory attach another
    laboratory's patient to any canonical person -- writing a false identity
    claim into the national index under someone else's name.
    """
    if has_national_scope(user):
        return

    from ...models.patient import Patient

    lab_id = getattr(user, "lab_id", None)
    owned = (
        db.query(Patient.id)
        .filter(Patient.id == patient_id, Patient.lab_id == lab_id)
        .first()
        if lab_id is not None
        else None
    )
    if owned is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="patient not found")


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
