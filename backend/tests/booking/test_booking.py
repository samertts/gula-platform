"""Booking Platform - Domain & Service Tests"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from app._compat import UTC

from shared.booking import BookingEngine, BookingStatus
from shared.domain.booking import Appointment, AppointmentStatus


class TestAppointmentStatus:
    def test_active_statuses(self):
        assert AppointmentStatus.PENDING.is_active() is True
        assert AppointmentStatus.CONFIRMED.is_active() is True
        assert AppointmentStatus.CHECKED_IN.is_active() is True
        assert AppointmentStatus.IN_PROGRESS.is_active() is True

    def test_terminal_statuses(self):
        assert AppointmentStatus.COMPLETED.is_terminal() is True
        assert AppointmentStatus.CANCELLED.is_terminal() is True
        assert AppointmentStatus.NO_SHOW.is_terminal() is True

    def test_non_active_statuses(self):
        assert AppointmentStatus.COMPLETED.is_active() is False
        assert AppointmentStatus.CANCELLED.is_active() is False
        assert AppointmentStatus.NO_SHOW.is_active() is False


class TestAppointment:
    def test_auto_generates_id(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        assert apt.id
        assert len(apt.id) > 0

    def test_default_status_is_pending(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        assert apt.status == AppointmentStatus.PENDING

    def test_transition_to_valid_status(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        apt.transition_to(AppointmentStatus.CONFIRMED)
        assert apt.status == AppointmentStatus.CONFIRMED

    def test_transition_to_invalid_status_raises(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        with pytest.raises(ValueError, match="Cannot transition"):
            apt.transition_to(AppointmentStatus.COMPLETED)

    def test_terminal_transitions_are_blocked(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        apt.transition_to(AppointmentStatus.CONFIRMED)
        apt.transition_to(AppointmentStatus.CANCELLED)
        with pytest.raises(ValueError):
            apt.transition_to(AppointmentStatus.CHECKED_IN)

    def test_can_check_in(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        apt.transition_to(AppointmentStatus.CONFIRMED)
        assert apt.can_check_in() is True

    def test_cannot_check_in_when_pending(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        assert apt.can_check_in() is False

    def test_is_reschedulable_when_pending(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        assert apt.is_reschedulable() is True

    def test_is_not_reschedulable_when_completed(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        apt.transition_to(AppointmentStatus.CONFIRMED)
        apt.transition_to(AppointmentStatus.CHECKED_IN)
        apt.transition_to(AppointmentStatus.IN_PROGRESS)
        apt.transition_to(AppointmentStatus.COMPLETED)
        assert apt.is_reschedulable() is False

    def test_full_workflow(self):
        apt = Appointment(patient_id="P001", lab_id=1)
        assert apt.status == AppointmentStatus.PENDING
        apt.transition_to(AppointmentStatus.CONFIRMED)
        assert apt.status == AppointmentStatus.CONFIRMED
        apt.transition_to(AppointmentStatus.CHECKED_IN)
        assert apt.status == AppointmentStatus.CHECKED_IN
        apt.transition_to(AppointmentStatus.IN_PROGRESS)
        assert apt.status == AppointmentStatus.IN_PROGRESS
        apt.transition_to(AppointmentStatus.COMPLETED)
        assert apt.status == AppointmentStatus.COMPLETED

    def test_to_dict_contains_all_fields(self):
        apt = Appointment(patient_id="P001", lab_id=1, patient_name="Ali")
        d = apt.to_dict()
        assert d["patient_id"] == "P001"
        assert d["lab_id"] == 1
        assert d["patient_name"] == "Ali"
        assert d["status"] == "pending"
        assert "id" in d
        assert "created_at" in d


class TestBookingEngine:
    def test_book_creates_appointment(self):
        engine = BookingEngine()
        apt = engine.book("P001", 1, datetime.now(UTC))
        assert apt.patient_id == "P001"
        assert apt.status == AppointmentStatus.PENDING
        assert engine.count() == 1

    def test_get_returns_appointment(self):
        engine = BookingEngine()
        apt = engine.book("P001", 1, datetime.now(UTC))
        fetched = engine.get(apt.id)
        assert fetched is not None
        assert fetched.id == apt.id

    def test_get_nonexistent_returns_none(self):
        engine = BookingEngine()
        assert engine.get("nonexistent") is None

    def test_confirm_transitions_to_confirmed(self):
        engine = BookingEngine()
        apt = engine.book("P001", 1, datetime.now(UTC))
        engine.confirm(apt.id)
        assert engine.get(apt.id).status == AppointmentStatus.CONFIRMED

    def test_cancel_transitions_to_cancelled(self):
        engine = BookingEngine()
        apt = engine.book("P001", 1, datetime.now(UTC))
        engine.cancel(apt.id, reason="Patient request")
        assert engine.get(apt.id).status == AppointmentStatus.CANCELLED
        assert engine.get(apt.id).notes == "Patient request"

    def test_complete_workflow(self):
        engine = BookingEngine()
        apt = engine.book("P001", 1, datetime.now(UTC))
        engine.confirm(apt.id)
        engine.check_in(apt.id)
        engine.start(apt.id)
        engine.complete(apt.id)
        assert engine.get(apt.id).status == AppointmentStatus.COMPLETED

    def test_list_by_patient(self):
        engine = BookingEngine()
        engine.book("P001", 1, datetime.now(UTC))
        engine.book("P001", 2, datetime.now(UTC))
        engine.book("P002", 1, datetime.now(UTC))
        assert len(engine.list_by_patient("P001")) == 2
        assert len(engine.list_by_patient("P002")) == 1

    def test_list_by_lab(self):
        engine = BookingEngine()
        engine.book("P001", 1, datetime.now(UTC))
        engine.book("P002", 1, datetime.now(UTC))
        engine.book("P003", 2, datetime.now(UTC))
        assert len(engine.list_by_lab(1)) == 2
        assert len(engine.list_by_lab(2)) == 1

    def test_get_available_slots(self):
        engine = BookingEngine()
        today = datetime.now(UTC)
        slots = engine.get_available_slots(1, today)
        assert len(slots) > 0
        assert all(isinstance(s, str) for s in slots)

    def test_get_available_slots_excludes_booked(self):
        engine = BookingEngine()
        today = datetime.now(UTC)
        slot_time = today.replace(hour=9, minute=0, second=0, microsecond=0)
        engine.book("P001", 1, slot_time)
        slots = engine.get_available_slots(1, today)
        assert slot_time.isoformat() not in slots

    def test_mark_no_show(self):
        engine = BookingEngine()
        apt = engine.book("P001", 1, datetime.now(UTC))
        engine.confirm(apt.id)
        engine.mark_no_show(apt.id)
        assert engine.get(apt.id).status == AppointmentStatus.NO_SHOW

    def test_list_by_date(self):
        engine = BookingEngine()
        today = datetime.now(UTC)
        engine.book("P001", 1, today)
        engine.book("P002", 1, today + timedelta(days=1))
        assert len(engine.list_by_date(1, today)) == 1

    def test_booking_status_alias(self):
        assert BookingStatus is AppointmentStatus
