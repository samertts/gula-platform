from __future__ import annotations

from app.national.exceptions import NationalDomainError


class AppointmentNotFoundError(NationalDomainError):
    def __init__(self, appointment_id: str) -> None:
        self.appointment_id = appointment_id
        super().__init__(f"Appointment not found: {appointment_id}")


class ResourceNotFoundError(NationalDomainError):
    def __init__(self, resource_id: str) -> None:
        self.resource_id = resource_id
        super().__init__(f"Resource not found: {resource_id}")


class ResourceNotAvailableError(NationalDomainError):
    def __init__(self, resource_id: str, reason: str) -> None:
        self.resource_id = resource_id
        self.reason = reason
        super().__init__(f"Resource not available: {resource_id}: {reason}")


class ScheduleNotFoundError(NationalDomainError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TimeSlotNotFoundError(NationalDomainError):
    def __init__(self, slot_id: str) -> None:
        self.slot_id = slot_id
        super().__init__(f"Time slot not found: {slot_id}")


class SlotNotAvailableError(NationalDomainError):
    def __init__(self, slot_id: str) -> None:
        self.slot_id = slot_id
        super().__init__(f"Time slot not available: {slot_id}")


class ConflictDetectionError(NationalDomainError):
    def __init__(self, level: str, conflicts: list[str]) -> None:
        self.level = level
        self.conflicts = conflicts
        super().__init__(f"Conflict detected (level={level}): {'; '.join(conflicts)}")


class WaitingListNotFoundError(NationalDomainError):
    def __init__(self, entry_id: str) -> None:
        self.entry_id = entry_id
        super().__init__(f"Waiting list entry not found: {entry_id}")


class CalendarNotFoundError(NationalDomainError):
    def __init__(self, calendar_id: str) -> None:
        self.calendar_id = calendar_id
        super().__init__(f"Calendar not found: {calendar_id}")


class InvalidAppointmentStateError(NationalDomainError):
    def __init__(self, appointment_id: str, current: str, target: str) -> None:
        self.appointment_id = appointment_id
        self.current = current
        self.target = target
        super().__init__(f"Invalid appointment state transition: {appointment_id} from {current} to {target}")
