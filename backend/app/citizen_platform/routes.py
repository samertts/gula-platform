from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

logger = logging.getLogger("gula.citizen.routes")

router = APIRouter(prefix="/citizen-platform", tags=["citizen-platform"])


def _get_sdk(request: Any) -> Any:
    from app.citizen_platform.integration import get_sdk
    return get_sdk()


@router.get("/dashboard/{citizen_id}")
async def get_dashboard(
    citizen_id: str,
    sdk: Any = Depends(_get_sdk),
):
    try:
        return await sdk.get_citizen_overview(citizen_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/profile/{citizen_id}")
async def get_profile(
    citizen_id: str,
    sdk: Any = Depends(_get_sdk),
):
    try:
        return await sdk.get_profile(citizen_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health-summary/{citizen_id}")
async def get_health_summary(
    citizen_id: str,
    sdk: Any = Depends(_get_sdk),
):
    try:
        return await sdk.get_health_summary(citizen_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/appointments/{citizen_id}")
async def list_appointments(
    citizen_id: str,
    status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sdk: Any = Depends(_get_sdk),
):
    try:
        appointments = await sdk.appointments.list_appointments(
            citizen_id, status=status, date_from=date_from, date_to=date_to, skip=skip, limit=limit,
        )
        return {"appointments": [a.__dict__ for a in appointments], "total": len(appointments)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/appointments/{citizen_id}")
async def book_appointment(
    citizen_id: str,
    body: dict[str, Any],
    sdk: Any = Depends(_get_sdk),
):
    try:
        appointment = await sdk.appointments.book_appointment(
            citizen_id=citizen_id,
            practitioner_id=body.get("practitioner_id", ""),
            facility_id=body.get("facility_id", ""),
            start_at=body.get("start_at"),
            end_at=body.get("end_at"),
            appointment_type=body.get("appointment_type", ""),
            notes=body.get("notes", ""),
        )
        return appointment.__dict__
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/medications/{citizen_id}")
async def list_medications(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        medications = sdk.medications.get_active_medications(citizen_id)
        return {"medications": [m.__dict__ for m in medications]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/lab-results/{citizen_id}")
async def list_lab_results(
    citizen_id: str,
    lab_id: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sdk: Any = Depends(_get_sdk),
):
    try:
        results = sdk.laboratory.get_results(
            citizen_id, lab_id=lab_id, status=status, skip=skip, limit=limit,
        )
        return {"results": [r.__dict__ for r in results], "total": len(results)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/radiology/{citizen_id}")
async def list_radiology_studies(
    citizen_id: str,
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sdk: Any = Depends(_get_sdk),
):
    try:
        studies = sdk.radiology.get_studies(citizen_id, status=status, skip=skip, limit=limit)
        return {"studies": [s.__dict__ for s in studies], "total": len(studies)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/family/{citizen_id}")
async def get_family(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        members = sdk.family.get_family_members(citizen_id)
        return {"members": [m.__dict__ for m in members]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/vaccinations/{citizen_id}")
async def get_vaccinations(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        records = sdk.preventive.get_vaccination_history(citizen_id)
        return {"vaccinations": [r.__dict__ for r in records]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/notifications/{citizen_id}")
async def get_notifications(
    citizen_id: str,
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    sdk: Any = Depends(_get_sdk),
):
    try:
        notifications = sdk.notifications.get_notifications(
            citizen_id, unread_only=unread_only, skip=skip, limit=limit,
        )
        return {
            "notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "title_ar": n.title_ar,
                    "message": n.message,
                    "message_ar": n.message_ar,
                    "type": n.alert_type,
                    "is_read": n.is_read,
                    "created_at": n.created_at,
                }
                for n in notifications
            ],
            "total": len(notifications),
            "unread_count": sdk.notifications.get_unread_count(citizen_id),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/certificates/{citizen_id}")
async def get_certificates(
    citizen_id: str,
    certificate_type: str | None = Query(None),
    status: str | None = Query(None),
    sdk: Any = Depends(_get_sdk),
):
    try:
        from app.citizen_platform.enums import CertificateType
        ct = CertificateType(certificate_type) if certificate_type else None
        certs = sdk.certificates.get_certificates(citizen_id, certificate_type=ct, status=status)
        return {"certificates": [c.__dict__ for c in certs]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/emergency-contacts/{citizen_id}")
async def get_emergency_contacts(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        contacts = sdk.emergency.get_contacts(citizen_id)
        return {"contacts": [c.__dict__ for c in contacts]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/screening/{citizen_id}")
async def get_screening_status(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        summary = sdk.preventive.get_screening_summary(citizen_id)
        due = [s.__dict__ for s in sdk.preventive.get_due_screenings(citizen_id)]
        overdue = [s.__dict__ for s in sdk.preventive.get_overdue_screenings(citizen_id)]
        return {**summary, "due": due, "overdue": overdue}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/consents/{citizen_id}")
async def get_consents(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        consents = sdk.privacy.get_active_consents(citizen_id)
        return {"consents": [c.__dict__ for c in consents]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/mobile-config/{citizen_id}")
async def get_mobile_config(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        return sdk.get_app_config(citizen_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/adherence/{citizen_id}")
async def get_adherence(citizen_id: str, sdk: Any = Depends(_get_sdk)):
    try:
        return sdk.medications.get_adherence_summary(citizen_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
