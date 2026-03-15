from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
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


@router.post("/register")
def register_lab(data: LabRegisterRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit_auth(request)

    # Password strength validation
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if data.password.isdigit() or data.password.isalpha():
        raise HTTPException(status_code=400, detail="Password must contain both letters and numbers")

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

    # Audit log
    log_action(
        db,
        action="register",
        resource_type="lab",
        user_id=None,
        details=f"New lab registered: {data.lab_name} by {data.email}",
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
