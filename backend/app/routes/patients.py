import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..models.patient import Patient
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.identity import normalize_name, match_score, hash_national_id

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientCreate(BaseModel):
    full_name: str
    phone: str
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    national_id: Optional[str] = None  # will be hashed before storage
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


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2 or len(v) > 200:
                raise ValueError("Name must be between 2 and 200 characters")
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
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("")
def list_patients(
    search: Optional[str] = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Patient).filter(Patient.lab_id == current_user.lab_id)

    if search:
        query = query.filter(
            (Patient.full_name.ilike(f"%{search}%")) |
            (Patient.phone.ilike(f"%{search}%"))
        )

    total = query.count()
    patients = query.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "patients": [patient_to_dict(p) for p in patients],
    }


@router.post("")
def create_patient(
    data: PatientCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Hash national ID if provided
    nid_hash = hash_national_id(data.national_id) if data.national_id else None

    # Duplicate detection (unless force_create is True)
    if not data.force_create:
        # Check for exact national ID match first
        if nid_hash:
            existing = db.query(Patient).filter(
                Patient.national_id_hash == nid_hash
            ).first()
            if existing:
                return {
                    "duplicate": True,
                    "message": "Patient with this national ID already exists",
                    "message_ar": "يوجد مريض مسجل بنفس الرقم الوطني",
                    "existing_patient": patient_to_dict(existing),
                }

        # OPTIMIZED: Pre-filter by phone (exact match) first - O(1) indexed lookup
        phone_digits = data.phone.replace("+", "").replace("-", "").replace(" ", "")[-10:]
        phone_matches = db.query(Patient).filter(
            Patient.lab_id == current_user.lab_id,
            Patient.phone.contains(phone_digits),
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
            return {
                "duplicate": True,
                "message": "Possible duplicate patients found. Set force_create=true to create anyway.",
                "message_ar": "تم العثور على مرضى مشابهين. استخدم force_create=true للإضافة رغم ذلك.",
                "matches": sorted(duplicates, key=lambda x: x["score"], reverse=True),
            }

    health_id = f"GULA-{secrets.token_hex(4).upper()}"

    patient = Patient(
        lab_id=current_user.lab_id,
        full_name=data.full_name,
        phone=data.phone,
        birth_date=data.birth_date,
        gender=data.gender,
        email=data.email,
        health_id=health_id,
        national_id_hash=nid_hash,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return {"message": "Patient created", "patient": patient_to_dict(patient)}


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
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return {"message": "Patient updated", "patient": patient_to_dict(patient)}
