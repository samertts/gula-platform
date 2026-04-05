"""GULA Blood Network (GBN) — API Routes.

Endpoints:
  POST   /gbn/donors                      register a new donor
  GET    /gbn/donors                      list donors (lab-scoped)
  GET    /gbn/donors/{id}                 donor detail + eligibility
  PATCH  /gbn/donors/{id}/screen          update eligibility after screening

  POST   /gbn/units                       register a new blood unit (post-donation)
  GET    /gbn/units                       inventory list (lab-scoped, filterable)
  PATCH  /gbn/units/{id}/status           update unit status (available/reserved/used/…)
  GET    /gbn/units/expiring              units expiring within N days

  POST   /gbn/requests                    create a blood request
  GET    /gbn/requests                    list requests (lab-scoped)
  GET    /gbn/requests/{id}               request detail
  POST   /gbn/requests/{id}/match         run matching engine
  PATCH  /gbn/requests/{id}/cancel        cancel a request

  POST   /gbn/transfusions                record a transfusion
  GET    /gbn/transfusions/patient/{pid}  transfusion history for a patient
  PATCH  /gbn/transfusions/{id}/reaction  report a transfusion reaction

  POST   /gbn/plasma                      add plasma product to inventory
  GET    /gbn/plasma                      list plasma products (lab-scoped)

  GET    /gbn/inventory/summary           per-(type,component) count
  GET    /gbn/inventory/shortages         shortage alerts
  GET    /gbn/network/search              cross-lab availability search

All write endpoints emit audit log entries.
"""

import secrets
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.blood import (
    Donor, BloodUnit, PlasmaProduct, BloodRequest, Transfusion,
    BLOOD_TYPES, COMPONENT_EXPIRY_DAYS, BLOOD_COMPATIBILITY,
)
from ..models.audit_log import AuditLog
from ..security.dependencies import get_current_user
from ..services.blood_matching import (
    screen_donor, match_request,
    find_available_units, inventory_summary,
    detect_shortages, expiring_soon, assert_compatible,
)

router = APIRouter(prefix="/gbn", tags=["blood-network"])

COMPONENT_TYPES = tuple(COMPONENT_EXPIRY_DAYS.keys())


# ── Helpers ───────────────────────────────────────────────────────────────────

def _audit(db: Session, user, action: str, resource_type: str, resource_id: int, details: str = ""):
    db.add(AuditLog(
        user_id       = user.id,
        user_role     = user.role,
        action        = action,
        resource_type = resource_type,
        resource_id   = resource_id,
        details       = details,
    ))


def _require_roles(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, f"هذه العملية تتطلب دور: {', '.join(roles)}")


def _get_lab_id(user) -> int:
    if not user.lab_id:
        raise HTTPException(403, "المستخدم غير مرتبط بمختبر")
    return user.lab_id


def _gen_barcode() -> str:
    return f"BLD-{secrets.token_hex(5).upper()}"


# ── Schemas ───────────────────────────────────────────────────────────────────

class DonorCreate(BaseModel):
    full_name:        str
    blood_type:       str
    phone:            Optional[str]  = None
    gender:           Optional[str]  = None   # M / F
    birth_date:       Optional[date] = None
    city:             Optional[str]  = None
    national_id_hash: Optional[str]  = None
    user_id:          Optional[int]  = None

    @field_validator("blood_type")
    @classmethod
    def _validate_blood_type(cls, v):
        if v not in BLOOD_TYPES:
            raise ValueError(f"فصيلة الدم غير صحيحة: {v}. الصحيح: {BLOOD_TYPES}")
        return v

    @field_validator("gender")
    @classmethod
    def _validate_gender(cls, v):
        if v is not None and v not in ("M", "F"):
            raise ValueError("الجنس يجب أن يكون M أو F")
        return v


class DonorScreen(BaseModel):
    hb_g_dl:            Optional[float] = None
    weight_kg:          Optional[float] = None
    eligibility_status: Optional[str]   = None   # eligible/deferred_temporary/deferred_permanent
    deferral_reason:    Optional[str]   = None
    deferral_until:     Optional[date]  = None


class UnitCreate(BaseModel):
    donor_id:        Optional[int]  = None
    blood_type:      str
    component:       str
    volume_ml:       Optional[int]  = None
    collection_date: Optional[date] = None

    @field_validator("blood_type")
    @classmethod
    def _validate_bt(cls, v):
        if v not in BLOOD_TYPES:
            raise ValueError(f"فصيلة الدم غير صحيحة: {v}")
        return v

    @field_validator("component")
    @classmethod
    def _validate_comp(cls, v):
        if v not in COMPONENT_TYPES:
            raise ValueError(f"نوع المكوّن غير صحيح: {v}. الصحيح: {COMPONENT_TYPES}")
        return v


class UnitStatusUpdate(BaseModel):
    status:           str
    storage_location: Optional[str]   = None
    storage_temp_c:   Optional[float] = None
    hiv_screened:     Optional[bool]  = None
    hbsag_screened:   Optional[bool]  = None
    hcv_screened:     Optional[bool]  = None
    syphilis_screened:Optional[bool]  = None
    screening_passed: Optional[bool]  = None
    notes:            Optional[str]   = None


class RequestCreate(BaseModel):
    blood_type:          str
    component:           str
    units_required:      int               = 1
    urgency:             str               = "routine"
    patient_id:          Optional[int]     = None
    clinical_indication: Optional[str]     = None
    notes:               Optional[str]     = None

    @field_validator("blood_type")
    @classmethod
    def _validate_bt(cls, v):
        if v not in BLOOD_TYPES and v != "any":
            raise ValueError(f"فصيلة الدم غير صحيحة: {v}")
        return v

    @field_validator("component")
    @classmethod
    def _validate_comp(cls, v):
        valid = COMPONENT_TYPES + ("plasma_product",)
        if v not in valid:
            raise ValueError(f"نوع المكوّن غير صحيح: {v}")
        return v

    @field_validator("urgency")
    @classmethod
    def _validate_urgency(cls, v):
        valid = ("routine", "urgent", "critical", "massive_transfusion")
        if v not in valid:
            raise ValueError(f"درجة الإلحاح غير صحيحة: {v}. الصحيح: {valid}")
        return v

    @field_validator("units_required")
    @classmethod
    def _validate_units(cls, v):
        if v < 1 or v > 50:
            raise ValueError("عدد الوحدات يجب أن يكون بين 1 و 50")
        return v


class TransfusionCreate(BaseModel):
    patient_id:          int
    unit_id:             int
    request_id:          Optional[int]   = None
    crossmatch_result:   str             # compatible / not_done
    volume_transfused_ml:Optional[int]   = None
    duration_minutes:    Optional[int]   = None
    pre_transfusion_hb:  Optional[float] = None
    notes:               Optional[str]   = None

    @field_validator("crossmatch_result")
    @classmethod
    def _validate_xmatch(cls, v):
        valid = ("compatible", "incompatible", "not_done")
        if v not in valid:
            raise ValueError(f"نتيجة الاختبار المتقاطع غير صحيحة: {v}")
        return v


class ReactionReport(BaseModel):
    reaction_type:    str
    reaction_notes:   Optional[str]   = None
    post_transfusion_hb: Optional[float] = None


class PlasmaProductCreate(BaseModel):
    product_type:      str
    batch_number:      str
    quantity_units:    int
    expiry_date:       date
    brand_name:        Optional[str]   = None
    lot_number:        Optional[str]   = None
    unit_volume_ml:    Optional[float] = None
    concentration:     Optional[str]   = None
    manufacturer:      Optional[str]   = None
    country_of_origin: Optional[str]   = None
    storage_condition: Optional[str]   = None
    notes:             Optional[str]   = None


# ═══════════════════════════════════════════════════════════════════
#  DONORS
# ═══════════════════════════════════════════════════════════════════

@router.post("/donors", status_code=201)
def register_donor(
    body: DonorCreate,
    db:   Session    = Depends(get_db),
    user             = Depends(get_current_user),
):
    """Register a new blood donor."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin")
    lab_id = _get_lab_id(user)

    donor = Donor(
        lab_id           = lab_id,
        user_id          = body.user_id,
        full_name        = body.full_name,
        blood_type       = body.blood_type,
        phone            = body.phone,
        gender           = body.gender,
        birth_date       = body.birth_date,
        city             = body.city,
        national_id_hash = body.national_id_hash,
    )
    db.add(donor)
    db.flush()
    _audit(db, user, "create", "gbn_donor", donor.id,
           f"تسجيل متبرع جديد: {donor.full_name} ({donor.blood_type})")
    db.commit()
    db.refresh(donor)
    return _donor_out(donor)


@router.get("/donors")
def list_donors(
    blood_type:  Optional[str] = Query(None),
    city:        Optional[str] = Query(None),
    eligible_only: bool        = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """List donors scoped to current lab."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)

    q = db.query(Donor).filter(Donor.lab_id == lab_id, Donor.is_active == True)  # noqa: E712
    if blood_type:
        q = q.filter(Donor.blood_type == blood_type)
    if city:
        q = q.filter(Donor.city.ilike(f"%{city}%"))
    if eligible_only:
        from datetime import date as ddate
        from ..models.blood import MIN_DONATION_INTERVAL_DAYS
        from sqlalchemy import or_, and_
        import datetime as dt
        cutoff = ddate.today() - dt.timedelta(days=MIN_DONATION_INTERVAL_DAYS)
        q = q.filter(
            Donor.eligibility_status == "eligible",
            or_(
                Donor.last_donation_date == None,  # noqa: E711
                Donor.last_donation_date <= cutoff,
            ),
        )

    total  = q.count()
    donors = q.order_by(Donor.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "donors": [_donor_out(d) for d in donors]}


@router.get("/donors/{donor_id}")
def get_donor(
    donor_id: int,
    db:    Session = Depends(get_db),
    user           = Depends(get_current_user),
):
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    donor = _get_donor(donor_id, user, db)
    result = _donor_out(donor)
    result["eligibility_check"] = {
        "eligible":      donor.is_eligible,
        "days_remaining": donor.days_until_eligible,
    }
    return result


@router.patch("/donors/{donor_id}/screen")
def screen_donor_endpoint(
    donor_id: int,
    body: DonorScreen,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Record a pre-donation screening and update eligibility."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin")
    donor = _get_donor(donor_id, user, db)

    elig = screen_donor(donor, hb_g_dl=body.hb_g_dl)

    if body.hb_g_dl is not None:
        donor.last_hb_g_dl = body.hb_g_dl
    if body.weight_kg is not None:
        donor.last_weight_kg = body.weight_kg
    if body.eligibility_status:
        donor.eligibility_status = body.eligibility_status
    if body.deferral_reason:
        donor.deferral_reason = body.deferral_reason
    if body.deferral_until:
        donor.deferral_until = body.deferral_until

    _audit(db, user, "update", "gbn_donor", donor.id,
           f"فحص أهلية: {elig.reason}")
    db.commit()
    return {"eligible": elig.eligible, "reason": elig.reason,
            "eligible_from": str(elig.eligible_from) if elig.eligible_from else None}


# ═══════════════════════════════════════════════════════════════════
#  BLOOD UNITS
# ═══════════════════════════════════════════════════════════════════

@router.post("/units", status_code=201)
def register_unit(
    body: UnitCreate,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Register a newly collected blood unit."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin")
    lab_id = _get_lab_id(user)

    cdate   = body.collection_date or date.today()
    expiry  = BloodUnit.compute_expiry(body.component, cdate)

    unit = BloodUnit(
        lab_id          = lab_id,
        donor_id        = body.donor_id,
        barcode         = _gen_barcode(),
        blood_type      = body.blood_type,
        component       = body.component,
        volume_ml       = body.volume_ml,
        collection_date = cdate,
        expiry_date     = expiry,
        collected_by    = user.id,
    )
    db.add(unit)
    db.flush()

    # Update donor's last donation date
    if body.donor_id:
        donor = db.query(Donor).filter(Donor.id == body.donor_id).first()
        if donor:
            donor.last_donation_date = cdate
            donor.total_donations    = (donor.total_donations or 0) + 1

    _audit(db, user, "create", "gbn_blood_unit", unit.id,
           f"تسجيل وحدة دم: {unit.blood_type}/{unit.component} باركود={unit.barcode}")
    db.commit()
    db.refresh(unit)
    return _unit_out(unit)


@router.get("/units")
def list_units(
    blood_type: Optional[str] = Query(None),
    component:  Optional[str] = Query(None),
    status:     Optional[str] = Query(None),
    skip: int  = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """List blood units for current lab."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)

    q = db.query(BloodUnit).filter(BloodUnit.lab_id == lab_id)
    if blood_type:
        q = q.filter(BloodUnit.blood_type == blood_type)
    if component:
        q = q.filter(BloodUnit.component == component)
    if status:
        q = q.filter(BloodUnit.status == status)

    total = q.count()
    units = q.order_by(BloodUnit.expiry_date.asc()).offset(skip).limit(limit).all()
    return {"total": total, "units": [_unit_out(u) for u in units]}


@router.get("/units/expiring")
def units_expiring_soon(
    days: int     = Query(3, ge=1, le=14),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Units expiring within N days — prioritize for use."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin")
    lab_id = _get_lab_id(user)
    units  = expiring_soon(db, lab_id=lab_id, days_ahead=days)
    return {"expiring_within_days": days, "count": len(units),
            "units": [_unit_out(u) for u in units]}


@router.patch("/units/{unit_id}/status")
def update_unit_status(
    unit_id: int,
    body: UnitStatusUpdate,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Update unit status (screening results, storage, availability)."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin")
    unit = _get_unit(unit_id, user, db)

    valid_statuses = ("quarantine", "available", "reserved", "used", "expired", "discarded")
    if body.status not in valid_statuses:
        raise HTTPException(422, f"حالة غير صحيحة: {body.status}")

    unit.status = body.status
    if body.storage_location  is not None: unit.storage_location   = body.storage_location
    if body.storage_temp_c    is not None: unit.storage_temp_c     = body.storage_temp_c
    if body.hiv_screened      is not None: unit.hiv_screened       = body.hiv_screened
    if body.hbsag_screened    is not None: unit.hbsag_screened     = body.hbsag_screened
    if body.hcv_screened      is not None: unit.hcv_screened       = body.hcv_screened
    if body.syphilis_screened is not None: unit.syphilis_screened  = body.syphilis_screened
    if body.screening_passed  is not None: unit.screening_passed   = body.screening_passed
    if body.notes             is not None: unit.notes              = body.notes

    _audit(db, user, "update", "gbn_blood_unit", unit.id,
           f"تحديث حالة الوحدة → {body.status}")
    db.commit()
    return _unit_out(unit)


# ═══════════════════════════════════════════════════════════════════
#  BLOOD REQUESTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/requests", status_code=201)
def create_request(
    body: RequestCreate,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Create a new blood request."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)

    req = BloodRequest(
        requesting_lab_id   = lab_id,
        patient_id          = body.patient_id,
        requested_by        = user.id,
        blood_type          = body.blood_type,
        component           = body.component,
        units_required      = body.units_required,
        urgency             = body.urgency,
        clinical_indication = body.clinical_indication,
        notes               = body.notes,
    )
    db.add(req)
    db.flush()
    _audit(db, user, "create", "gbn_blood_request", req.id,
           f"طلب دم: {req.blood_type}/{req.component} x{req.units_required} ({req.urgency})")
    db.commit()
    db.refresh(req)
    return _request_out(req)


@router.get("/requests")
def list_requests(
    status:  Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    skip: int  = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)

    q = db.query(BloodRequest).filter(BloodRequest.requesting_lab_id == lab_id)
    if status:  q = q.filter(BloodRequest.status  == status)
    if urgency: q = q.filter(BloodRequest.urgency == urgency)

    total    = q.count()
    requests = q.order_by(BloodRequest.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "requests": [_request_out(r) for r in requests]}


@router.post("/requests/{request_id}/match")
def match_blood_request(
    request_id: int,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Run the matching engine for a pending request.

    Searches local inventory first, then the national network.
    Reserves matched units and updates request status.
    """
    _require_roles(user, "admin", "lab_admin", "master_admin")
    lab_id = _get_lab_id(user)

    req = db.query(BloodRequest).filter(
        BloodRequest.id == request_id,
        BloodRequest.requesting_lab_id == lab_id,
    ).first()
    if not req:
        raise HTTPException(404, "الطلب غير موجود")
    if req.status not in ("pending", "matching"):
        raise HTTPException(422, f"لا يمكن مطابقة طلب بحالة: {req.status}")

    req.status = "matching"
    db.flush()

    result = match_request(db, req)

    if not result.matched_units:
        req.status = "pending"
        db.commit()
        return {
            "matched": 0,
            "shortage": result.shortage,
            "needs_transfer": False,
            "message": result.message,
            "units": [],
        }

    # Reserve matched units
    for unit in result.matched_units:
        unit.status = "reserved"

    req.status            = "matched"
    req.units_fulfilled   = len(result.matched_units)
    req.fulfilling_lab_id = result.from_lab_id
    req.matched_at        = datetime.now(timezone.utc)

    _audit(db, user, "update", "gbn_blood_request", req.id,
           f"مطابقة: {len(result.matched_units)} وحدة "
           f"{'(نقل بين مختبرات)' if result.needs_transfer else ''}")
    db.commit()

    return {
        "matched":         len(result.matched_units),
        "shortage":        result.shortage,
        "needs_transfer":  result.needs_transfer,
        "message":         result.message,
        "units":           [_unit_out(u) for u in result.matched_units],
    }


@router.patch("/requests/{request_id}/cancel")
def cancel_request(
    request_id: int,
    reason: str = Query(..., min_length=3),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    _require_roles(user, "admin", "lab_admin", "master_admin", "doctor")
    lab_id = _get_lab_id(user)
    req = db.query(BloodRequest).filter(
        BloodRequest.id == request_id,
        BloodRequest.requesting_lab_id == lab_id,
    ).first()
    if not req:
        raise HTTPException(404, "الطلب غير موجود")
    if req.status == "fulfilled":
        raise HTTPException(422, "لا يمكن إلغاء طلب مكتمل")

    # Release any reserved units back to available
    for txn in req.transfusions:
        if txn.unit and txn.unit.status == "reserved":
            txn.unit.status = "available"

    req.status            = "cancelled"
    req.cancelled_reason  = reason
    _audit(db, user, "update", "gbn_blood_request", req.id, f"إلغاء الطلب: {reason}")
    db.commit()
    return {"status": "cancelled"}


# ═══════════════════════════════════════════════════════════════════
#  TRANSFUSIONS
# ═══════════════════════════════════════════════════════════════════

@router.post("/transfusions", status_code=201)
def record_transfusion(
    body: TransfusionCreate,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Record a transfusion event.

    SAFETY: incompatible crossmatch is blocked unless forced by admin.
    """
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)

    unit = db.query(BloodUnit).filter(
        BloodUnit.id == body.unit_id,
        BloodUnit.lab_id == lab_id,
    ).first()
    if not unit:
        raise HTTPException(404, "وحدة الدم غير موجودة")
    if unit.status not in ("available", "reserved"):
        raise HTTPException(422, f"الوحدة ليست متاحة (الحالة: {unit.status})")
    if unit.is_expired:
        raise HTTPException(422, "وحدة الدم منتهية الصلاحية — غير مسموح بنقلها")
    if body.crossmatch_result == "incompatible":
        raise HTTPException(422,
            "⛔ الاختبار المتقاطع غير متوافق — نقل الدم محظور. "
            "راجع الطبيب المسؤول قبل المتابعة.")

    txn = Transfusion(
        patient_id           = body.patient_id,
        unit_id              = body.unit_id,
        request_id           = body.request_id,
        administered_by      = user.id,
        crossmatch_result    = body.crossmatch_result,
        transfusion_time     = datetime.now(timezone.utc),
        volume_transfused_ml = body.volume_transfused_ml,
        duration_minutes     = body.duration_minutes,
        pre_transfusion_hb   = body.pre_transfusion_hb,
        notes                = body.notes,
    )
    db.add(txn)

    unit.status = "used"

    # Update request fulfillment
    if body.request_id:
        req = db.query(BloodRequest).filter(BloodRequest.id == body.request_id).first()
        if req:
            req.units_fulfilled = (req.units_fulfilled or 0) + 1
            if req.units_fulfilled >= req.units_required:
                req.status       = "fulfilled"
                req.fulfilled_at = datetime.now(timezone.utc)

    db.flush()
    _audit(db, user, "create", "gbn_transfusion", txn.id,
           f"نقل دم: وحدة #{body.unit_id} → مريض #{body.patient_id} "
           f"(تقاطع: {body.crossmatch_result})")
    db.commit()
    db.refresh(txn)
    return _transfusion_out(txn)


@router.get("/transfusions/patient/{patient_id}")
def patient_transfusion_history(
    patient_id: int,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    txns = db.query(Transfusion).filter(
        Transfusion.patient_id == patient_id,
    ).order_by(Transfusion.transfusion_time.desc()).all()
    return {"patient_id": patient_id, "transfusions": [_transfusion_out(t) for t in txns]}


@router.patch("/transfusions/{txn_id}/reaction")
def report_reaction(
    txn_id: int,
    body: ReactionReport,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Report a post-transfusion adverse reaction."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    txn = db.query(Transfusion).filter(Transfusion.id == txn_id).first()
    if not txn:
        raise HTTPException(404, "سجل النقل غير موجود")

    txn.reaction_flag    = True
    txn.reaction_type    = body.reaction_type
    txn.reaction_notes   = body.reaction_notes
    txn.reaction_time    = datetime.now(timezone.utc)
    if body.post_transfusion_hb is not None:
        txn.post_transfusion_hb = body.post_transfusion_hb

    _audit(db, user, "update", "gbn_transfusion", txn.id,
           f"تفاعل نقل دم: {body.reaction_type}")
    db.commit()
    return {"recorded": True, "reaction_type": body.reaction_type}


# ═══════════════════════════════════════════════════════════════════
#  PLASMA PRODUCTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/plasma", status_code=201)
def add_plasma_product(
    body: PlasmaProductCreate,
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    _require_roles(user, "admin", "lab_admin", "master_admin")
    lab_id = _get_lab_id(user)

    product = PlasmaProduct(
        lab_id            = lab_id,
        product_type      = body.product_type,
        brand_name        = body.brand_name,
        batch_number      = body.batch_number,
        lot_number        = body.lot_number,
        quantity_units    = body.quantity_units,
        unit_volume_ml    = body.unit_volume_ml,
        concentration     = body.concentration,
        manufacturer      = body.manufacturer,
        country_of_origin = body.country_of_origin,
        storage_condition = body.storage_condition,
        expiry_date       = body.expiry_date,
        received_date     = date.today(),
        received_by       = user.id,
        notes             = body.notes,
    )
    db.add(product)
    db.flush()
    _audit(db, user, "create", "gbn_plasma_product", product.id,
           f"إضافة منتج بلازما: {body.product_type} دفعة {body.batch_number}")
    db.commit()
    db.refresh(product)
    return _plasma_out(product)


@router.get("/plasma")
def list_plasma_products(
    product_type: Optional[str] = Query(None),
    skip: int  = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)
    q = db.query(PlasmaProduct).filter(PlasmaProduct.lab_id == lab_id)
    if product_type:
        q = q.filter(PlasmaProduct.product_type == product_type)
    total    = q.count()
    products = q.order_by(PlasmaProduct.expiry_date.asc()).offset(skip).limit(limit).all()
    return {"total": total, "products": [_plasma_out(p) for p in products]}


# ═══════════════════════════════════════════════════════════════════
#  INVENTORY & NETWORK
# ═══════════════════════════════════════════════════════════════════

@router.get("/inventory/summary")
def get_inventory_summary(
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Per-(blood_type, component) count of available screened units."""
    _require_roles(user, "admin", "lab_admin", "staff", "master_admin", "doctor")
    lab_id = _get_lab_id(user)
    return inventory_summary(db, lab_id=lab_id)


@router.get("/inventory/shortages")
def get_shortages(
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Return shortage alerts for blood types below safe thresholds."""
    _require_roles(user, "admin", "lab_admin", "master_admin")
    lab_id = _get_lab_id(user)
    alerts = detect_shortages(db, lab_id=lab_id)
    return {"alert_count": len(alerts), "alerts": alerts}


@router.get("/network/search")
def network_search(
    blood_type: str = Query(...),
    component:  str = Query(...),
    units:      int = Query(1, ge=1, le=50),
    db:   Session = Depends(get_db),
    user          = Depends(get_current_user),
):
    """Search the entire network for available units across all labs."""
    _require_roles(user, "admin", "lab_admin", "master_admin")
    if blood_type not in BLOOD_TYPES:
        raise HTTPException(422, f"فصيلة دم غير صحيحة: {blood_type}")

    from ..services.blood_matching import find_units_network_wide
    grouped = find_units_network_wide(db, blood_type, component, units)

    result = []
    for lab_id, lab_units in grouped.items():
        result.append({
            "lab_id":    lab_id,
            "available": len(lab_units),
            "earliest_expiry": str(min(u.expiry_date for u in lab_units)),
        })
    result.sort(key=lambda x: -x["available"])

    total_units = sum(x["available"] for x in result)
    return {
        "blood_type":   blood_type,
        "component":    component,
        "requested":    units,
        "total_available_network": total_units,
        "labs": result,
    }


# ── Output serializers ────────────────────────────────────────────────────────

def _donor_out(d: Donor) -> dict:
    return {
        "id":               d.id,
        "full_name":        d.full_name,
        "blood_type":       d.blood_type,
        "phone":            d.phone,
        "gender":           d.gender,
        "city":             d.city,
        "eligibility_status": d.eligibility_status,
        "last_donation_date": str(d.last_donation_date) if d.last_donation_date else None,
        "total_donations":  d.total_donations,
        "is_eligible":      d.is_eligible,
        "created_at":       d.created_at.isoformat() if d.created_at else None,
    }


def _unit_out(u: BloodUnit) -> dict:
    return {
        "id":               u.id,
        "barcode":          u.barcode,
        "blood_type":       u.blood_type,
        "component":        u.component,
        "volume_ml":        u.volume_ml,
        "collection_date":  str(u.collection_date),
        "expiry_date":      str(u.expiry_date),
        "days_remaining":   u.days_remaining,
        "status":           u.status,
        "screening_passed": u.screening_passed,
        "temp_alert_flag":  u.temp_alert_flag,
        "lab_id":           u.lab_id,
    }


def _request_out(r: BloodRequest) -> dict:
    return {
        "id":               r.id,
        "blood_type":       r.blood_type,
        "component":        r.component,
        "units_required":   r.units_required,
        "units_fulfilled":  r.units_fulfilled,
        "urgency":          r.urgency,
        "status":           r.status,
        "requesting_lab_id": r.requesting_lab_id,
        "patient_id":       r.patient_id,
        "clinical_indication": r.clinical_indication,
        "matched_at":       r.matched_at.isoformat() if r.matched_at else None,
        "created_at":       r.created_at.isoformat() if r.created_at else None,
    }


def _transfusion_out(t: Transfusion) -> dict:
    return {
        "id":               t.id,
        "patient_id":       t.patient_id,
        "unit_id":          t.unit_id,
        "request_id":       t.request_id,
        "crossmatch_result": t.crossmatch_result,
        "transfusion_time": t.transfusion_time.isoformat() if t.transfusion_time else None,
        "reaction_flag":    t.reaction_flag,
        "reaction_type":    t.reaction_type,
        "pre_transfusion_hb":  t.pre_transfusion_hb,
        "post_transfusion_hb": t.post_transfusion_hb,
    }


def _plasma_out(p: PlasmaProduct) -> dict:
    return {
        "id":               p.id,
        "product_type":     p.product_type,
        "batch_number":     p.batch_number,
        "brand_name":       p.brand_name,
        "quantity_units":   p.quantity_units,
        "expiry_date":      str(p.expiry_date),
        "status":           p.status,
        "manufacturer":     p.manufacturer,
        "storage_condition":p.storage_condition,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_donor(donor_id: int, user, db: Session) -> Donor:
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(404, "المتبرع غير موجود")
    if donor.lab_id != user.lab_id:
        raise HTTPException(403, "لا يمكنك الوصول إلى هذا المتبرع")
    return donor


def _get_unit(unit_id: int, user, db: Session) -> BloodUnit:
    unit = db.query(BloodUnit).filter(BloodUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(404, "الوحدة غير موجودة")
    if unit.lab_id != user.lab_id:
        raise HTTPException(403, "لا يمكنك الوصول إلى هذه الوحدة")
    return unit
