from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..domain.exceptions import ForbiddenError, NotFoundError, ConflictError, ValidationError
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.auth import hash_password
from ..security.session import bump_perm_version


@dataclass
class LabDict:
    id: int
    name: str
    license_number: str | None
    lab_type: str | None
    director_name: str | None
    website: str | None
    city: str | None
    address: str | None
    phone: str | None
    is_active: bool
    created_at: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "license_number": self.license_number,
            "lab_type": self.lab_type,
            "director_name": self.director_name,
            "website": self.website,
            "city": self.city,
            "address": self.address,
            "phone": self.phone,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class EmployeeDict:
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


ALLOWED_LAB_TYPES = ("private", "government", "hospital", "clinic")
ALLOWED_ROLES = ("admin", "staff", "technician")


def lab_to_dict(lab: Lab) -> dict:
    return LabDict(
        id=lab.id,
        name=lab.name,
        license_number=lab.license_number,
        lab_type=lab.lab_type,
        director_name=lab.director_name,
        website=lab.website,
        city=lab.city,
        address=lab.address,
        phone=lab.phone,
        is_active=lab.is_active,
        created_at=lab.created_at.isoformat() if lab.created_at else None,
    ).to_dict()


def employee_to_dict(u: LabUser) -> dict:
    return EmployeeDict(
        id=u.id,
        name=u.name,
        email=u.email,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at.isoformat() if u.created_at else None,
    ).to_dict()


def get_lab(db: Session, lab_id: int) -> dict:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise NotFoundError("Lab not found")
    return lab_to_dict(lab)


def update_lab(
    db: Session, lab_id: int, updates: dict, current_user: LabUser
) -> dict:
    if current_user.role != "admin":
        raise ForbiddenError("Only admin can update lab info")

    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise NotFoundError("Lab not found")

    allowed_fields = {
        "name", "city", "address", "phone", "license_number",
        "lab_type", "director_name", "website",
    }
    for field, value in updates.items():
        if field in allowed_fields and value is not None:
            if isinstance(value, str):
                value = value.strip()[:300]
            setattr(lab, field, value)

    db.commit()
    db.refresh(lab)
    return lab_to_dict(lab)


def list_employees(db: Session, lab_id: int, current_user: LabUser) -> list[dict]:
    if current_user.role not in ("admin", "master_admin"):
        raise ForbiddenError("Admin access required")
    employees = (
        db.query(LabUser)
        .filter(LabUser.lab_id == lab_id)
        .order_by(LabUser.created_at.desc())
        .all()
    )
    return [employee_to_dict(u) for u in employees]


def create_employee(
    db: Session,
    lab_id: int,
    name: str,
    email: str,
    password: str,
    role: str,
    current_user: LabUser,
) -> dict:
    if current_user.role not in ("admin", "master_admin"):
        raise ForbiddenError("Admin access required")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    existing = db.query(LabUser).filter(LabUser.email == email).first()
    if existing:
        raise ConflictError("Email already registered")

    employee = LabUser(
        lab_id=lab_id,
        name=name.strip()[:200],
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return {"message": "Employee added successfully", "id": employee.id}


def update_employee(
    db: Session,
    lab_id: int,
    employee_id: int,
    is_active: bool | None,
    role: str | None,
    current_user: LabUser,
) -> dict:
    if current_user.role not in ("admin", "master_admin"):
        raise ForbiddenError("Admin access required")
    employee = (
        db.query(LabUser)
        .filter(LabUser.id == employee_id, LabUser.lab_id == lab_id)
        .first()
    )
    if not employee:
        raise NotFoundError("Employee not found")
    if employee.id == current_user.id:
        raise ValidationError("Cannot modify your own account")

    role_or_status_changed = False
    if is_active is not None:
        employee.is_active = is_active
        role_or_status_changed = True
    if role is not None:
        employee.role = role
        role_or_status_changed = True
    if role_or_status_changed:
        bump_perm_version(
            employee,
            db,
            actor_id=current_user.id,
            actor_role=current_user.role,
            reason="employee_update",
        )
    db.commit()
    return {"message": "Employee updated successfully"}