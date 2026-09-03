"""Canonical Emergency/EMS package; legacy EMS remains isolated."""

from .models import (
    CoreEmergencyDispatch,
    CoreEmergencyEPCR,
    CoreEmergencyHandover,
    CoreEmergencyIncident,
    CoreEmergencyOutbox,
    CoreEmergencyPrealert,
    CoreEmergencyTemporarySubject,
    CoreEmergencyTreatment,
    CoreEmergencyTriage,
)
from .routes import router
from .service import CanonicalEmergencyService

__all__ = [
    "CanonicalEmergencyService",
    "CoreEmergencyDispatch",
    "CoreEmergencyEPCR",
    "CoreEmergencyHandover",
    "CoreEmergencyIncident",
    "CoreEmergencyOutbox",
    "CoreEmergencyPrealert",
    "CoreEmergencyTemporarySubject",
    "CoreEmergencyTreatment",
    "CoreEmergencyTriage",
    "router",
]
