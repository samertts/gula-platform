from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PaymentMethod = Literal["cash", "electronic"]


class ClinicCreate(BaseModel):
    lab_id: int = Field(gt=0)
    province_id: int = Field(gt=0)
    administrative_unit_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=32)
    opening_time: str = Field(default="14:00", pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    closing_time: str = Field(default="18:00", pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")


class ClinicResponse(ClinicCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime


class ChronicPatientProfileCreate(BaseModel):
    patient_id: int = Field(gt=0)
    attending_doctor_id: int | None = Field(default=None, gt=0)
    conditions: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    enrolled_at: date


class TreatmentPlanCreate(BaseModel):
    patient_profile_id: int = Field(gt=0)
    medication_name: str = Field(min_length=2, max_length=255)
    medication_code: str | None = Field(default=None, max_length=128)
    quantity: int = Field(gt=0, le=100000)
    dosage: str = Field(min_length=1, max_length=255)
    instructions: str | None = Field(default=None, max_length=4000)
    valid_from: date
    valid_to: date | None = None

    @field_validator("valid_to")
    @classmethod
    def valid_range(cls, value: date | None, info):
        valid_from = info.data.get("valid_from")
        if value is not None and valid_from is not None and value < valid_from:
            raise ValueError("valid_to must not be before valid_from")
        return value


class DispensationCreate(BaseModel):
    patient_id: int = Field(gt=0)
    treatment_plan_id: int | None = Field(default=None, gt=0)
    dispense_year: int = Field(ge=2020, le=2100)
    dispense_month: int = Field(ge=1, le=12)
    medication_name: str = Field(min_length=2, max_length=255)
    quantity: int = Field(gt=0, le=100000)
    dosage: str = Field(min_length=1, max_length=255)
    blood_pressure: str | None = Field(default=None, max_length=64)
    blood_tests: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=4000)


class ServiceCreate(BaseModel):
    service_code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=64)
    price_cash: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    price_electronic: Decimal = Field(ge=0, max_digits=18, decimal_places=2)


class ServiceVisitCreate(BaseModel):
    patient_id: int | None = Field(default=None, gt=0)
    service_id: int = Field(gt=0)
    report: dict[str, Any] | None = None


class ClinicalRecordCreate(BaseModel):
    patient_id: int = Field(gt=0)
    record_type: str = Field(min_length=2, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class TicketCreate(BaseModel):
    patient_id: int | None = Field(default=None, gt=0)
    service_code: str = Field(min_length=2, max_length=64)
    payment_method: PaymentMethod


class CashCaptureCreate(BaseModel):
    cash_shift_id: str = Field(min_length=36, max_length=36)
    cashier_reference: str = Field(min_length=1, max_length=128)


class ElectronicConfirmationCreate(BaseModel):
    provider_code: str = Field(min_length=1, max_length=64)
    provider_transaction_id: str = Field(min_length=1, max_length=128)
    provider_signature: str = Field(min_length=64, max_length=128)


class WorkerCreate(BaseModel):
    user_id: int = Field(gt=0)
    worker_role: str = Field(min_length=2, max_length=64)
    starts_on: date
    ends_on: date | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clinic_id: int
    patient_id: int | None
    ticket_number: str
    service_code: str
    payment_method: str
    amount: Decimal
    payment_invoice_id: str | None
    payment_intent_id: str | None
    issued_by_id: int | None
    captured_by_id: int | None
    cash_shift_id: str | None
    payment_reference: str | None
    status: str
    created_at: datetime
    paid_at: datetime | None


class DailyFinancialReport(BaseModel):
    clinic_id: int
    report_date: date
    tickets_issued: int
    tickets_paid: int
    cash_total: Decimal
    electronic_total: Decimal
    pending_total: Decimal


class MonthlyChronicReport(BaseModel):
    clinic_id: int
    year: int
    month: int
    enrolled_patients: int
    dispensed_patients: int
    missed_patients: int
    dispensing_rate: Decimal
    most_requested_medications: list[dict[str, Any]]
