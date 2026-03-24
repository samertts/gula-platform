import re
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.user import User
from ..security.auth import hash_password, create_token
from ..security.rate_limit import rate_limit_auth, get_client_ip
from ..services.audit_service import log_action
from ..config import IS_PRODUCTION, JWT_EXPIRE_MINUTES, NID_HMAC_KEY

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
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        if len(v) > 100:
            raise ValueError("Email too long")
        return v


@router.post("/register")
def register_lab(data: LabRegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=409, detail="Registration failed. Please use a different email.")

    # Labs start INACTIVE — they must be approved by a platform admin before use.
    # This is required for a medical platform: we cannot allow unverified labs to
    # access patient data. Admin approves via PUT /admin/labs/{id}/activate.
    lab = Lab(
        name=data.lab_name,
        city=data.city,
        address=data.address,
        phone=data.phone,
        is_active=False,
    )
    db.add(lab)
    db.flush()

    # Lab admin user also starts inactive until the lab is approved.
    user = LabUser(
        lab_id=lab.id,
        name=data.admin_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="admin",
        is_active=False,
    )
    db.add(user)

    log_action(
        db,
        action="register",
        resource_type="lab",
        resource_id=lab.id,
        user_id=user.id,
        user_role=user.role,
        details=f"New lab registration pending approval: {data.lab_name} (lab_id={lab.id})",
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(lab)
    db.refresh(user)

    # No token issued — login will fail until admin activates the lab.
    return {
        "message": "Registration submitted successfully. Your account will be activated after review.",
        "message_ar": "تم تقديم طلب التسجيل بنجاح. سيتم تفعيل حسابك بعد المراجعة.",
        "lab_id": lab.id,
        "status": "pending_approval",
    }


# ─── Citizen Self-Registration ────────────────────────────────────────────────

class CitizenRegisterRequest(BaseModel):
    full_name: str
    phone: str
    email: str = ""
    password: str
    gender: str = ""
    birth_date: str = ""   # ISO date string YYYY-MM-DD
    national_id: str = ""  # raw NID, hashed server-side

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Full name must be between 2 and 200 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()
        if not re.match(r"^\+?[0-9]{7,15}$", v):
            raise ValueError("Invalid phone number")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if v and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        if len(v) > 100:
            raise ValueError("Email too long")
        return v

    @field_validator("national_id")
    @classmethod
    def validate_nid(cls, v):
        v = v.strip()
        if v and not re.match(r"^[0-9]{10,14}$", v):
            raise ValueError("National ID must be 10–14 digits")
        return v


@router.post("/register/citizen")
def register_citizen(data: CitizenRegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit_auth(request)

    # Password validation
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(data.password) > 128:
        raise HTTPException(status_code=400, detail="Password too long")

    # Check for duplicate phone
    existing_phone = db.query(User).filter(User.phone == data.phone).first()
    if existing_phone:
        raise HTTPException(status_code=409, detail="Registration failed. Please check your details.")

    # Check for duplicate email if provided
    if data.email:
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Registration failed. Please check your details.")

    # Hash NID using HMAC-SHA256 for privacy — use the same key as the rest of the app
    nid_hash = None
    if data.national_id:
        import hmac
        import hashlib
        nid_hash = hmac.new(NID_HMAC_KEY.encode(), data.national_id.encode(), hashlib.sha256).hexdigest()

        # Check for duplicate NID
        existing_nid = db.query(User).filter(User.national_id_hash == nid_hash).first()
        if existing_nid:
            raise HTTPException(status_code=409, detail="Registration failed. Please check your details.")

    citizen = User(
        email=data.email or None,
        phone=data.phone,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role="citizen",
        national_id_hash=nid_hash,
        is_active=True,
        is_verified=False,
    )
    db.add(citizen)
    db.flush()

    log_action(
        db,
        action="register",
        resource_type="citizen",
        resource_id=citizen.id,
        user_id=citizen.id,
        user_role="citizen",
        details=f"Citizen self-registered (user_id={citizen.id})",
        ip_address=get_client_ip(request),
    )
    db.commit()
    db.refresh(citizen)

    return {
        "message": "Account created successfully",
        "user_id": citizen.id,
    }
