"""Canonical Core Clinical appointment vertical slice."""

from .models import CoreAppointment, CoreAppointmentIdempotencyReceipt, CoreAppointmentSlot

__all__ = ["CoreAppointment", "CoreAppointmentIdempotencyReceipt", "CoreAppointmentSlot"]
