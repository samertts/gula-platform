"""Canonical Laboratory Result Core (Slice 04)."""

from .models import CoreClinicalNotification, CoreCriticalResultEvent, CoreLabResult
from .routes import router
from .service import ResultService

__all__ = ["CoreClinicalNotification", "CoreCriticalResultEvent", "CoreLabResult", "ResultService", "router"]
