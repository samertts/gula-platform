"""National Laboratory Information Management System (LIMS) Bounded Context.

This package implements the complete National LIMS platform on top of
the existing GULA foundation.  Foundation models (Lab, LabOrder, LabResult,
Patient, Sample, etc.) remain untouched.  Governance models also remain frozen.

Usage:
    from app.lims.models import Specimen, Instrument, Result, ...
    from app.lims.state_machine import enforce_specimen_transition
    from app.lims.services import SpecimenService, ResultService
    from app.lims.routes import lims_router

All LIMS entities support audit, versioning, soft delete, optimistic lock,
tenant isolation (lab_id), offline sync, events (outbox pattern), and FHIR mapping.
"""

from . import exceptions
from . import events
from . import state_machine
from . import models
from . import services

__all__ = [
    "exceptions",
    "events",
    "state_machine",
    "models",
    "services",
]
