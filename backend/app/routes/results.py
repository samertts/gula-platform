from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_order import LabOrder
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip, rate_limit_public, rate_limit_user
from ..services.order_service import (
    TEST_PROFILES,
)
from ..services.order_service import (
    cancel_order as _cancel_order,
)
from ..services.order_service import (
    create_order as _create_order,
)
from ..services.order_service import (
    download_result_pdf as _download_result_pdf,
)
from ..services.order_service import (
    get_order_by_id as _get_order_by_id,
)
from ..services.order_service import (
    get_patient_history_by_id as _get_patient_history_by_id,
)
from ..services.order_service import (
    get_patient_history_by_phone as _get_patient_history_by_phone,
)
from ..services.order_service import (
    get_public_result as _get_public_result,
)
from ..services.order_service import (
    list_orders as _list_orders,
)
from ..services.order_service import (
    validate_order as _validate_order,
)

router = APIRouter(tags=["results"])


# ===== Schemas =====


class ResultItem(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class CreateOrderRequest(BaseModel):
    patient_id: int
    doctor_name: str | None = None
    doctor_user_id: int | None = None  # link to a registered doctor account for data isolation
    results: list[ResultItem]

    @field_validator("doctor_name")
    @classmethod
    def validate_doctor_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError("Doctor name must be at most 200 characters")
        return v


class AnalyzeRequest(BaseModel):
    results: list[ResultItem]


@router.get("/test-profiles")
def list_test_profiles():
    """List available composite test profiles (CBC, Lipid, etc.)."""
    return {
        name: [
            {
                "test_name": t["test_name"],
                "unit": t["unit"],
                "normal_range_low": t["normal_range_low"],
                "normal_range_high": t["normal_range_high"],
            }
            for t in tests
        ]
        for name, tests in TEST_PROFILES.items()
    }


@router.post("/orders", status_code=201)
def create_order_route(
    data: CreateOrderRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit_user(request, current_user.id, max_per_minute=30)

    results_data = [
        {
            "test_name": r.test_name,
            "value": r.value,
            "value_text": r.value_text,
            "unit": r.unit,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
        }
        for r in data.results
    ]

    response = _create_order(
        db=db,
        lab_id=current_user.lab_id,
        user_id=current_user.id,
        user_role=current_user.role,
        patient_id=data.patient_id,
        doctor_name=data.doctor_name,
        doctor_user_id=data.doctor_user_id,
        results_data=results_data,
        ip_address=get_client_ip(request),
        idempotency_key=request.headers.get("Idempotency-Key"),
    )

    if "error" in response:
        raise HTTPException(status_code=response["status_code"], detail=response["error"])

    return response


@router.get("/orders")
def list_orders_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: str | None = Query(None, max_length=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _list_orders(
        db=db,
        lab_id=current_user.lab_id,
        user_role=current_user.role,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
    )


@router.get("/orders/{order_id}")
def get_order_route(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = _get_order_by_id(
        db=db,
        order_id=order_id,
        lab_id=current_user.lab_id,
        user_role=current_user.role,
        user_id=current_user.id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.post("/orders/{order_id}/validate")
def validate_order_route(
    order_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate and lock an order.  Only admin/master_admin/doctor may do this.
    After validation the order is immutable — results cannot be deleted or edited.

    Race-condition protection: uses an atomic UPDATE WHERE locked_at IS NULL
    so that two simultaneous validation requests cannot both succeed.
    """
    rate_limit_user(request, current_user.id, max_per_minute=20)

    result = _validate_order(
        db=db,
        order_id=order_id,
        lab_id=current_user.lab_id,
        user_role=current_user.role,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
    )

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return result


@router.post("/orders/{order_id}/cancel")
def cancel_order_route(
    order_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an order.  Validated (locked) orders cannot be cancelled."""
    rate_limit_user(request, current_user.id, max_per_minute=20)

    result = _cancel_order(
        db=db,
        order_id=order_id,
        lab_id=current_user.lab_id,
        user_role=current_user.role,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
    )

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return result


@router.get("/r/{token}")
def get_public_result_route(token: str, request: Request, db: Session = Depends(get_db)):
    """Public result page - accessible without authentication. Rate limited."""
    rate_limit_public(request, max_per_minute=30)

    result = _get_public_result(db=db, token=token, ip_address=get_client_ip(request))

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return result


@router.get("/r/{token}/pdf")
def download_result_pdf_route(token: str, request: Request, db: Session = Depends(get_db)):
    """Download result as a professional PDF report with QR code."""
    rate_limit_public(request, max_per_minute=10)

    result = _download_result_pdf(db=db, token=token, ip_address=get_client_ip(request))

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return Response(
        content=result["pdf_bytes"],
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'},
    )


@router.get("/patient-history/{patient_id}")
def get_patient_history_by_id_route(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete test history for a patient (authenticated, lab-scoped)."""
    result = _get_patient_history_by_id(
        db=db,
        patient_id=patient_id,
        lab_id=current_user.lab_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result


@router.get("/history/{phone}")
def get_patient_history_route(
    phone: str, request: Request, name: str | None = None, db: Session = Depends(get_db),
):
    """Get patient test history by phone number (public, rate limited).
    Requires 'name' query param matching full patient name as verification.

    Multi-tenant isolation: the phone number may belong to Patient records in
    multiple labs (each lab keeps its own patient roster).  We aggregate results
    across ALL labs where the phone+name pair matches, so the citizen sees their
    complete history regardless of which lab they visited.  Only the patient's
    own results are returned — no cross-patient data is possible.
    """
    rate_limit_public(request, max_per_minute=5)

    result = _get_patient_history_by_phone(db=db, phone=phone, name=name)

    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])

    return result


# ─── Clinical Intelligence ────────────────────────────────────────────────────


@router.post("/analyze")
def analyze_results(
    data: AnalyzeRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
):
    """Analyze a batch of results for multi-test clinical patterns.
    Returns detected patterns (sepsis, DKA, renal failure, etc.)
    and a flag summary. Does NOT diagnose — flags for physician review.
    """
    # Rate limit: 20 analyses per minute per user_id + IP fallback (CPU-heavy endpoint)
    rate_limit_user(request, current_user.id, max_per_minute=20)
    from ..services.clinical_intelligence import analyze_results as _analyze
    from ..services.clinical_intelligence import quick_flag_summary

    raw = [
        {
            "test_name": r.test_name,
            "value": r.value,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
        }
        for r in data.results
    ]

    patterns = _analyze(raw)
    summary = quick_flag_summary(raw)

    return {
        "patterns_detected": len(patterns),
        "patterns": patterns,
        "flag_summary": summary,
        "has_critical_pattern": any(p["severity"] == "critical" for p in patterns),
    }


@router.get("/orders/{order_id}/intelligence")
def analyze_order(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run clinical intelligence analysis on an existing order's results.
    Useful for post-entry review.
    """
    from ..services.clinical_intelligence import analyze_results as _analyze
    from ..services.clinical_intelligence import quick_flag_summary

    order = (
        db.query(LabOrder)
        .filter(
            LabOrder.id == order_id,
            LabOrder.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    raw = [
        {
            "test_name": r.test_name,
            "value": r.value,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
        }
        for r in order.results
    ]

    patterns = _analyze(raw)
    summary = quick_flag_summary(raw)

    return {
        "order_id": order_id,
        "patterns_detected": len(patterns),
        "patterns": patterns,
        "flag_summary": summary,
        "has_critical_pattern": any(p["severity"] == "critical" for p in patterns),
    }
