"""Digital Patient Card endpoints.

Endpoints
---------
- GET  /patient-card/{patient_id}            → card payload + signed QR token
- GET  /patient-card/{patient_id}/qr.png     → QR image (PNG) for the card token
- GET  /patient-card/{patient_id}/history    → full longitudinal history
- POST /patient-card/scan                    → resolve a scanned token to a patient
- GET  /patient-card/{patient_id}/print      → printable Arabic-first HTML card

Security invariants enforced here:
- All reads filter by ``current_user.lab_id`` (tenant isolation).
- Scan tokens are HMAC-signed and bound to the issuing lab; a token issued by
  Lab A cannot be redeemed by a user from Lab B even if it leaks.
- Every card view, scan, and history fetch is written to the audit log.
- Rate limits cap abuse at 60 requests/min/user (history is heavier — 30/min).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip, rate_limit_user
from ..services.audit_service import log_action
from ..services.patient_card import (
    CardTokenError,
    build_card_view,
    build_full_history,
    issue_card_token,
    lookup_patient_for_lab,
    render_card_qr_png,
    verify_card_token,
)

router = APIRouter(prefix="/patient-card", tags=["patient-card"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class ScanRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


# ── Card retrieval ───────────────────────────────────────────────────────────


@router.get("/{patient_id}")
def get_patient_card(
    patient_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the patient card payload + a freshly-signed QR token."""
    rate_limit_user(request, current_user.id, max_per_minute=60)

    patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    token = issue_card_token(patient.id, patient.lab_id)

    log_action(
        db,
        action="view",
        resource_type="patient_card",
        resource_id=patient.id,
        user_id=current_user.id,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
    )
    db.commit()

    return {
        "card": build_card_view(patient),
        "token": token,
        "qr_url": f"/patient-card/{patient.id}/qr.png",
    }


@router.get("/{patient_id}/qr.png")
def get_patient_card_qr(
    patient_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PNG image of the patient-card QR. Always issues a fresh token so an
    intercepted image with an expired token cannot be reused indefinitely.
    """
    rate_limit_user(request, current_user.id, max_per_minute=60)

    patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    token = issue_card_token(patient.id, patient.lab_id)
    png = render_card_qr_png(token)
    return Response(content=png, media_type="image/png")


# ── Scan ─────────────────────────────────────────────────────────────────────


@router.post("/scan")
def scan_patient_card(
    body: ScanRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resolve a scanned QR token to the patient record.

    Rejects with 403 when the token belongs to a different lab — patient cards
    are not portable across labs by design (each lab maintains its own
    longitudinal record; cross-lab linkage happens via the MPI/Citizen layer).
    """
    rate_limit_user(request, current_user.id, max_per_minute=60)

    try:
        patient_id, token_lab_id = verify_card_token(body.token)
    except CardTokenError as e:
        # Audit failed scans — they are an attack signal.
        log_action(
            db,
            action="scan_failed",
            resource_type="patient_card",
            resource_id=None,
            user_id=current_user.id,
            user_role=current_user.role,
            details=str(e)[:200],
            ip_address=get_client_ip(request),
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired card token") from e

    if token_lab_id != current_user.lab_id:
        log_action(
            db,
            action="scan_cross_lab_blocked",
            resource_type="patient_card",
            resource_id=patient_id,
            user_id=current_user.id,
            user_role=current_user.role,
            details=f"token_lab={token_lab_id}",
            ip_address=get_client_ip(request),
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Card belongs to a different lab")

    patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    log_action(
        db,
        action="scan",
        resource_type="patient_card",
        resource_id=patient.id,
        user_id=current_user.id,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
    )
    db.commit()

    return {"card": build_card_view(patient)}


# ── Full history ─────────────────────────────────────────────────────────────


@router.get("/{patient_id}/history")
def get_patient_full_history(
    patient_id: int,
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate the patient's full visit/result timeline within the lab."""
    rate_limit_user(request, current_user.id, max_per_minute=30)

    patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    history = build_full_history(db, patient, limit_orders=limit)

    log_action(
        db,
        action="view_history",
        resource_type="patient_card",
        resource_id=patient.id,
        user_id=current_user.id,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
    )
    db.commit()

    return history


# ── Printable Arabic card ────────────────────────────────────────────────────

_PRINT_TEMPLATE = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>بطاقة المراجع — {full_name}</title>
<style>
  @page {{ size: A6; margin: 8mm; }}
  body {{ font-family: "Tajawal", "Cairo", system-ui, sans-serif;
          margin: 0; padding: 0; color: #0f172a; }}
  .card {{ width: 100%; max-width: 360px; margin: 0 auto;
           border: 1px solid #1e40af; border-radius: 10px; padding: 14px; }}
  h1 {{ font-size: 14px; margin: 0 0 8px; color: #1e40af;
        letter-spacing: 0.5px; }}
  .row {{ display: flex; justify-content: space-between; gap: 10px;
          margin-bottom: 10px; }}
  .info dt {{ font-size: 11px; color: #475569; margin-top: 6px; }}
  .info dd {{ font-size: 13px; margin: 0; font-weight: 600; }}
  .qr {{ flex: 0 0 auto; text-align: center; }}
  .qr img {{ width: 130px; height: 130px; }}
  .health-id {{ font-family: "Courier New", monospace; font-size: 11px;
                background: #f1f5f9; padding: 4px 6px; border-radius: 4px;
                display: inline-block; }}
  footer {{ font-size: 10px; color: #64748b; text-align: center;
            margin-top: 8px; border-top: 1px dashed #cbd5e1; padding-top: 6px; }}
  @media print {{ body {{ background: white; }} }}
</style>
</head>
<body>
  <div class="card">
    <h1>بطاقة المراجع — منصة GULA</h1>
    <div class="row">
      <dl class="info">
        <dt>الاسم</dt><dd>{full_name}</dd>
        <dt>المعرّف الصحي</dt><dd><span class="health-id">{health_id}</span></dd>
        <dt>تاريخ الميلاد</dt><dd>{birth_date}</dd>
        <dt>الجنس</dt><dd>{gender_ar}</dd>
        <dt>الهاتف</dt><dd>{phone}</dd>
      </dl>
      <div class="qr">
        <img src="data:image/png;base64,{qr_b64}" alt="QR">
        <div style="font-size:10px; color:#475569; margin-top:4px;">امسح للوصول</div>
      </div>
    </div>
    <footer>
      هذه البطاقة سرية ومخصصة للاستخدام داخل المختبر فقط.
      صلاحية الرمز محدودة وتُجدَّد عند كل طباعة.
    </footer>
  </div>
</body>
</html>
"""


_GENDER_AR = {"M": "ذكر", "F": "أنثى", "male": "ذكر", "female": "أنثى"}


@router.get("/{patient_id}/print", response_class=HTMLResponse)
def get_patient_card_print(
    patient_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Printable Arabic-first HTML card with embedded QR (base64)."""
    import base64

    rate_limit_user(request, current_user.id, max_per_minute=30)

    patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    token = issue_card_token(patient.id, patient.lab_id)
    qr_png = render_card_qr_png(token, box_size=6, border=2)
    qr_b64 = base64.b64encode(qr_png).decode("ascii")

    html = _PRINT_TEMPLATE.format(
        full_name=_html_escape(patient.full_name),
        health_id=_html_escape(patient.health_id or "—"),
        birth_date=patient.birth_date.isoformat() if patient.birth_date else "—",
        gender_ar=_GENDER_AR.get(patient.gender or "", "—"),
        phone=_html_escape(patient.phone or "—"),
        qr_b64=qr_b64,
    )

    log_action(
        db,
        action="print",
        resource_type="patient_card",
        resource_id=patient.id,
        user_id=current_user.id,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
    )
    db.commit()

    return HTMLResponse(content=html)


def _html_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
