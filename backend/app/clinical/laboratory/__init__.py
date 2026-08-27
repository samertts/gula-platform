"""Canonical Laboratory Core (Slice 03)."""

from .models import CoreLabOrder, CoreLabOrderItem, CoreSpecimen, CoreSpecimenEvent
from .routes import router
from .service import LaboratoryService

__all__ = ["CoreLabOrder", "CoreLabOrderItem", "CoreSpecimen", "CoreSpecimenEvent", "LaboratoryService", "router"]
