"""Canonical Hospital Core package; legacy hospital remains isolated."""

from .models import (
    CoreAdmission,
    CoreBedAllocation,
    CoreCareTeamMember,
    CoreDischarge,
    CoreDischargeSummary,
    CoreHandover,
    CoreHospitalBed,
    CoreHospitalFacility,
    CoreHospitalRoom,
    CoreHospitalWard,
    CoreMedicationAdministration,
    CoreMedicationSafetyEvent,
    CoreNursingTask,
    CorePatientTransfer,
    CoreVitalObservation,
)
from .routes import router
from .service import CanonicalHospitalService

__all__ = [
    "CanonicalHospitalService",
    "CoreAdmission",
    "CoreBedAllocation",
    "CoreCareTeamMember",
    "CoreDischarge",
    "CoreDischargeSummary",
    "CoreHandover",
    "CoreHospitalBed",
    "CoreHospitalFacility",
    "CoreHospitalRoom",
    "CoreHospitalWard",
    "CoreMedicationAdministration",
    "CoreMedicationSafetyEvent",
    "CoreNursingTask",
    "CorePatientTransfer",
    "CoreVitalObservation",
    "router",
]
