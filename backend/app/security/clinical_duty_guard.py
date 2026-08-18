"""Shared server-side Duty guard for clinical mutations.

Design reminder: a valid login is not clinical authority. Every mutation must
carry a server-issued Duty context and a patient scope that the service verifies.
"""
from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.lab_user import LabUser
from app.services.doctor_duty_service import DoctorDutyService, DutyAuthorizationError


def require_clinical_duty(request: Request, current_user: LabUser, db: Session, patient_id: str) -> None:
    context_id = request.headers.get("X-Duty-Context-ID")
    if not context_id:
        raise HTTPException(status_code=403, detail={"code": "DUTY_CONTEXT_REQUIRED", "message": "Active clinical duty is required"})
    try:
        numeric_patient_id = int(patient_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail={"code": "PATIENT_SCOPE_UNVERIFIED", "message": "Patient scope cannot be verified"}) from exc
    try:
        DoctorDutyService(db).authorize_context(context_id=context_id, user_id=current_user.id, patient_id=numeric_patient_id)
    except DutyAuthorizationError as exc:
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": "Clinical access denied"}) from exc
