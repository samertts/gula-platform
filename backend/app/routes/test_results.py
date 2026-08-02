from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission, require_verify_authority
from ..security.rate_limit import rate_limit_user
from ..services.test_result_service import (
    citizen_timeline as service_timeline,
)
from ..services.test_result_service import (
    create_result,
    get_result,
    list_citizen_results,
    list_results,
    verify_result,
)
from ..services.test_result_service import (
    validate_result_payload as service_validate,
)

router = APIRouter(prefix="/test-results", tags=["test-results"])


class TestResultCreate(BaseModel):
    health_id: str = Field(..., min_length=3, max_length=32)
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: str | None = Field(None, max_length=50)
    value: float | None = None
    value_text: str | None = Field(None, max_length=200)
    unit: str | None = Field(None, max_length=20)
    normal_range_low: float | None = None
    normal_range_high: float | None = None
    sample_type: str | None = Field("blood", max_length=50)
    doctor_name: str | None = Field(None, max_length=200)
    order_id: int | None = Field(
        None, description="Attach to an existing order; otherwise a new one is created."
    )

    @field_validator("test_name", "doctor_name")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class TestResultValidateRequest(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: str | None = Field(None, max_length=50)
    value: float | None = None
    unit: str | None = Field(None, max_length=20)
    normal_range_low: float | None = None
    normal_range_high: float | None = None


@router.post("/", status_code=201)
def create_test_result(
    data: TestResultCreate,
    request: Request,
    current_user: LabUser = Depends(require_permission("results:write")),
    db: Session = Depends(get_db),
):
    return create_result(
        health_id=data.health_id,
        test_name=data.test_name,
        test_code=data.test_code,
        value=data.value,
        value_text=data.value_text,
        unit=data.unit,
        normal_range_low=data.normal_range_low,
        normal_range_high=data.normal_range_high,
        sample_type=data.sample_type,
        doctor_name=data.doctor_name,
        order_id=data.order_id,
        current_user=current_user,
        request=request,
        db=db,
    )


@router.post("/validate")
def validate_test_result(
    data: TestResultValidateRequest,
    request: Request,
    current_user: LabUser = Depends(require_permission("results:write")),
    db: Session = Depends(get_db),
):
    rate_limit_user(request, current_user.id, max_per_minute=60)
    return service_validate(
        test_name=data.test_name,
        value=data.value,
        unit=data.unit,
        normal_low=data.normal_range_low,
        normal_high=data.normal_range_high,
        test_code=data.test_code,
        db=db,
    )


@router.get("", summary="List lab test results")
def list_test_results(
    health_id: str | None = Query(None, max_length=32),
    category: str | None = Query(None, max_length=50),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    is_abnormal: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(require_permission("results:read")),
    db: Session = Depends(get_db),
):
    return list_results(
        current_user,
        db,
        health_id=health_id,
        category=category,
        date_from=date_from,
        date_to=date_to,
        is_abnormal=is_abnormal,
        skip=skip,
        limit=limit,
    )


@router.get("/{result_id}")
def get_test_result(
    result_id: int,
    current_user: LabUser = Depends(require_permission("results:read")),
    db: Session = Depends(get_db),
):
    return get_result(result_id, current_user, db)


@router.put("/{result_id}/verify")
def verify_test_result(
    result_id: int,
    request: Request,
    current_user: LabUser = Depends(require_verify_authority),
    db: Session = Depends(get_db),
):
    return verify_result(result_id, current_user, request, db)


@router.get("/citizen/{health_id}")
def list_citizen_results_endpoint(
    health_id: str,
    category: str | None = Query(None, max_length=50),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    is_abnormal: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(require_permission("results:read")),
    db: Session = Depends(get_db),
):
    return list_citizen_results(
        health_id, category, date_from, date_to, is_abnormal, skip, limit, current_user, db
    )


@router.get("/citizen/{health_id}/timeline")
def citizen_timeline_endpoint(
    health_id: str,
    category: str | None = Query(None, max_length=50),
    current_user: LabUser = Depends(require_permission("results:read")),
    db: Session = Depends(get_db),
):
    return service_timeline(health_id, category, current_user, db)
