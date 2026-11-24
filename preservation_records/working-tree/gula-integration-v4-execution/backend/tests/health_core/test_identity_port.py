"""Tests for the synthetic patient-identity seam (foundation of every workstream)."""

from __future__ import annotations

import pytest
from app.health_core.common.errors import (
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    UnknownPatientError,
)
from app.health_core.identity import (
    DEFAULT_SYNTHETIC_TENANT,
    PatientIdentityPort,
    PatientRef,
    SyntheticPatientRegistry,
)


def test_registry_is_in_memory_and_isolated():
    first = SyntheticPatientRegistry()
    second = SyntheticPatientRegistry()
    first.register_patient(tenant_id=DEFAULT_SYNTHETIC_TENANT)
    assert first.count == 1
    assert second.count == 0


def test_registered_patient_has_opaque_synthetic_reference(synthetic_registry):
    patient = synthetic_registry.register_patient(
        tenant_id=DEFAULT_SYNTHETIC_TENANT, label="synthetic-bravo"
    )
    assert isinstance(patient, PatientRef)
    assert patient.ref.startswith("SYN-PAT-")
    assert patient.tenant_id.startswith("SYN-")
    assert patient.label == "synthetic-bravo"
    assert not hasattr(patient, "national_id")


def test_resolve_within_tenant(synthetic_registry, synthetic_patient):
    resolved = synthetic_registry.resolve_patient(
        tenant_id=synthetic_patient.tenant_id, patient_ref=synthetic_patient.ref
    )
    assert resolved == synthetic_patient


def test_unknown_patient_fails_closed(synthetic_registry):
    with pytest.raises(UnknownPatientError) as exc:
        synthetic_registry.resolve_patient(
            tenant_id=DEFAULT_SYNTHETIC_TENANT, patient_ref="SYN-PAT-NOPE"
        )
    assert exc.value.code == "UNKNOWN_PATIENT"
    assert exc.value.status_code == 404


def test_cross_tenant_resolution_is_refused(synthetic_registry, synthetic_patient):
    with pytest.raises(TenantMismatchError) as exc:
        synthetic_registry.resolve_patient(
            tenant_id="SYN-LAB-9999", patient_ref=synthetic_patient.ref
        )
    assert exc.value.code == "TENANT_MISMATCH"
    assert exc.value.status_code == 403


def test_find_does_not_implicitly_create(synthetic_registry):
    assert synthetic_registry.find_patient(patient_ref="SYN-PAT-ABSENT") is None
    assert synthetic_registry.count == 0


def test_real_national_identifier_shape_is_rejected(synthetic_registry):
    with pytest.raises(InvalidSyntheticReferenceError):
        synthetic_registry.resolve_patient(
            tenant_id=DEFAULT_SYNTHETIC_TENANT, patient_ref="1234567890"
        )


def test_patient_ref_rejects_non_synthetic_values():
    with pytest.raises(InvalidSyntheticReferenceError):
        PatientRef(ref="PAT-123", tenant_id=DEFAULT_SYNTHETIC_TENANT)


def test_registry_satisfies_port_protocol():
    assert isinstance(SyntheticPatientRegistry(), PatientIdentityPort)


def test_snapshot_is_defensive(synthetic_registry, synthetic_patient):
    snapshot = synthetic_registry.snapshot()
    snapshot.clear()
    assert synthetic_registry.count == 1
