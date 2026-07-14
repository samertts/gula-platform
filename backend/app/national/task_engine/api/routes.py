from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.national.task_engine.application.service import TaskEngineService
from backend.app.national.task_engine.domain.entities import (
    NationalTask,
    TaskQueue,
    TaskSLADefinition,
)
from backend.app.national.task_engine.domain.enums import (
    TaskCategory,
    TaskPriority,
    TaskStatus,
)
from backend.app.national.task_engine.infrastructure.repository import (
    SQLAlchemyNationalTaskRepository,
    SQLAlchemyTaskAssignmentRepository,
    SQLAlchemyTaskAuditLogRepository,
    SQLAlchemyTaskCommentRepository,
    SQLAlchemyTaskEscalationRepository,
    SQLAlchemyTaskQueueRepository,
    SQLAlchemyTaskSLARepository,
)
from backend.app.security.dependencies import get_current_user

router = APIRouter(prefix="/national/tasks", tags=["National Task Engine"])


def _get_service() -> TaskEngineService:
    return TaskEngineService(
        task_repo=SQLAlchemyNationalTaskRepository(),
        queue_repo=SQLAlchemyTaskQueueRepository(),
        assignment_repo=SQLAlchemyTaskAssignmentRepository(),
        escalation_repo=SQLAlchemyTaskEscalationRepository(),
        sla_repo=SQLAlchemyTaskSLARepository(),
        comment_repo=SQLAlchemyTaskCommentRepository(),
        audit_repo=SQLAlchemyTaskAuditLogRepository(),
    )


@router.post("/")
async def create_task(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    task = NationalTask(
        id=str(uuid.uuid4()),
        title=data["title"],
        description=data.get("description", ""),
        priority=TaskPriority(data.get("priority", "medium")),
        category=TaskCategory(data.get("category", "general")),
        task_type=data.get("task_type", "general"),
        queue_id=data.get("queue_id"),
        sla_due_at=None,
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
        correlation_id=data.get("correlation_id"),
        created_by=current_user.id if hasattr(current_user, "id") else None,
    )
    result = await svc.create_task(task)
    return {"success": True, "id": result.id}


@router.post("/bulk")
async def bulk_create(data: list[dict], current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    tasks = []
    for item in data:
        task = NationalTask(
            id=str(uuid.uuid4()),
            title=item["title"],
            description=item.get("description", ""),
            priority=TaskPriority(item.get("priority", "medium")),
            category=TaskCategory(item.get("category", "general")),
            queue_id=item.get("queue_id"),
            tags=item.get("tags", []),
            created_by=current_user.id if hasattr(current_user, "id") else None,
        )
        tasks.append(task)
    results = await svc.bulk_create(tasks)
    return {"success": True, "count": len(results), "ids": [r.id for r in results]}


@router.get("/")
async def list_tasks(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    assignee: str | None = Query(None),
    queue_id: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    filters = {}
    if status: filters["status"] = status
    if priority: filters["priority"] = priority
    if category: filters["category"] = category
    if assignee: filters["assignee"] = assignee
    if queue_id: filters["queue_id"] = queue_id
    if search: filters["search"] = search
    tasks = await svc.list_tasks(skip=skip, limit=limit, filters=filters)
    return {"items": tasks, "total": len(tasks), "skip": skip, "limit": limit}


@router.get("/dashboard")
async def get_dashboard(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    return await svc.get_dashboard()


@router.get("/{task_id}")
async def get_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    task = await svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}")
async def update_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    task = await svc.update_task(task_id, data)
    return {"success": True, "id": task.id}


@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    try:
        await svc.delete_task(task_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{task_id}/assign")
async def assign_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.assign_task(
        task_id, data["assignee_id"], data.get("assigned_by")
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/start")
async def start_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    result = await svc.start_task(
        task_id, current_user.id if hasattr(current_user, "id") else None
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str, data: dict | None = None, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.complete_task(task_id, data.get("result") if data else None)
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/fail")
async def fail_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.fail_task(task_id, data.get("error", "unknown error"))
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str, data: dict | None = None, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.cancel_task(task_id, (data or {}).get("reason"))
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/escalate")
async def escalate_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.escalate_task(
        task_id, data.get("reason", ""), data.get("escalated_to")
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/delegate")
async def delegate_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.delegate_task(task_id, data["to_user"], data.get("reason"))
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/hold")
async def hold_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    result = await svc.hold_task(task_id)
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    result = await svc.resume_task(task_id)
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/comments")
async def add_comment(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    comment = await svc.add_comment(
        task_id,
        current_user.id if hasattr(current_user, "id") else "unknown",
        data.get("author_name", ""),
        data["content"],
    )
    return {"success": True, "comment_id": comment.id}


@router.get("/{task_id}/comments")
async def get_comments(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    comments = await svc.get_comments(task_id)
    return {"comments": comments}


@router.get("/{task_id}/history")
async def get_history(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    history = await svc.get_history(task_id)
    return {"history": history}


@router.get("/queues")
async def list_queues(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    queues = await svc.list_queues()
    return {"queues": queues}


@router.post("/queues")
async def create_queue(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    queue = TaskQueue(
        id=str(uuid.uuid4()),
        name=data["name"],
        description=data.get("description", ""),
    )
    result = await svc.create_queue(queue)
    return {"success": True, "id": result.id}


@router.put("/queues/{queue_id}")
async def update_queue(
    queue_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.update_queue(queue_id, data)
    return {"success": True}


@router.get("/sla-definitions")
async def list_slas(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    slas = await svc.list_slas()
    return {"sla_definitions": slas}


@router.post("/sla-definitions")
async def create_sla(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    sla = TaskSLADefinition(
        id=str(uuid.uuid4()),
        task_category=TaskCategory(data.get("category", "general")),
        task_type=data.get("task_type", "general"),
        priority=TaskPriority(data.get("priority", "medium")),
        warning_threshold_s=data.get("warning_threshold_s", 3600),
        breach_threshold_s=data.get("breach_threshold_s", 7200),
    )
    result = await svc.create_sla(sla)
    return {"success": True, "id": result.id}


@router.put("/sla-definitions/{sla_id}")
async def update_sla(
    sla_id: str, data: dict, current_user: Any = Depends(get_current_user)
):
    svc = _get_service()
    result = await svc.update_sla(sla_id, data)
    return {"success": True}


@router.get("/pending")
async def get_pending_tasks(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    user_id = current_user.id if hasattr(current_user, "id") else "unknown"
    tasks = await svc.get_pending_tasks(user_id)
    return {"tasks": tasks}


@router.get("/overdue")
async def get_overdue_tasks(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    tasks = await svc.get_overdue_tasks()
    return {"tasks": tasks}


@router.get("/stats")
async def get_stats(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    return await svc.get_stats()


@router.get("/health")
async def health():
    return {"status": "ok", "module": "task_engine", "version": "1.0.0"}
