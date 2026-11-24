"""Abstract patient-identity port.

Every Health Core component that needs a patient must depend on this interface,
never on MPI, NHID, ``citizens``, ``PatientLink``, or ``CitizenLink``. During this
program the only implementation is :class:`SyntheticPatientRegistry`, which is
an in-memory adapter. There is intentionally no production implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.common.ids import is_synthetic_id, reject_national_identifier

DEFAULT_SYNTHETIC_TENANT = "SYN-LAB-0001"


@dataclass(frozen=True, slots=True)
class PatientRef:
    """Opaque reference to a synthetic patient.

    Deliberately contains no national id, name, phone, date of birth or any
    other real-world identifier. ``label`` is a short synthetic fixture label,
    never patient data.
    """

    ref: str
    tenant_id: str
    label: str = "synthetic-patient"

    def __post_init__(self) -> None:
        reject_national_identifier(self.ref, field="patient_ref")
        reject_national_identifier(self.tenant_id, field="tenant_id")
        reject_national_identifier(self.label, field="label")
        if not is_synthetic_id(self.ref):
            raise InvalidSyntheticReferenceError(
                "patient ref must be a SYN- prefixed synthetic reference",
                details={"field": "patient_ref"},
            )
        if not is_synthetic_id(self.tenant_id):
            raise InvalidSyntheticReferenceError(
                "tenant id must be a SYN- prefixed synthetic reference",
                details={"field": "tenant_id"},
            )
        if len(self.label) > 64:
            raise InvalidSyntheticReferenceError(
                "synthetic label must be at most 64 characters",
                details={"field": "label"},
            )


@runtime_checkable
class PatientIdentityPort(Protocol):
    """The single identity dependency allowed in Health Core development."""

    def register_patient(self, *, tenant_id: str, label: str) -> PatientRef:
        """Create a new synthetic patient in the given synthetic tenant."""
        ...

    def resolve_patient(self, *, tenant_id: str, patient_ref: str) -> PatientRef:
        """Resolve an existing synthetic patient; fail closed if unknown or cross-tenant."""
        ...

    def find_patient(self, *, patient_ref: str) -> PatientRef | None:
        """Return the synthetic patient or ``None`` (no implicit creation)."""
        ...
