import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import NID_HMAC_KEY
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.user import User
from ..security.auth import hash_password
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip, rate_limit_auth
from ..services.audit_service import log_action
from ..services.identity import hash_national_id as mpi_hash_nid
from ..services.identity import normalize_name as mpi_normalize_name
from ..services.mpi.blocking import blocking_key, phone_last10
from ..services.mpi.models import Citizen


def _validate_password(password: str) -> None:
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password too long")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")


def _mint_citizen_from_self_registration(
    db: Session,
    *,
    full_name: str,
    phone: str,
    birth_date: str = "",
    gender: str = "",
    national_id: str = "",
) -> str | None:
    """Create (or link to) a canonical MPI Citizen for a self-registering user.

    Citizens exist as a national identity registry independent of any lab.
    Minting on self-registration makes the platform citizen-first instead of
    lab-first, so a user has a longitudinal record ready before their first
    lab visit. Returns the canonical citizen_ulid or None on failure
    (non-fatal; a reconciler can re-run).
    """
    import secrets
    import time

    try:
        nid_h = mpi_hash_nid(national_id) if national_id else None
        if nid_h:
            existing = (
                db.query(Citizen)
                .filter(Citizen.nid_hash == nid_h, Citizen.status.in_(("active", "review")))
                .first()
            )
            if existing is not None:
                return existing.canonical().citizen_ulid

        by = bm = bd = None
        if birth_date:
            try:
                from datetime import date as _date

                d = _date.fromisoformat(birth_date)
                by, bm, bd = d.year, d.month, d.day
            except ValueError:
                pass

        # ULID inline (avoid circular import with resolver)
        _crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        ms = int(time.time() * 1000) & ((1 << 48) - 1)
        rand = secrets.randbits(80)
        val = (ms << 80) | rand
        out = []
        for _ in range(26):
            out.append(_crockford[val & 0x1F])
            val >>= 5
        ulid = "".join(reversed(out))

        citizen = Citizen(
            citizen_ulid=ulid,
            nid_hash=nid_h,
            nid_verified=False,
            phone_last10=phone_last10(phone),
            birth_year=by,
            birth_month=bm,
            birth_day=bd,
            gender=(gender.upper()[:1] if gender else None),
            name_canonical=mpi_normalize_name(full_name),
            name_blocking_key=blocking_key(full_name),
            status="active",
            version=1,
        )
        db.add(citizen)
        db.flush()
        return ulid
    except Exception:
        return None


router = APIRouter(tags=["auth"])

# Roles that a lab admin is permitted to create for their own lab.
_ALLOWED_STAFF_ROLES = frozenset(
    {
        "technician",  # مختبري — enters and validates results
        "doctor",  # طبيب مشرف — reviews and authorises results
        "receptionist",  # موظف استقبال — registers patients and orders
        "staff",  # generic staff member
    },
)


class LabRegisterRequest(BaseModel):
    # Identity
    lab_name: str
    license_number: str = ""  # رقم الترخيص الصحي
    lab_type: str = "private"  # private | government | hospital | clinic
    director_name: str = ""  # اسم المدير / المسؤول
    # Location
    city: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    # Admin account
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

    @field_validator("lab_type")
    @classmethod
    def validate_lab_type(cls, v):
        allowed = {"private", "government", "hospital", "clinic"}
        if v and v not in allowed:
            raise ValueError(f"lab_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("admin_name", "director_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if v and (len(v) < 2 or len(v) > 200):
            raise ValueError("Name must be between 2 and 200 characters")
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


@router.post("/register", status_code=201)
def register_lab(
    data: LabRegisterRequest, request: Request, response: Response, db: Session = Depends(get_db),
):
    rate_limit_auth(request)

    _validate_password(data.password)

    existing = db.query(LabUser).filter(LabUser.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Registration failed. Please use a different email.",
        )

    # Labs start INACTIVE — they must be approved by a platform admin before use.
    # This is required for a medical platform: we cannot allow unverified labs to
    # access patient data. Admin approves via PUT /admin/labs/{id}/activate.
    lab = Lab(
        name=data.lab_name,
        license_number=data.license_number or None,
        lab_type=data.lab_type or "private",
        director_name=data.director_name or None,
        website=data.website or None,
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
    birth_date: str = ""  # ISO date string YYYY-MM-DD
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


@router.post("/register/citizen", status_code=201)
def register_citizen(
    data: CitizenRegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    rate_limit_auth(request)

    _validate_password(data.password)

    # Check for duplicate phone
    existing_phone = db.query(User).filter(User.phone == data.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=409, detail="Registration failed. Please check your details.",
        )

    # Check for duplicate email if provided
    if data.email:
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=409, detail="Registration failed. Please check your details.",
            )

    # Hash NID using HMAC-SHA256 for privacy — use the same key as the rest of the app
    nid_hash = None
    if data.national_id:
        import hashlib
        import hmac

        nid_hash = hmac.new(
            NID_HMAC_KEY.encode(), data.national_id.encode(), hashlib.sha256,
        ).hexdigest()

        # Check for duplicate NID
        existing_nid = db.query(User).filter(User.national_id_hash == nid_hash).first()
        if existing_nid:
            raise HTTPException(
                status_code=409, detail="Registration failed. Please check your details.",
            )

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
    try:
        db.flush()
    except IntegrityError:
        # DB UNIQUE constraints catch concurrent duplicate registrations (TOCTOU).
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Registration failed. Please check your details.",
        ) from None

    # Citizen-first: canonical national identity exists before any lab visit.
    citizen_ulid = _mint_citizen_from_self_registration(
        db,
        full_name=data.full_name,
        phone=data.phone,
        birth_date=data.birth_date,
        gender=data.gender,
        national_id=data.national_id,
    )

    log_action(
        db,
        action="register",
        resource_type="citizen",
        resource_id=citizen.id,
        user_id=citizen.id,
        user_role="citizen",
        details=f"Citizen self-registered (user_id={citizen.id}, citizen_ulid={citizen_ulid})",
        ip_address=get_client_ip(request),
    )
    db.commit()
    db.refresh(citizen)

    return {
        "message": "Account created successfully",
        "user_id": citizen.id,
        "citizen_ulid": citizen_ulid,
    }


# ─── Lab Staff Registration ───────────────────────────────────────────────────
# Lab admins add technicians, doctors, and receptionists to their own lab.
# No separate approval flow — the admin's lab must already be active.


class StaffRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "technician"  # technician | doctor | receptionist | staff

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Name must be between 2 and 200 characters")
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

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in _ALLOWED_STAFF_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(sorted(_ALLOWED_STAFF_ROLES))}")
        return v


@router.post("/register/staff", status_code=201)
def register_staff(
    data: StaffRegisterRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lab admin adds a new staff member to their lab.

    Only users with role 'admin' may call this endpoint.
    The new account is immediately active — no approval required since the
    lab admin is already verified.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Only lab administrators can register new staff",
                "message_ar": "فقط مدير المختبر يمكنه تسجيل موظفين جدد",
            },
        )

    _validate_password(data.password)

    if db.query(LabUser).filter(LabUser.email == data.email).first():
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Email already registered",
                "message_ar": "البريد الإلكتروني مسجل مسبقاً",
            },
        )

    staff = LabUser(
        lab_id=current_user.lab_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(staff)
    db.flush()

    log_action(
        db,
        action="register",
        resource_type="lab_user",
        resource_id=staff.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Staff registered: {data.name} <{data.email}> role={data.role} lab_id={current_user.lab_id}",
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(staff)

    return {
        "message": "Staff member registered successfully",
        "message_ar": "تم تسجيل الموظف بنجاح",
        "user_id": staff.id,
        "role": staff.role,
        "lab_id": staff.lab_id,
    }


# ─── Doctor Self-Registration ─────────────────────────────────────────────────
# Independent doctors (not yet affiliated with a lab) register publicly.
# Account starts active (can log in) but is_verified=False until approved
# by a ministry/province admin. Verified doctors can be linked to labs later.


class DoctorRegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    license_number: str  # رقم الإجازة الطبية — required
    specialty: str = ""  # التخصص
    workplace: str = ""  # جهة العمل الحالية (مستشفى / عيادة)
    national_id: str = ""  # الرقم الوطني — hashed, optional

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Full name must be 2-200 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()
        if not re.match(r"^\+?[0-9]{7,15}$", v):
            raise ValueError("Invalid phone number")
        return v

    @field_validator("license_number")
    @classmethod
    def validate_license(cls, v):
        v = v.strip()
        if len(v) < 3 or len(v) > 100:
            raise ValueError("License number must be 3-100 characters")
        return v

    @field_validator("national_id")
    @classmethod
    def validate_nid(cls, v):
        v = v.strip()
        if v and not re.match(r"^[0-9]{10,14}$", v):
            raise ValueError("National ID must be 10-14 digits")
        return v


@router.post("/register/doctor", status_code=201)
def register_doctor(
    data: DoctorRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Doctor self-registration (no auth required).

    Creates a User with role='doctor', is_active=True, is_verified=False.
    A ministry or province admin must verify the account before the doctor
    can access sensitive endpoints. The doctor's medical license number is
    stored in plain text (public document) while the national ID is hashed.
    """
    rate_limit_auth(request)

    _validate_password(data.password)

    # Duplicate email check
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Email already registered",
                "message_ar": "البريد الإلكتروني مسجل مسبقاً",
            },
        )

    # Duplicate phone check
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Phone number already registered",
                "message_ar": "رقم الهاتف مسجل مسبقاً",
            },
        )

    # Duplicate license number check
    if (
        db.query(User)
        .filter(
            User.license_number == data.license_number,
            User.role == "doctor",
        )
        .first()
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "A doctor with this license number is already registered",
                "message_ar": "طبيب بهذا الرقم الطبي مسجل مسبقاً",
            },
        )

    # Hash national ID if provided
    nid_hash = None
    if data.national_id:
        import hashlib
        import hmac

        nid_hash = hmac.new(
            NID_HMAC_KEY.encode(), data.national_id.encode(), hashlib.sha256,
        ).hexdigest()
        if db.query(User).filter(User.national_id_hash == nid_hash).first():
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "National ID already registered",
                    "message_ar": "الرقم الوطني مسجل مسبقاً",
                },
            )

    doctor = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role="doctor",
        license_number=data.license_number,
        specialty=data.specialty or None,
        national_id_hash=nid_hash,
        is_active=True,  # can log in immediately
        is_verified=False,  # full access after admin approval
    )
    db.add(doctor)
    db.flush()

    log_action(
        db,
        action="register",
        resource_type="doctor",
        resource_id=doctor.id,
        user_id=doctor.id,
        user_role="doctor",
        details=(
            f"Doctor registered: {data.full_name} | license={data.license_number} "
            f"| specialty={data.specialty} | workplace={data.workplace}"
        ),
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(doctor)

    return {
        "message": "Registration submitted. Your account will be activated after license verification.",
        "message_ar": "تم تقديم طلب التسجيل. سيتم تفعيل حسابك بعد التحقق من الإجازة الطبية.",
        "user_id": doctor.id,
        "status": "pending_verification",
    }
