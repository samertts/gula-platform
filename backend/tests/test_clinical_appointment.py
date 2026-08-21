from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from app.clinical_gateway.appointment_routes import AppointmentCreateRequest
from app.clinical_gateway.appointment_service import AppointmentCanonicalService
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.national.scheduling_platform.infrastructure.models import NationalAppointment
from pydantic import ValidationError


def test_appointment_create_contract_forbids_client_authority_fields() -> None:
    with pytest.raises(ValidationError):
        AppointmentCreateRequest(
            patient_id="patient-1",
            practitioner_id="client-controlled",
            appointment_type="consultation",
            start_at=datetime(2026, 8, 22, 9, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 22, 9, 30, tzinfo=UTC),
        )


def test_appointment_create_contract_requires_valid_time_and_key_shape() -> None:
    with pytest.raises(ValidationError):
        AppointmentCreateRequest(
            patient_id="patient-1",
            appointment_type="consultation",
            start_at=datetime(2026, 8, 22, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 22, 9, 30, tzinfo=UTC),
            idempotency_key="short",
        )


def test_appointment_safe_dict_excludes_idempotency_and_legacy_scope_secrets() -> None:
    appointment = NationalAppointment(
        id="appointment-1",
        patient_id="patient-1",
        organization_id="org-1",
        workspace_id="workspace-1",
        department_id="dept-1",
        tenant_id=10,
        legacy_lab_id=99,
        idempotency_key="private-key-value",
        start_at=datetime(2026, 8, 22, 9, 0, tzinfo=UTC),
        end_at=datetime(2026, 8, 22, 9, 30, tzinfo=UTC),
    )

    safe = AppointmentCanonicalService.to_safe_dict(appointment)

    assert safe["id"] == "appointment-1"
    assert safe["workspace_id"] == "workspace-1"
    assert "idempotency_key" not in safe
    assert "legacy_lab_id" not in safe
    assert "tenant_id" not in safe


def test_appointment_scope_unresolved_is_denied() -> None:
    appointment = NationalAppointment(id="appointment-1", patient_id="patient-1")
    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = appointment

    with pytest.raises(ClinicalGatewayBlocked, match="appointment_scope_unresolved"):
        AppointmentCanonicalService._appointment_model(db, "appointment-1")
