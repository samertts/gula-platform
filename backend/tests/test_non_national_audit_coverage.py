from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.models.audit_log import AuditLog
from app.services.route_audit import audit_route_mutation


@pytest.mark.asyncio
async def test_audit_route_mutation_records_successful_route(db):
    @audit_route_mutation(action="route.test_mutation", resource_type="test_resource")
    async def audited_route(*, current_user, db):
        return {"id": 41, "secret": "redacted"}

    actor = SimpleNamespace(id=7, role="doctor", lab_id=3)
    result = await audited_route(current_user=actor, db=db)

    assert result["id"] == 41
    entry = db.query(AuditLog).filter(AuditLog.action == "route.test_mutation").one()
    assert entry.resource_type == "test_resource"
    assert entry.resource_id == 41
    assert entry.user_id == 7
    assert entry.lab_id == 3
    assert '"captured":false' in (entry.details or "")
    assert "secret" not in (entry.details or "")


def test_security_gate_has_zero_audit_coverage_findings():
    gate_path = Path(__file__).parents[2] / "config" / "quality-gates" / "security-gate.py"
    spec = importlib.util.spec_from_file_location("security_gate", gate_path)
    assert spec and spec.loader
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    findings = gate.check_audit_log_coverage(gate.ROOT)
    assert findings == []
