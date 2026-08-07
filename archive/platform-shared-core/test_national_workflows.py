from __future__ import annotations

import pytest
from app.national.workflows import (
    EncounterWorkflow,
    MergeIdentityWorkflow,
    PatientRegistrationWorkflow,
    WorkflowContext,
    WorkflowState,
)


@pytest.mark.asyncio
async def test_patient_registration_workflow_standard():
    workflow = PatientRegistrationWorkflow()
    ctx = WorkflowContext(workflow_id="test-1", workflow_type="patient_registration")
    result = await workflow.execute(ctx, {"identity_type": "standard"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_patient_registration_workflow_newborn():
    workflow = PatientRegistrationWorkflow()
    ctx = WorkflowContext(workflow_id="test-2", workflow_type="patient_registration")
    result = await workflow.execute(ctx, {"identity_type": "newborn"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_patient_registration_workflow_foreigner():
    workflow = PatientRegistrationWorkflow()
    ctx = WorkflowContext(workflow_id="test-3", workflow_type="patient_registration")
    result = await workflow.execute(ctx, {"identity_type": "foreigner"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_encounter_workflow_outpatient():
    workflow = EncounterWorkflow()
    ctx = WorkflowContext(workflow_id="test-enc-1", workflow_type="encounter")
    result = await workflow.execute(ctx, {"encounter_type": "outpatient"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_encounter_workflow_emergency():
    workflow = EncounterWorkflow()
    ctx = WorkflowContext(workflow_id="test-enc-2", workflow_type="encounter")
    result = await workflow.execute(ctx, {"encounter_type": "emergency"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_merge_identity_workflow():
    workflow = MergeIdentityWorkflow()
    ctx = WorkflowContext(workflow_id="test-merge-1", workflow_type="merge")
    result = await workflow.execute(ctx, {"method": "manual"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_merge_identity_workflow_auto():
    workflow = MergeIdentityWorkflow()
    ctx = WorkflowContext(workflow_id="test-merge-2", workflow_type="merge")
    result = await workflow.execute(ctx, {"method": "nid_exact"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_workflow_compensation():
    workflow = PatientRegistrationWorkflow()
    ctx = WorkflowContext(workflow_id="test-comp-1", workflow_type="patient_registration")
    result = await workflow.execute(ctx, {"identity_type": "standard"})
    assert result.state == WorkflowState.COMPLETED
    await workflow.compensate(ctx)
    assert ctx.state == WorkflowState.COMPENSATED


@pytest.mark.asyncio
async def test_workflow_can_transition():
    workflow = PatientRegistrationWorkflow()
    assert await workflow.can_transition(WorkflowState.INITIATED, WorkflowState.IN_PROGRESS) is True
    assert (
        await workflow.can_transition(WorkflowState.COMPLETED, WorkflowState.IN_PROGRESS) is False
    )
