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

    # NR-150. This checked the WHOLE patients table with no lab_id filter, two
    # lines below a query that scopes correctly to current_user.lab_id. Any lab
    # could create one throwaway patient and loop this endpoint over candidate
    # national IDs: 409 meant "that ID exists somewhere in the country", 200
    # meant it did not, and the same throwaway row could be reused forever
    # because the hash is overwritten on success. Iraqi national IDs are
    # structured and enumerable, so that is an oracle over the population.
    #
    # Scoped to the caller's own laboratory. Cross-laboratory identity
    # resolution is not this endpoint's job -- it is exactly what the Master
    # Patient Index exists for, where it is gated by national scope (NR-148).
    existing = (
        db.query(Patient)
        .filter(
            Patient.national_id_hash == nid_hash,
            Patient.id != patient.id,
            Patient.lab_id == current_user.lab_id,
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


@router.get("/lookup")
def lookup_by_national_id(
    national_id: str,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    """Look up a patient by national ID (within the current lab)."""
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
