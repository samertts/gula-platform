from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.reference.infrastructure.dependencies import get_result_service
from app.reference.services import (
    CriticalResultError,
    DomainError,
    InvalidOrderError,
    LabResultDomain,
    ReferenceRange,
    ResultNotFoundError,
)
from app.reference.services.result_service import ResultService

router = APIRouter(prefix="/reference/results", tags=["reference-results"])


@router.post("")
async def submit_result(
    order_id: str = Query(..., description="معرف الطلب"),
    analyte: str = Query(..., description="اسم التحليل"),
    value: Decimal = Query(..., description="القيمة"),
    unit: str = Query(..., description="وحدة القياس"),
    min_value: Decimal | None = Query(None, description="الحد الأدنى الطبيعي"),
    max_value: Decimal | None = Query(None, description="الحد الأعلى الطبيعي"),
    min_critical: Decimal | None = Query(None, description="الحد الأدنى الحرج"),
    max_critical: Decimal | None = Query(None, description="الحد الأعلى الحرج"),
    notes: str = Query("", description="ملاحظات"),
    service: ResultService = Depends(get_result_service),
) -> dict:
    reference_range: ReferenceRange | None = None
    if any(x is not None for x in (min_value, max_value, min_critical, max_critical)):
        reference_range = ReferenceRange(
            analyte=analyte,
            unit=unit,
            min_value=min_value,
            max_value=max_value,
            min_critical=min_critical,
            max_critical=max_critical,
        )

    result = LabResultDomain(
        order_id=order_id,
        analyte=analyte,
        value=value,
        unit=unit,
        reference_range=reference_range,
        notes=notes,
    )

    try:
        saved = await service.submit_result(result)
    except InvalidOrderError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e
    except CriticalResultError as e:
        result.is_critical = True
        result.flagged = "حرج"
        return _result_to_response(result, critical_warning=str(e))
    except DomainError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e

    return _result_to_response(saved)


@router.get("/critical")
async def list_critical_results(
    lab_id: str = Query(..., description="معرف المختبر"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ResultService = Depends(get_result_service),
) -> dict:
    results, total = await service.list_critical_results(
        lab_id=lab_id,
        limit=limit,
        offset=offset,
    )
    return {
        "results": [_result_to_response(r) for r in results],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{result_id}")
async def get_result(
    result_id: str,
    service: ResultService = Depends(get_result_service),
) -> dict:
    try:
        result = await service.get_result(result_id)
    except ResultNotFoundError as e:
        raise HTTPException(status_code=404, detail="Resource not found") from e
    return _result_to_response(result)


def _result_to_response(
    result: LabResultDomain,
    critical_warning: str | None = None,
) -> dict:
    resp = {
        "result_id": result.result_id,
        "order_id": result.order_id,
        "analyte": result.analyte,
        "value": str(result.value),
        "unit": result.unit,
        "reference_range": (
            {
                "analyte": result.reference_range.analyte,
                "unit": result.reference_range.unit,
                "min_value": (
                    str(result.reference_range.min_value)
                    if result.reference_range.min_value is not None
                    else None
                ),
                "max_value": (
                    str(result.reference_range.max_value)
                    if result.reference_range.max_value is not None
                    else None
                ),
                "min_critical": (
                    str(result.reference_range.min_critical)
                    if result.reference_range.min_critical is not None
                    else None
                ),
                "max_critical": (
                    str(result.reference_range.max_critical)
                    if result.reference_range.max_critical is not None
                    else None
                ),
            }
            if result.reference_range
            else None
        ),
        "is_critical": result.is_critical,
        "flagged": result.flagged,
        "notes": result.notes,
        "created_at": (result.created_at.isoformat() if result.created_at else None),
        "performed_by": result.performed_by,
    }
    if critical_warning:
        resp["critical_warning"] = critical_warning
    return resp
