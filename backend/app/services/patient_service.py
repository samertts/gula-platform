"""Patient service - business logic layer for patient operations."""

import secrets
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.lab_order import LabOrder
from ..models.patient import Patient
from ..services.audit_service import log_action
from ..services.identity import hash_family_id, hash_national_id, match_score
from ..mpi import resolver as mpi_resolver


@dataclass
class PatientDict:
    """DTO for patient serialization."""

    id: int
    full_name: str
    phone: str
    birth_date: str | None
    gender: str | None
    email: str | None
    health_id: str | None
    is_minor: bool | None
    guardian_id: int | None
    has_national_id: bool
    has_family_id: bool
    created_at: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "birth_date": self.birth_date,
            "gender": self.gender,
            "email": self.email,
            "health_id": self.health_id,
            "is_minor": self.is_minor,
            "guardian_id": self.guardian_id,
            "has_national_id": self.has_national_id,
            "has_family_id": self.has_family_id,
            "created_at": self.created_at,
        }


def patient_to_dict(p: Patient) -> dict:
    """Convert Patient ORM to dict DTO."""
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


def list_patients(
    db: Session,
    lab_id: int,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    """List patients with optional search."""
    import re

    query = db.query(Patient).filter(Patient.lab_id == lab_id)

    if search:
        if re.match(r"^\+?\d+$", search):
            query = query.filter(Patient.phone.startswith(search))
        else:
            query = query.filter(Patient.full_name.ilike(f"%{search}%"))

    total = query.count()
    patients = query.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "patients": [patient_to_dict(p) for p in patients],
    }


def get_patient_by_id(db: Session, patient_id: int, lab_id: int) -> dict | None:
    """Get patient by ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()
    if not patient:
        return None
    return patient_to_dict(patient)


def create_patient(
    db: Session,
    lab_id: int,
    user_id: int,
    user_role: str,
    full_name: str,
    phone: str,
    birth_date: str | None = None,
    gender: str | None = None,
    email: str | None = None,
    national_id: str | None = None,
    family_id: str | None = None,
    force_create: bool = False,
    guardian_id: int | None = None,
    ip_address: str | None = None,
) -> dict:
    """Create a new patient with duplicate detection."""
    # Hash national ID and family ID if provided
    nid_hash = hash_national_id(national_id) if national_id else None
    fid_hash = hash_family_id(family_id) if family_id else None

    # Duplicate detection (unless force_create is True)
    if not force_create:
        duplicate_result = _check_duplicates(
            db,
            lab_id,
            full_name,
            phone,
            birth_date or "",
            nid_hash,
        )
        if duplicate_result:
            return duplicate_result

    # Validate guardian exists in the same lab if provided
    if guardian_id is not None:
        guardian = (
            db.query(Patient).filter(Patient.id == guardian_id, Patient.lab_id == lab_id).first()
        )
        if not guardian:
            return {"error": "Guardian patient not found in this lab", "status_code": 404}

    health_id = f"GULA-{secrets.token_hex(8).upper()}"

    patient = Patient(
        lab_id=lab_id,
        full_name=full_name,
        phone=phone,
        birth_date=birth_date,
        gender=gender,
        email=email,
        health_id=health_id,
        national_id_hash=nid_hash,
        family_id_hash=fid_hash,
        guardian_id=guardian_id,
    )
    db.add(patient)
    db.flush()

    # MPI resolution
    citizen_ulid, mpi_match_method = _resolve_mpi(
        db,
        patient,
        national_id,
        family_id,
        user_id,
        lab_id,
    )

    log_action(
        db,
        action="create",
        resource_type="patient",
        resource_id=patient.id,
        user_id=user_id,
        user_role=user_role,
        details=f"Created patient {patient.full_name} (phone={phone})",
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(patient)

    resp = patient_to_dict(patient)
    resp["citizen_ulid"] = citizen_ulid
    resp["mpi_match_method"] = mpi_match_method
    return {"message": "Patient created", "patient": resp}


def update_patient(
    db: Session,
    patient_id: int,
    lab_id: int,
    user_id: int,
    user_role: str,
    full_name: str | None = None,
    phone: str | None = None,
    birth_date: str | None = None,
    gender: str | None = None,
    email: str | None = None,
    family_id: str | None = None,
    ip_address: str | None = None,
) -> dict:
    """Update a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()
    if not patient:
        return {"error": "Patient not found", "status_code": 404}

    changed_fields = []
    if full_name is not None:
        patient.full_name = full_name
        changed_fields.append("full_name")
    if phone is not None:
        patient.phone = phone
        changed_fields.append("phone")
    if birth_date is not None:
        patient.birth_date = birth_date
        changed_fields.append("birth_date")
    if gender is not None:
        patient.gender = gender
        changed_fields.append("gender")
    if email is not None:
        patient.email = email
        changed_fields.append("email")
    if family_id is not None:
        patient.family_id_hash = hash_family_id(family_id) if family_id else None
        changed_fields.append("family_id")

    log_action(
        db,
        action="update",
        resource_type="patient",
        resource_id=patient_id,
        user_id=user_id,
        user_role=user_role,
        details=f"Updated fields: {', '.join(changed_fields)}",
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(patient)
    return {"message": "Patient updated", "patient": patient_to_dict(patient)}


def get_family_members(db: Session, family_id: str, lab_id: int) -> dict:
    """Return all patients sharing the same civil-registry family number."""
    import re

    cleaned = re.sub(r"\s", "", family_id)
    if not re.match(r"^\d{1,15}$", cleaned):
        return {"error": "Family ID must be 1-15 digits", "status_code": 400}

    fid_hash = hash_family_id(cleaned)

    members = (
        db.query(Patient)
        .filter(Patient.family_id_hash == fid_hash, Patient.lab_id == lab_id)
        .order_by(Patient.birth_date)
        .all()
    )

    if not members:
        return {"error": "No patients found with this family ID in your lab", "status_code": 404}

    # Attach order count + last visit for each member
    order_stats = {
        patient_id: (count, last_ts)
        for patient_id, count, last_ts in (
            db.query(LabOrder.patient_id, func.count(LabOrder.id), func.max(LabOrder.created_at))
            .filter(LabOrder.patient_id.in_([m.id for m in members]))
            .group_by(LabOrder.patient_id)
            .all()
        )
    }

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


def get_patient_children(db: Session, patient_id: int, lab_id: int) -> dict:
    """Return all minor patients (children) whose guardian is this patient."""
    guardian = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()
    if not guardian:
        return {"error": "Patient not found", "status_code": 404}

    children = (
        db.query(Patient)
        .filter(Patient.guardian_id == patient_id, Patient.lab_id == lab_id)
        .order_by(Patient.birth_date)
        .all()
    )

    return {
        "guardian": patient_to_dict(guardian),
        "children_count": len(children),
        "children": [patient_to_dict(c) for c in children],
    }


def _check_duplicates(
    db: Session,
    lab_id: int,
    full_name: str,
    phone: str,
    birth_date: str,
    nid_hash: str | None,
) -> dict | None:
    """Check for duplicate patients. Returns error dict if found, None otherwise."""
    # Check for exact national ID match first
    if nid_hash:
        existing = db.query(Patient).filter(Patient.national_id_hash == nid_hash).first()
        if existing:
            return {
                "error": {
                    "duplicate": True,
                    "message": "Patient with this national ID already exists",
                    "message_ar": "يوجد مريض مسجل بنفس الرقم الوطني",
                    "existing_patient": patient_to_dict(existing),
                },
                "status_code": 409,
            }

    # Pre-filter by phone (exact match) first
    phone_matches = (
        db.query(Patient).filter(Patient.lab_id == lab_id, Patient.phone == phone).limit(10).all()
    )

    duplicates = []
    for p in phone_matches:
        score = match_score(
            full_name,
            phone,
            birth_date,
            p.full_name,
            p.phone,
            str(p.birth_date) if p.birth_date else "",
            nid_hash,
            p.national_id_hash,
        )
        if score >= 0.65:
            duplicates.append({"patient": patient_to_dict(p), "score": round(score, 2)})

    # If no phone match, do name-based search
    if not duplicates:
        name_prefix = full_name.strip().split()[0] if full_name.strip() else ""
        if len(name_prefix) >= 2:
            name_matches = (
                db.query(Patient)
                .filter(Patient.lab_id == lab_id, Patient.full_name.ilike(f"{name_prefix}%"))
                .order_by(Patient.created_at.desc())
                .limit(50)
                .all()
            )

            for p in name_matches:
                score = match_score(
                    full_name,
                    phone,
                    birth_date,
                    p.full_name,
                    p.phone,
                    str(p.birth_date) if p.birth_date else "",
                    nid_hash,
                    p.national_id_hash,
                )
                if score >= 0.65:
                    duplicates.append({"patient": patient_to_dict(p), "score": round(score, 2)})

    if duplicates:
        return {
            "error": {
                "duplicate": True,
                "message": "Possible duplicate patients found. Set force_create=true to create anyway.",
                "message_ar": "تم العثور على مرضى مشابهين. استخدم force_create=true للإضافة رغم ذلك.",
                "matches": sorted(duplicates, key=lambda x: x["score"], reverse=True),
            },
            "status_code": 409,
        }

    return None


def _resolve_mpi(
    db: Session,
    patient: Patient,
    national_id: str | None,
    family_id: str | None,
    user_id: int,
    lab_id: int,
) -> tuple[str | None, str | None]:
    """Resolve MPI identity. Returns (citizen_ulid, match_method)."""
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
            lab_id=lab_id,
            local_patient_id=patient.id,
            name=patient.full_name,
            phone=patient.phone,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            gender=patient.gender,
            national_id=national_id,
            family_id=family_id,
            claimed_by_user_id=user_id,
        )
        citizen_ulid = outcome.citizen.citizen_ulid
        mpi_match_method = outcome.match_method
    except Exception as mpi_err:
        log_action(
            db,
            action="mpi_resolve_failed",
            resource_type="patient",
            resource_id=patient.id,
            user_id=user_id,
            user_role="system",
            details=f"MPI resolve failed: {type(mpi_err).__name__}: {str(mpi_err)[:200]}",
        )
    return citizen_ulid, mpi_match_method
