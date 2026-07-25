import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from ..security.rate_limit import rate_limit_admin
from ..services.admin_service import (
    activate_lab,
    change_user_role,
    create_lab,
    create_user,
    get_audit_logs,
    get_lab_detail,
    get_platform_stats,
    list_labs,
    list_pending_labs,
    list_users,
    toggle_lab,
    toggle_user,
)
from ..services.audit_service import log_action

logger = logging.getLogger("gula.admin")

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: LabUser = Depends(require_permission("system:admin"))):
    return current_user


def require_manage_users(
    current_user: LabUser = Depends(require_permission("platform:manage_users")),
):
    return current_user


@router.get("/stats")
def platform_stats(admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)):
    return get_platform_stats(db)


@router.get("/labs")
def list_all_labs(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    return list_labs(actor, db, skip=skip, limit=limit)


@router.put("/labs/{lab_id}/toggle")
def toggle_lab_endpoint(
    lab_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    return toggle_lab(lab_id, actor, db)


@router.put("/labs/{lab_id}/activate")
def activate_lab_endpoint(
    lab_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    return activate_lab(lab_id, actor, db)


@router.get("/labs/pending")
def list_pending_labs_endpoint(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    return list_pending_labs(actor, db, skip=skip, limit=limit)


@router.get("/labs/{lab_id}")
def get_lab_detail_endpoint(
    lab_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    return get_lab_detail(lab_id, actor, db)


@router.get("/doctors")
def list_doctors(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    is_verified: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    if actor.role not in ("master_admin", "ministry_admin", "province_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    from ..models.user import User

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
    if actor.role not in ("master_admin", "ministry_admin", "province_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    from ..models.user import User

    doctor = db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if doctor.is_verified:
        return {"message": "Doctor is already verified", "doctor_id": doctor_id}
    doctor.is_verified = True
    doctor.is_active = True
    log_action(
        db,
        action="approve_doctor",
        resource_type="doctor",
        resource_id=doctor.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Doctor approved: {doctor.full_name}",
    )
    db.commit()
    return {"message": "Doctor approved and verified", "doctor_id": doctor_id, "is_verified": True}


@router.put("/doctors/{doctor_id}/revoke")
def revoke_doctor(
    doctor_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    if actor.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    from ..models.user import User

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
        details=f"Doctor verification revoked: {doctor.full_name}",
    )
    db.commit()
    return {"message": "Doctor verification revoked", "doctor_id": doctor_id, "is_verified": False}


@router.get("/citizens")
def list_citizens(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    is_active: bool | None = None,
    is_verified: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    if actor.role not in ("master_admin", "ministry_admin", "province_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    from ..models.user import User

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
    if actor.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    from ..models.user import User

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
        details=f"Citizen {'activated' if citizen.is_active else 'deactivated'}",
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
    if actor.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    from ..models.user import User

    citizen = db.query(User).filter(User.id == citizen_id, User.role == "citizen").first()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
    if citizen.is_verified:
        return {"message": "Citizen is already verified", "citizen_id": citizen_id}
    citizen.is_verified = True
    citizen.is_active = True
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
def create_lab_endpoint(
    data: CreateLabRequest,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    return create_lab(
        data.name,
        data.city,
        data.phone,
        data.admin_email,
        data.admin_password,
        data.admin_name,
        data.province_id,
        actor,
        db,
    )


@router.get("/users")
def list_users_endpoint(
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
    role: str | None = None,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
):
    return list_users(actor, db, role=role, lab_id=lab_id, skip=skip, limit=limit)


class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    lab_id: int | None = None
    province_id: int | None = None
    national_id: str | None = None

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
def create_user_endpoint(
    request: Request,
    data: CreateUserRequest,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    rate_limit_admin(request, actor.id)
    return create_user(
        data.name,
        data.email,
        data.password,
        data.role,
        data.lab_id,
        data.province_id,
        data.national_id,
        actor,
        db,
    )


class ChangeRoleRequest(BaseModel):
    role: str
    province_id: int | None = None


@router.patch("/users/{user_id}/role")
def change_user_role_endpoint(
    request: Request,
    user_id: int,
    data: ChangeRoleRequest,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    rate_limit_admin(request, actor.id)
    return change_user_role(user_id, data.role, data.province_id, actor, db)


@router.put("/users/{user_id}/toggle")
def toggle_user_endpoint(
    user_id: int,
    actor: LabUser = Depends(require_manage_users),
    db: Session = Depends(get_db),
):
    return toggle_user(user_id, actor, db)


@router.get("/audit-logs")
def get_audit_logs_endpoint(
    actor: LabUser = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
    action: str | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
):
    return get_audit_logs(actor, db, action=action, user_id=user_id, skip=skip, limit=limit)


from app.core.seeds import ensure_master_admin  # noqa: F401


class _KillSwitchRequest(BaseModel):
    reason: str = "manual"


@router.get("/kill-switch/status")
def kill_switch_status(admin: LabUser = Depends(require_admin)):
    from ..core.kill_switch import status as ks_status

    return ks_status()


@router.post("/kill-switch/activate")
def kill_switch_activate(
    body: _KillSwitchRequest, admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)
):
    from ..core.kill_switch import activate as ks_activate

    result = ks_activate(reason=body.reason, propagate=True)
    log_action(
        db,
        action="kill_switch_activate",
        resource_type="system",
        user_id=admin.id,
        user_role=admin.role,
        details=json.dumps({"reason": body.reason}),
    )
    db.commit()
    return result


@router.post("/kill-switch/deactivate")
def kill_switch_deactivate(
    body: _KillSwitchRequest, admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)
):
    from ..core.kill_switch import deactivate as ks_deactivate

    result = ks_deactivate(reason=body.reason, propagate=True)
    log_action(
        db,
        action="kill_switch_deactivate",
        resource_type="system",
        user_id=admin.id,
        user_role=admin.role,
        details=json.dumps({"reason": body.reason}),
    )
    db.commit()
    return result


@router.get("/control-layer/stats")
def control_layer_stats(admin: LabUser = Depends(require_admin)):
    from ..core.auto_repair import auto_repair
    from ..core.policy_engine import policy_engine

    return {"policy": policy_engine.stats(), "auto_repair": auto_repair.stats()}
