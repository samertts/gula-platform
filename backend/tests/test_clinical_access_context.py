from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app._compat import UTC
from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked


def _gateway_context() -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        actor=SimpleNamespace(
            account=SimpleNamespace(id=11),
            session=SimpleNamespace(id=22),
        ),
        workspace=SimpleNamespace(
            id="workspace-1",
            organization_id="org-1",
            facility_id="facility-1",
            department_id="dept-1",
        ),
        legacy_user=SimpleNamespace(id=33, lab_id=44),
        scope=SimpleNamespace(
            operational_organization_id=55,
            operational_facility_id=66,
            tenant_id=77,
        ),
    )


def test_context_derives_scope_from_gateway_only():
    context = ClinicalAccessContext.from_gateway(
        _gateway_context(),
        purpose="patient_care",
        permissions=frozenset({"read"}),
        correlation_id=uuid4(),
    )

    assert context.account_id == 11
    assert context.session_id == 22
    assert context.organization_id == "org-1"
    assert context.facility_id == "facility-1"
    assert context.tenant_id == 77
    assert context.patient_scope == "workspace_read"
    assert "national_id" not in context.audit_fields()


def test_context_requires_purpose():
    with pytest.raises(ClinicalGatewayBlocked, match="missing_purpose"):
        ClinicalAccessContext.from_gateway(_gateway_context(), purpose=" ")


def test_context_denies_clinical_write_without_shift_assignment_task():
    context = ClinicalAccessContext.from_gateway(
        _gateway_context(),
        purpose="documentation",
        permissions=frozenset({"create"}),
    )

    with pytest.raises(ClinicalGatewayBlocked, match="clinical_shift_assignment_task_required"):
        context.require_operation("create")


def test_context_denies_write_without_permission_even_with_context():
    context = ClinicalAccessContext.from_gateway(
        _gateway_context(),
        purpose="documentation",
        permissions=frozenset(),
    )
    context = context.__class__(**{**context.__dict__, "shift_id": "shift-1", "assignment_id": "assignment-1", "task_id": "task-1", "patient_scope": "patient:1"})

    with pytest.raises(ClinicalGatewayBlocked, match="clinical_permission_required"):
        context.require_operation("create")


def test_context_allows_shift_start_only_with_server_permission():
    context = ClinicalAccessContext.from_gateway(
        _gateway_context(),
        purpose="workflow.shift.start",
        permissions=frozenset({"shift:start"}),
    )
    context.require_operation("shift_start")


def test_context_denies_task_create_without_assignment_and_patient_scope():
    context = ClinicalAccessContext.from_gateway(
        _gateway_context(),
        purpose="workflow.task.create",
        permissions=frozenset({"task:create"}),
    )
    with pytest.raises(ClinicalGatewayBlocked, match="shift_assignment_and_patient_scope_required"):
        context.require_operation("task_create")
