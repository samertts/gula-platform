from types import SimpleNamespace

import pytest
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.clinical_gateway.encounter_routes import router as encounter_router
from app.clinical_gateway.encounter_service import EncounterService
from app.clinical_gateway.workflow_routes import router as workflow_router


def test_encounter_and_workflow_routes_are_canonical_only():
    encounter_paths = {route.path for route in encounter_router.routes}
    workflow_paths = {route.path for route in workflow_router.routes}
    assert "/api/v1/clinical/encounters" in encounter_paths
    assert "/api/v1/clinical/encounters/{encounter_id}/start" in encounter_paths
    assert "/api/v1/clinical/workflow/shifts/start" in workflow_paths
    assert "/api/v1/clinical/workflow/tasks/{task_id}/complete" in workflow_paths


def test_encounter_rejects_unknown_type_before_database_lookup():
    access = SimpleNamespace(require_operation=lambda operation: None)
    with pytest.raises(ClinicalGatewayBlocked, match="invalid_encounter_type"):
        EncounterService(db=None).create(
            access=access,
            patient_id=101,
            encounter_type="client-controlled-type",
        )
