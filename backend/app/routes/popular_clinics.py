from __future__ import annotations

import hashlib
import hmac
import os
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.popular_clinic import PopularClinicTicket
from app.schemas.popular_clinic import (
    CashCaptureCreate,
    ChronicPatientProfileCreate,
    ClinicalRecordCreate,
    ClinicCreate,
    ClinicResponse,
    DispensationCreate,
    ElectronicConfirmationCreate,
    MonthlyChronicReport,
    ServiceCreate,
    ServiceVisitCreate,
    TicketCreate,
    TicketResponse,
    TreatmentPlanCreate,
    WorkerCreate,
)
from app.security.dependencies import require_institutional_permission
from app.services.popular_clinics import PopularClinicService

router = APIRouter(prefix="/popular-clinics", tags=["Government Popular Clinics"])
DbSession = Annotated[Session, Depends(get_db)]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _service(db: Session) -> PopularClinicService:
    return PopularClinicService(db)


def _ticket_response(ticket: PopularClinicTicket) -> TicketResponse:
    return TicketResponse.model_validate(ticket)


def _clinic(db: Session, clinic_id: int, actor):
    return _service(db).clinic_for_actor(clinic_id, actor)


def _verify_internal_payment_signature(ticket: PopularClinicTicket, payload: ElectronicConfirmationCreate) -> None:
    from fastapi import HTTPException

    if payload.provider_code != "gula_internal":
        raise HTTPException(status_code=403, detail="Only the approved internal payment provider is accepted")
    signing_key = os.getenv("INTERNAL_PAYMENT_SIGNING_KEY")
    if not signing_key:
        raise HTTPException(status_code=503, detail="Internal payment verification is not configured")
    message = f"{ticket.id}|{ticket.amount}|{payload.provider_transaction_id}".encode()
    expected = hmac.new(signing_key.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.provider_signature):
        raise HTTPException(status_code=403, detail="Invalid internal payment signature")


@router.get("", response_model=list[ClinicResponse])
def list_clinics(
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:read")),
):
    return _service(db).list_clinics(current_user)


@router.post("", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
def create_clinic(
    payload: ClinicCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:manage")),
):
    if current_user.role not in {"master_admin", "ministry_admin", "province_admin"} and payload.lab_id != current_user.lab_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Clinic must belong to the current institution")
    clinic = _service(db).create_clinic(**payload.model_dump())
    _commit(db)
    return clinic


@router.get("/{clinic_id}/summary")
def clinic_summary(
    clinic_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    service = _service(db)
    today = date.today()
    return {
        "clinic": ClinicResponse.model_validate(clinic).model_dump(),
        "active_workers": len(service.list_workers(clinic)),
        "services": len(service.list_services(clinic)),
        "monthly_chronic_report": service.monthly_chronic_report(clinic, today.year, today.month),
    }


@router.get("/{clinic_id}/patients")
def list_patients(
    clinic_id: int,
    db: DbSession,
    search: str | None = Query(default=None, max_length=100),
    current_user=Depends(require_institutional_permission("popular_clinics:patient:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return [
        {
            "id": patient.id,
            "full_name": patient.full_name,
            "birth_date": patient.birth_date,
            "phone": patient.phone,
            "health_id": patient.health_id,
        }
        for patient in _service(db).list_patients(clinic, search)
    ]


@router.post("/{clinic_id}/patients/profile", status_code=status.HTTP_201_CREATED)
def create_chronic_profile(
    clinic_id: int,
    payload: ChronicPatientProfileCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:clinical:write")),
):
    clinic = _clinic(db, clinic_id, current_user)
    profile = _service(db).create_profile(clinic, current_user, **payload.model_dump())
    _commit(db)
    return profile


@router.get("/{clinic_id}/patients/{patient_id}/card")
def patient_card(
    clinic_id: int,
    patient_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:patient:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _service(db).patient_card(clinic, patient_id)


@router.get("/{clinic_id}/patients/{patient_id}/booklet")
def patient_booklet(
    clinic_id: int,
    patient_id: int,
    db: DbSession,
    year: int | None = Query(default=None, ge=2020, le=2100),
    current_user=Depends(require_institutional_permission("popular_clinics:patient:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _service(db).booklet(clinic, patient_id, year or date.today().year)


@router.post("/{clinic_id}/patients/{patient_id}/treatment-plans", status_code=status.HTTP_201_CREATED)
def create_treatment_plan(
    clinic_id: int,
    patient_id: int,
    payload: TreatmentPlanCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:prescription:write")),
):
    clinic = _clinic(db, clinic_id, current_user)
    profile = _service(db)._profile(clinic, payload.patient_profile_id)
    if profile.patient_id != patient_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Treatment plan profile does not belong to patient")
    plan = _service(db).create_treatment_plan(clinic, current_user, **payload.model_dump())
    _commit(db)
    return plan


@router.post("/{clinic_id}/patients/{patient_id}/monthly-dispensations", status_code=status.HTTP_201_CREATED)
def create_monthly_dispensation(
    clinic_id: int,
    patient_id: int,
    payload: DispensationCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:dispense:record")),
):
    if payload.patient_id != patient_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Payload patient does not match path patient")
    clinic = _clinic(db, clinic_id, current_user)
    item = _service(db).dispense(clinic, current_user, **payload.model_dump())
    _commit(db)
    return item


@router.get("/{clinic_id}/services")
def list_services(
    clinic_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _service(db).list_services(clinic)


@router.post("/{clinic_id}/services", response_model=ServiceCreate, status_code=status.HTTP_201_CREATED)
def create_service(
    clinic_id: int,
    payload: ServiceCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:manage")),
):
    clinic = _clinic(db, clinic_id, current_user)
    item = _service(db).create_service(clinic, **payload.model_dump())
    _commit(db)
    return item


@router.post("/{clinic_id}/service-visits", status_code=status.HTTP_201_CREATED)
def create_service_visit(
    clinic_id: int,
    payload: ServiceVisitCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:clinical:write")),
):
    clinic = _clinic(db, clinic_id, current_user)
    visit = _service(db).create_service_visit(clinic, current_user, **payload.model_dump())
    _commit(db)
    return visit


@router.get("/{clinic_id}/workforce")
def list_workforce(
    clinic_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _service(db).list_workers(clinic)


@router.post("/{clinic_id}/workforce", status_code=status.HTTP_201_CREATED)
def add_worker(
    clinic_id: int,
    payload: WorkerCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:workforce:manage")),
):
    clinic = _clinic(db, clinic_id, current_user)
    worker = _service(db).add_worker(clinic, **payload.model_dump())
    _commit(db)
    return worker


@router.get("/{clinic_id}/patients/{patient_id}/records")
def list_records(
    clinic_id: int,
    patient_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:patient:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _service(db).list_records(clinic, patient_id)


@router.post("/{clinic_id}/patients/{patient_id}/records", status_code=status.HTTP_201_CREATED)
def create_record(
    clinic_id: int,
    patient_id: int,
    payload: ClinicalRecordCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:clinical:write")),
):
    if payload.patient_id != patient_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Payload patient does not match path patient")
    clinic = _clinic(db, clinic_id, current_user)
    record = _service(db).create_record(clinic, current_user, **payload.model_dump())
    _commit(db)
    return record


@router.get("/{clinic_id}/tickets", response_model=list[TicketResponse])
def list_tickets(
    clinic_id: int,
    db: DbSession,
    patient_id: int | None = Query(default=None, gt=0),
    current_user=Depends(require_institutional_permission("popular_clinics:ticket:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return [_ticket_response(item) for item in _service(db).list_tickets(clinic, patient_id)]


@router.post("/{clinic_id}/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def issue_ticket(
    clinic_id: int,
    payload: TicketCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:ticket:issue")),
):
    clinic = _clinic(db, clinic_id, current_user)
    ticket = _service(db).issue_ticket(clinic, current_user, **payload.model_dump())
    _commit(db)
    return _ticket_response(ticket)


@router.post("/{clinic_id}/tickets/{ticket_id}/cancel", response_model=TicketResponse)
def cancel_ticket(
    clinic_id: int,
    ticket_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:ticket:cancel")),
):
    clinic = _clinic(db, clinic_id, current_user)
    ticket = _service(db).cancel_ticket(clinic, current_user, ticket_id)
    _commit(db)
    return _ticket_response(ticket)


@router.get("/{clinic_id}/tickets/{ticket_id}/payment-status", response_model=TicketResponse)
def ticket_payment_status(
    clinic_id: int,
    ticket_id: int,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:ticket:read")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _ticket_response(_service(db)._ticket(clinic, ticket_id))


@router.post("/{clinic_id}/tickets/{ticket_id}/cash-capture", response_model=TicketResponse)
def capture_ticket_cash(
    clinic_id: int,
    ticket_id: int,
    payload: CashCaptureCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:payment:capture")),
):
    clinic = _clinic(db, clinic_id, current_user)
    ticket = _service(db).capture_cash(clinic, current_user, ticket_id, payload.cash_shift_id, payload.cashier_reference)
    _commit(db)
    return _ticket_response(ticket)


@router.post("/{clinic_id}/tickets/{ticket_id}/electronic-confirm", response_model=TicketResponse)
def confirm_ticket_electronic(
    clinic_id: int,
    ticket_id: int,
    payload: ElectronicConfirmationCreate,
    db: DbSession,
    current_user=Depends(require_institutional_permission("popular_clinics:payment:confirm")),
):
    clinic = _clinic(db, clinic_id, current_user)
    ticket = _service(db)._ticket(clinic, ticket_id)
    _verify_internal_payment_signature(ticket, payload)
    ticket = _service(db).confirm_electronic(
        clinic,
        current_user,
        ticket_id,
        payload.provider_code,
        payload.provider_transaction_id,
    )
    _commit(db)
    return _ticket_response(ticket)


@router.get("/{clinic_id}/financial-reports/daily")
def daily_financial_report(
    clinic_id: int,
    db: DbSession,
    report_date: date | None = Query(default=None),
    current_user=Depends(require_institutional_permission("popular_clinics:report:daily")),
):
    clinic = _clinic(db, clinic_id, current_user)
    return _service(db).daily_report(clinic, report_date or date.today())


@router.get("/{clinic_id}/chronic-care-reports/monthly", response_model=MonthlyChronicReport)
def monthly_chronic_report(
    clinic_id: int,
    db: DbSession,
    year: int | None = Query(default=None, ge=2020, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    current_user=Depends(require_institutional_permission("popular_clinics:report:monthly")),
):
    clinic = _clinic(db, clinic_id, current_user)
    today = date.today()
    return _service(db).monthly_chronic_report(clinic, year or today.year, month or today.month)


@router.get("/chronic-care-reports/monthly/comparison")
def monthly_chronic_report_comparison(
    db: DbSession,
    year: int | None = Query(default=None, ge=2020, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    current_user=Depends(require_institutional_permission("popular_clinics:report:monthly")),
):
    today = date.today()
    target_year, target_month = year or today.year, month or today.month
    service = _service(db)
    clinics = service.list_clinics(current_user)
    return [service.monthly_chronic_report(clinic, target_year, target_month) for clinic in clinics]
