from __future__ import annotations

from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class AppointmentCreated(NationalDomainEvent):
    event_type: str = "national.scheduling.appointment.created"
    aggregate_type: str = "Appointment"
    appointment_id: str = ""
    patient_id: str = ""
    practitioner_id: str = ""


@dataclass
class AppointmentRescheduled(NationalDomainEvent):
    event_type: str = "national.scheduling.appointment.rescheduled"
    aggregate_type: str = "Appointment"
    appointment_id: str = ""
    previous_start: str = ""
    new_start: str = ""


@dataclass
class AppointmentCancelled(NationalDomainEvent):
    event_type: str = "national.scheduling.appointment.cancelled"
    aggregate_type: str = "Appointment"
    appointment_id: str = ""
    reason: str = ""


@dataclass
class AppointmentCompleted(NationalDomainEvent):
    event_type: str = "national.scheduling.appointment.completed"
    aggregate_type: str = "Appointment"
    appointment_id: str = ""


@dataclass
class AppointmentNoShow(NationalDomainEvent):
    event_type: str = "national.scheduling.appointment.no_show"
    aggregate_type: str = "Appointment"
    appointment_id: str = ""
    patient_id: str = ""


@dataclass
class ResourceBooked(NationalDomainEvent):
    event_type: str = "national.scheduling.resource.booked"
    aggregate_type: str = "Resource"
    resource_id: str = ""
    appointment_id: str = ""


@dataclass
class ResourceFreed(NationalDomainEvent):
    event_type: str = "national.scheduling.resource.freed"
    aggregate_type: str = "Resource"
    resource_id: str = ""
    appointment_id: str = ""


@dataclass
class WaitingListAdded(NationalDomainEvent):
    event_type: str = "national.scheduling.waiting_list.added"
    aggregate_type: str = "WaitingList"
    waiting_list_id: str = ""
    patient_id: str = ""
    resource_id: str = ""


@dataclass
class WaitingListFulfilled(NationalDomainEvent):
    event_type: str = "national.scheduling.waiting_list.fulfilled"
    aggregate_type: str = "WaitingList"
    waiting_list_id: str = ""
    patient_id: str = ""
    appointment_id: str = ""
