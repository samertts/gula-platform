from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.auth import hash_password, create_token

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
def register_lab(data: LabRegisterRequest, db: Session = Depends(get_db)):
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
