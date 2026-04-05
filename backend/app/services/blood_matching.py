"""GULA Blood Network — Matching Engine.

Responsibilities:
  1. Blood type compatibility enforcement (never negotiable)
  2. Donor eligibility screening
  3. Unit availability scoring and ranking
  4. Cross-lab inventory search (national coordination)
  5. Demand forecasting (shortage alerts)
  6. Automatic request routing

All compatibility checks raise ValueError on violation — callers must catch
and return 422.  This keeps safety logic out of route handlers.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.blood import (
    Donor, BloodUnit, BloodRequest, PlasmaProduct,
    BLOOD_COMPATIBILITY, COMPONENT_EXPIRY_DAYS,
    MIN_DONATION_INTERVAL_DAYS, MIN_HB_MALE_G_DL, MIN_HB_FEMALE_G_DL,
)

logger = logging.getLogger("gula.gbn.matching")


# ── 1. Compatibility ──────────────────────────────────────────────────────────

def compatible_donor_types(recipient_type: str) -> tuple[str, ...]:
    """Return tuple of blood types a recipient can safely receive.

    Raises ValueError for unknown blood types — call this at API boundary.
    """
    if recipient_type not in BLOOD_COMPATIBILITY:
        raise ValueError(f"Unknown blood type: {recipient_type!r}")
    return BLOOD_COMPATIBILITY[recipient_type]


def is_compatible(donor_type: str, recipient_type: str) -> bool:
    """True if donor blood is safe to transfuse into recipient."""
    try:
        return donor_type in compatible_donor_types(recipient_type)
    except ValueError:
        return False


def assert_compatible(donor_type: str, recipient_type: str) -> None:
    """Raise ValueError if transfusion would be incompatible."""
    if not is_compatible(donor_type, recipient_type):
        raise ValueError(
            f"INCOMPATIBLE TRANSFUSION: donor {donor_type} → recipient {recipient_type}. "
            "Transfusion blocked by blood-type safety rule."
        )


# ── 2. Donor Eligibility ──────────────────────────────────────────────────────

class EligibilityResult:
    __slots__ = ("eligible", "reason", "eligible_from")

    def __init__(self, eligible: bool, reason: str = "", eligible_from: Optional[date] = None):
        self.eligible     = eligible
        self.reason       = reason
        self.eligible_from = eligible_from   # None = eligible now or permanently deferred


def screen_donor(donor: Donor, hb_g_dl: Optional[float] = None) -> EligibilityResult:
    """Full eligibility screen against WHO / Iraqi MoH standards.

    Checks (in order):
      1. Permanent deferral
      2. Temporary deferral (until date)
      3. Minimum donation interval (90 days)
      4. Haemoglobin threshold (if provided)

    Returns EligibilityResult — never raises.
    """
    if donor.eligibility_status == "deferred_permanent":
        return EligibilityResult(False, "متبرع مؤجل بشكل دائم: " + (donor.deferral_reason or ""))

    if donor.eligibility_status == "deferred_temporary" and donor.deferral_until:
        today = date.today()
        if today < donor.deferral_until:
            return EligibilityResult(
                False,
                f"تأجيل مؤقت حتى {donor.deferral_until}",
                eligible_from=donor.deferral_until,
            )

    if donor.last_donation_date:
        days_since = (date.today() - donor.last_donation_date).days
        if days_since < MIN_DONATION_INTERVAL_DAYS:
            remaining   = MIN_DONATION_INTERVAL_DAYS - days_since
            eligible_on = date.today() + timedelta(days=remaining)
            return EligibilityResult(
                False,
                f"الفترة بين التبرعات لم تكتمل — {days_since} يوم منذ آخر تبرع (الحد الأدنى {MIN_DONATION_INTERVAL_DAYS} يوماً)",
                eligible_from=eligible_on,
            )

    # Haemoglobin check (optional — only if measured today)
    if hb_g_dl is not None:
        min_hb = MIN_HB_MALE_G_DL if donor.gender == "M" else MIN_HB_FEMALE_G_DL
        if hb_g_dl < min_hb:
            return EligibilityResult(
                False,
                f"الهيموغلوبين منخفض: {hb_g_dl} g/dL (الحد الأدنى {min_hb} g/dL)",
            )

    return EligibilityResult(True, "مؤهل للتبرع")


# ── 3. Unit Availability Search ───────────────────────────────────────────────

def find_available_units(
    db: Session,
    blood_type: str,
    component: str,
    units_needed: int,
    lab_id: Optional[int] = None,
    include_all_labs: bool = False,
) -> list[BloodUnit]:
    """Find available, non-expired, screened units matching the request.

    Priority order:
      1. Closest to expiry (FEFO — First Expired, First Out)
      2. Screened (screening_passed=True) preferred
      3. Same lab first, then other labs if include_all_labs=True

    Args:
        blood_type:       Recipient's blood type (compatibility is applied)
        component:        Requested component type
        units_needed:     How many units to return (soft limit — returns what's available)
        lab_id:           Preferred lab to source from
        include_all_labs: If True, search all labs in the network

    Returns list of BloodUnit (may be shorter than units_needed if stock is low).
    """
    if blood_type not in BLOOD_COMPATIBILITY:
        raise ValueError(f"Unknown blood type: {blood_type!r}")

    compatible = compatible_donor_types(blood_type)
    today      = date.today()

    base_filter = and_(
        BloodUnit.blood_type.in_(compatible),
        BloodUnit.component    == component,
        BloodUnit.status       == "available",
        BloodUnit.expiry_date  >  today,
        # Only use fully screened units
        BloodUnit.screening_passed == True,  # noqa: E712
    )

    q = db.query(BloodUnit).filter(base_filter)

    if lab_id and not include_all_labs:
        q = q.filter(BloodUnit.lab_id == lab_id)
    elif lab_id and include_all_labs:
        # Same-lab units first, then others
        q = q.order_by(
            (BloodUnit.lab_id != lab_id).asc(),   # False (0) = same lab comes first
            BloodUnit.expiry_date.asc(),
        )
    else:
        q = q.order_by(BloodUnit.expiry_date.asc())

    units = q.limit(units_needed).all()
    logger.info(
        "find_available_units: type=%s component=%s needed=%d found=%d lab_id=%s",
        blood_type, component, units_needed, len(units), lab_id,
    )
    return units


def find_units_network_wide(
    db: Session,
    blood_type: str,
    component: str,
    units_needed: int,
) -> dict[int, list[BloodUnit]]:
    """Search entire network for available units, grouped by lab_id.

    Returns dict mapping lab_id → [BloodUnit, ...] ordered FEFO.
    Used for national coordination / inter-lab routing.
    """
    compatible = compatible_donor_types(blood_type)
    today = date.today()

    units = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.blood_type.in_(compatible),
            BloodUnit.component    == component,
            BloodUnit.status       == "available",
            BloodUnit.expiry_date  >  today,
            BloodUnit.screening_passed == True,  # noqa: E712
        )
        .order_by(BloodUnit.expiry_date.asc())
        .limit(units_needed * 5)   # fetch extra for routing decisions
        .all()
    )

    grouped: dict[int, list[BloodUnit]] = {}
    for u in units:
        grouped.setdefault(u.lab_id, []).append(u)
    return grouped


# ── 4. Match Request ──────────────────────────────────────────────────────────

class MatchResult:
    """Result of a match operation."""
    __slots__ = ("matched_units", "from_lab_id", "needs_transfer", "shortage", "message")

    def __init__(
        self,
        matched_units: list[BloodUnit],
        from_lab_id: Optional[int],
        needs_transfer: bool,
        shortage: int,
        message: str,
    ):
        self.matched_units  = matched_units
        self.from_lab_id    = from_lab_id
        self.needs_transfer = needs_transfer
        self.shortage       = shortage       # units still unfulfilled
        self.message        = message


def match_request(db: Session, request: BloodRequest) -> MatchResult:
    """Attempt to fulfil a BloodRequest from available inventory.

    Algorithm:
      1. Try requesting lab first
      2. If insufficient, search entire network
      3. Calculate shortage (unfulfilled units)

    Does NOT mutate any records — caller handles reservation.
    """
    needed = request.units_required - request.units_fulfilled

    # Step 1: same-lab inventory
    local_units = find_available_units(
        db,
        blood_type    = request.blood_type,
        component     = request.component,
        units_needed  = needed,
        lab_id        = request.requesting_lab_id,
        include_all_labs = False,
    )

    if len(local_units) >= needed:
        return MatchResult(
            matched_units  = local_units[:needed],
            from_lab_id    = request.requesting_lab_id,
            needs_transfer = False,
            shortage       = 0,
            message        = f"تمّت المطابقة من مخزون المختبر ({needed} وحدة)",
        )

    # Step 2: network-wide search
    network = find_units_network_wide(db, request.blood_type, request.component, needed)
    all_network_units: list[BloodUnit] = []
    best_lab_id: Optional[int] = None

    # Prefer labs with most available units to minimize number of transfers
    for lab_id, units in sorted(network.items(), key=lambda kv: -len(kv[1])):
        if lab_id == request.requesting_lab_id:
            continue
        if not best_lab_id:
            best_lab_id = lab_id
        all_network_units.extend(units)
        if len(all_network_units) + len(local_units) >= needed:
            break

    combined = (local_units + all_network_units)[:needed]
    shortage = max(0, needed - len(combined))

    if not combined:
        return MatchResult(
            matched_units  = [],
            from_lab_id    = None,
            needs_transfer = False,
            shortage       = needed,
            message        = f"⚠️ لا توجد وحدات متاحة لفصيلة {request.blood_type} ({request.component}) في الشبكة",
        )

    needs_transfer = any(u.lab_id != request.requesting_lab_id for u in combined)
    source_lab     = best_lab_id if needs_transfer else request.requesting_lab_id
    transfer_msg   = " (يحتاج نقل بين مختبرات)" if needs_transfer else ""

    return MatchResult(
        matched_units  = combined,
        from_lab_id    = source_lab,
        needs_transfer = needs_transfer,
        shortage       = shortage,
        message        = f"تمّت المطابقة: {len(combined)} وحدة{transfer_msg}" + (
            f" — نقص {shortage} وحدة" if shortage else ""
        ),
    )


# ── 5. Inventory Summary ──────────────────────────────────────────────────────

def inventory_summary(db: Session, lab_id: Optional[int] = None) -> dict:
    """Return a per-(blood_type, component) count of available units.

    Used for dashboard display and shortage detection.
    """
    today = date.today()
    q = db.query(
        BloodUnit.blood_type,
        BloodUnit.component,
        func.count(BloodUnit.id).label("available"),
        func.min(BloodUnit.expiry_date).label("earliest_expiry"),
    ).filter(
        BloodUnit.status == "available",
        BloodUnit.expiry_date > today,
        BloodUnit.screening_passed == True,  # noqa: E712
    )

    if lab_id:
        q = q.filter(BloodUnit.lab_id == lab_id)

    rows = q.group_by(BloodUnit.blood_type, BloodUnit.component).all()

    summary: dict[str, dict] = {}
    for row in rows:
        key = f"{row.blood_type}/{row.component}"
        summary[key] = {
            "blood_type":      row.blood_type,
            "component":       row.component,
            "available":       row.available,
            "earliest_expiry": str(row.earliest_expiry) if row.earliest_expiry else None,
        }
    return summary


# ── 6. Shortage Detection ─────────────────────────────────────────────────────

# Minimum safe stock per blood type per component (configurable)
_DEFAULT_THRESHOLDS: dict[str, int] = {
    "whole":     5,
    "RBC":       10,
    "platelets": 3,
    "plasma":    5,
    "cryo":      2,
}


def detect_shortages(
    db: Session,
    lab_id: Optional[int] = None,
    thresholds: Optional[dict[str, int]] = None,
) -> list[dict]:
    """Return list of shortage alerts for blood types below safe thresholds.

    Each alert: {blood_type, component, available, threshold, deficit}
    """
    t = thresholds or _DEFAULT_THRESHOLDS
    summary = inventory_summary(db, lab_id)
    alerts  = []

    from ..models.blood import BLOOD_TYPES
    for btype in BLOOD_TYPES:
        for comp, threshold in t.items():
            key       = f"{btype}/{comp}"
            available = summary.get(key, {}).get("available", 0)
            if available < threshold:
                alerts.append({
                    "blood_type": btype,
                    "component":  comp,
                    "available":  available,
                    "threshold":  threshold,
                    "deficit":    threshold - available,
                    "severity":   "critical" if available == 0 else "warning",
                })

    # Sort: critical first, then by deficit descending
    alerts.sort(key=lambda a: (a["severity"] != "critical", -a["deficit"]))
    return alerts


# ── 7. Expiry Alerts ──────────────────────────────────────────────────────────

def expiring_soon(
    db: Session,
    lab_id: Optional[int] = None,
    days_ahead: int = 3,
) -> list[BloodUnit]:
    """Return available units expiring within `days_ahead` days."""
    cutoff = date.today() + timedelta(days=days_ahead)
    q = db.query(BloodUnit).filter(
        BloodUnit.status == "available",
        BloodUnit.expiry_date <= cutoff,
        BloodUnit.expiry_date >= date.today(),
    )
    if lab_id:
        q = q.filter(BloodUnit.lab_id == lab_id)
    return q.order_by(BloodUnit.expiry_date.asc()).all()
