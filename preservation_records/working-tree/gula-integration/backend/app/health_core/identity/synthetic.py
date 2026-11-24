"""In-memory synthetic patient registry.

This adapter touches no database, no MPI, no network and no filesystem. All
state is process-local and disappears with the object, so no durable real-looking
identity record can be created. It is the only identity implementation available
to Health Core development in this program.
"""

from __future__ import annotations

from app.health_core.common.errors import TenantMismatchError, UnknownPatientError
from app.health_core.common.ids import new_synthetic_id, reject_national_identifier
from app.health_core.identity.port import PatientRef


class SyntheticPatientRegistry:
    """A tenant-scoped, in-memory registry of synthetic patients."""

    def __init__(self) -> None:
        self._patients: dict[str, PatientRef] = {}

    def register_patient(self, *, tenant_id: str, label: str = "synthetic-patient") -> PatientRef:
        """Create and store a synthetic patient. No persistence, no MPI call."""
        patient = PatientRef(
            ref=new_synthetic_id("PAT"),
            tenant_id=tenant_id,
            label=label,
        )
        self._patients[patient.ref] = patient
        return patient

    def resolve_patient(self, *, tenant_id: str, patient_ref: str) -> PatientRef:
        """Resolve a patient only within its own synthetic tenant."""
        reject_national_identifier(patient_ref, field="patient_ref")
        patient = self._patients.get(patient_ref)
        if patient is None:
            raise UnknownPatientError(
                "synthetic patient not found",
                details={"patient_ref": patient_ref, "tenant_id": tenant_id},
            )
        if patient.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic patient belongs to a different tenant",
                details={"patient_ref": patient_ref, "tenant_id": tenant_id},
            )
        return patient

    def find_patient(self, *, patient_ref: str) -> PatientRef | None:
        """Return the patient without tenant filtering (for internal joins only)."""
        reject_national_identifier(patient_ref, field="patient_ref")
        return self._patients.get(patient_ref)

    def snapshot(self) -> dict[str, PatientRef]:
        """Return a defensive copy for test assertions."""
        return dict(self._patients)

    @property
    def count(self) -> int:
        """Number of synthetic patients currently registered."""
        return len(self._patients)
