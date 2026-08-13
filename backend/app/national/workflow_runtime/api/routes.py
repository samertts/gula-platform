from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.national.workflow_runtime.application.service import (
    WorkflowRuntimeService,
)
from backend.app.national.workflow_runtime.domain.entities import (
    WorkflowDefinition,
    WorkflowStepDefinition,
    WorkflowTemplate,
)
from backend.app.national.workflow_runtime.domain.enums import WorkflowTrigger
from backend.app.national.workflow_runtime.infrastructure.repository import (
    SQLAlchemyWorkflowApprovalRepository,
    SQLAlchemyWorkflowCompensationRepository,
    SQLAlchemyWorkflowDefinitionRepository,
    SQLAlchemyWorkflowExecutionRepository,
    SQLAlchemyWorkflowExecutionStepRepository,
    SQLAlchemyWorkflowTemplateRepository,
    SQLAlchemyWorkflowTimerRepository,
)
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/national/workflows", tags=["National Workflows"])


def _get_service() -> WorkflowRuntimeService:

    return WorkflowRuntimeService(
        definition_repo=SQLAlchemyWorkflowDefinitionRepository(),
        execution_repo=SQLAlchemyWorkflowExecutionRepository(),
        step_repo=SQLAlchemyWorkflowExecutionStepRepository(),
        approval_repo=SQLAlchemyWorkflowApprovalRepository(),
        compensation_repo=SQLAlchemyWorkflowCompensationRepository(),
        timer_repo=SQLAlchemyWorkflowTimerRepository(),
        saga_repo=None,
        template_repo=SQLAlchemyWorkflowTemplateRepository(),
    )


@router.post("/definitions")
async def create_definition(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    steps = [WorkflowStepDefinition(**s) for s in data.get("steps", [])]
    definition = WorkflowDefinition(
        id=str(uuid.uuid4()),
        name=data["name"],
        description=data.get("description", ""),
        type=data.get("type", ""),
        steps=steps,
        input_schema=data.get("input_schema", {}),
        output_schema=data.get("output_schema", {}),
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
        created_by=current_user.id if hasattr(current_user, "id") else None,
    )
    result = await svc.create_definition(definition)
    return {"success": True, "id": result.id, "version": result.version}


@router.get("/definitions")
async def list_definitions(
    type: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    filters = {}
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status
    if search:
        filters["search"] = search
    definitions = await svc.list_definitions(skip=skip, limit=limit, filters=filters)
    return {"items": definitions, "total": len(definitions), "skip": skip, "limit": limit}


@router.get("/definitions/{definition_id}")
async def get_definition(definition_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    definition = await svc.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    return definition


@router.delete("/definitions/{definition_id}")
async def delete_definition(definition_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    deleted = await svc.delete_definition(definition_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    return {"success": True}


@router.post("/definitions/{definition_id}/execute")
async def execute_workflow(
    definition_id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    definition = await svc.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    execution = await svc.start_execution(
        workflow_type=definition.type,
        input_data=data.get("input", {}),
        trigger=WorkflowTrigger.API,
        correlation_id=data.get("correlation_id"),
        created_by=current_user.id if hasattr(current_user, "id") else None,
    )
    return {"success": True, "execution_id": execution.id, "status": execution.status.value}


@router.post("/execute")
async def execute_by_type(
    data: dict,
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    execution = await svc.start_execution(
        workflow_type=data["type"],
        input_data=data.get("input", {}),
        trigger=WorkflowTrigger.API,
        correlation_id=data.get("correlation_id"),
        created_by=current_user.id if hasattr(current_user, "id") else None,
    )
    return {"success": True, "execution_id": execution.id, "status": execution.status.value}


@router.get("/executions")
async def list_executions(
    status: str | None = Query(None),
    workflow_id: str | None = Query(None),
    trigger: str | None = Query(None),
    correlation_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    filters = {}
    if status:
        filters["status"] = status
    if workflow_id:
        filters["workflow_id"] = workflow_id
    if trigger:
        filters["trigger"] = trigger
    if correlation_id:
        filters["correlation_id"] = correlation_id
    executions = await svc.list_executions(skip=skip, limit=limit, filters=filters)
    return {"items": executions, "total": len(executions), "skip": skip, "limit": limit}


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    execution = await svc.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Workflow execution not found")
    steps = await svc.get_execution_steps(execution_id)
    return {"execution": execution, "steps": steps}


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    data: dict | None = None,
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    execution = await svc.cancel_execution(execution_id, (data or {}).get("reason"))
    return {"success": True, "status": execution.status.value}


@router.post("/executions/{execution_id}/pause")
async def pause_execution(execution_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    execution = await svc.pause_execution(execution_id)
    return {"success": True, "status": execution.status.value}


@router.post("/executions/{execution_id}/resume")
async def resume_execution(execution_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    execution = await svc.resume_execution(execution_id)
    return {"success": True, "status": execution.status.value}


@router.get("/executions/{execution_id}/steps")
async def get_execution_steps(execution_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    steps = await svc.get_execution_steps(execution_id)
    return {"steps": steps}


@router.get("/executions/{execution_id}/approvals")
async def get_execution_approvals(
    execution_id: str, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    if svc._approval_repo:
        approvals = await svc._approval_repo.find_by_execution(execution_id)
        return {"approvals": approvals}
    return {"approvals": []}


@router.post("/executions/{execution_id}/approve")
async def approve_step(
    execution_id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    approval = await svc.approve_step(
        execution_id,
        data["step_id"],
        current_user.id if hasattr(current_user, "id") else "unknown",
        data.get("comments"),
    )
    return {"success": True, "approval_id": approval.id}


@router.post("/executions/{execution_id}/reject")
async def reject_step(
    execution_id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    approval = await svc.reject_step(
        execution_id,
        data["step_id"],
        current_user.id if hasattr(current_user, "id") else "unknown",
        data.get("comments"),
    )
    return {"success": True, "approval_id": approval.id}


@router.get("/approvals/pending")
async def get_pending_approvals(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    user_id = current_user.id if hasattr(current_user, "id") else "unknown"
    approvals = await svc.get_pending_approvals(user_id)
    return {"approvals": approvals}


@router.post("/templates")
async def create_template(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    template = WorkflowTemplate(
        id=str(uuid.uuid4()),
        name=data["name"],
        description=data.get("description", ""),
        definition=data.get("definition", {}),
        parameters=data.get("parameters", {}),
        category=data.get("category", "general"),
        tags=data.get("tags", []),
        created_by=current_user.id if hasattr(current_user, "id") else None,
    )
    result = await svc.create_template(template)
    return {"success": True, "id": result.id}


@router.get("/templates")
async def list_templates(
    category: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    filters = {}
    if category:
        filters["category"] = category
    templates = await svc.list_templates(skip=skip, limit=limit, filters=filters)
    return {"items": templates, "total": len(templates)}


@router.post("/templates/{template_id}/instantiate")
async def instantiate_template(
    template_id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    definition = await svc.instantiate_template(
        template_id,
        data.get("parameters", {}),
        current_user.id if hasattr(current_user, "id") else None,
    )
    return {"success": True, "definition_id": definition.id}


@router.get("/stats")
async def get_stats(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    return await svc.get_stats()


@router.get("/definitions/{definition_id}/versions")
async def list_definition_versions(
    definition_id: str, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    definition = await svc.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Definition not found")
    versions = await svc.list_versions(definition.type)
    return {"versions": versions}


@router.get("/health")
async def health():
    return {"status": "ok", "module": "workflow_runtime", "version": "1.0.0"}
