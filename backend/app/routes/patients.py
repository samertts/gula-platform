import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..models.patient import Patient
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip, rate_limit_user
from ..services.identity import normalize_name, match_score, hash_national_id, hash_family_id
from ..services.audit_service import log_action
from ..services.mpi import resolver as mpi_resolver

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientCreate(BaseModel):
    full_name: str
    phone: str
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    national_id: Optional[str] = None  # will be hashed before storage
    family_id: Optional[str] = None    # civil registry family number — hashed before storage
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
                raise ValueError("Invalid date")
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
    guardian_id: Optional[int] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    family_id: Optional[str] = None  # set/update civil registry family number

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


def patient_to_dict(p: Patient) -> dict:
    return {
        "id": p.id,
        "full_name": p.full_name,
        "phone": p.phone,
        "birth_date": str(p.birth_date) if p.birth_date else None,
        "gender": p.gender,
        "email": p.email,
        "health_id": p.health_id,
        "is_minor": p.is_minor,
        "guardian_id": p.guardian_id,
        "has_national_id": bool(p.national_id_hash),
        "has_family_id": bool(p.family_id_hash),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("")
def list_patients(
    request: Request,
    search: Optional[str] = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit_user(request, current_user.id, max_per_minute=120)
    query = db.query(Patient).filter(Patient.lab_id == current_user.lab_id)

    if search:
        # Optimization: If search looks like a phone number, use exact or prefix match to leverage index
        import re
        if re.match(r"^\+?\d+$", search):
            query = query.filter(Patient.phone.startswith(search))
        else:
            # For names, use prefix search if possible, or ilike if necessary
            query = query.filter(Patient.full_name.ilike(f"%{search}%"))

    total = query.count()
    patients = query.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "patients": [patient_to_dict(p) for p in patients],
    }


@router.post("", status_code=201)
def create_patient(
    data: PatientCreate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit_user(request, current_user.id, max_per_minute=30)
    # Hash national ID and family ID if provided
    nid_hash = hash_national_id(data.national_id) if data.national_id else None
    fid_hash = hash_family_id(data.family_id) if data.family_id else None

    # Duplicate detection (unless force_create is True)
    if not data.force_create:
        # Check for exact national ID match first
        if nid_hash:
            existing = db.query(Patient).filter(
                Patient.national_id_hash == nid_hash
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail={
                    "duplicate": True,
                    "message": "Patient with this national ID already exists",
                    "message_ar": "يوجد مريض مسجل بنفس الرقم الوطني",
                    "existing_patient": patient_to_dict(existing),
                })

        # OPTIMIZED: Pre-filter by phone (exact match) first - O(1) indexed lookup
        # Use startswith or exact match to leverage the index on phone column
        phone_matches = db.query(Patient).filter(
            Patient.lab_id == current_user.lab_id,
            Patient.phone == data.phone,
        ).limit(10).all()

        duplicates = []
        for p in phone_matches:
            score = match_score(
                data.full_name, data.phone, data.birth_date or "",
                p.full_name, p.phone, str(p.birth_date) if p.birth_date else "",
                nid_hash, p.national_id_hash,
            )
            if score >= 0.65:
                duplicates.append({"patient": patient_to_dict(p), "score": round(score, 2)})

        # If no phone match, do name-based search (limited scope)
        if not duplicates:
            name_prefix = data.full_name.strip().split()[0] if data.full_name.strip() else ""
            if len(name_prefix) >= 2:
                name_matches = db.query(Patient).filter(
                    Patient.lab_id == current_user.lab_id,
                    Patient.full_name.ilike(f"{name_prefix}%"),
                ).order_by(Patient.created_at.desc()).limit(50).all()

                for p in name_matches:
                    score = match_score(
                        data.full_name, data.phone, data.birth_date or "",
                        p.full_name, p.phone, str(p.birth_date) if p.birth_date else "",
                        nid_hash, p.national_id_hash,
                    )
                    if score >= 0.65:
                        duplicates.append({"patient": patient_to_dict(p), "score": round(score, 2)})

        if duplicates:
            raise HTTPException(status_code=409, detail={
                "duplicate": True,
                "message": "Possible duplicate patients found. Set force_create=true to create anyway.",
                "message_ar": "تم العثور على مرضى مشابهين. استخدم force_create=true للإضافة رغم ذلك.",
                "matches": sorted(duplicates, key=lambda x: x["score"], reverse=True),
            })

    # Validate guardian exists in the same lab if provided
    if data.guardian_id is not None:
        guardian = db.query(Patient).filter(
            Patient.id == data.guardian_id,
            Patient.lab_id == current_user.lab_id,
        ).first()
        if not guardian:
            raise HTTPException(status_code=404, detail={
                "message": "Guardian patient not found in this lab",
                "message_ar": "لم يتم العثور على ولي الأمر في هذا المختبر",
            })

    health_id = f"GULA-{secrets.token_hex(8).upper()}"

    patient = Patient(
        lab_id=current_user.lab_id,
        full_name=data.full_name,
        phone=data.phone,
        birth_date=data.birth_date,
        gender=data.gender,
        email=data.email,
        health_id=health_id,
        national_id_hash=nid_hash,
        family_id_hash=fid_hash,
        guardian_id=data.guardian_id,
    )
    db.add(patient)
    db.flush()

    # National unified-record linkage (MPI). Every lab patient resolves to a
    # single canonical Citizen so the same person across labs shares one
    # longitudinal record. Failure is non-fatal: we log and still return the
    # patient; a reconciler can re-run MPI later.
    birth_year = birth_month = birth_day = None
    if patient.birth_date:
        birth_year, birth_month, birth_day = (
            patient.birth_date.year,
            patient.birth_date.month,
            patient.birth_date.day,
        )
    citizen_ulid = None
    mpi_match_method = None
    try:
        outcome = mpi_resolver.resolve_identity(
            db,
            lab_id=current_user.lab_id,
            local_patient_id=patient.id,
            name=patient.full_name,
            phone=patient.phone,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            gender=patient.gender,
            national_id=data.national_id,
            family_id=data.family_id,
            claimed_by_user_id=current_user.id,
        )
        citizen_ulid = outcome.citizen.citizen_ulid
        mpi_match_method = outcome.match_method
    except Exception as mpi_err:
        log_action(
            db,
            action="mpi_resolve_failed",
            resource_type="patient",
            resource_id=patient.id,
            user_id=current_user.id,
            user_role=current_user.role,
            details=f"MPI resolve failed: {type(mpi_err).__name__}: {str(mpi_err)[:200]}",
        )

    db.commit()
    db.refresh(patient)

    resp = patient_to_dict(patient)
    resp["citizen_ulid"] = citizen_ulid
    resp["mpi_match_method"] = mpi_match_method
    return {"message": "Patient created", "patient": resp}


@router.get("/family/{family_id}")
def get_family_members(
    family_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all patients sharing the same civil-registry family number.

    The family_id is hashed before lookup — the raw number is never stored.
    Useful for viewing a patient's family health history side by side.
    """
    import re
    cleaned = re.sub(r"\s", "", family_id)
    if not re.match(r"^\d{1,15}$", cleaned):
        raise HTTPException(status_code=400, detail="Family ID must be 1-15 digits")

    fid_hash = hash_family_id(cleaned)

    members = db.query(Patient).filter(
        Patient.family_id_hash == fid_hash,
        Patient.lab_id == current_user.lab_id,
    ).order_by(Patient.birth_date).all()

    if not members:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No patients found with this family ID in your lab",
                "message_ar": "لا يوجد مرضى مسجلون بهذا الرقم العائلي في مختبرك",
            },
        )

    # Attach order count + last visit for each member — single extra query
    from ..models.lab_order import LabOrder
    from sqlalchemy import func

    order_stats = dict(
        db.query(LabOrder.patient_id, func.count(LabOrder.id), func.max(LabOrder.created_at))
        .filter(LabOrder.patient_id.in_([m.id for m in members]))
        .group_by(LabOrder.patient_id)
        .all()
    )

    result = []
    for m in members:
        stats = order_stats.get(m.id)
        member_dict = patient_to_dict(m)
        member_dict["order_count"] = stats[0] if stats else 0
        member_dict["last_visit"] = stats[1].isoformat() if stats and stats[1] else None
        result.append(member_dict)

    return {
        "family_member_count": len(result),
        "members": result,
    }


@router.get("/{patient_id}/children")
def get_patient_children(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all minor patients (children) whose guardian is this patient.

    Allows lab staff to view the full paediatric history of a guardian's
    dependents from a single screen.
    """
    guardian = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not guardian:
        raise HTTPException(status_code=404, detail="Patient not found")

    children = db.query(Patient).filter(
        Patient.guardian_id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).order_by(Patient.birth_date).all()

    return {
        "guardian": patient_to_dict(guardian),
        "children_count": len(children),
        "children": [patient_to_dict(c) for c in children],
    }


@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient_to_dict(patient)


@router.put("/{patient_id}")
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    changed_fields = list(data.model_dump(exclude_unset=True).keys())
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "family_id":
            # Convert raw family ID to hash before storing
            patient.family_id_hash = hash_family_id(value) if value else None
        else:
            setattr(patient, field, value)

    log_action(
        db,
        action="update",
        resource_type="patient",
        resource_id=patient_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated fields: {', '.join(changed_fields)}",
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(patient)
    return {"message": "Patient updated", "patient": patient_to_dict(patient)}
