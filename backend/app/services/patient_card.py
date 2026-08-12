"""Patient Card service — digital, QR-backed patient identity.

Builds on the existing Patient model (no schema changes). The "card" is a
short-lived, HMAC-signed token that encodes (patient_id, lab_id, exp). Lab
staff scan the QR at the counter to retrieve the patient's record without
manual lookup. The token is bound to the issuing lab — scans from a different
lab are rejected even if the token leaks.

Why HMAC and not a JWT here:
- Smaller payload → fits comfortably in a low-density QR (good for cheap printers)
- No header overhead, no algorithm-confusion attack surface
- We never need third-party verification — the same backend issues and verifies

History aggregation pulls from the existing operational tables
(`lab_orders`, `lab_results`) — patient "visits" in this platform are
represented by lab orders. No new tables are introduced.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

from sqlalchemy.orm import Session

from ..config import SECRET_KEY
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.patient import Patient

# ── Token format ─────────────────────────────────────────────────────────────
# Body = base64url("<patient_id>.<lab_id>.<exp_unix>")
# Sig  = base64url(HMAC_SHA256(SECRET, body))[:22]   (≈128 bits, plenty)
# Final token = "<body>.<sig>"
#
# Total length is well under 100 chars even for large IDs — small enough to
# scan reliably from a printed card on a low-end Android camera.

_DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 365  # 1 year — patient cards are durable
_DOMAIN = b"gula.patient_card.v1"  # domain-separates from other HMACs


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _sign(body: bytes) -> str:
    mac = hmac.new(SECRET_KEY.encode("utf-8"), _DOMAIN + b"|" + body, hashlib.sha256).digest()
    return _b64u_encode(mac)[:22]


def issue_card_token(patient_id: int, lab_id: int, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> str:
    """Mint a signed, time-bound token for a patient card QR."""
    exp = int(time.time()) + max(60, ttl_seconds)
    body = f"{patient_id}.{lab_id}.{exp}".encode("ascii")
    body_b64 = _b64u_encode(body)
    sig = _sign(body)
    return f"{body_b64}.{sig}"


class CardTokenError(Exception):
    """Raised when a card token is malformed, expired, or has a bad signature."""


def verify_card_token(token: str) -> tuple[int, int]:
    """Verify a card token and return ``(patient_id, lab_id)``.

    Raises ``CardTokenError`` on any failure. Caller MUST then verify the
    returned ``lab_id`` matches the scanning user's lab — this function
    only proves the token is authentic, not that the holder is authorised.
    """
    if not token or not isinstance(token, str) or len(token) > 200:
        raise CardTokenError("invalid token format")

    parts = token.split(".")
    if len(parts) != 2:
        raise CardTokenError("invalid token format")

    body_b64, sig = parts
    expected = _sign(_b64u_decode(body_b64)) if _is_b64u(body_b64) else None
    if expected is None or not hmac.compare_digest(expected, sig):
        raise CardTokenError("bad signature")

    try:
        body = _b64u_decode(body_b64).decode("ascii")
        pid_s, lab_s, exp_s = body.split(".")
        patient_id = int(pid_s)
        lab_id = int(lab_s)
        exp = int(exp_s)
    except (ValueError, UnicodeDecodeError):
        raise CardTokenError("invalid token body") from None

    if exp < int(time.time()):
        raise CardTokenError("token expired")

    if patient_id <= 0 or lab_id <= 0:
        raise CardTokenError("invalid token body")

    return patient_id, lab_id


def _is_b64u(s: str) -> bool:
    if not s:
        return False
    try:
        _b64u_decode(s)
        return True
    except (ValueError, Exception):
        return False


# ── Card view ────────────────────────────────────────────────────────────────


def build_card_view(patient: Patient) -> dict:
    """Compact, presentation-ready snapshot for the front-side of the card.

    Excludes the national_id_hash and family_id_hash — those are sensitive
    derivations that should never round-trip through the UI.
    """
    return {
        "patient_id": patient.id,
        "health_id": patient.health_id,
        "full_name": patient.full_name,
        "phone": patient.phone,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "gender": patient.gender,
        "is_minor": patient.is_minor,
        "lab_id": patient.lab_id,
    }


# ── Full history aggregator ──────────────────────────────────────────────────


def build_full_history(
    db: Session,
    patient: Patient,
    *,
    limit_orders: int = 100,
) -> dict:
    """Return the patient's full longitudinal record visible to their lab.

    Tenant isolation is the caller's responsibility: pass a Patient already
    filtered by the current user's lab_id. We re-assert it on every nested
    query as defence in depth.
    """
    orders = (
        db.query(LabOrder)
        .filter(
            LabOrder.patient_id == patient.id,
            LabOrder.lab_id == patient.lab_id,
        )
        .order_by(LabOrder.created_at.desc())
        .limit(max(1, min(limit_orders, 500)))
        .all()
    )

    order_ids = [o.id for o in orders]
    results_by_order: dict[int, list[LabResult]] = {}
    if order_ids:
        for r in (
            db.query(LabResult)
            .filter(LabResult.order_id.in_(order_ids))
            .order_by(LabResult.created_at.asc())
            .all()
        ):
            results_by_order.setdefault(r.order_id, []).append(r)

    timeline = []
    for o in orders:
        timeline.append(
            {
                "type": "lab_order",
                "order_id": o.id,
                "doctor_name": o.doctor_name,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "validated_at": o.validated_at.isoformat() if o.validated_at else None,
                "results": [
                    {
                        "id": r.id,
                        "test_name": r.test_name,
                        "value": r.value,
                        "value_text": r.value_text,
                        "unit": r.unit,
                        "flag": r.flag,
                        "normal_range_low": r.normal_range_low,
                        "normal_range_high": r.normal_range_high,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in results_by_order.get(o.id, [])
                ],
            },
        )

    completed_or_validated = sum(1 for o in orders if o.status in ("completed", "validated"))
    pending = sum(1 for o in orders if o.status == "pending")

    return {
        "patient": build_card_view(patient),
        "summary": {
            "total_orders": len(orders),
            "completed_or_validated": completed_or_validated,
            "pending": pending,
            "first_visit": orders[-1].created_at.isoformat()
            if orders and orders[-1].created_at
            else None,
            "last_visit": orders[0].created_at.isoformat()
            if orders and orders[0].created_at
            else None,
        },
        "timeline": timeline,
    }


# ── QR generation ────────────────────────────────────────────────────────────


def render_card_qr_png(token: str, *, box_size: int = 8, border: int = 3) -> bytes:
    """Render a PNG QR for the given card token. Delegates to shared.qr."""
    from shared.qr import generate_qr_image

    return generate_qr_image(token, box_size=box_size, border=border)


def lookup_patient_for_lab(db: Session, *, patient_id: int, lab_id: int) -> Patient | None:
    """Single source of truth for tenant-scoped patient lookup."""
    return db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()
