"""Master Admin endpoints — platform-wide management.

Access levels:
  master_admin    100  — all endpoints
  ministry_admin   90  — can manage province_admin and below
  province_admin   80  — can manage admin and below within their province
  admin            50  — can manage staff/doctor/technician within their lab
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models.audit_log import AuditLog
from ..models.lab import Lab
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..models.user import User
from ..security.auth import hash_password
from ..security.dependencies import require_permission
from ..security.rate_limit import rate_limit_admin
from ..security.rbac import (
    ROLE_LEVELS,
    VALID_ROLES,
    can_manage_role,
    can_manage_user,
    get_role_level,
)
from ..security.session import bump_perm_version
from ..services.audit_service import log_action

logger = logging.getLogger("gula.admin")

router = APIRouter(prefix="/admin", tags=["admin"])

# ── Access control helpers ────────────────────────────────────────────────────


def require_admin(current_user: LabUser = Depends(require_permission("system:admin"))):
    """Require master_admin for platform-wide system operations."""
    return current_user


def require_manage_users(
    current_user: LabUser = Depends(require_permission("platform:manage_users")),
):
    """Require any role that has platform:manage_users permission."""
    return current_user


# ── Serialization helper ──────────────────────────────────────────────────────


def _user_dict(u: LabUser, lab_name: str | None = None) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "role_level": get_role_level(u.role),
        "lab_id": u.lab_id,
        "lab_name": lab_name,
        "province_id": u.province_id,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "created_by": u.created_by,
    }


# =============================================================================
# PLATFORM STATS
# =============================================================================


@router.get("/stats")
def platform_stats(admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)):
    """Platform-wide statistics (master_admin only)."""
    return {
        "total_labs": db.query(func.count(Lab.id)).scalar() or 0,
        "active_labs": db.query(func.count(Lab.id)).filter(Lab.is_active).scalar() or 0,
        "total_users": db.query(func.count(LabUser.id)).scalar() or 0,
        "total_patients": db.query(func.count(Patient.id)).scalar() or 0,
        "total_orders": db.query(func.count(LabOrder.id)).scalar() or 0,
        "total_results": db.query(func.count(LabResult.id)).scalar() or 0,
        "roles_breakdown": {
            role: db.query(func.count(LabUser.id)).filter(LabUser.role == role).scalar() or 0
            for role in VALID_ROLES
        },
    }


# =============================================================================
# LAB MANAGEMENT
# =============================================================================


@router.get("/labs")
def list_all_labs(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """List labs. Province admins see only their province's labs."""
    query = db.query(Lab)
    if actor.role == "province_admin" and actor.province_id:
        # Province admins can only see labs in their province via users
        lab_ids_in_province = [
            row[0]
            for row in db.query(LabUser.lab_id)
            .filter(LabUser.province_id == actor.province_id)
            .distinct()
            .all()
        ]
        query = query.filter(Lab.id.in_(lab_ids_in_province))
    elif actor.role == "admin":
        # Lab admins see only their own lab
        query = query.filter(Lab.id == actor.lab_id)

    total = query.count()
    labs = query.order_by(Lab.created_at.desc()).offset(skip).limit(limit).all()
    lab_ids = [l.id for l in labs]

    user_counts = (
        dict(
            db.query(LabUser.lab_id, func.count(LabUser.id))
            .filter(LabUser.lab_id.in_(lab_ids))
            .group_by(LabUser.lab_id)
            .all()
        )
        if lab_ids
        else {}
    )

    patient_counts = (
        dict(
            db.query(Patient.lab_id, func.count(Patient.id))
            .filter(Patient.lab_id.in_(lab_ids))
            .group_by(Patient.lab_id)
            .all()
        )
        if lab_ids
        else {}
    )

    return {
        "total": total,
        "labs": [
            {
                "id": l.id,
                "name": l.name,
                "city": l.city,
                "phone": l.phone,
                "license_number": l.license_number,
                "is_active": l.is_active,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "user_count": user_counts.get(l.id, 0),
                "patient_count": patient_counts.get(l.id, 0),
            }
            for l in labs
        ],
    }


@router.put("/labs/{lab_id}/toggle")
def toggle_lab(
    lab_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a lab (ministry_admin+ or province_admin for their province)."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    # Province admin: only own province
    if actor.role == "province_admin":
        has_lab = (
            db.query(LabUser)
            .filter(
                LabUser.lab_id == lab_id,
                LabUser.province_id == actor.province_id,
            )
            .first()
        )
        if not has_lab:
            raise HTTPException(status_code=403, detail="Lab not in your province")

    lab.is_active = not lab.is_active
    log_action(
        db,
        action="toggle_lab",
        resource_type="lab",
        resource_id=lab.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Lab {'activated' if lab.is_active else 'deactivated'}: {lab.name}",
    )
    db.commit()
    return {
        "message": f"Lab {'activated' if lab.is_active else 'deactivated'}",
        "is_active": lab.is_active,
    }


@router.put("/labs/{lab_id}/activate")
def activate_lab(
    lab_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Approve and activate a pending lab registration (and its admin user).
    Explicit activate-only endpoint — safer than toggle for the approval workflow.
    """
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    if lab.is_active:
        return {"message": "Lab is already active", "lab_id": lab_id, "is_active": True}

    lab.is_active = True

    # Also activate the lab's admin user(s) so they can log in
    db.query(LabUser).filter(
        LabUser.lab_id == lab_id,
        LabUser.role == "admin",
    ).update({"is_active": True})

    log_action(
        db,
        action="activate_lab",
        resource_type="lab",
        resource_id=lab.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Lab approved and activated: {lab.name}",
    )
    db.commit()
    return {"message": "Lab activated successfully", "lab_id": lab_id, "is_active": True}


@router.get("/labs/pending")
def list_pending_labs(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    """List labs pending activation (registered but not yet approved)."""
    query = db.query(Lab).filter(not Lab.is_active)

    if actor.role == "province_admin" and actor.province_id:
        lab_ids_in_province = [
            row[0]
            for row in db.query(LabUser.lab_id)
            .filter(LabUser.province_id == actor.province_id)
            .distinct()
            .all()
        ]
        query = query.filter(Lab.id.in_(lab_ids_in_province))

    total = query.count()
    labs = query.order_by(Lab.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for lab in labs:
        admin_user = (
            db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()
        )
        result.append(
            {
                "id": lab.id,
                "name": lab.name,
                "city": lab.city,
                "phone": lab.phone,
                "created_at": lab.created_at.isoformat() if lab.created_at else None,
                "admin_email": admin_user.email if admin_user else None,
                "admin_name": admin_user.name if admin_user else None,
            }
        )

    return {"total": total, "pending_labs": result}


# Update pending labs response to include new lab profile fields
@router.get("/labs/{lab_id}")
def get_lab_detail(
    lab_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Get full lab detail including new profile fields."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    admin_user = db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()
    staff_count = db.query(func.count(LabUser.id)).filter(LabUser.lab_id == lab.id).scalar() or 0
    patient_count = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab.id).scalar() or 0

    return {
        "id": lab.id,
        "name": lab.name,
        "license_number": lab.license_number,
        "lab_type": lab.lab_type,
        "director_name": lab.director_name,
        "website": lab.website,
        "city": lab.city,
        "address": lab.address,
        "phone": lab.phone,
        "is_active": lab.is_active,
        "created_at": lab.created_at.isoformat() if lab.created_at else None,
        "admin_email": admin_user.email if admin_user else None,
        "admin_name": admin_user.name if admin_user else None,
        "staff_count": staff_count,
        "patient_count": patient_count,
    }


# =============================================================================
# DOCTOR MANAGEMENT
# =============================================================================


@router.get("/doctors")
def list_doctors(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    is_verified: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    """List doctor accounts. ministry_admin and above.

    Pass is_verified=false to see doctors pending approval.
    """
    if actor.role not in ("master_admin", "ministry_admin", "province_admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(User).filter(User.role == "doctor")
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)

    total = query.count()
    doctors = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "doctors": [
            {
                "id": d.id,
                "full_name": d.full_name,
                "email": d.email,
                "phone": d.phone,
                "license_number": d.license_number,
                "specialty": d.specialty,
                "is_active": d.is_active,
                "is_verified": d.is_verified,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in doctors
        ],
    }


@router.put("/doctors/{doctor_id}/approve")
def approve_doctor(
    doctor_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Approve and verify a doctor registration.

    Sets is_verified=True and is_active=True so the doctor gains full
    API access. Only ministry_admin and above may approve.
    """
    if actor.role not in ("master_admin", "ministry_admin", "province_admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    doctor = db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(
            status_code=404,
            detail={"message": "Doctor not found", "message_ar": "الطبيب غير موجود"},
        )
    if doctor.is_verified:
        return {
            "message": "Doctor is already verified",
            "message_ar": "الطبيب موثق مسبقاً",
            "doctor_id": doctor_id,
        }

    doctor.is_verified = True
    doctor.is_active = True
    log_action(
        db,
        action="approve_doctor",
        resource_type="doctor",
        resource_id=doctor.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Doctor approved: {doctor.full_name} | license={doctor.license_number}",
    )
    db.commit()
    return {
        "message": "Doctor approved and verified",
        "message_ar": "تم اعتماد الطبيب بنجاح",
        "doctor_id": doctor_id,
        "is_verified": True,
    }


@router.put("/doctors/{doctor_id}/revoke")
def revoke_doctor(
    doctor_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Revoke a doctor's verification (e.g. expired license)."""
    if actor.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    doctor = db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_verified = False
    log_action(
        db,
        action="revoke_doctor",
        resource_type="doctor",
        resource_id=doctor.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Doctor verification revoked: {doctor.full_name} | license={doctor.license_number}",
    )
    db.commit()
    return {
        "message": "Doctor verification revoked",
        "message_ar": "تم إلغاء اعتماد الطبيب",
        "doctor_id": doctor_id,
        "is_verified": False,
    }


# =============================================================================
# CITIZEN MANAGEMENT
# =============================================================================


@router.get("/citizens")
def list_citizens(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    is_active: bool | None = None,
    is_verified: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    """List citizen accounts. ministry_admin+ only."""
    if actor.role not in ("master_admin", "ministry_admin", "province_admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(User).filter(User.role == "citizen")
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)

    total = query.count()
    citizens = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "citizens": [
            {
                "id": c.id,
                "full_name": c.full_name,
                "phone": c.phone,
                "email": c.email,
                "is_active": c.is_active,
                "is_verified": c.is_verified,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in citizens
        ],
    }


@router.put("/citizens/{citizen_id}/toggle")
def toggle_citizen(
    citizen_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a citizen account. ministry_admin+ only."""
    if actor.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    citizen = db.query(User).filter(User.id == citizen_id, User.role == "citizen").first()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")

    citizen.is_active = not citizen.is_active
    log_action(
        db,
        action="toggle_citizen",
        resource_type="citizen",
        resource_id=citizen.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Citizen {'activated' if citizen.is_active else 'deactivated'}: user_id={citizen.id}",
    )
    db.commit()
    return {
        "message": f"Citizen {'activated' if citizen.is_active else 'deactivated'}",
        "citizen_id": citizen_id,
        "is_active": citizen.is_active,
    }


@router.put("/citizens/{citizen_id}/verify")
def verify_citizen(
    citizen_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Mark a citizen account as verified (identity confirmed). ministry_admin+ only."""
    if actor.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    citizen = db.query(User).filter(User.id == citizen_id, User.role == "citizen").first()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")

    if citizen.is_verified:
        return {"message": "Citizen is already verified", "citizen_id": citizen_id}

    citizen.is_verified = True
    citizen.is_active = True  # Verified citizens are always active
    log_action(
        db,
        action="verify_citizen",
        resource_type="citizen",
        resource_id=citizen.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Citizen identity verified: user_id={citizen.id}",
    )
    db.commit()
    return {
        "message": "Citizen verified successfully",
        "citizen_id": citizen_id,
        "is_verified": True,
    }


class CreateLabRequest(BaseModel):
    name: str
    city: str = ""
    phone: str = ""
    admin_email: str
    admin_password: str
    admin_name: str
    province_id: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Lab name too short")
        return v

    @field_validator("admin_email")
    @classmethod
    def validate_email(cls, v):
        import re

        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email")
        return v


@router.post("/labs", status_code=201)
def create_lab(
    data: CreateLabRequest,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Create a new lab with its admin user."""
    if len(data.admin_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if db.query(LabUser).filter(LabUser.email == data.admin_email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    province_id = data.province_id
    # Province admin must assign to their own province
    if actor.role == "province_admin":
        province_id = actor.province_id

    lab = Lab(name=data.name, city=data.city, phone=data.phone)
    db.add(lab)
    db.flush()

    lab_admin = LabUser(
        lab_id=lab.id,
        name=data.admin_name,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
        role="admin",
        province_id=province_id,
        created_by=actor.id,
    )
    db.add(lab_admin)
    log_action(
        db,
        action="create_lab",
        resource_type="lab",
        resource_id=lab.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Created lab '{data.name}' with admin {data.admin_email}",
    )
    db.commit()
    return {"message": "Lab created", "lab_id": lab.id, "admin_email": data.admin_email}


# =============================================================================
# USER MANAGEMENT (Hierarchy-enforced)
# =============================================================================


@router.get("/users")
def list_users(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    role: str | None = None,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    """List users the actor is authorised to see."""
    actor_level = get_role_level(actor.role)
    query = db.query(LabUser)

    # Each role sees only users strictly below their level in the hierarchy
    visible_roles = [r for r, lvl in ROLE_LEVELS.items() if lvl < actor_level]
    if not visible_roles:
        return {"total": 0, "users": []}
    query = query.filter(LabUser.role.in_(visible_roles))

    # Province admin — own province only
    if actor.role == "province_admin" and actor.province_id:
        query = query.filter(LabUser.province_id == actor.province_id)

    # Lab admin — own lab only
    if actor.role == "admin":
        query = query.filter(LabUser.lab_id == actor.lab_id)

    if role:
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=400, detail=f"Invalid role. Valid: {sorted(VALID_ROLES)}"
            )
        if not can_manage_role(actor.role, role):
            raise HTTPException(status_code=403, detail="Cannot view users of that role level")
        query = query.filter(LabUser.role == role)

    if lab_id:
        query = query.filter(LabUser.lab_id == lab_id)

    total = query.count()
    users = query.order_by(LabUser.created_at.desc()).offset(skip).limit(limit).all()

    # Batch load lab names
    lab_ids = {u.lab_id for u in users}
    labs_map = (
        {l.id: l.name for l in db.query(Lab).filter(Lab.id.in_(lab_ids)).all()} if lab_ids else {}
    )

    return {
        "total": total,
        "users": [_user_dict(u, labs_map.get(u.lab_id)) for u in users],
    }


class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    lab_id: int | None = None
    province_id: int | None = None
    national_id: str | None = None  # raw — will be hashed server-side

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        import re

        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name too short")
        return v


@router.post("/users", status_code=201)
def create_user(
    request: Request,
    data: CreateUserRequest,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Create a new user. Role must be strictly below the actor's level."""
    rate_limit_admin(request, actor.id)
    # Hierarchy check
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {sorted(VALID_ROLES)}")
    if not can_manage_role(actor.role, data.role):
        raise HTTPException(
            status_code=403,
            detail=f"Cannot create a user with role '{data.role}' — must be below your level ({actor.role})",
        )

    # Password validation
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if data.password.isdigit() or data.password.isalpha():
        raise HTTPException(status_code=400, detail="Password must contain letters and numbers")

    # Email uniqueness
    if db.query(LabUser).filter(LabUser.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Determine lab_id
    target_lab_id = data.lab_id or actor.lab_id
    if actor.role == "admin":
        target_lab_id = actor.lab_id  # lab admin can only create in own lab

    # Lab must exist
    if not db.query(Lab).filter(Lab.id == target_lab_id, Lab.is_active).first():
        raise HTTPException(status_code=404, detail="Lab not found or inactive")

    # Determine province_id
    target_province = data.province_id
    if actor.role == "province_admin":
        target_province = actor.province_id

    # NID hashing
    nid_hash = None
    if data.national_id:
        nid_hash = _hash_nid(data.national_id)
        if db.query(LabUser).filter(LabUser.national_id_hash == nid_hash).first():
            raise HTTPException(status_code=409, detail="National ID already registered")

    new_user = LabUser(
        lab_id=target_lab_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        province_id=target_province,
        national_id_hash=nid_hash,
        created_by=actor.id,
        is_active=True,
    )
    db.add(new_user)

    log_action(
        db,
        action="create_user",
        resource_type="user",
        resource_id=None,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Created user {data.email} with role '{data.role}' in lab {target_lab_id}",
    )
    db.commit()
    db.refresh(new_user)

    lab = db.query(Lab).filter(Lab.id == target_lab_id).first()
    return {"message": "User created", "user": _user_dict(new_user, lab.name if lab else None)}


class ChangeRoleRequest(BaseModel):
    role: str
    province_id: int | None = None


@router.patch("/users/{user_id}/role")
def change_user_role(
    request: Request,
    user_id: int,
    data: ChangeRoleRequest,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    rate_limit_admin(request, actor.id)
    """Change a user's role. Both current and new role must be below actor's level."""
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {sorted(VALID_ROLES)}")

    target = db.query(LabUser).filter(LabUser.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Cannot modify self
    if target.id == actor.id:
        raise HTTPException(status_code=403, detail="Cannot modify your own role")

    # Hierarchy: can manage current role AND new role
    if not can_manage_user(actor, target):
        raise HTTPException(status_code=403, detail="Cannot modify a user at your level or above")
    if not can_manage_role(actor.role, data.role):
        raise HTTPException(
            status_code=403,
            detail=f"Cannot assign role '{data.role}' — must be below your level",
        )

    old_role = target.role
    target.role = data.role
    if data.province_id is not None:
        target.province_id = data.province_id

    # Bump perm_version to invalidate all existing JWTs for this user
    bump_perm_version(
        target,
        db,
        actor_id=actor.id,
        actor_role=actor.role,
        reason=f"role_change: {old_role} → {data.role}",
    )

    log_action(
        db,
        action="role_change",
        resource_type="user",
        resource_id=target.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Changed role of {target.email}: {old_role} → {data.role}",
    )
    db.commit()
    return {
        "message": "Role updated",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": data.role,
    }


@router.put("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user (must be below actor's level)."""
    target = db.query(LabUser).filter(LabUser.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == actor.id:
        raise HTTPException(status_code=403, detail="Cannot deactivate yourself")
    if not can_manage_user(actor, target):
        raise HTTPException(status_code=403, detail="Cannot modify a user at your level or above")

    target.is_active = not target.is_active
    bump_perm_version(target, db, actor_id=actor.id, actor_role=actor.role, reason="toggle_user")
    log_action(
        db,
        action="toggle_user",
        resource_type="user",
        resource_id=target.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"User {target.email} {'activated' if target.is_active else 'deactivated'}",
    )
    db.commit()
    return {"message": f"User {'activated' if target.is_active else 'deactivated'}"}


# =============================================================================
# AUDIT LOGS
# =============================================================================


@router.get("/audit-logs")
def get_audit_logs(
    actor: LabUser = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
    action: str | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
):
    """View audit logs. Admins see only their lab's logs; higher roles see all."""
    query = db.query(AuditLog)

    # Lab admins: only their users' actions
    if actor.role == "admin":
        lab_user_ids = [
            row[0] for row in db.query(LabUser.id).filter(LabUser.lab_id == actor.lab_id).all()
        ]
        query = query.filter(AuditLog.user_id.in_(lab_user_ids))

    if action:
        query = query.filter(AuditLog.action == action)
    if user_id and get_role_level(actor.role) >= 80:  # province_admin+
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "user_id": l.user_id,
                "user_role": l.user_role,
                "details": l.details,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }


# =============================================================================
# BOOTSTRAP — Master Admin
# =============================================================================

# Re-exported from core/seeds for backward compatibility.
# Startup import path: core/startup_guard → core/seeds (not routes).
from app.core.seeds import ensure_master_admin, hash_nid as _hash_nid  # noqa: F401


# =============================================================================
# CONTROL LAYER — Kill Switch (master_admin only)
# =============================================================================


class _KillSwitchRequest(BaseModel):
    reason: str = "manual"


@router.get("/kill-switch/status")
def kill_switch_status(admin: LabUser = Depends(require_admin)):
    """Return current kill switch state."""
    from ..core.kill_switch import status as ks_status

    return ks_status()


@router.post("/kill-switch/activate")
def kill_switch_activate(
    body: _KillSwitchRequest,
    admin: LabUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate the kill switch — halts all autonomous AI/repair actions platform-wide."""
    from ..core.kill_switch import activate as ks_activate

    result = ks_activate(reason=body.reason, propagate=True)
    log_action(
        db,
        action="kill_switch_activate",
        resource_type="system",
        resource_id=None,
        user_id=admin.id,
        user_role=admin.role,
        details=json.dumps({"reason": body.reason}),
    )
    db.commit()
    logger.critical(
        "[KILL-SWITCH] Activated by %s (id=%d) — reason: %s", admin.email, admin.id, body.reason
    )
    return result


@router.post("/kill-switch/deactivate")
def kill_switch_deactivate(
    body: _KillSwitchRequest,
    admin: LabUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Deactivate the kill switch — resumes autonomous actions."""
    from ..core.kill_switch import deactivate as ks_deactivate

    result = ks_deactivate(reason=body.reason, propagate=True)
    log_action(
        db,
        action="kill_switch_deactivate",
        resource_type="system",
        resource_id=None,
        user_id=admin.id,
        user_role=admin.role,
        details=json.dumps({"reason": body.reason}),
    )
    db.commit()
    logger.warning(
        "[KILL-SWITCH] Deactivated by %s (id=%d) — reason: %s", admin.email, admin.id, body.reason
    )
    return result


@router.get("/control-layer/stats")
def control_layer_stats(admin: LabUser = Depends(require_admin)):
    """Return Policy Engine and Auto-Repair statistics."""
    from ..core.auto_repair import auto_repair
    from ..core.policy_engine import policy_engine

    return {
        "policy": policy_engine.stats(),
        "auto_repair": auto_repair.stats(),
    }
