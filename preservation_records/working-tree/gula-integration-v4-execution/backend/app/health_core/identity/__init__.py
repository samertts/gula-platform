"""Patient identity seam for synthetic Health Core development.

This is the ONLY identity dependency permitted inside ``app.health_core``.
The real MPI adapter is deliberately absent: it may be introduced only after
owner decisions are executed and MPI is re-audited to ACCEPT.
"""

from app.health_core.identity.port import (
    DEFAULT_SYNTHETIC_TENANT,
    PatientIdentityPort,
    PatientRef,
)
from app.health_core.identity.synthetic import SyntheticPatientRegistry

__all__ = ["DEFAULT_SYNTHETIC_TENANT", "PatientIdentityPort", "PatientRef", "SyntheticPatientRegistry"]
