from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.auth import hash_password
from ..security.dependencies import get_current_user
from ..security.session import bump_perm_version

router = APIRouter(prefix="/labs", tags=["labs"])


class LabUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    license_number: str | None = None
    lab_type: str | None = None  # private | government | hospital | clinic
    director_name: str | None = None
    website: str | None = None

    @field_validator("lab_type")
    @classmethod
    def validate_lab_type(cls, v):
        if v is not None and v not in ("private", "government", "hospital", "clinic"):
            raise ValueError("lab_type must be private, government, hospital, or clinic")
        return v


@router.get("/me")
def get_my_lab(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

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
    }


class CreateEmployeeRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "staff"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.strip().lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("admin", "staff", "technician"):
            raise ValueError("Role must be admin, staff, or technician")
        return v


class UpdateEmployeeRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in ("admin", "staff", "technician"):
            raise ValueError("Invalid role")
        return v


@router.get("/me/employees")
def list_my_employees(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all employees in the current lab. Admin only."""
    if current_user.role not in ("admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    employees = (
        db.query(LabUser)
        .filter(LabUser.lab_id == current_user.lab_id)
        .order_by(LabUser.created_at.desc())
        .all()
    )
    return {
        "employees": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in employees
        ]
    }


@router.post("/me/employees", status_code=201)
def create_employee(
    data: CreateEmployeeRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new employee to the current lab. Admin only."""
    if current_user.role not in ("admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="كلمة المرور يجب أن تكون 8 أحرف على الأقل")
    if db.query(LabUser).filter(LabUser.email == data.email).first():
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجل مسبقاً")

    employee = LabUser(
        lab_id=current_user.lab_id,
        name=data.name.strip()[:200],
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return {"message": "تم إضافة الموظف بنجاح", "id": employee.id}


@router.put("/me/employees/{employee_id}")
def update_employee(
    employee_id: int,
    data: UpdateEmployeeRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update employee status or role. Admin only."""
    if current_user.role not in ("admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    employee = (
        db.query(LabUser)
        .filter(LabUser.id == employee_id, LabUser.lab_id == current_user.lab_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكن تعديل حسابك الخاص")

    role_or_status_changed = False
    if data.is_active is not None:
        employee.is_active = data.is_active
        role_or_status_changed = True
    if data.role is not None:
        employee.role = data.role
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
    return {"message": "تم تحديث بيانات الموظف"}


@router.put("/me")
def update_my_lab(
    data: LabUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update lab info")

    lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    # Explicit field assignment (whitelist) instead of dynamic setattr
    allowed_fields = {
        "name",
        "city",
        "address",
        "phone",
        "license_number",
        "lab_type",
        "director_name",
        "website",
    }
    for field, value in data.model_dump(exclude_unset=True).items():
        if field in allowed_fields:
            if value is not None and isinstance(value, str):
                value = value.strip()[:300]  # Truncate to prevent oversized input
            setattr(lab, field, value)

    db.commit()
    db.refresh(lab)

    return {
        "message": "Lab updated",
        "lab": {
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
        },
    }
