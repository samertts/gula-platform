from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from ..security.rate_limit import get_client_ip, rate_limit_user
from ..services.patient_service import (
    create_patient as _create_patient,
)
from ..services.patient_service import (
    get_family_members as _get_family_members,
)
from ..services.patient_service import (
    get_patient_by_id as _get_patient_by_id,
)
from ..services.patient_service import (
    get_patient_children as _get_patient_children,
)
from ..services.patient_service import (
    list_patients as _list_patients,
)
from ..services.patient_service import (
    update_patient as _update_patient,
)

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientCreate(BaseModel):
    full_name: str
    phone: str
    birth_date: str | None = None
    gender: str | None = None
    email: str | None = None
    national_id: str | None = None  # will be hashed before storage
    family_id: str | None = None  # civil registry family number — hashed before storage
    force_create: bool = False  # skip duplicate check

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Name must be between 2 and 200 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        import re

        cleaned = re.sub(r"[\s\-\+]", "", v)
        if not re.match(r"^(07\d{9}|9647\d{9})$", cleaned):
            raise ValueError("Phone must be a valid Iraqi number (e.g. 07xxxxxxxxx)")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("male", "female", "M", "F"):
            raise ValueError("Gender must be 'male' or 'female'")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v):
        if v:
            import re
            from datetime import date

            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("Birth date must be YYYY-MM-DD format")
            try:
                d = date.fromisoformat(v)
                if d > date.today():
                    raise ValueError("Birth date cannot be in the future")
                if d.year < 1900:
                    raise ValueError("Birth date year must be after 1900")
            except ValueError as e:
                if "Birth date" in str(e):
                    raise
                raise ValueError("Invalid date") from e
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v:
            import re

            v = v.strip().lower()
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
                raise ValueError("Invalid email format")
            if len(v) > 100:
                raise ValueError("Email too long")
        return v

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, v):
        if v:
            import re

            cleaned = re.sub(r"\s", "", v)
            if not re.match(r"^\d{12,13}$", cleaned):
                raise ValueError("National ID must be 12-13 digits")
            return cleaned
        return v

    @field_validator("family_id")
    @classmethod
    def validate_family_id(cls, v):
        if v:
            import re

            cleaned = re.sub(r"\s", "", v)
            if not re.match(r"^\d{1,15}$", cleaned):
                raise ValueError("Family ID must be 1-15 digits")
            return cleaned
        return v

    # Guardian — ID of the parent/guardian patient record.
    # Strongly recommended when birth_date indicates the patient is under 18.
    guardian_id: int | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    email: str | None = None
    family_id: str | None = None  # set/update civil registry family number

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2 or len(v) > 200:
                raise ValueError("Name must be between 2 and 200 characters")
        return v

    @field_validator("family_id")
    @classmethod
    def validate_family_id(cls, v):
        if v is not None and v != "":
            import re

            cleaned = re.sub(r"\s", "", v)
            if not re.match(r"^\d{1,15}$", cleaned):
                raise ValueError("Family ID must be 1-15 digits")
            return cleaned
        return v


@router.get("")
def list_patients_route(
    request: Request,
    search: str | None = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    rate_limit_user(request, current_user.id, max_per_minute=120)
    return _list_patients(
        db=db,
        lab_id=current_user.lab_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post("", status_code=201)
def create_patient_route(
    data: PatientCreate,
    request: Request,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    rate_limit_user(request, current_user.id, max_per_minute=30)

    response = _create_patient(
        db=db,
        lab_id=current_user.lab_id,
        user_id=current_user.id,
        user_role=current_user.role,
        full_name=data.full_name,
        phone=data.phone,
        birth_date=data.birth_date,
        gender=data.gender,
        email=data.email,
        national_id=data.national_id,
        family_id=data.family_id,
        force_create=data.force_create,
        guardian_id=data.guardian_id,
        ip_address=get_client_ip(request),
    )

    if "error" in response:
        raise HTTPException(status_code=response["status_code"], detail=response["error"])

    return response


@router.get("/family/{family_id}")
def get_family_members_route(
    family_id: str,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    """Return all patients sharing the same civil-registry family number.

    The family_id is hashed before lookup — the raw number is never stored.
    Useful for viewing a patient's family health history side by side.
    """
    result = _get_family_members(db=db, family_id=family_id, lab_id=current_user.lab_id)

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return result


@router.get("/{patient_id}/children")
def get_patient_children_route(
    patient_id: int,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    """Return all minor patients (children) whose guardian is this patient.

    Allows lab staff to view the full paediatric history of a guardian's
    dependents from a single screen.
    """
    result = _get_patient_children(db=db, patient_id=patient_id, lab_id=current_user.lab_id)

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return result


@router.get("/{patient_id}")
def get_patient_route(
    patient_id: int,
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    result = _get_patient_by_id(db=db, patient_id=patient_id, lab_id=current_user.lab_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result


@router.put("/{patient_id}")
def update_patient_route(
    patient_id: int,
    data: PatientUpdate,
    request: Request,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    response = _update_patient(
        db=db,
        patient_id=patient_id,
        lab_id=current_user.lab_id,
        user_id=current_user.id,
        user_role=current_user.role,
        full_name=data.full_name,
        phone=data.phone,
        birth_date=data.birth_date,
        gender=data.gender,
        email=data.email,
        family_id=data.family_id,
        ip_address=get_client_ip(request),
    )

    if "error" in response:
        raise HTTPException(status_code=response["status_code"], detail=response["error"])

    return response
