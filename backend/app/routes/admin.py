"""Master Admin endpoints - platform-wide management."""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone

from ..database import get_db, SessionLocal
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.patient import Patient
from ..models.audit_log import AuditLog
from ..security.dependencies import get_current_user
from ..security.auth import hash_password
from ..services.audit_service import log_action

logger = logging.getLogger("gula.admin")

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: LabUser = Depends(get_current_user)):
    """Only allow master_admin for platform-wide admin operations."""
    if current_user.role != "master_admin":
        raise HTTPException(status_code=403, detail="Master admin access required")
    return current_user


# ===== PLATFORM STATS =====
@router.get("/stats")
def platform_stats(admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)):
    """Platform-wide statistics."""
    return {
        "total_labs": db.query(func.count(Lab.id)).scalar() or 0,
        "active_labs": db.query(func.count(Lab.id)).filter(Lab.is_active == True).scalar() or 0,
        "total_users": db.query(func.count(LabUser.id)).scalar() or 0,
        "total_patients": db.query(func.count(Patient.id)).scalar() or 0,
        "total_orders": db.query(func.count(LabOrder.id)).scalar() or 0,
        "total_results": db.query(func.count(LabResult.id)).scalar() or 0,
    }


# ===== LAB MANAGEMENT =====
@router.get("/labs")
def list_all_labs(
    admin: LabUser = Depends(require_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """List all labs on the platform."""
    from sqlalchemy.orm import subqueryload
    labs = db.query(Lab).order_by(Lab.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(func.count(Lab.id)).scalar() or 0

    # Batch query counts to avoid N+1
    lab_ids = [l.id for l in labs]
    user_counts = dict(
        db.query(LabUser.lab_id, func.count(LabUser.id))
        .filter(LabUser.lab_id.in_(lab_ids))
        .group_by(LabUser.lab_id)
        .all()
    ) if lab_ids else {}
    patient_counts = dict(
        db.query(Patient.lab_id, func.count(Patient.id))
        .filter(Patient.lab_id.in_(lab_ids))
        .group_by(Patient.lab_id)
        .all()
    ) if lab_ids else {}

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
def toggle_lab(lab_id: int, admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)):
    """Activate or deactivate a lab."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    lab.is_active = not lab.is_active
    log_action(db, action="toggle_lab", resource_type="lab", resource_id=lab.id,
               user_id=admin.id, user_role=admin.role,
               details=f"Lab {'activated' if lab.is_active else 'deactivated'}: {lab.name}")
    db.commit()
    return {"message": f"Lab {'activated' if lab.is_active else 'deactivated'}", "is_active": lab.is_active}


class CreateLabRequest(BaseModel):
    name: str
    city: str = ""
    phone: str = ""
    admin_email: str
    admin_password: str
    admin_name: str


@router.post("/labs")
def create_lab_admin(
    data: CreateLabRequest,
    admin: LabUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new lab with its admin user."""
    name = data.name
    city = data.city
    phone = data.phone
    admin_email = data.admin_email
    admin_password = data.admin_password
    admin_name = data.admin_name

    if len(admin_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if db.query(LabUser).filter(LabUser.email == admin_email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    lab = Lab(name=name, city=city, phone=phone)
    db.add(lab)
    db.flush()

    lab_admin = LabUser(
        lab_id=lab.id,
        name=admin_name,
        email=admin_email,
        password_hash=hash_password(admin_password),
        role="admin",
    )
    db.add(lab_admin)
    log_action(db, action="create_lab", resource_type="lab", resource_id=lab.id,
               user_id=admin.id, user_role=admin.role, details=f"Created lab: {name}")
    db.commit()
    return {"message": "Lab created", "lab_id": lab.id, "admin_email": admin_email}


# ===== USER MANAGEMENT =====
@router.get("/users")
def list_users(
    admin: LabUser = Depends(require_admin),
    db: Session = Depends(get_db),
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """List all users, optionally filtered by role."""
    VALID_ROLES = {"admin", "staff", "technician", "master_admin"}
    query = db.query(LabUser)
    if role:
        if role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="Invalid role")
        query = query.filter(LabUser.role == role)
    total = query.count()
    users = query.order_by(LabUser.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "lab_id": u.lab_id,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.put("/users/{user_id}/toggle")
def toggle_user(user_id: int, admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)):
    """Activate or deactivate a user."""
    user = db.query(LabUser).filter(LabUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "master_admin":
        raise HTTPException(status_code=403, detail="Cannot modify master admin")
    user.is_active = not user.is_active
    log_action(db, action="toggle_user", resource_type="user", resource_id=user.id,
               user_id=admin.id, user_role=admin.role)
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}"}


# ===== AUDIT LOGS =====
@router.get("/audit-logs")
def get_audit_logs(
    admin: LabUser = Depends(require_admin),
    db: Session = Depends(get_db),
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """View system audit logs."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
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


# ===== BOOTSTRAP =====
def ensure_master_admin():
    """Create master admin on first startup if not exists."""
    db = SessionLocal()
    try:
        existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()
        if existing:
            return

        email = os.getenv("GULA_ADMIN_EMAIL", "admin@gula-platform.org")
        password = os.getenv("GULA_ADMIN_PASSWORD")
        if not password:
            import secrets
            password = secrets.token_urlsafe(24)
            # SECURITY: Never log passwords - write to a temporary file instead
            _pw_file = "/tmp/.gula_admin_pw"
            try:
                with open(_pw_file, "w") as f:
                    f.write(password)
                os.chmod(_pw_file, 0o600)
                logger.warning(
                    "[GULA] GULA_ADMIN_PASSWORD not set. Temporary password written to %s. "
                    "Set GULA_ADMIN_PASSWORD in .env and delete this file.", _pw_file
                )
            except OSError:
                logger.warning(
                    "[GULA] GULA_ADMIN_PASSWORD not set. Could not write temp file. "
                    "Set GULA_ADMIN_PASSWORD in .env for production."
                )
        name = os.getenv("GULA_ADMIN_NAME", "GULA Admin")

        # Create a platform-level lab for admin
        platform_lab = db.query(Lab).filter(Lab.name == "GULA Platform").first()
        if not platform_lab:
            platform_lab = Lab(name="GULA Platform", city="Platform", is_active=True)
            db.add(platform_lab)
            db.flush()

        admin = LabUser(
            lab_id=platform_lab.id,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="master_admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info(f"Master admin created: {email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create master admin: {e}")
    finally:
        db.close()
