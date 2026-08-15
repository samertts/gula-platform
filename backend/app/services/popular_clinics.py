from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError, ServiceError
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.popular_clinic import (
    ChronicPatientProfile,
    MonthlyDispensation,
    PopularClinic,
    PopularClinicalRecord,
    PopularClinicTicket,
    PopularClinicWorker,
    PopularServiceCatalog,
    PopularServiceVisit,
    TreatmentPlan,
    now_utc,
)
from app.payments.service import PaymentService

PLATFORM_ROLES = {"master_admin", "ministry_admin", "province_admin"}
CASH_AMOUNT = Decimal("3250.00")
ELECTRONIC_AMOUNT = Decimal("3000.00")


def _today() -> date:
    return datetime.now(UTC).date()


class PopularClinicService:
    def __init__(self, db: Session):
        self.db = db

    def clinic_for_actor(self, clinic_id: int, actor: LabUser) -> PopularClinic:
        query = self.db.query(PopularClinic).filter(
            PopularClinic.id == clinic_id,
            PopularClinic.is_active.is_(True),
        )
        if actor.role not in PLATFORM_ROLES:
            query = query.filter(PopularClinic.lab_id == actor.lab_id)
        if actor.role == "province_admin":
            query = query.filter(PopularClinic.province_id == actor.province_id)
        clinic = query.first()
        if clinic is None:
            raise NotFoundError("Popular clinic not found or outside actor scope")
        return clinic

    def _patient(self, clinic: PopularClinic, patient_id: int) -> Patient:
        patient = (
            self.db.query(Patient)
            .filter(Patient.id == patient_id, Patient.lab_id == clinic.lab_id)
            .first()
        )
        if patient is None:
            raise NotFoundError("Patient not found in clinic institution")
        return patient

    def _profile(self, clinic: PopularClinic, profile_id: int) -> ChronicPatientProfile:
        profile = (
            self.db.query(ChronicPatientProfile)
            .filter(
                ChronicPatientProfile.id == profile_id,
                ChronicPatientProfile.clinic_id == clinic.id,
            )
            .first()
        )
        if profile is None:
            raise NotFoundError("Chronic patient profile not found")
        return profile

    def _service(self, clinic: PopularClinic, service_code: str) -> PopularServiceCatalog:
        item = (
            self.db.query(PopularServiceCatalog)
            .filter(
                PopularServiceCatalog.clinic_id == clinic.id,
                PopularServiceCatalog.service_code == service_code,
                PopularServiceCatalog.is_active.is_(True),
            )
            .first()
        )
        if item is None:
            raise NotFoundError("Clinic service not found or inactive")
        return item

    def create_clinic(self, **values) -> PopularClinic:
        clinic = PopularClinic(**values)
        self.db.add(clinic)
        self.db.flush()
        return clinic

    def list_clinics(self, actor: LabUser) -> list[PopularClinic]:
        query = self.db.query(PopularClinic).filter(PopularClinic.is_active.is_(True))
        if actor.role not in PLATFORM_ROLES:
            query = query.filter(PopularClinic.lab_id == actor.lab_id)
        if actor.role == "province_admin":
            query = query.filter(PopularClinic.province_id == actor.province_id)
        return query.order_by(PopularClinic.name).all()

    def create_profile(self, clinic: PopularClinic, actor: LabUser, **values) -> ChronicPatientProfile:
        patient = self._patient(clinic, values["patient_id"])
        existing = (
            self.db.query(ChronicPatientProfile)
            .filter(
                ChronicPatientProfile.clinic_id == clinic.id,
                ChronicPatientProfile.patient_id == patient.id,
            )
            .first()
        )
        if existing is not None:
            raise ConflictError("Patient already has an active chronic-care profile in this clinic")
        doctor_id = values.get("attending_doctor_id") or actor.id
        if self.db.query(LabUser.id).filter(LabUser.id == doctor_id, LabUser.lab_id == clinic.lab_id).first() is None:
            raise NotFoundError("Attending doctor is outside clinic institution")
        profile = ChronicPatientProfile(clinic_id=clinic.id, **values)
        profile.attending_doctor_id = doctor_id
        self.db.add(profile)
        self.db.flush()
        return profile

    def create_treatment_plan(self, clinic: PopularClinic, actor: LabUser, **values) -> TreatmentPlan:
        self._profile(clinic, values["patient_profile_id"])
        plan = TreatmentPlan(prescribed_by_id=actor.id, **values)
        self.db.add(plan)
        self.db.flush()
        return plan

    def dispense(self, clinic: PopularClinic, actor: LabUser, **values) -> MonthlyDispensation:
        patient = self._patient(clinic, values["patient_id"])
        existing = (
            self.db.query(MonthlyDispensation)
            .filter(
                MonthlyDispensation.clinic_id == clinic.id,
                MonthlyDispensation.patient_id == patient.id,
                MonthlyDispensation.dispense_year == values["dispense_year"],
                MonthlyDispensation.dispense_month == values["dispense_month"],
                MonthlyDispensation.status.notin_({"cancelled", "reversed"}),
            )
            .first()
        )
        if existing is not None:
            raise ConflictError("Patient may receive only one medication quota per month")
        item = MonthlyDispensation(
            clinic_id=clinic.id,
            approved_by_id=actor.id,
            dispensed_by_id=actor.id,
            **values,
        )
        self.db.add(item)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Monthly dispensing already exists") from exc
        return item

    def create_service(self, clinic: PopularClinic, **values) -> PopularServiceCatalog:
        item = PopularServiceCatalog(clinic_id=clinic.id, **values)
        self.db.add(item)
        self.db.flush()
        return item

    def list_services(self, clinic: PopularClinic) -> list[PopularServiceCatalog]:
        return (
            self.db.query(PopularServiceCatalog)
            .filter(PopularServiceCatalog.clinic_id == clinic.id, PopularServiceCatalog.is_active.is_(True))
            .order_by(PopularServiceCatalog.category, PopularServiceCatalog.name)
            .all()
        )

    def create_service_visit(self, clinic: PopularClinic, actor: LabUser, **values) -> PopularServiceVisit:
        if values.get("patient_id") is not None:
            self._patient(clinic, values["patient_id"])
        self._service_by_id(clinic, values["service_id"])
        visit = PopularServiceVisit(clinic_id=clinic.id, provider_id=actor.id, **values)
        self.db.add(visit)
        self.db.flush()
        return visit

    def _service_by_id(self, clinic: PopularClinic, service_id: int) -> PopularServiceCatalog:
        item = (
            self.db.query(PopularServiceCatalog)
            .filter(PopularServiceCatalog.id == service_id, PopularServiceCatalog.clinic_id == clinic.id)
            .first()
        )
        if item is None:
            raise NotFoundError("Clinic service not found")
        return item

    def create_record(self, clinic: PopularClinic, actor: LabUser, **values) -> PopularClinicalRecord:
        self._patient(clinic, values["patient_id"])
        record = PopularClinicalRecord(clinic_id=clinic.id, author_id=actor.id, **values)
        self.db.add(record)
        self.db.flush()
        return record

    def list_records(self, clinic: PopularClinic, patient_id: int) -> list[PopularClinicalRecord]:
        self._patient(clinic, patient_id)
        return (
            self.db.query(PopularClinicalRecord)
            .filter(
                PopularClinicalRecord.clinic_id == clinic.id,
                PopularClinicalRecord.patient_id == patient_id,
            )
            .order_by(PopularClinicalRecord.created_at.desc())
            .all()
        )

    def _ticket_amount(self, service: PopularServiceCatalog, method: str) -> Decimal:
        if service.service_code == "CHRONIC_DISPENSE":
            return CASH_AMOUNT if method == "cash" else ELECTRONIC_AMOUNT
        return Decimal(service.price_cash if method == "cash" else service.price_electronic)

    def issue_ticket(self, clinic: PopularClinic, actor: LabUser, **values) -> PopularClinicTicket:
        if values.get("patient_id") is not None:
            self._patient(clinic, values["patient_id"])
        service = self._service(clinic, values["service_code"])
        method = values["payment_method"]
        amount = self._ticket_amount(service, method)
        ticket_number = f"PCL-{clinic.id}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"
        ticket = PopularClinicTicket(
            clinic_id=clinic.id,
            ticket_number=ticket_number,
            amount=amount,
            issued_by_id=actor.id,
            status="paid" if amount == 0 else "payment_pending",
            **values,
        )
        self.db.add(ticket)
        self.db.flush()
        if amount > 0:
            payment_service = PaymentService(self.db)
            invoice = payment_service.create_invoice(
                institution_id=clinic.lab_id,
                patient_reference=str(ticket.patient_id) if ticket.patient_id else None,
                due_at=datetime.now(UTC) + timedelta(hours=24),
                lines=[
                    SimpleNamespace(
                        unit_amount=amount,
                        quantity=1,
                        description=f"Popular clinic ticket {ticket.ticket_number}",
                        service_reference=service.service_code,
                    )
                ],
                actor_user_id=actor.id,
            )
            method_code = "CASH" if method == "cash" else "QR"
            intent = payment_service.create_intent(
                institution_id=clinic.lab_id,
                invoice_id=invoice.id,
                amount=amount,
                method=method_code,
                idempotency_key=f"popular-clinic-ticket:{ticket.id}",
                expires_at=datetime.now(UTC) + timedelta(hours=24),
                actor_user_id=actor.id,
            )
            ticket.payment_invoice_id = invoice.id
            ticket.payment_intent_id = intent.id
        else:
            ticket.paid_at = now_utc()
        self.db.flush()
        return ticket

    def _ticket(self, clinic: PopularClinic, ticket_id: int) -> PopularClinicTicket:
        ticket = (
            self.db.query(PopularClinicTicket)
            .filter(PopularClinicTicket.id == ticket_id, PopularClinicTicket.clinic_id == clinic.id)
            .first()
        )
        if ticket is None:
            raise NotFoundError("Clinic ticket not found")
        return ticket

    def capture_cash(self, clinic: PopularClinic, actor: LabUser, ticket_id: int, cash_shift_id: str, cashier_reference: str) -> PopularClinicTicket:
        ticket = self._ticket(clinic, ticket_id)
        if ticket.status == "paid":
            return ticket
        if ticket.payment_method != "cash" or not ticket.payment_intent_id:
            raise ServiceError("This ticket is not a cash payment", status_code=409)
        payment_service = PaymentService(self.db)
        shift = payment_service._cash_shift(cash_shift_id, clinic.lab_id)
        if shift.cashier_user_id != actor.id:
            raise ServiceError("Only the cashier who owns the open shift may capture this ticket", status_code=403)
        attempt = payment_service.capture_cash(
            institution_id=clinic.lab_id,
            intent_id=ticket.payment_intent_id,
            cash_shift_id=cash_shift_id,
            cashier_reference=cashier_reference,
            actor_user_id=actor.id,
        )
        ticket.status = "paid"
        ticket.captured_by_id = actor.id
        ticket.cash_shift_id = cash_shift_id
        ticket.payment_reference = cashier_reference
        ticket.paid_at = attempt.verified_at or now_utc()
        self.db.flush()
        return ticket

    def confirm_electronic(self, clinic: PopularClinic, actor: LabUser, ticket_id: int, provider_code: str, provider_transaction_id: str) -> PopularClinicTicket:
        ticket = self._ticket(clinic, ticket_id)
        if ticket.status == "paid":
            return ticket
        if ticket.payment_method != "electronic" or not ticket.payment_intent_id:
            raise ServiceError("This ticket is not an electronic payment", status_code=409)
        if provider_code != "gula_internal":
            raise ServiceError("Only the approved internal payment provider may confirm this operation", status_code=403)
        payment_service = PaymentService(self.db)
        payment_service.capture_internal_electronic(
            institution_id=clinic.lab_id,
            intent_id=ticket.payment_intent_id,
            provider_code=provider_code,
            provider_transaction_id=provider_transaction_id,
            actor_user_id=actor.id,
        )
        ticket.status = "paid"
        ticket.captured_by_id = actor.id
        ticket.payment_reference = provider_transaction_id
        ticket.paid_at = now_utc()
        self.db.flush()
        return ticket

    def cancel_ticket(self, clinic: PopularClinic, actor: LabUser, ticket_id: int) -> PopularClinicTicket:
        ticket = self._ticket(clinic, ticket_id)
        if ticket.status == "paid":
            raise ServiceError("Paid tickets require the payment refund workflow", status_code=409)
        if ticket.status == "cancelled":
            return ticket
        ticket.status = "cancelled"
        ticket.cancelled_at = now_utc()
        self.db.flush()
        return ticket

    def patient_card(self, clinic: PopularClinic, patient_id: int) -> dict:
        patient = self._patient(clinic, patient_id)
        profile = (
            self.db.query(ChronicPatientProfile)
            .filter(
                ChronicPatientProfile.clinic_id == clinic.id,
                ChronicPatientProfile.patient_id == patient.id,
            )
            .first()
        )
        plans = []
        if profile is not None:
            plans = (
                self.db.query(TreatmentPlan)
                .filter(TreatmentPlan.patient_profile_id == profile.id, TreatmentPlan.status == "active")
                .order_by(TreatmentPlan.valid_from.desc())
                .all()
            )
        doctor = None
        if profile is not None and profile.attending_doctor_id is not None:
            doctor = self.db.query(LabUser).filter(LabUser.id == profile.attending_doctor_id).first()
        return {
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
                "birth_date": patient.birth_date,
                "phone": patient.phone,
                "health_id": patient.health_id,
            },
            "clinic": {"id": clinic.id, "name": clinic.name},
            "chronic_profile": {
                "id": profile.id if profile else None,
                "conditions": profile.conditions if profile else [],
                "notes": profile.notes if profile else None,
                "enrolled_at": profile.enrolled_at if profile else None,
                "doctor": {"id": doctor.id, "name": doctor.name} if doctor else None,
            },
            "treatment_plans": [
                {
                    "id": plan.id,
                    "medication_name": plan.medication_name,
                    "medication_code": plan.medication_code,
                    "quantity": plan.quantity,
                    "dosage": plan.dosage,
                    "instructions": plan.instructions,
                    "valid_from": plan.valid_from,
                    "valid_to": plan.valid_to,
                }
                for plan in plans
            ],
        }

    def booklet(self, clinic: PopularClinic, patient_id: int, year: int) -> dict:
        self._patient(clinic, patient_id)
        rows = (
            self.db.query(MonthlyDispensation)
            .filter(
                MonthlyDispensation.clinic_id == clinic.id,
                MonthlyDispensation.patient_id == patient_id,
                MonthlyDispensation.dispense_year == year,
            )
            .order_by(MonthlyDispensation.dispense_month)
            .all()
        )
        by_month = {
            month: {
                "month": month,
                "status": "not_received",
                "dispensation": None,
            }
            for month in range(1, 13)
        }
        for row in rows:
            by_month[row.dispense_month] = {
                "month": row.dispense_month,
                "status": row.status,
                "dispensation": {
                    "id": row.id,
                    "approved_by_id": row.approved_by_id,
                    "dispensed_by_id": row.dispensed_by_id,
                    "dispensed_at": row.dispensed_at,
                    "medication_name": row.medication_name,
                    "quantity": row.quantity,
                    "dosage": row.dosage,
                    "blood_pressure": row.blood_pressure,
                    "blood_tests": row.blood_tests,
                    "notes": row.notes,
                },
            }
        return {"clinic_id": clinic.id, "patient_id": patient_id, "year": year, "months": list(by_month.values())}

    def list_tickets(self, clinic: PopularClinic, patient_id: int | None = None) -> list[PopularClinicTicket]:
        query = self.db.query(PopularClinicTicket).filter(PopularClinicTicket.clinic_id == clinic.id)
        if patient_id is not None:
            self._patient(clinic, patient_id)
            query = query.filter(PopularClinicTicket.patient_id == patient_id)
        return query.order_by(PopularClinicTicket.created_at.desc()).limit(500).all()

    def list_patients(self, clinic: PopularClinic, search: str | None = None) -> list[Patient]:
        query = self.db.query(Patient).filter(Patient.lab_id == clinic.lab_id)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter((Patient.full_name.ilike(term)) | (Patient.phone.ilike(term)))
        return query.order_by(Patient.full_name).limit(200).all()

    def daily_report(self, clinic: PopularClinic, report_date: date) -> dict:
        start = datetime.combine(report_date, time.min, tzinfo=UTC)
        end = start + timedelta(days=1)
        tickets = (
            self.db.query(PopularClinicTicket)
            .filter(
                PopularClinicTicket.clinic_id == clinic.id,
                PopularClinicTicket.created_at >= start,
                PopularClinicTicket.created_at < end,
            )
            .all()
        )
        paid = [item for item in tickets if item.status == "paid"]
        cash = sum((Decimal(item.amount) for item in paid if item.payment_method == "cash"), Decimal("0.00"))
        electronic = sum((Decimal(item.amount) for item in paid if item.payment_method == "electronic"), Decimal("0.00"))
        pending = sum((Decimal(item.amount) for item in tickets if item.status == "payment_pending"), Decimal("0.00"))
        return {
            "clinic_id": clinic.id,
            "report_date": report_date,
            "tickets_issued": len(tickets),
            "tickets_paid": len(paid),
            "cash_total": cash,
            "electronic_total": electronic,
            "pending_total": pending,
        }

    def monthly_chronic_report(self, clinic: PopularClinic, year: int, month: int) -> dict:
        enrolled = (
            self.db.query(ChronicPatientProfile)
            .filter(ChronicPatientProfile.clinic_id == clinic.id, ChronicPatientProfile.status == "active")
            .count()
        )
        dispensed_query = (
            self.db.query(MonthlyDispensation)
            .filter(
                MonthlyDispensation.clinic_id == clinic.id,
                MonthlyDispensation.dispense_year == year,
                MonthlyDispensation.dispense_month == month,
                MonthlyDispensation.status == "dispensed",
            )
        )
        dispensed = dispensed_query.count()
        missed = max(enrolled - dispensed, 0)
        rate = (Decimal(dispensed) / Decimal(enrolled) * Decimal("100")) if enrolled else Decimal("0")
        medication_rows = (
            self.db.query(MonthlyDispensation.medication_name, func.sum(MonthlyDispensation.quantity))
            .filter(
                MonthlyDispensation.clinic_id == clinic.id,
                MonthlyDispensation.dispense_year == year,
                MonthlyDispensation.dispense_month == month,
                MonthlyDispensation.status == "dispensed",
            )
            .group_by(MonthlyDispensation.medication_name)
            .order_by(func.sum(MonthlyDispensation.quantity).desc())
            .limit(20)
            .all()
        )
        return {
            "clinic_id": clinic.id,
            "year": year,
            "month": month,
            "enrolled_patients": enrolled,
            "dispensed_patients": dispensed,
            "missed_patients": missed,
            "dispensing_rate": rate.quantize(Decimal("0.01")),
            "most_requested_medications": [
                {"medication_name": name, "quantity": int(quantity or 0)}
                for name, quantity in medication_rows
            ],
        }

    def add_worker(self, clinic: PopularClinic, **values) -> PopularClinicWorker:
        worker = PopularClinicWorker(clinic_id=clinic.id, active=True, **values)
        self.db.add(worker)
        self.db.flush()
        return worker

    def list_workers(self, clinic: PopularClinic) -> list[PopularClinicWorker]:
        return (
            self.db.query(PopularClinicWorker)
            .filter(PopularClinicWorker.clinic_id == clinic.id, PopularClinicWorker.active.is_(True))
            .order_by(PopularClinicWorker.worker_role, PopularClinicWorker.user_id)
            .all()
        )
