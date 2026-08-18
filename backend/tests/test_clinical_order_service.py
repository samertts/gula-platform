from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.clinical_gateway.order_service import ClinicalOrderService


def _access(**overrides):
    values = {
        "account_id": 11,
        "session_id": 22,
        "legacy_user_id": 33,
        "legacy_lab_id": 44,
        "organization_id": "org-1",
        "facility_id": "facility-1",
        "workspace_id": "workspace-1",
        "department_id": "dept-1",
        "operational_organization_id": 55,
        "operational_facility_id": 66,
        "tenant_id": 77,
        "shift_id": "shift-1",
        "assignment_id": "assignment-1",
        "task_id": "task-1",
        "patient_scope": "patient:101",
        "purpose": "patient_care",
        "permissions": frozenset({"create", "update"}),
        "issued_at": None,
        "expires_at": None,
        "correlation_id": __import__("uuid").uuid4(),
    }
    values.update(overrides)
    return SimpleNamespace(**values, require_operation=lambda operation: None)


def test_create_rejects_spoofed_prescriber_without_db():
    with pytest.raises(ClinicalGatewayBlocked, match="prescriber_mismatch"):
        ClinicalOrderService(db=None).create(
            access=_access(),
            patient_id=101,
            encounter_id="enc-1",
            service="lab",
            client_prescriber_id="someone-else",
        )


def test_transition_map_has_no_backward_or_terminal_reopen():
    service = ClinicalOrderService(db=None)
    assert service is not None
    from app.clinical_gateway.order_service import _ALLOWED_TRANSITIONS

    assert "DRAFT" not in _ALLOWED_TRANSITIONS["COMPLETED"]
    assert "IN_PROGRESS" not in _ALLOWED_TRANSITIONS["CANCELLED"]
    assert "COMPLETED" not in _ALLOWED_TRANSITIONS["REJECTED"]
