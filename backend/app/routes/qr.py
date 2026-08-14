import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from shared.qr import generate_qr, generate_qr_image

from .._compat import UTC
from ..config import BASE_URL
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..security.rate_limit import rate_limit_public

router = APIRouter(tags=["qr"])


@router.get("/qr/{token}")
def generate_qr_route(token: str, request: Request):
    """Generate QR code for a result link (URL only)."""
    rate_limit_public(request, max_per_minute=20)

    if not token or len(token) > 64 or len(token) < 10:
        return Response(content=b"Invalid token", status_code=400)

    url = f"{BASE_URL}/r/{token}"
    img_bytes = generate_qr_image(url, box_size=10, border=4)
    return Response(content=img_bytes, media_type="image/png")


@router.get("/qr-medical/{token}")
def generate_medical_qr(token: str, request: Request, db: Session = Depends(get_db)):
    """Generate Structured Medical QR containing actual test data."""
    rate_limit_public(request, max_per_minute=10)

    token_h = hash_token(token)
    result = db.query(LabResult).filter(LabResult.token_hash == token_h).first()
    if not result:
        return Response(content=b"Not found", status_code=404, headers={"Cache-Control": "no-store"})
    expires_at = result.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at is not None and expires_at <= datetime.now(UTC):
        return Response(content=b"Not found", status_code=404, headers={"Cache-Control": "no-store"})

    order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
    lab = db.query(Lab).filter(Lab.id == order.lab_id).first() if order else None

    all_results = db.query(LabResult).filter(LabResult.order_id == result.order_id).all()

    medical_data = {
        "v": 1,
        "sys": "GULA",
        "lab": lab.name if lab else None,
        "dt": order.created_at.strftime("%Y-%m-%d") if order and order.created_at else None,
        "url": f"{BASE_URL}/r/{token}",
        "tests": [
            {
                "id": r.test_name,
                "v": r.value,
                "t": r.value_text,
                "u": r.unit,
                "rl": r.normal_range_low,
                "rh": r.normal_range_high,
                "f": r.flag,
            }
            for r in all_results
        ],
    }

    data_str = json.dumps(medical_data, separators=(",", ":"), ensure_ascii=False)

    qr = generate_qr(data_str, box_size=8, border=3, error_correction="M")
    img = qr.make_image(fill_color="#1e40af", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
