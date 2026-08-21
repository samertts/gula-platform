from __future__ import annotations

from typing import Any, NoReturn, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.clinical_gateway.diagnostic_report_service import (
    DiagnosticReportConflict,
    DiagnosticReportService,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

router = APIRouter(prefix="/api/v1/clinical/diagnostic-reports", tags=["Canonical Diagnostic Reports"])


class DiagnosticReportFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)


class DiagnosticReportAmendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    conclusion: str | None = Field(default=None, max_length=10000)
    reason: str = Field(min_length=1, max_length=1000)


def _raise(exc: Exception) -> NoReturn:
    if isinstance(exc, ClinicalGatewayBlocked):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Diagnostic report authorization denied") from exc
    if isinstance(exc, DiagnosticReportConflict):
        detail = str(exc)
        if detail.endswith("not_found"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic report source not found") from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
    raise exc


@router.post("/from-lab-orders/{order_id}", status_code=status.HTTP_201_CREATED)
def create_from_lab_order(
    order_id: int,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        report = DiagnosticReportService(db).create_from_lab_order(actor=actor, order_id=order_id)
        db.commit()
        return cast(dict[str, Any], DiagnosticReportService.to_safe_dict(report))
    except (ClinicalGatewayBlocked, DiagnosticReportConflict) as exc:
        db.rollback()
        _raise(exc)


@router.post("/from-radiology-reports/{report_id}", status_code=status.HTTP_201_CREATED)
def create_from_radiology_report(
    report_id: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        report = DiagnosticReportService(db).create_from_radiology_report(actor=actor, report_id=report_id)
        db.commit()
        return cast(dict[str, Any], DiagnosticReportService.to_safe_dict(report))
    except (ClinicalGatewayBlocked, DiagnosticReportConflict) as exc:
        db.rollback()
        _raise(exc)


@router.get("/{report_id}")
def get_diagnostic_report(
    report_id: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        report = DiagnosticReportService(db).get(actor=actor, report_id=report_id)
        return cast(dict[str, Any], DiagnosticReportService.to_safe_dict(report))
    except (ClinicalGatewayBlocked, DiagnosticReportConflict) as exc:
        db.rollback()
        _raise(exc)


@router.post("/{report_id}/finalize")
def finalize_diagnostic_report(
    report_id: str,
    payload: DiagnosticReportFinalizeRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        report = DiagnosticReportService(db).finalize(
            actor=actor,
            report_id=report_id,
            expected_version=payload.expected_version,
        )
        db.commit()
        return cast(dict[str, Any], DiagnosticReportService.to_safe_dict(report))
    except (ClinicalGatewayBlocked, DiagnosticReportConflict) as exc:
        db.rollback()
        _raise(exc)


@router.post("/{report_id}/amend")
def amend_diagnostic_report(
    report_id: str,
    payload: DiagnosticReportAmendRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        report = DiagnosticReportService(db).amend(
            actor=actor,
            report_id=report_id,
            expected_version=payload.expected_version,
            conclusion=payload.conclusion,
            reason=payload.reason,
        )
        db.commit()
        return cast(dict[str, Any], DiagnosticReportService.to_safe_dict(report))
    except (ClinicalGatewayBlocked, DiagnosticReportConflict) as exc:
        db.rollback()
        _raise(exc)
