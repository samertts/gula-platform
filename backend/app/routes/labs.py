from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services import lab_service

router = APIRouter(prefix="/labs", tags=["labs"])


class LabUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    license_number: str | None = None
    lab_type: str | None = None
    director_name: str | None = None
    website: str | None = None

    @field_validator("lab_type")
    @classmethod
    def validate_lab_type(cls, v):
        if v is not None and v not in lab_service.ALLOWED_LAB_TYPES:
            raise ValueError("lab_type must be private, government, hospital, or clinic")
        return v


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
        if v not in lab_service.ALLOWED_ROLES:
            raise ValueError("Role must be admin, staff, or technician")
        return v


class UpdateEmployeeRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in lab_service.ALLOWED_ROLES:
            raise ValueError("Invalid role")
        return v


@router.get("/me")
def get_my_lab(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return lab_service.get_lab(db, current_user.lab_id)


@router.get("/me/employees")
def list_my_employees(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employees = lab_service.list_employees(db, current_user.lab_id, current_user)
    return {"employees": employees}


@router.post("/me/employees", status_code=201)
def create_employee(
    data: CreateEmployeeRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = lab_service.create_employee(
        db, current_user.lab_id, data.name, data.email, data.password, data.role, current_user
    )
    return {"message": "Employee added successfully", "id": result["id"]}


@router.put("/me/employees/{employee_id}")
def update_employee(
    employee_id: int,
    data: UpdateEmployeeRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return lab_service.update_employee(
        db, current_user.lab_id, employee_id, data.is_active, data.role, current_user
    )


@router.put("/me")
def update_my_lab(
    data: LabUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = lab_service.update_lab(
        db, current_user.lab_id, data.model_dump(exclude_unset=True), current_user
    )
    return {"message": "Lab updated", "lab": result}
