"""Health Identity management - create and link health IDs."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..security.dependencies import get_current_user, require_permission
from ..services.identity import hash_national_id

router = APIRouter(prefix="/identity", tags=["identity"])


class LinkIdentityRequest(BaseModel):
    patient_id: int
    national_id: str
    confirm_name: str | None = None


class LookupByIdentityRequest(BaseModel):
    national_id: str


@router.post("/link")
def link_national_id(
    data: LinkIdentityRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link a national ID to a patient's health record."""
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == data.patient_id,
            Patient.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    nid_hash = hash_national_id(data.national_id)

    # Check if another patient already has this national ID
    existing = (
        db.query(Patient)
        .filter(
            Patient.national_id_hash == nid_hash,
            Patient.id != patient.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This national ID is already linked to another patient record",
        )

    patient.national_id_hash = nid_hash
    db.commit()

    return {
        "message": "National ID linked successfully",
        "patient_id": patient.id,
        "health_id": patient.health_id,
    }


def _lookup_patient_by_nid(
    national_id: str,
    current_user: LabUser,
    db: Session,
) -> dict:
    """Shared lookup implementation (within the current lab)."""
    nid_hash = hash_national_id(national_id)
    patient = (
        db.query(Patient)
        .filter(
            Patient.national_id_hash == nid_hash,
            Patient.lab_id == current_user.lab_id,
        )
        .first()
    )

    if not patient:
        return {"found": False, "message": "No patient found with this national ID"}

    return {
        "found": True,
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "health_id": patient.health_id,
            "birth_date": str(patient.birth_date) if patient.birth_date else None,
        },
    }


@router.post("/lookup-by-nid")
def lookup_by_national_id_body(
    data: LookupByIdentityRequest,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    """Look up a patient by national ID sent in the request body.

    Preferred path: a protected identifier must not travel in a URL/query string
    where it is captured by access logs, proxies and browser history.
    """
    return _lookup_patient_by_nid(data.national_id, current_user, db)


@router.get("/lookup", deprecated=True)
def lookup_by_national_id(
    national_id: str,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    """DEPRECATED: use ``POST /identity/lookup-by-nid`` instead.

    Retained only for backward compatibility with existing clients; the NID in
    the query string is a privacy exposure that will be removed once clients
    are migrated (requires a separate owner-approved contract change).
    """
    return _lookup_patient_by_nid(national_id, current_user, db)
