from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.auth import hash_password, create_token
from ..security.rate_limit import rate_limit_auth
from ..services.audit_service import log_action

router = APIRouter(tags=["auth"])


class LabRegisterRequest(BaseModel):
    lab_name: str
    city: str = ""
    address: str = ""
    phone: str = ""
    admin_name: str
    email: str
    password: str

    @field_validator("lab_name")
    @classmethod
    def validate_lab_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Lab name must be between 2 and 200 characters")
        return v

    @field_validator("admin_name")
    @classmethod
    def validate_admin_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Admin name must be between 2 and 200 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        import re
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        if len(v) > 100:
            raise ValueError("Email too long")
        return v


@router.post("/register")
def register_lab(data: LabRegisterRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit_auth(request)

    # Password strength validation
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if data.password.isdigit() or data.password.isalpha():
        raise HTTPException(status_code=400, detail="Password must contain both letters and numbers")
    if len(data.password) > 128:
        raise HTTPException(status_code=400, detail="Password too long")

    existing = db.query(LabUser).filter(LabUser.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    lab = Lab(
        name=data.lab_name,
        city=data.city,
        address=data.address,
        phone=data.phone,
    )
    db.add(lab)
    db.flush()

    user = LabUser(
        lab_id=lab.id,
        name=data.admin_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="admin",
    )
    db.add(user)

    # Audit log (avoid logging PII like email in details)
    log_action(
        db,
        action="register",
        resource_type="lab",
        resource_id=lab.id,
        user_id=user.id,
        user_role=user.role,
        details=f"New lab registered: {data.lab_name} (lab_id={lab.id})",
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(lab)
    db.refresh(user)

    token = create_token({"user_id": user.id, "lab_id": lab.id, "role": user.role})

    return {
        "message": "Lab registered successfully",
        "lab_id": lab.id,
        "user_id": user.id,
        "token": token,
    }
