from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from auth import hash_password, verify_password, create_access_token, get_db, get_current_user, require_roles
from models.user import User
from models.patient import Patient

router = APIRouter(prefix="/auth", tags=["Auth"])


# -------------------------------------------------------
# Schemas
# -------------------------------------------------------

class RegisterRequest(BaseModel):
    name:        str
    email:       str
    password:    str
    phone:       Optional[str] = None
    national_id: Optional[str] = None
    role:        Optional[str] = "citizen"


class LoginRequest(BaseModel):
    email:    str
    password: str


class CreateUserRequest(BaseModel):
    name:        str
    email:       str
    password:    str
    role:        str
    phone:       Optional[str] = None
    national_id: Optional[str] = None


# -------------------------------------------------------
# Routes
# -------------------------------------------------------

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    allowed_roles = {"patient", "citizen"}
    if body.role not in allowed_roles:
        raise HTTPException(400, "self_registration_only_patient_or_citizen")

    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(409, "email_already_registered")

    user = User(
        name          = body.name,
        email         = body.email.lower(),
        phone         = body.phone,
        national_id   = body.national_id,
        password_hash = hash_password(body.password),
        role          = body.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if body.role == "patient":
        patient = Patient(
            user_id     = user.id,
            full_name   = body.name,
            phone       = body.phone,
            national_id = body.national_id
        )
        db.add(patient)
        db.commit()

    token = create_access_token({"id": user.id, "email": user.email, "role": user.role, "name": user.name})

    return {
        "ok":           True,
        "user":         {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        "access_token": token,
        "token_type":   "bearer"
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "invalid_credentials")

    if not user.is_active:
        raise HTTPException(403, "account_disabled")

    token = create_access_token({"id": user.id, "email": user.email, "role": user.role, "name": user.name})

    return {
        "ok":           True,
        "user":         {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        "access_token": token,
        "token_type":   "bearer"
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "ok":   True,
        "user": {
            "id":          user.id,
            "name":        user.name,
            "email":       user.email,
            "role":        user.role,
            "phone":       user.phone,
            "national_id": user.national_id
        }
    }


@router.post("/users")
def create_user(body: CreateUserRequest, db: Session = Depends(get_db),
                _=Depends(require_roles("admin"))):
    valid_roles = {"admin", "lab_staff", "doctor", "patient", "citizen"}
    if body.role not in valid_roles:
        raise HTTPException(400, "invalid_role")

    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(409, "email_already_exists")

    user = User(
        name          = body.name,
        email         = body.email.lower(),
        phone         = body.phone,
        national_id   = body.national_id,
        password_hash = hash_password(body.password),
        role          = body.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"ok": True, "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}


@router.get("/users")
def list_users(role: Optional[str] = None, db: Session = Depends(get_db),
               _=Depends(require_roles("admin"))):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    users = q.order_by(User.id.desc()).all()
    return {
        "ok":    True,
        "users": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": u.is_active}
                  for u in users]
    }
