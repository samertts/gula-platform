from __future__ import annotations

import pytest
from app.national.workflows import MergeIdentityWorkflow, WorkflowContext, WorkflowState


@pytest.mark.asyncio
async def test_auto_merge_flow():
    workflow = MergeIdentityWorkflow()
    ctx = WorkflowContext(workflow_id="merge-auto-1", workflow_type="merge")
    result = await workflow.execute(ctx, {"method": "nid_exact"})
    assert result.state == WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_manual_merge_flow_includes_human_review():
    workflow = MergeIdentityWorkflow()
    ctx = WorkflowContext(workflow_id="merge-manual-1", workflow_type="merge")
    await workflow.execute(ctx, {"method": "manual"})
    step_names = [s.name for s in workflow._steps]
    assert "human_review" in step_names


@pytest.mark.asyncio
async def test_auto_merge_skips_human_review():
    workflow = MergeIdentityWorkflow()
    ctx = WorkflowContext(workflow_id="merge-auto-2", workflow_type="merge")
    await workflow.execute(ctx, {"method": "nid_exact"})
    step_names = [s.name for s in workflow._steps]
    assert "human_review" not in step_names


@pytest.mark.asyncio
async def test_merge_audit_logging():
    workflow = MergeIdentityWorkflow()
    ctx = WorkflowContext(workflow_id="merge-audit-1", workflow_type="merge")
    await workflow.execute(ctx, {"method": "manual"})
    step_names = [s.name for s in workflow._steps]
    assert "audit_logging" in step_names
