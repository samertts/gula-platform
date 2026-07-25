from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog
from ..models.lab import Lab
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..security.auth import hash_password
from ..security.rbac import (
    ROLE_LEVELS,
    VALID_ROLES,
    can_manage_role,
    can_manage_user,
    get_role_level,
)
from ..security.session import bump_perm_version
from ..services.audit_service import log_action


def get_platform_stats(db: Session) -> dict:
    total_labs = db.query(func.count(Lab.id)).scalar() or 0
    active_labs = db.query(func.count(Lab.id)).filter(Lab.is_active).scalar() or 0
    total_users = db.query(func.count(LabUser.id)).scalar() or 0
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_orders = db.query(func.count(LabOrder.id)).scalar() or 0
    total_results = db.query(func.count(LabResult.id)).scalar() or 0
    roles_breakdown = {
        role: db.query(func.count(LabUser.id)).filter(LabUser.role == role).scalar() or 0
        for role in VALID_ROLES
    }
    return {
        "total_labs": total_labs,
        "active_labs": active_labs,
        "total_users": total_users,
        "total_patients": total_patients,
        "total_orders": total_orders,
        "total_results": total_results,
        "roles_breakdown": roles_breakdown,
    }


def list_labs(actor: LabUser, db: Session, skip: int = 0, limit: int = 50) -> dict:
    query = db.query(Lab)
    if actor.role == "province_admin" and actor.province_id:
        lab_ids = [
            row[0]
            for row in db.query(LabUser.lab_id)
            .filter(LabUser.province_id == actor.province_id)
            .distinct()
            .all()
        ]
        query = query.filter(Lab.id.in_(lab_ids))
    elif actor.role == "admin":
        query = query.filter(Lab.id == actor.lab_id)

    total = query.count()
    labs = query.order_by(Lab.created_at.desc()).offset(skip).limit(limit).all()
    lab_ids = [lab.id for lab in labs]

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
                "id": lab.id,
                "name": lab.name,
                "city": lab.city,
                "phone": lab.phone,
                "license_number": lab.license_number,
                "is_active": lab.is_active,
                "created_at": lab.created_at.isoformat() if lab.created_at else None,
                "user_count": user_counts.get(lab.id, 0),
                "patient_count": patient_counts.get(lab.id, 0),
            }
            for lab in labs
        ],
    }


def toggle_lab(lab_id: int, actor: LabUser, db: Session) -> dict:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
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


def activate_lab(lab_id: int, actor: LabUser, db: Session) -> dict:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    if lab.is_active:
        return {"message": "Lab is already active", "lab_id": lab_id, "is_active": True}
    lab.is_active = True
    db.query(LabUser).filter(LabUser.lab_id == lab_id, LabUser.role == "admin").update(
        {"is_active": True}
    )
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


def list_pending_labs(actor: LabUser, db: Session, skip: int = 0, limit: int = 50) -> dict:
    query = db.query(Lab).filter(Lab.is_active == False)
    if actor.role == "province_admin" and actor.province_id:
        lab_ids = [
            row[0]
            for row in db.query(LabUser.lab_id)
            .filter(LabUser.province_id == actor.province_id)
            .distinct()
            .all()
        ]
        query = query.filter(Lab.id.in_(lab_ids))
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


def get_lab_detail(lab_id: int, _actor: LabUser, db: Session) -> dict:
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


def user_dict(u: LabUser, lab_name: str | None = None) -> dict:
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


def create_lab(
    name: str,
    city: str,
    phone: str,
    admin_email: str,
    admin_password: str,
    admin_name: str,
    province_id: int | None,
    actor: LabUser,
    db: Session,
) -> dict:
    if len(admin_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if db.query(LabUser).filter(LabUser.email == admin_email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    target_province = province_id
    if actor.role == "province_admin":
        target_province = actor.province_id
    lab = Lab(name=name, city=city, phone=phone)
    db.add(lab)
    db.flush()
    lab_admin = LabUser(
        lab_id=lab.id,
        name=admin_name,
        email=admin_email,
        password_hash=hash_password(admin_password),
        role="admin",
        province_id=target_province,
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
        details=f"Created lab '{name}' with admin {admin_email}",
    )
    db.commit()
    return {"message": "Lab created", "lab_id": lab.id, "admin_email": admin_email}


def list_users(
    actor: LabUser,
    db: Session,
    role: str | None = None,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    actor_level = get_role_level(actor.role)
    query = db.query(LabUser)
    visible_roles = [r for r, lvl in ROLE_LEVELS.items() if lvl < actor_level]
    if not visible_roles:
        return {"total": 0, "users": []}
    query = query.filter(LabUser.role.in_(visible_roles))
    if actor.role == "province_admin" and actor.province_id:
        query = query.filter(LabUser.province_id == actor.province_id)
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
    lab_ids_set = {u.lab_id for u in users}
    labs_map = (
        {lab.id: lab.name for lab in db.query(Lab).filter(Lab.id.in_(lab_ids_set)).all()}
        if lab_ids_set
        else {}
    )
    return {"total": total, "users": [user_dict(u, labs_map.get(u.lab_id)) for u in users]}


def create_user(
    name: str,
    email: str,
    password: str,
    target_role: str,
    lab_id: int | None,
    province_id: int | None,
    national_id: str | None,
    actor: LabUser,
    db: Session,
) -> dict:
    if target_role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {sorted(VALID_ROLES)}")
    if not can_manage_role(actor.role, target_role):
        raise HTTPException(status_code=403, detail=f"Cannot create user with role '{target_role}'")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if password.isdigit() or password.isalpha():
        raise HTTPException(status_code=400, detail="Password must contain letters and numbers")
    if db.query(LabUser).filter(LabUser.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    target_lab_id = lab_id or actor.lab_id
    if actor.role == "admin":
        target_lab_id = actor.lab_id
    if not db.query(Lab).filter(Lab.id == target_lab_id, Lab.is_active).first():
        raise HTTPException(status_code=404, detail="Lab not found or inactive")
    target_province = province_id
    if actor.role == "province_admin":
        target_province = actor.province_id
    nid_hash = None
    if national_id:
        from app.core.seeds import hash_nid

        nid_hash = hash_nid(national_id)
        if db.query(LabUser).filter(LabUser.national_id_hash == nid_hash).first():
            raise HTTPException(status_code=409, detail="National ID already registered")
    new_user = LabUser(
        lab_id=target_lab_id,
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=target_role,
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
        user_id=actor.id,
        user_role=actor.role,
        details=f"Created user {email} with role '{target_role}'",
    )
    db.commit()
    db.refresh(new_user)
    lab = db.query(Lab).filter(Lab.id == target_lab_id).first()
    return {"message": "User created", "user": user_dict(new_user, lab.name if lab else None)}


def change_user_role(
    user_id: int, new_role: str, province_id: int | None, actor: LabUser, db: Session
) -> dict:
    if new_role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {sorted(VALID_ROLES)}")
    target = db.query(LabUser).filter(LabUser.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == actor.id:
        raise HTTPException(status_code=403, detail="Cannot modify your own role")
    if not can_manage_user(actor, target):
        raise HTTPException(status_code=403, detail="Cannot modify a user at your level or above")
    if not can_manage_role(actor.role, new_role):
        raise HTTPException(status_code=403, detail=f"Cannot assign role '{new_role}'")
    old_role = target.role
    target.role = new_role
    if province_id is not None:
        target.province_id = province_id
    bump_perm_version(
        target,
        db,
        actor_id=actor.id,
        actor_role=actor.role,
        reason=f"role_change: {old_role}->{new_role}",
    )
    log_action(
        db,
        action="role_change",
        resource_type="user",
        resource_id=target.id,
        user_id=actor.id,
        user_role=actor.role,
        details=f"Changed role of {target.email}: {old_role} -> {new_role}",
    )
    db.commit()
    return {
        "message": "Role updated",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": new_role,
    }


def toggle_user(user_id: int, actor: LabUser, db: Session) -> dict:
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


def get_audit_logs(
    actor: LabUser,
    db: Session,
    action: str | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    query = db.query(AuditLog)
    if actor.role == "admin":
        lab_user_ids = [
            row[0] for row in db.query(LabUser.id).filter(LabUser.lab_id == actor.lab_id).all()
        ]
        query = query.filter(AuditLog.user_id.in_(lab_user_ids))
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id and get_role_level(actor.role) >= 80:
        query = query.filter(AuditLog.user_id == user_id)
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "user_id": log.user_id,
                "user_role": log.user_role,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
