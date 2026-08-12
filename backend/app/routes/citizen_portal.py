"""Citizen Portal API
==================
Authenticated endpoints for patients (citizens) to access their own clinical
records across ALL labs where they have been registered, linked via phone number.

Authentication: same httpOnly cookie JWT as staff login, but role='citizen'.
The `/citizen/login` endpoint is a thin wrapper around the main login flow
that ONLY accepts citizen accounts (rejects staff attempts).

Endpoints
---------
POST /citizen/login          — Citizen sign-in; sets httpOnly cookie
POST /citizen/logout         — Revokes tokens; clears cookies
GET  /citizen/profile        — Citizen profile + labs visited count
GET  /citizen/results        — All test results across all labs (paginated)
GET  /citizen/orders         — All orders across all labs
GET  /citizen/health-record  — Structured health record summary (EHR-lite)

Security
--------
- Requires role='citizen' in JWT (LabUser.role == 'citizen' rejected)
- Results are always scoped to citizen's own phone/national-id hash
- No cross-citizen data access is possible
"""

import hashlib
import hmac as _hmac
import logging
import time as _time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app._compat import UTC

from ..config import JWT_EXPIRE_MINUTES, NID_HMAC_KEY, REFRESH_TOKEN_EXPIRE_DAYS, USE_SECURE_COOKIES
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_order import LabOrder
from ..models.patient import Patient
from ..models.user import User
from ..security.auth import (
    blacklist_token,
    create_refresh_token,
    create_token,
    decode_refresh_token,
    decode_token,
    verify_password,
)
from ..security.rate_limit import rate_limit_auth
from ..services.audit_service import log_action

logger = logging.getLogger("gula.citizen")

router = APIRouter(prefix="/citizen", tags=["citizen-portal"])


# ─────────────────────────── Schemas ─────────────────────────────────────────


class CitizenLoginRequest(BaseModel):
    identifier: str  # email or phone — frontend sends both
    email: str | None = None
    password: str

    @field_validator("identifier", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip().lower() if v else v


# ─────────────────────────── Helpers ──────────────────────────────────────────


def _current_citizen(request: Request, db: Session) -> User:
    """Extract and validate citizen JWT from cookie.  Raises 401 if invalid."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    from ..security.auth import decode_token, is_token_blacklisted

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalid or expired")
    if is_token_blacklisted(payload.get("jti", "")):
        raise HTTPException(status_code=401, detail="Token revoked")
    if payload.get("role") != "citizen":
        raise HTTPException(status_code=403, detail="Citizen access only")
    user = (
        db.query(User)
        .filter(
            User.id == payload["user_id"],
            User.role == "citizen",
            User.is_active,
            User.is_verified,
        )
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Account not found or deactivated")
    return user


def _citizen_patients(citizen: User, db: Session) -> list[Patient]:
    """Return all Patient rows linked to this citizen (by phone or NID hash)."""
    filters = []
    if citizen.phone:
        filters.append(Patient.phone == citizen.phone)
    if citizen.national_id_hash:
        filters.append(Patient.national_id_hash == citizen.national_id_hash)
    if not filters:
        return []
    from sqlalchemy import or_

    return db.query(Patient).filter(or_(*filters)).all()


def _flag_label(flag: str | None) -> str:
    return {"H": "مرتفع", "L": "منخفض", "critical": "حرج"}.get(flag or "", "طبيعي")


def _status_label(status: str | None) -> str:
    return {
        "pending": "معلق",
        "completed": "منجز",
        "validated": "مُعتمد",
        "cancelled": "ملغي",
    }.get(status or "", status or "")


# ─────────────────────────── Auth Endpoints ───────────────────────────────────


@router.post("/login")
def citizen_login(
    data: CitizenLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Citizen-only login.  Rejects lab staff accounts.
    Sets httpOnly access_token + refresh_token cookies.
    """
    rate_limit_auth(request)
    identifier = data.identifier or data.email or ""
    identifier = identifier.strip().lower()

    # Look up by email first, then phone
    citizen: User | None = None
    if "@" in identifier:
        citizen = (
            db.query(User)
            .filter(
                User.email == identifier,
                User.role == "citizen",
                User.is_active,
                User.is_verified,
            )
            .first()
        )
    else:
        # Phone lookup — normalize to digits-only, then exact match.
        # Using LIKE with user input allows SQL wildcard injection (%/_).
        # Exact match after normalization is secure and equally flexible.
        phone_digits = "".join(c for c in identifier if c.isdigit())
        # Try both the full digits string and the version without leading country prefix
        # (e.g., stored as "07001234567" and lookup as "7001234567" after stripping 0)
        phone_short = phone_digits.lstrip("0") if phone_digits else ""
        citizen = (
            db.query(User)
            .filter(
                User.phone.in_([phone_digits, phone_short])
                if phone_short
                else User.phone == phone_digits,
                User.role == "citizen",
                User.is_active,
                User.is_verified,
            )
            .first()
        )

    from ..security.auth import _DUMMY_HASH

    password_ok = verify_password(
        data.password,
        citizen.password_hash if citizen else _DUMMY_HASH,
    )

    if not citizen or not password_ok:
        log_action(
            db,
            action="citizen_login_failed",
            resource_type="auth",
            user_id=citizen.id if citizen else None,
            user_role="citizen",
            details=f"Failed citizen login for identifier_hmac: {_hmac.new(NID_HMAC_KEY.encode(), identifier.encode(), hashlib.sha256).hexdigest()[:16]}",
            ip_address=request.client.host if request.client else "unknown",
        )
        db.commit()
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

    # Build token payload for citizen (no perm_version needed)
    payload = {
        "user_id": citizen.id,
        "lab_id": None,
        "role": "citizen",
        "perm_ver": 1,
    }
    access_token = create_token(payload)
    refresh_token = create_refresh_token(payload)

    # Update last_login
    citizen.last_login = datetime.now(UTC)
    log_action(
        db,
        action="citizen_login",
        resource_type="auth",
        user_id=citizen.id,
        user_role="citizen",
        details="Citizen logged in",
        ip_address=request.client.host if request.client else "unknown",
    )
    db.commit()

    cookie_kwargs = {"httponly": True, "samesite": "strict", "secure": USE_SECURE_COOKIES}
    response.set_cookie(
        "access_token", access_token, max_age=JWT_EXPIRE_MINUTES * 60, path="/", **cookie_kwargs,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
        **cookie_kwargs,
    )

    return {
        "id": citizen.id,
        "name": citizen.full_name,
        "email": citizen.email,
        "phone": citizen.phone,
        "role": "citizen",
    }


@router.post("/logout")
def citizen_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke citizen tokens and clear cookies."""
    access = request.cookies.get("access_token")
    refresh = request.cookies.get("refresh_token")
    for tok, decoder in [(access, decode_token), (refresh, decode_refresh_token)]:
        if tok:
            payload = decoder(tok)
            if payload and payload.get("jti"):
                remaining = max(1, int(payload.get("exp", 0) - _time.time()))
                blacklist_token(payload["jti"], remaining)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "تم تسجيل الخروج بنجاح"}


# ─────────────────────────── Data Endpoints ───────────────────────────────────


@router.get("/profile")
def citizen_profile(request: Request, db: Session = Depends(get_db)):
    """Citizen profile + count of labs visited."""
    citizen = _current_citizen(request, db)
    patients = _citizen_patients(citizen, db)
    lab_ids = {p.lab_id for p in patients if p.lab_id}
    return {
        "id": citizen.id,
        "name": citizen.full_name,
        "email": citizen.email,
        "phone": citizen.phone,
        "is_verified": citizen.is_verified,
        "labs_visited": len(lab_ids),
        "patient_records": len(patients),
        "member_since": citizen.created_at.isoformat() if citizen.created_at else None,
    }


@router.get("/results")
def citizen_results(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """All test results for this citizen across all labs.
    Results are linked via the patient's phone number or national ID.
    Returns newest first.
    """
    citizen = _current_citizen(request, db)
    patients = _citizen_patients(citizen, db)
    if not patients:
        return {"results": [], "total": 0, "offset": offset}

    patient_ids = [p.id for p in patients]
    lab_map = {}  # lab_id → lab_name

    # Load orders for these patients
    orders = (
        db.query(LabOrder)
        .filter(LabOrder.patient_id.in_(patient_ids))
        .options(joinedload(LabOrder.results))
        .order_by(desc(LabOrder.created_at))
        .all()
    )

    # Collect lab names
    lab_ids = {o.lab_id for o in orders}
    if lab_ids:
        labs = db.query(Lab).filter(Lab.id.in_(lab_ids)).all()
        lab_map = {l.id: l.name for l in labs}

    # Flatten to individual results
    all_results = []
    for order in orders:
        lab_name = lab_map.get(order.lab_id, "مختبر")
        for r in order.results:
            all_results.append(
                {
                    "id": r.id,
                    "test_name": r.test_name,
                    "value": r.value,
                    "value_text": r.value_text,
                    "unit": r.unit,
                    "reference_low": r.normal_range_low,
                    "reference_high": r.normal_range_high,
                    "flag": _flag_label(r.flag),
                    "flag_code": r.flag,
                    "status": order.status,
                    "order_id": order.id,
                    "lab_name": lab_name,
                    "collected_at": order.created_at.isoformat() if order.created_at else None,
                    "result_token": r.token,
                    "is_validated": order.status == "validated",
                },
            )

    total = len(all_results)
    page = all_results[offset : offset + limit]
    return {"results": page, "total": total, "offset": offset, "limit": limit}


@router.get("/orders")
def citizen_orders(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """All lab orders for this citizen across all labs, newest first."""
    citizen = _current_citizen(request, db)
    patients = _citizen_patients(citizen, db)
    if not patients:
        return {"orders": [], "total": 0}

    patient_ids = [p.id for p in patients]

    orders = (
        db.query(LabOrder)
        .filter(LabOrder.patient_id.in_(patient_ids))
        .options(joinedload(LabOrder.results))
        .order_by(desc(LabOrder.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = db.query(LabOrder).filter(LabOrder.patient_id.in_(patient_ids)).count()

    lab_ids = {o.lab_id for o in orders}
    lab_map = {}
    if lab_ids:
        labs = db.query(Lab).filter(Lab.id.in_(lab_ids)).all()
        lab_map = {l.id: l.name for l in labs}

    result = []
    for o in orders:
        tests = [{"name": r.test_name, "flag": r.flag} for r in o.results]
        result.append(
            {
                "id": o.id,
                "order_number": f"ORD-{o.id:06d}",
                "status": o.status,
                "status_label": _status_label(o.status),
                "lab_name": lab_map.get(o.lab_id, "مختبر"),
                "doctor_name": o.doctor_name,
                "tests": tests,
                "test_names": " • ".join(r.test_name for r in o.results),
                "result_count": len(o.results),
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "validated_at": o.validated_at.isoformat() if o.validated_at else None,
            },
        )

    return {"orders": result, "total": total, "offset": offset, "limit": limit}


@router.get("/health-record")
def citizen_health_record(request: Request, db: Session = Depends(get_db)):
    """Structured health record summary for the citizen.
    Aggregates all results into an EHR-lite view with:
    - latest value per test type
    - abnormal flags summary
    - timeline of visits
    - critical alerts (if any current critical values)
    """
    citizen = _current_citizen(request, db)
    patients = _citizen_patients(citizen, db)
    if not patients:
        return {
            "patient_name": citizen.full_name,
            "visits": 0,
            "latest_results": {},
            "abnormal_flags": [],
            "critical_flags": [],
            "timeline": [],
        }

    patient_ids = [p.id for p in patients]

    orders = (
        db.query(LabOrder)
        .filter(
            LabOrder.patient_id.in_(patient_ids),
            LabOrder.status.in_(["completed", "validated"]),
        )
        .options(joinedload(LabOrder.results))
        .order_by(desc(LabOrder.created_at))
        .limit(200)
        .all()
    )

    latest_per_test: dict = {}  # test_name → latest result
    abnormal: list = []
    critical: list = []
    timeline: list = []

    for order in orders:
        lab_name = f"مختبر #{order.lab_id}"
        timeline.append(
            {
                "date": order.created_at.date().isoformat() if order.created_at else None,
                "lab": lab_name,
                "tests": len(order.results),
                "status": _status_label(order.status),
            },
        )
        for r in order.results:
            key = r.test_name.lower().strip()
            if key not in latest_per_test:
                latest_per_test[key] = {
                    "name": r.test_name,
                    "value": r.value,
                    "value_text": r.value_text,
                    "unit": r.unit,
                    "flag": r.flag,
                    "date": order.created_at.date().isoformat() if order.created_at else None,
                    "reference": f"{r.normal_range_low}–{r.normal_range_high}"
                    if r.normal_range_low is not None
                    else None,
                }
            if r.flag in ("H", "L", "critical"):
                item = {
                    "name": r.test_name,
                    "value": r.value,
                    "unit": r.unit,
                    "flag": r.flag,
                    "date": order.created_at.date().isoformat() if order.created_at else None,
                }
                if r.flag == "critical":
                    critical.append(item)
                else:
                    abnormal.append(item)

    return {
        "patient_name": citizen.full_name,
        "phone": citizen.phone,
        "visits": len(orders),
        "labs_visited": len({o.lab_id for o in orders}),
        "latest_results": latest_per_test,
        "abnormal_flags": abnormal[:20],
        "critical_flags": critical[:20],
        "timeline": timeline[:30],
        "generated_at": datetime.now(UTC).isoformat(),
    }
