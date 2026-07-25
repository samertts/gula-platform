from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.national.scheduling_platform.domain.entities import (
    Appointment,
    AppointmentReminder,
    Calendar,
    ConflictResult,
    Resource,
    Schedule,
    TimeSlot,
    WaitingList,
)
from app.national.scheduling_platform.domain.enums import (
    AppointmentStatus,
    ConflictLevel,
    RecurrencePattern,
    ResourceType,
    SlotStatus,
)
from app.national.scheduling_platform.domain.events import (
    AppointmentCancelled,
    AppointmentCompleted,
    AppointmentCreated,
    AppointmentNoShow,
    AppointmentRescheduled,
    ResourceBooked,
    ResourceFreed,
    WaitingListAdded,
    WaitingListFulfilled,
)
from app.national.scheduling_platform.domain.repository import (
    AppointmentReminderRepository,
    AppointmentRepository,
    CalendarRepository,
    ResourceRepository,
    ScheduleRepository,
    TimeSlotRepository,
    WaitingListRepository,
)
from app.national.scheduling_platform.exceptions import (
    AppointmentNotFoundError,
    CalendarNotFoundError,
    ConflictDetectionError,
    ResourceNotFoundError,
    ScheduleNotFoundError,
    WaitingListNotFoundError,
)

logger = logging.getLogger("gula.national.scheduling_platform")


_ALLOWED_APPOINTMENT_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.PROPOSED: {
        AppointmentStatus.PENDING,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.ENTERED_IN_ERROR,
    },
    AppointmentStatus.PENDING: {
        AppointmentStatus.BOOKED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.ENTERED_IN_ERROR,
    },
    AppointmentStatus.BOOKED: {
        AppointmentStatus.ARRIVED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.ENTERED_IN_ERROR,
    },
    AppointmentStatus.ARRIVED: {
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.IN_PROGRESS: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
    AppointmentStatus.ENTERED_IN_ERROR: set(),
}


class SchedulingPlatformService:
    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        resource_repository: ResourceRepository,
        schedule_repository: ScheduleRepository,
        time_slot_repository: TimeSlotRepository,
        waiting_list_repository: WaitingListRepository,
        calendar_repository: CalendarRepository,
        reminder_repository: AppointmentReminderRepository,
        event_bus: EventBus,
    ) -> None:
        self.appointment_repository = appointment_repository
        self.resource_repository = resource_repository
        self.schedule_repository = schedule_repository
        self.time_slot_repository = time_slot_repository
        self.waiting_list_repository = waiting_list_repository
        self.calendar_repository = calendar_repository
        self.reminder_repository = reminder_repository
        self.event_bus = event_bus

    async def create_appointment(
        self,
        patient_id: str,
        practitioner_id: str = "",
        facility_id: str = "",
        resource_id: str = "",
        title: str = "",
        description: str = "",
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        appointment_type: str = "",
        recurrence_pattern: RecurrencePattern = RecurrencePattern.NONE,
        recurrence_end: datetime | None = None,
        reminder_enabled: bool = True,
        reminder_minutes_before: int = 60,
        notes: str = "",
        metadata: dict[str, Any] | None = None,
        created_by: str = "",
    ) -> Appointment:
        conflict = await self.detect_conflicts(
            start_at=start_at,
            end_at=end_at,
            resource_id=resource_id,
            practitioner_id=practitioner_id,
        )
        if conflict.level == ConflictLevel.HARD:
            raise ConflictDetectionError(
                conflict.level.value,
                [c["type"] for c in conflict.conflicts],
            )

        appointment = Appointment(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            practitioner_id=practitioner_id,
            facility_id=facility_id,
            resource_id=resource_id,
            title=title or f"Appointment for patient {patient_id}",
            description=description,
            start_at=start_at,
            end_at=end_at,
            status=AppointmentStatus.PROPOSED,
            appointment_type=appointment_type,
            recurrence_pattern=recurrence_pattern,
            recurrence_end=recurrence_end,
            reminder_enabled=reminder_enabled,
            reminder_minutes_before=reminder_minutes_before,
            notes=notes,
            metadata=metadata or {},
            created_by=created_by,
        )

        saved = await self.appointment_repository.save(appointment)

        if resource_id:
            self._publish_event(
                ResourceBooked(
                    resource_id=resource_id,
                    appointment_id=saved.id,
                    aggregate_id=resource_id,
                    payload={
                        "appointment_id": saved.id,
                        "start_at": start_at.isoformat() if start_at else "",
                    },
                ),
            )

        if reminder_enabled and start_at:
            reminder_time = start_at - timedelta(minutes=reminder_minutes_before)
            if reminder_time > datetime.now(UTC):
                reminder = AppointmentReminder(
                    id=str(uuid.uuid4()),
                    appointment_id=saved.id,
                    channel="email",
                    status="scheduled",
                )
                await self.reminder_repository.save(reminder)

        self._publish_event(
            AppointmentCreated(
                appointment_id=saved.id,
                patient_id=patient_id,
                practitioner_id=practitioner_id,
                aggregate_id=saved.id,
                payload={
                    "patient_id": patient_id,
                    "practitioner_id": practitioner_id,
                    "start_at": start_at.isoformat() if start_at else None,
                    "end_at": end_at.isoformat() if end_at else None,
                    "resource_id": resource_id,
                },
            ),
        )

        return saved

    async def get_appointment(self, appointment_id: str) -> Appointment:
        appointment = await self.appointment_repository.get(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(appointment_id)
        return appointment

    async def list_appointments(
        self,
        patient_id: str | None = None,
        practitioner_id: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if practitioner_id:
            filters["practitioner_id"] = practitioner_id
        if status:
            filters["status"] = AppointmentStatus(status)
        return await self.appointment_repository.list(skip=skip, limit=limit, **filters)

    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_start: datetime,
        new_end: datetime,
        reason: str = "",
    ) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        if not appointment.is_cancellable:
            raise ConflictDetectionError(
                "reschedule",
                [
                    f"Appointment {appointment_id} is in status {appointment.status.value} and cannot be rescheduled",
                ],
            )

        conflict = await self.detect_conflicts(
            start_at=new_start,
            end_at=new_end,
            resource_id=appointment.resource_id,
            practitioner_id=appointment.practitioner_id,
            exclude_appointment_id=appointment_id,
        )
        if conflict.level == ConflictLevel.HARD:
            raise ConflictDetectionError(
                conflict.level.value,
                [c["type"] for c in conflict.conflicts],
            )

        previous_start = appointment.start_at
        appointment.start_at = new_start
        appointment.end_at = new_end
        appointment.version += 1
        saved = await self.appointment_repository.save(appointment)

        self._publish_event(
            AppointmentRescheduled(
                appointment_id=appointment_id,
                previous_start=previous_start.isoformat() if previous_start else "",
                new_start=new_start.isoformat(),
                aggregate_id=appointment_id,
                payload={
                    "reason": reason,
                    "previous_start": str(previous_start),
                    "new_start": str(new_start),
                },
            ),
        )

        return saved

    async def cancel_appointment(self, appointment_id: str, reason: str = "") -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        if not appointment.is_cancellable:
            raise ConflictDetectionError(
                "cancel",
                [
                    f"Appointment {appointment_id} is in status {appointment.status.value} and cannot be cancelled",
                ],
            )

        old_status = appointment.status
        appointment.status = AppointmentStatus.CANCELLED
        appointment.version += 1
        saved = await self.appointment_repository.save(appointment)

        if appointment.resource_id:
            self._publish_event(
                ResourceFreed(
                    resource_id=appointment.resource_id,
                    appointment_id=appointment_id,
                    aggregate_id=appointment.resource_id,
                    payload={"appointment_id": appointment_id},
                ),
            )

        self._publish_event(
            AppointmentCancelled(
                appointment_id=appointment_id,
                reason=reason,
                aggregate_id=appointment_id,
                payload={"reason": reason, "previous_status": old_status.value},
            ),
        )

        return saved

    async def complete_appointment(self, appointment_id: str) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        if appointment.status != AppointmentStatus.IN_PROGRESS:
            raise ConflictDetectionError(
                "complete",
                [f"Appointment {appointment_id} must be IN_PROGRESS to complete"],
            )
        appointment.status = AppointmentStatus.COMPLETED
        appointment.version += 1
        saved = await self.appointment_repository.save(appointment)

        self._publish_event(
            AppointmentCompleted(
                appointment_id=appointment_id,
                aggregate_id=appointment_id,
                payload={},
            ),
        )

        return saved

    async def mark_no_show(self, appointment_id: str) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        if appointment.status not in (AppointmentStatus.BOOKED, AppointmentStatus.ARRIVED):
            raise ConflictDetectionError(
                "no_show",
                [
                    f"Appointment {appointment_id} cannot be marked no-show from {appointment.status.value}",
                ],
            )
        appointment.status = AppointmentStatus.NO_SHOW
        appointment.version += 1
        saved = await self.appointment_repository.save(appointment)

        if appointment.resource_id:
            self._publish_event(
                ResourceFreed(
                    resource_id=appointment.resource_id,
                    appointment_id=appointment_id,
                    aggregate_id=appointment.resource_id,
                    payload={"appointment_id": appointment_id},
                ),
            )

        self._publish_event(
            AppointmentNoShow(
                appointment_id=appointment_id,
                patient_id=appointment.patient_id,
                aggregate_id=appointment_id,
                payload={"patient_id": appointment.patient_id},
            ),
        )

        return saved

    async def update_appointment_status(
        self,
        appointment_id: str,
        new_status: AppointmentStatus,
    ) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        allowed = _ALLOWED_APPOINTMENT_TRANSITIONS.get(appointment.status, set())
        if new_status not in allowed:
            raise ConflictDetectionError(
                "status_transition",
                [f"Cannot transition from {appointment.status.value} to {new_status.value}"],
            )
        appointment.status = new_status
        appointment.version += 1
        return await self.appointment_repository.save(appointment)

    async def check_availability(
        self,
        resource_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, Any]:
        resource = await self.resource_repository.get(resource_id)
        if not resource:
            raise ResourceNotFoundError(resource_id)

        overlapping = await self.appointment_repository.find_overlapping(
            start_at=start_at,
            end_at=end_at,
            resource_id=resource_id,
        )

        slots = await self.time_slot_repository.find_available(
            resource_id=resource_id,
            date_from=start_at,
            date_to=end_at,
        )

        return {
            "resource_id": resource_id,
            "resource_name": resource.name,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "available": len(overlapping) == 0 and len(slots) > 0,
            "overlapping_appointments": len(overlapping),
            "available_slots": len(slots),
        }

    async def find_available_slots(
        self,
        resource_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> list[dict[str, Any]]:
        slots = await self.time_slot_repository.find_available(
            resource_id=resource_id,
            date_from=date_from,
            date_to=date_to,
        )
        return [
            {
                "id": s.id,
                "schedule_id": s.schedule_id,
                "start_at": s.start_at.isoformat() if s.start_at else None,
                "end_at": s.end_at.isoformat() if s.end_at else None,
                "status": s.status.value,
            }
            for s in slots
        ]

    async def detect_conflicts(
        self,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        resource_id: str | None = None,
        practitioner_id: str | None = None,
        exclude_appointment_id: str | None = None,
    ) -> ConflictResult:
        result = ConflictResult()

        if not start_at or not end_at:
            return result

        if resource_id:
            overlapping = await self.appointment_repository.find_overlapping(
                start_at=start_at,
                end_at=end_at,
                resource_id=resource_id,
                exclude_id=exclude_appointment_id,
            )
            if overlapping:
                for apt in overlapping:
                    result.add_conflict(
                        "resource_double_booked",
                        {
                            "resource_id": resource_id,
                            "conflicting_appointment_id": apt.id,
                            "conflicting_start": apt.start_at.isoformat() if apt.start_at else "",
                            "conflicting_end": apt.end_at.isoformat() if apt.end_at else "",
                        },
                    )

        if practitioner_id:
            overlapping = await self.appointment_repository.find_overlapping(
                start_at=start_at,
                end_at=end_at,
                practitioner_id=practitioner_id,
                exclude_id=exclude_appointment_id,
            )
            if overlapping:
                for apt in overlapping:
                    result.add_conflict(
                        "personnel_double_booked",
                        {
                            "practitioner_id": practitioner_id,
                            "conflicting_appointment_id": apt.id,
                        },
                    )

        return result

    async def create_resource(
        self,
        name: str,
        type: ResourceType = ResourceType.ROOM,
        description: str = "",
        capacity: int = 1,
        location: str = "",
        calendar_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        resource = Resource(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            description=description,
            capacity=capacity,
            location=location,
            calendar_id=calendar_id,
            metadata=metadata or {},
        )
        return await self.resource_repository.save(resource)

    async def update_resource(
        self,
        resource_id: str,
        updates: dict[str, Any],
    ) -> Resource:
        resource = await self.resource_repository.get(resource_id)
        if not resource:
            raise ResourceNotFoundError(resource_id)

        for key, value in updates.items():
            if hasattr(resource, key) and key not in ("id", "created_at"):
                if key == "type" and isinstance(value, str):
                    value = ResourceType(value)
                setattr(resource, key, value)

        resource.updated_at = datetime.now(UTC)
        return await self.resource_repository.save(resource)

    async def deactivate_resource(self, resource_id: str) -> Resource:
        resource = await self.resource_repository.get(resource_id)
        if not resource:
            raise ResourceNotFoundError(resource_id)
        resource.is_active = False
        resource.updated_at = datetime.now(UTC)
        return await self.resource_repository.save(resource)

    async def get_resource(self, resource_id: str) -> Resource:
        resource = await self.resource_repository.get(resource_id)
        if not resource:
            raise ResourceNotFoundError(resource_id)
        return resource

    async def list_resources(
        self,
        type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Resource]:
        filters: dict[str, Any] = {}
        if type:
            filters["type"] = ResourceType(type)
        return await self.resource_repository.list(skip=skip, limit=limit, **filters)

    async def set_availability(
        self,
        resource_id: str,
        date: date,
        start_time: time,
        end_time: time,
        slot_duration_minutes: int = 30,
        is_available: bool = True,
    ) -> Schedule:
        existing = await self.schedule_repository.find_by_date(resource_id, date)
        if existing:
            existing.start_time = start_time
            existing.end_time = end_time
            existing.is_available = is_available
            existing.slot_duration_minutes = slot_duration_minutes
            schedule = await self.schedule_repository.save(existing)
        else:
            schedule = Schedule(
                id=str(uuid.uuid4()),
                resource_id=resource_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available,
                slot_duration_minutes=slot_duration_minutes,
            )
            schedule = await self.schedule_repository.save(schedule)

        await self._generate_time_slots(schedule)
        return schedule

    async def block_time(
        self,
        resource_id: str,
        start_at: datetime,
        end_at: datetime,
        purpose: str = "",
    ) -> list[TimeSlot]:
        schedule = await self.schedule_repository.find_by_date(resource_id, start_at.date())
        if not schedule:
            raise ScheduleNotFoundError(
                f"No schedule found for resource {resource_id} on {start_at.date()}",
            )
        slots = await self.time_slot_repository.find_by_schedule(schedule.id)
        blocked: list[TimeSlot] = []
        for slot in slots:
            if slot.start_at and slot.end_at:
                if slot.start_at >= start_at and slot.end_at <= end_at and slot.is_available:
                    slot.status = SlotStatus.BLOCKED
                    slot.purpose = purpose
                    blocked.append(await self.time_slot_repository.save(slot))
        return blocked

    async def get_schedule(self, resource_id: str, date: date) -> dict[str, Any]:
        schedule = await self.schedule_repository.find_by_date(resource_id, date)
        if not schedule:
            raise ScheduleNotFoundError(f"No schedule for resource {resource_id} on {date}")
        slots = await self.time_slot_repository.find_by_schedule(schedule.id)
        return {
            "id": schedule.id,
            "resource_id": schedule.resource_id,
            "date": schedule.date.isoformat() if schedule.date else None,
            "start_time": schedule.start_time.isoformat() if schedule.start_time else None,
            "end_time": schedule.end_time.isoformat() if schedule.end_time else None,
            "is_available": schedule.is_available,
            "slot_duration_minutes": schedule.slot_duration_minutes,
            "slots": [
                {
                    "id": s.id,
                    "start_at": s.start_at.isoformat() if s.start_at else None,
                    "end_at": s.end_at.isoformat() if s.end_at else None,
                    "status": s.status.value,
                    "booked_by": s.booked_by,
                    "purpose": s.purpose,
                }
                for s in slots
            ],
        }

    async def add_to_waiting_list(
        self,
        patient_id: str,
        resource_id: str = "",
        preferred_date_from: date | None = None,
        preferred_date_to: date | None = None,
        preferred_time_from: time | None = None,
        preferred_time_to: time | None = None,
        priority: int = 0,
        notes: str = "",
    ) -> WaitingList:
        entry = WaitingList(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            resource_id=resource_id,
            preferred_date_from=preferred_date_from,
            preferred_date_to=preferred_date_to,
            preferred_time_from=preferred_time_from,
            preferred_time_to=preferred_time_to,
            priority=priority,
            notes=notes,
        )
        saved = await self.waiting_list_repository.save(entry)

        self._publish_event(
            WaitingListAdded(
                waiting_list_id=saved.id,
                patient_id=patient_id,
                resource_id=resource_id,
                aggregate_id=saved.id,
                payload={
                    "patient_id": patient_id,
                    "resource_id": resource_id,
                    "priority": priority,
                },
            ),
        )

        return saved

    async def fulfill_waiting_list(
        self,
        entry_id: str,
        appointment_id: str,
    ) -> WaitingList:
        entry = await self.waiting_list_repository.get(entry_id)
        if not entry:
            raise WaitingListNotFoundError(entry_id)
        entry.status = "fulfilled"

        self._publish_event(
            WaitingListFulfilled(
                waiting_list_id=entry_id,
                patient_id=entry.patient_id,
                appointment_id=appointment_id,
                aggregate_id=entry_id,
                payload={"appointment_id": appointment_id},
            ),
        )

        return await self.waiting_list_repository.save(entry)

    async def remove_from_waiting_list(self, entry_id: str) -> None:
        entry = await self.waiting_list_repository.get(entry_id)
        if not entry:
            raise WaitingListNotFoundError(entry_id)
        await self.waiting_list_repository.delete(entry_id)

    async def list_waiting_list(
        self,
        resource_id: str | None = None,
        status: str = "active",
        skip: int = 0,
        limit: int = 100,
    ) -> list[WaitingList]:
        filters: dict[str, Any] = {"status": status}
        if resource_id:
            filters["resource_id"] = resource_id
        return await self.waiting_list_repository.list(skip=skip, limit=limit, **filters)

    async def send_reminders(self) -> list[AppointmentReminder]:
        now = datetime.now(UTC)
        due = await self.reminder_repository.find_due_reminders(before=now)
        sent: list[AppointmentReminder] = []
        for reminder in due:
            try:
                reminder.status = "sent"
                reminder.sent_at = now
                sent.append(await self.reminder_repository.save(reminder))
            except Exception as exc:
                reminder.status = "failed"
                reminder.error = str(exc)
                await self.reminder_repository.save(reminder)
                logger.error("Failed to send reminder %s: %s", reminder.id, exc)
        return sent

    async def create_calendar(
        self,
        name: str,
        description: str = "",
        timezone: str = "UTC",
        business_hours: dict[str, Any] | None = None,
        holidays: list[dict[str, Any]] | None = None,
    ) -> Calendar:
        calendar = Calendar(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            timezone=timezone,
            business_hours=business_hours or {},
            holidays=holidays or [],
        )
        return await self.calendar_repository.save(calendar)

    async def get_calendar(self, calendar_id: str) -> Calendar:
        calendar = await self.calendar_repository.get(calendar_id)
        if not calendar:
            raise CalendarNotFoundError(calendar_id)
        return calendar

    async def list_calendars(self, skip: int = 0, limit: int = 100) -> list[Calendar]:
        return await self.calendar_repository.list(skip=skip, limit=limit)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        date.today()
        stats: dict[str, Any] = {
            "by_status": {},
            "total": 0,
            "today": 0,
            "upcoming": 0,
        }
        for status in AppointmentStatus:
            count = await self.appointment_repository.count_by_status(status)
            stats["by_status"][status.value] = count
        stats["total"] = sum(stats["by_status"].values())

        resources = await self.resource_repository.list(limit=1000)
        stats["total_resources"] = len(resources)
        stats["active_resources"] = sum(1 for r in resources if r.is_active)

        return stats

    def _publish_event(self, domain_event: Any) -> None:
        try:
            event = Event(
                name=domain_event.event_type,
                data=domain_event.payload if hasattr(domain_event, "payload") else {},
                correlation_id=getattr(domain_event, "correlation_id", ""),
                tenant_id=getattr(domain_event, "tenant_id", ""),
            )
            self.event_bus.publish(event)
        except Exception as exc:
            logger.error(
                "Failed to publish event %s: %s",
                getattr(domain_event, "event_type", "unknown"),
                exc,
            )

    async def _generate_time_slots(self, schedule: Schedule) -> list[TimeSlot]:
        if not schedule.date or not schedule.start_time or not schedule.end_time:
            return []
        existing = await self.time_slot_repository.find_by_schedule(schedule.id)
        existing_by_start = {}
        for s in existing:
            if s.start_at:
                key = s.start_at.isoformat()
                existing_by_start[key] = s

        start_dt = datetime.combine(schedule.date, schedule.start_time, tzinfo=UTC)
        end_dt = datetime.combine(schedule.date, schedule.end_time, tzinfo=UTC)
        duration = timedelta(minutes=schedule.slot_duration_minutes)
        slots: list[TimeSlot] = []
        current = start_dt
        while current < end_dt:
            slot_end = current + duration
            key = current.isoformat()
            if key in existing_by_start:
                slots.append(existing_by_start[key])
            else:
                slot = TimeSlot(
                    id=str(uuid.uuid4()),
                    schedule_id=schedule.id,
                    start_at=current,
                    end_at=slot_end,
                    status=SlotStatus.AVAILABLE,
                )
                slots.append(slot)
            current = slot_end

        return await self.time_slot_repository.save_many(slots)
