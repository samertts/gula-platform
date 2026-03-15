import io
import json
import qrcode
from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from ..config import BASE_URL
from ..database import get_db
from ..models.lab_result import LabResult, hash_token
from ..models.lab_order import LabOrder
from ..models.patient import Patient
from ..models.lab import Lab

router = APIRouter(tags=["qr"])


@router.get("/qr/{token}")
def generate_qr(token: str):
    """Generate QR code for a result link (URL only)."""
    url = f"{BASE_URL}/r/{token}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/qr-medical/{token}")
def generate_medical_qr(token: str, db: Session = Depends(get_db)):
    """Generate Structured Medical QR containing actual test data.

    This QR can be scanned by any compatible health system to import results
    directly without manual entry. Uses a FHIR-lite JSON format.
    """
    token_h = hash_token(token)
    result = db.query(LabResult).filter(LabResult.token_hash == token_h).first()
    if not result:
        return Response(content=b"Not found", status_code=404)

    order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first() if order else None
    lab = db.query(Lab).filter(Lab.id == order.lab_id).first() if order else None

    # Get all results for this order
    all_results = db.query(LabResult).filter(LabResult.order_id == result.order_id).all()

    # Build FHIR-lite structured data (compact for QR)
    medical_data = {
        "v": 1,  # schema version
        "sys": "GULA",
        "lab": lab.name if lab else None,
        "pid": patient.health_id if patient else None,
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

    # Compact JSON (no spaces)
    data_str = json.dumps(medical_data, separators=(",", ":"), ensure_ascii=False)

    qr = qrcode.QRCode(version=None, box_size=8, border=3, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data_str)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1e40af", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")
